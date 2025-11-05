"""
WebSocket support for real-time updates in ScribeNet.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Store connections per project
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store global connections (all projects)
        self.global_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, project_id: str = None):
        """Accept and store a WebSocket connection."""
        await websocket.accept()
        
        if project_id:
            if project_id not in self.active_connections:
                self.active_connections[project_id] = set()
            self.active_connections[project_id].add(websocket)
        else:
            self.global_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket, project_id: str = None):
        """Remove a WebSocket connection."""
        if project_id and project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        else:
            self.global_connections.discard(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            pass
    
    async def broadcast_to_project(self, message: dict, project_id: str):
        """Send a message to all clients watching a project."""
        if project_id not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        dead_connections = set()
        
        for connection in self.active_connections[project_id]:
            try:
                await connection.send_text(message_str)
            except Exception:
                dead_connections.add(connection)
        
        # Clean up dead connections
        for connection in dead_connections:
            self.disconnect(connection, project_id)
    
    async def broadcast_global(self, message: dict):
        """Send a message to all global connections."""
        message_str = json.dumps(message)
        dead_connections = set()
        
        for connection in self.global_connections:
            try:
                await connection.send_text(message_str)
            except Exception:
                dead_connections.add(connection)
        
        # Clean up dead connections
        for connection in dead_connections:
            self.disconnect(connection)


# Global connection manager instance
manager = ConnectionManager()


async def emit_event(
    event_type: str,
    data: dict,
    project_id: str = None,
):
    """
    Emit an event to WebSocket clients.
    
    Args:
        event_type: Type of event (agent_started, chapter_completed, etc.)
        data: Event data
        project_id: Optional project ID to broadcast to specific project
    """
    message = {
        "event": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }
    
    if project_id:
        await manager.broadcast_to_project(message, project_id)
    else:
        await manager.broadcast_global(message)


async def project_websocket_endpoint(websocket: WebSocket, project_id: str):
    """
    WebSocket endpoint for project-specific updates.
    
    Usage in FastAPI:
        @app.websocket("/ws/projects/{project_id}")
        async def websocket_endpoint(websocket: WebSocket, project_id: str):
            await project_websocket_endpoint(websocket, project_id)
    """
    await manager.connect(websocket, project_id)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message(
            {
                "event": "connected",
                "data": {"project_id": project_id},
                "timestamp": datetime.now().isoformat(),
            },
            websocket,
        )
        
        # Keep connection alive and listen for client messages
        while True:
            # Receive text from client (ping/pong or commands)
            data = await websocket.receive_text()
            
            # Echo back for now (can implement commands later)
            if data == "ping":
                await manager.send_personal_message(
                    {"event": "pong", "timestamp": datetime.now().isoformat()},
                    websocket,
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, project_id)


async def global_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for global updates (all projects).
    
    Usage in FastAPI:
        @app.websocket("/ws/agents")
        async def websocket_endpoint(websocket: WebSocket):
            await global_websocket_endpoint(websocket)
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message(
            {
                "event": "connected",
                "data": {"scope": "global"},
                "timestamp": datetime.now().isoformat(),
            },
            websocket,
        )
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            
            if data == "ping":
                await manager.send_personal_message(
                    {"event": "pong", "timestamp": datetime.now().isoformat()},
                    websocket,
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
