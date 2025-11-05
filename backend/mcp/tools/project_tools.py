"""
Project management tools for MCP.
"""

from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from backend.mcp.tools.base import BaseTool
from backend.memory.database import Database


class ProjectTools(BaseTool):
    """Tools for project management (create, list, get info)."""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
    
    def get_tools(self) -> List[Tool]:
        """Return project management tool definitions."""
        return [
            Tool(
                name="list_projects",
                description="List all projects in the system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of projects to return",
                            "default": 10
                        }
                    }
                }
            ),
            Tool(
                name="get_project_info",
                description="Get detailed information about a project by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The unique identifier of the project"
                        }
                    },
                    "required": ["project_id"]
                }
            ),
            Tool(
                name="create_project",
                description="Create a new book writing project with title, genre, and description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the book"
                        },
                        "genre": {
                            "type": "string",
                            "description": "The genre (e.g., sci-fi, mystery, fantasy, romance)"
                        },
                        "description": {
                            "type": "string",
                            "description": "A brief description of the book's concept"
                        },
                        "target_chapters": {
                            "type": "integer",
                            "description": "Number of chapters planned for the book",
                            "default": 20
                        }
                    },
                    "required": ["title", "genre"]
                }
            ),
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a project management tool."""
        
        if tool_name == "list_projects":
            return await self._list_projects(arguments)
        elif tool_name == "get_project_info":
            return await self._get_project_info(arguments)
        elif tool_name == "create_project":
            return await self._create_project(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _list_projects(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List all projects."""
        limit = arguments.get("limit", 10)
        projects = self.db.list_projects()
        
        # Apply limit
        projects = projects[:limit] if limit else projects
        
        if not projects:
            return self.format_info("No projects found in the system.")
        
        result = "Projects:\n"
        for proj in projects:
            result += f"\n- {proj['title']} ({proj['genre']})\n"
            result += f"  ID: {proj['id']}\n"
            result += f"  Status: {proj['status']}\n"
            if proj.get('target_chapters'):
                result += f"  Target Chapters: {proj['target_chapters']}\n"
        
        return self.format_info(result)
    
    async def _get_project_info(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get detailed project information."""
        project_id = arguments["project_id"]
        project = self.db.get_project(project_id)
        
        if not project:
            return self.format_error(f"Project with ID '{project_id}' not found.")
        
        result = f"Project: {project['title']}\n"
        result += f"Genre: {project['genre']}\n"
        result += f"Status: {project['status']}\n"
        result += f"Target Chapters: {project.get('target_chapters', 'Not set')}\n"
        
        if project.get('description'):
            result += f"\nDescription:\n{project['description']}\n"
        
        if project.get('vision_document'):
            result += f"\nVision Document:\n{project['vision_document'][:500]}...\n"
        
        if project.get('outline'):
            result += f"\nOutline:\n{project['outline'][:500]}...\n"
        
        return self.format_info(result)
    
    async def _create_project(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Create a new project."""
        title = arguments["title"]
        genre = arguments["genre"]
        description = arguments.get("description", "")
        target_chapters = arguments.get("target_chapters", 20)
        
        project = self.db.create_project(
            title=title,
            genre=genre,
            description=description,
            target_chapters=target_chapters
        )
        
        result = f"Created project: {project['title']}\n"
        result += f"ID: {project['id']}\n"
        result += f"Genre: {project['genre']}\n"
        result += f"Target Chapters: {target_chapters}\n\n"
        result += "Next steps:\n"
        result += "1. Use 'generate_outline' to create the story structure\n"
        result += "2. Use 'write_chapter' to start writing chapters\n"
        
        return self.format_success(result)
