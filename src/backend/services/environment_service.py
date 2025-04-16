import json
import httpx
from typing import Dict, Any, Union, Optional

from models import (
    ServiceConfig, AirQualityIndex, AirQualityData,
    PollenType, PollenForecastData, EnvResult, LocationError
)

class EnvironmentService:
    """Service for fetching environmental data."""
    
    async def get_environmental_data(self, latitude: float, longitude: float,
                                data_type: str = "both", config: ServiceConfig = None) -> Union[EnvResult, LocationError]:
        """
        Get environmental data for the specified location.
        
        Args:
            latitude: The latitude coordinate
            longitude: The longitude coordinate
            data_type: Type of data to fetch ("air", "pollen", or "both")
            config: Service configuration
            
        Returns:
            EnvResult or LocationError
        """
        try:
            air_quality_data = None
            pollen_forecast_data = None
            raw_air_quality = None
            raw_pollen_data = None
            
            # Check if the coordinates are valid
            if abs(latitude) > 90 or abs(longitude) > 180:
                raise ValueError("Invalid coordinates provided")
            
            # Get air quality data if requested
            if data_type.lower() in ["air", "both"]:
                try:
                    raw_air_quality = await self._get_air_quality(config.api_key, latitude, longitude, config.http_client)
                    if raw_air_quality:
                        air_quality_data = self._parse_air_quality_data(raw_air_quality)
                except Exception as e:
                    if data_type.lower() == "air":
                        return LocationError(
                            error_message=f"Air quality data not available for this location: {str(e)}",
                            location={"latitude": latitude, "longitude": longitude}
                        )
            
            # Get pollen forecast data if requested
            if data_type.lower() in ["pollen", "both"]:
                try:
                    raw_pollen_data = await self._get_pollen_forecast(config.api_key, latitude, longitude, 3, config.http_client)
                    if raw_pollen_data:
                        pollen_forecast_data = self._parse_pollen_data(raw_pollen_data)
                except Exception as e:
                    if data_type.lower() == "pollen":
                        return LocationError(
                            error_message=f"Pollen forecast data not available for this location: {str(e)}",
                            location={"latitude": latitude, "longitude": longitude}
                        )
            
            # If both were requested and neither is available
            if data_type.lower() == "both" and not air_quality_data and not pollen_forecast_data:
                return LocationError(
                    error_message="Environmental data is not available for this location.",
                    location={"latitude": latitude, "longitude": longitude}
                )
            
            # Prepare the raw data to pass directly to the LLM
            raw_data = {
                "location": {"latitude": latitude, "longitude": longitude}
            }
            
            if raw_air_quality:
                raw_data["air_quality"] = raw_air_quality
            
            if raw_pollen_data:
                raw_data["pollen_forecast"] = raw_pollen_data
            
            return EnvResult(
                air_quality=air_quality_data,
                pollen_forecast=pollen_forecast_data,
                location={"latitude": latitude, "longitude": longitude},
                message=json.dumps(raw_data)  # Raw data passed for formatted later
            )
        except Exception as e:
            return LocationError(
                error_message=f"Error retrieving environmental data: {str(e)}",
                location={"latitude": latitude, "longitude": longitude}
            )
    
    async def _get_air_quality(self, api_key: str, latitude: float, longitude: float, http_client: httpx.AsyncClient):
        """Get air quality data from the Google Air Quality API."""
        if api_key == "your_api_key":
            # Return sample data for testing
            return {
                'dateTime': '2025-03-24T02:00:00Z', 
                'regionCode': 'us', 
                'indexes': [
                    {
                        'code': 'uaqi', 
                        'displayName': 'Universal AQI', 
                        'aqi': 62, 
                        'aqiDisplay': '62', 
                        'color': {'red': 0.70980394, 'green': 0.8862745, 'blue': 0.11764706}, 
                        'category': 'Good air quality', 
                        'dominantPollutant': 'o3'
                    }
                ]
            }
        
        url = 'https://airquality.googleapis.com/v1/currentConditions:lookup'
        headers = {'Content-Type': 'application/json'}
        params = {'key': api_key}
        data = {
            "location": {
                "latitude": latitude,
                "longitude": longitude
            }
        }
        
        response = await http_client.post(url, headers=headers, json=data, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Error {response.status_code}: {response.text}")
    
    async def _get_pollen_forecast(self, api_key: str, latitude: float, longitude: float, days: int, http_client: httpx.AsyncClient):
        """Get pollen forecast data from the Google Pollen API."""
        if api_key == "your_api_key":
            # Return sample data for testing
            return {
                'regionCode': 'US', 
                'dailyInfo': [
                    {
                        'date': {'year': 2025, 'month': 3, 'day': 24}, 
                        'pollenTypeInfo': [
                            {
                                'code': 'GRASS', 
                                'displayName': 'Grass', 
                                'inSeason': False, 
                                'indexInfo': {
                                    'code': 'UPI', 
                                    'displayName': 'Universal Pollen Index', 
                                    'value': 1, 
                                    'category': 'Very Low'
                                }, 
                                'healthRecommendations': ["Pollen levels are very low right now. It's a great day to enjoy the outdoors!"]
                            },
                            {
                                'code': 'TREE', 
                                'displayName': 'Tree', 
                                'inSeason': True, 
                                'indexInfo': {
                                    'code': 'UPI', 
                                    'displayName': 'Universal Pollen Index', 
                                    'value': 2, 
                                    'category': 'Low'
                                }, 
                                'healthRecommendations': ["It's a good day for outdoor activities since pollen levels are low."]
                            }
                        ]
                    }
                ]
            }
        
        url = f"https://pollen.googleapis.com/v1/forecast:lookup"
        params = {
            "location.latitude": latitude,
            "location.longitude": longitude,
            "days": days,
            "key": api_key
        }
        
        response = await http_client.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Error {response.status_code}: {response.text}")
    
    def _parse_air_quality_data(self, data: dict) -> AirQualityData:
        """Parse the raw air quality data into our internal structure."""
        indexes = []
        for idx in data.get('indexes', []):
            indexes.append(AirQualityIndex(
                display_name=idx.get('displayName', ''),
                value=idx.get('aqi', 0),
                category=idx.get('category', ''),
                description=None  # Description not available in the API response
            ))
        
        return AirQualityData(
            indexes=indexes,
            timestamp=data.get('dateTime', '')
        )
    
    def _parse_pollen_data(self, data: dict) -> PollenForecastData:
        """Parse the raw pollen data into our internal structure."""
        types = []
        
        # Get the first day's data
        if data.get('dailyInfo') and len(data['dailyInfo']) > 0:
            daily_info = data['dailyInfo'][0]
            date_info = daily_info.get('date', {})
            date_str = f"{date_info.get('year', 2025)}-{date_info.get('month', 1)}-{date_info.get('day', 1)}"
            
            for pollen_type in daily_info.get('pollenTypeInfo', []):
                if 'displayName' in pollen_type:
                    index_info = pollen_type.get('indexInfo', {})
                    types.append(PollenType(
                        name=pollen_type.get('displayName', ''),
                        level=index_info.get('category', 'Unknown'),
                        in_season=pollen_type.get('inSeason', False),
                        recommendations=pollen_type.get('healthRecommendations', [])
                    ))
        
            return PollenForecastData(
                types=types,
                date=date_str
            )
        
        return PollenForecastData(types=[], date="")