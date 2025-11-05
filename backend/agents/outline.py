"""
Outline Agent for ScribeNet.
Manages story structure, plot consistency, and story bible.
"""

import json
from typing import Dict, Any, List, Optional
from backend.agents.base import BaseAgent


class OutlineAgent(BaseAgent):
    """
    Outline agent responsible for story structure and story bible management.
    
    Key Functions:
    - Generate initial outline from high-level concept
    - Expand outline with chapter summaries and plot points
    - Maintain character arcs across chapters
    - Track subplot threads
    - Update outline when major changes occur
    - Validate continuity against story bible
    """

    def __init__(self):
        super().__init__(agent_type="outline")

    def build_system_prompt(self) -> str:
        """Build the system prompt for the outline agent."""
        return """You are an Outline Agent specializing in story structure and narrative consistency.

Your responsibilities:
1. Create detailed story outlines with chapter-by-chapter structure
2. Maintain the Story Bible (characters, locations, timeline, worldbuilding rules)
3. Track character arcs and development across chapters
4. Monitor subplot threads and ensure resolution
5. Validate narrative continuity and consistency
6. Update outlines when plot changes occur

Story Bible Elements:
- Characters: Name, role, traits, arc, relationships, key moments
- Locations: Description, significance, rules
- Timeline: Event sequencing, time periods
- Rules: Magic systems, technology levels, social structures
- Themes: Core messages and motifs
- Subplots: Secondary narrative threads

Always output structured JSON with clear organization.
Be meticulous about continuity and internal consistency."""

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an outline task.
        
        Args:
            task_input: Contains task_type and related data
            
        Returns:
            Task results
        """
        task_type = task_input.get("task_type")
        
        if task_type == "create_outline":
            return await self.create_outline(task_input)
        elif task_type == "create_story_bible":
            return await self.create_story_bible(task_input)
        elif task_type == "update_story_bible":
            return await self.update_story_bible(task_input)
        elif task_type == "validate_continuity":
            return await self.validate_continuity(task_input)
        elif task_type == "expand_chapter":
            return await self.expand_chapter(task_input)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def create_outline(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create detailed chapter-by-chapter outline.
        
        Args:
            task_input: Contains vision_document, target_chapters, genre
            
        Returns:
            Structured outline with chapter summaries
        """
        vision = task_input.get("vision_document", "")
        target_chapters = task_input.get("target_chapters", 20)
        genre = task_input.get("genre", "fiction")
        existing_story_bible = task_input.get("story_bible", None)

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Create a detailed outline for a {genre} book with {target_chapters} chapters.

**Vision Document:**
{vision}

{"**Existing Story Bible:** " + json.dumps(existing_story_bible, indent=2) if existing_story_bible else ""}

Generate a structured outline with:

```json
{{
  "outline": [
    {{
      "chapter_number": 1,
      "title": "Chapter Title",
      "summary": "2-3 sentence summary of what happens",
      "key_events": ["Event 1", "Event 2", "Event 3"],
      "characters_involved": ["Character A", "Character B"],
      "location": "Primary location",
      "pov_character": "Character name or null",
      "narrative_progress": "How this advances the overall story",
      "subplots": ["Subplot identifier 1", "Subplot identifier 2"],
      "themes": ["Theme 1", "Theme 2"],
      "estimated_word_count": 3000
    }}
  ],
  "overall_arc": {{
    "act_1": "Setup (chapters X-Y)",
    "act_2": "Confrontation (chapters X-Y)",
    "act_3": "Resolution (chapters X-Y)"
  }},
  "subplot_threads": [
    {{
      "id": "subplot_1",
      "name": "Subplot name",
      "description": "Brief description",
      "introduced_chapter": 1,
      "resolved_chapter": 15,
      "chapters_involved": [1, 3, 5, 7, 15]
    }}
  ]
}}
```

Ensure each chapter builds logically on previous ones."""
            }
        ]

        response = await self.chat(messages, max_tokens=4096, temperature=0.6)
        
        return {
            "outline": response,
            "status": "created"
        }

    async def create_story_bible(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comprehensive story bible from vision and outline.
        
        Args:
            task_input: Contains vision_document, outline, genre
            
        Returns:
            Structured story bible
        """
        vision = task_input.get("vision_document", "")
        outline = task_input.get("outline", "")
        genre = task_input.get("genre", "fiction")

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Create a comprehensive Story Bible for this {genre} project.

**Vision Document:**
{vision}

**Outline:**
{outline}

Generate a detailed story bible with this structure:

```json
{{
  "characters": [
    {{
      "name": "Character Name",
      "role": "protagonist|antagonist|supporting|minor",
      "age": "Age or age range",
      "traits": ["trait1", "trait2", "trait3"],
      "background": "Brief background",
      "goals": "What they want",
      "arc": "How they change throughout the story",
      "relationships": {{
        "Character B": "relationship description"
      }},
      "introduced_chapter": 1,
      "key_moments": [
        {{
          "chapter": 5,
          "event": "Key character moment"
        }}
      ],
      "physical_description": "Physical appearance",
      "voice_notes": "How they speak, mannerisms"
    }}
  ],
  "locations": [
    {{
      "name": "Location Name",
      "type": "city|building|region|planet|etc",
      "description": "Detailed description",
      "significance": "Why it matters to the story",
      "rules": ["Location-specific rule 1", "rule 2"],
      "first_appearance": 1,
      "chapters_featured": [1, 3, 5]
    }}
  ],
  "timeline": [
    {{
      "event": "Event description",
      "time_period": "When it happens",
      "chapter": 1,
      "significance": "Impact on story"
    }}
  ],
  "worldbuilding_rules": {{
    "magic_system": "Description if fantasy",
    "technology_level": "Tech capabilities if sci-fi",
    "social_structure": "How society works",
    "economy": "Economic system",
    "other_rules": ["rule 1", "rule 2"]
  }},
  "themes": [
    {{
      "theme": "Theme name",
      "description": "What this theme explores",
      "how_expressed": "How it appears in the story",
      "key_chapters": [1, 5, 10, 20]
    }}
  ],
  "subplots": [
    {{
      "id": "subplot_1",
      "name": "Subplot name",
      "description": "What this subplot is about",
      "characters_involved": ["Character A", "Character B"],
      "introduced_chapter": 1,
      "resolved_chapter": 15,
      "key_developments": [
        {{
          "chapter": 3,
          "development": "What happens"
        }}
      ]
    }}
  ]
}}
```

