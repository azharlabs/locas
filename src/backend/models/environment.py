from typing import List, Optional, Dict

class AirQualityIndex:
    """Air quality index data for a specific pollutant or standard."""
    def __init__(self, display_name: str, value: int, category: str, description: Optional[str] = None):
        self.display_name = display_name
        self.value = value
        self.category = category
        self.description = description

class AirQualityData:
    """Collection of air quality indices with timestamp."""
    def __init__(self, indexes: List[AirQualityIndex], timestamp: str):
        self.indexes = indexes
        self.timestamp = timestamp

class PollenType:
    """Information about a specific pollen type."""
    def __init__(self, name: str, level: str, in_season: bool, recommendations: Optional[List[str]] = None):
        self.name = name
        self.level = level
        self.in_season = in_season
        self.recommendations = recommendations or []

class PollenForecastData:
    """Collection of pollen type data for a forecast."""
    def __init__(self, types: List[PollenType], date: str):
        self.types = types
        self.date = date

class EnvResult:
    """Combined environmental data for a location."""
    def __init__(self, air_quality: Optional[AirQualityData] = None, 
                 pollen_forecast: Optional[PollenForecastData] = None,
                 location: Dict[str, float] = None, 
                 message: str = ""):
        self.air_quality = air_quality
        self.pollen_forecast = pollen_forecast
        self.location = location or {}
        self.message = message