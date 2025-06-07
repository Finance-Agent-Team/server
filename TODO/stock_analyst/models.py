"""Pydantic models and data structures for AI Stock Analyst."""

from dataclasses import dataclass
from typing import List, Optional, Literal
from datetime import datetime
import csv
import io

from pydantic import BaseModel, Field


class StockAnalysis(BaseModel):
    """Structured output for stock analysis results."""
    symbol: str = Field(description="Stock symbol")
    current_price: Optional[float] = Field(description="Current stock price")
    trend: str = Field(description="Overall trend: bullish, bearish, or neutral")
    recommendation: str = Field(description="Investment recommendation: buy, hold, or sell")
    risk_level: str = Field(description="Risk assessment: low, medium, or high")
    key_insights: List[str] = Field(description="Key insights about the stock")
    confidence: float = Field(ge=0, le=1, description="Confidence in analysis (0-1)")


class StockDataPoint(BaseModel):
    """Individual stock data point for CSV export."""
    date: str = Field(description="Trading date")
    symbol: str = Field(description="Stock symbol")
    open_price: float = Field(description="Opening price")
    high_price: float = Field(description="Highest price")
    low_price: float = Field(description="Lowest price")
    close_price: float = Field(description="Closing price")
    volume: int = Field(description="Trading volume")
    daily_change: Optional[float] = Field(description="Daily price change", default=None)
    daily_change_pct: Optional[float] = Field(description="Daily percentage change", default=None)


class DetailedStockData(BaseModel):
    """Complete stock data collection for CSV export."""
    symbol: str = Field(description="Stock symbol")
    data_points: List[StockDataPoint] = Field(description="List of stock data points")
    analysis_date: str = Field(description="When this analysis was performed")
    summary_stats: Optional[dict] = Field(description="Summary statistics", default=None)
    
    def to_csv(self) -> str:
        """Convert stock data to CSV format."""
        output = io.StringIO()
        if not self.data_points:
            return "No data available"
        
        fieldnames = ['date', 'symbol', 'open_price', 'high_price', 'low_price', 
                     'close_price', 'volume', 'daily_change', 'daily_change_pct']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for point in self.data_points:
            writer.writerow(point.model_dump())
        
        return output.getvalue()


class RequestType(BaseModel):
    """Classification of user request type."""
    request_type: Literal["specific", "general"] = Field(description="Type of request")
    specific_elements: List[str] = Field(description="Specific elements requested", default=[])
    confidence: float = Field(ge=0, le=1, description="Confidence in classification")
    reasoning: str = Field(description="Why this classification was chosen")


@dataclass
class UserProfile:
    """User investment profile for personalized analysis."""
    name: str = "Investor"
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    investment_horizon: str = "medium-term"  # short-term, medium-term, long-term 