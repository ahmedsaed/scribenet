"""
FastAPI main application for ScribeNet.
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import projects, chapters, agents
from backend.api.websockets import project_websocket_endpoint, global_websocket_endpoint

# Create FastAPI app
app = FastAPI(
    title="ScribeNet API",
    description="A self-hosted multi-agent system for collaborative book writing",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router)
app.include_router(chapters.router)
app.include_router(agents.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ScribeNet API",
        "version": "0.1.0",
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# WebSocket endpoints
@app.websocket("/ws/projects/{project_id}")
async def websocket_project(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for project-specific updates."""
    await project_websocket_endpoint(websocket, project_id)


@app.websocket("/ws/agents")
async def websocket_agents(websocket: WebSocket):
    """WebSocket endpoint for global agent updates."""
    await global_websocket_endpoint(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
