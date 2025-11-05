"""
Unit tests for MCP Story Bible Tools.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from backend.mcp.tools.story_bible_tools import StoryBibleTools


class TestStoryBibleTools:
    """Test suite for StoryBibleTools class."""
    
    @pytest.fixture
    def story_bible_tools(self):
        """Create StoryBibleTools instance with mocked dependencies."""
        tools = StoryBibleTools()
        tools.db = Mock()
        tools.vector_store = Mock()
        return tools
    
    def test_get_tools_returns_two_tools(self, story_bible_tools):
        """Test that get_tools returns 2 tool definitions."""
        tools = story_bible_tools.get_tools()
        
        assert len(tools) == 2
        tool_names = [tool.name for tool in tools]
        assert "get_story_bible" in tool_names
        assert "add_story_element" in tool_names
    
    @pytest.mark.asyncio
    async def test_get_story_bible_success(self, story_bible_tools):
        """Test successful story bible retrieval."""
        story_bible_tools.db.get_story_bible.return_value = {
            'characters': [
                {
                    'name': 'John Doe',
                    'description': 'Main protagonist'
                }
            ],
            'locations': [
                {
                    'name': 'City Alpha',
                    'description': 'Futuristic city'
                }
            ]
        }
        
        result = await story_bible_tools.execute("get_story_bible", {
            "project_id": "proj-1"
        })
        
        assert len(result) == 1
        assert "John Doe" in result[0].text or "character" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_get_story_bible_empty(self, story_bible_tools):
        """Test story bible retrieval with no elements."""
        story_bible_tools.db.get_story_bible.return_value = None
        
        result = await story_bible_tools.execute("get_story_bible", {
            "project_id": "proj-1"
        })
        
        assert len(result) == 1
        assert "no" in result[0].text.lower() or "story bible" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_get_story_bible_project_not_found(self, story_bible_tools):
        """Test story bible retrieval for project with empty bible."""
        story_bible_tools.db.get_story_bible.return_value = {}
        
        result = await story_bible_tools.execute("get_story_bible", {
            "project_id": "proj-1"
        })
        
        assert len(result) == 1
        # Should return some result (even if empty)
    
    @pytest.mark.asyncio
    async def test_add_story_element_success(self, story_bible_tools):
        """Test successful story element addition."""
        story_bible_tools.db.get_project.return_value = {
            'id': 'proj-1',
            'title': 'Test Novel'
        }
        story_bible_tools.db.create_story_element.return_value = {
            'id': 'elem-1',
            'element_type': 'character',
            'name': 'Jane Doe',
            'data': {'description': 'Supporting character'}
        }
        
        result = await story_bible_tools.execute("add_story_element", {
            "project_id": "proj-1",
            "element_type": "character",
            "name": "Jane Doe",
            "description": "Supporting character"
        })
        
        assert len(result) == 1
        assert "Added" in result[0].text or "✅" in result[0].text
        assert "Jane Doe" in result[0].text
        assert story_bible_tools.db.create_story_element.called
    
    @pytest.mark.asyncio
    async def test_add_story_element_project_not_found(self, story_bible_tools):
        """Test adding element to non-existent project."""
        story_bible_tools.db.get_project.return_value = None
        
        result = await story_bible_tools.execute("add_story_element", {
            "project_id": "proj-1",
            "element_type": "character",
            "name": "Jane Doe",
            "description": "Supporting character"
        })
        
        assert len(result) == 1
        assert "not found" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, story_bible_tools):
        """Test executing unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await story_bible_tools.execute("nonexistent_tool", {})
