"""
Chapter routes for ScribeNet API.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from backend.api.models import ErrorResponse
from backend.memory.database import Database

router = APIRouter(prefix="/api/projects/{project_id}/chapters", tags=["chapters"])


def get_db() -> Database:
    """Get database instance."""
    return Database()


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    responses={404: {"model": ErrorResponse}},
)
async def list_chapters(project_id: str):
    """
    List all chapters for a project.
    
    Args:
        project_id: Project UUID
        
    Returns:
        List of chapters with status and scores
    """
    db = get_db()
    
    # Verify project exists
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    
    try:
        chapters = db.get_project_chapters(project_id)
        
        # Enrich with latest scores
        result = []
        for chapter in chapters:
            chapter_data = {
                "chapter_id": chapter["id"],
                "chapter_number": chapter["chapter_number"],
                "title": chapter["title"],
                "status": chapter["status"],
                "word_count": chapter["word_count"],
                "version": chapter["version"],
            }
            
            # Get latest score
            latest_score = db.get_latest_chapter_score(chapter["id"])
            if latest_score:
                chapter_data["latest_score"] = latest_score["overall_score"]
                chapter_data["scores"] = latest_score["scores"]
            else:
                chapter_data["latest_score"] = None
                chapter_data["scores"] = None
            
            result.append(chapter_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list chapters: {str(e)}",
        )


@router.get(
    "/{chapter_number}",
    response_model=Dict[str, Any],
    responses={404: {"model": ErrorResponse}},
)
async def get_chapter(project_id: str, chapter_number: int):
    """
    Get chapter details including content and scores.
    
    Args:
        project_id: Project UUID
        chapter_number: Chapter number
        
    Returns:
        Chapter details with content and quality scores
    """
    db = get_db()
    
    try:
        # Get chapter by project_id and chapter_number
        chapters = db.get_project_chapters(project_id)
        chapter = next(
            (c for c in chapters if c["chapter_number"] == chapter_number),
            None
        )
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_number} not found in project {project_id}",
            )
        
        # Get latest version content
        versions = db.get_chapter_versions(chapter["id"])
        latest_version = max(versions, key=lambda v: v["version"]) if versions else None
        
        # Get all scores
        scores = db.get_chapter_scores(chapter["id"])
        latest_score = db.get_latest_chapter_score(chapter["id"])
        
        result = {
            "chapter_id": chapter["id"],
            "chapter_number": chapter["chapter_number"],
            "title": chapter["title"],
            "outline": chapter.get("outline", ""),
            "status": chapter["status"],
            "word_count": chapter["word_count"],
            "version": chapter["version"],
            "content": latest_version["content"] if latest_version else "",
            "latest_score": latest_score,
            "all_scores": scores,
            "versions": [
                {
                    "version_id": v["id"],
                    "version": v["version"],
                    "created_by": v["created_by"],
                    "created_at": v["created_at"],
                    "metadata": v.get("metadata", {}),
                }
                for v in versions
            ],
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chapter: {str(e)}",
        )


@router.post(
    "/{chapter_number}/regenerate",
    response_model=Dict[str, Any],
    responses={404: {"model": ErrorResponse}},
)
async def regenerate_chapter(project_id: str, chapter_number: int):
    """
    Trigger regeneration of a chapter.
    
    Args:
        project_id: Project UUID
        chapter_number: Chapter number
        
    Returns:
        Status message
    """
    db = get_db()
    
    try:
        # Get chapter
        chapters = db.get_project_chapters(project_id)
        chapter = next(
            (c for c in chapters if c["chapter_number"] == chapter_number),
            None
        )
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_number} not found",
            )
        
        # Update status to pending for regeneration
        db.update_chapter(chapter["id"], status="pending")
        
        # TODO: Trigger workflow to regenerate chapter
        # This will be implemented when we add workflow control endpoints
        
        return {
            "status": "queued",
            "message": f"Chapter {chapter_number} queued for regeneration",
            "chapter_id": chapter["id"],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate chapter: {str(e)}",
        )
