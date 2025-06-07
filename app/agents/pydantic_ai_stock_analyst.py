"""
Enhanced Stock Analyst Agent using PydanticAI Graph with MCP Integration
Combines the MCP data pulling approach with structured graph workflow
"""

from __future__ import annotations
import asyncio
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Literal
from pathlib import Path

from pydantic import BaseModel, EmailStr
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
from pydantic_ai.mcp import MCPServerStdio


# --- Pydantic Models for Data Structures ---

class StockDataPoint(BaseModel):
    """Individual stock data point"""
    date: str
    symbol: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    daily_change: Optional[float] = None
    daily_change_pct: Optional[float] = None


class MarketConditions(BaseModel):
    """Current market conditions"""
    sentiment: Literal["bullish", "bearish", "neutral"]
    volatility: Literal["high", "medium", "low"]
    trend: Literal["upward", "downward", "sideways"]
    confidence: float  # 0-1


class UserProfile(BaseModel):
    """User investment profile"""
    name: str = "Investor"
    risk_tolerance: Literal["conservative", "moderate", "aggressive"] = "moderate"
    investment_horizon: Literal["short", "medium", "long"] = "medium"
    email: Optional[EmailStr] = None


class AnalysisResult(BaseModel):
    """Final analysis result"""
    symbol: str
    recommendation: Literal["buy", "hold", "sell"]
    confidence: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    reasoning: str
    market_conditions: MarketConditions
    data_points: List[StockDataPoint]
    analysis_timestamp: datetime


# --- Graph State Management ---

@dataclass
class StockAnalysisState:
    """State that flows through the analysis graph"""
    symbol: str
    user_profile: UserProfile
    raw_data: List[StockDataPoint] = field(default_factory=list)
    market_conditions: Optional[MarketConditions] = None
    technical_analysis: Optional[str] = None
    fundamental_analysis: Optional[str] = None
    sentiment_analysis: Optional[str] = None
    final_result: Optional[AnalysisResult] = None
    mcp_agent_messages: List[ModelMessage] = field(default_factory=list)
    analysis_agent_messages: List[ModelMessage] = field(default_factory=list)


# --- MCP Setup ---

def create_mcp_server() -> Optional[MCPServerStdio]:
    """Create and configure the MCP server for stock data"""
    try:
        # You'll need to adjust this path based on your actual MCP server location
        mcp_server_path = os.getenv('MCP_STOCK_SERVER_PATH', '/path/to/stock-mcp-server/dist/index.js')
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        
        return MCPServerStdio(
            'node',
            args=[mcp_server_path],
            env={
                'ALPHA_VANTAGE_API_KEY': api_key,
                **os.environ
            }
        )
    except Exception as e:
        print(f"Warning: Could not create MCP server: {e}")
        return None


# --- Agent Creation Functions (with error handling) ---

def create_agents():
    """Create PydanticAI agents with proper error handling"""
    agents = {}
    
    # Check if Anthropic API key is available
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("Warning: ANTHROPIC_API_KEY not set. Agents will use mock responses.")
        return None
    
    try:
        mcp_server = create_mcp_server()
        mcp_servers = [mcp_server] if mcp_server else []
        
        # Data collection agent with MCP
        agents['data_agent'] = Agent(
            'anthropic:claude-3-5-sonnet-latest',
            deps_type=UserProfile,
            mcp_servers=mcp_servers,
            system_prompt="You are a data collection specialist. Use MCP tools to gather comprehensive stock data."
        )
        
        # Technical analysis agent
        agents['technical_agent'] = Agent(
            'anthropic:claude-3-5-sonnet-latest', 
            deps_type=UserProfile,
            system_prompt="You are a technical analysis expert. Analyze stock data patterns, trends, and technical indicators."
        )
        
        # Fundamental analysis agent
        agents['fundamental_agent'] = Agent(
            'anthropic:claude-3-5-sonnet-latest',
            deps_type=UserProfile, 
            system_prompt="You are a fundamental analysis expert. Evaluate company financials, market position, and intrinsic value."
        )
        
        # Sentiment analysis agent
        agents['sentiment_agent'] = Agent(
            'anthropic:claude-3-5-sonnet-latest',
            deps_type=UserProfile,
            system_prompt="You are a market sentiment analyst. Analyze news, social media, and market psychology indicators."
        )
        
        # Final recommendation agent
        agents['recommendation_agent'] = Agent(
            'anthropic:claude-3-5-sonnet-latest',
            output_type=AnalysisResult,
            deps_type=UserProfile,
            system_prompt="You are a senior investment advisor. Synthesize all analysis to provide final investment recommendations."
        )
        
        return agents
        
    except Exception as e:
        print(f"Warning: Could not create agents: {e}")
        return None


