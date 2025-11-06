"""
Story bible database operations for ScribeNet.
Handles story elements (characters, locations, themes, etc.).
"""

import json
from typing import Optional, List, Dict, Any


class StoryBibleOperations:
    """Mixin class for story bible related database operations."""

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
