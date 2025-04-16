import json
import httpx
from typing import Dict, Any, Optional, List, Union, Tuple

from openai import AsyncOpenAI
from models import ServiceConfig, LocationResults, LocationError, EnvResult
from services import PlacesService, EnvironmentService, OpenAIService, SearchService
from assistant.analyzers import LandAnalyzer, LocalBusinessAnalyzer
from assistant.utils import ToolBuilder, ResultFormatter
from assistant.location_parser import LocationParser

class LocationAssistant:
    """
    Main assistant for analyzing locations and providing insights.
    """
    
    def __init__(self, openai_api_key: str, maps_api_key: str = "your_api_key", serper_api_key: str = "serper_api_key"):
        """
        Initialize the location assistant.
        
        Args:
            openai_api_key: OpenAI API key
            maps_api_key: Google Maps API key
            serper_api_key: Serper API key for web search
        """
        # Initialize services
        self.openai_service = OpenAIService(openai_api_key)
        self.places_service = PlacesService()
        self.env_service = EnvironmentService()
        self.search_service = SearchService(serper_api_key)
        
        # Store API keys
        self.openai_api_key = openai_api_key
        self.maps_api_key = maps_api_key
        self.serper_api_key = serper_api_key
        
        # Initialize OpenAI client
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)

        # Initialize location parser
        self.location_parser = LocationParser(
                                    google_maps_api_key=maps_api_key,
                                    openai_api_key=openai_api_key)

        # Initialize the latitude and longitude 
        self.latitude = None
        self.longitude = None

        self.user_query = ""
        
        # Initialize analyzers
        self.land_analyzer = LandAnalyzer(self.places_service, self.env_service, self.openai_service)
        self.business_analyzer = LocalBusinessAnalyzer(self.places_service, self.env_service, self.openai_service)
        
        # System prompts
        self.assistant_system_prompt = """
        You are a helpful location assistant that helps users find places near them and provides environmental information.
        
        When users ask about places, use the appropriate search function based on their request:
        - For finding places by category, use find_places
        - For comprehensive location analysis, use analyze_location_suitability
        - For business viability analysis, use analyze_business_viability
        - For information that requires real-time data, use search_web
        
        When users ask about air quality or pollen, use the get_environmental_data function.
        
        Always format search results in a user-friendly way. If distances are available, 
        mention them to help the user understand how far places are from them.
        
        If the requested data is not available for a location, explain the issue in a helpful way.
        """
    
    async def process_query(self, user_query: str, latitude: Optional[float] = None, longitude: Optional[float] = None, maps_api_key: Optional[str] = None):
        """
        Process a user query with the given location.
        
        Args:
            user_query: The user's question or request
            latitude: The user's latitude (optional if location in query)
            longitude: The user's longitude (optional if location in query)
            maps_api_key: Optional Google Maps API key (uses default if not provided)
            
        Returns:
            Response string
        """
        self.user_query = user_query
        # Parse the user query to extract location information if not provided
        parsed_query, extracted_coordinates = await self._parse_query(user_query)
        
        # Use extracted coordinates if no explicit coordinates provided
        if (latitude is None or longitude is None) and extracted_coordinates:
            latitude = extracted_coordinates.get('lat')
            longitude = extracted_coordinates.get('lng')
            print(f"Using extracted coordinates: Latitude {latitude}, Longitude {longitude}")
        
        # If still no coordinates, use default (San Francisco)
        if latitude is None or longitude is None:
            latitude = self.latitude
            longitude = self.longitude
            if latitude is None or longitude is None:
                return "no valid address"
            
        self.latitude = latitude
        self.longitude = longitude
        
        # Create the HTTP client
        async with httpx.AsyncClient(timeout=30) as client:
            # Create the configuration
            config = ServiceConfig(
                api_key=maps_api_key or self.maps_api_key,
                http_client=client,
                max_result_retries=2
            )
            
            # Use LLM to determine the query type and best action
            query_type_result = await self._classify_query_with_llm(parsed_query)
            query_type = query_type_result.get("query_type", "general")
            
            print(f"LLM classified query as: {query_type}")
            
            if query_type == "land_purchase":
                # For land purchase queries, use the comprehensive analysis
                print("Detected land purchase query, conducting comprehensive analysis...")
                return await self.land_analyzer.analyze_location(
                    latitude, longitude, parsed_query, None, config
                )
                
            elif query_type == "business":
                # For business viability queries
                business_type = query_type_result.get("business_type", "business")
                print(f"Detected {business_type} query, analyzing viability...")
                return await self.business_analyzer.analyze_location(
                    latitude, longitude, parsed_query, None, config, business_type
                )
            
            elif query_type == "web_search":
                # For web search queries, use the web search service
                print("Detected web search query, searching the web...")
                return await self._handle_web_search_query(parsed_query)
            
            else:
                # For general queries, use the standard conversation flow
                return await self._handle_general_query(parsed_query, latitude, longitude, config)
    
    async def _parse_query(self, user_query: str) -> Tuple[str, Optional[Dict[str, float]]]:
        """
        Parse the user query to extract location information.
        
        Args:
            user_query: The full user query
            
        Returns:
            Tuple of (parsed_query, coordinates_dict)
        """
        # Use the location parser to extract location from query
        clean_query, coordinates = await self.location_parser.parse_query(user_query)
        
        # If coordinates were extracted, use them
        if coordinates:
            print(f"Extracted coordinates from query: {coordinates}")
            return clean_query, coordinates
        
        # If neural processing is needed, we could use the OpenAI API to extract location
        # (Not implemented in this version)
        
        return user_query, None
    
    async def _classify_query_with_llm(self, query: str) -> Dict[str, Any]:
        """
        Use LLM to classify the query type and extract relevant details.
        
        Args:
            query: The user query
            
        Returns:
            Dict with query classification details including 'query_type' 
            (one of: 'land_purchase', 'business', 'web_search', 'general')
            and optional 'business_type' if applicable
        """
        try:
            # Define the system prompt for query classification
            system_prompt = """
            You are a query classifier for a location-based assistant. Your task is to classify user queries into the following categories:
            
            1. land_purchase - Queries about buying, purchasing, or investing in land
            2. business - Queries about starting, opening, or operating a business
            3. web_search - Queries that would benefit from current web information (news, regulations, updates, etc.)
            4. general - Any other general location-based queries
            
            For business queries, also identify the specific type of business mentioned.
            
            Respond with a JSON object containing:
            - query_type: "land_purchase", "business", "web_search", or "general"
            - business_type: The specific type of business (only for business queries)
            
            Common business types include: "tea stall", "coffee shop", "restaurant", "retail store", "grocery store", "bakery", etc.
            If no specific business is mentioned, use "business" as the generic type.
            """
            
            # Send the query to the LLM for classification
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Classify this query: \"{query}\""}
                ],
                temperature=0.2,  # Low temperature for consistent classification
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            classification_result = json.loads(response.choices[0].message.content)
            
            # Ensure the response has the correct format
            if "query_type" not in classification_result:
                classification_result["query_type"] = "general"
                
            # For business queries, ensure business_type is set
            if classification_result["query_type"] == "business" and "business_type" not in classification_result:
                classification_result["business_type"] = "business"
                
            return classification_result
        
        except Exception as e:
            # If any error occurs during classification, default to general query
            print(f"Error classifying query with LLM: {str(e)}")
            return {"query_type": "general"}
    
    async def _handle_web_search_query(self, query: str) -> str:
        """
        Handle a web search query.
        
        Args:
            query: The user query
            
        Returns:
            Response string with web search results
        """
        try:
            # Augment the query with location context if it's relevant
            search_query = self.user_query
            
            if self.latitude and self.longitude:
                # Add location if it seems relevant to the query
                location_keywords = ["near", "around", "nearby", "close", "location", "area", "neighborhood", "place"]
                if any(keyword in query.lower() for keyword in location_keywords):
                    # Use reverse geocoding to get location name (simplified here)
                    search_query = f"{query} {self.latitude}, {self.longitude}"
            
            # Get search results
            search_results = await self.search_service.search_and_extract(search_query, max_results=2)
            
            if not search_results:
                return "I couldn't find any relevant information from the web for your query."
            
            # Format the search results for the OpenAI API
            formatted_results = []
            for idx, result in enumerate(search_results, 1):
                formatted_results.append(f"Source {idx}: {result['title']}\nURL: {result['link']}\n\n{result['content'][:1000]}...")
            
            # Use OpenAI to generate a summary
            prompt = f"""
                The user asked: "{query}"

                I found the following information from the web:

                """ + '\n\n'.join(formatted_results) + """

                Please provide a helpful response that answers the user's question based on this information. 
                 include the relevant details and format properlly . Cite the sources when appropriate.
                """

            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an assistant that helps users with location-based queries using the latest information from the web."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content or "I couldn't generate a response based on the search results."
            
        except Exception as e:
            return f"I encountered an error while searching the web: {str(e)}"
    
    async def _handle_general_query(self, user_query: str, latitude: float, longitude: float, config: ServiceConfig) -> str:
        """Handle general queries using OpenAI function calling."""
        # Prepare the initial message
        full_query = f"{user_query} My location is {latitude}, {longitude}"
        messages = [
            {"role": "system", "content": self.assistant_system_prompt},
            {"role": "user", "content": full_query}
        ]
        
        # Create the tools
        tools = ToolBuilder.create_tools()
        
        # Initial conversation turns
        max_turns = 5
        current_turn = 0
        
        while current_turn < max_turns:
            current_turn += 1
            
            try:
                # Call the OpenAI API
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # Get the assistant's message
                assistant_message = response.choices[0].message
                messages.append({"role": "assistant", "content": assistant_message.content or "", "tool_calls": assistant_message.tool_calls})
                
                # Check if there are any tool calls
                if assistant_message.tool_calls:
                    # Handle each tool call
                    for tool_call in assistant_message.tool_calls:
                        # Parse the tool call arguments
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        # Call the tool
                        tool_result = await self._handle_tool_call(
                            tool_name=tool_call.function.name,
                            tool_args=tool_args,
                            config=config
                        )
                        
                        # Format the result
                        formatted_result = ResultFormatter.format_tool_result(tool_result)
                        
                        # Add the tool response to the conversation
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": formatted_result
                        })
                    
                    # Continue the conversation
                    continue
                else:
                    # No tool calls, we have a final answer
                    return assistant_message.content or "I couldn't generate a response."
            
            except Exception as e:
                # Handle any errors
                return f"Error processing your request: {str(e)}"
        
        # If we hit the max turns, return a failure message
        return "I'm sorry, I wasn't able to complete your request within the allowed number of turns."
    
    async def _handle_tool_call(self, tool_name: str, tool_args: Dict[str, Any], config: ServiceConfig) -> Union[LocationResults, EnvResult, LocationError, Dict[str, Any]]:
        """Handle a tool call from the model."""
        if tool_name == "find_places":
            return await self.places_service.find_places(
                latitude=tool_args.get("latitude"),
                longitude=tool_args.get("longitude"),
                place_type=tool_args.get("place_type"),
                radius=tool_args.get("radius"),
                keyword=tool_args.get("keyword"),
                config=config
            )
        elif tool_name == "analyze_location_suitability":
            # This would normally return a MultiLocationResults, but we'll just pass the query to the analyzer
            result = await self.land_analyzer.analyze_location(
                latitude=tool_args.get("latitude"),
                longitude=tool_args.get("longitude"),
                user_query="Can I buy land here?",
                radius=tool_args.get("radius"),
                config=config
            )
            # Convert the string result to LocationResults
            return LocationResults(
                places=[],
                total_found=1,
                search_term="land_analysis"
            )
        elif tool_name == "analyze_business_viability":
            # Get the business type from the args or use a default
            business_type = tool_args.get("business_type", "business")
            
            # Call the business analyzer
            result = await self.business_analyzer.analyze_location(
                latitude=tool_args.get("latitude"),
                longitude=tool_args.get("longitude"),
                user_query=f"Can I start a {business_type} here?",
                radius=tool_args.get("radius"),
                config=config,
                business_type=business_type
            )
            # Convert the string result to LocationResults
            return LocationResults(
                places=[],
                total_found=1,
                search_term=f"{business_type}_viability"
            )
        elif tool_name == "get_environmental_data":
            return await self.env_service.get_environmental_data(
                latitude=tool_args.get("latitude"),
                longitude=tool_args.get("longitude"),
                data_type=tool_args.get("data_type", "both"),
                config=config
            )
        elif tool_name == "search_web":
            query = tool_args.get("query", "")
            search_results = await self.search_service.search_and_extract(query, max_results=2)
            return {
                "results": search_results,
                "query": query
            }
        else:
            return LocationError(f"Unknown tool: {tool_name}")