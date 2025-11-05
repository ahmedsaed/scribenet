"""
Unit tests for MCP Critique Tools.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from backend.mcp.tools.critique_tools import CritiqueTools


class TestCritiqueTools:
    """Test suite for CritiqueTools class."""
    
    @pytest.fixture
    def critique_tools(self):
        """Create CritiqueTools instance with mocked dependencies."""
        tools = CritiqueTools()
        tools.db = Mock()
        tools.vector_store = Mock()
        tools.critic = AsyncMock()
        tools.grammar_editor = AsyncMock()
        tools.style_editor = AsyncMock()
        tools.continuity_editor = AsyncMock()
        return tools
    
    def test_get_tools_returns_two_tools(self, critique_tools):
        """Test that get_tools returns 2 tool definitions."""
        tools = critique_tools.get_tools()
        
        assert len(tools) == 2
        tool_names = [tool.name for tool in tools]
        assert "critique_chapter" in tool_names
        assert "revise_chapter" in tool_names
    
    @pytest.mark.asyncio
    async def test_critique_chapter_success(self, critique_tools):
        """Test successful chapter critique."""
        critique_tools.db.list_chapters.return_value = [{
            'id': 'ch-1',
            'chapter_number': 1,
            'title': 'Chapter 1',
            'content': 'Test content',
            'status': 'draft'
        }]
        critique_tools.db.get_latest_chapter_content.return_value = "Test chapter content"
        critique_tools.critic.execute.return_value = {
            'scores': {
                'overall_score': 8.5,
                'plot': 9,
                'characters': 8,
                'pacing': 8
            },
            'feedback': 'Good work!',
            'needs_revision': False
        }
        
        result = await critique_tools.execute("critique_chapter", {
            "project_id": "proj-1",
            "chapter_number": 1
        })
        
        assert len(result) == 1
        assert "Critique" in result[0].text or "📊" in result[0].text
        assert "8.5" in result[0].text or "9" in result[0].text
        assert critique_tools.critic.execute.called
        assert critique_tools.db.save_score.called
    
    @pytest.mark.asyncio
    async def test_critique_chapter_not_found(self, critique_tools):
        """Test critiquing non-existent chapter."""
        critique_tools.db.list_chapters.return_value = []
        
        result = await critique_tools.execute("critique_chapter", {
            "project_id": "proj-1",
            "chapter_number": 1
        })
        
        assert len(result) == 1
        assert "not found" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_critique_chapter_no_content(self, critique_tools):
        """Test critiquing chapter without content."""
        critique_tools.db.list_chapters.return_value = [{
            'id': 'ch-1',
            'chapter_number': 1,
            'title': 'Chapter 1',
            'status': 'draft'
        }]
        critique_tools.db.get_latest_chapter_content.return_value = None
        
        result = await critique_tools.execute("critique_chapter", {
            "project_id": "proj-1",
            "chapter_number": 1
        })
        
        assert len(result) == 1
        assert "no content" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_revise_chapter_not_found(self, critique_tools):
        """Test revising non-existent chapter."""
        critique_tools.db.list_chapters.return_value = []
        
        result = await critique_tools.execute("revise_chapter", {
            "project_id": "proj-1",
            "chapter_number": 1,
            "focus_areas": ["grammar"]
        })
        
        assert len(result) == 1
        assert "not found" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, critique_tools):
        """Test executing unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await critique_tools.execute("nonexistent_tool", {})
