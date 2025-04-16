import httpx
from typing import Dict, Any, Union, Optional

from models import ServiceConfig, PointOfInterest, LocationResults, LocationError

class PlacesService:
    """Service for interacting with Google Places API."""
    
    def __init__(self):
        """Initialize the places service."""
        self.amenity_types = {
            'police': 'police',
            'schools': 'school',
            'hospitals': 'hospital',
            'transportation': 'transit_station',
            'shopping': 'shopping_mall',
            'parks': 'park',
            'restaurants': 'restaurant',
            'banks': 'bank',
            'hotels': 'lodging',
            'gas_stations': 'gas_station',
            'atms': 'atm',
            'government': 'local_government_office',
            'grocery': 'grocery_or_supermarket',
            'cafes': 'cafe',
            'pharmacies': 'pharmacy',
            'water_bodies': 'natural_feature'
        }
    
    async def find_places(self, latitude: float, longitude: float, place_type: str,
                      radius: Optional[int] = None, keyword: Optional[str] = None,
                      config: ServiceConfig = None) -> Union[LocationResults, LocationError]:
        """
        Find places near the specified location.
        
        Args:
            latitude: The latitude coordinate
            longitude: The longitude coordinate
            place_type: Type of place to search for
            radius: Search radius in meters (optional)
            keyword: Additional keyword for search (optional)
            config: Service configuration
            
        Returns:
            LocationResults or LocationError
        """
        try:
            # Prepare the search parameters
            radius = radius or config.default_radius
            
            # If place_type is in our predefined type mapping, use the Google Places type
            if place_type in self.amenity_types:
                google_place_type = self.amenity_types[place_type]
            else:
                # Otherwise use it directly
                google_place_type = place_type
            
            # Make the API request
            response = await self._make_places_request(
                config=config,
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                type=google_place_type,
                keyword=keyword
            )
            
            # Process the response
            places = self._process_places_response(response, latitude, longitude, place_type)
            
            # If no places found, return error
            if places.total_found == 0:
                return LocationError(
                    error_message=f"No {place_type} found near the provided location (lat: {latitude}, lng: {longitude})",
                    location={"latitude": latitude, "longitude": longitude}
                )
                
            return places
        except Exception as e:
            return LocationError(
                error_message=f"Error finding {place_type}: {str(e)}",
                location={"latitude": latitude, "longitude": longitude}
            )
    
    async def _make_places_request(self, config: ServiceConfig, latitude: float, longitude: float,
                             radius: int, type: str = None, keyword: str = None) -> Dict[str, Any]:
        """Make a request to the Google Places API."""
        
        try:
            # Build the URL for the Places API Nearby Search
            base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            
            # Required parameters
            params = {
                "location": f"{latitude},{longitude}",
                "radius": radius,
                "key": config.api_key,
                "language": config.default_language,
            }
            
            # Optional parameters
            if type:
                params["type"] = type
            if keyword:
                params["keyword"] = keyword
            
            # Make the HTTP request
            response = await config.http_client.get(base_url, params=params)
            
            # Raise an exception if the request failed
            response.raise_for_status()
            
            # Return the JSON response
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise ValueError(f"API key invalid or quota exceeded: {e}")
            elif e.response.status_code == 404:
                raise ValueError(f"Service not available: {e}")
            else:
                raise ValueError(f"HTTP error occurred: {e}")
        except httpx.RequestError as e:
            raise ValueError(f"Network error occurred: {e}")
        except Exception as e:
            raise ValueError(f"Error making request: {e}")
    
    def _process_places_response(self, response: Dict[str, Any], latitude: float, 
                          longitude: float, search_term: str) -> LocationResults:
        """Process the Google Places API response into a LocationResults object."""
        
        # Extract results
        results = response.get("results", [])
        
        # Convert each result to a PointOfInterest
        places = []
        for place in results:
            poi = PointOfInterest(
                name=place.get("name", "Unnamed"),
                address=place.get("vicinity", "No address provided"),
                rating=place.get("rating"),
                types=place.get("types", []),
                # We could calculate distance using the haversine formula
                distance=None
            )
            places.append(poi)
        
        # Create the LocationResults
        return LocationResults(
            places=places,
            total_found=len(places),
            search_term=search_term
        )