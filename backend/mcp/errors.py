"""
Custom exceptions for MCP integration.
"""


class MCPError(Exception):
    """Base exception for MCP-related errors."""
    pass


class ServerConnectionError(MCPError):
    """Failed to connect to MCP server."""
    pass


class ToolNotFoundError(MCPError):
    """Requested tool doesn't exist."""
    pass


class ToolExecutionError(MCPError):
    """Tool execution failed."""
    pass


class ServerConfigurationError(MCPError):
    """Invalid MCP server configuration."""
    pass
