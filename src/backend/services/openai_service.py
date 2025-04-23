import json
import logging
from openai import AsyncOpenAI
from typing import Dict, Any, List, Optional

import re
import urllib.parse

class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self, api_key: str):
        """Initialize with API key."""
        self.client = AsyncOpenAI(api_key=api_key)
        
        self.formatter_system_prompt = """
        You are a helpful assistant that formats environmental data into clear, readable messages.
        Your job is to take structured data about air quality and pollen forecasts and present it
        in a way that's informative, well-organized, and easy for people to understand.
        
        - Make the information scannable with bullet points or sections
        - Highlight key information that would be important to people with allergies or sensitivity to air pollution
        - Use plain language that anyone can understand
        - If there are health recommendations, make them clear and actionable
        """
        
        self.land_analysis_system_prompt = """
        You are a real estate location analyst providing insights about locations.
        Your analysis should be detailed, balanced, and objective, focusing on both 
        advantages and potential concerns for land purchase decisions.
        
        For each factor you analyze, you must provide a numeric rating on a scale of 1-10,
        where 1 is extremely poor and 10 is excellent. You must also provide an overall
        rating for the location at the end of your analysis.
        
        Present the ratings in a clear format like:
        - Factor Name: Description of analysis... [Rating: X/10]
        
        End with an "Overall Rating: X/10" that takes all factors into account.
        """
        
        self.business_analysis_system_prompt = """
        You are a small business location analyst specializing in retail and food service businesses.
        You provide insights about locations for business opportunities, with 
        consideration for foot traffic, competition, and business viability.
        
        For each factor you analyze, you must provide a numeric rating on a scale of 1-10,
        where 1 is extremely poor and 10 is excellent. You must also provide an overall
        rating for the location at the end of your analysis.
        
        Present the ratings in a clear format like:
        - Factor Name: Description of analysis... [Rating: X/10]
        
        End with an "Overall Rating: X/10" that takes all factors into account.
        """
    
    async def format_environmental_data(self, raw_data: Dict[str, Any]) -> str:
        """Format raw environmental data into a human-readable message."""
        # Check if raw_data is a string and try to parse it
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return "Error: Invalid environmental data format"
        
        if not raw_data or (not raw_data.get('air_quality') and not raw_data.get('pollen_forecast')):
            return "No environmental data available for this location."
        
        # Format the prompt with the raw data
        prompt = f"""
        Please format the following environmental data into a human-readable message:
        
        {json.dumps(raw_data, indent=2)}
        
        The message should be clear, informative, and easy to understand.
        Highlight key information and use formatting like bullet points to make it scannable.
        If there are health recommendations, make them prominent.
        """
        
        try:
            # Use OpenAI to format the message
            response = await self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": self.formatter_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            # Fallback formatting if the OpenAI call fails
            message_parts = []
            
            if air_data := raw_data.get('air_quality'):
                for idx in air_data.get('indexes', []):
                    message_parts.append(f"Air Quality: {idx.get('category', 'Unknown')} ({idx.get('aqi', 'N/A')})")
                    break
            
            if pollen_data := raw_data.get('pollen_forecast'):
                daily_info = pollen_data.get('dailyInfo', [])
                if daily_info and daily_info[0].get('pollenTypeInfo'):
                    pollen_levels = []
                    for p_type in daily_info[0]['pollenTypeInfo']:
                        level = p_type.get('indexInfo', {}).get('category', 'Unknown')
                        pollen_levels.append(f"{p_type.get('displayName', 'Unknown')}: {level}")
                    
                    if pollen_levels:
                        message_parts.append(f"Pollen Levels: {', '.join(pollen_levels)}")
            
            if not message_parts:
                return "Environmental data available but could not be formatted."
            
            return " | ".join(message_parts)
            
    async def analyze_land_purchase(self, latitude: float, longitude: float, user_query: str, location_data: str) -> str:
        """
        Analyze location data for land purchase suitability.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            user_query: The original user query
            location_data: Formatted location data to analyze
            
        Returns:
            Analysis as a string with embedded Google Maps links
        """
        # Parse the location data to extract place information
        parsed_places = self._extract_places_from_data(location_data)
        
        analysis_prompt = f"""
        A user at coordinates ({latitude}, {longitude}) is asking: "{user_query}"
        
        They want to know if this is a good place to buy land.
        
        Here is data about the surrounding area:
        
        {location_data}
        
        Please provide a detailed analysis of the suitability of this location for land purchase. 
        
        For each of the following factors, provide a detailed analysis AND a numeric rating on a scale of 1-10:
        
        1. Essential Services [Rating: X/10] - Proximity to schools, hospitals, police, fire stations
        2. Amenities [Rating: X/10] - Access to shopping, restaurants, parks, entertainment
        3. Transportation [Rating: X/10] - Public transit options, road access, walkability
        4. Environmental Factors [Rating: X/10] - Air quality, green spaces, water bodies, pollution
        5. Neighborhood Profile [Rating: X/10] - Overall character, development stage, growth potential
        
        Highlight both advantages and potential concerns for each factor.
        
        Conclude with an Overall Rating (scale of 1-10) and a summary assessment of whether this location would be good for land purchase.
        
        Format your response with clear section headings and make the ratings visually distinguishable.
        
        VERY IMPORTANT: When you mention any specific place (school, hospital, park, mall, etc.), include the place's exact name and put [PLACE] tag before it, like this: [PLACE]Central Park. This will be used to generate map links.
        
        Include a Google Maps link for the main location at the beginning of your analysis in this format: "Location: [MAP]{latitude},{longitude}"
        """
        
        try:
            analysis_response = await self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": self.land_analysis_system_prompt},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Process the output to add Google Maps links
            analysis_text = analysis_response.choices[0].message.content
            enhanced_analysis = self._add_map_links(analysis_text, latitude, longitude, parsed_places)
            
            return enhanced_analysis
        except Exception as e:
            return f"Error generating land purchase analysis: {str(e)}"
    
    async def analyze_business_viability(self, latitude: float, longitude: float, 
                                  user_query: str, location_data: str, 
                                  business_type: str = "tea stall") -> str:
        """
        Analyze location data for business viability.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            user_query: The original user query
            location_data: Formatted location data to analyze
            business_type: Type of business to analyze
            
        Returns:
            Analysis as a string with embedded Google Maps links
        """
        # Parse the location data to extract place information
        parsed_places = self._extract_places_from_data(location_data)
        
        analysis_prompt = f"""
        A user at coordinates ({latitude}, {longitude}) is asking: "{user_query}"
        
        They want to know if this is a good place to open a {business_type}.
        
        Here is data about the surrounding area:
        
        {location_data}
        
        Please provide a detailed analysis of the viability of opening a {business_type} at this location.
        
        For each of the following factors, provide a detailed analysis AND a numeric rating on a scale of 1-10:
        
        1. Customer Traffic [Rating: X/10] - Foot traffic generators like schools, offices, transit stations
        2. Competition [Rating: X/10] - Existing similar businesses, market saturation, competitive advantage
        3. Demographics [Rating: X/10] - Population density, income levels, target customer presence
        4. Location Accessibility [Rating: X/10] - Visibility, parking, public transit, walkability
        5. Growth Potential [Rating: X/10] - Area development plans, economic trends, future prospects
        
        Highlight both advantages and potential challenges for each factor.
        
        Conclude with an Overall Rating (scale of 1-10) and a summary assessment of whether this location would be good for a {business_type}.
        
        Format your response with clear section headings and make the ratings visually distinguishable.
        
        VERY IMPORTANT: When you mention any specific place (school, hospital, park, mall, etc.), include the place's exact name and put [PLACE] tag before it, like this: [PLACE]Central Park. This will be used to generate map links.
        
        Include a Google Maps link for the main location at the beginning of your analysis in this format: "Location: [MAP]{latitude},{longitude}"
        """
        
        try:
            analysis_response = await self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": self.business_analysis_system_prompt},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Process the output to add Google Maps links
            analysis_text = analysis_response.choices[0].message.content
            enhanced_analysis = self._add_map_links(analysis_text, latitude, longitude, parsed_places)
            
            return enhanced_analysis
        except Exception as e:
            return f"Error generating business viability analysis: {str(e)}"
            
    def _extract_places_from_data(self, location_data: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract place information from the structured location data.
        
        Args:
            location_data: The formatted location data
            
        Returns:
            Dictionary mapping place names to their coordinates and details
        """
        places_dict = {}
        
        # Use regex to find place entries in the formatted data
        place_pattern = r"(.+?)\s*\((.+?)(?:,\s*(.+?))?(?:,\s*(.+?))?(?:,\s*(.+?))?\)"
        
        try:
            lines = location_data.split('\n')
            for line in lines:
                if ":" in line and "found" not in line.lower():
                    # This might be a place listing
                    matches = re.findall(place_pattern, line)
                    for match in matches:
                        name = match[0].strip()
                        if name and len(match) > 1:
                            # Extract any coordinates or address info
                            details = {
                                "name": name,
                                "address": ", ".join([m for m in match[1:] if m])
                            }
                            
                            # Look for lat/lng in the line
                            coords = re.search(r"(\d+\.\d+),\s*(\d+\.\d+)", line)
                            if coords:
                                details["lat"] = coords.group(1)
                                details["lng"] = coords.group(2)
                                
                            places_dict[name.lower()] = details
        except Exception as e:
            logging.info(f"Error extracting places: {str(e)}")
            
        return places_dict
    
    def _add_map_links(self, analysis_text: str, latitude: float, longitude: float, 
                      parsed_places: Dict[str, Dict[str, Any]]) -> str:
        """
        Process the analysis text to add Google Maps links.
        
        Args:
            analysis_text: The raw analysis text
            latitude: The main location latitude
            longitude: The main location longitude
            parsed_places: Dictionary of places extracted from the data
            
        Returns:
            Enhanced analysis text with embedded map links
        """
        # Add the main location map link if not already present
        if "[MAP]" in analysis_text:
            analysis_text = analysis_text.replace(f"[MAP]{latitude},{longitude}", 
                                                f"[View on Google Maps](https://www.google.com/maps?q={latitude},{longitude})")
        else:
            # Add the map link at the beginning if not present
            map_link = f"\n**Location: [View on Google Maps](https://www.google.com/maps?q={latitude},{longitude})**\n\n"
            analysis_text = map_link + analysis_text
        
        # Find all [PLACE] tags and add Google Maps links
        place_pattern = r'\[PLACE\](.*?)(?=\s|\.|\,|\)|\]|$)'
        
        def replace_place(match):
            place_name = match.group(1).strip()
            
            # Check if we have this place in our parsed data
            place_info = parsed_places.get(place_name.lower())
            
            if place_info and "lat" in place_info and "lng" in place_info:
                # We have coordinates
                map_url = f"https://www.google.com/maps?q={place_info['lat']},{place_info['lng']}"
            else:
                # Use search query
                search_query = urllib.parse.quote(f"{place_name} near {latitude},{longitude}")
                map_url = f"https://www.google.com/maps/search/?api=1&query={search_query}"
                
            return f"{place_name} ([Map]({map_url}))"
            
        # Replace all [PLACE] tags with the place name + map link
        enhanced_text = re.sub(place_pattern, replace_place, analysis_text)
        
        return enhanced_text