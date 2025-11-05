# ScribeNet

A self-hosted multi-agent system for collaborative book writing using LLMs.

## 🎯 Overview

ScribeNet uses multiple AI agents working together to write books:
- **Director Agent**: Plans and coordinates the project
- **Writer Agents**: Generate creative prose
- **Editor Agents**: Polish and refine (Phase 2)
- **Critic Agent**: Evaluate quality (Phase 2)

## 📋 Phase 1 - MVP Status ✅

**All Phase 1 tasks complete!**

- [x] SQLite schema + basic database operations
- [x] Ollama setup with single model
- [x] Basic FastAPI with project CRUD endpoints
- [x] Director agent with simple task assignment
- [x] Single Writer agent (narrative only)
- [x] Simple LangGraph workflow
- [x] CLI interface for testing

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Poetry
- Ollama (easier setup than vLLM for consumer GPUs)

### Installation

1. **Install Ollama:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

2. **Install dependencies:**
```bash
poetry install
```

3. **Configure settings:**
Edit `config.yaml` to set your Ollama model preferences.

4. **Pull a model:**
```bash
# Example: Pull Llama 3.1 8B (recommended for 12GB GPU)
ollama pull llama3.1:8b
```

5. **Start Ollama server** (if not already running):
```bash
ollama serve
```

### Usage

#### Option 1: CLI (Testing)

Run the test CLI to create a project and write a chapter:

```bash
poetry run python cli.py
```

This will:
1. Create a test science fiction project
2. Generate a vision document and outline
3. Write the first chapter
4. Save everything to the database

#### Option 2: API Server

Start the FastAPI server:

```bash
cd backend
poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8080
```

API will be available at `http://localhost:8080`

**Endpoints:**
- `GET /` - API info
- `GET /health` - Health check
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects
- `GET /api/projects/{id}` - Get project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

## 📁 Project Structure

```
scribenet/
├── backend/
│   ├── agents/          # AI agents (Director, Writer, etc.)
│   ├── api/             # FastAPI routes and models
│   ├── llm/             # Ollama client
│   ├── memory/          # Database and storage
│   ├── orchestration/   # LangGraph workflows
│   └── utils/           # Configuration and utilities
├── data/                # SQLite database (created on first run)
├── config.yaml          # Configuration file
├── cli.py               # CLI testing interface
└── TECHNICAL_PLAN.md    # Full technical documentation
```

## 🔧 Configuration

Key settings in `config.yaml`:

```yaml
llm:
  mode: "single"              # single model mode (best for 12GB GPU)
  single_model: "llama3.1:8b"
  ollama_url: "http://localhost:11434"
  num_ctx: 32768              # Context window

project:
  default_word_count_per_chapter: 3000
  target_chapters: 20
```

## 📝 Example Workflow

1. **Create Project**: Director generates vision and outline
2. **Write Chapters**: Writer agent generates content based on outline
3. **Store Results**: All content saved to SQLite with versioning

## 🚧 What's Next (Phase 2)

- Multiple writer types (dialogue, description)
- Editor agents (grammar, style, continuity)
- Critic agent with quality scoring
- Context summarization for long books
- ChromaDB vector search
- Git version control integration

## 📚 Documentation

See `TECHNICAL_PLAN.md` for complete architecture and implementation details.

## 🐛 Troubleshooting

**Ollama server not reachable:**
- Ensure Ollama is running: `ollama serve`
- Check `config.yaml` has correct `ollama_url`
- Try `curl http://localhost:11434/api/tags` to verify connection

**Out of memory errors:**
- Use a smaller model (e.g., `llama3.1:8b` instead of `:14b`)
- Ollama automatically manages quantization and memory
- Try a Q4 quantized model if needed

**Import errors:**
- Run `poetry install` to ensure all dependencies are installed

## 📄 License

MIT
