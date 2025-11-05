"""
Editor agents for ScribeNet.
Multi-pass editing system for grammar, style, and continuity.
"""

import json
from typing import Dict, Any, List, Optional
from backend.agents.base import BaseAgent


class BaseEditor(BaseAgent):
    """
    Base class for editor agents.
    Provides common editing functionality.
    """

    def __init__(self, agent_type: str, agent_name: str):
        super().__init__(agent_type=agent_type, agent_name=agent_name)

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an editing task."""
        task_type = task_input.get("task_type", "edit")
        
        if task_type == "edit":
            return await self.edit(task_input)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def edit(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Edit content. Subclasses should implement specific editing logic.
        
        Args:
            task_input: Contains content to edit and editing parameters
            
        Returns:
            Edited content with changes tracked
        """
        raise NotImplementedError("Subclasses must implement edit()")

    def format_changes(self, original: str, edited: str, change_list: List[Dict]) -> Dict[str, Any]:
        """
        Format editing results with tracked changes.
        
        Args:
            original: Original content
            edited: Edited content
            change_list: List of changes made
            
        Returns:
            Formatted editing result
        """
        return {
            "original_content": original,
            "edited_content": edited,
            "changes": change_list,
            "editor_type": self.agent_name,
            "change_count": len(change_list)
        }


class GrammarEditor(BaseEditor):
    """
    Grammar editor specializing in spelling, grammar, and punctuation.
    Focuses on technical correctness without changing voice or style.
    """

    def __init__(self):
        super().__init__(agent_type="editors", agent_name="grammar")

    def build_system_prompt(self) -> str:
        """Build the system prompt for the grammar editor."""
        return """You are a Grammar Editor specializing in technical correctness.

Your responsibilities:
1. Fix spelling errors
2. Correct grammar mistakes
3. Fix punctuation errors
4. Ensure proper capitalization
5. Fix sentence fragments and run-ons
6. Correct subject-verb agreement
7. Fix pronoun references

Guidelines:
- Make ONLY grammatical corrections
- DO NOT change voice, style, or word choice unless grammatically incorrect
- DO NOT rewrite for style - only fix errors
- Preserve the author's voice and intent
- Be conservative - only fix clear errors
- Track every change you make

You are the first pass - focus purely on technical correctness."""

    async def edit(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform grammar editing pass.
        
        Args:
            task_input: Contains content, chapter_number
            
        Returns:
            Grammar-corrected content with tracked changes
        """
        content = task_input.get("content", "")
        chapter_number = task_input.get("chapter_number", 0)

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Edit this content for grammar, spelling, and punctuation only:

{content}

Return a JSON object with:
```json
{{
  "edited_content": "The fully corrected text",
  "changes": [
    {{
      "type": "grammar|spelling|punctuation",
      "original": "original text",
      "corrected": "corrected text",
      "explanation": "Brief explanation of the fix"
    }}
  ]
}}
```

Make ONLY grammatical corrections. Do not change style or voice.""",
            },
        ]

        response = await self.chat(messages, max_tokens=int(len(content.split()) * 1.5))

        try:
            # Try to parse JSON response
            result = json.loads(response)
            return self.format_changes(
                original=content,
                edited=result.get("edited_content", content),
                change_list=result.get("changes", [])
            )
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "original_content": content,
                "edited_content": response,
                "changes": [],
                "editor_type": "grammar",
                "error": "Could not parse changes list"
            }


