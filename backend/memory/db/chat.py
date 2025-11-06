"""
Chat database operations for ScribeNet.
Handles Director chat messages.
"""

from typing import List, Dict, Any


class ChatOperations:
    """Mixin class for chat message database operations."""

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
