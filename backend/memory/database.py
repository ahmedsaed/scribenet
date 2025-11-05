"""
Database module for ScribeNet.
Handles SQLite database operations for projects, chapters, story bible, and tasks.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class Database:
    """SQLite database manager for ScribeNet."""

    def __init__(self, db_path: str = "data/scribenet.db"):
        self.db_path = db_path
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
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
                    vision_document TEXT
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

    # ==================== Project Operations ====================

    def create_project(
        self,
        project_id: str,
        title: str,
        genre: Optional[str] = None,
        vision_document: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO projects (id, title, genre, vision_document, status)
                VALUES (?, ?, ?, ?, 'planning')
            """,
                (project_id, title, genre, vision_document),
            )
        
        # Get the project after the connection is committed
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Failed to retrieve created project {project_id}")
        return project

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def update_project(self, project_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update project fields."""
        allowed_fields = ["title", "genre", "status", "vision_document"]
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return self.get_project(project_id)

        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [project_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
            return self.get_project(project_id)

    def delete_project(self, project_id: str) -> bool:
        """Delete project and all related data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cursor.rowcount > 0

    # ==================== Chapter Operations ====================

    def create_chapter(
        self,
        chapter_id: str,
        project_id: str,
        chapter_number: int,
        title: Optional[str] = None,
        outline: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new chapter."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chapters (id, project_id, chapter_number, title, outline, status)
                VALUES (?, ?, ?, ?, ?, 'planning')
            """,
                (chapter_id, project_id, chapter_number, title, outline),
            )
            return self.get_chapter(chapter_id)

    def get_chapter(self, chapter_id: str) -> Optional[Dict[str, Any]]:
        """Get chapter by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chapters WHERE id = ?", (chapter_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_chapters(self, project_id: str) -> List[Dict[str, Any]]:
        """List all chapters for a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chapters WHERE project_id = ? ORDER BY chapter_number",
                (project_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_project_chapters(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all chapters for a project (alias for list_chapters)."""
        return self.list_chapters(project_id)

    def update_chapter(self, chapter_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update chapter fields."""
        allowed_fields = ["title", "outline", "status", "word_count", "version"]
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return self.get_chapter(chapter_id)

        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [chapter_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE chapters SET {set_clause} WHERE id = ?", values)
            return self.get_chapter(chapter_id)

    # ==================== Chapter Version Operations ====================

    def save_chapter_version(
        self,
        version_id: str,
        chapter_id: str,
        version: int,
        content: str,
        created_by: str,
        metadata: Optional[Dict[str, Any]] = None,
        agent_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a chapter version."""
        metadata_json = json.dumps(metadata) if metadata else None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chapter_versions (id, chapter_id, version, content, created_by, agent_name, model, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (version_id, chapter_id, version, content, created_by, agent_name, model, metadata_json),
            )

            cursor.execute(
                "SELECT * FROM chapter_versions WHERE id = ?", (version_id,)
            )
            row = cursor.fetchone()
            result = dict(row)
            if result.get("metadata"):
                result["metadata"] = json.loads(result["metadata"])
            return result

    def get_chapter_versions(self, chapter_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a chapter."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chapter_versions WHERE chapter_id = ? ORDER BY version DESC",
                (chapter_id,),
            )
            results = [dict(row) for row in cursor.fetchall()]
            for result in results:
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"])
            return results

    def get_latest_chapter_content(self, chapter_id: str) -> Optional[str]:
        """Get the latest content for a chapter."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT content FROM chapter_versions 
                WHERE chapter_id = ? 
                ORDER BY version DESC 
                LIMIT 1
            """,
                (chapter_id,),
            )
            row = cursor.fetchone()
            return row["content"] if row else None

    # ==================== Story Element Operations ====================

    def create_story_element(
        self,
        element_id: str,
        project_id: str,
        element_type: str,
        name: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a story element (character, location, etc)."""
        data_json = json.dumps(data)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO story_elements (id, project_id, element_type, name, data)
                VALUES (?, ?, ?, ?, ?)
            """,
                (element_id, project_id, element_type, name, data_json),
            )

            cursor.execute("SELECT * FROM story_elements WHERE id = ?", (element_id,))
            row = cursor.fetchone()
            result = dict(row)
            result["data"] = json.loads(result["data"])
            return result

    def list_story_elements(
        self, project_id: str, element_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List story elements for a project, optionally filtered by type."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if element_type:
                cursor.execute(
                    "SELECT * FROM story_elements WHERE project_id = ? AND element_type = ?",
                    (project_id, element_type),
                )
            else:
                cursor.execute(
                    "SELECT * FROM story_elements WHERE project_id = ?", (project_id,)
                )

            results = [dict(row) for row in cursor.fetchall()]
            for result in results:
                result["data"] = json.loads(result["data"])
            return results

    def get_story_element(
        self, project_id: str, element_type: str, name: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific story element by type and name."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM story_elements 
                   WHERE project_id = ? AND element_type = ? AND name = ?""",
                (project_id, element_type, name),
            )
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result["data"] = json.loads(result["data"])
                return result
            return None

    def update_story_element(
        self,
        element_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a story element's data."""
        data_json = json.dumps(data)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE story_elements 
                   SET data = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (data_json, element_id),
            )
            
            cursor.execute("SELECT * FROM story_elements WHERE id = ?", (element_id,))
            row = cursor.fetchone()
            result = dict(row)
            result["data"] = json.loads(result["data"])
            return result

    def delete_story_element(self, element_id: str) -> bool:
        """Delete a story element."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM story_elements WHERE id = ?", (element_id,))
            return cursor.rowcount > 0

    def get_story_bible(self, project_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get complete story bible organized by element type."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM story_elements WHERE project_id = ? ORDER BY element_type, name",
                (project_id,),
            )
            
            # Organize by type
            story_bible = {
                "characters": [],
                "locations": [],
                "timeline": [],
                "worldbuilding_rules": [],
                "themes": [],
                "subplots": []
            }
            
            for row in cursor.fetchall():
                element = dict(row)
                element["data"] = json.loads(element["data"])
                element_type = element["element_type"]
                
                if element_type in story_bible:
                    story_bible[element_type].append(element)
                else:
                    # Handle custom types
                    if "other" not in story_bible:
                        story_bible["other"] = []
                    story_bible["other"].append(element)
            
            return story_bible

    def save_full_story_bible(
        self, project_id: str, story_bible_data: Dict[str, Any]
    ) -> None:
        """
        Save or update complete story bible.
        This replaces all existing story elements for the project.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete existing story elements
            cursor.execute("DELETE FROM story_elements WHERE project_id = ?", (project_id,))
            
            # Insert new ones
            import uuid
            for element_type, elements in story_bible_data.items():
                if not isinstance(elements, list):
                    # Handle worldbuilding_rules which might be a dict
                    if element_type == "worldbuilding_rules":
                        element_id = str(uuid.uuid4())
                        cursor.execute(
                            """INSERT INTO story_elements (id, project_id, element_type, name, data)
                               VALUES (?, ?, ?, ?, ?)""",
                            (element_id, project_id, "worldbuilding_rules", "rules", json.dumps(elements)),
                        )
                    continue
                
                for element in elements:
                    element_id = str(uuid.uuid4())
                    name = element.get("name", element.get("theme", element.get("id", "unnamed")))
                    cursor.execute(
                        """INSERT INTO story_elements (id, project_id, element_type, name, data)
                           VALUES (?, ?, ?, ?, ?)""",
                        (element_id, project_id, element_type, str(name), json.dumps(element)),
                    )

    # ==================== Task Operations ====================

    def create_task(
        self,
        task_id: str,
        project_id: str,
        agent_type: str,
        task_type: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new task."""
        input_json = json.dumps(input_data)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tasks (id, project_id, agent_type, task_type, input_data, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """,
                (task_id, project_id, agent_type, task_type, input_json),
            )

            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            result = dict(row)
            result["input_data"] = json.loads(result["input_data"]) if result["input_data"] else None
            result["output_data"] = json.loads(result["output_data"]) if result["output_data"] else None
            return result

    def update_task_status(
        self,
        task_id: str,
        status: str,
        output_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update task status and optionally set output data."""
        output_json = json.dumps(output_data) if output_data else None
        completed_at = datetime.now().isoformat() if status == "completed" else None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tasks 
                SET status = ?, output_data = ?, completed_at = ?
                WHERE id = ?
            """,
                (status, output_json, completed_at, task_id),
            )

            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            result = dict(row)
            result["input_data"] = json.loads(result["input_data"]) if result["input_data"] else None
            result["output_data"] = json.loads(result["output_data"]) if result["output_data"] else None
            return result

    def list_tasks(
        self, project_id: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tasks for a project, optionally filtered by status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    "SELECT * FROM tasks WHERE project_id = ? AND status = ? ORDER BY created_at",
                    (project_id, status),
                )
            else:
                cursor.execute(
                    "SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at",
                    (project_id,),
                )

            results = [dict(row) for row in cursor.fetchall()]
            for result in results:
                result["input_data"] = json.loads(result["input_data"]) if result["input_data"] else None
                result["output_data"] = json.loads(result["output_data"]) if result["output_data"] else None
            return results

    # ==================== Decision Log Operations ====================

    def log_decision(
        self,
        decision_id: str,
        project_id: str,
        agent_id: str,
        decision_type: str,
        rationale: str,
    ) -> Dict[str, Any]:
        """Log an agent decision."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO decisions (id, project_id, agent_id, decision_type, rationale)
                VALUES (?, ?, ?, ?, ?)
            """,
                (decision_id, project_id, agent_id, decision_type, rationale),
            )

            cursor.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
            row = cursor.fetchone()
            return dict(row)

    # ==================== Score Operations ====================

    def save_score(
        self,
        score_id: str,
        project_id: str,
        chapter_id: Optional[str],
        content_type: str,
        scores: Dict[str, Any],
        overall_score: float,
        feedback: str = "",
        requires_revision: bool = False,
        revision_priority: str = "none",
    ) -> Dict[str, Any]:
        """Save a quality score evaluation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scores (
                    id, project_id, chapter_id, content_type,
                    scores, overall_score, feedback,
                    requires_revision, revision_priority
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    score_id,
                    project_id,
                    chapter_id,
                    content_type,
                    json.dumps(scores),
                    overall_score,
                    feedback,
                    1 if requires_revision else 0,
                    revision_priority,
                ),
            )

            cursor.execute("SELECT * FROM scores WHERE id = ?", (score_id,))
            row = cursor.fetchone()
            result = dict(row)
            result["scores"] = json.loads(result["scores"])
            return result

    def get_chapter_scores(self, chapter_id: str) -> List[Dict[str, Any]]:
        """Get all scores for a chapter."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM scores WHERE chapter_id = ? ORDER BY created_at DESC",
                (chapter_id,),
            )
            results = [dict(row) for row in cursor.fetchall()]

            for result in results:
                result["scores"] = json.loads(result["scores"])
            return results

    def get_latest_chapter_score(self, chapter_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent score for a chapter."""
        scores = self.get_chapter_scores(chapter_id)
        return scores[0] if scores else None

    def get_project_scores(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all scores for a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM scores WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            )
            results = [dict(row) for row in cursor.fetchall()]

            for result in results:
                result["scores"] = json.loads(result["scores"])
            return results

    # ==================== Summary Operations ====================

    def save_summary(
        self,
        summary_id: str,
        project_id: str,
        start_chapter: int,
        end_chapter: int,
        summary_text: str,
        version_hash: str,
    ) -> Dict[str, Any]:
        """Save a chapter summary for context compression."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if summary for this range already exists
            cursor.execute(
                """
                SELECT id FROM summaries
                WHERE project_id = ? AND start_chapter = ? AND end_chapter = ?
            """,
                (project_id, start_chapter, end_chapter),
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing summary
                cursor.execute(
                    """
                    UPDATE summaries
                    SET summary_text = ?, version_hash = ?, created_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (summary_text, version_hash, existing["id"]),
                )
                summary_id = existing["id"]
            else:
                # Insert new summary
                cursor.execute(
                    """
                    INSERT INTO summaries (
                        id, project_id, start_chapter, end_chapter,
                        summary_text, version_hash
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (summary_id, project_id, start_chapter, end_chapter, summary_text, version_hash),
                )

            cursor.execute("SELECT * FROM summaries WHERE id = ?", (summary_id,))
            row = cursor.fetchone()
            return dict(row)

    def get_summary(
        self, project_id: str, start_chapter: int, end_chapter: int
    ) -> Optional[Dict[str, Any]]:
        """Get summary for a chapter range."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM summaries
                WHERE project_id = ? AND start_chapter = ? AND end_chapter = ?
                ORDER BY created_at DESC
                LIMIT 1
            """,
                (project_id, start_chapter, end_chapter),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_project_summaries(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all summaries for a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM summaries WHERE project_id = ? ORDER BY start_chapter",
                (project_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def invalidate_summaries(self, project_id: str, chapter_number: int) -> None:
        """Invalidate summaries that include a modified chapter."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM summaries
                WHERE project_id = ? AND start_chapter <= ? AND end_chapter >= ?
            """,
                (project_id, chapter_number, chapter_number),
            )

    # ==================== Chat Message Operations ====================

    def save_chat_message(
        self,
        message_id: str,
        project_id: str,
        sender: str,  # 'user' or 'assistant'
        message: str,
    ) -> Dict[str, Any]:
        """Save a chat message to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_messages (id, project_id, sender, message)
                VALUES (?, ?, ?, ?)
            """,
                (message_id, project_id, sender, message),
            )
            cursor.execute("SELECT * FROM chat_messages WHERE id = ?", (message_id,))
            row = cursor.fetchone()
            return dict(row)

    def get_chat_messages(self, project_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get chat messages for a project, ordered by creation time."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM chat_messages
                WHERE project_id = ?
                ORDER BY created_at ASC
                LIMIT ?
            """,
                (project_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def clear_chat_messages(self, project_id: str) -> None:
        """Clear all chat messages for a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM chat_messages WHERE project_id = ?",
                (project_id,),
            )


