"""MCP server setup and management for AI Stock Analyst."""

import os
from pydantic_ai.mcp import MCPServerStdio
from .config import get_mcp_server_path, get_alpha_vantage_api_key


def create_mcp_server() -> MCPServerStdio:
    """Create and configure the MCP server for stock analysis."""
    return MCPServerStdio(
        'node',
        args=[get_mcp_server_path()],
        env={
            'ALPHA_VANTAGE_API_KEY': get_alpha_vantage_api_key(),
            **os.environ
        }
    ) 