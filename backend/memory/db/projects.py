"""
Project database operations for ScribeNet.
Handles CRUD operations for projects.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any


class ProjectOperations:
    """Mixin class for project-related database operations."""

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
        allowed_fields = ["title", "genre", "status", "vision_document", "outline", "target_chapters"]
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
