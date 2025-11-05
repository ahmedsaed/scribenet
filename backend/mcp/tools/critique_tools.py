"""
Critique and revision tools for MCP.
"""

from typing import Any, Dict, List, Optional
from mcp.types import Tool, TextContent

from backend.mcp.tools.base import BaseTool
from backend.memory.database import Database
from backend.memory.vector_store import VectorStore
from backend.agents.critic import CriticAgent
from backend.agents.editor import GrammarEditor, StyleEditor, ContinuityEditor
from backend.utils.config import get_config


class CritiqueTools(BaseTool):
    """Tools for critiquing and revising chapters."""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.config = get_config()
        self.critic = CriticAgent()
        self.grammar_editor = GrammarEditor()
        self.style_editor = StyleEditor()
        self.continuity_editor = ContinuityEditor()
    
    def get_tools(self) -> List[Tool]:
        """Return critique tool definitions."""
        return [
            Tool(
                name="critique_chapter",
                description="Run the critic agent to evaluate a chapter's quality across multiple dimensions (prose, pacing, character, dialogue, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The project ID"
                        },
                        "chapter_number": {
                            "type": "integer",
                            "description": "The chapter number to critique"
                        }
                    },
                    "required": ["project_id", "chapter_number"]
                }
            ),
            Tool(
                name="revise_chapter",
                description="Apply revisions to a chapter using the editor agents. Performs grammar, style, and continuity editing.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The project ID"
                        },
                        "chapter_number": {
                            "type": "integer",
                            "description": "The chapter number to revise"
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional: Specific areas to focus on (grammar, style, continuity)",
                            "default": ["grammar", "style", "continuity"]
                        }
                    },
                    "required": ["project_id", "chapter_number"]
                }
            ),
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a critique tool."""
        
        if tool_name == "critique_chapter":
            return await self._critique_chapter(arguments)
        elif tool_name == "revise_chapter":
            return await self._revise_chapter(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
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
    
    async def _critique_chapter(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Critique a chapter."""
        project_id = arguments["project_id"]
        chapter_number = arguments["chapter_number"]
        
        chapter = self._get_chapter_by_number(project_id, chapter_number)  # Fixed: use helper method
        if not chapter:
            return self.format_error(f"Chapter {chapter_number} not found.")
        
        if not chapter.get('content'):
            return self.format_error("Chapter has no content to critique.")
        
        self.logger.info(f"Critiquing chapter {chapter_number}")
        
        # Use Critic agent
        critique_result = await self.critic.execute(
            task="evaluate_chapter",
            context={
                "content": chapter['content'],
                "chapter_number": chapter_number,
                "project_id": project_id,
            }
        )
        
        # Save scores to database
        import uuid
        score_id = str(uuid.uuid4())
        scores = critique_result.get('scores', {})
        overall_score = scores.get('overall_score', 0)
        self.db.save_score(
            score_id=score_id,
            project_id=project_id,
            chapter_id=chapter['id'],
            content_type='chapter',
            scores=scores,
            overall_score=overall_score,
            feedback=critique_result.get('feedback', ''),
            requires_revision=critique_result.get('needs_revision', False),
            revision_priority='medium' if critique_result.get('needs_revision', False) else 'none'
        )
        
        # Format result
        result = f"📊 Critique for Chapter {chapter_number}\n\n"
        result += f"Overall Score: {scores.get('overall_score', 0)}/10\n\n"
        result += "Individual Scores:\n"
        for category, score in scores.items():
            if category != 'overall_score':
                result += f"  - {category.replace('_', ' ').title()}: {score}/10\n"
        
        result += f"\nFeedback:\n{critique_result.get('feedback', 'No feedback')}\n\n"
        
        if critique_result.get('needs_revision'):
            result += "⚠️  This chapter needs revision.\n"
            result += "Use 'revise_chapter' to improve it.\n"
        else:
            result += "✅ This chapter meets quality standards!\n"
        
        return self.format_info(result)
    
    async def _revise_chapter(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Revise a chapter."""
        project_id = arguments["project_id"]
        chapter_number = arguments["chapter_number"]
        focus_areas = arguments.get("focus_areas", ["grammar", "style", "continuity"])
        
        chapter = self._get_chapter_by_number(project_id, chapter_number)  # Fixed: use helper method
        if not chapter:
            return self.format_error(f"Chapter {chapter_number} not found.")
        
        if not chapter.get('content'):
            return self.format_error("Chapter has no content to revise.")
        
        self.logger.info(f"Revising chapter {chapter_number}, focus: {focus_areas}")
        
        content = chapter['content']
        chapter_id = chapter['id']
        revision_notes = []
        
        # Apply each editor based on focus areas
        if "grammar" in focus_areas:
            result = await self.grammar_editor.execute({
                "content": content,
                "chapter_number": chapter_number,
            })
            content = result['edited_content']
            revision_notes.append(f"Grammar: {result.get('notes', 'Applied corrections')}")
        
        if "style" in focus_areas:
            result = await self.style_editor.execute({
                "content": content,
                "chapter_number": chapter_number,
            })
            content = result['edited_content']
            revision_notes.append(f"Style: {result.get('notes', 'Enhanced style')}")
        
        if "continuity" in focus_areas:
            # Get previous chapters for continuity check
            previous_chapters = self.db.get_chapters_by_project(project_id)
            previous_chapters = [c for c in previous_chapters if c['chapter_number'] < chapter_number]
            
            result = await self.continuity_editor.execute({
                "content": content,
                "chapter_number": chapter_number,
                "previous_chapters": previous_chapters[-3:] if previous_chapters else [],
            })
            content = result['edited_content']
            revision_notes.append(f"Continuity: {result.get('notes', 'Checked continuity')}")
        
        # Save revised version
        word_count = len(content.split())
        chapter_id = chapter['id']
        
        # Update chapter metadata
        self.db.update_chapter(
            chapter_id=chapter_id,
            word_count=word_count,
            status="revised"
        )
        
        # Save new content version
        import uuid
        version_id = f"version-{uuid.uuid4()}"
        current_version = chapter.get('version', 1)
        self.db.save_chapter_version(
            version_id=version_id,
            chapter_id=chapter_id,
            version=current_version + 1,
            content=content,
            created_by="system",
            agent_name="EditorAgents",
            metadata={"focus_areas": focus_areas, "revision_notes": revision_notes}
        )
        
        # Update vector store
        try:
            vector_store = VectorStore(persist_directory=self.config.chroma.persist_directory)
            vector_store.update_chapter(
                project_id=project_id,
                chapter_number=chapter_number,
                content=content,
                metadata={"status": "revised", "word_count": word_count}
            )
        except Exception as e:
            self.logger.warning(f"Could not update vector store: {e}")
        
        result = f"Revised Chapter {chapter_number}\n\n"
        result += f"Focus Areas: {', '.join(focus_areas)}\n"
        result += f"New Word Count: {word_count}\n\n"
        result += "Revision Notes:\n"
        for note in revision_notes:
            result += f"  - {note}\n"
        result += "\nChapter status updated to: revised\n"
        
        return self.format_success(result)
