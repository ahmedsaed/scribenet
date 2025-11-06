"""
Chapter database operations for ScribeNet.
Handles chapters and chapter versions.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class ChapterOperations:
    """Mixin class for chapter-related database operations."""

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
