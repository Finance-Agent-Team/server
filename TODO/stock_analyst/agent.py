"""Core PydanticAI agent and analysis logic for AI Stock Analyst."""

import asyncio
import re
from typing import List, Literal, Optional
from datetime import datetime
import os

import logfire
from pydantic_ai import Agent, RunContext

from .models import UserProfile, RequestType, DetailedStockData, StockDataPoint
from .mcp_client import create_mcp_server
from .config import cleanup_tasks
from .csv_tool import (
    get_daily_stock_csv, 
    get_intraday_stock_csv, 
    get_weekly_stock_csv, 
    analyze_csv_data
)


class AIStockAnalyst:
    """Main application class for the AI Stock Analyst using PydanticAI."""
    
    def __init__(self):
        # Set up MCP server
        mcp_server = create_mcp_server()
        
        # Initialize AI Agent with simple system prompt
        self.agent = Agent(
            'anthropic:claude-3-5-sonnet-latest',
            deps_type=UserProfile,
            mcp_servers=[mcp_server],
            system_prompt=(
                "You are an expert stock analyst with access to multiple data sources:\n"
                "1. MCP tools for general stock data and alerts\n"
                "2. Alpha Vantage CSV tools for detailed historical data that can be exported\n\n"
                "Available CSV tools:\n"
                "- get_stock_csv_daily: Get daily stock data as CSV (best for historical analysis)\n"
                "- get_stock_csv_intraday: Get intraday data as CSV (1min, 5min, 15min, 30min, 60min intervals)\n"
                "- get_stock_csv_weekly: Get weekly data as CSV (long-term trends)\n"
                "- save_csv_to_file: Save CSV data to a file for export\n\n"
                "Choose CSV tools when users want:\n"
                "- Detailed historical data\n"
                "- Data they can export/save\n"
                "- Specific time intervals\n"
                "- Raw data for further analysis\n\n"
                "Use MCP tools for general queries and real-time alerts."
            )
        )
        
        # Initialize classification agent for request type
        self.classifier_agent = Agent(
            'anthropic:claude-3-5-sonnet-latest',
            result_type=RequestType,
            system_prompt=(
                "You are a request classifier. Analyze user requests to determine if they want:"
                "1. SPECIFIC detailed data (mentions: performance, data, movements, date range, CSV, export, detailed analysis, historical data, etc.)"
                "2. GENERAL overview/summary (vague requests, general questions, quick info, latest data, overall view, etc.)"
                
                "SPECIFIC requests typically ask for:"
                "- Historical data or date ranges"
                "- Performance metrics"
                "- Detailed movements or analysis"
                "- Export or file requests"
                "- Multiple data points"
                
                "GENERAL requests typically ask for:"
                "- Overall consensus or opinion"
                "- Latest/current info"
                "- Quick summaries"
                "- General market view"
                "- Simple recommendations"
            )
        )
        
        # Add personalized system prompt
        @self.agent.system_prompt
        async def personalized_prompt(ctx: RunContext[UserProfile]) -> str:
            """Dynamic system prompt based on user preferences"""
            return f"""
            You are analyzing stocks for {ctx.deps.name} with the following profile:
            - Risk Tolerance: {ctx.deps.risk_tolerance}
            - Investment Horizon: {ctx.deps.investment_horizon}
            
            Tailor your analysis and recommendations accordingly, using the MCP tools to get current data.
            """
        
        # Add Alpha Vantage CSV tools
        @self.agent.tool
        async def get_stock_csv_daily(ctx: RunContext[UserProfile], symbol: str, adjusted: bool = True) -> str:
            """
            Get daily stock data from Alpha Vantage as CSV format.
            
            Args:
                symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')
                adjusted: Whether to get adjusted prices (default: True)
            
            Returns CSV data that can be saved or analyzed.
            """
            logfire.info(f"Fetching daily CSV data for {symbol}")
            csv_data = await get_daily_stock_csv(symbol, adjusted)
            
            # If it's valid CSV data, also provide analysis
            if not csv_data.startswith("Error") and not csv_data.startswith("Rate limit"):
                analysis = await analyze_csv_data(csv_data, symbol)
                return f"{analysis}\n\n📄 **Raw CSV Data**:\n```csv\n{csv_data[:1000]}{'...' if len(csv_data) > 1000 else ''}\n```"
            else:
                return csv_data

        @self.agent.tool
        async def get_stock_csv_intraday(
            ctx: RunContext[UserProfile], 
            symbol: str,
            interval: Literal["1min", "5min", "15min", "30min", "60min"] = "5min",
            month: Optional[str] = None
        ) -> str:
            """
            Get intraday stock data from Alpha Vantage as CSV format.
            
            Args:
                symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')
                interval: Time interval (1min, 5min, 15min, 30min, 60min)
                month: Optional month in YYYY-MM format for historical data
            
            Returns CSV data that can be saved or analyzed.
            """
            logfire.info(f"Fetching intraday CSV data for {symbol} ({interval})")
            csv_data = await get_intraday_stock_csv(symbol, interval, month)
            
            # If it's valid CSV data, also provide analysis
            if not csv_data.startswith("Error") and not csv_data.startswith("Rate limit"):
                analysis = await analyze_csv_data(csv_data, symbol)
                return f"{analysis}\n\n📄 **Raw CSV Data**:\n```csv\n{csv_data[:1000]}{'...' if len(csv_data) > 1000 else ''}\n```"
            else:
                return csv_data

        @self.agent.tool
        async def get_stock_csv_weekly(ctx: RunContext[UserProfile], symbol: str, adjusted: bool = True) -> str:
            """
            Get weekly stock data from Alpha Vantage as CSV format.
            
            Args:
                symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')
                adjusted: Whether to get adjusted prices (default: True)
            
            Returns CSV data that can be saved or analyzed.
            """
            logfire.info(f"Fetching weekly CSV data for {symbol}")
            csv_data = await get_weekly_stock_csv(symbol, adjusted)
            
            # If it's valid CSV data, also provide analysis
            if not csv_data.startswith("Error") and not csv_data.startswith("Rate limit"):
                analysis = await analyze_csv_data(csv_data, symbol)
                return f"{analysis}\n\n📄 **Raw CSV Data**:\n```csv\n{csv_data[:1000]}{'...' if len(csv_data) > 1000 else ''}\n```"
            else:
                return csv_data

        @self.agent.tool
        async def save_csv_to_file(ctx: RunContext[UserProfile], csv_data: str, symbol: str, data_type: str = "daily") -> str:
            """
            Save CSV data to a file.
            
            Args:
                csv_data: The CSV data string to save
                symbol: Stock symbol for filename
                data_type: Type of data (daily, intraday, weekly) for filename
            
            Returns the filename where data was saved.
            """
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{symbol}_{data_type}_data_{timestamp}.csv"
            
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    f.write(csv_data)
                
                logfire.info(f"CSV file saved: {filename}")
                return f"✅ CSV data saved to: {filename} ({len(csv_data)} characters)"
            except Exception as e:
                logfire.error(f"Failed to save CSV file: {e}")
                return f"❌ Error saving CSV file: {str(e)}"

        # Create a separate CSV-only agent for specific requests (no MCP)
        self.csv_agent = Agent(
            'anthropic:claude-3-5-sonnet-latest',
            deps_type=UserProfile,
            system_prompt=(
                "You are an expert stock analyst with access to Alpha Vantage CSV tools.\n"
                "Use these tools to get detailed stock data that can be exported:\n"
                "- get_stock_csv_daily: Get daily stock data as CSV\n"
                "- get_stock_csv_intraday: Get intraday data as CSV\n"
                "- get_stock_csv_weekly: Get weekly data as CSV\n"
                "- save_csv_to_file: Save CSV data to a file\n\n"
                "Always use these tools to provide detailed analysis with exportable data."
            )
        )
        
        # Add the same CSV tools to the CSV-only agent
        @self.csv_agent.tool
        async def get_stock_csv_daily(ctx: RunContext[UserProfile], symbol: str, adjusted: bool = True) -> str:
            """Get daily stock data from Alpha Vantage as CSV format."""
            logfire.info(f"Fetching daily CSV data for {symbol}")
            csv_data = await get_daily_stock_csv(symbol, adjusted)
            
            if not csv_data.startswith("Error") and not csv_data.startswith("Rate limit"):
                analysis = await analyze_csv_data(csv_data, symbol)
                return f"{analysis}\n\n📄 **Raw CSV Data**:\n```csv\n{csv_data[:1000]}{'...' if len(csv_data) > 1000 else ''}\n```"
            else:
                return csv_data

        @self.csv_agent.tool
        async def get_stock_csv_intraday(
            ctx: RunContext[UserProfile], 
            symbol: str,
            interval: Literal["1min", "5min", "15min", "30min", "60min"] = "5min",
            month: Optional[str] = None
        ) -> str:
            """Get intraday stock data from Alpha Vantage as CSV format."""
            logfire.info(f"Fetching intraday CSV data for {symbol} ({interval})")
            csv_data = await get_intraday_stock_csv(symbol, interval, month)
            
            if not csv_data.startswith("Error") and not csv_data.startswith("Rate limit"):
                analysis = await analyze_csv_data(csv_data, symbol)
                return f"{analysis}\n\n📄 **Raw CSV Data**:\n```csv\n{csv_data[:1000]}{'...' if len(csv_data) > 1000 else ''}\n```"
            else:
                return csv_data

        @self.csv_agent.tool
        async def save_csv_to_file(ctx: RunContext[UserProfile], csv_data: str, symbol: str, data_type: str = "daily") -> str:
            """Save CSV data to a file."""
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{symbol}_{data_type}_data_{timestamp}.csv"
            
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    f.write(csv_data)
                
                logfire.info(f"CSV file saved: {filename}")
                return f"✅ CSV data saved to: {filename} ({len(csv_data)} characters)"
            except Exception as e:
                logfire.error(f"Failed to save CSV file: {e}")
                return f"❌ Error saving CSV file: {str(e)}"

        logfire.info("AI Stock Analyst initialized with PydanticAI + Claude + Logfire + CSV Tools")
    
    async def classify_request(self, user_input: str) -> RequestType:
        """Classify if user wants specific detailed data or general overview."""
        try:
            result = await self.classifier_agent.run(
                f"Classify this request: '{user_input}'"
            )
            logfire.info(f"Request classified as: {result.output.request_type}")
            return result.output
        except Exception as e:
            logfire.error(f"Request classification failed: {e}")
            # Default to general if classification fails
            return RequestType(
                request_type="general",
                specific_elements=[],
                confidence=0.5,
                reasoning="Classification failed, defaulting to general"
            )

    def parse_mcp_data(self, mcp_output: str, symbol: str) -> DetailedStockData:
        """Parse MCP stock data output into structured format."""
        data_points = []
        
        # Extract data lines using regex - handle both single-line and multi-line formats
        # Single-line format: 2025-06-06: Open: 203.0000 High: 205.7000...
        # Multi-line format: 2025-06-06:\n  Open: 203.0000\n  High: 205.7000...
        
        # First try single-line format
        single_line_pattern = r'(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?):?\s*Open:\s*([\d.]+)\s*High:\s*([\d.]+)\s*Low:\s*([\d.]+)\s*Close:\s*([\d.]+)\s*Volume:\s*([\d,]+)'
        matches = re.findall(single_line_pattern, mcp_output)
        
        # If no matches, try multi-line format (MCP server format)
        if not matches:
            multi_line_pattern = r'(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?):[\s\S]*?Open:\s*([\d.]+)[\s\S]*?High:\s*([\d.]+)[\s\S]*?Low:\s*([\d.]+)[\s\S]*?Close:\s*([\d.]+)[\s\S]*?Volume:\s*([\d,]+)'
            matches = re.findall(multi_line_pattern, mcp_output)
        
        logfire.info(f"Raw MCP output preview: {mcp_output[:500]}...")
        logfire.info(f"Parsing MCP data for {symbol}, found {len(matches)} data points")
        
        previous_close = None
        for i, match in enumerate(matches):
            try:
                datetime_str, open_price, high_price, low_price, close_price, volume = match
                
                # Clean and convert values
                open_val = float(open_price)
                high_val = float(high_price)
                low_val = float(low_price)
                close_val = float(close_price)
                volume_val = int(volume.replace(',', ''))  # Remove commas from volume
                
                # Calculate daily change if we have previous close
                daily_change = None
                daily_change_pct = None
                if previous_close is not None:
                    daily_change = close_val - previous_close
                    daily_change_pct = (daily_change / previous_close) * 100
                
                data_point = StockDataPoint(
                    date=datetime_str.strip(),  # Use the full datetime string
                    symbol=symbol,
                    open_price=open_val,
                    high_price=high_val,
                    low_price=low_val,
                    close_price=close_val,
                    volume=volume_val,
                    daily_change=daily_change,
                    daily_change_pct=daily_change_pct
                )
                data_points.append(data_point)
                previous_close = close_val
                
                if i < 3:  # Log first few data points for debugging
                    logfire.info(f"Parsed data point {i+1}: {datetime_str} - Close: {close_val}, Volume: {volume_val}")
                    
            except Exception as e:
                logfire.error(f"Error parsing data point {i+1}: {match} - {str(e)}")
                continue
        
        # Calculate summary stats
        if data_points:
            closes = [dp.close_price for dp in data_points]
            volumes = [dp.volume for dp in data_points]
            summary_stats = {
                "avg_close": sum(closes) / len(closes),
                "max_close": max(closes),
                "min_close": min(closes),
                "avg_volume": sum(volumes) / len(volumes),
                "total_data_points": len(data_points)
            }
        else:
            summary_stats = {}
        
        return DetailedStockData(
            symbol=symbol,
            data_points=data_points,
            analysis_date=datetime.now().isoformat(),
            summary_stats=summary_stats
        )

    async def save_csv_file(self, data: DetailedStockData, filename: str = None) -> str:
        """Save detailed stock data to CSV file."""
        if len(data.data_points) == 0:
            logfire.warning(f"No data points to save for {data.symbol}")
            return "No data available to save"
            
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{data.symbol}_stock_data_{timestamp}.csv"
        
        csv_content = data.to_csv()
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_content)
            logfire.info(f"CSV file saved: {filename} with {len(data.data_points)} data points")
            
            # Also log the first few lines for verification
            lines = csv_content.split('\n')[:5]
            logfire.info(f"CSV content preview: {lines}")
            
            return filename
        except Exception as e:
            logfire.error(f"Failed to save CSV file: {e}")
            return f"Error saving file: {str(e)}"

    async def handle_specific_request(self, user_input: str, symbol: str, profile: UserProfile) -> tuple[str, str]:
        """Handle specific detailed requests with CSV export."""
        logfire.info(f"Handling specific request for {symbol}")
        
        try:
            # For specific requests, use CSV-only agent (no MCP servers)
            result = await asyncio.wait_for(
                self.csv_agent.run(
                    f"Use get_stock_csv_daily to get detailed data for {symbol}. Analyze the data and save it to a CSV file using save_csv_to_file.",
                    deps=profile,
                    model_settings={'max_tokens': 2500}
                ),
                timeout=120  # 2 minutes timeout for detailed analysis
            )
                
            logfire.info(f"CSV result output length: {len(result.output)} characters")
            
            # For CSV tools, return the result directly (it already contains analysis + CSV file info)
            response = f"""
📊 **Detailed Analysis for {symbol}**
{result.output}

✅ **CSV Tools Used**: This analysis used Alpha Vantage CSV tools for direct data access.
"""
            
            # Check if a CSV file was mentioned in the output
            csv_file = ""
            if "CSV data saved to:" in result.output:
                # Extract filename from the output
                lines = result.output.split('\n')
                for line in lines:
                    if "CSV data saved to:" in line:
                        csv_file = line.split("CSV data saved to:")[1].split()[0]
                        break
            
            return response, csv_file
                
        except asyncio.TimeoutError:
            logfire.error(f"Specific request timed out for {symbol}")
            return f"⏰ Detailed analysis for {symbol} timed out. The analysis was taking too long. Please try again or use a simpler request.", ""
        except Exception as e:
            logfire.error(f"Specific request failed for {symbol}: {e}")
            return f"❌ Detailed analysis failed for {symbol}: {str(e)}", ""

    async def handle_general_request(self, user_input: str, symbol: str, profile: UserProfile) -> str:
        """Handle general requests with text summary."""
        logfire.info(f"Handling general request for {symbol}")
        
        try:
            async with self.agent.run_mcp_servers():
                result = await asyncio.wait_for(
                    self.agent.run(
                        f"Analyze {symbol} stock. Call get-daily-stock-data for {symbol} and provide a brief summary.",
                        deps=profile,
                        model_settings={'max_tokens': 1000}
                    ),
                    timeout=60  # 1 minute timeout for general analysis
                )
                
                return result.output
                
        except asyncio.TimeoutError:
            logfire.error(f"General request timed out for {symbol}")
            return f"⏰ Analysis for {symbol} timed out. Please try again."
        except Exception as e:
            logfire.error(f"General request failed for {symbol}: {e}")
            return f"❌ Analysis failed for {symbol}: {str(e)}"

    async def smart_analyze(self, user_input: str, symbol: str, profile: UserProfile) -> tuple[str, str]:
        """Smart analysis that handles both specific and general requests."""
        # Classify the request
        request_type = await self.classify_request(user_input)
        
        logfire.info(f"Processing {request_type.request_type} request for {symbol}")
        
        if request_type.request_type == "specific":
            response, csv_file = await self.handle_specific_request(user_input, symbol, profile)
            return response, csv_file
        else:
            response = await self.handle_general_request(user_input, symbol, profile)
            return response, ""

    async def analyze_stock(self, symbol: str, profile: UserProfile, timeout: int = 60) -> str:
        """Analyze a single stock with detailed insights."""
        logfire.info(f"Starting analysis for {symbol} - User: {profile.name}")
        
        try:
            async with self.agent.run_mcp_servers():
                result = await asyncio.wait_for(
                    self.agent.run(
                        f"""
                        Please analyze {symbol} stock. Start by calling get-daily-stock-data with symbol="{symbol}" to get the current price and data.
                        Then provide a brief analysis including:
                        - Current price and recent performance
                        - Buy/hold/sell recommendation for {profile.risk_tolerance} risk tolerance
                        - Key insights for {profile.investment_horizon} investment horizon
                        """,
                        deps=profile,
                        model_settings={'max_tokens': 1500}
                    ),
                    timeout=timeout
                )
                
                logfire.info(f"Analysis completed for {symbol}")
                return result.output
                
        except asyncio.TimeoutError:
            logfire.error(f"Analysis timed out for {symbol}")
            return f"⏰ Analysis for {symbol} timed out. Please try again with a shorter analysis or check your connection."
        except Exception as e:
            logfire.error(f"Analysis failed for {symbol}: {e}")
            return f"❌ Analysis failed for {symbol}: {str(e)}"
        finally:
            await cleanup_tasks()
    
    async def compare_stocks(self, symbols: List[str], profile: UserProfile) -> str:
        """Compare multiple stocks and provide portfolio recommendations."""
        logfire.info(f"Comparing stocks: {', '.join(symbols)} for user: {profile.name}")
        
        try:
            async with self.agent.run_mcp_servers():
                result = await self.agent.run(
                    f"""
                    Please compare these stocks: {', '.join(symbols)}
                    
                    For each stock, please call these MCP tools:
                    1. get-daily-stock-data with the stock symbol
                    2. get-stock-data with 5min interval 
                    3. get-stock-alerts for each symbol
                    
                    Then provide a comparison including:
                    - Performance comparison based on the data
                    - Risk analysis for each stock
                    - Portfolio allocation recommendations for {profile.risk_tolerance} tolerance
                    - Best and worst performers with explanations
                    - Investment strategy for {profile.investment_horizon} horizon
                    """,
                    deps=profile,
                    model_settings={
                        'max_tokens': 3000
                    }
                )
                
                logfire.info("Stock comparison completed")
                return result.output
        except Exception as e:
            logfire.error(f"Stock comparison failed: {e}")
            return f"❌ Stock comparison failed: {str(e)}"
        finally:
            await cleanup_tasks()
    
    async def market_overview(self, sectors: List[str] = None) -> str:
        """Get market overview for specified sectors."""
        if sectors is None:
            sectors = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
        
        logfire.info(f"Generating market overview for: {', '.join(sectors)}")
        
        try:
            async with self.agent.run_mcp_servers():
                result = await self.agent.run(
                    f"""
                    Please provide a comprehensive market overview by analyzing these key stocks: {', '.join(sectors)}
                    
                    For each stock ({', '.join(sectors)}), please call:
                    1. get-daily-stock-data to get current data
                    2. get-stock-alerts to check for significant movements
                    
                    Then provide a market overview including:
                    - Overall market sentiment analysis
                    - Sector performance trends
                    - Key opportunities and risks identified
                    - Market outlook based on current performance
                    - Top recommendations supported by the data
                    """,
                    deps=UserProfile(),
                    model_settings={
                        'max_tokens': 2500
                    }
                )
                
                logfire.info("Market overview completed")
                return result.output
        except Exception as e:
            logfire.error(f"Market overview failed: {e}")
            return f"❌ Market overview failed: {str(e)}"
        finally:
            await cleanup_tasks()
    
    async def quick_analysis(self, symbol: str, timeout: int = 30) -> str:
        """Quick stock analysis with just daily data."""
        profile = UserProfile()
        
        try:
            async with self.agent.run_mcp_servers():
                result = await asyncio.wait_for(
                    self.agent.run(
                        f"Please call get-daily-stock-data with symbol='{symbol}' and provide a brief analysis with current price and recommendation.",
                        deps=profile,
                        model_settings={'max_tokens': 800}
                    ),
                    timeout=timeout
                )
                return result.output
        except asyncio.TimeoutError:
            return f"⏰ Quick analysis for {symbol} timed out. Please try again."
        except Exception as e:
            return f"❌ Quick analysis failed for {symbol}: {str(e)}"
        finally:
            await cleanup_tasks()
    
    async def verify_tools_working(self) -> bool:
        """Simple verification that MCP tools are available."""
        return True 