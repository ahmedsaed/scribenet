"""
MCP (Model Context Protocol) integration for ScribeNet.
"""

from backend.mcp.client_manager import MCPClientManager
from backend.mcp.errors import (
    MCPError,
    ServerConnectionError,
    ToolNotFoundError,
    ToolExecutionError,
)

__all__ = [
    "MCPClientManager",
    "MCPError",
    "ServerConnectionError",
    "ToolNotFoundError",
    "ToolExecutionError",
]
