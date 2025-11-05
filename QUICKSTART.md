# ScribeNet Quick Start Guide

## 🎯 Goal
Get ScribeNet running and write your first AI-generated chapter in under 10 minutes!

## ✅ Prerequisites Checklist

- [ ] Python 3.10 or higher installed
- [ ] Poetry installed (`curl -sSL https://install.python-poetry.org | python3 -`)
- [ ] Ollama installed (much easier than vLLM!)
- [ ] NVIDIA GPU with at least 12GB VRAM recommended (CPU works too)

## 🚀 Step-by-Step Setup

### 1. Install Ollama

```bash
# One-line install for Linux/Mac
curl -fsSL https://ollama.com/install.sh | sh
```

For Windows, download from: https://ollama.com/download

### 2. Install Project Dependencies

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

Or manually:
```bash
poetry install
mkdir -p data
```

### 3. Configure Your System

Edit `config.yaml`:

```yaml
llm:
  ollama_url: "http://localhost:11434"  # Default Ollama URL
  single_model: "llama3.1:8b"           # Your model name
```

### 4. Pull a Model and Start Ollama

```bash
# Pull Llama 3.1 8B (recommended for 12GB GPU)
ollama pull llama3.1:8b

# Start Ollama server (if not already running)
ollama serve
```

Wait for "Ollama is running" message.

### 5. Test the System

```bash
# Run the CLI test
poetry run python cli.py
```

This will:
1. ✅ Check configuration
2. ✅ Verify Ollama connection
3. ✅ Create a test project ("The Last Starship")
4. ✅ Generate vision document and outline
5. ✅ Write Chapter 1 (about 1500 words)
6. ✅ Save everything to database

**Expected time**: 2-5 minutes depending on your GPU

## 📊 What You'll See

```
🚀 ScribeNet CLI - Project Creation Test
==============================================================

📚 Creating project:
   Title: The Last Starship
   Genre: Science Fiction
   Chapters: 5
   
🔄 Running project workflow...

📋 Planning project: The Last Starship
✅ Project plan created

📝 Creating outline for 5 chapters
✅ Outline created

📊 RESULTS
==============================================================

✅ Phase: writing

📄 Vision Document:
------------------------------------------------------------
[Generated vision document will appear here]

📝 Outline:
------------------------------------------------------------
[Generated chapter outline will appear here]

✅ Project created and saved to database!
```

## 🎨 Using the API

Start the API server:

```bash
cd backend
poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8080
```

Then visit: `http://localhost:8080/docs` for interactive API documentation.

### Create a Project via API

```bash
curl -X POST http://localhost:8080/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Novel",
    "genre": "Fantasy",
    "vision_document": "An epic tale of magic and adventure"
  }'
```

### List Projects

```bash
curl http://localhost:8080/api/projects
```

## 🔍 Check Your Results

Database location: `data/scribenet.db`

View with:
```bash
sqlite3 data/scribenet.db "SELECT title, status FROM projects;"
sqlite3 data/scribenet.db "SELECT chapter_number, word_count FROM chapters;"
```

## ⚙️ Model Recommendations for RTX 3060 12GB

**Best Performance:**
- llama3.1:8b (8GB) ⭐ Recommended for 12GB GPU
- qwen2.5:7b (7GB) - Better creative writing

**Higher Quality (may need more VRAM):**
- qwen2.5:14b (14GB)
- gemma2:12b (12GB)
- deepseek-r1:14b (14GB)

## 🐛 Troubleshooting

### Ollama server not reachable
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Expected: JSON with list of models
```

If not running:
```bash
ollama serve
```

### Model not found
```bash
# List installed models
ollama list

# Pull the model if missing
ollama pull llama3.1:8b
```

### Out of memory
- Ollama automatically manages quantization
- Try a smaller model: `llama3.1:8b` instead of larger models
- Use Q4 variants if available

### Slow generation
- Ensure GPU is being used (check with `nvidia-smi`)
- Reduce `target_word_count` in test
- Increase temperature for faster but more varied output

## 🎯 Next Steps

1. **Customize your project**: Edit the test parameters in `cli.py`
2. **Write more chapters**: Modify the CLI to iterate through chapters
3. **Explore the API**: Use the FastAPI docs at `/docs`
4. **Move to Phase 2**: Add editor agents, critic, and more!

## 📚 Additional Resources

- Full documentation: `TECHNICAL_PLAN.md`
- Configuration options: `config.yaml` (with comments)
- API reference: `http://localhost:8080/docs` (when server is running)
- Ollama docs: https://ollama.com/library

## 💡 Pro Tips

- Start with shorter chapters (1000-1500 words) for testing
- Use temperature 0.8-0.9 for creative writing
- Save important outputs - database can be reset
- Watch GPU memory usage with `nvidia-smi`

---

**Ready to write your novel?** 🚀📖✨
