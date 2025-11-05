# Phase 3 Implementation Checklist

**Goal**: Complete backend integration and prepare for frontend development

**Estimated Time**: 5-9 days of focused development

---

## 🎯 Priority 1: Workflow Agent Integration (Days 1-2)

### Task 1.1: Integrate OutlineAgent
**File**: `backend/orchestration/workflows.py`

**Changes Needed**:
```python
# In create_outline_node():
# BEFORE (current):
result = await director.execute({
    "task_type": "create_outline",
    ...
})

# AFTER (should be):
from backend.agents.outline import OutlineAgent
outline_agent = OutlineAgent()

result = await outline_agent.execute({
    "task_type": "create_outline",
    ...
})
```

**Steps**:
1. Import OutlineAgent at top of workflows.py
2. Initialize outline_agent instance
3. Replace Director call with OutlineAgent call in create_outline_node()
4. Test outline generation

**Files to Modify**:
- [ ] `backend/orchestration/workflows.py` (lines ~85-105)

---

### Task 1.2: Generate Story Bible
**File**: `backend/orchestration/workflows.py`

**Add New Node**:
```python
async def generate_story_bible_node(state: ProjectState) -> ProjectState:
    """Generate story bible after outline creation."""
    print("📚 Generating story bible")
    
    result = await outline_agent.execute({
        "task_type": "generate_story_bible",
        "outline": state["outline"],
        "genre": state.get("genre", "fiction"),
    })
    
    # Save to database
    db.save_full_story_bible(
        project_id=state["project_id"],
        story_bible=result["story_bible"]
    )
    
    # Add to ChromaDB
    vector_store.add_story_bible(
        project_id=state["project_id"],
        story_bible=result["story_bible"]
    )
    
    state["story_bible"] = result["story_bible"]
    return state
```

**Update Workflow Graph**:
```python
workflow.add_node("generate_story_bible", generate_story_bible_node)
workflow.add_edge("create_outline", "generate_story_bible")
workflow.add_edge("generate_story_bible", END)
```

**Steps**:
1. Add generate_story_bible_node() function
2. Update workflow graph to include new node
3. Test story bible generation and persistence

**Files to Modify**:
- [ ] `backend/orchestration/workflows.py` (add new node after create_outline_node)

---

### Task 1.3: Include Story Bible in Context
**File**: `backend/orchestration/workflows.py`

**Changes in write_chapter_node()**:
```python
# Add after semantic context retrieval:
story_bible = db.get_story_bible(state['project_id'])

# Pass to writer:
result = await writer.execute({
    ...
    "story_bible": story_bible,
})

# Pass to critic:
evaluation = await critic.execute('evaluate_chapter', {
    ...
    "story_bible": story_bible,
})

# Pass to continuity editor:
continuity_editor.edit({
    ...
    "story_bible": story_bible,
})
```

**Steps**:
1. Retrieve story bible from database
2. Add to writer context
3. Add to critic evaluation
4. Add to continuity editor validation

**Files to Modify**:
- [ ] `backend/orchestration/workflows.py` (lines ~180-350)

---

## 📡 Priority 2: API Endpoint Expansion (Days 3-5)

### Task 2.1: Chapter Endpoints
**New File**: `backend/api/routes/chapters.py`

**Endpoints to Implement**:
- [ ] `POST /api/projects/{id}/chapters` - Start writing a chapter
- [ ] `GET /api/projects/{id}/chapters` - List all chapters
- [ ] `GET /api/projects/{id}/chapters/{num}` - Get chapter details
- [ ] `PUT /api/projects/{id}/chapters/{num}` - Update chapter
- [ ] `POST /api/projects/{id}/chapters/{num}/revise` - Trigger revision
- [ ] `GET /api/projects/{id}/chapters/{num}/versions` - Get version history
- [ ] `POST /api/projects/{id}/chapters/{num}/rollback` - Rollback to version
- [ ] `GET /api/projects/{id}/chapters/{num}/scores` - Get quality scores

**Models to Add** (`backend/api/models.py`):
```python
class ChapterCreate(BaseModel):
    chapter_number: int
    chapter_outline: Optional[str] = None
    target_word_count: int = 3000

class ChapterResponse(BaseModel):
    chapter_id: str
    project_id: str
    chapter_number: int
    title: str
    status: str
    word_count: int
    version: int
    created_at: datetime
    updated_at: datetime

class ChapterVersionResponse(BaseModel):
    version_id: str
    version: int
    content: str
    created_by: str
    created_at: datetime
    metadata: Dict[str, Any]
```

