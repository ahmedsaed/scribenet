"""
Project routes for ScribeNet API.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List
import uuid

from backend.api.models import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ErrorResponse,
)
from backend.memory.database import Database

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_db() -> Database:
    """Get database instance."""
    return Database()


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def create_project(project_data: ProjectCreate):
    """
    Create a new book project.
    
    Args:
        project_data: Project creation data
        
    Returns:
        Created project details
    """
    db = get_db()
    project_id = str(uuid.uuid4())
    
    try:
        project = db.create_project(
            project_id=project_id,
            title=project_data.title,
            genre=project_data.genre,
            vision_document=project_data.vision_document,
        )
        return ProjectResponse(**project)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create project: {str(e)}",
        )


@router.get(
    "",
    response_model=List[ProjectResponse],
    responses={500: {"model": ErrorResponse}},
)
async def list_projects():
    """
    List all projects.
    
    Returns:
        List of all projects
    """
    db = get_db()
    
    try:
        projects = db.list_projects()
        return [ProjectResponse(**p) for p in projects]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}",
        )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_project(project_id: str):
    """
    Get project details by ID.
    
    Args:
        project_id: Project UUID
        
    Returns:
        Project details
    """
    db = get_db()
    
    try:
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )
        return ProjectResponse(**project)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project: {str(e)}",
        )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def update_project(project_id: str, update_data: ProjectUpdate):
    """
    Update project details.
    
    Args:
        project_id: Project UUID
        update_data: Fields to update
        
    Returns:
        Updated project details
    """
    db = get_db()
    
    # Check if project exists
    existing = db.get_project(project_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    
    # Get only the fields that were set
    update_dict = update_data.model_dump(exclude_unset=True)
    
    if not update_dict:
        # No updates provided, return existing
        return ProjectResponse(**existing)
    
    try:
        updated = db.update_project(project_id, **update_dict)
        return ProjectResponse(**updated)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update project: {str(e)}",
        )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_project(project_id: str):
    """
    Delete a project and all related data.
    
    Args:
        project_id: Project UUID
    """
    db = get_db()
    
    # Check if project exists
    existing = db.get_project(project_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    
    try:
        db.delete_project(project_id)
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}",
        )
