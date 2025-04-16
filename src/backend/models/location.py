from typing import List, Optional, Dict, Any

class PointOfInterest:
    """Represents a point of interest from location search."""
    def __init__(self, name: str, address: str, rating: Optional[float] = None, 
                 types: List[str] = None, distance: Optional[float] = None):
        self.name = name
        self.address = address
        self.rating = rating
        self.types = types or []
        self.distance = distance
    
    def __str__(self):
        return f"{self.name}: {self.address}"

class LocationResults:
    """Collection of points of interest from a search."""
    def __init__(self, places: List[PointOfInterest], total_found: int, search_term: str):
        self.places = places
        self.total_found = total_found
        self.search_term = search_term

class LocationError:
    """Error from location-based services."""
    def __init__(self, error_message: str, location: Optional[Dict[str, float]] = None):
        self.error_message = error_message
        self.location = location or {}

class MultiLocationResults:
    """Results from multiple location-based searches."""
    def __init__(self, category_results: Dict[str, LocationResults], location: Dict[str, float] = None):
        self.category_results = category_results
        self.location = location or {}