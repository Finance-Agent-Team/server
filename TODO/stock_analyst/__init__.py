"""
AI Stock Analyst - PydanticAI + Claude + Logfire Integration
A comprehensive stock analysis system using Model Context Protocol (MCP)
"""

from .agent import AIStockAnalyst
from .models import StockAnalysis, UserProfile
from .mcp_client import create_mcp_server

__version__ = "1.0.0"
__all__ = ["AIStockAnalyst", "StockAnalysis", "UserProfile", "create_mcp_server"] 