Be thorough and ensure all major story elements are documented."""
            }
        ]

        response = await self.chat(messages, max_tokens=4096, temperature=0.4)
        
        return {
            "story_bible": response,
            "status": "created"
        }

    async def update_story_bible(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update story bible with new information or changes.
        
        Args:
            task_input: Contains current_story_bible, updates, reason
            
        Returns:
            Updated story bible
        """
        current_bible = task_input.get("current_story_bible", {})
        updates = task_input.get("updates", {})
        reason = task_input.get("reason", "General update")
        chapter_context = task_input.get("chapter_context", "")

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Update the Story Bible based on new information.

**Current Story Bible:**
```json
{json.dumps(current_bible, indent=2)}
```

**Reason for Update:**
{reason}

**New Information/Updates:**
{json.dumps(updates, indent=2)}

**Context (if from chapter):**
{chapter_context}

Return the COMPLETE updated story bible with the same structure.
Integrate the new information seamlessly.
Highlight what changed in a "changes" field."""
            }
        ]

        response = await self.chat(messages, max_tokens=4096, temperature=0.3)
        
        return {
            "story_bible": response,
            "status": "updated"
        }

    async def validate_continuity(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check chapter content against story bible for continuity errors.
        
        Args:
            task_input: Contains chapter_content, story_bible, chapter_number
            
        Returns:
            Continuity check results with any errors found
        """
        chapter_content = task_input.get("chapter_content", "")
        story_bible = task_input.get("story_bible", {})
        chapter_number = task_input.get("chapter_number", 0)
        previous_chapters_summary = task_input.get("previous_chapters_summary", "")

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Validate continuity for Chapter {chapter_number} against the Story Bible.

**Story Bible:**
```json
{json.dumps(story_bible, indent=2)}
```

**Previous Chapters Summary:**
{previous_chapters_summary}

**Chapter {chapter_number} Content:**
{chapter_content}

Check for:
1. Character consistency (traits, relationships, development)
2. Location accuracy (descriptions, rules)
3. Timeline consistency (event order, time periods)
4. Worldbuilding rule violations
5. Subplot continuity
6. Theme alignment

Return a JSON report:
```json
{{
  "continuity_valid": true/false,
  "errors": [
    {{
      "type": "character|location|timeline|worldbuilding|subplot",
      "severity": "minor|major|critical",
      "description": "What the error is",
      "location_in_chapter": "Approximate location",
      "suggestion": "How to fix"
    }}
  ],
  "warnings": [
    {{
      "type": "category",
      "description": "Potential issue",
      "suggestion": "Recommendation"
    }}
  ],
  "character_developments": [
    {{
      "character": "Name",
      "development": "What changed/happened"
    }}
  ],
  "story_bible_updates_needed": []
}}
```"""
            }
        ]

        response = await self.chat(messages, max_tokens=2048, temperature=0.3)
        
        return {
            "validation_report": response,
            "chapter_number": chapter_number
        }

    async def expand_chapter(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand outline entry for a specific chapter with more detail.
        
        Args:
            task_input: Contains chapter_number, current_outline, story_bible
            
        Returns:
            Detailed chapter outline
        """
        chapter_number = task_input.get("chapter_number")
        current_outline = task_input.get("current_outline", "")
        story_bible = task_input.get("story_bible", {})
        previous_chapter_summary = task_input.get("previous_chapter_summary", "")

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Expand the outline for Chapter {chapter_number} with detailed scene-by-scene breakdown.

**Story Bible:**
```json
{json.dumps(story_bible, indent=2)}
```

**Overall Outline:**
{current_outline}

**Previous Chapter Summary:**
{previous_chapter_summary}

Create a detailed breakdown:
```json
{{
  "chapter_number": {chapter_number},
  "title": "Chapter Title",
  "scenes": [
    {{
      "scene_number": 1,
      "title": "Scene title",
      "setting": "Location and time",
      "characters": ["Character A", "Character B"],
      "pov": "Character name or null",
      "purpose": "What this scene accomplishes",
      "key_events": ["Event 1", "Event 2"],
      "emotional_tone": "Tone of the scene",
      "estimated_words": 800,
      "notes": "Any specific guidance for writer"
    }}
  ],
  "chapter_goals": [
    "Goal 1: Advance main plot",
    "Goal 2: Develop character X",
    "Goal 3: Foreshadow event Y"
  ],
  "opening_hook": "How the chapter should start",
  "closing": "How it should end",
  "transitions": {{
    "from_previous": "Connection to previous chapter",
    "to_next": "Setup for next chapter"
  }}
}}
```"""
            }
        ]

        response = await self.chat(messages, max_tokens=2048, temperature=0.5)
        
        return {
            "expanded_chapter_outline": response,
            "chapter_number": chapter_number
        }
