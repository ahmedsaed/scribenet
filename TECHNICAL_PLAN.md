# ScribeNet: Technical Implementation Plan

> A self-hosted multi-agent system for collaborative book writing

**Last Updated:** November 4, 2025

---

## 📋 Project Overview

**Name:** ScribeNet  
**Goal:** Self-hosted LLM agent system for writing, editing, and refining books collaboratively  
**Architecture:** Multi-agent system with shared memory and orchestration layer

---

## 🏗️ System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Dashboard                         │
│              (Visualization & Manual Control)                │
└────────────────────┬─────────────────────────────────────────┘
                     │ WebSocket + REST API
┌────────────────────┴─────────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            LangGraph Orchestrator                      │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │          Director Agent (Coordinator)           │  │  │
│  │  └────┬────────────────────────────────────────┬───┘  │  │
│  │       │                                        │      │  │
│  │  ┌────┴──────┐  ┌──────────┐  ┌──────────┐  ┌┴────┐ │  │
│  │  │ Outline   │  │ Writers  │  │ Editors  │  │Critic│ │  │
│  │  │  Agent    │  │ (Multi)  │  │ (Multi)  │  │Agent │ │  │
│  │  └───────────┘  └──────────┘  └──────────┘  └──────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                               │
│        ┌─────────────────────┼────────────────────┐          │
│        │                     │                    │          │
│  ┌─────┴──────┐    ┌─────────┴────────┐   ┌──────┴──────┐  │
│  │   Ollama   │    │   Chroma DB      │   │   SQLite    │  │
│  │  (Models)  │    │ (Vector Store)   │   │  (State)    │  │
│  └────────────┘    └──────────────────┘   └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                     ┌────────┴──────────┐
                     │   Git Repository  │
                     │ (Version Control) │
                     └───────────────────┘
```

---

## 🧠 Agent Specifications

### 1. Director Agent

**Responsibility:** Project orchestration, task delegation, quality control

**Key Functions:**
- Parse user input (genre, theme, length, style preferences)
- Create and maintain project roadmap
- Break book into chapters/sections
- Assign writing tasks to Writer agents
- Trigger Editor/Critic reviews at appropriate stages
- Resolve conflicts between agent suggestions
- Track project completion metrics

**Data Structures:**
```
project_state = {
  "project_id": "uuid",
  "genre": "sci-fi",
  "target_chapters": 25,
  "completed_chapters": 3,
  "current_phase": "drafting", // planning, drafting, editing, finalizing
  "vision_document": "markdown_text",
  "active_tasks": [...],
  "decisions_log": [...]
}
```

**Prompting Strategy:**
- System prompt defines role as project manager
- Include current project state and vision document in context
- Use structured output (JSON) for task assignments

---

### 2. Outline Agent

**Responsibility:** Story structure, plot consistency, story bible maintenance

**Key Functions:**
- Generate initial outline from high-level concept
- Expand outline with chapter summaries, beats, and plot points
- Maintain character arcs across chapters
- Track subplot threads
- Update outline when major changes occur
- Validate continuity against story bible

**Story Bible Schema:**
```json
{
  "characters": [
    {
      "name": "Character Name",
      "role": "protagonist",
      "traits": [...],
      "arc": "description",
      "relationships": {...},
      "introduced_chapter": 1,
      "key_moments": [...]
    }
  ],
  "locations": [...],
  "timeline": [...],
  "rules": {
    "magic_system": "...",
    "technology_level": "...",
    "social_structure": "..."
  },
  "themes": [...],
  "subplots": [...]
}
```

**Memory Integration:**
- Store story bible in SQLite (structured data)
- Index key concepts in Chroma for semantic search
- Version story bible changes in Git

---

### 3. Writer Agents (Multi-Instance)

**Types:**
1. **Narrative Writer** - Main storytelling, prose, action
2. **Dialogue Writer** - Character conversations, voice consistency
3. **Description Writer** - Scenes, settings, worldbuilding details
4. **Technical Writer** - Scientific/technical accuracy (optional)

**Key Functions:**
- Receive writing assignment (chapter, scene, or section)
- Retrieve context (previous chapters, character info, outline)
- Generate draft content
- Tag sections with metadata (POV, location, time, characters present)
- Handle rewrites based on feedback

**Input Context:**
- Relevant outline section
- Character profiles involved in scene
- Previous 2-3 chapters (for continuity)
- Style guide/reference examples
- Specific writing instructions from Director

**Model Routing:**
- Fast drafts: Llama 3.1 8B
- Quality prose: Llama 3.1 70B or Qwen 2.5 32B
- Specialized voice: Fine-tuned models (future)

---

### 4. Editor Agents (Multi-Pass)

**Types:**
1. **Grammar Editor** - Spelling, grammar, punctuation
2. **Style Editor** - Voice consistency, rhythm, flow
3. **Continuity Editor** - Story bible compliance, timeline consistency

**Key Functions:**
- Receive draft text + edit instructions
- Apply specific editing pass
- Track changes (diff format)
- Provide explanations for significant changes
- Escalate major issues to Director

**Edit Passes (Sequential):**
```
Draft → Grammar Edit → Style Edit → Continuity Edit → Final
```

**Quality Metrics:**
- Grammar error count
- Readability score (Flesch-Kincaid)
- Style consistency score (vs. reference)
- Continuity flags (character inconsistencies, timeline errors)

---

### 5. Critic Agent

**Responsibility:** Quality assessment, reader perspective simulation

**Key Functions:**
- Rate sections on multiple dimensions (1-10 scale):
  - Engagement/pacing
  - Character consistency
  - Emotional impact
  - Originality
  - Prose quality
  - Dialogue naturality
- Provide specific, actionable feedback
- Identify weak sections for rewrite
- Simulate reader reactions
- Track quality trends over chapters

**Scoring Output:**
```json
{
  "chapter_id": 5,
  "scores": {
    "engagement": 7,
    "character_consistency": 9,
    "emotional_impact": 6,
    "originality": 8,
    "prose_quality": 7,
    "dialogue": 8
  },
  "feedback": "The pacing drags in the middle section...",
  "suggestions": [...],
  "requires_rewrite": false,
  "flag_for_director": false
}
```

---

### 🗜️ **6. Summarizer Agent**

**Responsibility:** Context compression, narrative history condensation

**Key Functions:**
- Generate concise summaries of completed chapters
- Compress old context when token limit approaches
- Maintain critical continuity information in summaries
- Create hierarchical summaries (brief overview + chapter details)
- Preserve active plot threads and unresolved elements

**Trigger Conditions:**
- Context window usage > 80% threshold
- Manual request from Director agent
- Periodic summarization after N chapters

**Output Format:** Structured markdown with:
- Overall arc summary (2-3 paragraphs)
- Chapter-by-chapter key points
- Active subplot tracking
- Continuity notes (characters, locations, established rules)

**Model Configuration:**
- Use efficient model (Llama 3.1 8B Q8)
- Low temperature (0.3-0.4) for factual accuracy
- Target 10:1 compression ratio

---

## 💾 Memory System

### Components

#### 1. SQLite Database

**Purpose:** Structured state management, project metadata

**Schema:**
```sql
-- Projects
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  title TEXT,
  genre TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  status TEXT,
  vision_document TEXT
);