**Files to Create**:
- [ ] `backend/api/routes/chapters.py` (~300 lines)

**Files to Modify**:
- [ ] `backend/api/models.py` (add chapter models)
- [ ] `backend/api/main.py` (include router)

---

### Task 2.2: Story Bible Endpoints
**New File**: `backend/api/routes/story_bible.py`

**Endpoints to Implement**:
- [ ] `GET /api/projects/{id}/story-bible` - Get full story bible
- [ ] `GET /api/projects/{id}/story-bible/characters` - List characters
- [ ] `POST /api/projects/{id}/story-bible/characters` - Add character
- [ ] `GET /api/projects/{id}/story-bible/characters/{name}` - Get character
- [ ] `PUT /api/projects/{id}/story-bible/characters/{name}` - Update character
- [ ] `DELETE /api/projects/{id}/story-bible/characters/{name}` - Delete character
- [ ] Similar for: locations, timeline, rules, subplots

**Models to Add**:
```python
class CharacterCreate(BaseModel):
    name: str
    role: str
    traits: List[str]
    arc: str
    relationships: Dict[str, str] = {}

class CharacterResponse(BaseModel):
    name: str
    role: str
    traits: List[str]
    arc: str
    relationships: Dict[str, str]
    introduced_chapter: Optional[int]
    key_moments: List[str] = []

class StoryBibleResponse(BaseModel):
    characters: List[CharacterResponse]
    locations: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    rules: Dict[str, Any]
    themes: List[str]
    subplots: List[Dict[str, Any]]
```

**Files to Create**:
- [ ] `backend/api/routes/story_bible.py` (~400 lines)

**Files to Modify**:
- [ ] `backend/api/models.py` (add story bible models)
- [ ] `backend/api/main.py` (include router)

---

### Task 2.3: Agent & Task Endpoints
**New File**: `backend/api/routes/agents.py`

**Endpoints to Implement**:
- [ ] `GET /api/agents/status` - Get status of all agents
- [ ] `GET /api/tasks` - View task queue
- [ ] `GET /api/tasks/{id}` - Get task details
- [ ] `POST /api/tasks/{id}/cancel` - Cancel task
- [ ] `GET /api/agents/metrics` - Performance metrics

**Note**: This requires task queue implementation in orchestration layer.

**Files to Create**:
- [ ] `backend/api/routes/agents.py` (~200 lines)
- [ ] `backend/orchestration/task_queue.py` (new - task management)

---

### Task 2.4: Search Endpoints
**New File**: `backend/api/routes/search.py`

**Endpoints to Implement**:
- [ ] `POST /api/search/semantic` - Semantic search across content
- [ ] `POST /api/search/characters` - Find content by character
- [ ] `POST /api/search/themes` - Find content by theme
- [ ] `GET /api/projects/{id}/timeline` - Get project timeline
- [ ] `GET /api/projects/{id}/continuity` - Check continuity issues

**Files to Create**:
- [ ] `backend/api/routes/search.py` (~150 lines)

---

### Task 2.5: Workflow Control Endpoints
**Add to**: `backend/api/routes/projects.py`

**Endpoints to Add**:
- [ ] `POST /api/projects/{id}/start` - Begin writing workflow
- [ ] `POST /api/projects/{id}/pause` - Pause workflow
- [ ] `POST /api/projects/{id}/resume` - Resume workflow
- [ ] `GET /api/projects/{id}/status` - Get workflow status
- [ ] `POST /api/projects/{id}/regenerate-outline` - Regenerate outline

**Files to Modify**:
- [ ] `backend/api/routes/projects.py` (add ~100 lines)

---

## 🔌 Priority 3: WebSocket Implementation (Days 6-7)

### Task 3.1: WebSocket Server
**New File**: `backend/api/websockets.py`

**Implementation**:
```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        self.active_connections[project_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        self.active_connections[project_id].discard(websocket)
    
    async def broadcast(self, message: dict, project_id: str):
        for connection in self.active_connections.get(project_id, set()):
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws/projects/{project_id}")
async def project_websocket(websocket: WebSocket, project_id: str):
    await manager.connect(websocket, project_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
```

**Files to Create**:
- [ ] `backend/api/websockets.py` (~200 lines)

**Files to Modify**:
- [ ] `backend/api/main.py` (add WebSocket routes)

---

### Task 3.2: Event Emission from Workflows
**File**: `backend/orchestration/workflows.py`

