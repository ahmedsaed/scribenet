"""
Vector Store module for ScribeNet.
Handles ChromaDB operations for semantic search and embedding storage.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


class VectorStore:
    """
    ChromaDB vector store manager for semantic search and context retrieval.
    
    Collections:
    - chapters: Full chapter text for similarity search
    - story_bible: Character descriptions, locations, rules
    - style_examples: Reference prose for style matching
    - research_notes: User-provided background material
    """
    
    def __init__(self, persist_directory: str = "data/chroma"):
        """
        Initialize ChromaDB client.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Use sentence transformers for embeddings
        # all-MiniLM-L6-v2 is fast and efficient for semantic search
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize collections
        self._init_collections()
    
    def _init_collections(self):
        """Initialize or get existing collections."""
        # Chapters collection
        self.chapters_collection = self.client.get_or_create_collection(
            name="chapters",
            embedding_function=self.embedding_function,
            metadata={"description": "Full chapter text for semantic search"}
        )
        
        # Story bible collection
        self.story_bible_collection = self.client.get_or_create_collection(
            name="story_bible",
            embedding_function=self.embedding_function,
            metadata={"description": "Characters, locations, world rules"}
        )
        
        # Style examples collection
        self.style_collection = self.client.get_or_create_collection(
            name="style_examples",
            embedding_function=self.embedding_function,
            metadata={"description": "Reference prose for style matching"}
        )
        
        # Research notes collection
        self.research_collection = self.client.get_or_create_collection(
            name="research_notes",
            embedding_function=self.embedding_function,
            metadata={"description": "User-provided background material"}
        )
    
    # ==================== Chapter Operations ====================
    
    def add_chapter(
        self,
        chapter_id: str,
        project_id: str,
        chapter_number: int,
        title: str,
        content: str,
        metadata: Dict[str, Any] = None
    ):
        """
        Add or update a chapter in the vector store.
        
        Args:
            chapter_id: Unique chapter identifier
            project_id: Project identifier
            chapter_number: Chapter number
            title: Chapter title
            content: Full chapter text
            metadata: Additional metadata (characters, locations, themes, etc.)
        """
        metadata = metadata or {}
        
        # Prepare metadata
        chapter_metadata = {
            "project_id": project_id,
            "chapter_number": chapter_number,
            "title": title,
            "document_type": "chapter",
            **metadata
        }
        
        # Add to collection (ChromaDB will replace if ID exists)
        self.chapters_collection.upsert(
            ids=[chapter_id],
            documents=[content],
            metadatas=[chapter_metadata]
        )
    
    def search_chapters(
        self,
        query: str,
        project_id: Optional[str] = None,
        n_results: int = 5,
        where_filter: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant chapters.
        
        Args:
            query: Search query text
            project_id: Optional project filter
            n_results: Number of results to return
            where_filter: Optional metadata filter
            
        Returns:
            List of matching chapters with content and metadata
        """
        # Build filter
        filters = where_filter or {}
        if project_id:
            filters["project_id"] = project_id
        
        # Perform search
        results = self.chapters_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filters if filters else None
        )
        
        # Format results
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted
    
    def get_chapters_by_characters(
        self,
        project_id: str,
        character_names: List[str],
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find chapters where specific characters appear.
        
        Args:
            project_id: Project identifier
            character_names: List of character names
            n_results: Number of results to return
            
        Returns:
            List of matching chapters
        """
        # Search for chapters mentioning characters
        query = f"scenes with {', '.join(character_names)}"
        return self.search_chapters(
            query=query,
            project_id=project_id,
            n_results=n_results
        )
    
    def delete_chapter(self, chapter_id: str):
        """Delete a chapter from the vector store."""
        try:
            self.chapters_collection.delete(ids=[chapter_id])
        except Exception:
            pass  # Chapter may not exist
    
    # ==================== Story Bible Operations ====================
    
    def add_story_element(
        self,
        element_id: str,
        project_id: str,
        element_type: str,
        name: str,
        content: str,
        metadata: Dict[str, Any] = None
    ):
        """
        Add a story bible element (character, location, rule, etc.).
        
        Args:
            element_id: Unique element identifier
            project_id: Project identifier
            element_type: Type (character, location, rule, subplot, theme)
            name: Element name
            content: Text description/content
            metadata: Additional metadata
        """
        metadata = metadata or {}
        
        element_metadata = {
            "project_id": project_id,
            "element_type": element_type,
            "name": name,
            "document_type": "story_bible",
            **metadata
        }
        
        self.story_bible_collection.upsert(
            ids=[element_id],
            documents=[content],
            metadatas=[element_metadata]
        )
    
    def search_story_bible(
        self,
        query: str,
        project_id: Optional[str] = None,
        element_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search story bible elements.
        
        Args:
            query: Search query
            project_id: Optional project filter
            element_type: Optional element type filter
            n_results: Number of results
            
        Returns:
            List of matching story bible elements
        """
        filters = {}
        if project_id:
            filters["project_id"] = project_id
        if element_type:
            filters["element_type"] = element_type
        
        results = self.story_bible_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filters if filters else None
        )
        
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted
    
    def get_character_info(
        self,
        project_id: str,
        character_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get character information from story bible.
        
        Args:
            project_id: Project identifier
            character_name: Character name
            
        Returns:
            Character info or None
        """
        results = self.search_story_bible(
            query=character_name,
            project_id=project_id,
            element_type="character",
            n_results=1
        )
        return results[0] if results else None
    
    def delete_story_element(self, element_id: str):
        """Delete a story bible element."""
        try:
            self.story_bible_collection.delete(ids=[element_id])
        except Exception:
            pass
    
    # ==================== Style Examples Operations ====================
    
    def add_style_example(
        self,
        example_id: str,
        project_id: str,
        content: str,
        style_tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Add a style reference example.
        
        Args:
            example_id: Unique example identifier
            project_id: Project identifier
            content: Example text
            style_tags: Style descriptors (e.g., "suspenseful", "lyrical")
            metadata: Additional metadata
        """
        metadata = metadata or {}
        style_tags = style_tags or []
        
        example_metadata = {
            "project_id": project_id,
            "document_type": "style_example",
            "style_tags": json.dumps(style_tags),
            **metadata
        }
        
        self.style_collection.upsert(
            ids=[example_id],
            documents=[content],
            metadatas=[example_metadata]
        )
    
    def find_similar_style(
        self,
        reference_text: str,
        project_id: Optional[str] = None,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find style examples similar to reference text.
        
        Args:
            reference_text: Text to match style against
            project_id: Optional project filter
            n_results: Number of results
            
        Returns:
            List of similar style examples
        """
        filters = {}
        if project_id:
            filters["project_id"] = project_id
        
        results = self.style_collection.query(
            query_texts=[reference_text],
            n_results=n_results,
            where=filters if filters else None
        )
        
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted
    
    # ==================== Research Notes Operations ====================
    
    def add_research_note(
        self,
        note_id: str,
        project_id: str,
        content: str,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Add research or reference material.
        
        Args:
            note_id: Unique note identifier
            project_id: Project identifier
            content: Note content
            tags: Topic tags
            metadata: Additional metadata
        """
        metadata = metadata or {}
        tags = tags or []
        
        note_metadata = {
            "project_id": project_id,
            "document_type": "research",
            "tags": json.dumps(tags),
            **metadata
        }
        
        self.research_collection.upsert(
            ids=[note_id],
            documents=[content],
            metadatas=[note_metadata]
        )
    
    def search_research(
        self,
        query: str,
        project_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search research notes.
        
        Args:
            query: Search query
            project_id: Optional project filter
            n_results: Number of results
            
        Returns:
            List of matching research notes
        """
        filters = {}
        if project_id:
            filters["project_id"] = project_id
        
        results = self.research_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filters if filters else None
        )
        
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted
    
    # ==================== Utility Operations ====================
    
    def delete_project_data(self, project_id: str):
        """
        Delete all vector data for a project.
        
        Args:
            project_id: Project identifier
        """
        collections = [
            self.chapters_collection,
            self.story_bible_collection,
            self.style_collection,
            self.research_collection
        ]
        
        for collection in collections:
            try:
                # Get all IDs for this project
                results = collection.get(
                    where={"project_id": project_id}
                )
                if results['ids']:
                    collection.delete(ids=results['ids'])
            except Exception:
                pass  # Continue even if deletion fails
    
    def get_collection_stats(self) -> Dict[str, int]:
        """
        Get statistics about all collections.
        
        Returns:
            Dictionary with collection names and document counts
        """
        return {
            "chapters": self.chapters_collection.count(),
            "story_bible": self.story_bible_collection.count(),
            "style_examples": self.style_collection.count(),
            "research_notes": self.research_collection.count()
        }
    
    def reset_all(self):
        """Reset all collections (use with caution!)."""
        self.client.reset()
        self._init_collections()
