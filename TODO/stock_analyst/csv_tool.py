"""Alpha Vantage CSV tools for PydanticAI agent."""

import aiohttp
import asyncio
import pandas as pd
from typing import Optional, Literal
from pydantic import BaseModel, Field
import logfire

from .config import get_alpha_vantage_api_key


class AlphaVantageCSVParams(BaseModel):
    """Parameters for Alpha Vantage CSV requests."""
    symbol: str = Field(description="Stock symbol (e.g., 'AAPL', 'GOOGL')")
    function: Literal[
        "TIME_SERIES_INTRADAY",
        "TIME_SERIES_DAILY", 
        "TIME_SERIES_DAILY_ADJUSTED",
        "TIME_SERIES_WEEKLY",
        "TIME_SERIES_MONTHLY"
    ] = Field(description="The Alpha Vantage function to call")
    interval: Optional[Literal["1min", "5min", "15min", "30min", "60min"]] = Field(
        default=None, 
        description="Time interval for intraday data (required for TIME_SERIES_INTRADAY)"
    )
    outputsize: Literal["compact", "full"] = Field(
        default="compact",
        description="compact = latest 100 data points, full = full-length time series"
    )
    month: Optional[str] = Field(
        default=None,
        description="Month in YYYY-MM format for historical intraday data (e.g., '2024-01')"
    )


async def fetch_alpha_vantage_csv(params: AlphaVantageCSVParams) -> str:
    """
    Fetch stock data from Alpha Vantage as CSV format.
    
    Returns CSV string that can be saved directly or processed with pandas.
    """
    api_key = get_alpha_vantage_api_key()
    
    # Build the URL
    base_url = "https://www.alphavantage.co/query"
    url_params = {
        "function": params.function,
        "symbol": params.symbol,
        "apikey": api_key,
        "datatype": "csv"
    }
    
    # Add interval for intraday data
    if params.function == "TIME_SERIES_INTRADAY":
        if not params.interval:
            raise ValueError("interval is required for TIME_SERIES_INTRADAY function")
        url_params["interval"] = params.interval
    
    # Add optional parameters
    if params.outputsize:
        url_params["outputsize"] = params.outputsize
    if params.month:
        url_params["month"] = params.month
    
    logfire.info(f"Fetching Alpha Vantage CSV data: {params.function} for {params.symbol}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(base_url, params=url_params) as response:
                if response.status == 200:
                    csv_data = await response.text()
                    
                    # Check if we got an error message instead of CSV
                    if "Error Message" in csv_data or "Note:" in csv_data:
                        logfire.error(f"Alpha Vantage API error: {csv_data}")
                        return f"API Error: {csv_data}"
                    
                    # Check if we hit rate limit
                    if "Thank you for using Alpha Vantage" in csv_data:
                        logfire.warning("Alpha Vantage rate limit reached")
                        return "Rate limit reached. Please try again later."
                    
                    logfire.info(f"Successfully fetched CSV data: {len(csv_data)} characters")
                    return csv_data
                else:
                    error_msg = f"HTTP {response.status}: {await response.text()}"
                    logfire.error(f"Alpha Vantage request failed: {error_msg}")
                    return f"Request failed: {error_msg}"
    
    except asyncio.TimeoutError:
        logfire.error("Alpha Vantage request timed out")
        return "Request timed out. Please try again."
    except Exception as e:
        logfire.error(f"Alpha Vantage request error: {e}")
        return f"Error: {str(e)}"


async def get_daily_stock_csv(symbol: str, adjusted: bool = True) -> str:
    """Get daily stock data as CSV."""
    function = "TIME_SERIES_DAILY_ADJUSTED" if adjusted else "TIME_SERIES_DAILY"
    params = AlphaVantageCSVParams(
        symbol=symbol,
        function=function,
        outputsize="full"  # Get full historical data
    )
    return await fetch_alpha_vantage_csv(params)


async def get_intraday_stock_csv(
    symbol: str, 
    interval: Literal["1min", "5min", "15min", "30min", "60min"] = "5min",
    month: Optional[str] = None
) -> str:
    """Get intraday stock data as CSV."""
    params = AlphaVantageCSVParams(
        symbol=symbol,
        function="TIME_SERIES_INTRADAY",
        interval=interval,
        outputsize="full",
        month=month
    )
    return await fetch_alpha_vantage_csv(params)


async def get_weekly_stock_csv(symbol: str, adjusted: bool = True) -> str:
    """Get weekly stock data as CSV."""
    function = "TIME_SERIES_WEEKLY_ADJUSTED" if adjusted else "TIME_SERIES_WEEKLY"
    params = AlphaVantageCSVParams(
        symbol=symbol,
        function=function,
        outputsize="full"
    )
    return await fetch_alpha_vantage_csv(params)


async def analyze_csv_data(csv_data: str, symbol: str) -> str:
    """
    Analyze CSV data and return insights.
    This converts CSV to pandas for quick analysis.
    """
    try:
        from io import StringIO
        
        # Read CSV into pandas
        df = pd.read_csv(StringIO(csv_data))
        
        if df.empty:
            return f"No data available for {symbol}"
        
        # Get basic info
        latest_row = df.iloc[0] if not df.empty else None
        if latest_row is None:
            return f"No valid data found for {symbol}"
        
        # Extract key metrics
        analysis = f"""
📊 **CSV Data Analysis for {symbol}**

📈 **Latest Data Point**: {latest_row.get('timestamp', 'N/A')}
💰 **Current Price**: ${latest_row.get('close', latest_row.get('4. close', 'N/A'))}
📊 **Trading Volume**: {latest_row.get('volume', latest_row.get('5. volume', 'N/A')):,}

📋 **Dataset Info**:
- Total data points: {len(df)}
- Date range: {df.iloc[-1].get('timestamp', 'N/A')} to {df.iloc[0].get('timestamp', 'N/A')}

💾 **CSV Data Retrieved**: {len(csv_data)} characters of raw CSV data
"""
        
        return analysis
        
    except Exception as e:
        logfire.error(f"CSV analysis failed: {e}")
        return f"CSV data retrieved ({len(csv_data)} chars) but analysis failed: {str(e)}" 