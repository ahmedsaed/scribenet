"""
Base database module for ScribeNet.
Handles connection management and schema initialization.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager


class DatabaseBase:
    """Base class providing connection management and schema initialization."""

    def __init__(self, db_path: str = "data/scribenet.db"):
        self.db_path = db_path
        # For in-memory databases, we need to maintain a persistent connection
        self._persistent_conn = None
        if db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:")
            self._persistent_conn.row_factory = sqlite3.Row
        else:
            # Ensure data directory exists for file-based databases
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        if self._persistent_conn:
            # For in-memory databases, use the persistent connection
            # Don't close it, just yield it
            try:
                yield self._persistent_conn
                self._persistent_conn.commit()
            except Exception:
                self._persistent_conn.rollback()
                raise
        else:
            # For file-based databases, create a new connection each time
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def init_database(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    genre TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'planning',
                    vision_document TEXT,
                    outline TEXT,
                    target_chapters INTEGER DEFAULT 20
                )
            """)

            # Chapters table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    chapter_number INTEGER NOT NULL,
                    title TEXT,
                    outline TEXT,
                    status TEXT DEFAULT 'planning',
                    word_count INTEGER DEFAULT 0,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    UNIQUE(project_id, chapter_number)
                )
            """)

            # Chapter versions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapter_versions (
                    id TEXT PRIMARY KEY,
                    chapter_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_by TEXT,
                    agent_name TEXT,
                    model TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
                )
            """)

            # Story elements table (story bible)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS story_elements (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    element_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)

            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    input_data TEXT,
                    output_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)

            # Decisions log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    rationale TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)

            # Summaries table (for context compression)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    start_chapter INTEGER NOT NULL,
                    end_chapter INTEGER NOT NULL,
                    summary_text TEXT NOT NULL,
                    version_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)

            # Scores table (for critic evaluations)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    chapter_id TEXT,
                    content_type TEXT NOT NULL,
                    scores JSON NOT NULL,
                    overall_score REAL NOT NULL,
                    feedback TEXT,
                    requires_revision BOOLEAN DEFAULT 0,
                    revision_priority TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
                )
            """)

            # Chat messages table (for Director conversations)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)

            # Create indexes for common queries
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_chapters_project ON chapters(project_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_scores_chapter ON scores(chapter_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_project ON chat_messages(project_id)"
            )

            # Ensure provenance columns exist on chapter_versions for agent tracking
            try:
                cursor.execute("PRAGMA table_info(chapter_versions)")
                existing = [row[1] for row in cursor.fetchall()]
                if 'agent_name' not in existing:
                    cursor.execute("ALTER TABLE chapter_versions ADD COLUMN agent_name TEXT")
                if 'model' not in existing:
                    cursor.execute("ALTER TABLE chapter_versions ADD COLUMN model TEXT")
            except Exception:
                # Non-fatal: older DBs may not support altering, ignore errors
                pass
            
            # Ensure outline and target_chapters columns exist on projects table
            try:
                cursor.execute("PRAGMA table_info(projects)")
                existing = [row[1] for row in cursor.fetchall()]
                if 'outline' not in existing:
                    cursor.execute("ALTER TABLE projects ADD COLUMN outline TEXT")
                if 'target_chapters' not in existing:
                    cursor.execute("ALTER TABLE projects ADD COLUMN target_chapters INTEGER DEFAULT 20")
            except Exception:
                # Non-fatal: older DBs may not support altering, ignore errors
                pass