# Global agents (created lazily)
_agents = None

def get_agents():
    """Get or create agents"""
    global _agents
    if _agents is None:
        _agents = create_agents()
    return _agents


# --- Graph Nodes ---

@dataclass
class DataCollection(BaseNode[StockAnalysisState]):
    """First node: Collect raw stock data using MCP"""
    
    async def run(self, ctx: GraphRunContext[StockAnalysisState]) -> TechnicalAnalysis:
        agents = get_agents()
        
        if not agents or not agents.get('data_agent'):
            # Mock data collection when agents are not available
            print(f"Using mock data collection for {ctx.state.symbol}")
            data_points = self._create_mock_data(ctx.state.symbol)
            ctx.state.raw_data = data_points
            return TechnicalAnalysis()
        
        try:
            async with agents['data_agent'].run_mcp_servers():
                result = await agents['data_agent'].run(
                    f"Use get-daily-stock-data to collect comprehensive data for {ctx.state.symbol}. "
                    f"Get at least 30 days of historical data with open, high, low, close, and volume.",
                    deps=ctx.state.user_profile,
                    message_history=ctx.state.mcp_agent_messages
                )
                
                ctx.state.mcp_agent_messages += result.new_messages()
                
                # Parse the MCP response into structured data
                data_points = self._parse_mcp_data(result.output, ctx.state.symbol)
                ctx.state.raw_data = data_points
                
                return TechnicalAnalysis()
                
        except Exception as e:
            # Fallback to mock data on error
            print(f"Data collection failed: {e}. Using mock data.")
            data_points = self._create_mock_data(ctx.state.symbol)
            ctx.state.raw_data = data_points
            return TechnicalAnalysis()
    
    def _create_mock_data(self, symbol: str) -> List[StockDataPoint]:
        """Create mock stock data for demonstration"""
        data_points = []
        base_price = 150.0
        
        for i in range(30):
            date_str = f"2024-{12 - i//30:02d}-{(i % 30) + 1:02d}"
            price_variance = (i % 10) - 5  # Simple price variation
            
            data_point = StockDataPoint(
                date=date_str,
                symbol=symbol,
                open_price=base_price + price_variance,
                high_price=base_price + price_variance + 2,
                low_price=base_price + price_variance - 2,
                close_price=base_price + price_variance + 1,
                volume=1000000 + (i * 10000),
                daily_change=1.5 if i % 2 == 0 else -0.8,
                daily_change_pct=1.0 if i % 2 == 0 else -0.5
            )
            data_points.append(data_point)
        
        return data_points
    
    def _parse_mcp_data(self, mcp_output: str, symbol: str) -> List[StockDataPoint]:
        """Parse MCP output into structured data points"""
        # This is a simplified implementation
        # In practice, you'd parse the actual MCP JSON/CSV response
        # For now, return mock data
        return self._create_mock_data(symbol)


@dataclass
class TechnicalAnalysis(BaseNode[StockAnalysisState]):
    """Second node: Perform technical analysis"""
    
    async def run(self, ctx: GraphRunContext[StockAnalysisState]) -> FundamentalAnalysis:
        agents = get_agents()
        data_summary = self._prepare_data_summary(ctx.state.raw_data)
        
        if not agents or not agents.get('technical_agent'):
            # Mock technical analysis
            ctx.state.technical_analysis = f"Mock technical analysis for {ctx.state.symbol}: " \
                                         f"Based on {len(ctx.state.raw_data)} data points, " \
                                         f"the stock shows moderate bullish momentum with good volume support."
            return FundamentalAnalysis()
        
        try:
            result = await agents['technical_agent'].run(
                f"Perform technical analysis for {ctx.state.symbol}. "
                f"Analyze the following data for trends, support/resistance levels, "
                f"moving averages, and momentum indicators:\n{data_summary}",
                deps=ctx.state.user_profile
            )
            
            ctx.state.technical_analysis = result.output
            return FundamentalAnalysis()
        except Exception as e:
            # Fallback to mock analysis
            print(f"Technical analysis failed: {e}. Using mock analysis.")
            ctx.state.technical_analysis = f"Mock technical analysis for {ctx.state.symbol} (error fallback)"
            return FundamentalAnalysis()
    
    def _prepare_data_summary(self, data_points: List[StockDataPoint]) -> str:
        """Prepare a summary of the data for analysis"""
        if not data_points:
            return "No data available"
        
        latest = data_points[-1]
        oldest = data_points[0]
        
        return f"""
        Data Summary for {latest.symbol}:
        - Latest Price: ${latest.close_price:.2f}
        - Price Change: {latest.daily_change_pct:.2f}%
        - Period: {oldest.date} to {latest.date}
        - Average Volume: {sum(d.volume for d in data_points) / len(data_points):,.0f}
        - Data Points: {len(data_points)}
        """


