# ScribeNet: Technical Implementation Plan

> A self-hosted multi-agent system for collaborative book writing with interactive guidance

**Last Updated:** November 6, 2025

---

## 📋 Project Overview

**Name:** ScribeNet  
**Goal:** Self-hosted LLM agent system for writing, editing, and refining books with AI guidance  
**Architecture:** Multi-agent system with shared memory, MCP tool integration, and interactive chat interface

---

## 🏗️ System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Dashboard                         │
│        (Chat Interface + Project Visualization)              │
└────────────────────┬─────────────────────────────────────────┘
                     │ WebSocket + REST API
┌────────────────────┴─────────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │               Agent System                            │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │    Director Agent (Interactive Guide)           │  │  │
│  │  │    - Chat interface for user interaction        │  │  │
│  │  │    - Coordinates other agents via tools         │  │  │
│  │  │    - MCP tool calling integration               │  │  │
│  │  └────┬────────────────────────────────────────┬───┘  │  │
│  │       │                                        │      │  │
│  │  ┌────┴──────┐  ┌──────────┐  ┌──────────┐  ┌┴────┐ │  │
│  │  │ Outline   │  │ Writers  │  │ Editors  │  │Critic│ │  │
│  │  │  Agent    │  │ (Multi)  │  │ (Multi)  │  │Agent │ │  │
│  │  └───────────┘  └──────────┘  └──────────┘  └──────┘ │  │
│  │                                                        │  │
│  │  All agents emit status via WebSocket automatically   │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                               │
│        ┌─────────────────────┼────────────────────┐          │
│        │                     │                    │          │
│  ┌─────┴──────┐    ┌─────────┴────────┐   ┌──────┴──────┐  │
│  │   Ollama   │    │   Chroma DB      │   │   SQLite    │  │
│  │  (Models)  │    │ (Vector Store)   │   │  (State)    │  │
│  └────────────┘    └──────────────────┘   └─────────────┘  │
│                              │                               │
│  ┌───────────────────────────┴─────────────────────────┐   │
│  │           MCP (Model Context Protocol)               │   │
│  │  - File system tools (read/write/search)             │   │
│  │  - Git operations (commit, diff, history)            │   │
│  │  - Custom tools (extensible)                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                     ┌────────┴──────────┐
                     │   Git Repository  │
                     │ (Version Control) │
                     └───────────────────┘
