import os
import json
import httpx
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup

class SearchService:
    """Service for web search functionality using Serper API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key."""
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        self.serper_url = "https://google.serper.dev/search"
    
    async def search_web(self, query: str, num_results: int = 8) -> Dict[str, Any]:
        """
        Search the web using Serper API.
        
        Args:
            query: The search query
            num_results: Number of results to return (default: 5)
            
        Returns:
            Search results dictionary
        """
        payload = json.dumps({"q": query, "num": num_results})
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.serper_url, headers=headers, data=payload, timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                return {"organic": []}
            except Exception as e:
                print(f"Search error: {str(e)}")
                return {"organic": [], "error": str(e)}
    
    async def fetch_url_content(self, url: str) -> str:
        """
        Fetch and extract text content from a URL.
        
        Args:
            url: The URL to fetch
            
        Returns:
            Extracted text content
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get text
                text = soup.get_text(separator="\n")
                
                # Clean up text - remove multiple newlines and spaces
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = "\n".join(chunk for chunk in chunks if chunk)
                
                return text
            except httpx.TimeoutException:
                return "Timeout error while fetching content"
            except Exception as e:
                return f"Error fetching content: {str(e)}"
    
    async def search_and_extract(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Search for a query and extract content from the top results.
        
        Args:
            query: The search query
            max_results: Maximum number of results to process
            
        Returns:
            List of dictionaries with title, link, and content
        """
        search_results = await self.search_web(query)
        print("search_results================", search_results)
        
        results = []
        if "organic" in search_results:
            for i, result in enumerate(search_results["organic"]):
                if i >= max_results:
                    break
                    
                title = result.get("title", "No title")
                link = result.get("link", "")
                snippet = result.get("snippet", "")
                
                if link:
                    try:
                        content = await self.fetch_url_content(link)
                        # Limit content length to avoid excessive data
                        content = content[:10000] + "..." if len(content) > 10000 else content
                    except Exception as e:
                        content = f"Error extracting content: {str(e)}"
                else:
                    content = snippet
                
                results.append({
                    "title": title,
                    "link": link,
                    "content": content
                })
        
        return results