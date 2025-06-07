from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.1, max_tokens: int = 2000):
        """Initialize the LLM service."""
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def analyze_news_articles(self, articles: List[Dict[str, Any]], company_symbol: str) -> Dict[str, Any]:
        """Analyze news articles using the LLM."""
        try:
            # Prepare analysis prompt
            articles_text = "\n\n".join([
                f"Title: {article['title']}\nContent: {article['content'][:500]}..."
                for article in articles[:5]  # Limit to top 5 articles
            ])
            
            analysis_prompt = f"""
            Analyze the following financial news articles for {company_symbol}:
            
            {articles_text}
            
            Provide a comprehensive analysis including:
            1. Overall sentiment (positive, negative, neutral)
            2. Key themes and topics
            3. Market implications
            4. Risk factors mentioned
            5. Investment considerations
            
            Format your response as a structured analysis.
            """
            
            # Get LLM analysis
            messages = [
                SystemMessage(content="You are a financial news analyst. Provide objective, comprehensive analysis of news articles."),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            return {
                "analysis_type": "comprehensive_news_analysis",
                "findings": {
                    "analysis_text": response.content,
                    "articles_analyzed": len(articles),
                    "company_symbol": company_symbol
                },
                "confidence_score": 0.8,  # Could be computed based on article quality/quantity
                "model_version": "gpt-4"
            }
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            raise 