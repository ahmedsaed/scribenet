#!/usr/bin/env python3
"""
Command-line interface for testing ScribeNet workflows.
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.memory.database import Database
from backend.orchestration.workflows import run_project_workflow, run_chapter_workflow
from backend.utils.config import get_config
from backend.llm.ollama_client import close_ollama_client, set_token_callback
from rich.console import Console
from collections import deque


async def test_project_creation():
    """Test creating a project with outline."""
    print("\n" + "=" * 60)
    print("🚀 ScribeNet CLI - Project Creation Test")
    print("=" * 60 + "\n")
    
    # Initialize database
    db = Database()
    
    # Project details
    project_id = str(uuid.uuid4())
    title = "The Last Starship"
    genre = "Science Fiction"
    description = "A thrilling space opera about humanity's last hope for survival"
    target_chapters = 2  # Very small for quick testing
    
    print("📚 Creating project:")
    print(f"   Title: {title}")
    print(f"   Genre: {genre}")
    print(f"   Chapters: {target_chapters}")
    print(f"   ID: {project_id}\n")
    
    # Create project in database
    db.create_project(
        project_id=project_id,
        title=title,
        genre=genre,
    )
    
    # Run workflow
    print("🔄 Running project workflow...\n")
    final_state = await run_project_workflow(
        project_id=project_id,
        title=title,
        genre=genre,
        description=description,
        target_chapters=target_chapters,
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60 + "\n")
    
    if final_state.get("error"):
        print(f"❌ Error: {final_state['error']}")
        return None
    
    print(f"✅ Phase: {final_state.get('phase')}")
    print("\n📄 Vision Document:")
    print("-" * 60)
    print(final_state.get("vision_document", "N/A"))
    
    print("\n📝 Outline:")
    print("-" * 60)
    print(final_state.get("outline", "N/A"))
    
    # Update project in database
    db.update_project(
        project_id,
        vision_document=final_state.get("vision_document"),
        status="outlined",
    )
    
    print("\n✅ Project created and saved to database!")
    return project_id, final_state


async def test_chapter_writing(project_id: str = None, outline: str = None):
    """Test writing a single chapter."""
    print("\n" + "=" * 60)
    print("✍️  ScribeNet CLI - Chapter Writing Test")
    print("=" * 60 + "\n")
    
    db = Database()
    
    # Use test data if no project provided
    if not project_id or not outline:
        print("⚠️  No project provided, using test data...")
        project_id = "test-project"
        outline = """
Chapter 1: The Signal
A mysterious signal from deep space changes everything.

Chapter 2: Preparation
The crew prepares for the dangerous journey.
"""
    
    chapter_id = str(uuid.uuid4())
    chapter_number = 1
    
    print("📖 Writing chapter:")
    print(f"   Chapter: {chapter_number}")
    print(f"   ID: {chapter_id}\n")
    
    # Create chapter in database
    db.create_chapter(
        chapter_id=chapter_id,
        project_id=project_id,
        chapter_number=chapter_number,
        title=f"Chapter {chapter_number}",
    )
    
    # Run workflow
    print("🔄 Running chapter workflow...\n")
    final_state = await run_chapter_workflow(
        project_id=project_id,
        chapter_id=chapter_id,
        chapter_number=chapter_number,
        outline=outline,
        chapter_outline="A mysterious signal from deep space changes everything.",
        target_word_count=500,  # Much smaller for testing (reduced from 1500)
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60 + "\n")
    
    if final_state.get("error"):
        print(f"❌ Error: {final_state['error']}")
        return
    
    print(f"✅ Status: {final_state.get('status')}")
    print(f"📏 Word Count: {final_state.get('word_count', 0)}")
    
    print("\n📋 Writing Instructions:")
    print("-" * 60)
    print(final_state.get("writing_instructions", "N/A"))
    
    print("\n📖 Chapter Content:")
    print("-" * 60)
    content = final_state.get("chapter_content", "N/A")
    # Show first 500 characters
    if len(content) > 500:
        print(content[:500] + "...\n[Content truncated for display]")
    else:
        print(content)
    # Log a short preview (last 3 lines) for quick inspection
    try:
        last_lines = "\n".join([line for line in content.strip().splitlines() if line][-3:])
        if last_lines:
            print("Chapter preview (last 3 lines):\n" + last_lines)
    except Exception:
        pass
    
    # Save chapter version
    version_id = str(uuid.uuid4())
    db.save_chapter_version(
        version_id=version_id,
        chapter_id=chapter_id,
        version=1,
        content=content,
        created_by="narrative_writer",
        metadata={"word_count": final_state.get("word_count", 0)},
        agent_name="narrative_writer",
        model=getattr(get_config().llm, 'single_model', None),
    )
    
    # Update chapter
    db.update_chapter(
        chapter_id,
        status="completed",
        word_count=final_state.get("word_count", 0),
    )
    
    print("\n✅ Chapter written and saved to database!")


async def test_full_workflow():
    """Test the complete workflow: project + chapter."""
    print("\n" + "🌟" * 30)
    print("   SCRIBENET FULL WORKFLOW TEST")
    print("🌟" * 30 + "\n")
    
    # Step 1: Create project
    result = await test_project_creation()
    if not result:
        print("\n❌ Project creation failed, stopping test")
        return
    
    project_id, project_state = result
    outline = project_state.get("outline", "")
    
    # Step 2: Write first chapter
    await test_chapter_writing(project_id=project_id, outline=outline)
    
    print("\n" + "🌟" * 30)
    print("   TEST COMPLETE!")
    print("🌟" * 30 + "\n")


async def main():
    """Main CLI entry point with spinner showing live generated tokens."""
    console = Console()
    
    console.print("🔧 Checking configuration...")
    try:
        config = get_config()
        console.print("✅ Config loaded")
        console.print(f"   Ollama URL: {config.llm.ollama_url}")
        console.print(f"   Database: {config.database.path}")
    except Exception:
        console.print("❌ Config error")
        return
    
    # Check if Ollama is running
    from backend.llm.ollama_client import get_ollama_client
    client = get_ollama_client()
    
    console.print("\n🔌 Checking Ollama server...")
    is_healthy = await client.health_check()
    if is_healthy:
        console.print("✅ Ollama server is running\n")
    else:
        console.print(f"❌ Ollama server not reachable at {config.llm.ollama_url}")
        console.print("   Please start Ollama server first:")
        console.print("   ollama serve")
        console.print(f"   ollama pull {config.llm.single_model}")
        return
    
    # Set up a status spinner that shows live tokens
    token_buffer = deque(maxlen=20)  # Keep last 20 tokens for preview
    status = console.status("[bold green]Starting...", spinner="dots")
    
    def _token_cb(tok: str):
        """Callback for receiving tokens from streaming LLM."""
        token_buffer.append(tok)
        # Join tokens to create preview text - strip newlines to keep it on one line
        preview = "".join(list(token_buffer)).replace("\n", " ").replace("\r", " ")
        # Update status with token preview
        status.update(f"[bold green]Generating...[/bold green] [dim]{preview}[/dim]")
    
    # Register global callback
    set_token_callback(_token_cb)
    
    # Start the status display
    status.start()
    
    try:
        await test_full_workflow()
    finally:
        # Stop the status display
        status.stop()
        # Clear callback and close client
        set_token_callback(None)
    
    try:
        await close_ollama_client()
        console.print("\n✅ Ollama client closed cleanly")
    except Exception:
        console.print("\n⚠️ Error closing Ollama client")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