-- Chapters
CREATE TABLE chapters (
  id TEXT PRIMARY KEY,
  project_id TEXT,
  chapter_number INTEGER,
  title TEXT,
  outline TEXT,
  status TEXT, -- planning, drafting, editing, completed
  word_count INTEGER,
  version INTEGER,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- Chapter Versions (for drafts/edits)
CREATE TABLE chapter_versions (
  id TEXT PRIMARY KEY,
  chapter_id TEXT,
  version INTEGER,
  content TEXT,
  created_by TEXT, -- agent type
  created_at TIMESTAMP,
  metadata JSON,
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

-- Story Bible
CREATE TABLE story_elements (
  id TEXT PRIMARY KEY,
  project_id TEXT,
  element_type TEXT, -- character, location, rule, subplot
  name TEXT,
  data JSON,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- Task Queue
CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  project_id TEXT,
  agent_type TEXT,
  task_type TEXT,
  status TEXT, -- pending, in_progress, completed, failed
  input_data JSON,
  output_data JSON,
  created_at TIMESTAMP,
  completed_at TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- Agent Decisions Log
CREATE TABLE decisions (
  id TEXT PRIMARY KEY,
  project_id TEXT,
  agent_id TEXT,
  decision_type TEXT,
  rationale TEXT,
  timestamp TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);
```

#### 2. ChromaDB Vector Store

**Purpose:** Semantic search, context retrieval, thematic consistency

**Collections:**
- `chapters` - Full chapter text for similarity search
- `story_bible` - Character descriptions, locations, rules
- `style_examples` - Reference prose for style matching
- `research_notes` - User-provided background material

**Metadata per Document:**
```json
{
  "project_id": "uuid",
  "document_type": "chapter",
  "chapter_number": 3,
  "characters": ["Alice", "Bob"],
  "location": "Mars Colony",
  "time_period": "2245-03-15",
  "themes": ["isolation", "discovery"]
}
```

**Query Patterns:**
- "Find chapters where character X appears"
- "Retrieve similar emotional scenes"
- "Get worldbuilding context for location Y"
- "Find style examples matching tone Z"

#### 3. Git Repository

**Purpose:** Version control, rollback capability, collaborative editing

**Structure:**
```
project-{id}/
├── .git/
├── outline.md
├── story_bible.json
├── chapters/
│   ├── chapter_01.md
│   ├── chapter_02.md
│   └── ...
├── drafts/
│   └── chapter_01/
│       ├── draft_v1.md
│       ├── draft_v2.md
│       └── ...
└── metadata/
    ├── vision_document.md
    └── decisions_log.json
```

**Commit Strategy:**
- Auto-commit after each major milestone
- Tag releases (e.g., `draft-1.0`, `final-1.0`)
- Branch for experimental rewrites

---

## 🔄 Orchestration Layer (LangGraph)

### Workflow Graphs

#### Main Writing Workflow

```
Start → Director (Plan) → Outline Agent → Director (Review)
                                              ↓
                                         Assign Chapters
                                              ↓
                                    ┌─────────┴──────────┐
                                    ↓                    ↓
                            Writer Agent(s)      (Parallel execution)
                                    ↓                    ↓
                                    └─────────┬──────────┘
                                              ↓
                                      Collect Drafts
                                              ↓
                                    Editor Agent (Pass 1)
                                              ↓
                                    Editor Agent (Pass 2)
                                              ↓
                                    Editor Agent (Pass 3)
                                              ↓
                                       Critic Agent
                                              ↓
                                    Director (Review)
                                              ↓
                                    ┌─────────┴──────────┐
                                    ↓                    ↓
                              Accept/Next          Revise (loop back)
```

#### Revision Sub-Workflow

```
Critic Feedback → Director (Analyze) → Assign Rewrite
                                            ↓
                                    Specific Writer Agent
                                            ↓
                                    Targeted Editor Pass
                                            ↓
                                       Critic (Re-check)
                                            ↓
                                    Approve or Loop
```

### State Management

**LangGraph State Schema:**
```python
{
  "project_id": "uuid",
  "current_chapter": 3,
  "active_agents": ["narrative_writer", "editor_grammar"],
  "pending_tasks": [...],
  "context": {
    "outline": "...",
    "previous_chapters": [...],
    "story_bible": {...}
  },
  "iteration_count": 2,
  "max_iterations": 5,
  "quality_threshold": 7.0,
  "current_scores": {...}
}
```

### Conditional Routing

- If quality score < threshold → Revision workflow
- If continuity errors detected → Outline agent review
- If major plot change → Director intervention + outline update
- If iteration limit reached → Escalate to human review

---

## 🚀 Backend API (FastAPI)

### Core Endpoints

#### Project Management
- `POST /api/projects` - Create new book project
- `GET /api/projects/{id}` - Get project details
- `GET /api/projects` - List all projects
- `PUT /api/projects/{id}` - Update project settings
- `DELETE /api/projects/{id}` - Delete project

#### Writing Operations
- `POST /api/projects/{id}/start` - Begin writing workflow
- `POST /api/projects/{id}/chapters/{num}/write` - Generate specific chapter
- `POST /api/projects/{id}/chapters/{num}/revise` - Revise chapter
- `GET /api/projects/{id}/chapters/{num}` - Get chapter content
- `GET /api/projects/{id}/chapters` - List all chapters

#### Story Bible
- `GET /api/projects/{id}/story-bible` - Get full story bible
- `POST /api/projects/{id}/story-bible/characters` - Add character
- `PUT /api/projects/{id}/story-bible/characters/{name}` - Update character
- `GET /api/projects/{id}/story-bible/timeline` - Get timeline

#### Agent Status
- `GET /api/agents/status` - Get status of all agents
- `GET /api/tasks` - View task queue
- `POST /api/tasks/{id}/cancel` - Cancel pending task

#### Memory & Search
- `POST /api/search/semantic` - Semantic search across content
- `GET /api/projects/{id}/versions` - List version history
- `POST /api/projects/{id}/rollback` - Rollback to previous version

### WebSocket Endpoints

- `WS /ws/projects/{id}` - Real-time updates (agent activity, progress)
- `WS /ws/logs` - System-wide event stream

---

## 🎨 Frontend Dashboard (Next.js)

### Pages/Views

#### 1. Project Dashboard
- List of all book projects
- Quick stats (progress, word count, status)
- Create new project button

#### 2. Project Overview
- Visual timeline/progress bar
- Current phase indicator
- Chapter completion grid
- Recent agent activity feed

#### 3. Chapter View
- Side-by-side: Outline | Draft | Final
- Version history timeline
- Agent comments/suggestions
- Edit controls (regenerate, manual edit)

#### 4. Story Bible Explorer
- Tabbed interface: Characters | Locations | Rules | Timeline
- Interactive character relationship graph
- Search functionality

#### 5. Agent Activity Monitor
- Real-time agent status
- Task queue visualization
- Execution logs
- Performance metrics (tokens used, time per task)

#### 6. Quality Dashboard
- Chapter-by-chapter quality scores (charts)
- Trend analysis
- Critic feedback summary
- Flagged issues

#### 7. Settings & Configuration
- Model selection per agent type
- Temperature/creativity sliders
- Style preferences
- Workflow customization

### Key UI Components

- **Chapter Card:** Status, word count, quality score, quick actions
- **Agent Status Badge:** Idle/Working/Completed with progress
- **Story Element Card:** Character/location with quick-view modal
- **Timeline Visualization:** Interactive chapter sequence with dependencies
- **Diff Viewer:** Show edits between versions
- **Quality Radar Chart:** Multi-dimensional scores

---

## 🤖 LLM Backend (Ollama)

### Why Ollama?

Ollama is better suited for local development and consumer hardware:
- ✅ Easy installation and model management
- ✅ Optimized for consumer GPUs (RTX 3060 12GB)
- ✅ Simple API and model switching
- ✅ Automatic quantization and optimization
- ✅ Built-in model library
- ✅ Lower memory overhead

### Model Deployment

**Supported Models (12GB GPU Compatible):**
- **Llama 3.1 8B Q8** - Fast drafting, routine tasks, good all-rounder
- **Qwen 3 8B Q8** - Creative writing, dialogue
- **Qwen 3 14B Q4** - Higher quality prose (larger model, quantized)
- **Gemma 3 12B Q4** - Technical accuracy, structured content
- **deepseek-r1:14b-qwen-distill-q4_K_M** - Reasoning-heavy tasks

### Model Loading Strategies

**Strategy 1: Single Model (Recommended for 12GB GPU)**
Load one model and use it for all agents. Ollama keeps it in memory automatically.

```python
# Single model configuration
ollama_config = {
  "mode": "single",
  "model": "llama3.1:8b",  # Ollama model tag
  "num_ctx": 32768,        # Context window
  "keep_alive": "24h"      # Keep in memory
}
```

**Strategy 2: Multiple Models with Auto-Loading**
Ollama can automatically load/unload models as needed with minimal overhead.

```python
# Multi-model configuration
ollama_config = {
  "mode": "auto",
  "models": {
    "fast": "llama3.1:8b",      # Director, editors
    "creative": "qwen2.5:14b",  # Writers
    "reasoning": "deepseek-r1:14b"  # Critic
  },
  "num_ctx": 16384,      # Smaller context per model
  "keep_alive": "5m"     # Auto-unload after 5 min
}
```

**Strategy 3: Single Model with Manual Switching (Fallback)**
Explicitly switch models for different tasks if needed.

```python
# Manual switching configuration
ollama_config = {
  "mode": "manual",
  "default_model": "llama3.1:8b",
  "agent_models": {
    "director": "llama3.1:8b",
    "writer_narrative": "qwen2.5:14b",
    "writer_dialogue": "qwen2.5:7b"
  }
}
```

### Agent-to-Model Assignment

User-configurable mapping of agents to models:

```yaml
# In config.yaml
agents:
  director:
    model: "llama3.1:8b"
    temperature: 0.7
  outline:
    model: "llama3.1:8b"
    temperature: 0.6
  writers:
    narrative:
      model: "qwen2.5:14b"  # Use best available
      temperature: 0.8
    dialogue:
      model: "qwen2.5:7b"
      temperature: 0.9
    description:
      model: "qwen2.5:7b"
      temperature: 0.85
  editors:
    grammar:
      model: "llama3.1:8b"
      temperature: 0.3
    style:
      model: "llama3.1:8b"
      temperature: 0.4
    continuity:
      model: "llama3.1:8b"
      temperature: 0.5
  critic:
    model: "deepseek-r1:14b"  # Reasoning model
    temperature: 0.5
```

### Model Selection Guidelines

| Agent Type | Workload | Recommended Model | Rationale |
|------------|----------|-------------------|-----------|
| Director | Coordination, planning | llama3.1:8b | Fast, reliable reasoning |
| Outline | Structure, consistency | llama3.1:8b | Good at organization |
| Writer (Narrative) | Creative prose | qwen2.5:14b or qwen2.5:7b | Strong creative writing |
| Writer (Dialogue) | Character voice | qwen2.5:7b | Natural conversation |
| Writer (Description) | Vivid scenes | qwen2.5:7b or gemma2:12b | Descriptive language |
| Editor | Grammar, style | llama3.1:8b | Precise, rule-based |
| Critic | Evaluation, reasoning | deepseek-r1:14b or llama3.1:8b | Analytical thinking |

### Ollama Installation & Setup

**Installation:**
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows
# Download from ollama.com
```

**Pull Models:**
```bash
# Fast all-rounder
ollama pull llama3.1:8b

# Creative writing
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b

# Optional: reasoning
ollama pull deepseek-r1:14b
```

**Start Ollama Server:**
```bash
# Starts automatically on installation, or:
ollama serve

# Server runs on http://localhost:11434
```

**Check Available Models:**
```bash
ollama list
```

### Prompt Engineering Strategy

**Template Structure:**
```
[System Prompt: Role Definition]
[Context: Story Bible + Previous Chapters]
[Task: Specific instruction]
[Format: Output schema]
[Constraints: Word count, style, tone]
```

**Agent-Specific Prompts:**
- **Director:** "You are a book project manager coordinating writing agents..."
- **Writer:** "You are a [narrative/dialogue/description] writer with expertise in [genre]..."
- **Editor:** "You are a [grammar/style/continuity] editor reviewing [section]..."
- **Critic:** "You are a literary critic evaluating [chapter] on [criteria]..."

**Dynamic Context Injection:**
- Use vector search to retrieve relevant past content
- Include 2-3 most recent chapters for continuity
- Add character profiles for characters in scene
- Inject style examples when needed

### Context Window & Summary Management

**Problem:** Long books exceed model context limits. Agents need history but can't fit everything.

**Solution:** Adaptive summarization with rolling context window.

#### Strategy

1. **Context Window Monitoring**
   - Track token count of context being sent to model
   - Set threshold at 80% of max context length
   - Example: 32K context → trigger summary at ~25K tokens

2. **Rolling Window Structure**
   ```
   [Summary of Chapters 1-N] + [Full Chapter N+1] + [Full Chapter N+2] + [Current Task]
   
   ├─ Old History (Summarized) ─┤├── Recent Context (Full) ──┤├─ Task ─┤
         20-30% of context          40-50% of context         20-30%
   ```

3. **Summary Generation Process**
   ```
   When context > 80% threshold:
   1. Identify "old context" (chapters beyond recent N chapters)
   2. Call Summarizer Agent with old context
   3. Generate hierarchical summary:
      - High-level: Overall arc, major events, character development
      - Chapter-by-chapter: Key plot points, character moments
      - Continuity: Active subplots, unresolved threads
   4. Replace old context with summary
   5. Keep recent chapters in full
   ```

4. **Summary Compression Ratios**
   - Target: 10:1 compression (10K tokens → 1K summary)
   - Hierarchical: Brief overview + detailed chapter notes
   - Preserve critical continuity elements

#### Summarizer Agent

**Role:** Condense long narrative history into compact, information-dense summaries.

**Input:**
- Chapters to summarize (text)
- Story bible (for character/plot reference)
- Summarization depth (brief/detailed)

**Output:**
```markdown
## Overall Summary (Chapters 1-8)
[2-3 paragraph overview of major arc, themes, character development]

## Chapter Summaries
### Chapter 1: [Title]
- **Key Events:** [bullet points]
- **Character Moments:** [important developments]
- **Plot Threads:** [what was introduced/resolved]

### Chapter 2: [Title]
...

## Active Threads
- [Unresolved subplot 1]
- [Character arc in progress]
- [Mystery/question needing resolution]

## Continuity Notes
- [Important details mentioned that may be referenced later]
- [World-building rules established]
- [Character relationships/status]
```

**Model Assignment:**
- Use fast, efficient model (Llama 3.1 8B Q8)
- Low temperature (0.3-0.4) for factual accuracy
- Instruction: "Summarize comprehensively but concisely"

#### Implementation Details

```python
# Context management pseudocode
def prepare_context(agent, task, project_id):
    # Get relevant chapters
    recent_chapters = get_recent_chapters(project_id, n=2)
    older_chapters = get_older_chapters(project_id, exclude_recent=2)
    
    # Build context
    context_parts = []
    
    # Add story bible (always included, compact)
    story_bible = get_story_bible(project_id)
    context_parts.append(format_story_bible(story_bible))
    
    # Check if we need summarization
    full_context = format_chapters(older_chapters + recent_chapters)
    token_count = estimate_tokens(full_context + task)
    max_tokens = get_model_context_window(agent.model)
    
    if token_count > max_tokens * 0.8:
        # Generate or retrieve summary
        summary = get_or_generate_summary(
            project_id=project_id,
            chapters=older_chapters,
            cache_key=f"summary_{min(older_chapters)}-{max(older_chapters)}"
        )
        context_parts.append(summary)
        context_parts.extend(format_chapters(recent_chapters))
    else:
        # Context fits, use full chapters
        context_parts.extend(format_chapters(older_chapters + recent_chapters))
    
    # Add current task
    context_parts.append(task)
    
    return "\n\n".join(context_parts)
```

#### Summary Caching

- **Cache summaries in SQLite:** Avoid regenerating identical summaries
- **Cache key:** `project_id + chapter_range + version_hash`
- **Invalidation:** When chapters in range are edited
- **Storage:** 
  ```sql
  CREATE TABLE summaries (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    start_chapter INTEGER,
    end_chapter INTEGER,
    summary_text TEXT,
    version_hash TEXT,
    created_at TIMESTAMP
  );
  ```

#### Incremental Summarization

For very long books (50+ chapters):

1. **Tier 1:** Summarize chapters 1-10 → Summary A
2. **Tier 2:** Summarize chapters 11-20 → Summary B
3. **Tier 3:** Summarize Summary A + Summary B → Meta-Summary AB
4. **Context:** Meta-Summary AB + Recent chapters + Task

This creates a hierarchical compression allowing unlimited book length.

### Token Management

- **Budget per task:** 
  - Outline: 4K tokens
  - Chapter draft: 8K-16K tokens
  - Edit pass: 4K tokens
  - Critique: 2K tokens
  - Summary generation: 2K tokens output
- **Context window strategy:** Adaptive summarization + rolling window + vector retrieval
- **Streaming:** Use streaming responses for real-time UI updates
- **Token tracking:** Log token usage per agent call for optimization

---

## 🔧 Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | LangGraph | Agent workflow coordination |
| **Backend** | FastAPI | REST API, WebSocket, business logic |
| **Frontend** | Next.js (TypeScript) | Dashboard, visualization |
| **Database** | SQLite | Structured state, metadata |
| **Vector DB** | ChromaDB | Semantic search, embeddings |
| **LLM Serving** | Ollama | Local inference, model management |
| **Version Control** | Git (programmatic) | Chapter versioning |
| **Real-time** | WebSockets | Live updates to frontend |
| **Task Queue** | Built-in (SQLite-backed) | Agent task management |

---

## 📦 Project Structure

```
scribenet/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── projects.py
│   │   │   ├── chapters.py
│   │   │   ├── story_bible.py
│   │   │   └── agents.py
│   │   ├── websockets.py
│   │   └── main.py
│   ├── agents/
│   │   ├── director.py
│   │   ├── outline.py
│   │   ├── writer.py
│   │   ├── editor.py
│   │   ├── critic.py
│   │   ├── summarizer.py
│   │   └── base.py
│   ├── orchestration/
│   │   ├── workflows.py
│   │   ├── graph.py
│   │   └── state.py
│   ├── memory/
│   │   ├── database.py
│   │   ├── vector_store.py
│   │   ├── git_manager.py
│   │   ├── story_bible.py
│   │   └── context_manager.py
│   ├── llm/
│   │   ├── ollama_client.py
│   │   ├── prompts.py
│   │   ├── models.py
│   │   └── token_counter.py
│   └── utils/
│       ├── config.py
│       └── logging.py
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx (dashboard)
│   │   │   ├── projects/
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx
│   │   │   │       ├── chapters/[num]/page.tsx
│   │   │   │       └── story-bible/page.tsx
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ChapterCard.tsx
│   │   │   ├── AgentMonitor.tsx
│   │   │   ├── StoryBibleViewer.tsx
│   │   │   ├── QualityChart.tsx
│   │   │   └── DiffViewer.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   └── types/
│   │       └── index.ts
│   ├── public/
│   └── package.json
├── models/
│   └── (downloaded LLM models)
├── data/
│   ├── projects/ (git repos per project)
│   ├── scribenet.db (SQLite)
│   └── chroma/ (vector DB storage)
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── TECHNICAL_PLAN.md (this file)
```

---

## 🚦 Development Phases

### Phase 1: Foundation (MVP) ✅ COMPLETE
- [x] SQLite schema + basic database operations
- [x] Ollama setup with single model (llama3.1:8b)
- [x] Basic FastAPI with project CRUD endpoints
- [x] Director agent with simple task assignment
- [x] Single Writer agent (narrative only)
- [x] Simple LangGraph workflow (linear: plan → write → done)
- [x] CLI interface for testing

**Status**: All Phase 1 components implemented and functional.

**Files Created**:
- `backend/memory/database.py` - Complete SQLite schema with CRUD operations
- `backend/llm/ollama_client.py` - Ollama client with async support
- `backend/api/main.py` + `backend/api/routes/projects.py` - FastAPI with project endpoints
- `backend/agents/base.py` - Base agent class with Ollama integration
- `backend/agents/director.py` - Director agent with planning and task assignment
- `backend/agents/writer.py` - Narrative writer agent
- `backend/orchestration/workflows.py` + `backend/orchestration/state.py` - LangGraph workflows
- `cli.py` - Command-line testing interface
- `config.yaml` - Configuration file
- `pyproject.toml` - Project dependencies

**Testing**: Use `poetry run python cli.py` to test the complete workflow.

### Phase 2: Core Agents (COMPLETED ✅)

**Status**: All core agent types and memory systems implemented.

**Completed**:
- ✅ **Outline agent** (`backend/agents/outline.py`) - 450 lines
  - Create detailed chapter-by-chapter outlines
  - Generate comprehensive story bible
  - Update story bible with new information
  - Validate continuity against story bible
  - Expand chapter outlines with scene-by-scene breakdowns

- ✅ **Story bible database operations** (`backend/memory/database.py`)
  - `get_story_element()` - Fetch specific element by type and name
  - `update_story_element()` - Update element data
  - `delete_story_element()` - Remove element
  - `get_story_bible()` - Retrieve complete story bible organized by type
  - `save_full_story_bible()` - Save/replace entire story bible

- ✅ **Multiple writer agents** (`backend/agents/writer.py`) - +240 lines
  - `NarrativeWriterAgent` - Main storytelling, action, narrative flow (temp 0.8)
  - `DialogueWriterAgent` - Character conversations, voice consistency, subtext (temp 0.9)
  - `DescriptionWriterAgent` - Scene-setting, worldbuilding, sensory details (temp 0.85)

- ✅ **Editor agents** (`backend/agents/editor.py`) - 355 lines
  - `BaseEditor` - Common editing infrastructure with change tracking
  - `GrammarEditor` - Spelling, grammar, punctuation (temp 0.3)
  - `StyleEditor` - Voice consistency, rhythm, flow (temp 0.4)
  - `ContinuityEditor` - Story consistency, plot logic (temp 0.5)
  - JSON-structured output for all edits

- ✅ **Critic agent** (`backend/agents/critic.py`) - 450 lines
  - Multi-dimensional scoring system (8 dimensions)
  - Evaluation methods: chapter, scene, quick check, version comparison
  - Actionable feedback generation
  - Quality threshold checking (configurable)
  - Revision priority assessment (critical/high/medium/low/none)

- ✅ **Summarizer agent** (`backend/agents/summarizer.py`) - 370 lines
  - Hierarchical summarization (overview + chapter details)
  - Context window monitoring
  - 10:1 compression ratio targeting
  - Meta-summarization for very long books
  - Continuity extraction
  - Summary caching support

- ✅ **Score database operations** (`backend/memory/database.py`)
  - `save_score()` - Save critic evaluations
  - `get_chapter_scores()` - Get all scores for a chapter
  - `get_latest_chapter_score()` - Get most recent score
  - `get_project_scores()` - Get all project scores

- ✅ **Summary database operations** (`backend/memory/database.py`)
  - `save_summary()` - Save chapter summaries with caching
  - `get_summary()` - Retrieve cached summary for range
  - `get_project_summaries()` - Get all project summaries
  - `invalidate_summaries()` - Invalidate when chapters change

- ✅ **ChromaDB integration** (`backend/memory/vector_store.py`) - 530 lines
  - Four collections: chapters, story_bible, style_examples, research_notes
  - Semantic search across all content types
  - Character/location/theme-based retrieval
  - Style matching for consistent prose
  - Project-scoped filtering

- ✅ **Git integration** (`backend/memory/git_manager.py`) - 570 lines
  - Per-project git repositories
  - Chapter versioning with auto-commits
  - Draft management
  - Branch creation for experimental rewrites
  - Rollback to any commit
  - Tag creation for milestones (draft-1.0, final-1.0)
  - Diff viewing between versions
  - Export functionality

**Phase 2 Summary**:
- **7 new agents**: Outline, Dialogue Writer, Description Writer, Grammar Editor, Style Editor, Continuity Editor, Critic, Summarizer
- **3 memory systems**: ChromaDB (vector), Git (version control), Enhanced SQLite (scores/summaries)
- **Total new code**: ~3,000 lines across 6 new files + database enhancements
- **All agents follow BaseAgent pattern** with proper system prompts and execute() methods
- **JSON-structured outputs** for reliable parsing
- **Python 3.10 compatible** (fixed f-string issues)

**Integration Status**:
- ⏳ Agents need to be integrated into LangGraph workflows
- ⏳ Director agent needs routing logic for multi-writer/editor selection
- ⏳ Revision loops need to be implemented based on critic scores
- ⏳ Context management needs summarizer integration

**Next Steps** (Phase 3):
1. Update `backend/orchestration/workflows.py` to integrate all new agents
2. Implement revision sub-workflow with quality gates
3. Add multi-pass editing pipeline (Grammar → Style → Continuity)
4. Integrate summarizer for context window management
5. Add ChromaDB to context retrieval in workflows
6. Configure Git auto-commits on milestones
7. Test complete end-to-end workflow with all agents
8. Begin frontend development (Next.js dashboard)

### Phase 3: Frontend
- [ ] Next.js dashboard scaffold
- [ ] Project list and creation flow
- [ ] Chapter view with version history
- [ ] Story Bible explorer
- [ ] WebSocket integration for live updates
- [ ] Agent activity monitor

### Phase 4: Polish & Optimization
- [ ] Multi-model routing (8B for drafts, 70B for quality)
- [ ] Advanced prompt engineering per agent
- [ ] Quality metrics & analytics dashboard
- [ ] Manual intervention points (human-in-the-loop)
- [ ] Export formats (PDF, EPUB, DOCX)
- [ ] Performance optimization & caching

### Phase 5: Advanced Features
- [ ] Fine-tuned models for specific voices
- [ ] Collaborative editing (multiple human authors)
- [ ] Style transfer from reference books
- [ ] Chapter dependency graph visualization
- [ ] Advanced critic with reader persona simulation
- [ ] Plugin system for custom agents

---

## ⚙️ Configuration

### User-Configurable Settings

```yaml
# config.yaml
project:
  default_word_count_per_chapter: 3000
  max_revision_iterations: 3
  quality_threshold: 7.0
  recent_chapters_in_context: 2  # Keep N recent chapters in full

agents:
  director:
    model: "llama-3.1-8b-q8"
    temperature: 0.7
  outline:
    model: "llama-3.1-8b-q8"
    temperature: 0.6
  writers:
    narrative:
      model: "qwen-3-14b-q4"
      temperature: 0.8
    dialogue:
      model: "qwen-3-8b-q8"
      temperature: 0.9
    description:
      model: "qwen-3-8b-q8"
      temperature: 0.85
  editors:
    grammar:
      model: "llama-3.1-8b-q8"
      temperature: 0.3
    style:
      model: "llama-3.1-8b-q8"
      temperature: 0.4
    continuity:
      model: "llama-3.1-8b-q8"
      temperature: 0.5
  critic:
    model: "deepseek-r1-14b"
    temperature: 0.5
  summarizer:
    model: "llama-3.1-8b-q8"
    temperature: 0.4
    compression_ratio: 10  # Target 10:1 compression

memory:
  chroma_collection: "scribenet"
  embedding_model: "all-MiniLM-L6-v2"
  vector_search_top_k: 5
  context_window_threshold: 0.8  # Trigger summary at 80% of max

llm:
  # Model loading strategy: "single", "auto", or "manual"
  mode: "single"
  
  # Available models (user can swap in config)
  available_models:
    - name: "llama3.1:8b"
      context_window: 32768
      memory_estimate_mb: 8000
    - name: "qwen2.5:7b"
      context_window: 32768
      memory_estimate_mb: 7000
    - name: "qwen2.5:14b"
      context_window: 32768
      memory_estimate_mb: 10000
    - name: "gemma2:12b"
      context_window: 8192
      memory_estimate_mb: 9000
    - name: "deepseek-r1:14b"
      context_window: 32768
      memory_estimate_mb: 10000
  
  # Active model (based on mode)
  single_model: "llama3.1:8b"  # Used when mode=single
  
  ollama_url: "http://localhost:11434"
  max_tokens: 8192
  timeout: 120
  num_ctx: 32768  # Context window size

git:
  auto_commit: true
  commit_on: ["chapter_complete", "outline_update"]
```

---

## 🔐 Security & Privacy Considerations

- **Self-hosted:** All data stays local, no external API calls
- **Access control:** Basic auth for dashboard (optional multi-user later)
- **Data encryption:** SQLite encryption at rest (optional)
- **Model security:** Models run in isolated containers
- **Backup strategy:** Automated Git backups + database dumps

---

## 📊 Success Metrics

**System Performance:**
- Time to generate chapter (target: <5 min for 3K words)
- Quality score improvement through revisions
- Agent task completion rate

**Output Quality:**
- Average critic scores per chapter
- Continuity error rate
- Human user satisfaction ratings

**User Experience:**
- Dashboard responsiveness
- Real-time update latency (<500ms)
- Export success rate

---

## 🎯 Next Steps

1. **Review this plan** and identify any gaps or concerns
2. **Set up development environment** (Python, Node.js, Ollama)
3. **Choose model strategy** based on your hardware:
   - **Recommended for RTX 3060 12GB:** Single model mode with Llama 3.1 8B Q8 or Qwen 3 8B Q8
   - **Alternative:** Dual model with two 8B models if you want role separation
   - Update `config.yaml` with your model choice
4. **Initialize project structure** (directories, git repo)
5. **Begin Phase 1 implementation** (database, basic API, single agent)
6. **Iterate based on testing** and add agents incrementally

---

## 💡 Model Usage Recommendations

### For RTX 3060 12GB GPU

**Option 1: Single Model (Simplest & Most Efficient)**
```yaml
llm:
  mode: "single"
  single_model: "llama-3.1-8b-q8"  # or "qwen-3-8b-q8"
  gpu_memory_utilization: 0.85
```
- ✅ No model switching overhead
- ✅ Maximum context window utilization
- ✅ Simplest to configure and debug
- ✅ Consistent output quality
- ⚠️ All agents use same model

**Option 2: Dual Small Models (Role Specialization)**
```yaml
llm:
  mode: "dual"
  dual_models:
    - name: "llama-3.1-8b-q8"
      roles: ["director", "outline", "editors", "summarizer"]
      gpu_memory_utilization: 0.42
    - name: "qwen-3-8b-q8"
      roles: ["writers", "critic"]
      gpu_memory_utilization: 0.42
```
- ✅ Specialized models for different tasks
- ✅ Both fit in memory simultaneously
- ⚠️ Reduced context window per model (~16K tokens each)
- ⚠️ More complex configuration

**Option 3: Quality-Focused Rotation (Advanced Users)**
```yaml
llm:
  mode: "swap"
  # Use larger model for critical tasks, unload/reload as needed
```
- ✅ Access to 14B models (Qwen 3 14B Q4, DeepSeek R1 14B)
- ⚠️ Significant overhead from model loading (10-30 seconds per swap)
- ⚠️ Only recommended if quality improvement justifies wait time

### Recommended Starting Point
Start with **Option 1** (single Llama 3.1 8B Q8). Test the full workflow. If you need better creative writing quality, try swapping to Qwen 3 8B Q8 or experiment with Qwen 3 14B Q4 for writer agents specifically.

---

## 📚 Resources & References

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Ollama Documentation:** https://github.com/ollama/ollama
- **ChromaDB Guide:** https://docs.trychroma.com/
- **FastAPI Best Practices:** https://fastapi.tiangolo.com/
- **Next.js Documentation:** https://nextjs.org/docs

---

**Ready to build?** Let's turn this plan into reality! 🚀
