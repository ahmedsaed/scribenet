"""
Chapter management tools for MCP.
"""

from typing import Any, Dict, List, Optional
from mcp.types import Tool, TextContent

from backend.mcp.tools.base import BaseTool
from backend.memory.database import Database
from backend.memory.vector_store import VectorStore
from backend.agents.writer import NarrativeWriterAgent
from backend.utils.config import get_config


class ChapterTools(BaseTool):
    """Tools for chapter operations (list, get, write)."""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.config = get_config()
        self.vector_store = VectorStore(
            persist_directory=self.config.chroma.persist_directory
        )
        self.writer = NarrativeWriterAgent()
    
    def get_tools(self) -> List[Tool]:
        """Return chapter management tool definitions."""
        return [
            Tool(
                name="list_chapters",
                description="List all chapters in a project with their status and word counts",
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
                name="get_chapter_content",
                description="Get the full content and metadata of a specific chapter",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The unique identifier of the project"
                        },
                        "chapter_number": {
                            "type": "integer",
                            "description": "The chapter number to retrieve"
                        }
                    },
                    "required": ["project_id", "chapter_number"]
                }
            ),
            Tool(
                name="write_chapter",
                description="Write a complete chapter draft using the narrative writer agent. This creates the initial prose.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The project ID"
                        },
                        "chapter_number": {
                            "type": "integer",
                            "description": "The chapter number to write"
                        },
                        "additional_guidance": {
                            "type": "string",
                            "description": "Optional: Additional instructions or focus areas for this chapter"
                        }
                    },
                    "required": ["project_id", "chapter_number"]
                }
            ),
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a chapter management tool."""
        
        if tool_name == "list_chapters":
            return await self._list_chapters(arguments)
        elif tool_name == "get_chapter_content":
            return await self._get_chapter_content(arguments)
        elif tool_name == "write_chapter":
            return await self._write_chapter(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _list_chapters(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List all chapters in a project."""
        project_id = arguments["project_id"]
        chapters = self.db.list_chapters(project_id)  # Fixed: use list_chapters instead of get_chapters_by_project
        
        if not chapters:
            return self.format_info(f"No chapters found for project '{project_id}'.")
        
        result = f"Chapters ({len(chapters)}):\n"
        for chapter in chapters:
            result += f"\nChapter {chapter['chapter_number']}: {chapter.get('title', 'Untitled')}\n"
            result += f"  Status: {chapter['status']}\n"
            result += f"  Word Count: {chapter.get('word_count', 0)}\n"
            
            # Add quality scores if available
            chapter_id = chapter.get('id')
            if chapter_id:
                scores = self.db.get_chapter_scores(chapter_id)  # Fixed: use correct method with chapter_id
                if scores:
                    avg_score = sum(s.get('overall_score', 0) for s in scores) / len(scores)
                    result += f"  Quality Score: {avg_score:.1f}/10\n"
        
        return self.format_info(result)
    
    def _get_chapter_by_number(self, project_id: str, chapter_number: int) -> Optional[Dict[str, Any]]:
        """Helper method to get a chapter by project ID and chapter number with content."""
        chapters = self.db.list_chapters(project_id)
        for chapter in chapters:
            if chapter['chapter_number'] == chapter_number:
                # Get the content from latest version
                chapter_id = chapter['id']
                content = self.db.get_latest_chapter_content(chapter_id)
                if content:
                    chapter['content'] = content
                return chapter
        return None
    
    async def _get_chapter_content(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get full chapter content."""
        project_id = arguments["project_id"]
        chapter_number = arguments["chapter_number"]
        
        chapter = self._get_chapter_by_number(project_id, chapter_number)  # Fixed: use helper method
        
        if not chapter:
            return self.format_error(
                f"Chapter {chapter_number} not found in project '{project_id}'."
            )
        
        result = f"Chapter {chapter['chapter_number']}: {chapter.get('title', 'Untitled')}\n"
        result += f"Status: {chapter['status']}\n"
        result += f"Word Count: {chapter.get('word_count', 0)}\n\n"
        result += f"Content:\n{chapter.get('content', 'No content yet.')}\n"
        
        return self.format_info(result)
    
    async def _write_chapter(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Write a new chapter."""
        project_id = arguments["project_id"]
        chapter_number = arguments["chapter_number"]
        additional_guidance = arguments.get("additional_guidance", "")
        
        project = self.db.get_project(project_id)
        if not project:
            return self.format_error(f"Project '{project_id}' not found.")
        
        if not project.get('outline'):
            return self.format_error(
                "Project needs an outline first. Use 'generate_outline' tool."
            )
        
        self.logger.info(f"Writing chapter {chapter_number} for project: {project['title']}")
        
        # Get recent chapters for context
        previous_chapters = self.db.list_chapters(project_id)  # Fixed: use list_chapters
        previous_chapters = [c for c in previous_chapters if c['chapter_number'] < chapter_number]
        previous_chapters.sort(key=lambda x: x['chapter_number'])
        
        # Build context
        context_parts = []
        if project.get('vision_document'):
            context_parts.append(f"Vision: {project['vision_document'][:500]}")
        
        # Get relevant context from vector store
        search_query = f"Chapter {chapter_number}"
        if additional_guidance:
            search_query += f" {additional_guidance}"
        
        try:
            semantic_context = self.vector_store.search_chapters(
                query=search_query,
                project_id=project_id,
                n_results=3  # Fixed: use n_results parameter
            )
            if semantic_context:
                context_parts.append("Relevant previous content:")
                for ctx in semantic_context:
                    context_parts.append(f"- {ctx.get('content', '')[:200]}...")
        except Exception as e:
            self.logger.warning(f"Could not retrieve semantic context: {e}")
        
        context = "\n".join(context_parts)
        
        # Use NarrativeWriter to write the chapter
        write_result = await self.writer.execute({
            "project_id": project_id,
            "chapter_number": chapter_number,
            "outline": project['outline'],
            "context": context,
            "previous_chapters": previous_chapters[-2:] if previous_chapters else [],
            "additional_guidance": additional_guidance,
        })
        
        chapter_content = write_result['content']
        word_count = len(chapter_content.split())
        
        # Generate IDs
        import uuid
        chapter_id = f"chapter-{uuid.uuid4()}"
        version_id = f"version-{uuid.uuid4()}"
        
        # Save chapter to database (metadata only)
        self.db.create_chapter(
            chapter_id=chapter_id,
            project_id=project_id,
            chapter_number=chapter_number,
            title=f"Chapter {chapter_number}",
            outline=None
        )
        
        # Update chapter with word_count and status
        self.db.update_chapter(
            chapter_id=chapter_id,
            word_count=word_count,
            status="draft"
        )
        
        # Save content as first version
        self.db.save_chapter_version(
            version_id=version_id,
            chapter_id=chapter_id,
            version=1,
            content=chapter_content,
            created_by="system",
            agent_name="NarrativeWriter",
            metadata={"additional_guidance": additional_guidance}
        )
        
        # Add to vector store
        try:
            self.vector_store.add_chapter(
                project_id=project_id,
                chapter_number=chapter_number,
                content=chapter_content,
                metadata={"status": "draft", "word_count": word_count}
            )
        except Exception as e:
            self.logger.warning(f"Could not add to vector store: {e}")
        
        result = f"Wrote Chapter {chapter_number}\n\n"
        result += f"Word Count: {word_count}\n"
        result += f"Status: draft\n\n"
        result += f"Preview:\n{chapter_content[:500]}...\n\n"
        result += "Next steps:\n"
        result += "- Use 'critique_chapter' to evaluate quality\n"
        result += "- Use 'revise_chapter' to improve the draft\n"
        
        return self.format_success(result)
