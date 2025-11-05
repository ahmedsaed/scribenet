"""
Unit tests for Base Tool functionality.
"""

import pytest
from backend.mcp.tools.base import BaseTool
from mcp.types import TextContent, Tool
from typing import List, Dict, Any


class ConcreteTestTool(BaseTool):
    """Concrete implementation of BaseTool for testing."""
    
    def get_tools(self) -> List[Tool]:
        """Return test tool definitions."""
        return [
            Tool(
                name="test_tool",
                description="A test tool",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute test tool."""
        return self.format_success("Test executed")


class TestBaseTool:
    """Test suite for BaseTool base class."""
    
    @pytest.fixture
    def base_tool(self):
        """Create a concrete BaseTool implementation for testing."""
        return ConcreteTestTool()
    
    def test_format_success(self, base_tool):
        """Test formatting success messages."""
        result = base_tool.format_success("Operation completed")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "✅" in result[0].text
        assert "Operation completed" in result[0].text
    
    def test_format_error(self, base_tool):
        """Test formatting error messages."""
        result = base_tool.format_error("Something went wrong")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "❌" in result[0].text
        assert "Something went wrong" in result[0].text
    
    def test_format_info(self, base_tool):
        """Test formatting info messages."""
        result = base_tool.format_info("Here is some information")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Here is some information" in result[0].text
    
    def test_get_tools_returns_list(self, base_tool):
        """Test that get_tools returns a list of tools."""
        tools = base_tool.get_tools()
        assert isinstance(tools, list)
        assert len(tools) == 1
        assert tools[0].name == "test_tool"
    
    @pytest.mark.asyncio
    async def test_execute_returns_text_content(self, base_tool):
        """Test that execute returns TextContent list."""
        result = await base_tool.execute("test_tool", {})
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
