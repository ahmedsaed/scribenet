"""
Unit tests for MCP Search Tools.
"""

import pytest
from unittest.mock import Mock, patch
from backend.mcp.tools.search_tools import SearchTools


class TestSearchTools:
    """Test suite for SearchTools class."""
    
    @pytest.fixture
    def search_tools(self):
        """Create SearchTools instance."""
        return SearchTools()
    
    def test_get_tools_returns_one_tool(self, search_tools):
        """Test that get_tools returns 1 tool definition."""
        tools = search_tools.get_tools()
        
        assert len(tools) == 1
        assert tools[0].name == "search_context"
    
    @pytest.mark.asyncio
    async def test_search_context_no_results(self, search_tools):
        """Test search with no results."""
        with patch('backend.mcp.tools.search_tools.VectorStore') as mock_vector_store:
            mock_instance = Mock()
            mock_instance.search_chapters.return_value = []
            mock_instance.search_story_bible.return_value = []
            mock_vector_store.return_value = mock_instance
            
            result = await search_tools.execute("search_context", {
                "project_id": "proj-1",
                "query": "nonexistent",
                "search_type": "both",
                "limit": 5
            })
            
            assert len(result) == 1
            assert "no results" in result[0].text.lower() or "search results" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, search_tools):
        """Test executing unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await search_tools.execute("nonexistent_tool", {})