@dataclass  
class FundamentalAnalysis(BaseNode[StockAnalysisState]):
    """Third node: Perform fundamental analysis"""
    
    async def run(self, ctx: GraphRunContext[StockAnalysisState]) -> SentimentAnalysis:
        agents = get_agents()
        
        if not agents or not agents.get('fundamental_agent'):
            # Mock fundamental analysis
            ctx.state.fundamental_analysis = f"Mock fundamental analysis for {ctx.state.symbol}: " \
                                           f"Company shows solid fundamentals with reasonable valuation " \
                                           f"for {ctx.state.user_profile.risk_tolerance} risk tolerance."
            return SentimentAnalysis()
        
        try:
            result = await agents['fundamental_agent'].run(
                f"Perform fundamental analysis for {ctx.state.symbol}. "
                f"Consider the company's financial health, competitive position, "
                f"growth prospects, and valuation metrics. "
                f"User risk tolerance: {ctx.state.user_profile.risk_tolerance}",
                deps=ctx.state.user_profile
            )
            
            ctx.state.fundamental_analysis = result.output
            return SentimentAnalysis()
        except Exception as e:
            print(f"Fundamental analysis failed: {e}. Using mock analysis.")
            ctx.state.fundamental_analysis = f"Mock fundamental analysis for {ctx.state.symbol} (error fallback)"
            return SentimentAnalysis()


@dataclass
class SentimentAnalysis(BaseNode[StockAnalysisState]):
    """Fourth node: Analyze market sentiment"""
    
    async def run(self, ctx: GraphRunContext[StockAnalysisState]) -> FinalRecommendation:
        agents = get_agents()
        
        if not agents or not agents.get('sentiment_agent'):
            # Mock sentiment analysis
            ctx.state.sentiment_analysis = f"Mock sentiment analysis for {ctx.state.symbol}: " \
                                         f"Market sentiment appears moderately positive with stable outlook."
        else:
            try:
                result = await agents['sentiment_agent'].run(
                    f"Analyze current market sentiment for {ctx.state.symbol}. "
                    f"Consider news sentiment, social media buzz, analyst ratings, "
                    f"and overall market conditions affecting this stock.",
                    deps=ctx.state.user_profile
                )
                
                ctx.state.sentiment_analysis = result.output
            except Exception as e:
                print(f"Sentiment analysis failed: {e}. Using mock analysis.")
                ctx.state.sentiment_analysis = f"Mock sentiment analysis for {ctx.state.symbol} (error fallback)"
        
        # Determine market conditions based on sentiment
        ctx.state.market_conditions = MarketConditions(
            sentiment="bullish",  # This would be derived from actual sentiment analysis
            volatility="medium",
            trend="upward", 
            confidence=0.75
        )
        
        return FinalRecommendation()


