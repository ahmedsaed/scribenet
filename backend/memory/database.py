"""
Database module for ScribeNet.
Handles SQLite database operations for projects, chapters, story bible, and tasks.

This module uses a modular architecture with separate components for each domain:
- db.base: Connection management and schema initialization
- db.projects: Project CRUD operations
- db.chapters: Chapter and version operations
- db.story_bible: Story element operations
- db.analysis: Scores, tasks, decisions, and summaries
- db.chat: Chat message operations
"""

from backend.memory.db.base import DatabaseBase
from backend.memory.db.projects import ProjectOperations
from backend.memory.db.chapters import ChapterOperations
from backend.memory.db.story_bible import StoryBibleOperations
from backend.memory.db.analysis import AnalysisOperations
from backend.memory.db.chat import ChatOperations


class Database(
    DatabaseBase,
    ProjectOperations,
    ChapterOperations,
    StoryBibleOperations,
    AnalysisOperations,
    ChatOperations,
):
    """
    SQLite database manager for ScribeNet.
    
    Composed of multiple specialized operation classes for better maintainability:
    - DatabaseBase: Connection management and schema initialization
    - ProjectOperations: Project CRUD
    - ChapterOperations: Chapter and version management
    - StoryBibleOperations: Story element management
    - AnalysisOperations: Tasks, decisions, scores, summaries
    - ChatOperations: Chat message management
    """
    
    def __init__(self, db_path: str = "data/scribenet.db"):
        """Initialize the database with all components."""
        # Call parent __init__ to set up connection and schema
        DatabaseBase.__init__(self, db_path)


