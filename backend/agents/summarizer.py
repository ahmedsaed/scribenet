"""
Summarizer Agent - Context compression and narrative history condensation

Generates concise summaries of completed chapters to manage context windows
and maintain narrative continuity in long-form writing projects.
"""

import json
import hashlib
from typing import Dict, Any, List
from backend.agents.base import BaseAgent


class SummarizerAgent(BaseAgent):
    """
    Context compression agent that creates hierarchical summaries of chapters
    to keep essential information while reducing token count.
    
    Features:
    - Hierarchical summarization (overview + chapter details)
    - Maintains active plot threads and unresolved elements
    - Preserves critical continuity information
    - Caches summaries for reuse
    - Supports incremental and meta-summarization for very long books
    """
    
    def __init__(self):
        """
        Initialize the Summarizer agent.
        
        Args:
            ollama_client: Ollama client instance for LLM communication
            config: Configuration dictionary containing summarizer-specific settings
        """
        # Align with BaseAgent construction (BaseAgent pulls config/ollama itself)
        super().__init__(agent_type="summarizer")

        # Compression settings from config
        try:
            summarizer_config = getattr(self.config.agents, 'summarizer')
            self.compression_ratio = getattr(summarizer_config, 'compression_ratio', 10)
        except Exception:
            self.compression_ratio = 10

        try:
            self.context_threshold = getattr(self.config.memory, 'context_window_threshold', 0.8)
        except Exception:
            self.context_threshold = 0.8
        
    def get_system_prompt(self) -> str:
        """Get the system prompt for the summarizer agent."""
        return """You are an expert literary summarizer specializing in preserving narrative continuity.

Your role is to create concise, information-dense summaries of story chapters that capture all essential information while drastically reducing token count.

When summarizing, you MUST preserve:
- **Major plot events and turning points**
- **Character development and emotional arcs**
- **Key dialogue or revelations**
- **World-building details and established rules**
- **Active subplots and unresolved threads**
- **Continuity details** (locations visited, time passing, character status)
- **Foreshadowing and setup for future events**

Your summaries should be:
- **Comprehensive but concise**: Capture everything important in minimal words
- **Factual and objective**: No interpretation, just what happened
- **Well-organized**: Use clear structure (overall arc + chapter breakdowns)
- **Continuity-focused**: Highlight details that may be referenced later

Target compression ratio: 10:1 (1000 words → 100 word summary)

Format your summaries in structured markdown for easy parsing and readability."""
    
    async def execute(self, task: str, context: Dict[str, Any] = None) -> Any:
        """
        Execute a summarizer task.
        
        Args:
            task: The task type ("summarize_chapters", "summarize_chapter", "meta_summarize")
            context: Task context including chapters to summarize
            
        Returns:
            Summary text and metadata
        """
        context = context or {}
        
        if task == "summarize_chapters":
            return await self.summarize_chapters(
                chapters=context.get('chapters', []),
                story_bible=context.get('story_bible', {})
            )
        elif task == "summarize_chapter":
            return await self.summarize_single_chapter(
                chapter_text=context.get('chapter_text', ''),
                chapter_number=context.get('chapter_number', 1),
                story_bible=context.get('story_bible', {})
            )
        elif task == "meta_summarize":
            return await self.create_meta_summary(
                summaries=context.get('summaries', []),
                story_bible=context.get('story_bible', {})
            )
        elif task == "extract_continuity":
            return await self.extract_continuity_points(
                text=context.get('text', ''),
                story_bible=context.get('story_bible', {})
            )
        else:
            raise ValueError(f"Unknown summarizer task: {task}")
    
    async def summarize_chapters(
        self,
        chapters: List[Dict[str, Any]],
        story_bible: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create hierarchical summary of multiple chapters.
        
        Args:
            chapters: List of chapter dictionaries with 'number', 'title', 'content'
            story_bible: Story bible for context
            
        Returns:
            Dictionary with summary text, metadata, and version hash
        """
        if not chapters:
            return {
                "summary": "",
                "chapter_range": (0, 0),
                "word_count": 0,
                "compression_ratio": 0,
                "version_hash": "",
            }
        
        # Build chapter text for prompt
        chapter_texts = []
        for ch in chapters:
            chapter_texts.append(f"## Chapter {ch['number']}: {ch.get('title', 'Untitled')}{chr(10)}{chr(10)}{ch['content']}")
        
        chapters_combined = f"{chr(10)}{chr(10)}".join(chapter_texts)
        
        start_chapter = chapters[0]['number']
        end_chapter = chapters[-1]['number']
        prompt = f"""Summarize chapters {start_chapter}-{end_chapter} comprehensively and concisely.

**Story Bible Context:**
{json.dumps(story_bible, indent=2)}

**Chapters to Summarize:**
{chapters_combined}

---

Create a structured summary in the following markdown format:

## Overall Summary (Chapters {start_chapter}-{end_chapter})
[2-3 paragraph overview of the major arc, themes, and character development across these chapters]

## Chapter Summaries

### Chapter {start_chapter}: [Title]
- **Key Events:** [bullet points of major plot events]
- **Character Moments:** [important character development or revelations]
- **Plot Threads:** [what subplots were introduced, advanced, or resolved]
- **Continuity Notes:** [specific details that may be referenced later]

[Repeat for each chapter]

## Active Threads at End of Chapter {end_chapter}
- [Unresolved subplot 1]
- [Character arc in progress]
- [Mystery/question needing resolution]
- [Other active elements]

## Critical Continuity Details
- [Important world-building or rules established]
- [Character relationships and current status]
- [Timeline markers and location changes]
- [Items, abilities, or knowledge gained]

Target: Compress to ~{100 * len(chapters)} words while preserving all essential narrative information."""

        # Async LLM call
        summary = await self.generate(prompt, max_tokens=2048)

        # Calculate compression metrics
        original_word_count = sum(len(ch["content"].split()) for ch in chapters)
        summary_word_count = len(summary.split())
        compression_ratio = original_word_count / summary_word_count if summary_word_count > 0 else 0

        # Generate version hash for cache invalidation
        content_hash = hashlib.md5(chapters_combined.encode()).hexdigest()

        return {
            "summary": summary,
            "chapter_range": (start_chapter, end_chapter),
            "original_word_count": original_word_count,
            "summary_word_count": summary_word_count,
            "compression_ratio": compression_ratio,
            "version_hash": content_hash,
            "chapter_count": len(chapters),
        }
    
    async def summarize_single_chapter(
        self,
        chapter_text: str,
        chapter_number: int,
        story_bible: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create detailed summary of a single chapter.
        
        Args:
            chapter_text: Full chapter text
            chapter_number: Chapter number
            story_bible: Story bible for context
            
        Returns:
            Dictionary with summary and metadata
        """
        prompt = f"""Summarize this chapter comprehensively but concisely.

**Story Bible Context:**
{json.dumps(story_bible, indent=2)}

**Chapter {chapter_number}:**
{chapter_text}

---

Provide a structured summary:

### Chapter {chapter_number} Summary
- **Opening:** [How chapter begins]
- **Key Events:** [Major plot events in order]
- **Character Development:** [Changes, revelations, decisions]
- **Emotional Arc:** [Emotional journey through chapter]
- **Plot Advancement:** [How story moves forward]
- **Continuity Details:** [Specific facts that may be referenced]
- **Closing:** [How chapter ends, cliffhanger or resolution]

Target: ~150-200 words."""

        summary = await self.generate(prompt, max_tokens=1024)

        original_word_count = len(chapter_text.split())
        summary_word_count = len(summary.split())
        compression_ratio = original_word_count / summary_word_count if summary_word_count > 0 else 0

        return {
            "summary": summary,
            "chapter_number": chapter_number,
            "original_word_count": original_word_count,
            "summary_word_count": summary_word_count,
            "compression_ratio": compression_ratio,
        }
    
    async def create_meta_summary(
        self,
        summaries: List[str],
        story_bible: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a meta-summary from multiple chapter summaries.
        Used for very long books with tiered compression.
        
        Args:
            summaries: List of summary texts to further compress
            story_bible: Story bible for context
            
        Returns:
            Meta-summary dictionary
        """
        summaries_combined = f"{chr(10)}{chr(10)}---{chr(10)}{chr(10)}".join(summaries)
        
        prompt = f"""Create a high-level summary of these chapter summaries.

**Story Bible Context:**
{json.dumps(story_bible, indent=2)}

**Chapter Summaries:**
{summaries_combined}

---

Provide a meta-summary that captures the overall narrative arc while preserving critical continuity:

## Meta-Summary
[3-4 paragraph overview of the major story developments across all these chapters]

## Major Plot Developments
- [Key plot event 1]
- [Key plot event 2]
...

## Character Arcs
- **[Character Name]:** [Arc summary]
...

## Active Elements
- [Unresolved plots]
- [Character goals]
- [World state]

Target: ~300-400 words."""
        
        meta_summary = await self.generate(prompt, max_tokens=2048)

        return {
            "meta_summary": meta_summary,
            "summaries_count": len(summaries),
            "word_count": len(meta_summary.split()),
        }
    
    async def extract_continuity_points(
        self,
        text: str,
        story_bible: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract critical continuity points from text.
        
        Args:
            text: Text to analyze
            story_bible: Story bible for reference
            
        Returns:
            Dictionary with extracted continuity elements
        """
        prompt = f"""Extract all critical continuity details from this text.

**Story Bible Reference:**
{json.dumps(story_bible, indent=2)}

**Text:**
{text}

---

Identify and extract:

{{
  "characters_introduced": ["name", ...],
  "characters_present": ["name", ...],
  "locations": ["location name", ...],
  "time_markers": ["when this happens", ...],
  "rules_established": ["world-building rule", ...],
  "items_introduced": ["important item", ...],
  "relationships_changed": ["Character A and B now...", ...],
  "promises_made": ["commitment or foreshadowing", ...],
  "unresolved_threads": ["question or conflict", ...]
}}

Return as valid JSON."""
        
        response = await self.generate(prompt, max_tokens=1024)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"extraction_text": response, "parsing_error": "Failed to parse JSON response"}
    
    def estimate_token_count(self, text: str) -> int:
        """
        Rough estimate of token count.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count (rough: 1 token ≈ 0.75 words)
        """
        word_count = len(text.split())
        return int(word_count * 1.33)  # Approximate tokens
    
    def should_summarize(self, current_context_tokens: int, max_context_tokens: int) -> bool:
        """
        Check if summarization is needed based on context size.
        
        Args:
            current_context_tokens: Current token count
            max_context_tokens: Maximum allowed tokens
            
        Returns:
            True if summarization should be triggered
        """
        usage_ratio = current_context_tokens / max_context_tokens
        return usage_ratio >= self.context_threshold
    
    def calculate_summary_range(
        self,
        total_chapters: int,
        recent_chapters_to_keep: int = 2
    ) -> tuple:
        """
        Calculate which chapters should be summarized vs kept in full.
        
        Args:
            total_chapters: Total number of chapters
            recent_chapters_to_keep: Number of recent chapters to keep in full
            
        Returns:
            Tuple of (start_chapter, end_chapter) to summarize
        """
        if total_chapters <= recent_chapters_to_keep:
            return (0, 0)  # Don't summarize yet
        
        # Summarize everything except recent chapters
        end_of_summary = total_chapters - recent_chapters_to_keep
        return (1, end_of_summary)
