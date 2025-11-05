"""
State management for LangGraph workflows.
"""

from typing import TypedDict, List, Dict, Any, Optional


class ProjectState(TypedDict, total=False):
    """State for project workflow."""
    
    # Project info
    project_id: str
    title: str
    genre: str
    description: str
    target_chapters: int
    
    # Vision and planning
    vision_document: Optional[str]
    outline: Optional[str]
    
    # Current progress
    current_chapter: int
    completed_chapters: List[int]
    
    # Agent outputs
    chapter_instructions: Optional[Dict[str, Any]]
    chapter_content: Optional[str]
    
    # Status
    phase: str  # planning, outlining, writing, completed
    error: Optional[str]


class ChapterState(TypedDict, total=False):
    """State for chapter writing workflow."""
    
    # Chapter info
    project_id: str
    chapter_id: str
    chapter_number: int
    
    # Input
    outline: str
    chapter_outline: str
    previous_context: str
    target_word_count: int
    
    # Agent outputs
    writing_instructions: Optional[str]
    chapter_content: Optional[str]
    word_count: Optional[int]
    
    # Status
    status: str  # planning, writing, completed
    error: Optional[str]
