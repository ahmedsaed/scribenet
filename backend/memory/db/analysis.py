"""
Analysis database operations for ScribeNet.
Handles tasks, decisions, scores, and summaries.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class AnalysisOperations:
    """Mixin class for analysis-related database operations (tasks, decisions, scores, summaries)."""

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
