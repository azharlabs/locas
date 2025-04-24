from typing import Dict, Any, Union, List
import logging
from models import LocationResults, EnvResult, LocationError, MultiLocationResults

class ResultFormatter:
    """Formatters for converting results to human-readable text."""
    
    @staticmethod
    def format_tool_result(result: Union[LocationResults, EnvResult, LocationError, MultiLocationResults, Dict[str, Any]]) -> str:
        """
        Format any result type to a human-readable string.
        
        Args:
            result: The result to format
            
        Returns:
            Formatted string representation
        """
        if isinstance(result, LocationResults):
            return ResultFormatter.format_location_results(result)
        elif isinstance(result, MultiLocationResults):
            return ResultFormatter.format_multi_location_results(result)
        elif isinstance(result, EnvResult):
            return result.message
        elif isinstance(result, LocationError):
            return f"Error: {result.error_message}"
        elif isinstance(result, dict) and "results" in result:
            # Handle web search results
            return ResultFormatter.format_web_search_results(result)
        elif isinstance(result, str):
            return result
        else:
            return f"Unexpected result type: {type(result)}"
    
    @staticmethod
    def format_location_results(result: LocationResults) -> str:
        """Format location results into a readable string."""
        places_text = "\n".join([
            f"- {place.name}: {place.address}" + 
            (f" (Rating: {place.rating}/5)" if place.rating else "") 
            for place in result.places
        ])
        return f"Found {result.total_found} {result.search_term}:\n{places_text}"
    
    @staticmethod
    def format_multi_location_results(result: MultiLocationResults) -> str:
        """Format multi-location results into a readable string."""
        parts = [f"Analysis results for location (Lat: {result.location.get('latitude')}, Lng: {result.location.get('longitude')}):\n"]
        
        for category, loc_result in result.category_results.items():
            if category == "environmental_message":
                # Skip this as it's not a LocationResults object
                continue
                
            if category == "environmental" and "environmental_message" in result.category_results:
                # Use the pre-formatted environmental message
                parts.append(f"\nEnvironmental Data:\n{result.category_results['environmental_message']}")
                continue
            
            # Format this category's results
            if loc_result.total_found > 0:
                category_name = category.replace('_', ' ').title()
                parts.append(f"\n{category_name} ({loc_result.total_found}):")
                
                # Add top 3 places in this category
                places = loc_result.places[:3]
                for place in places:
                    place_info = f"- {place.name}: {place.address}"
                    if place.rating:
                        place_info += f" (Rating: {place.rating}/5)"
                    parts.append(place_info)
                
                if loc_result.total_found > 3:
                    parts.append(f"  ...and {loc_result.total_found - 3} more")
        
        return "\n".join(parts)
    
    @staticmethod
    def format_web_search_results(result: Dict[str, Any]) -> str:
        """
        Format web search results into a readable string.
        
        Args:
            result: Dictionary containing search results
            
        Returns:
            Formatted string representation
        """
        if not result.get("results"):
            return f"No web search results found for query: {result.get('query', 'Unknown query')}"
        
        parts = [f"Web search results for: {result.get('query', 'Unknown query')}"]
        
        for idx, search_result in enumerate(result["results"], 1):
            title = search_result.get("title", "No title")
            link = search_result.get("link", "No link")
            
            # Limit content length for readability
            content = search_result.get("content", "No content")
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            parts.append(f"\n{idx}. {title}")
            parts.append(f"   URL: {link}")
            parts.append(f"   Summary: {content[:200]}...")
        
        return "\n".join(parts)