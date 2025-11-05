"""
Base class for MCP tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from mcp.types import Tool, TextContent
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Base class for all MCP tools.
    
    Each tool class should:
    1. Define tools in get_tools() method
    2. Implement tool execution in execute() method
    3. Handle errors gracefully
    """
    
    def __init__(self):
        """Initialize the tool."""
        self.logger = logger
    
    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """
        Return a list of MCP Tool definitions.
        
        Returns:
            List of Tool objects with name, description, and inputSchema
        """
        pass
    
    @abstractmethod
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Execute a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments for the tool
        
        Returns:
            List of TextContent results
        
        Raises:
            ValueError: If tool_name is not supported
            Exception: For execution errors
        """
        pass
    
    def format_success(self, message: str) -> List[TextContent]:
        """Helper to format success response."""
        return [TextContent(type="text", text=f"✅ {message}")]
    
    def format_error(self, message: str) -> List[TextContent]:
        """Helper to format error response."""
        return [TextContent(type="text", text=f"❌ {message}")]
    
    def format_info(self, message: str) -> List[TextContent]:
        """Helper to format informational response."""
        return [TextContent(type="text", text=message)]
