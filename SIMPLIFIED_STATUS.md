# ScribeNet - Simplified Status & Next Steps

**Date**: November 5, 2025

---

## ✅ What's Actually Built (Phases 1-2)

### Backend is Working!
- **6 Agent Types** (as per original plan):
  1. Director - Orchestration & planning
  2. Outline - Story structure & story bible
  3. Writer - Content generation (supports narrative/dialogue/description modes)
  4. Editor - Multi-pass editing (grammar/style/continuity)
  5. Critic - Quality evaluation & revision decisions
  6. Summarizer - Context compression

- **3 Memory Systems**:
  1. SQLite - Structured data (projects, chapters, scores, story bible)
  2. ChromaDB - Semantic search (chapters, story bible, style examples)
  3. Git - Version control (chapter history, rollback, tags)

- **Working Workflow**:
  - Create project → Generate outline → Write chapters → Edit → Critique → Revise (if needed)
  - Tested via CLI and works end-to-end

### The Problem: NO VISIBILITY! 👀
- Everything happens in CLI with print statements
- Can't see what agents are doing in real-time
- Can't control or intervene
- No way to view results except reading log files
- Feels like working blind

---

## 🎯 Phase 3: Frontend Dashboard (PRIORITY!)

**Goal**: Stop being blind. Build a dashboard so you can SEE and CONTROL everything.

### Day 1: Minimal Backend APIs
Add just enough endpoints to feed the frontend:

**New Files**:
```
backend/api/routes/chapters.py    # GET chapters, GET chapter content
backend/api/websockets.py          # Real-time updates
```

**New Endpoints**:
```
POST /api/projects/{id}/start           # Start writing
GET  /api/projects/{id}/status          # Current status
GET  /api/projects/{id}/chapters        # List chapters
GET  /api/projects/{id}/chapters/{num}  # Get chapter + scores
GET  /api/agents/status                 # What's each agent doing?
WS   /ws/projects/{id}                  # Real-time events
```

**WebSocket Events**:
- `workflow_started`, `workflow_completed`
- `agent_started`, `agent_completed` (which agent + task)
- `chapter_completed` (with preview)
- `quality_scored` (with scores)
- `error` (with details)

### Days 2-5: Frontend Dashboard

**Stack**:
- Next.js 14 + TypeScript
- Tailwind CSS
- Shadcn/ui components
- WebSocket client

**3 Simple Pages**:

#### 1. Project List (`/`)
```
My Projects                    [+ New Project]
─────────────────────────────────────────────
📖 The Last Starship
   Sci-Fi  •  Chapter 3/20  •  In Progress
   [Open]

📖 Mystery at Oak Manor
   Mystery  •  Chapter 12/15  •  Editing
   [Open]
```

#### 2. Main Dashboard (`/projects/[id]`)  ⭐ MOST IMPORTANT
```
┌─────────────────────────────────────────────┐
│ 📖 The Last Starship (Sci-Fi)   [⏸ Pause]  │
│ Progress: ●●●○○○○○○○○○○○○○○○○○○ 3/20 (15%) │
├─────────────────────────────────────────────┤
│                                             │
│ 🤖 AGENTS (Real-time)                       │
│ ✍️  Writer    Working on Chapter 3... 2:34  │
│ 📊 Critic     Idle                          │
│ ✂️  Editor    Waiting                        │
│ 📝 Outline    Completed                     │
│                                             │
│ 📚 CHAPTERS                                 │
│ Ch 1 ✅ 8.2⭐  Ch 2 ✅ 7.8⭐  Ch 3 🔄        │
│                                             │
│ 📊 LATEST SCORES (Ch 2)                    │
│ Engagement: ████████░░ 8/10                │
│ Quality:    ███████░░░ 7/10                │
│ Continuity: █████████░ 9/10                │
│                                             │
│ 📜 ACTIVITY LOG                             │
│ [14:32] ✅ Chapter 2 completed (3,245 words)│
│ [14:31] 📊 Quality score: 7.8/10            │
│ [14:29] ✂️  Editing complete                 │
│ [14:20] ✍️  Chapter 2 draft complete         │
│                                             │
└─────────────────────────────────────────────┘
```

#### 3. Chapter Detail (`/projects/[id]/chapters/[num]`)
```
┌──────────────────────────────────────────┐
│ Chapter 3: The Discovery                 │
│ Status: ✅  •  3,245 words  •  8.2⭐      │
├──────────────────────────────────────────┤
│                                          │
│ 📄 CONTENT                               │
│ ┌────────────────────────┐               │
│ │ Content preview...     │               │
│ │ [View Full] [Export]   │               │
│ └────────────────────────┘               │
│                                          │
│ 📊 QUALITY SCORES                        │
│ Engagement:  ████████░░ 8/10            │
│ Quality:     ███████░░░ 7/10            │
│ Continuity:  █████████░ 9/10            │
│                                          │
│ 💬 CRITIC FEEDBACK                       │
│ "Good pacing overall. Dialogue in the   │
│  middle section could be more dynamic." │
│                                          │
│ [🔄 Regenerate] [✏️ Edit Manually]       │
│                                          │
└──────────────────────────────────────────┘
```

### Components to Build:
- `AgentStatusCard` - Show agent state (idle/working/completed)
- `ChapterGrid` - Visual grid of chapters
- `ScoreDisplay` - Progress bars for metrics
- `ActivityFeed` - Real-time event log
- `ProgressBar` - Overall completion

---

## Why This Order?

1. **You can't improve what you can't see** - Dashboard first!
2. **Workflow is functional** - Not perfect, but it works
3. **Once you have visibility**, you'll know exactly what to fix
4. **Stop guessing** - Watch the agents work, see the problems

---

## After Phase 3

**Phase 4: Fix Workflow** (3-4 days)
- Clean up workflows.py architecture
- Make agent selection configurable
- Add story bible generation
- Improve context management

**Phase 5: Polish** (ongoing)
- Export features (PDF/EPUB/DOCX)
- Manual intervention points
- Performance optimization
- Advanced features

---

## Clean Agent List (Per Original Plan)

The plan specified **6 agent types**, not 8:

1. **Director** - Orchestration
2. **Outline** - Story structure
3. **Writer** - Content (can have modes: narrative/dialogue/description)
4. **Editor** - Editing (can have passes: grammar/style/continuity)
5. **Critic** - Quality eval
6. **Summarizer** - Context compression

Current implementation has these 6 types. The "8 agents" confusion came from counting writer/editor subtypes separately, but they're really just different modes of operation for Writer and Editor agents.

---

## Summary

**What Works**: Backend, agents, workflows, CLI testing
**What's Missing**: Dashboard to see and control everything
**Next Step**: Build the dashboard (5-6 days)
**After That**: Fix workflow structure based on what you learn from watching it

**Stop Working Blind. Build the Dashboard First!** 👀

---

**Ready to start?** Let's begin with the backend API additions tomorrow!
