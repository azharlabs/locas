from typing import Dict, Optional, Tuple
import googlemaps
from geopy.geocoders import Nominatim
from openai import AsyncOpenAI

class LocationParser:
    """Parser for extracting location information from user queries using LLM."""
    
    def __init__(self, google_maps_api_key: str, openai_api_key: str):
        """
        Initialize the location parser.
        
        Args:
            google_maps_api_key: Google Maps API key for geocoding
            openai_api_key: OpenAI API key for LLM parsing
        """
        self.google_maps_api_key = google_maps_api_key
        self.openai_api_key = openai_api_key
        self.gmaps = None
        self.geolocator = None
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        
        # Initialize geocoding clients if API key is provided
        if google_maps_api_key and google_maps_api_key != "your_api_key":
            self.gmaps = googlemaps.Client(key=google_maps_api_key)
        
        # Nominatim as fallback geocoder
        self.geolocator = Nominatim(user_agent="location_assistant")
    
    async def parse_query(self, user_query: str) -> Tuple[str, Optional[Dict[str, float]]]:
        """
        Parse the user query to extract the actual query and location coordinates using LLM.
        
        Args:
            user_query: The full user query which may include location information
            
        Returns:
            Tuple containing (clean_query, coordinates_dict)
            - clean_query: User query with location information removed
            - coordinates_dict: Dictionary with 'lat' and 'lng' keys, or None if no location found
        """
        # Use LLM to extract location information
        extraction_result = await self._extract_location_with_llm(user_query)
        
        # Initialize variables
        clean_query = user_query
        coordinates = None
        
        # Process the extraction result
        if extraction_result:
            location_type = extraction_result.get('type')
            location_value = extraction_result.get('value')
            
            if location_type == 'coordinates' and 'lat' in location_value and 'lng' in location_value:
                # Direct coordinates were found
                coordinates = location_value
                clean_query = extraction_result.get('clean_query', user_query)
            
            elif location_type == 'map_url' and location_value:
                # Google Maps URL was found
                coordinates = await self._extract_coordinates_from_maps_url_llm(location_value)
                clean_query = extraction_result.get('clean_query', user_query)
            
            elif location_type == 'address' and location_value:
                # Address was found, use geocoding
                coordinates = self.extract_coordinates_from_search(location_value)
                clean_query = extraction_result.get('clean_query', user_query)
        
        # If LLM extraction failed, fall back to the address extraction
        if not coordinates:
            # Try to extract location from the query as an address
            address_candidates = self.extract_potential_addresses(user_query)
            
            for address in address_candidates:
                coordinates = self.extract_coordinates_from_search(address)
                if coordinates:
                    # Remove the address from the query (simple replacement)
                    clean_query = user_query.replace(address, "").strip()
                    break
        
        return clean_query, coordinates
    
    async def _extract_location_with_llm(self, user_query: str) -> Optional[Dict]:
        """
        Extract location information from user query using LLM.
        
        Args:
            user_query: The user query to analyze
            
        Returns:
            Dictionary with extraction results or None if extraction failed
        """
        try:
            prompt = f"""
            Analyze the following query and extract any location information:
            
            "{user_query}"
            
            Identify if it contains:
            1. Specific coordinates (latitude and longitude)
            2. A Google Maps URL
            3. A physical address or named location
            
            Format your response as a JSON object with these fields:
            - type: "coordinates", "map_url", "address", or "none"
            - value: The extracted value (coordinates as {{lat: float, lng: float}}, URL as string, or address as string)
            - clean_query: The original query with the location information removed
            
            Only return the JSON object, no additional text.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a location information extraction assistant. Extract location data from user queries and format as specified."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            # Extract and parse the JSON response
            extraction_text = response.choices[0].message.content
            import json
            extraction_result = json.loads(extraction_text)
            
            return extraction_result
            
        except Exception as e:
            print(f"Error using LLM for extraction: {str(e)}")
            return None
    
    async def _extract_coordinates_from_maps_url_llm(self, url: str) -> Optional[Dict[str, float]]:
        """
        Extract coordinates from a Google Maps URL using LLM
        
        Args:
            url: Google Maps URL
            
        Returns:
            Dictionary with lat, lng keys or None if extraction failed
        """
        try:
            prompt = f"""
            Extract the latitude and longitude coordinates from this Google Maps URL:
            
            "{url}"
            
            Format your response as a JSON object with:
            - lat: The latitude as a float
            - lng: The longitude as a float
            
            If you cannot find coordinates, return {{"lat": null, "lng": null}}
            Only return the JSON object, no additional text.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a URL parsing assistant that extracts coordinates from Google Maps URLs."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            # Extract and parse the JSON response
            extraction_text = response.choices[0].message.content
            import json
            result = json.loads(extraction_text)
            
            # Verify the coordinates are valid
            if result.get('lat') is not None and result.get('lng') is not None:
                lat = float(result['lat'])
                lng = float(result['lng'])
                
                # Validate coordinate ranges
                if abs(lat) <= 90 and abs(lng) <= 180:
                    return {'lat': lat, 'lng': lng}
            
            return None
            
        except Exception as e:
            print(f"Error extracting coordinates from URL with LLM: {str(e)}")
            return None
    
    def extract_coordinates_from_search(self, search_text: str) -> Optional[Dict[str, float]]:
        """
        Extract coordinates from a search text (address or direct coordinates)
        
        Args:
            search_text: Address or coordinates string
            
        Returns:
            Dictionary with lat, lng keys or None if extraction failed
        """
        try:
            # Use geocoding to convert address to coordinates
            if self.gmaps:
                # Try Google Maps geocoding first
                geocode_result = self.gmaps.geocode(search_text)
                if geocode_result and len(geocode_result) > 0:
                    location = geocode_result[0]['geometry']['location']
                    return {
                        'lat': location['lat'],
                        'lng': location['lng']
                    }
            
            # Fallback to Nominatim geocoding
            if self.geolocator:
                location = self.geolocator.geocode(search_text)
                if location:
                    return {
                        'lat': location.latitude,
                        'lng': location.longitude
                    }
            
            return None
        except Exception as e:
            print(f"Error extracting coordinates from search: {e}")
            return None
    
    def extract_potential_addresses(self, text: str) -> list:
        """
        Extract potential addresses from text.
        This is a simplified implementation used as a fallback.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of potential address strings
        """
        # Simple approach: add the full text as a candidate
        candidates = [text.strip()]
        
        return candidates