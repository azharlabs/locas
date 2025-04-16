from typing import Dict, Any, List

class ToolBuilder:
    """Helper for building OpenAI tool definitions."""
    
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
            ToolBuilder.get_environmental_data_tool(),
            ToolBuilder.search_web_tool()
        ]
    
    @staticmethod
    def find_places_tool() -> Dict[str, Any]:
        """Create the find_places tool definition."""
        return ToolBuilder._convert_to_tool_format(
            name="find_places",
            description="Find places of a specific type near the specified location.",
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
                    "place_type": {
                        "type": "string",
                        "description": "Type of place to search for (e.g., \"park\", \"hospital\", \"gym\")"
                    },
                    "radius": {
                        "type": "integer",
                        "description": "Search radius in meters (default: 1500)"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Additional keywords to refine the search (optional)"
                    }
                },
                "required": ["latitude", "longitude", "place_type"]
            }
        )
    
    @staticmethod
    def analyze_location_suitability_tool() -> Dict[str, Any]:
        """Create the analyze_location_suitability tool definition."""
        return ToolBuilder._convert_to_tool_format(
            name="analyze_location_suitability",
            description="Analyze the suitability of a location for land purchase by checking multiple categories of nearby amenities.",
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
                    }
                },
                "required": ["latitude", "longitude"]
            }
        )
    
    @staticmethod
    def analyze_business_viability_tool() -> Dict[str, Any]:
        """Create the analyze_business_viability tool definition."""
        return ToolBuilder._convert_to_tool_format(
            name="analyze_business_viability",
            description="Analyze the viability of opening a business at the specified location by checking foot traffic generators and competition.",
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
                    "business_type": {
                        "type": "string",
                        "description": "Type of business to analyze (e.g., \"tea stall\", \"coffee shop\", \"restaurant\")",
                        "default": "business"
                    }
                },
                "required": ["latitude", "longitude"]
            }
        )
    
    @staticmethod
    def get_environmental_data_tool() -> Dict[str, Any]:
        """Create the get_environmental_data tool definition."""
        return ToolBuilder._convert_to_tool_format(
            name="get_environmental_data",
            description="Get environmental data for the specified location.",
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
                    "data_type": {
                        "type": "string",
                        "description": "Type of data to return - \"air\" for air quality, \"pollen\" for pollen data, or \"both\" (default)",
                        "enum": ["air", "pollen", "both"]
                    }
                },
                "required": ["latitude", "longitude"]
            }
        )
    
    @staticmethod
    def search_web_tool() -> Dict[str, Any]:
        """Create the search_web tool definition."""
        return ToolBuilder._convert_to_tool_format(
            name="search_web",
            description="Search the web for current information related to the query.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find information on the web"
                    }
                },
                "required": ["query"]
            }
        )
    
    @staticmethod
    def _convert_to_tool_format(name: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Convert parameters to the OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }