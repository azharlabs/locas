from typing import Dict, Union, Optional

from models import ServiceConfig, MultiLocationResults, LocationError, LocationResults, EnvResult
from services import PlacesService, EnvironmentService, OpenAIService
from assistant.utils import ResultFormatter

class LocalBusinessAnalyzer:
    """Analyzer for local business location viability."""
    
    def __init__(self, places_service: PlacesService, env_service: EnvironmentService, openai_service: OpenAIService):
        """Initialize with required services."""
        self.places_service = places_service
        self.env_service = env_service
        self.openai_service = openai_service
        
        # Categories relevant to local business analysis
        self.categories = [
            'schools', 'hospitals', 'transportation', 'shopping', 
            'parks', 'government', 'cafes', 'restaurants'
        ]
    
    async def analyze_location(self, latitude: float, longitude: float, user_query: str,
                         radius: Optional[int] = None, config: ServiceConfig = None,
                         business_type: str = "tea stall") -> str:
        """
        Analyze location viability for a local business.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            user_query: The original user query
            radius: Search radius (optional)
            config: Service configuration
            business_type: Type of business to analyze (default: "tea stall")
            
        Returns:
            Analysis result as a string
        """
        try:
            # Collect data for all relevant categories
            result = await self._collect_location_data(latitude, longitude, radius, config, business_type)
            
            # Format the result for analysis
            if isinstance(result, LocationError):
                return f"Error analyzing location: {result.error_message}"
            
            formatted_result = ResultFormatter.format_multi_location_results(result)
            
            # Send to OpenAI for analysis
            analysis = await self.openai_service.analyze_business_viability(
                latitude, longitude, user_query, formatted_result, business_type
            )
            
            return analysis
        except Exception as e:
            return f"Error analyzing location for {business_type} viability: {str(e)}"
    
    async def _collect_location_data(self, latitude: float, longitude: float, 
                              radius: Optional[int] = None, 
                              config: ServiceConfig = None,
                              business_type: str = "tea stall") -> Union[MultiLocationResults, LocationError]:
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
            
            # Check for competitors based on business type
            if business_type == "tea stall":
                competitors_type = "cafe"
                search_keyword = "tea"
            elif business_type == "restaurant":
                competitors_type = "restaurant"
                search_keyword = None
            elif business_type == "coffee shop":
                competitors_type = "cafe"
                search_keyword = "coffee"
            else:
                # Default case
                competitors_type = "store"
                search_keyword = business_type
            
            # Specifically look for competing businesses
            competitors_result = await self.places_service.find_places(
                latitude=latitude,
                longitude=longitude,
                place_type=competitors_type,
                keyword=search_keyword,
                radius=radius,
                config=config
            )
            
            if isinstance(competitors_result, LocationResults):
                category_results["competition"] = competitors_result
            else:
                category_results["competition"] = LocationResults(
                    places=[],
                    total_found=0,
                    search_term="competition"
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
                error_message=f"Error collecting location data: {str(e)}",
                location={"latitude": latitude, "longitude": longitude}
            )