class StyleEditor(BaseEditor):
    """
    Style editor specializing in voice consistency, rhythm, and flow.
    Focuses on improving prose quality while maintaining author voice.
    """

    def __init__(self):
        super().__init__(agent_type="editors", agent_name="style")

    def build_system_prompt(self) -> str:
        """Build the system prompt for the style editor."""
        return """You are a Style Editor specializing in prose quality and consistency.

Your responsibilities:
1. Ensure consistent voice and tone
2. Improve sentence rhythm and flow
3. Vary sentence structure for readability
4. Eliminate redundancy and wordiness
5. Strengthen weak verbs and descriptions
6. Improve pacing
7. Ensure smooth transitions

Guidelines:
- Preserve the author's unique voice
- Make prose more engaging without over-editing
- Cut unnecessary words ("very", "really", "just", excessive adverbs)
- Strengthen passive voice where appropriate
- Vary sentence length and structure
- Ensure paragraphs flow naturally
- Track significant changes with explanations

You are the second pass - focus on making good prose great."""

    async def edit(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform style editing pass.
        
        Args:
            task_input: Contains content, style_guide, reference_examples
            
        Returns:
            Style-improved content with tracked changes
        """
        content = task_input.get("content", "")
        style_guide = task_input.get("style_guide", "")
        reference_examples = task_input.get("reference_examples", "")
        chapter_number = task_input.get("chapter_number", 0)

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Edit this content for style, rhythm, and flow:

{content}

{("Style Guide:" + chr(10) + style_guide) if style_guide else ""}
{("Reference Examples:" + chr(10) + reference_examples) if reference_examples else ""}

Return a JSON object with:
```json
{{
  "edited_content": "The style-improved text",
  "changes": [
    {{
      "type": "rhythm|voice|clarity|pacing|wordiness|other",
      "original": "original passage",
      "improved": "improved passage",
      "explanation": "Why this improves the prose"
    }}
  ],
  "overall_assessment": "Brief assessment of the prose quality"
}}
```

Improve prose quality while preserving voice.""",
            },
        ]

        response = await self.chat(messages, max_tokens=int(len(content.split()) * 1.5))

        try:
            result = json.loads(response)
            return self.format_changes(
                original=content,
                edited=result.get("edited_content", content),
                change_list=result.get("changes", [])
            )
        except json.JSONDecodeError:
            return {
                "original_content": content,
                "edited_content": response,
                "changes": [],
                "editor_type": "style",
                "error": "Could not parse changes list"
            }


class ContinuityEditor(BaseEditor):
    """
    Continuity editor specializing in story consistency.
    Ensures alignment with story bible, previous chapters, and plot logic.
    """

    def __init__(self):
        super().__init__(agent_type="editors", agent_name="continuity")

    def build_system_prompt(self) -> str:
        """Build the system prompt for the continuity editor."""
        return """You are a Continuity Editor specializing in story consistency.

Your responsibilities:
1. Check character consistency (traits, voice, development)
2. Verify setting/worldbuilding accuracy
3. Ensure timeline consistency
4. Validate plot logic and causality
5. Check for contradictions with previous chapters
6. Ensure proper setup and payoff
7. Verify story bible compliance

Guidelines:
- Flag any continuity errors or contradictions
- Suggest fixes that maintain narrative flow
- Ensure character behavior matches their established traits
- Check that worldbuilding rules are followed
- Verify timeline makes sense
- Note any missing setup or unresolved elements
- Track all continuity issues found

You are the third pass - ensure the story holds together logically."""

    async def edit(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform continuity editing pass.
        
        Args:
            task_input: Contains content, story_bible, previous_chapters_summary
            
        Returns:
            Continuity-checked content with issues flagged
        """
        content = task_input.get("content", "")
        story_bible = task_input.get("story_bible", {})
        previous_chapters = task_input.get("previous_chapters_summary", "")
        chapter_number = task_input.get("chapter_number", 0)

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Check this content for continuity issues:

**Chapter {chapter_number} Content:**
{content}

**Story Bible:**
```json
{json.dumps(story_bible, indent=2)}
```

**Previous Chapters Summary:**
{previous_chapters}

Return a JSON object with:
```json
{{
  "edited_content": "Content with any continuity fixes applied",
  "continuity_issues": [
    {{
      "type": "character|setting|timeline|plot|worldbuilding",
      "severity": "minor|major|critical",
      "issue": "Description of the problem",
      "location": "Where in the text",
      "suggestion": "How to fix it",
      "needs_rewrite": true/false
    }}
  ],
  "fixes_applied": [
    {{
      "original": "original text",
      "fixed": "fixed text",
      "reason": "Why this was changed"
    }}
  ],
  "overall_continuity": "Brief assessment of continuity"
}}
```

Fix minor issues, flag major ones for review.""",
            },
        ]

        response = await self.chat(messages, max_tokens=int(len(content.split()) * 1.5))

        try:
            result = json.loads(response)
            return {
                "original_content": content,
                "edited_content": result.get("edited_content", content),
                "changes": result.get("fixes_applied", []),
                "continuity_issues": result.get("continuity_issues", []),
                "editor_type": "continuity",
                "overall_assessment": result.get("overall_continuity", "")
            }
        except json.JSONDecodeError:
            return {
                "original_content": content,
                "edited_content": response,
                "changes": [],
                "continuity_issues": [],
                "editor_type": "continuity",
                "error": "Could not parse response"
            }