```

### Key Design Decisions

1. **No CLI**: All interaction through web dashboard with chat interface
2. **No Orchestration Layer**: Agents are invoked directly or via Director agent using MCP tools
3. **MCP Integration**: Director can call tools (file operations, git, custom functions)
4. **Real-time Updates**: WebSocket status emission from all agents automatically
5. **Stateless Agents**: Fresh instances per request (except cached MCP connections)

---

## 🧠 Agent Specifications

### 1. Director Agent

**Responsibility:** Interactive guidance, project orchestration, tool coordination

**Key Functions:**
- **Interactive Chat**: Conversational interface for user guidance and questions
- **MCP Tool Calling**: Invoke tools for file operations, git commands, searches
- Parse user input (genre, theme, length, style preferences)
- Provide creative suggestions and project guidance
- Answer questions about the project or writing process
- Coordinate other agents through tool invocations (future)
- Track project state and provide status updates

**MCP Tools Available** (via config.yaml):
- File system operations (read, write, list, search)
- Git operations (commit, diff, history, branches)
- Custom extensible tools

**Real-time Status**:
- Emits `agent_working` when processing requests
- Emits `agent_completed` when responses are generated  
- Emits `agent_error` on failures
- WebSocket updates visible in dashboard

**Data Structures:**
```python
project_state = {
  "project_id": "uuid",
  "title": "Book Title",
  "genre": "sci-fi",
  "target_chapters": 25,
  "completed_chapters": 3,
  "vision_document": "markdown_text",
  "status": "active"  # planning, active, completed
}
```

**Chat Integration:**
- Maintains conversation history in database
- Context includes project details and chat history
- Supports tool calling (MCP) during conversation
- Can invoke other agents via tools (planned feature)

**Prompting Strategy:**
- System prompt defines role as creative director and guide
- Include current project state in context
- Conversational and helpful tone
- Can request tool usage from LLM (MCP integration)

**Status Emission:**
- Automatically emits status via BaseAgent methods
- WebSocket updates shown in dashboard AgentStatusCard
- No manual status management needed

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

**Note**: Currently implemented as a single agent with mode selection. Can be invoked for specific types.

**Key Functions:**
- Receive writing assignment (chapter, scene, or section)
- Retrieve context (previous chapters, character info, outline)
- Generate draft content
- Handle rewrites based on feedback

**Status Emission:**
- Emits `agent_working` when generating content
- Emits `agent_completed` on success
- Emits `agent_error` on failure
- All automatic via BaseAgent

**Input Context:**
- Relevant outline section
- Character profiles involved in scene
- Previous chapters (for continuity)
- Style guide/reference examples
- Specific writing instructions

**Model Routing:**
- Configurable per agent type in config.yaml
- Fast drafts: Llama 3.1 8B
- Quality prose: Qwen 2.5 14B
- All handled by Ollama

---

### 4. Editor Agents (Multi-Pass)

**Types:**
1. **Grammar Editor** - Spelling, grammar, punctuation
2. **Style Editor** - Voice consistency, rhythm, flow
3. **Continuity Editor** - Story bible compliance, timeline consistency

**Note**: Currently implemented as a single agent with pass type selection.

**Key Functions:**
- Receive draft text + edit instructions
- Apply specific editing pass
- Provide explanations for changes
- Return edited content

**Status Emission:**
- Automatic via BaseAgent (working → completed/error)
- Visible in dashboard in real-time

**Edit Passes (Sequential):**
```
Draft → Grammar Edit → Style Edit → Continuity Edit → Final
```

**Quality Metrics:**
- Can be implemented as separate evaluations
- Grammar error count
- Readability score
- Style consistency score

---

### 5. Critic Agent

**Responsibility:** Quality assessment, feedback generation

**Key Functions:**
- Rate content on multiple dimensions (1-10 scale):
  - Engagement/pacing
  - Character consistency
  - Emotional impact
  - Originality
  - Prose quality
  - Dialogue naturality
- Provide specific, actionable feedback
- Identify weak sections for improvement
- Track quality trends

**Status Emission:**
- Automatic via BaseAgent
- Real-time updates in dashboard

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
  "overall_score": 7.5
}
```

---

### 6. Summarizer Agent

**Responsibility:** Context compression, narrative history condensation

**Key Functions:**
- Generate concise summaries of completed chapters
- Compress old context when token limit approaches
- Maintain critical continuity information
- Create hierarchical summaries

**Status Emission:**
- Automatic via BaseAgent
- Shows "working" while summarizing

**Output Format:** 
Structured markdown with:
- Overall arc summary
- Chapter-by-chapter key points
- Active subplot tracking
- Continuity notes

**Model Configuration:**
- Uses efficient model (Llama 3.1 8B)
- Low temperature (0.3-0.4) for accuracy
- Target 10:1 compression ratio

---

## 💾 Memory System

### Components

#### 1. SQLite Database

**Purpose:** Structured state management, project metadata, chat history

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

