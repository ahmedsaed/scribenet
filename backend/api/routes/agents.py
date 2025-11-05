"""
Agent status routes for ScribeNet API.
"""

from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/agents", tags=["agents"])


# Global agent status tracker (in-memory for now)
# In production, this would be in Redis or a state manager
_agent_status: Dict[str, Dict[str, Any]] = {
    "director": {"status": "idle", "current_task": None, "last_active": None},
    "outline": {"status": "idle", "current_task": None, "last_active": None},
    "writer": {"status": "idle", "current_task": None, "last_active": None},
    "editor": {"status": "idle", "current_task": None, "last_active": None},
    "critic": {"status": "idle", "current_task": None, "last_active": None},
    "summarizer": {"status": "idle", "current_task": None, "last_active": None},
}


def update_agent_status(agent_name: str, status: str, task: str = None):
    """
    Update agent status. Called from workflow nodes.
    
    Args:
        agent_name: Name of the agent
        status: Status (idle, working, completed, error)
        task: Current task description
    """
    if agent_name in _agent_status:
        _agent_status[agent_name]["status"] = status
        _agent_status[agent_name]["current_task"] = task
        _agent_status[agent_name]["last_active"] = datetime.now().isoformat()


@router.get(
    "/status",
    response_model=Dict[str, Any],
)
async def get_agent_status():
    """
    Get current status of all agents.
    
    Returns:
        Status dictionary for all agents
    """
    return {
        "agents": _agent_status,
        "timestamp": datetime.now().isoformat(),
    }


@router.get(
    "/metrics",
    response_model=Dict[str, Any],
)
async def get_agent_metrics():
    """
    Get performance metrics for agents.
    
    Returns:
        Metrics including token usage, execution times, etc.
    """
    # TODO: Implement actual metrics tracking
    # For now, return placeholder data
    return {
        "total_tokens_used": 0,
        "average_chapter_time": 0,
        "success_rate": 100.0,
        "agents": {
            agent: {
                "tasks_completed": 0,
                "average_time": 0,
                "tokens_used": 0,
            }
            for agent in _agent_status.keys()
        },
    }
