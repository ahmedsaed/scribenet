"""
Unit tests for MCP Chapter Tools.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from backend.mcp.tools.chapter_tools import ChapterTools


class TestChapterTools:
    """Test suite for ChapterTools class."""
    
    @pytest.fixture
    def chapter_tools(self):
        """Create ChapterTools instance with mocked dependencies."""
        tools = ChapterTools()
        tools.db = Mock()
        tools.vector_store = Mock()
        tools.writer = AsyncMock()
        return tools
    
    def test_get_tools_returns_three_tools(self, chapter_tools):
        """Test that get_tools returns 3 tool definitions."""
        tools = chapter_tools.get_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "list_chapters" in tool_names
        assert "get_chapter_content" in tool_names
        assert "write_chapter" in tool_names
    
    @pytest.mark.asyncio
    async def test_list_chapters_success(self, chapter_tools):
        """Test listing chapters successfully."""
        chapter_tools.db.list_chapters.return_value = [
            {"id": "ch-1", "chapter_number": 1, "title": "Chapter 1", "status": "draft", "word_count": 2500},
            {"id": "ch-2", "chapter_number": 2, "title": "Chapter 2", "status": "revised", "word_count": 3000},
        ]
        chapter_tools.db.get_chapter_scores.return_value = []
        
        result = await chapter_tools.execute("list_chapters", {"project_id": "proj-1"})
        
        assert len(result) == 1
        assert "Chapter 1" in result[0].text
        assert "Chapter 2" in result[0].text
        assert "draft" in result[0].text
        assert "2500" in result[0].text
        chapter_tools.db.list_chapters.assert_called_once_with("proj-1")
    
    @pytest.mark.asyncio
    async def test_list_chapters_empty(self, chapter_tools):
        """Test listing chapters when none exist."""
        chapter_tools.db.list_chapters.return_value = []
        
        result = await chapter_tools.execute("list_chapters", {"project_id": "proj-1"})
        
        assert len(result) == 1
        assert "No chapters found" in result[0].text
    
    @pytest.mark.asyncio
    async def test_list_chapters_with_scores(self, chapter_tools):
        """Test listing chapters with quality scores."""
        chapter_tools.db.list_chapters.return_value = [
            {"id": "ch-1", "chapter_number": 1, "title": "Chapter 1", "status": "draft", "word_count": 2500},
        ]
        chapter_tools.db.get_chapter_scores.return_value = [
            {"overall_score": 8.5}
        ]
        
        result = await chapter_tools.execute("list_chapters", {"project_id": "proj-1"})
        
        assert len(result) == 1
        assert "8.5" in result[0].text or "Quality Score" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_chapter_content_success(self, chapter_tools):
        """Test getting chapter content successfully."""
        # Mock the helper method we'll create
        chapter_tools._get_chapter_by_number = Mock(return_value={
            "id": "ch-1",
            "chapter_number": 1,
            "title": "The Beginning",
            "status": "draft",
            "word_count": 2500,
            "content": "Once upon a time..."
        })
        
        result = await chapter_tools.execute("get_chapter_content", {
            "project_id": "proj-1",
            "chapter_number": 1
        })
        
        assert len(result) == 1
        assert "The Beginning" in result[0].text
        assert "Once upon a time" in result[0].text
        assert "2500" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_chapter_content_not_found(self, chapter_tools):
        """Test getting chapter content when chapter doesn't exist."""
        chapter_tools._get_chapter_by_number = Mock(return_value=None)
        
        result = await chapter_tools.execute("get_chapter_content", {
            "project_id": "proj-1",
            "chapter_number": 99
        })
        
        assert len(result) == 1
        assert "not found" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_write_chapter_success(self, chapter_tools):
        """Test writing a chapter successfully."""
        # Mock dependencies
        chapter_tools.db.get_project.return_value = {
            "id": "proj-1",
            "title": "Test Novel",
            "outline": "Chapter 1: Introduction",
            "vision_document": "A great story"
        }
        chapter_tools.db.list_chapters.return_value = []
        chapter_tools.vector_store.search_chapters.return_value = []
        chapter_tools.writer.execute.return_value = {
            "content": "This is the chapter content. It has many words."
        }
        chapter_tools.db.create_chapter.return_value = {
            "id": "ch-1",
            "chapter_number": 1,
            "content": "This is the chapter content. It has many words.",
            "word_count": 8,
            "status": "draft"
        }
        
        result = await chapter_tools.execute("write_chapter", {
            "project_id": "proj-1",
            "chapter_number": 1,
            "additional_guidance": "Make it exciting"
        })
        
        assert len(result) == 1
        assert "Wrote Chapter" in result[0].text or "✅" in result[0].text
        assert chapter_tools.writer.execute.called
        assert chapter_tools.db.create_chapter.called
    
    @pytest.mark.asyncio
    async def test_write_chapter_no_outline(self, chapter_tools):
        """Test writing chapter fails when project has no outline."""
        chapter_tools.db.get_project.return_value = {
            "id": "proj-1",
            "title": "Test Novel",
            "outline": None
        }
        
        result = await chapter_tools.execute("write_chapter", {
            "project_id": "proj-1",
            "chapter_number": 1
        })
        
        assert len(result) == 1
        assert "outline" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_write_chapter_project_not_found(self, chapter_tools):
        """Test writing chapter when project doesn't exist."""
        chapter_tools.db.get_project.return_value = None
        
        result = await chapter_tools.execute("write_chapter", {
            "project_id": "nonexistent",
            "chapter_number": 1
        })
        
        assert len(result) == 1
        assert "not found" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, chapter_tools):
        """Test executing an unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await chapter_tools.execute("nonexistent_tool", {})
