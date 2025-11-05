"""
Context search tools for MCP.
"""

from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from backend.mcp.tools.base import BaseTool
from backend.memory.vector_store import VectorStore
from backend.utils.config import get_config


class SearchTools(BaseTool):
    """Tools for semantic search across chapters and story bible."""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
    
    def get_tools(self) -> List[Tool]:
        """Return search tool definitions."""
        return [
            Tool(
                name="search_context",
                description="Search for relevant context across all chapters and story bible using semantic search",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The project ID"
                        },
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5
                        },
                        "search_type": {
                            "type": "string",
                            "description": "What to search: chapters, story_bible, or both",
                            "enum": ["chapters", "story_bible", "both"],
                            "default": "both"
                        }
                    },
                    "required": ["project_id", "query"]
                }
            ),
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a search tool."""
        
        if tool_name == "search_context":
            return await self._search_context(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _search_context(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Search for relevant context."""
        project_id = arguments["project_id"]
        query = arguments["query"]
        limit = arguments.get("limit", 5)
        search_type = arguments.get("search_type", "both")
        
        try:
            vector_store = VectorStore(persist_directory=self.config.chroma.persist_directory)
        except Exception as e:
            return self.format_error(f"Could not initialize vector store: {e}")
        
        results = []
        result_text = f"Search results for: '{query}'\n\n"
        
        # Search chapters
        if search_type in ["chapters", "both"]:
            try:
                chapter_results = vector_store.search_chapters(
                    query=query,
                    project_id=project_id,
                    n_results=limit  # Fixed: use n_results parameter
                )
                
                if chapter_results:
                    result_text += "=== Chapters ===\n\n"
                    for i, chapter in enumerate(chapter_results, 1):
                        result_text += f"{i}. Chapter {chapter.get('chapter_number', 'Unknown')}"
                        if chapter.get('title'):
                            result_text += f": {chapter['title']}"
                        result_text += "\n"
                        
                        # Show excerpt
                        content = chapter.get('content', '')
                        if len(content) > 200:
                            content = content[:200] + "..."
                        result_text += f"   {content}\n\n"
                    
                    results.extend(chapter_results)
            except Exception as e:
                self.logger.warning(f"Could not search chapters: {e}")
                result_text += f"Note: Could not search chapters: {e}\n\n"
        
        # Search story bible
        if search_type in ["story_bible", "both"]:
            try:
                bible_results = vector_store.search_story_bible(
                    query=query,
                    project_id=project_id,
                    n_results=limit  # Fixed: use n_results parameter
                )
                
                if bible_results:
                    result_text += "=== Story Bible ===\n\n"
                    for i, elem in enumerate(bible_results, 1):
                        elem_type = elem.get('element_type', 'unknown')
                        name = elem.get('name', 'Unnamed')
                        description = elem.get('description', 'No description')
                        
                        result_text += f"{i}. [{elem_type.title()}] {name}\n"
                        result_text += f"   {description}\n\n"
                    
                    results.extend(bible_results)
            except Exception as e:
                self.logger.warning(f"Could not search story bible: {e}")
                result_text += f"Note: Could not search story bible: {e}\n\n"
        
        if not results:
            return self.format_info("No results found.")
        
        result_text += f"\nTotal results: {len(results)}\n"
        
        return self.format_success(result_text)
