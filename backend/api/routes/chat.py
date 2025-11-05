"""
Chat routes for ScribeNet API - Director agent interaction.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from backend.agents.director import DirectorAgent
from backend.memory.database import Database

router = APIRouter(prefix="/api/projects", tags=["chat"])


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, description="User message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default_factory=list, description="Previous messages in conversation"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message: str
    timestamp: str
    conversation_id: Optional[str] = None


def get_db() -> Database:
    """Get database instance."""
    return Database()


@router.post(
    "/{project_id}/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def chat_with_director(project_id: str, request: ChatRequest):
    """
    Chat with the Director agent for a specific project.
    
    The Director agent has full context of the project and can:
    - Answer questions about the project
    - Provide guidance and suggestions
    - Trigger workflows and coordinate other agents
    - Manage the overall creative direction
    
    Args:
        project_id: Project UUID
        request: Chat request with message and conversation history
        
    Returns:
        Director's response
    """
    db = get_db()
    
    # Get project details
    try:
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project: {str(e)}",
        )
    
    # Initialize Director agent
    director = DirectorAgent()
    
    try:
        # Get the response from Director
        response = await director.chat_with_context(
            project=project,
            user_message=request.message,
            conversation_history=request.conversation_history,
        )
        
        return ChatResponse(
            message=response,
            timestamp=datetime.utcnow().isoformat(),
            conversation_id=project_id,  # Using project_id as conversation_id for now
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get response from Director: {str(e)}",
        )