@dataclass
class FinalRecommendation(BaseNode[StockAnalysisState, None, AnalysisResult]):
    """Final node: Generate investment recommendation"""
    
    async def run(self, ctx: GraphRunContext[StockAnalysisState]) -> End[AnalysisResult]:
        agents = get_agents()
        
        # Combine all analyses
        combined_analysis = f"""
        Symbol: {ctx.state.symbol}
        
        Technical Analysis:
        {ctx.state.technical_analysis or 'Not available'}
        
        Fundamental Analysis:  
        {ctx.state.fundamental_analysis or 'Not available'}
        
        Sentiment Analysis:
        {ctx.state.sentiment_analysis or 'Not available'}
        
        User Profile:
        - Risk Tolerance: {ctx.state.user_profile.risk_tolerance}
        - Investment Horizon: {ctx.state.user_profile.investment_horizon}
        """
        
        if not agents or not agents.get('recommendation_agent'):
            # Create mock final result
            final_result = self._create_mock_result(ctx.state.symbol, combined_analysis)
        else:
            try:
                result = await agents['recommendation_agent'].run(
                    f"Based on the comprehensive analysis below, provide a final investment "
                    f"recommendation with specific price targets and risk management:\n{combined_analysis}",
                    deps=ctx.state.user_profile,
                    message_history=ctx.state.analysis_agent_messages
                )
                
                ctx.state.analysis_agent_messages += result.new_messages()
                final_result = result.output
            except Exception as e:
                print(f"Final recommendation failed: {e}. Using mock result.")
                final_result = self._create_mock_result(ctx.state.symbol, combined_analysis)
        
        # Ensure we have market conditions
        if not ctx.state.market_conditions:
            ctx.state.market_conditions = MarketConditions(
                sentiment="neutral",
                volatility="medium", 
                trend="sideways",
                confidence=0.5
            )
        
        # Update with actual data
        final_result.data_points = ctx.state.raw_data
        final_result.market_conditions = ctx.state.market_conditions
        final_result.analysis_timestamp = datetime.now()
        
        ctx.state.final_result = final_result
        return End(final_result)
    
    def _create_mock_result(self, symbol: str, analysis: str) -> AnalysisResult:
        """Create a mock analysis result for demonstration"""
        return AnalysisResult(
            symbol=symbol,
            recommendation="hold",
            confidence=0.75,
            target_price=165.0,
            stop_loss=135.0,
            reasoning=f"Mock analysis for {symbol}: Based on combined technical, fundamental, and sentiment analysis, "
                     f"the stock shows moderate potential with balanced risk. Recommendation is to hold for "
                     f"medium-term investors. Note: This is a demonstration with mock data.",
            market_conditions=MarketConditions(
                sentiment="neutral",
                volatility="medium",
                trend="sideways",
                confidence=0.6
            ),
            data_points=[],  # Will be updated with actual data
            analysis_timestamp=datetime.now()
        )


# --- Main Graph Definition ---

stock_analysis_graph = Graph(
    nodes=[DataCollection, TechnicalAnalysis, FundamentalAnalysis, SentimentAnalysis, FinalRecommendation],
    state_type=StockAnalysisState
)


# --- Main Analysis Class ---

class PydanticAIStockAnalyst:
    """Main class for the enhanced stock analyst with PydanticAI Graph"""
    
    def __init__(self):
        self.graph = stock_analysis_graph
    
    async def analyze_stock(
        self, 
        symbol: str, 
        user_profile: Optional[UserProfile] = None
    ) -> AnalysisResult:
        """Run the complete stock analysis workflow"""
        
        if user_profile is None:
            user_profile = UserProfile()
        
        # Initialize state
        state = StockAnalysisState(
            symbol=symbol.upper(),
            user_profile=user_profile
        )
        
        # Run the graph
        result = await self.graph.run(DataCollection(), state=state)
        
        return result.output
    
    async def get_analysis_steps(
        self,
        symbol: str,
        user_profile: Optional[UserProfile] = None
    ) -> List[str]:
        """Get a step-by-step breakdown of the analysis process"""
        
        if user_profile is None:
            user_profile = UserProfile()
        
        state = StockAnalysisState(
            symbol=symbol.upper(),
            user_profile=user_profile  
        )
        
        steps = []
        async with self.graph.iter(DataCollection(), state=state) as run:
            async for node in run:
                steps.append(f"{type(node).__name__}: {node}")
        
        return steps
    
    def generate_mermaid_diagram(self) -> str:
        """Generate a Mermaid diagram of the analysis workflow"""
        return self.graph.mermaid_code(start_node=DataCollection)


# --- Usage Example ---

async def main():
    """Example usage of the enhanced stock analyst"""
    
    analyst = PydanticAIStockAnalyst()
    
    # Create user profile
    user = UserProfile(
        name="John Investor",
        risk_tolerance="moderate",
        investment_horizon="long"
    )
    
    # Analyze a stock
    print("Starting comprehensive stock analysis...")
    result = await analyst.analyze_stock("AAPL", user)
    
    print(f"\n--- Analysis Result for {result.symbol} ---")
    print(f"Recommendation: {result.recommendation}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Reasoning: {result.reasoning}")
    
    if result.target_price:
        print(f"Target Price: ${result.target_price:.2f}")
    if result.stop_loss:
        print(f"Stop Loss: ${result.stop_loss:.2f}")
    
    print(f"\nMarket Conditions:")
    print(f"- Sentiment: {result.market_conditions.sentiment}")
    print(f"- Volatility: {result.market_conditions.volatility}")  
    print(f"- Trend: {result.market_conditions.trend}")
    
    print(f"\nData Points: {len(result.data_points)} historical records")


if __name__ == "__main__":
    asyncio.run(main()) 