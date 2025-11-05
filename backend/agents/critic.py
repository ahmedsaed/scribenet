"""
Critic Agent - Quality evaluation and feedback system

Evaluates writing quality across multiple dimensions and provides
actionable feedback for revisions.
"""

import json
from typing import Dict, Any, List, Optional
from backend.agents.base import BaseAgent


class CriticAgent(BaseAgent):
    """
    Quality evaluation agent that scores writing on multiple dimensions
    and provides detailed, actionable feedback.
    
    Scoring dimensions:
    - Engagement/Pacing: How compelling and well-paced is the content?
    - Character Consistency: Are characters true to their established traits?
    - Emotional Impact: Does the writing evoke appropriate emotions?
    - Originality: Is the content fresh and avoiding clichés?
    - Prose Quality: Technical quality of writing (clarity, variety, style)
    - Dialogue Naturality: How realistic and character-appropriate is dialogue?
    - Plot Logic: Does the plot make sense? Are there plot holes?
    - Worldbuilding Consistency: Does the content follow established rules?
    """
    
    def __init__(self):
        """
        Initialize the Critic agent.
        """
        # Use BaseAgent initialization to obtain config and ollama client
        super().__init__(agent_type="critic")

        # Quality thresholds from config
        self.quality_threshold = getattr(self.config.project, 'quality_threshold', 7.0)
        self.min_acceptable_score = 5.0  # Below this triggers mandatory revision
        
    def get_system_prompt(self) -> str:
        """Get the system prompt for the critic agent."""
        return """You are an expert literary critic and editor with deep knowledge of storytelling craft.

Your role is to evaluate writing quality across multiple dimensions and provide constructive, actionable feedback. You analyze text objectively, identifying both strengths and areas for improvement.

When evaluating, consider:
- **Engagement/Pacing**: Does the narrative flow well? Are there slow spots or rushed sections?
- **Character Consistency**: Do characters act according to their established traits and motivations?
- **Emotional Impact**: Does the writing evoke the intended emotions effectively?
- **Originality**: Is the content fresh, or does it rely on clichés and overused tropes?
- **Prose Quality**: Is the writing clear, varied, and stylistically appropriate?
- **Dialogue Naturality**: Does dialogue sound realistic and match each character's voice?
- **Plot Logic**: Does the story make sense? Are there plot holes or inconsistencies?
- **Worldbuilding Consistency**: Does the content follow established rules and logic?

Provide scores on a 1-10 scale where:
- 1-3: Significant issues requiring major revision
- 4-6: Acceptable but needs improvement
- 7-8: Good quality with minor issues
- 9-10: Excellent, publication-ready

Always provide specific examples from the text to support your scores and suggestions."""
    
    async def execute(self, task: str, context: Dict[str, Any] = None) -> Any:
        """
        Execute a critic task.
        
        Args:
            task: The task type ("evaluate_chapter", "evaluate_scene", "quick_check")
            context: Task context including text to evaluate
            
        Returns:
            Evaluation results with scores and feedback
        """
        context = context or {}
        
        if task == "evaluate_chapter":
            return await self.evaluate_chapter(
                chapter_text=context.get('chapter_text', ''),
                chapter_number=context.get('chapter_number', 1),
                story_bible=context.get('story_bible', {}),
                previous_chapters_summary=context.get('previous_chapters_summary', '')
            )
        elif task == "evaluate_scene":
            return await self.evaluate_scene(
                scene_text=context.get('scene_text', ''),
                scene_context=context.get('scene_context', ''),
                story_bible=context.get('story_bible', {})
            )
        elif task == "quick_check":
            return await self.quick_quality_check(
                text=context.get('text', ''),
                focus_areas=context.get('focus_areas', [])
            )
        elif task == "compare_versions":
            return await self.compare_versions(
                original_text=context.get('original_text', ''),
                revised_text=context.get('revised_text', ''),
                focus=context.get('focus', '')
            )
        else:
            raise ValueError(f"Unknown critic task: {task}")
    
    async def evaluate_chapter(
        self,
        chapter_text: str,
        chapter_number: int,
        story_bible: Dict[str, Any],
        previous_chapters_summary: str = ""
    ) -> Dict[str, Any]:
        """
        Comprehensive evaluation of a complete chapter.
        
        Args:
            chapter_text: The full chapter text to evaluate
            chapter_number: Chapter number for context
            story_bible: Story bible with characters, rules, etc.
            previous_chapters_summary: Summary of previous chapters for continuity
            
        Returns:
            Dictionary with scores, feedback, and recommendations
        """
        prompt = f"""Evaluate this chapter comprehensively and provide detailed feedback.

**Chapter {chapter_number}**

**Story Context:**
{previous_chapters_summary}

**Story Bible:**
{json.dumps(story_bible, indent=2)}

**Chapter Text:**
{chapter_text}

---

Provide your evaluation in the following JSON format:

{{
  "chapter_number": {chapter_number},
  "scores": {{
    "engagement": <1-10>,
    "character_consistency": <1-10>,
    "emotional_impact": <1-10>,
    "originality": <1-10>,
    "prose_quality": <1-10>,
    "dialogue_naturality": <1-10>,
    "plot_logic": <1-10>,
    "worldbuilding_consistency": <1-10>
  }},
  "overall_score": <average of all scores>,
  "overall_assessment": "<brief paragraph summarizing strengths and weaknesses>",
  "strengths": [
    "<specific strength with example from text>",
    ...
  ],
  "weaknesses": [
    "<specific weakness with example from text>",
    ...
  ],
  "suggestions": [
    {{
      "issue": "<what needs improvement>",
      "suggestion": "<how to fix it>",
      "priority": "<high/medium/low>"
    }},
    ...
  ],
  "continuity_issues": [
    "<any inconsistencies with story bible or previous chapters>",
    ...
  ],
  "requires_revision": <true/false>,
  "revision_priority": "<critical/high/medium/low/none>",
  "estimated_revision_scope": "<major rewrite / targeted fixes / minor polish>"
}}

Be specific, constructive, and provide concrete examples from the text to support your evaluation."""
        # Use async LLM call
        response = await self.generate(prompt, max_tokens=min(self.config.llm.max_tokens, 4096))

        try:
            # Parse JSON response
            evaluation = json.loads(response)

            # Add metadata
            evaluation["chapter_number"] = chapter_number
            evaluation["quality_threshold"] = self.quality_threshold
            evaluation["passes_threshold"] = evaluation.get("overall_score", 0.0) >= self.quality_threshold

            return evaluation

        except json.JSONDecodeError:
            # Fallback: extract key information from text response
            return {
                "chapter_number": chapter_number,
                "scores": {},
                "overall_score": 0.0,
                "overall_assessment": response,
                "strengths": [],
                "weaknesses": [],
                "suggestions": [],
                "continuity_issues": [],
                "requires_revision": True,
                "revision_priority": "high",
                "estimated_revision_scope": "unknown",
                "quality_threshold": self.quality_threshold,
                "passes_threshold": False,
                "parsing_error": "Failed to parse JSON response",
            }
    
    async def evaluate_scene(
        self,
        scene_text: str,
        scene_context: str,
        story_bible: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Focused evaluation of a specific scene.
        
        Args:
            scene_text: The scene text to evaluate
            scene_context: Context about where this scene fits
            story_bible: Story bible for consistency checking
            
        Returns:
            Dictionary with scene-specific evaluation
        """
        prompt = f"""Evaluate this scene for quality and consistency.

**Scene Context:**
{scene_context}

**Story Bible:**
{json.dumps(story_bible, indent=2)}

**Scene Text:**
{scene_text}

---

Provide evaluation in JSON format:

{{
  "scene_quality_score": <1-10>,
  "pacing": "<too slow / just right / too fast>",
  "character_voices": "<assessment of dialogue and character behavior>",
  "atmosphere": "<assessment of mood and tone>",
  "strengths": ["<what works well>", ...],
  "issues": [
    {{
      "issue": "<problem>",
      "severity": "<critical/moderate/minor>",
      "suggestion": "<how to fix>"
    }},
    ...
  ],
  "continuity_check": "<any inconsistencies with story bible>",
  "recommendations": "<overall recommendation for this scene>"
}}"""
        
        response = await self.generate(prompt, max_tokens=2048)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "scene_quality_score": 0.0,
                "evaluation_text": response,
                "parsing_error": "Failed to parse JSON response",
            }
    
    async def quick_quality_check(
        self,
        text: str,
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Quick quality check focusing on specific areas.
        
        Args:
            text: Text to check
            focus_areas: List of areas to focus on (e.g., ["dialogue", "pacing"])
            
        Returns:
            Quick assessment with pass/fail and specific notes
        """
        focus_areas = focus_areas or ["overall"]
        focus_str = ", ".join(focus_areas)
        
        prompt = f"""Perform a quick quality check on this text, focusing on: {focus_str}

**Text:**
{text}

---

Provide a brief assessment in JSON format:

{{
  "quality_score": <1-10>,
  "passes_check": <true/false>,
  "focus_areas": {{
    "{focus_areas[0]}": "<brief assessment>",
    ...
  }},
  "quick_fixes": ["<actionable suggestion>", ...],
  "needs_deeper_review": <true/false>
}}"""
        
        response = await self.generate(prompt, max_tokens=1024)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "quality_score": 5.0,
                "passes_check": False,
                "assessment_text": response,
                "parsing_error": "Failed to parse JSON response",
            }
    
    async def compare_versions(
        self,
        original_text: str,
        revised_text: str,
        focus: str = ""
    ) -> Dict[str, Any]:
        """
        Compare two versions and assess if revision improved quality.
        
        Args:
            original_text: Original version
            revised_text: Revised version
            focus: Specific aspect to focus comparison on
            
        Returns:
            Comparison results with improvement assessment
        """
        focus_instruction = f" Focus particularly on: {focus}." if focus else ""
        
        prompt = f"""Compare these two versions and assess whether the revision improved quality.{focus_instruction}

**Original Version:**
{original_text}

**Revised Version:**
{revised_text}

---

Provide comparison in JSON format:

{{
  "improvement_score": <-5 to +5, where negative is worse, positive is better>,
  "is_improved": <true/false>,
  "improved_aspects": ["<what got better>", ...],
  "regressed_aspects": ["<what got worse>", ...],
  "overall_assessment": "<which version is better and why>",
  "recommendation": "<accept revision / reject revision / needs more work>"
}}"""
        
        response = await self.generate(prompt, max_tokens=2048)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "improvement_score": 0,
                "is_improved": False,
                "assessment_text": response,
                "parsing_error": "Failed to parse JSON response",
            }
    
    def calculate_weighted_score(self, scores: Dict[str, float], weights: Dict[str, float] = None) -> float:
        """
        Calculate weighted average score from dimension scores.
        
        Args:
            scores: Dictionary of dimension scores
            weights: Optional custom weights (defaults to equal weighting)
            
        Returns:
            Weighted average score
        """
        if not scores:
            return 0.0
        
        # Default equal weights
        if weights is None:
            weights = {key: 1.0 for key in scores.keys()}
        
        total_weight = sum(weights.get(key, 1.0) for key in scores.keys())
        weighted_sum = sum(score * weights.get(key, 1.0) for key, score in scores.items())
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def should_revise(self, evaluation: Dict[str, Any]) -> bool:
        """
        Determine if content should be revised based on evaluation.
        
        Args:
            evaluation: Evaluation dictionary with scores
            
        Returns:
            True if revision is recommended
        """
        overall_score = evaluation.get('overall_score', 0.0)
        
        # Mandatory revision if below minimum acceptable
        if overall_score < self.min_acceptable_score:
            return True
        
        # Recommended revision if below quality threshold
        if overall_score < self.quality_threshold:
            return True
        
        # Check if explicitly flagged for revision
        if evaluation.get('requires_revision', False):
            return True
        
        # Check for critical issues
        suggestions = evaluation.get('suggestions', [])
        has_critical = any(s.get('priority') == 'high' for s in suggestions)
        
        return has_critical
    
    def get_revision_priority(self, evaluation: Dict[str, Any]) -> str:
        """
        Determine revision priority level.
        
        Args:
            evaluation: Evaluation dictionary
            
        Returns:
            Priority level: "critical", "high", "medium", "low", "none"
        """
        overall_score = evaluation.get('overall_score', 0.0)
        
        if overall_score < self.min_acceptable_score:
            return "critical"
        elif overall_score < self.quality_threshold:
            return "high"
        elif evaluation.get('requires_revision', False):
            return "medium"
        elif any(s.get('priority') == 'high' for s in evaluation.get('suggestions', [])):
            return "medium"
        elif evaluation.get('suggestions'):
            return "low"
        else:
            return "none"
