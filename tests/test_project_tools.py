"""
Unit tests for MCP Project Tools.
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from backend.mcp.tools.project_tools import ProjectTools


class TestProjectTools:
    """Test suite for ProjectTools class."""
    
    @pytest.fixture
    def project_tools(self):
        """Create ProjectTools instance with mocked database."""
        tools = ProjectTools()
        tools.db = Mock()
        return tools
    
    def test_get_tools_returns_three_tools(self, project_tools):
        """Test that get_tools returns 3 tool definitions."""
        tools = project_tools.get_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "list_projects" in tool_names
        assert "get_project_info" in tool_names
        assert "create_project" in tool_names
    
    @pytest.mark.asyncio
    async def test_list_projects_success(self, project_tools):
        """Test listing projects successfully."""
        # Mock database response
        project_tools.db.list_projects.return_value = [
            {"id": "proj-1", "title": "Test Book", "genre": "fantasy", "status": "planning", "target_chapters": 20},
            {"id": "proj-2", "title": "Another Book", "genre": "sci-fi", "status": "outlined", "target_chapters": 15},
        ]
        
        result = await project_tools.execute("list_projects", {"limit": 10})
        
        assert len(result) == 1
        assert "Test Book" in result[0].text
        assert "Another Book" in result[0].text
        assert "fantasy" in result[0].text
        project_tools.db.list_projects.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_projects_empty(self, project_tools):
        """Test listing projects when none exist."""
        project_tools.db.list_projects.return_value = []
        
        result = await project_tools.execute("list_projects", {"limit": 10})
        
        assert len(result) == 1
        assert "No projects found" in result[0].text
    
    @pytest.mark.asyncio
    async def test_list_projects_with_limit(self, project_tools):
        """Test listing projects with limit applied."""
        projects = [{"id": f"proj-{i}", "title": f"Book {i}", "genre": "fantasy", "status": "planning"} 
                   for i in range(20)]
        project_tools.db.list_projects.return_value = projects
        
        result = await project_tools.execute("list_projects", {"limit": 5})
        
        # Should only show 5 projects
        lines = result[0].text.split('\n')
        project_lines = [l for l in lines if l.startswith('- ')]
        assert len(project_lines) == 5
    
    @pytest.mark.asyncio
    async def test_get_project_info_success(self, project_tools):
        """Test getting project info successfully."""
        project_tools.db.get_project.return_value = {
            "id": "proj-1",
            "title": "Test Novel",
            "genre": "mystery",
            "status": "writing",
            "target_chapters": 25,
            "description": "A thrilling mystery",
            "vision_document": "Story vision here",
            "outline": "Chapter 1: Intro\nChapter 2: Conflict"
        }
        
        result = await project_tools.execute("get_project_info", {"project_id": "proj-1"})
        
        assert len(result) == 1
        assert "Test Novel" in result[0].text
        assert "mystery" in result[0].text
        assert "writing" in result[0].text
        project_tools.db.get_project.assert_called_once_with("proj-1")
    
    @pytest.mark.asyncio
    async def test_get_project_info_not_found(self, project_tools):
        """Test getting project info when project doesn't exist."""
        project_tools.db.get_project.return_value = None
        
        result = await project_tools.execute("get_project_info", {"project_id": "nonexistent"})
        
        assert len(result) == 1
        assert "not found" in result[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_create_project_success(self, project_tools):
        """Test creating a project successfully."""
        mock_project = {
            "id": "proj-123",
            "title": "New Book",
            "genre": "romance",
            "status": "planning",
            "target_chapters": 30
        }
        
        project_tools.db.create_project.return_value = mock_project
        project_tools.db.get_project.return_value = {**mock_project, "target_chapters": 30}
        
        result = await project_tools.execute("create_project", {
            "title": "New Book",
            "genre": "romance",
            "description": "A love story",
            "target_chapters": 30
        })
        
        assert len(result) == 1
        assert "Created project" in result[0].text or "✅" in result[0].text
        assert "New Book" in result[0].text
        assert project_tools.db.create_project.called
    
    @pytest.mark.asyncio
    async def test_create_project_minimal_args(self, project_tools):
        """Test creating a project with minimal arguments."""
        mock_project = {
            "id": "proj-456",
            "title": "Simple Book",
            "genre": "fantasy",
            "status": "planning",
        }
        
        project_tools.db.create_project.return_value = mock_project
        project_tools.db.get_project.return_value = {**mock_project, "target_chapters": 20}
        
        result = await project_tools.execute("create_project", {
            "title": "Simple Book",
            "genre": "fantasy"
        })
        
        assert len(result) == 1
        assert "Simple Book" in result[0].text
        assert project_tools.db.create_project.called
    
    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, project_tools):
        """Test executing an unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await project_tools.execute("nonexistent_tool", {})
    
    @pytest.mark.asyncio
    async def test_error_handling(self, project_tools):
        """Test that errors are properly propagated."""
        project_tools.db.list_projects.side_effect = Exception("Database error")
        
        # Should raise the exception since we don't catch it
        with pytest.raises(Exception, match="Database error"):
            await project_tools.execute("list_projects", {"limit": 10})
