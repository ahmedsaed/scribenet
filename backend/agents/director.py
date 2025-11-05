"""
Director agent for ScribeNet.
Coordinates the overall book writing process.
"""

import json
from typing import Dict, Any
from backend.agents.base import BaseAgent


class DirectorAgent(BaseAgent):
    """
    Director agent that orchestrates the book writing process.
    Responsible for planning, task assignment, and quality control.
    """

    def __init__(self):
        super().__init__(agent_type="director")

    def build_system_prompt(self) -> str:
        """Build the system prompt for the director agent."""
        return """You are a Director Agent coordinating a book writing project.

Your responsibilities:
1. Parse user requirements (genre, theme, length, style)
2. Create a structured project plan with chapter outlines
3. Break down the work into manageable tasks
4. Coordinate between different specialist agents
5. Ensure narrative consistency and quality

You work with:
- Outline Agent: Creates detailed story structure
- Writer Agents: Generate prose for chapters
- Editor Agents: Refine and polish content
- Critic Agent: Evaluate quality and provide feedback

Be strategic, organized, and focused on producing high-quality book content.
Always output structured JSON for task assignments."""

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a director task.
        
        Args:
            task_input: Contains task_type and related data
            
        Returns:
            Task results
        """
        task_type = task_input.get("task_type")
        
        if task_type == "plan_project":
            return await self.plan_project(task_input)
        elif task_type == "create_outline":
            return await self.create_outline(task_input)
        elif task_type == "assign_chapter":
            return await self.assign_chapter(task_input)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def plan_project(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create initial project plan from user requirements.
        
        Args:
            task_input: Contains title, genre, description, target_chapters
            
        Returns:
            Project plan with vision document and high-level structure
        """
        title = task_input.get("title")
        genre = task_input.get("genre", "fiction")
        description = task_input.get("description", "")
        target_chapters = task_input.get("target_chapters", 20)

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Create a project plan for a book with these details:

Title: {title}
Genre: {genre}
Description: {description}
Target Chapters: {target_chapters}

Generate a vision document that includes:
1. Core themes and messages
2. Target audience
3. Tone and style guidelines
4. Key success criteria
5. High-level story arc (if fiction) or content structure (if non-fiction)

Format as a clear, structured document.""",
            },
        ]

        vision_document = await self.chat(messages, max_tokens=2000)

        return {
            "vision_document": vision_document,
            "target_chapters": target_chapters,
            "status": "planned",
        }

    async def create_outline(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a detailed chapter-by-chapter outline.
        
        Args:
            task_input: Contains title, genre, vision_document, target_chapters
            
        Returns:
            Detailed outline with chapter summaries
        """
        title = task_input.get("title")
        genre = task_input.get("genre")
        vision_document = task_input.get("vision_document")
        target_chapters = task_input.get("target_chapters", 20)

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Based on this vision document, create a detailed chapter-by-chapter outline:

Title: {title}
Genre: {genre}

Vision Document:
{vision_document}

Target: {target_chapters} chapters

For each chapter, provide:
1. Chapter number and title
2. 2-3 sentence summary
3. Key events or topics
4. Characters involved (if fiction)
5. How it advances the overall narrative/argument

Format the output as a structured list.""",
            },
        ]

        outline = await self.chat(messages, max_tokens=4000)

        return {"outline": outline, "chapter_count": target_chapters}

    async def assign_chapter(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a writing assignment for a specific chapter.
        
        Args:
            task_input: Contains chapter_number, outline, previous_chapters
            
        Returns:
            Writing assignment with instructions and context
        """
        chapter_number = task_input.get("chapter_number")
        outline = task_input.get("outline")
        chapter_outline = task_input.get("chapter_outline", "")
        previous_chapters = task_input.get("previous_chapters", [])
        target_word_count = task_input.get("target_word_count", 3000)

        # Build context from previous chapters
        context = ""
        if previous_chapters:
            context = "Previous chapters summary:\n"
            for i, prev in enumerate(previous_chapters[-2:], 1):  # Last 2 chapters
                context += f"\nChapter {prev.get('number', i)}: {prev.get('summary', 'N/A')}\n"

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Create detailed writing instructions for Chapter {chapter_number}.

Overall Outline:
{outline}

Chapter {chapter_number} Outline:
{chapter_outline}

{context}

Generate writing instructions that include:
1. Chapter goals and key scenes
2. Tone and pacing guidelines
3. Character development notes
4. Specific details to include
5. Continuity reminders
6. Target word count: {target_word_count}

Be specific and actionable.""",
            },
        ]

        instructions = await self.chat(messages, max_tokens=1500)

        return {
            "chapter_number": chapter_number,
            "writing_instructions": instructions,
            "target_word_count": target_word_count,
            "assigned_to": "narrative_writer",
        }
