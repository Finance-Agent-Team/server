from pydantic import BaseModel, Field
from tavily import TavilyClient
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TavilySearchToolInput(BaseModel):
    query: str = Field(description="Search query")
    max_results: int = Field(default=5, description="Maximum number of results")
    include_domains: Optional[List[str]] = Field(default=None, description="Domains to include in search")

def search_tavily_news(query: str, max_results: int = 3, include_domains: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Search for news articles using Tavily Search API.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        include_domains: List of domains to include in search
        
    Returns:
        Dictionary containing search results and metadata
    """
    try:
        logger.info(f"Searching Tavily for: {query}")
        
        client = TavilyClient()
        
        search_params = {
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": True
        }
        
        if include_domains:
            search_params["include_domains"] = include_domains
        
        response = client.search(**search_params)
        
        articles = []
        for item in response.get("results", []):
            try:
                # Extract publish date from content or use current time
                published_at = datetime.now()
                if "published" in item:
                    try:
                        published_at = datetime.fromisoformat(item["published"].replace("Z", "+00:00"))
                    except:
                        pass
                
                article = {
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "url": item.get("url", ""),
                    "published_at": published_at,
                    "source": "tavily",
                    "metadata": {
                        "score": item.get("score", 0),
                        "raw_content": (item.get("raw_content") or "")#[:4000]  # Limit raw content
                    }
                }
                articles.append(article)
            except Exception as e:
                logger.warning(f"Error processing Tavily search result: {e}")
                continue
        
        return {
            "success": True,
            "articles": articles,
            "total_found": len(articles),
            "source": "tavily",
            "answer": response.get("answer", ""),
            "fetched_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching Tavily for '{query}': {e}")
        return {
            "success": False,
            "articles": [],
            "error": str(e),
            "source": "tavily"
        }