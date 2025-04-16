from typing import Dict, Union, Optional

from models import ServiceConfig, MultiLocationResults, LocationError, LocationResults, EnvResult
from services import PlacesService, EnvironmentService, OpenAIService
from assistant.utils import ResultFormatter

class LandAnalyzer:
    """Analyzer for land purchase location suitability."""
    
    def __init__(self, places_service: PlacesService, env_service: EnvironmentService, openai_service: OpenAIService):
        """Initialize with required services."""
        self.places_service = places_service
        self.env_service = env_service
        self.openai_service = openai_service
        
        # Categories of interest for land purchase analysis
        self.categories = [
            'police', 'schools', 'hospitals', 'transportation', 
            'shopping', 'parks', 'restaurants', 'banks', 
            'government', 'water_bodies'
        ]
    
    async def analyze_location(self, latitude: float, longitude: float, user_query: str,
                         radius: Optional[int] = None, config: ServiceConfig = None) -> str:
        """
        Analyze location suitability for land purchase.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            user_query: The original user query
            radius: Search radius (optional)
            config: Service configuration
            
        Returns:
            Analysis result as a string
        """
        try:
            # Collect data for all relevant categories
            result = await self._collect_location_data(latitude, longitude, radius, config)
            
            # Format the result for analysis
            if isinstance(result, LocationError):
                return f"Error analyzing location: {result.error_message}"
            
            formatted_result = ResultFormatter.format_multi_location_results(result)
            
            # Send to OpenAI for analysis
            analysis = await self.openai_service.analyze_land_purchase(
                latitude, longitude, user_query, formatted_result
            )
            
            return analysis
        except Exception as e:
            return f"Error analyzing location for land purchase: {str(e)}"
    
    async def _collect_location_data(self, latitude: float, longitude: float, 
                              radius: Optional[int] = None, 
                              config: ServiceConfig = None) -> Union[MultiLocationResults, LocationError]:
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
                error_message=f"Error collecting location data: {str(e)}",
                location={"latitude": latitude, "longitude": longitude}
            )