-- Chat Messages (NEW)
CREATE TABLE chat_messages (
  id TEXT PRIMARY KEY,
  project_id TEXT,
  sender TEXT, -- 'user' or 'assistant'
  message TEXT,
  created_at TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- Quality Scores (NEW)
CREATE TABLE quality_scores (
  id TEXT PRIMARY KEY,
  chapter_id TEXT,
  dimension TEXT, -- engagement, quality, etc.
  score INTEGER, -- 0-10
  created_at TIMESTAMP,
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);
```

**Key Features:**
- Project isolation by project_id
- Chat history persistence
- Version tracking for chapters
- Quality metrics storage

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

##  Backend API (FastAPI)

### Core Endpoints

#### Project Management
- `POST /api/projects` - Create new book project
- `GET /api/projects/{id}` - Get project details
- `GET /api/projects` - List all projects
- `PUT /api/projects/{id}` - Update project settings
- `DELETE /api/projects/{id}` - Delete project

#### Chat Interface (Primary Interaction)
- `POST /api/projects/{id}/chat` - Send message to Director agent
- `GET /api/projects/{id}/chat/history` - Get conversation history
- `GET /api/projects/{id}/chat/tools` - Get available MCP tools
- `DELETE /api/projects/{id}/chat/history` - Clear chat history

#### Chapters
- `GET /api/projects/{id}/chapters` - List all chapters
- `GET /api/projects/{id}/chapters/{num}` - Get chapter details
- `POST /api/projects/{id}/chapters` - Create new chapter
- `PUT /api/projects/{id}/chapters/{num}` - Update chapter

#### Agent Operations (Future)
- `POST /api/agents/writer/generate` - Direct writer invocation
- `POST /api/agents/critic/evaluate` - Direct critic invocation
- `POST /api/agents/editor/edit` - Direct editor invocation

### WebSocket Endpoints

- `WS /ws/projects/{id}` - Real-time agent status updates
  - Agent status changes (working/completed/error/idle)
  - Progress updates
  - Tool execution notifications
  - Chat message events

**WebSocket Event Format:**
```json
{
  "event": "agent_working",
  "data": {
    "agent_type": "director",
    "message": "Processing request...",
    "progress": 50
  },
  "timestamp": "2025-11-06T10:30:00Z"
}
```

### MCP Integration

**MCP Servers Configured** (via config.yaml):
- File system server (read/write/search files)
- Git server (version control operations)
- Custom tools (extensible)

**Tool Invocation Flow:**
1. User asks Director a question requiring tools
2. Director LLM requests tool usage
3. Backend executes tool via MCP client
4. Result returned to LLM
5. LLM incorporates result in response
6. User sees final answer

**Configuration:**
```yaml
mcp:
  enabled: true
  servers:
    - name: filesystem
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"]
    - name: git
      command: npx
      args: ["-y", "@modelcontextprotocol/server-git", "--repository", "/path/to/repo"]
```

---

## 🎨 Frontend Dashboard (Next.js)

### Current Implementation

**Tech Stack:**
- Next.js 15 with App Router
- TypeScript
- Tailwind CSS
- WebSocket for real-time updates

### Pages/Views

#### 1. Project List (`/`)
- Grid of all book projects
- Project cards with status and progress
- Create new project modal
- Quick access to each project

#### 2. Project Dashboard (`/projects/[id]`)
**Main view with real-time updates:**

- **Chat Interface** (Primary interaction):
  - Conversational interface with Director agent
  - Message history persistence
  - Tool selection modal (configure which MCP tools to use)
  - Clear chat history option
  
- **Agent Status Cards**:
  - Real-time status indicators (idle/working/completed/error)
  - Pulsing animations for active agents
  - Elapsed time tooltip on hover
  - Progress bars for long operations
  - Status for all 6 agent types visible
  
- **Activity Feed**:
  - Live event log
  - WebSocket-driven updates
  - Shows agent actions, completions, errors
  
- **Chapter Grid** (Placeholder):
  - Visual representation of chapters
  - Status indicators
  - Quality scores
  - Click to view/edit
  
- **Expandable Sections**:
  - Quality scores
  - Project metadata
  - Export options

### Key UI Components

Implemented:
- ✅ **AgentStatusCard** - Real-time agent status with tooltip timer
- ✅ **ChatMessageBubble** - User/assistant messages
- ✅ **ToolSelectionModal** - Hierarchical tool configuration
- ✅ **ConfirmModal** - Branded confirmation dialogs
- ✅ **ActivityFeed** - Live event stream
- ✅ **ToastContainer** - Notifications
- ✅ **ExpandableSection** - Collapsible UI sections

Planned:
- ⏳ **ChapterGrid** - Visual chapter management
- ⏳ **StoryBibleViewer** - Character/location database
- ⏳ **QualityDashboard** - Score visualization

### Real-time Features

**WebSocket Integration:**
- Agent status updates every operation
- No polling required
- Automatic reconnection
- Project-scoped channels

**Event Types:**
- `agent_working` - Agent starts processing
- `agent_completed` - Agent finishes successfully
- `agent_error` - Agent encounters error
- `agent_idle` - Agent returns to idle
- (Future: `tool_executing`, `chapter_completed`, `quality_scored`)

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
| **Backend** | FastAPI | REST API, WebSocket, business logic |
| **Frontend** | Next.js 15 (TypeScript) | Dashboard, chat interface |
| **Database** | SQLite | Structured state, metadata, chat history |
| **Vector DB** | ChromaDB | Semantic search, embeddings |
| **LLM Serving** | Ollama | Local inference, model management |
| **Version Control** | Git (programmatic) | Chapter versioning |
| **Real-time** | WebSockets | Agent status updates, live events |
| **Tool Integration** | MCP (Model Context Protocol) | File ops, git, extensible tools |
| **Agent Framework** | Custom (BaseAgent) | Stateless agents with auto-status |

---

## 📦 Project Structure

```
scribenet/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── projects.py    # Project CRUD
│   │   │   ├── chapters.py    # Chapter management
│   │   │   └── chat.py        # Chat with Director
│   │   ├── websockets.py      # Real-time updates
│   │   └── main.py            # FastAPI app
│   ├── agents/
│   │   ├── base.py            # BaseAgent with auto-status
│   │   ├── director.py        # Interactive guide + MCP
│   │   ├── outline.py         # Story structure
│   │   ├── writer.py          # Content generation
│   │   ├── editor.py          # Multi-pass editing
│   │   ├── critic.py          # Quality evaluation
│   │   └── summarizer.py      # Context compression
│   ├── mcp/
│   │   └── client_manager.py # MCP connection manager
│   ├── memory/
│   │   ├── database.py        # SQLite operations
│   │   ├── vector_store.py    # ChromaDB wrapper
│   │   └── git_manager.py     # Git operations
│   ├── llm/
│   │   ├── ollama_client.py   # Ollama API client
│   │   └── prompts.py         # Prompt templates
│   └── utils/
│       ├── config.py          # Configuration management
│       └── logging.py         # Logging setup
├── frontend/
│   ├── app/
│   │   ├── page.tsx                        # Project list
│   │   ├── projects/[id]/page.tsx          # Main dashboard
│   │   ├── layout.tsx                      # Root layout
│   │   └── globals.css                     # Global styles
│   ├── components/
│   │   ├── AgentStatusCard.tsx             # Real-time agent status
│   │   ├── ChatMessageBubble.tsx           # Chat UI
│   │   ├── ToolSelectionModal.tsx          # MCP tool config
│   │   ├── ConfirmModal.tsx                # Confirmations
│   │   ├── ActivityFeed.tsx                # Event log
│   │   ├── ChapterGrid.tsx                 # Chapter overview
│   │   ├── ToastContainer.tsx              # Notifications
│   │   └── ExpandableSection.tsx           # Collapsible UI
│   ├── lib/
│   │   ├── api.ts                          # API client
│   │   ├── websocket.ts                    # WebSocket hook
│   │   └── branding.ts                     # Brand config
│   └── package.json
├── data/
│   ├── projects/                           # Git repos per project
│   │   └── project-{id}/
│   │       ├── outline.md
│   │       ├── chapters/
│   │       ├── drafts/
│   │       └── metadata/
│   ├── scribenet.db                        # SQLite database
│   └── chroma/                             # Vector DB storage
├── config.yaml                              # System configuration
├── pyproject.toml                           # Python dependencies
├── README.md
└── TECHNICAL_PLAN.md (this file)
```

---

## 🚦 Development Status

### ✅ Phase 1: Foundation (COMPLETE)
- SQLite schema with CRUD operations
- Ollama integration with async client
- Basic FastAPI with project endpoints
- All 6 core agents (Director, Outline, Writer, Editor, Critic, Summarizer)
- BaseAgent with automatic status emission
- Memory systems (SQLite, ChromaDB, Git)

### ✅ Phase 2: Core Backend (COMPLETE)
- All agent types implemented and functional
- Database persistence with version tracking
- Vector store for semantic search
- Git integration for version control
- Chat API with conversation history
- MCP integration for tool calling

### ✅ Phase 3: Frontend Dashboard (COMPLETE)
- Next.js 15 with App Router
- Project list and creation
- Main project dashboard with real-time updates
- Chat interface with Director agent
- Agent status cards with live WebSocket updates
- Tool selection modal for MCP configuration
- Activity feed and event logging
- Responsive design with Tailwind CSS

### ✅ Phase 4: Real-time Features (COMPLETE)
- WebSocket server for live updates
- Agent status emission (working/completed/error/idle)
- Automatic status updates from BaseAgent methods
- Project-scoped WebSocket channels
- Real-time UI updates without polling

### 🎯 Phase 5: Enhancements (IN PROGRESS)
- [ ] Chapter management UI (grid, details, editing)
- [ ] Story bible interface (characters, locations, timeline)
- [ ] Quality dashboard with score visualization
- [ ] Export functionality (PDF, EPUB, DOCX)
- [ ] Advanced MCP tool integration (invoke agents via tools)

### 🚀 Phase 6: Advanced Features (PLANNED)
- [ ] Streaming LLM responses (token-by-token)
- [ ] Progress bars for long operations
- [ ] Multi-step workflow automation
- [ ] Fine-tuned models for specific genres
- [ ] Advanced visualization (character graphs, plot timelines)

---

## 📊 Current Status Summary

**What Works:**
- ✅ All 6 agents functional with automatic status updates
- ✅ Interactive chat interface with Director agent
- ✅ MCP tool calling (file operations, git, extensible)
- ✅ Real-time WebSocket updates for all agents
- ✅ Database persistence (projects, chapters, chat history, scores)
- ✅ Vector store for semantic search
- ✅ Git version control
- ✅ Responsive web dashboard
- ✅ Multi-project support
- ✅ Tool selection and configuration UI

**What's Next:**
- ⏳ Chapter management interface
- ⏳ Story bible visualization
- ⏳ Quality score charts
- ⏳ Content export features
- ⏳ Workflow automation via Director + tools

**Testing**: Use the web dashboard to create projects and interact with the Director agent via chat.
- `backend/api/main.py` + `backend/api/routes/projects.py` - FastAPI with project endpoints
- `backend/agents/base.py` - Base agent class with Ollama integration
- `backend/agents/director.py` - Director agent with planning and task assignment
- `backend/agents/writer.py` - Narrative writer agent
- `backend/orchestration/workflows.py` + `backend/orchestration/state.py` - LangGraph workflows

---

## ⚙️ Configuration

### System Configuration (config.yaml)

```yaml
# Project defaults
project:
  default_word_count_per_chapter: 3000
  max_revision_iterations: 3
  quality_threshold: 7.0

# Agent models and settings
agents:
  director:
    model: "llama3.1:8b"
    temperature: 0.7
  outline:
    model: "llama3.1:8b"
    temperature: 0.6
  writers:
    narrative:
      model: "qwen2.5:14b"
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
    model: "llama3.1:8b"
    temperature: 0.5
  summarizer:
    model: "llama3.1:8b"
    temperature: 0.4
    compression_ratio: 10

# MCP tool integration
mcp:
  enabled: true
  servers:
    - name: filesystem
      command: npx
      args:
        - "-y"
        - "@modelcontextprotocol/server-filesystem"
        - "/path/to/projects"
    - name: git
      command: npx
      args:
        - "-y"
        - "@modelcontextprotocol/server-git"
        - "--repository"
        - "/path/to/repo"

# Memory systems
memory:
  chroma_collection: "scribenet"
  embedding_model: "all-MiniLM-L6-v2"
  vector_search_top_k: 5
  context_window_threshold: 0.8

# LLM backend
llm:
  ollama_url: "http://localhost:11434"
  num_ctx: 32768
  timeout: 120

# Git integration
git:
  auto_commit: true
  commit_on: ["chapter_complete", "outline_update"]
```

### Multi-User & Multi-Project Support

**Current Implementation**: ✅ Fully supported

**Architecture**:
- Agents are stateless (fresh instance per request)
- Projects isolated by `project_id` in database
- WebSocket channels scoped to projects (`/ws/projects/{project_id}`)
- Git repositories per project (`data/projects/project-{id}/`)
- Vector store filtered by project_id metadata
- Singleton MCP connection (safe, no state bleeding)

**Behavior**:
- Multiple users can work on different projects simultaneously ✅
- Multiple users on same project: works, but last write wins ⚠️
- No collaboration conflict resolution (designed for single user)

---

##  Resources & References

- **Ollama Documentation:** https://github.com/ollama/ollama
- **MCP (Model Context Protocol):** https://modelcontextprotocol.io/
- **ChromaDB Guide:** https://docs.trychroma.com/
- **FastAPI Best Practices:** https://fastapi.tiangolo.com/
- **Next.js Documentation:** https://nextjs.org/docs

---

**Status**: Production-ready for personal use! 🎊

Interactive chat interface with Director agent, real-time status updates for all agents, MCP tool integration, and comprehensive memory systems all working together.
│  │ ✂️  Editor       Waiting                                │  │
│  │ 📝 Outline      Completed                              │  │
│  │ 🎯 Director     Monitoring                             │  │
│  │ 📦 Summarizer   Completed                              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  📚 CHAPTERS                                                  │
│  ┌──────┬──────┬──────┬──────┬──────┐                        │
│  │ Ch 1 │ Ch 2 │ Ch 3 │ Ch 4 │ Ch 5 │                        │
│  │  ✅  │  ✅  │  🔄  │  ⏳  │  ⏳  │                        │
│  │ 8.2⭐│ 7.8⭐│  -   │  -   │  -   │                        │
│  └──────┴──────┴──────┴──────┴──────┘                        │
│                                                               │
│  📊 LATEST SCORES (Chapter 2)                                │
│  Engagement: ████████░░ 8/10                                 │
│  Quality:    ███████░░░ 7/10                                 │
│  Continuity: █████████░ 9/10                                 │
│                                                               │
│  📜 ACTIVITY LOG                                             │
│  [14:32] ✅ Chapter 2 completed (3,245 words)                │
│  [14:31] 📊 Quality score: 7.8/10                            │
│  [14:29] ✂️  Editing pass 3/3 complete                       │
│  [14:27] ✂️  Editing pass 2/3 complete                       │
│  [14:25] ✂️  Editing pass 1/3 complete                       │
│  [14:20] ✍️  Chapter 2 draft complete                        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Components Needed**:
- `AgentStatusCard` - Show agent state (idle/working/completed)
- `ChapterGrid` - Visual grid of chapters with status
- `ScoreDisplay` - Progress bars for quality metrics
- `ActivityFeed` - Real-time event log
- `ProgressBar` - Overall book completion

---

#### 3.4: Chapter Detail View

**URL**: `/projects/[id]/chapters/[num]`

View and manage individual chapters:

```
┌──────────────────────────────────────────────────────────┐
│  Chapter 3: The Discovery                                │
│  Status: ✅ Complete  |  Word Count: 3,245  |  Score: 8.2⭐│
├──────────────────────────────────────────────────────────┤
│                                                           │
│  📄 CONTENT                    📊 QUALITY SCORES         │
│  ┌──────────────────────┐     ┌───────────────────┐     │
│  │                      │     │ Engagement:  8/10 │     │
│  │ Content preview...   │     │ Quality:     7/10 │     │
│  │                      │     │ Continuity:  9/10 │     │
│  │ [View Full]          │     │ Originality: 7/10 │     │
│  └──────────────────────┘     └───────────────────┘     │
│                                                           │
│  💬 CRITIC FEEDBACK                                      │
│  "Good pacing overall. The dialogue in the middle        │
│   section could be more dynamic..."                      │
│                                                           │
│  🔧 ACTIONS                                              │
│  [🔄 Regenerate] [✏️ Edit Manually] [📥 Export]          │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

#### 3.5: Project List View

**URL**: `/`

Simple list of all projects:

```
┌──────────────────────────────────────────────────────────┐
│  My Projects                              [+ New Project] │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  📖 The Last Starship                                    │
│     Sci-Fi  •  Chapter 3/20  •  In Progress              │
│     [Open]                                                │
│                                                           │
│  📖 Mystery at Oak Manor                                 │
│     Mystery  •  Chapter 12/15  •  Editing                │
│     [Open]                                                │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

#### 3.6: Implementation Priority

**Day 1**: Backend APIs + WebSocket
- Add minimal endpoints
- Implement WebSocket server
- Add event emission to workflows

**Day 2-3**: Main Dashboard
- Project overview page
- Real-time agent status
- Chapter grid
- Activity feed

**Day 4**: Chapter Detail View
- Content display
- Quality scores
- Actions (regenerate, export)

**Day 5**: Polish + Project List
- Project list page
- Project creation flow
- Styling and UX improvements

---

#### 3.7: Key Features

**Real-time Updates**:
- WebSocket connection to backend
- Auto-update agent status every second
- Live activity log
- No page refresh needed

**Control Panel**:
- Start/pause/resume workflows
- Regenerate specific chapters
- Adjust quality thresholds
- Manual intervention points

**Transparency**:
- See exactly what each agent is doing
- Read full chapter content
- View quality scores and feedback
- Check activity history

---

**Success Criteria**:
- ✅ Can create project and start workflow from UI
- ✅ Can see agent activity in real-time
- ✅ Can view chapters and their quality scores
- ✅ Can regenerate chapters from UI
- ✅ Activity log shows all workflow events
- ✅ No more blind CLI-only workflow!

**Estimated Time**: 5-6 days total



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

##  Resources & References

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Ollama Documentation:** https://github.com/ollama/ollama
- **ChromaDB Guide:** https://docs.trychroma.com/
- **FastAPI Best Practices:** https://fastapi.tiangolo.com/
- **Next.js Documentation:** https://nextjs.org/docs

---

**Ready to build Phase 3!** Let's get that dashboard working so you can finally see what's happening! 🚀
