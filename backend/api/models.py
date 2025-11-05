"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    title: str = Field(..., min_length=1, max_length=200, description="Project title")
    genre: Optional[str] = Field(None, max_length=100, description="Book genre")
    vision_document: Optional[str] = Field(None, description="Vision and goals for the project")


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    genre: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, pattern="^(planning|drafting|editing|completed)$")
    vision_document: Optional[str] = None


class ProjectResponse(BaseModel):
    """Response model for project data."""
    id: str
    title: str
    genre: Optional[str]
    created_at: str
    updated_at: str
    status: str
    vision_document: Optional[str]

    class Config:
        from_attributes = True


class ChapterCreate(BaseModel):
    """Request model for creating a chapter."""
    chapter_number: int = Field(..., ge=1, description="Chapter number")
    title: Optional[str] = Field(None, max_length=200, description="Chapter title")
    outline: Optional[str] = Field(None, description="Chapter outline")


class ChapterResponse(BaseModel):
    """Response model for chapter data."""
    id: str
    project_id: str
    chapter_number: int
    title: Optional[str]
    outline: Optional[str]
    status: str
    word_count: int
    version: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
