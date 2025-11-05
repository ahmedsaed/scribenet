"""
Writer agent for ScribeNet.
Generates narrative prose for book chapters.
"""

from typing import Dict, Any
from backend.agents.base import BaseAgent


class NarrativeWriterAgent(BaseAgent):
    """
    Narrative writer agent that generates story prose.
    Specializes in main storytelling, action, and narrative flow.
    """

    def __init__(self):
        super().__init__(agent_type="writers", agent_name="narrative")

    def build_system_prompt(self) -> str:
        """Build the system prompt for the narrative writer."""
        return """You are a Narrative Writer Agent specializing in creative storytelling.

Your responsibilities:
1. Write engaging, well-paced narrative prose
2. Develop compelling scenes with vivid descriptions
3. Maintain consistent voice and style throughout
4. Follow the provided outline and instructions carefully
5. Ensure continuity with previous chapters
6. Create immersive, emotionally resonant content

Guidelines:
- Write in a natural, flowing style
- Show, don't tell - use specific details and actions
- Vary sentence structure for rhythm
- Build tension and release appropriately
- End chapters with hooks when appropriate
- Respect character voices and development

You are writing for publication quality - make every word count."""

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a writing task.
        
        Args:
            task_input: Contains writing_instructions, context, word_count
            
        Returns:
            Generated chapter content
        """
        task_type = task_input.get("task_type", "write_chapter")
        
        if task_type == "write_chapter":
            return await self.write_chapter(task_input)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def write_chapter(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write a complete chapter based on instructions.
        
        Args:
            task_input: Contains chapter_number, writing_instructions, 
                       chapter_outline, previous_context, target_word_count
            
        Returns:
            Chapter content and metadata
        """
        chapter_number = task_input.get("chapter_number")
        writing_instructions = task_input.get("writing_instructions")
        chapter_outline = task_input.get("chapter_outline", "")
        previous_context = task_input.get("previous_context", "")
        target_word_count = task_input.get("target_word_count", 3000)

        # Build the writing prompt
        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Write Chapter {chapter_number} following these instructions:

Writing Instructions:
{writing_instructions}

Chapter Outline:
{chapter_outline}

Previous Context:
{previous_context}

Requirements:
- Target word count: {target_word_count} words
- Write complete, polished prose
- Include chapter title at the beginning
- Maintain consistency with previous chapters
- Focus on engaging storytelling

Write the full chapter now:""",
            },
        ]

        # Generate the chapter
        # Use higher max_tokens for longer content
        max_tokens = int(target_word_count * 1.5)  # Tokens ≈ words * 1.3-1.5
        
        chapter_content = await self.chat(
            messages,
            max_tokens=max_tokens,
            temperature=self.temperature,
        )

        # Estimate word count
        word_count = len(chapter_content.split())

        return {
            "chapter_number": chapter_number,
            "content": chapter_content,
            "word_count": word_count,
            "status": "draft",
            "created_by": "narrative_writer",
        }

    async def revise_chapter(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Revise an existing chapter based on feedback.
        
        Args:
            task_input: Contains chapter_content, feedback, revision_instructions
            
        Returns:
            Revised chapter content
        """
        chapter_content = task_input.get("chapter_content")
        feedback = task_input.get("feedback")
        revision_instructions = task_input.get("revision_instructions", "")

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Revise this chapter based on the feedback:

Original Chapter:
{chapter_content}

Feedback:
{feedback}

Revision Instructions:
{revision_instructions}

Provide the complete revised chapter:""",
            },
        ]

        revised_content = await self.chat(messages, max_tokens=6000)

        return {
            "content": revised_content,
            "word_count": len(revised_content.split()),
            "status": "revised",
        }


class DialogueWriterAgent(BaseAgent):
    """
    Dialogue writer agent specializing in character conversations.
    Focuses on authentic voice, subtext, and character interactions.
    """

    def __init__(self):
        super().__init__(agent_type="writers", agent_name="dialogue")

    def build_system_prompt(self) -> str:
        """Build the system prompt for the dialogue writer."""
        return """You are a Dialogue Writer Agent specializing in character conversations.

Your responsibilities:
1. Write authentic, character-specific dialogue
2. Ensure each character has a distinct voice
3. Use subtext and implication effectively
4. Balance dialogue with action beats and description
5. Avoid on-the-nose exposition
6. Create natural conversation flow

Guidelines:
- Each character should sound unique (word choice, sentence structure, speech patterns)
- Use dialogue tags sparingly - action beats often work better
- Include pauses, interruptions, and realistic speech patterns
- Reveal character through how they speak, not just what they say
- Consider power dynamics, relationships, and emotional states
- Make dialogue serve multiple purposes (advance plot, reveal character, create tension)

