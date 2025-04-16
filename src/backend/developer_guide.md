# Developer Guide: Extending the Locas

This guide explains how to extend the Locas with new tools and analyzers. Follow these steps to add new functionality to the system.

## Table of Contents

1. [Understanding the Architecture](#understanding-the-architecture)
2. [Adding a New Analyzer](#adding-a-new-analyzer)
3. [Adding a New Tool](#adding-a-new-tool)
4. [Integrating a New External Service](#integrating-a-new-external-service)
5. [Testing Your Extensions](#testing-your-extensions)

## Understanding the Architecture

Before adding extensions, it's important to understand how the components interact:

- **Analyzers** are specialized modules that handle specific query types (like land purchase or business viability)
- **Tools** are function definitions used by the OpenAI model to take actions during conversations
- **Services** connect to external APIs and provide data to analyzers and tools

The main flow is:
1. User submits a query with location information
2. The system extracts the location and determines the query type
3. It routes the query to the appropriate analyzer
4. The analyzer uses various services to collect data
5. The analyzer processes the data and returns a result

## Adding a New Analyzer

Let's say we want to add a "RealEstateAnalyzer" for property value analysis. Here's what you need to do:

### 1. Create the Analyzer Class

Create a new file `assistant/analyzers/real_estate_analyzer.py`:

```python
from typing import Dict, Union, Optional

from models import ServiceConfig, MultiLocationResults, LocationError, LocationResults, EnvResult
from services import PlacesService, EnvironmentService, OpenAIService
from assistant.utils import ResultFormatter

class RealEstateAnalyzer:
    """Analyzer for real estate property values and market trends."""
    
    def __init__(self, places_service: PlacesService, env_service: EnvironmentService, openai_service: OpenAIService):
        """Initialize with required services."""
        self.places_service = places_service
        self.env_service = env_service
        self.openai_service = openai_service
        
        # Categories relevant to real estate analysis
        self.categories = [
            'schools', 'hospitals', 'transportation', 'shopping', 
            'parks', 'crime', 'restaurants'
        ]
    
    async def analyze_location(self, latitude: float, longitude: float, user_query: str,
                         radius: Optional[int] = None, config: ServiceConfig = None,
                         property_type: str = "residential") -> str:
        """
        Analyze location for real estate property value.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            user_query: The original user query
            radius: Search radius (optional)
            config: Service configuration
            property_type: Type of property to analyze (default: "residential")
            
        Returns:
            Analysis result as a string
        """
        try:
            # Collect data for all relevant categories
            result = await self._collect_location_data(latitude, longitude, radius, config, property_type)
            
            # Format the result for analysis
            if isinstance(result, LocationError):
                return f"Error analyzing location: {result.error_message}"
            
            formatted_result = ResultFormatter.format_multi_location_results(result)
            
            # Send to OpenAI for analysis
            analysis = await self.openai_service.analyze_real_estate(
                latitude, longitude, user_query, formatted_result, property_type
            )
            
            return analysis
        except Exception as e:
            return f"Error analyzing location for {property_type} real estate: {str(e)}"
    
    async def _collect_location_data(self, latitude: float, longitude: float, 
                              radius: Optional[int] = None, 
                              config: ServiceConfig = None,
                              property_type: str = "residential") -> Union[MultiLocationResults, LocationError]:
        """Collect data for all relevant categories."""
        try:
            category_results = {}
            location = {"latitude": latitude, "longitude": longitude}
            
            # Search for each category of interest
            for category in self.categories:
                result = await self.places_service.find_places(
                    latitude=latitude,
                    longitude=longitude,
                    place_type=category,
                    radius=radius,
                    config=config
                )
                
                if isinstance(result, LocationResults):
                    category_results[category] = result
                else:
                    # If there was an error, add an empty result
                    category_results[category] = LocationResults(
                        places=[],
                        total_found=0,
                        search_term=category
                    )
            
            # Get environmental data
            env_result = await self.env_service.get_environmental_data(
                latitude=latitude,
                longitude=longitude,
                data_type="both",
                config=config
            )
            
            if isinstance(env_result, EnvResult):
                # Add a special entry for environmental data
                category_results["environmental"] = LocationResults(
                    places=[],
                    total_found=1,
                    search_term="environmental"
                )
                
                # Get formatted environmental data
                env_message = await self.openai_service.format_environmental_data(env_result.message)
                category_results["environmental_message"] = env_message
            
            return MultiLocationResults(
                category_results=category_results,
                location=location
            )
        except Exception as e:
            return LocationError(
                error_message=f"Error collecting real estate data: {str(e)}",
                location={"latitude": latitude, "longitude": longitude}
            )
```

### 2. Update the `__init__.py` in the analyzers directory

Update `assistant/analyzers/__init__.py` to include your new analyzer:

```python
from assistant.analyzers.land_analyzer import LandAnalyzer
from assistant.analyzers.local_business_analyzer import LocalBusinessAnalyzer
from assistant.analyzers.real_estate_analyzer import RealEstateAnalyzer

__all__ = ['LandAnalyzer', 'LocalBusinessAnalyzer', 'RealEstateAnalyzer']
```

### 3. Add Query Detection Method in LocationAssistant

Update `assistant/location_assistant.py` to detect and route to your new analyzer.

First, add a new detection method:

```python
def _is_real_estate_query(self, query: str) -> Dict[str, Any]:
    """
    Check if the query is about real estate and identify the property type.
    
    Args:
        query: The user query
        
    Returns:
        Dict with 'is_real_estate' boolean and 'property_type' string if applicable
    """
    query_lower = query.lower()
    
    # Define property types to check for
    property_types = {
        "residential": ["house", "home", "apartment", "condo", "residential"],
        "commercial": ["office", "retail space", "commercial", "shop space"],
        "industrial": ["warehouse", "factory", "industrial", "manufacturing"]
    }
    
    # Check for real estate terms
    real_estate_terms = ["property", "real estate", "housing", "market value", "price"]
    
    # Check for specific property types
    for property_type, keywords in property_types.items():
        for keyword in keywords:
            if keyword in query_lower:
                for term in real_estate_terms:
                    if term in query_lower:
                        return {
                            "is_real_estate": True,
                            "property_type": property_type
                        }
    
    # Check for general real estate queries
    for term in real_estate_terms:
        if term in query_lower:
            return {
                "is_real_estate": True,
                "property_type": "residential"  # Default to residential
            }
            
    return {
        "is_real_estate": False,
        "property_type": None
    }
```

### 4. Initialize the Analyzer in LocationAssistant Constructor

Add the new analyzer to the `__init__` method in `assistant/location_assistant.py`:

```python
# Add to imports
from assistant.analyzers import LandAnalyzer, LocalBusinessAnalyzer, RealEstateAnalyzer

# Inside the __init__ method
self.real_estate_analyzer = RealEstateAnalyzer(
    self.places_service, self.env_service, self.openai_service
)
```

### 5. Update the Process Query Method

Update the `process_query` method in `assistant/location_assistant.py` to handle the new query type:

```python
# Inside process_query method, after checking for business queries
# Check if it's a real estate query
real_estate_check = self._is_real_estate_query(parsed_query)
if real_estate_check["is_real_estate"]:
    # For real estate queries
    property_type = real_estate_check["property_type"]
    print(f"Detected {property_type} real estate query, analyzing...")
    return await self.real_estate_analyzer.analyze_location(
        latitude, longitude, parsed_query, None, config, property_type
    )
```

## Adding a New Tool

Now, let's add a new tool for real estate price information.

### 1. Add a Method to the OpenAI Service

First, add a new analysis method to `services/openai_service.py`:

```python
async def analyze_real_estate(self, latitude: float, longitude: float, 
                      user_query: str, location_data: str, 
                      property_type: str = "residential") -> str:
    """
    Analyze location data for real estate value.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        user_query: The original user query
        location_data: Formatted location data to analyze
        property_type: Type of property to analyze
        
    Returns:
        Analysis as a string
    """
    analysis_prompt = f"""
    A user at coordinates ({latitude}, {longitude}) is asking: "{user_query}"
    
    They want to know about real estate property values for {property_type} property in this area.
    
    Here is data about the surrounding area:
    
    {location_data}
    
    Please provide a detailed analysis of the real estate market for {property_type} properties at this location. Consider:
    1. Proximity to amenities (schools, shopping, parks)
    2. Transportation options
    3. Environmental factors
    4. Neighborhood profile
    5. Potential market trends
    
    Highlight both advantages and potential challenges. Be balanced and objective.
    Conclude with a general assessment of whether this would be a valuable location for {property_type} real estate.
    """
    
    try:
        # Add a system prompt for real estate if it doesn't exist
        if not hasattr(self, 'real_estate_analysis_system_prompt'):
            self.real_estate_analysis_system_prompt = """
            You are a real estate market analyst providing insights about locations.
            Your analysis should be detailed, balanced, and objective, focusing on both 
            advantages and potential concerns for real estate investments and property values.
            """
        
        analysis_response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.real_estate_analysis_system_prompt},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return analysis_response.choices[0].message.content
    except Exception as e:
        return f"Error generating real estate analysis: {str(e)}"
```

### 2. Add the Tool Definition to ToolBuilder

Add a new tool definition in `assistant/utils/tools.py`:

```python
@staticmethod
def analyze_real_estate_tool() -> Dict[str, Any]:
    """Create the analyze_real_estate tool definition."""
    return ToolBuilder._convert_to_tool_format(
        name="analyze_real_estate",
        description="Analyze the real estate market and property values at the specified location.",
        parameters={
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "The latitude coordinate"
                },
                "longitude": {
                    "type": "number",
                    "description": "The longitude coordinate"
                },
                "radius": {
                    "type": "integer",
                    "description": "Search radius in meters (default: 1500)"
                },
                "property_type": {
                    "type": "string",
                    "description": "Type of property to analyze (e.g., \"residential\", \"commercial\", \"industrial\")",
                    "default": "residential"
                }
            },
            "required": ["latitude", "longitude"]
        }
    )
```

### 3. Update the Tool List

Add your new tool to the `create_tools` method in `assistant/utils/tools.py`:

```python
@staticmethod
def create_tools() -> List[Dict[str, Any]]:
    """
    Create the full set of tools for the assistant.
    
    Returns:
        List of tool definitions
    """
    return [
        ToolBuilder.find_places_tool(),
        ToolBuilder.analyze_location_suitability_tool(),
        ToolBuilder.analyze_business_viability_tool(),
        ToolBuilder.analyze_real_estate_tool(),  # Add the new tool
        ToolBuilder.get_environmental_data_tool()
    ]
```

### 4. Update the Tool Call Handler

Update the `_handle_tool_call` method in `assistant/location_assistant.py` to handle your new tool:

```python
async def _handle_tool_call(self, tool_name: str, tool_args: Dict[str, Any], config: ServiceConfig) -> Union[LocationResults, EnvResult, LocationError]:
    """Handle a tool call from the model."""
    # ... existing tool handlers ...
    
    elif tool_name == "analyze_real_estate":
        # Get the property type from the args or use a default
        property_type = tool_args.get("property_type", "residential")
        
        # Call the real estate analyzer
        result = await self.real_estate_analyzer.analyze_location(
            latitude=tool_args.get("latitude"),
            longitude=tool_args.get("longitude"),
            user_query=f"How's the {property_type} real estate market here?",
            radius=tool_args.get("radius"),
            config=config,
            property_type=property_type
        )
        # Convert the string result to LocationResults
        return LocationResults(
            places=[],
            total_found=1,
            search_term=f"{property_type}_real_estate"
        )
    
    # ... remaining tool handlers ...
```

## Integrating a New External Service

Let's say we want to add historical property price data. Here's how:

### 1. Create a New Service Class

Create a new file `services/property_service.py`:

```python
import httpx
from typing import Dict, Any, Union, Optional

from models import ServiceConfig, LocationError

class PropertyService:
    """Service for fetching property price history and market data."""
    
    async def get_property_data(self, latitude: float, longitude: float,
                           property_type: str = "residential", 
                           config: ServiceConfig = None) -> Union[Dict[str, Any], LocationError]:
        """
        Get property market data for the specified location.
        
        Args:
            latitude: The latitude coordinate
            longitude: The longitude coordinate
            property_type: Type of property (residential, commercial, industrial)
            config: Service configuration
            
        Returns:
            Dict with property data or LocationError
        """
        try:
            # In a real implementation, you would call an actual property data API
            # For this example, we'll return mock data
            
            # Check if API key exists and is not the placeholder
            if config.api_key == "your_api_key":
                # Return sample data for testing
                return self._get_mock_property_data(property_type)
            
            # Build the URL for the Property API
            base_url = "https://api.propertydata.example/v1/market"
            
            # Required parameters
            params = {
                "location": f"{latitude},{longitude}",
                "property_type": property_type,
                "key": config.api_key
            }
            
            # Make the HTTP request
            response = await config.http_client.get(base_url, params=params)
            
            # Raise an exception if the request failed
            response.raise_for_status()
            
            # Return the JSON response
            return response.json()
            
        except Exception as e:
            return LocationError(
                error_message=f"Error retrieving property data: {str(e)}",
                location={"latitude": latitude, "longitude": longitude}
            )
    
    def _get_mock_property_data(self, property_type: str) -> Dict[str, Any]:
        """Get mock property data for development and testing."""
        if property_type == "residential":
            return {
                "average_price": 750000,
                "price_trend": "+5.2% (YoY)",
                "avg_price_sqft": 450,
                "inventory": "Low",
                "avg_days_on_market": 28,
                "property_type": "residential"
            }
        elif property_type == "commercial":
            return {
                "average_price": 1250000,
                "price_trend": "+2.8% (YoY)",
                "avg_price_sqft": 380,
                "vacancy_rate": "8.5%",
                "property_type": "commercial"
            }
        else:
            return {
                "average_price": 950000,
                "price_trend": "+1.9% (YoY)",
                "avg_price_sqft": 210,
                "vacancy_rate": "12%",
                "property_type": property_type
            }
```

### 2. Update the `__init__.py` in the services directory

Update `services/__init__.py` to include your new service:

```python
from services.places_service import PlacesService
from services.environment_service import EnvironmentService
from services.openai_service import OpenAIService
from services.property_service import PropertyService

__all__ = ['PlacesService', 'EnvironmentService', 'OpenAIService', 'PropertyService']
```

### 3. Update LocationAssistant to use the new service

In `assistant/location_assistant.py`, add the new service to the imports and initialize it:

```python
# Add to imports
from services import PlacesService, EnvironmentService, OpenAIService, PropertyService

# Inside the __init__ method
self.property_service = PropertyService()

# Then update the real_estate_analyzer initialization to include the new service
self.real_estate_analyzer = RealEstateAnalyzer(
    self.places_service, self.env_service, self.openai_service, self.property_service
)
```

### 4. Update the RealEstateAnalyzer to use the new service

Modify your `RealEstateAnalyzer` constructor to accept the new service:

```python
def __init__(self, places_service: PlacesService, env_service: EnvironmentService, 
             openai_service: OpenAIService, property_service: PropertyService):
    """Initialize with required services."""
    self.places_service = places_service
    self.env_service = env_service
    self.openai_service = openai_service
    self.property_service = property_service
    
    # Categories relevant to real estate analysis
    self.categories = [
        'schools', 'hospitals', 'transportation', 'shopping', 
        'parks', 'crime', 'restaurants'
    ]
```

### 5. Update the Data Collection Method

Add property data collection to the `_collect_location_data` method:

```python
# Inside _collect_location_data method, before returning the result
# Get property data
property_data = await self.property_service.get_property_data(
    latitude=latitude,
    longitude=longitude,
    property_type=property_type,
    config=config
)

if not isinstance(property_data, LocationError):
    # Add property data to the results
    category_results["property_market"] = LocationResults(
        places=[],
        total_found=1,
        search_term="property_market"
    )
    # Store the raw property data
    category_results["property_market_data"] = property_data
```

## Testing Your Extensions

Here's how to test your new functionality:

### 1. Create Test Queries

Create test queries that should trigger your new analyzer:

```python
test_cases = [
    # Test real estate query
    {
        "name": "Real Estate Query",
        "payload": {
            "query": "What's the property value of homes near Central Park, New York?"
        }
    },
    # Test with property type
    {
        "name": "Commercial Real Estate",
        "payload": {
            "query": "Is this a good area for commercial real estate? 40.7128, -74.0060"
        }
    }
]
```

### 2. Run Tests to Verify

Run your test client with the new test cases to verify the functionality works correctly.

### 3. Check Log Output

Make sure your system correctly identifies the query type and routes it to the right analyzer.

### 4. Review Analysis Output

Check that the analysis includes the data from your new service and provides useful insights.

## Conclusion

By following these steps, you can extend the Locas with new analyzers and tools. This modular approach allows you to:

1. Add new query types (like real estate analysis)
2. Integrate new data sources (like property market data)
3. Create new tools for the OpenAI model to use
4. Expand the capabilities of the system without major architectural changes

Remember to update tests when adding new functionality to ensure everything works correctly together.