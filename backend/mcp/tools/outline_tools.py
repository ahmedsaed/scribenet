"""
Outline generation tools for MCP.
"""

from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from backend.mcp.tools.base import BaseTool
from backend.memory.database import Database
from backend.agents.director import DirectorAgent
from backend.agents.outline import OutlineAgent


class OutlineTools(BaseTool):
    """Tools for generating and managing outlines."""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.outline_agent = OutlineAgent()
        self.director = DirectorAgent()
    
    def get_tools(self) -> List[Tool]:
        """Return outline tool definitions."""
        return [
            Tool(
                name="generate_outline",
                description="Generate a detailed chapter-by-chapter outline for a book project. Creates the story structure and vision.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The project ID to generate outline for"
                        },
                        "description": {
                            "type": "string",
                            "description": "Additional guidance or requirements for the outline"
                        }
                    },
                    "required": ["project_id"]
                }
            ),
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute an outline tool."""
        
        if tool_name == "generate_outline":
            return await self._generate_outline(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _generate_outline(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Generate project outline."""
        project_id = arguments["project_id"]
        additional_desc = arguments.get("description", "")
        
        project = self.db.get_project(project_id)
        if not project:
            return self.format_error(f"Project '{project_id}' not found.")
        
        self.logger.info(f"Generating outline for project: {project['title']}")
        
        # Generate vision if not exists
        vision_document = project.get('vision_document')
        if not vision_document:
            vision_result = await self.director.execute({
                "task_type": "plan_project",
                "title": project['title'],
                "genre": project['genre'],
                "description": project.get('description', '') + ' ' + additional_desc,
                "target_chapters": project.get('target_chapters', 20),
            })
            vision_document = vision_result['vision_document']
            
            # Save vision
            self.db.update_project(project_id, vision_document=vision_document)
        
        # Generate outline using OutlineAgent
        outline_result = await self.outline_agent.execute({
            "task_type": "create_outline",
            "title": project['title'],
            "genre": project['genre'],
            "vision_document": vision_document,
            "target_chapters": project.get('target_chapters', 20),
        })
        
        outline_content = outline_result['outline']
        
        # Save outline to database
        self.db.update_project(project_id, outline=outline_content, status='outlined')
        
        result = f"Generated outline for: {project['title']}\n\n"
        result += f"Outline Preview:\n{outline_content[:800]}...\n\n"
        result += "Full outline saved to project.\n"
        result += "Ready to start writing chapters!\n"
        
        return self.format_success(result)