You are a master of the craft - every line should feel authentic and purposeful."""

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a dialogue writing task."""
        task_type = task_input.get("task_type", "write_dialogue")
        
        if task_type == "write_dialogue":
            return await self.write_dialogue(task_input)
        elif task_type == "enhance_dialogue":
            return await self.enhance_dialogue(task_input)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def write_dialogue(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write dialogue for a specific scene.
        
        Args:
            task_input: Contains scene_context, characters, purpose, tone
            
        Returns:
            Dialogue-focused scene content
        """
        scene_context = task_input.get("scene_context", "")
        characters = task_input.get("characters", [])
        purpose = task_input.get("purpose", "")
        tone = task_input.get("tone", "")
        character_profiles = task_input.get("character_profiles", {})

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Write a dialogue-focused scene with these parameters:

Scene Context:
{scene_context}

Characters Involved:
{', '.join(characters)}

Character Profiles:
{character_profiles}

Purpose of Scene:
{purpose}

Tone:
{tone}

Write the scene focusing on natural, character-specific dialogue. Include necessary action beats and minimal description.""",
            },
        ]

        dialogue_content = await self.chat(messages, max_tokens=2048)

        return {
            "content": dialogue_content,
            "characters": characters,
            "created_by": "dialogue_writer",
        }

    async def enhance_dialogue(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance existing dialogue to make it more natural and character-specific.
        
        Args:
            task_input: Contains scene_content, character_profiles, feedback
            
        Returns:
            Enhanced dialogue
        """
        scene_content = task_input.get("scene_content", "")
        character_profiles = task_input.get("character_profiles", {})
        feedback = task_input.get("feedback", "Make dialogue more natural and distinct")

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Enhance the dialogue in this scene:

Original Scene:
{scene_content}

Character Profiles:
{character_profiles}

Feedback:
{feedback}

Rewrite the dialogue to make it more authentic, character-specific, and effective.""",
            },
        ]

        enhanced_content = await self.chat(messages, max_tokens=2048)

        return {
            "content": enhanced_content,
            "created_by": "dialogue_writer",
        }


class DescriptionWriterAgent(BaseAgent):
    """
    Description writer agent specializing in vivid scene-setting and worldbuilding.
    Focuses on sensory details, atmosphere, and immersive environments.
    """

    def __init__(self):
        super().__init__(agent_type="writers", agent_name="description")

    def build_system_prompt(self) -> str:
        """Build the system prompt for the description writer."""
        return """You are a Description Writer Agent specializing in vivid, immersive scene descriptions.

Your responsibilities:
1. Create rich, sensory descriptions of settings and environments
2. Build atmosphere and mood through description
3. Use all five senses (not just visual)
4. Integrate description seamlessly with action and narrative
5. Reveal world through specific, concrete details
6. Avoid purple prose - be evocative but purposeful

Guidelines:
- Show the world through character perspective
- Use specific, concrete details rather than abstract adjectives
- Engage multiple senses: sight, sound, smell, touch, taste
- Let description serve the story (mood, character state, foreshadowing)
- Vary description density - linger when appropriate, move quickly when needed
- Use fresh metaphors and comparisons sparingly but effectively
- Consider lighting, weather, temperature, textures

You are a master of bringing worlds to life through carefully chosen details."""

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a description writing task."""
        task_type = task_input.get("task_type", "write_description")
        
        if task_type == "write_description":
            return await self.write_description(task_input)
        elif task_type == "enhance_description":
            return await self.enhance_description(task_input)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def write_description(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write detailed description for a location or scene.
        
        Args:
            task_input: Contains location_name, mood, pov_character, purpose
            
        Returns:
            Descriptive content
        """
        location_name = task_input.get("location_name", "")
        location_details = task_input.get("location_details", "")
        mood = task_input.get("mood", "")
        pov_character = task_input.get("pov_character", "")
        purpose = task_input.get("purpose", "")
        word_count = task_input.get("word_count", 300)

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Write a vivid description with these parameters:

Location:
{location_name}

Location Details (from story bible):
{location_details}

Mood/Atmosphere:
{mood}

POV Character:
{pov_character}

Purpose:
{purpose}

Target Length: ~{word_count} words

Write an immersive, sensory-rich description that serves the narrative.""",
            },
        ]

        description_content = await self.chat(messages, max_tokens=int(word_count * 1.5))

        return {
            "content": description_content,
            "location": location_name,
            "created_by": "description_writer",
        }

    async def enhance_description(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance existing description to make it more vivid and immersive.
        
        Args:
            task_input: Contains scene_content, feedback, desired_mood
            
        Returns:
            Enhanced descriptive content
        """
        scene_content = task_input.get("scene_content", "")
        feedback = task_input.get("feedback", "Make descriptions more vivid and sensory")
        desired_mood = task_input.get("desired_mood", "")

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Enhance the descriptive passages in this scene:

Original Scene:
{scene_content}

Feedback:
{feedback}

Desired Mood:
{desired_mood}

Rewrite with more vivid, sensory-rich descriptions while maintaining narrative flow.""",
            },
        ]

        enhanced_content = await self.chat(messages, max_tokens=2048)

        return {
            "content": enhanced_content,
            "created_by": "description_writer",
        }
