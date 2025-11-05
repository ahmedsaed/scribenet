"""
Story bible management tools for MCP.
"""

from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from backend.mcp.tools.base import BaseTool
from backend.memory.database import Database
from backend.memory.vector_store import VectorStore
from backend.utils.config import get_config


class StoryBibleTools(BaseTool):
    """Tools for managing the story bible (characters, locations, rules, themes)."""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.config = get_config()
    
    def get_tools(self) -> List[Tool]:
        """Return story bible tool definitions."""
        return [
            Tool(
                name="get_story_bible",
                description="Get the story bible for a project (characters, locations, rules, themes)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The project ID"
                        },
                        "element_type": {
                            "type": "string",
                            "description": "Optional: Filter by type (character, location, rule, theme)",
                            "enum": ["character", "location", "rule", "theme"]
                        }
                    },
                    "required": ["project_id"]
                }
            ),
            Tool(
                name="add_story_element",
                description="Add a new element to the story bible (character, location, rule, or theme)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The project ID"
                        },
                        "element_type": {
                            "type": "string",
                            "description": "Type of element",
                            "enum": ["character", "location", "rule", "theme"]
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the element"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the element"
                        }
                    },
                    "required": ["project_id", "element_type", "name", "description"]
                }
            ),
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a story bible tool."""
        
        if tool_name == "get_story_bible":
            return await self._get_story_bible(arguments)
        elif tool_name == "add_story_element":
            return await self._add_story_element(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _get_story_bible(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get the story bible."""
        project_id = arguments["project_id"]
        element_type = arguments.get("element_type")
        
        story_bible = self.db.get_story_bible(project_id)
        
        if not story_bible:
            return self.format_info(
                "No story bible found for this project. Elements will be created as you write."
            )
        
        # Filter by type if specified
        if element_type:
            elements = story_bible.get(element_type + 's', [])
            if not elements:
                return self.format_info(f"No {element_type}s found in story bible.")
            
            result = f"{element_type.title()}s:\n\n"
            for elem in elements:
                result += f"**{elem.get('name', 'Unnamed')}**\n"
                result += f"{elem.get('description', 'No description')}\n\n"
        else:
            # Show all elements
            result = "Story Bible:\n\n"
            
            for category in ['characters', 'locations', 'rules', 'themes']:
                elements = story_bible.get(category, [])
                if elements:
                    result += f"=== {category.title()} ===\n"
                    for elem in elements:
                        result += f"- {elem.get('name', 'Unnamed')}\n"
                    result += "\n"
        
        return self.format_info(result)
    
    async def _add_story_element(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Add an element to the story bible."""
        project_id = arguments["project_id"]
        element_type = arguments["element_type"]
        name = arguments["name"]
        description = arguments["description"]
        
        project = self.db.get_project(project_id)
        if not project:
            return self.format_error(f"Project '{project_id}' not found.")
        
        # Create story element
        self.db.create_story_element(
            project_id=project_id,
            element_type=element_type,
            name=name,
            description=description
        )
        
        # Add to vector store for semantic search
        try:
            vector_store = VectorStore(persist_directory=self.config.chroma.persist_directory)
            vector_store.add_story_bible_element(
                project_id=project_id,
                element_type=element_type,
                name=name,
                description=description
            )
        except Exception as e:
            self.logger.warning(f"Could not add to vector store: {e}")
        
        result = f"Added {element_type}: {name}\n\n"
        result += f"Description: {description}\n\n"
        result += "This element is now part of the story bible and will be available for context in future chapters.\n"
        
        return self.format_success(result)