**Add Event Emitter**:
```python
from backend.api.websockets import manager

async def emit_event(project_id: str, event_type: str, data: dict):
    """Emit event to WebSocket clients."""
    await manager.broadcast({
        "event": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }, project_id)

# In each workflow node:
await emit_event(state["project_id"], "agent_started", {
    "agent": "writer",
    "chapter": state["chapter_number"]
})

await emit_event(state["project_id"], "chapter_progress", {
    "chapter": state["chapter_number"],
    "progress": 50,
    "status": "writing"
})

await emit_event(state["project_id"], "agent_completed", {
    "agent": "writer",
    "chapter": state["chapter_number"]
})
```

**Event Types to Emit**:
- `agent_started` - Agent begins work
- `agent_completed` - Agent finishes
- `agent_error` - Agent encounters error
- `chapter_progress` - Chapter writing progress
- `quality_updated` - New quality scores
- `revision_triggered` - Revision loop started
- `outline_updated` - Outline changed
- `story_bible_updated` - Story bible changed

**Files to Modify**:
- [ ] `backend/orchestration/workflows.py` (add emit_event calls throughout)

---

## ✅ Priority 4: Testing & Validation (Days 8-9)

### Task 4.1: End-to-End Tests
**New File**: `tests/test_e2e.py`

**Tests to Write**:
- [ ] Test complete project creation (vision + outline + story bible)
- [ ] Test 5-chapter book generation
- [ ] Test revision loops trigger correctly
- [ ] Test quality gates enforce thresholds
- [ ] Test Git commits on milestones
- [ ] Test context window management (15+ chapters)
- [ ] Test all API endpoints

**Files to Create**:
- [ ] `tests/test_e2e.py` (~500 lines)
- [ ] `tests/test_api.py` (~400 lines)
- [ ] `tests/test_workflows.py` (~300 lines)

---

### Task 4.2: Manual Testing Script
**New File**: `scripts/test_complete_workflow.py`

**Script Should**:
1. Create project
2. Generate outline with story bible
3. Write 3 chapters
4. Verify all agents called
5. Check database contents
6. Verify Git commits
7. Test API endpoints
8. Display results

**Files to Create**:
- [ ] `scripts/test_complete_workflow.py` (~200 lines)

---

### Task 4.3: Performance Testing
**Measure**:
- [ ] Time per chapter (target: < 5 min for 3K words)
- [ ] Token usage per agent
- [ ] Memory usage
- [ ] Database query performance
- [ ] Context window usage

**Tools**:
- Add timing decorators to agents
- Log token counts
- Profile with cProfile
- Monitor with psutil

---

## 📝 Documentation Updates

### Files to Update:
- [ ] `README.md` - Update status and features
- [ ] `QUICKSTART.md` - Update with API examples
- [ ] `TECHNICAL_PLAN.md` - Mark Phase 3 complete when done
- [ ] API documentation (consider using FastAPI's auto-generated docs)

---

## 🎯 Success Criteria

Before moving to Phase 4 (Frontend), verify:

- ✅ OutlineAgent used in workflows
- ✅ Story bible generated and populated
- ✅ All API endpoints functional (projects, chapters, story bible, agents, search)
- ✅ WebSocket real-time updates working
- ✅ End-to-end test completes successfully (5-10 chapters)
- ✅ Context window management tested (20+ chapters)
- ✅ Git commits on all milestones
- ✅ Quality gates enforce thresholds
- ✅ Revision loops work correctly
- ✅ All memory systems integrated (SQLite, ChromaDB, Git)

---

## 📊 Progress Tracking

Use this checklist to track progress:

### Day 1-2: Workflow Integration
- [ ] Task 1.1: Integrate OutlineAgent
- [ ] Task 1.2: Generate Story Bible
- [ ] Task 1.3: Include Story Bible in Context

### Day 3-5: API Expansion
- [ ] Task 2.1: Chapter Endpoints
- [ ] Task 2.2: Story Bible Endpoints
- [ ] Task 2.3: Agent & Task Endpoints
- [ ] Task 2.4: Search Endpoints
- [ ] Task 2.5: Workflow Control Endpoints

### Day 6-7: WebSocket
- [ ] Task 3.1: WebSocket Server
- [ ] Task 3.2: Event Emission from Workflows

### Day 8-9: Testing
- [ ] Task 4.1: End-to-End Tests
- [ ] Task 4.2: Manual Testing Script
- [ ] Task 4.3: Performance Testing

### Final: Documentation
- [ ] Update README.md
- [ ] Update QUICKSTART.md
- [ ] Update TECHNICAL_PLAN.md
- [ ] API documentation review

---

**Start Date**: TBD  
**Target Completion**: 9 days from start  
**Next Phase**: Phase 4 - Frontend Dashboard
