"""
LangGraph workflow definitions for ScribeNet.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from backend.orchestration.state import ProjectState, ChapterState
from backend.agents.director import DirectorAgent
from backend.agents.writer import NarrativeWriterAgent
from backend.memory.database import Database
from backend.memory.vector_store import VectorStore
from backend.memory.git_manager import GitManager
from backend.agents.summarizer import SummarizerAgent
from backend.agents.critic import CriticAgent
from backend.agents.editor import GrammarEditor, StyleEditor, ContinuityEditor
from backend.utils.config import get_config
import uuid
import json


# Initialize agents
config = get_config()

# Initialize agents and helpers
director = DirectorAgent()
writer = NarrativeWriterAgent()
summarizer = SummarizerAgent()
critic = CriticAgent()

# Memory & persistence
db = Database()
# Initialize vector store (Chroma). This is a required dependency — fail fast if not available.
vector_store = VectorStore(persist_directory=getattr(config.chroma, 'persist_directory', 'data/chroma'))

git_manager = GitManager(projects_base_path=getattr(config.git, 'projects_path', 'data/projects'))

# Editors for multi-pass editing
grammar_editor = GrammarEditor()
style_editor = StyleEditor()
continuity_editor = ContinuityEditor()


# ==================== Project Workflow ====================

async def plan_project_node(state: ProjectState) -> ProjectState:
    """Director creates project plan and vision document."""
    print(f"📋 Planning project: {state['title']}")
    
    try:
        result = await director.execute({
            "task_type": "plan_project",
            "title": state["title"],
            "genre": state.get("genre", "fiction"),
            "description": state.get("description", ""),
            "target_chapters": state.get("target_chapters", 20),
        })
        
        state["vision_document"] = result["vision_document"]
        state["phase"] = "outlining"
        # Initialize git repo for project if configured
        try:
            git_manager.init_project(
                project_id=state["project_id"],
                title=state["title"],
                genre=state.get("genre", ""),
                vision_document=state.get("vision_document", ""),
            )
            print("🔒 Git repository initialized for project")
        except Exception:
            # Non-fatal if git not available
            pass
        print("✅ Project plan created")
        
    except Exception as e:
        state["error"] = str(e)
        state["phase"] = "error"
        print(f"❌ Error planning project: {e}")
    
    return state


async def create_outline_node(state: ProjectState) -> ProjectState:
    """Director creates detailed chapter outline."""
    print(f"📝 Creating outline for {state['target_chapters']} chapters")
    
    try:
        result = await director.execute({
            "task_type": "create_outline",
            "title": state["title"],
            "genre": state.get("genre", "fiction"),
            "vision_document": state["vision_document"],
            "target_chapters": state["target_chapters"],
        })
        
        state["outline"] = result["outline"]
        state["current_chapter"] = 1
        state["completed_chapters"] = []
        state["phase"] = "writing"
        print("✅ Outline created")
        # Save outline to git if configured
        try:
            if getattr(config.git, 'auto_commit', False) and 'outline_update' in getattr(config.git, 'commit_on', []):
                git_manager.save_outline(project_id=state['project_id'], outline_content=state['outline'])
                print("🔒 Outline committed to git")
        except Exception:
            pass
        
    except Exception as e:
        state["error"] = str(e)
        state["phase"] = "error"
        print(f"❌ Error creating outline: {e}")
    
    return state


def should_continue_writing(state: ProjectState) -> str:
    """Determine if we should continue writing or end."""
    if state.get("error"):
        return "error"
    
    current = state.get("current_chapter", 1)
    target = state.get("target_chapters", 20)
    
    if current <= target:
        return "continue"
    else:
        return "end"


def build_project_workflow() -> StateGraph:
    """Build the main project workflow graph."""
    workflow = StateGraph(ProjectState)
    
    # Add nodes
    workflow.add_node("plan", plan_project_node)
    workflow.add_node("create_outline", create_outline_node)
    
    # Define edges
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "create_outline")
    workflow.add_edge("create_outline", END)
    
    return workflow.compile()


# ==================== Chapter Writing Workflow ====================

async def assign_chapter_node(state: ChapterState) -> ChapterState:
    """Director assigns chapter writing task."""
    print(f"📌 Assigning Chapter {state['chapter_number']}")
    
    try:
        # Retrieve semantic context from vector store to populate previous_chapters
        try:
            query_text = state.get('chapter_outline') or state.get('outline') or ''
            prev_results = vector_store.search_chapters(
                query=query_text,
                project_id=state.get('project_id'),
                n_results=getattr(config.memory, 'vector_search_top_k', 5)
            )
            previous_context = "\n\n".join(r['content'] for r in prev_results)
        except Exception:
            previous_context = ""

        result = await director.execute({
            "task_type": "assign_chapter",
            "chapter_number": state["chapter_number"],
            "outline": state["outline"],
            "chapter_outline": state.get("chapter_outline", ""),
            "previous_chapters": previous_context,
            "target_word_count": state.get("target_word_count", 3000),
        })

        state["writing_instructions"] = result["writing_instructions"]
        state["status"] = "writing"
        print("✅ Chapter assignment created")

    except Exception as e:
        state["error"] = str(e)
        state["status"] = "error"
        print(f"❌ Error assigning chapter: {e}")

    return state


async def write_chapter_node(state: ChapterState) -> ChapterState:
    """Writer generates chapter content."""
    print(f"✍️  Writing Chapter {state['chapter_number']}")
    
    try:
        result = await writer.execute({
            "task_type": "write_chapter",
            "chapter_number": state["chapter_number"],
            "writing_instructions": state["writing_instructions"],
            "chapter_outline": state.get("chapter_outline", ""),
            "previous_context": state.get("previous_context", ""),
            "target_word_count": state.get("target_word_count", 3000),
        })

        # Save draft/version to database
        content = result.get('content', '')
        word_count = result.get('word_count', len(content.split()))
        version_id = str(uuid.uuid4())
        try:
            db.save_chapter_version(
                version_id=version_id,
                chapter_id=state['chapter_id'],
                version=1,
                content=content,
                created_by='narrative_writer',
                metadata={"word_count": word_count},
                agent_name='narrative_writer',
                model=getattr(config.llm, 'single_model', None)
            )
        except Exception:
            pass

        # Add to vector store for semantic retrieval
        try:
            vector_store.add_chapter(
                chapter_id=state['chapter_id'],
                project_id=state['project_id'],
                chapter_number=state['chapter_number'],
                title=state.get('title', f"Chapter {state['chapter_number']}"),
                content=content,
                metadata={}
            )
        except Exception:
            pass

        # Generate chapter summary for context compression
        try:
            summary_res = await summarizer.execute('summarize_chapter', {
                'chapter_text': content,
                'chapter_number': state['chapter_number'],
                'story_bible': {}
            })
            # Persist summary
            try:
                db.save_summary(
                    summary_id=str(uuid.uuid4()),
                    project_id=state['project_id'],
                    start_chapter=state['chapter_number'],
                    end_chapter=state['chapter_number'],
                    summary_text=summary_res.get('summary', ''),
                    version_hash=summary_res.get('version_hash', '')
                )
            except Exception:
                pass
        except Exception:
            summary_res = None

        # Meta-summarize older chapters to manage context window
        try:
            recent_keep = getattr(config.project, 'recent_chapters_in_context', 2)
            all_summaries = db.get_project_summaries(state['project_id'])
            if len(all_summaries) > recent_keep + 1:
                # Summarize the older range (from 1 to N - recent_keep)
                cutoff = len(all_summaries) - recent_keep
                older_summaries = [s['summary_text'] for s in all_summaries[:cutoff]]
                meta = await summarizer.execute('meta_summarize', {
                    'summaries': older_summaries,
                    'story_bible': {}
                })
                # Save meta-summary for range
                try:
                    db.save_summary(
                        summary_id=str(uuid.uuid4()),
                        project_id=state['project_id'],
                        start_chapter=1,
                        end_chapter=cutoff,
                        summary_text=meta.get('meta_summary', ''),
                        version_hash=meta.get('meta_summary', '')[:32]
                    )
                except Exception:
                    pass
        except Exception:
            pass

        # Run critic evaluation
        try:
            evaluation = await critic.execute('evaluate_chapter', {
                'chapter_text': content,
                'chapter_number': state['chapter_number'],
                'story_bible': {},
                'previous_chapters_summary': summary_res.get('summary') if summary_res else ''
            })

            # Save score
            try:
                db.save_score(
                    score_id=str(uuid.uuid4()),
                    project_id=state['project_id'],
                    chapter_id=state['chapter_id'],
                    content_type='chapter',
                    scores=evaluation.get('scores', {}),
                    overall_score=evaluation.get('overall_score', 0.0),
                    feedback=evaluation.get('overall_assessment', ''),
                    requires_revision=evaluation.get('requires_revision', False),
                    revision_priority=evaluation.get('revision_priority', 'none')
                )
            except Exception:
                pass

            # If revision is recommended, run revision sub-workflow with multi-pass editing
            if critic.should_revise(evaluation):
                max_iters = getattr(config.project, 'max_revision_iterations', 3)
                revised_content = content
                for it in range(max_iters):
                    # Instruct writer to revise based on suggestions
                    revision_instructions = json.dumps(evaluation.get('suggestions', []))
                    revised = await writer.revise_chapter({
                        'chapter_content': revised_content,
                        'feedback': evaluation,
                        'revision_instructions': revision_instructions
                    })
                    revised_content = revised.get('content', revised_content)

                    # Multi-pass editing: Grammar -> Style -> Continuity
                    try:
                        g = await grammar_editor.edit({'content': revised_content, 'chapter_number': state['chapter_number']})
                        revised_content = g.get('edited_content', revised_content)
                    except Exception:
                        pass

                    try:
                        s = await style_editor.edit({'content': revised_content, 'chapter_number': state['chapter_number']})
                        revised_content = s.get('edited_content', revised_content)
                    except Exception:
                        pass

                    try:
                        c = await continuity_editor.edit({'content': revised_content, 'chapter_number': state['chapter_number'], 'story_bible': {}})
                        revised_content = c.get('edited_content', revised_content)
                    except Exception:
                        pass

                    # Save revised version
                    try:
                        db.save_chapter_version(
                            version_id=str(uuid.uuid4()),
                            chapter_id=state['chapter_id'],
                            version=it+2,
                            content=revised_content,
                            created_by='revision_pipeline',
                            metadata={'iteration': it+1},
                            agent_name='revision_pipeline',
                            model=getattr(config.llm, 'single_model', None)
                        )
                    except Exception:
                        pass

                    # Re-evaluate
                    evaluation = await critic.execute('evaluate_chapter', {
                        'chapter_text': revised_content,
                        'chapter_number': state['chapter_number'],
                        'story_bible': {},
                        'previous_chapters_summary': summary_res.get('summary') if summary_res else ''
                    })

                    if not critic.should_revise(evaluation):
                        content = revised_content
                        break

        except Exception as e:
            # Non-fatal: log evaluation errors and continue
            print(f"⚠️ Critic evaluation error: {e}")

        state["chapter_content"] = content
        state["word_count"] = word_count
        state["status"] = "completed"
        print(f"✅ Chapter written ({word_count} words)")
        # Auto-commit chapter on milestone if configured
        try:
            if getattr(config.git, 'auto_commit', False) and 'chapter_complete' in getattr(config.git, 'commit_on', []):
                commit_message = f"Finalize Chapter {state['chapter_number']}"
                git_manager.save_chapter(
                    project_id=state['project_id'],
                    chapter_number=state['chapter_number'],
                    title=state.get('title', f"Chapter {state['chapter_number']}"),
                    content=content,
                    commit_message=commit_message
                )
                print("🔒 Chapter committed to git")
        except Exception:
            pass
        
    except Exception as e:
        state["error"] = str(e)
        state["status"] = "error"
        print(f"❌ Error writing chapter: {e}")
    
    return state


def build_chapter_workflow() -> StateGraph:
    """Build the chapter writing workflow graph."""
    workflow = StateGraph(ChapterState)
    
    # Add nodes
    workflow.add_node("assign", assign_chapter_node)
    workflow.add_node("write", write_chapter_node)
    
    # Define edges
    workflow.set_entry_point("assign")
    workflow.add_edge("assign", "write")
    workflow.add_edge("write", END)
    
    return workflow.compile()


# ==================== Workflow Execution Functions ====================

async def run_project_workflow(
    project_id: str,
    title: str,
    genre: str = "fiction",
    description: str = "",
    target_chapters: int = 20,
) -> Dict[str, Any]:
    """
    Run the complete project creation workflow.
    
    Args:
        project_id: Project UUID
        title: Book title
        genre: Book genre
        description: Project description
        target_chapters: Number of chapters
        
    Returns:
        Final project state
    """
    initial_state: ProjectState = {
        "project_id": project_id,
        "title": title,
        "genre": genre,
        "description": description,
        "target_chapters": target_chapters,
        "phase": "planning",
        "current_chapter": 0,
        "completed_chapters": [],
    }
    
    workflow = build_project_workflow()
    final_state = await workflow.ainvoke(initial_state)
    
    return final_state


async def run_chapter_workflow(
    project_id: str,
    chapter_id: str,
    chapter_number: int,
    outline: str,
    chapter_outline: str = "",
    target_word_count: int = 3000,
) -> Dict[str, Any]:
    """
    Run the chapter writing workflow.
    
    Args:
        project_id: Project UUID
        chapter_id: Chapter UUID
        chapter_number: Chapter number
        outline: Full project outline
        chapter_outline: Specific chapter outline
        target_word_count: Target words for chapter
        
    Returns:
        Final chapter state with content
    """
    initial_state: ChapterState = {
        "project_id": project_id,
        "chapter_id": chapter_id,
        "chapter_number": chapter_number,
        "outline": outline,
        "chapter_outline": chapter_outline,
        "previous_context": "",
        "target_word_count": target_word_count,
        "status": "planning",
    }
    
    workflow = build_chapter_workflow()
    final_state = await workflow.ainvoke(initial_state)
    
    return final_state
