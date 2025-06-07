"""
Demo script showcasing the integration of Tavily news search with LLM analysis.
This demonstrates how to fetch financial news articles and analyze them using GPT-4.
"""

from tavily_search_news import search_tavily_news
from llm_service import LLMService
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_and_analyze_news(company_symbol: str, query: str = None, max_results: int = 5) -> Dict[str, Any]:
    """
    Fetch news articles for a company and analyze them using the LLM service.
    
    Args:
        company_symbol: The stock symbol of the company (e.g., 'AAPL')
        query: Optional custom search query. If None, uses company symbol
        max_results: Maximum number of articles to fetch and analyze
    
    Returns:
        Dictionary containing both search results and analysis
    """
    # Initialize services
    llm_service = LLMService()
    
    # Prepare search query if not provided
    if query is None:
        query = f"Latest news and developments about {company_symbol} stock"
    
    # Define trusted financial news domains
    domains = [
        "bloomberg.com",
        "reuters.com",
        "wsj.com",
        "cnbc.com",
        "marketwatch.com"
    ]
    
    # Fetch news articles
    print(f"\nFetching news for {company_symbol}...")
    search_results = search_tavily_news(
        query=query,
        max_results=max_results,
        include_domains=domains
    )
    
    if not search_results["success"]:
        raise Exception(f"Failed to fetch news: {search_results.get('error', 'Unknown error')}")
    
    # Prepare articles for analysis
    articles = [
        {
            "title": article["title"],
            "content": article["metadata"]["raw_content"],
            "url": article["url"],
            "published_at": article["published_at"]
        }
        for article in search_results["articles"]
    ]
    
    # Analyze articles using LLM
    print(f"\nAnalyzing {len(articles)} articles...")
    analysis_results = llm_service.analyze_news_articles(
        articles=articles,
        company_symbol=company_symbol
    )
    
    return {
        "search_results": search_results,
        "analysis": analysis_results
    }

def print_results(results: Dict[str, Any]) -> None:
    """Print the search and analysis results in a readable format."""
    print("\n" + "="*80)
    print("SEARCH AND ANALYSIS RESULTS")
    print("="*80)
    
    # Print search summary
    print("\nSearch Summary:")
    print(f"Total articles found: {results['search_results']['total_found']}")
    print(f"AI Summary: {results['search_results'].get('answer', 'No summary available')}")
    
    # Print articles
    print("\nArticles Analyzed:")
    for idx, article in enumerate(results['search_results']['articles'], 1):
        print(f"\n{idx}. {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Published: {article['published_at']}")
        print(f"   Relevance Score: {article['metadata']['score']}")
    
    # Print LLM analysis
    print("\nLLM Analysis:")
    print("-"*40)
    print(results['analysis']['findings']['analysis_text'])
    print("\nAnalysis Metadata:")
    print(f"Confidence Score: {results['analysis']['confidence_score']}")
    print(f"Model Version: {results['analysis']['model_version']}")

def main():
    """Run the demo with example companies."""
    try:
        # Example 1: Apple Inc.
        print("\nAnalyzing Google Inc. (GOOG)...")
        google_results = fetch_and_analyze_news(
            company_symbol="GOOG",
            query="Google I/O 2025",
            max_results=1
        )
        print_results(google_results)
        
        # Example 2: Tesla Inc. with custom query
        # print("\nAnalyzing Tesla Inc. (TSLA)...")
        # tesla_results = fetch_and_analyze_news(
        #     company_symbol="TSLA",
        #     query="Tesla stock performance and electric vehicle market competition",
        #     max_results=3
        # )
        # print_results(tesla_results)
        
    except Exception as e:
        print(f"\nError running demo: {str(e)}")
        print("Make sure you have set up both TAVILY_API_KEY and OPENAI_API_KEY in your environment variables.")

if __name__ == "__main__":
    main()
