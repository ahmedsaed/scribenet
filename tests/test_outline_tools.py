"""
Unit tests for MCP Outline Tools.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from backend.mcp.tools.outline_tools import OutlineTools


class TestOutlineTools:
    """Test suite for OutlineTools class."""
    
    @pytest.fixture
    def outline_tools(self):
        """Create OutlineTools instance with mocked dependencies."""
        tools = OutlineTools()
        tools.db = Mock()
        tools.director = AsyncMock()
        tools.outline_agent = AsyncMock()
        return tools
    
    def test_get_tools_returns_one_tool(self, outline_tools):
        """Test that get_tools returns 1 tool definition."""
        tools = outline_tools.get_tools()
        
        assert len(tools) == 1
        assert tools[0].name == "generate_outline"
    
    @pytest.mark.asyncio
    async def test_generate_outline_success(self, outline_tools):
        """Test successful outline generation."""
        outline_tools.db.get_project.return_value = {
            'id': 'proj-1',
            'title': 'Test Novel',
            'genre': 'sci-fi',
            'vision_document': 'A great vision',
            'target_chapters': 20
        }
        outline_tools.outline_agent.execute.return_value = {
            'outline': 'Chapter 1: Introduction\nChapter 2: Rising Action'
        }
        
        result = await outline_tools.execute("generate_outline", {
            "project_id": "proj-1",
            "description": "Additional context"
        })
        
        assert len(result) == 1
        assert "outline" in result[0].text.lower() or "Outline" in result[0].text
        assert outline_tools.outline_agent.execute.called
        assert outline_tools.db.update_project.called
    
    @pytest.mark.asyncio
    async def test_generate_outline_without_vision(self, outline_tools):
        """Test outline generation when vision doesn't exist."""
        outline_tools.db.get_project.return_value = {
            'id': 'proj-1',
            'title': 'Test Novel',
            'genre': 'sci-fi',
            'description': 'A test novel',
            'target_chapters': 20
        }
        outline_tools.director.execute.return_value = {
            'vision_document': 'Generated vision'
        }
        outline_tools.outline_agent.execute.return_value = {
            'outline': 'Chapter 1: Introduction'
        }
        
        result = await outline_tools.execute("generate_outline", {
            "project_id": "proj-1"
        })
        
        assert len(result) == 1
        assert outline_tools.director.execute.called
        assert outline_tools.outline_agent.execute.called
    
    @pytest.mark.asyncio
    async def test_generate_outline_project_not_found(self, outline_tools):
        """Test outline generation for non-existent project."""
        outline_tools.db.get_project.return_value = None
        
        result = await outline_tools.execute("generate_outline", {
            "project_id": "proj-1"
        })
        
        assert len(result) == 1
        assert "not found" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, outline_tools):
        """Test executing unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await outline_tools.execute("nonexistent_tool", {})
