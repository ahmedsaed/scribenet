"""
Core MCP Server for ScribeNet.
Exposes ScribeNet's core functionality as MCP tools.
"""

import asyncio
import sys
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

# Create MCP server
app = Server("scribenet-core")

# Import ScribeNet components (we'll do lazy imports to avoid circular dependencies)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_project_info",
            description="Get information about a project by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The unique identifier of the project"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="list_projects",
            description="List all projects in the system",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of projects to return",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="create_project",
            description="Create a new book writing project",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the book"
                    },
                    "genre": {
                        "type": "string",
                        "description": "The genre of the book (e.g., sci-fi, mystery, fantasy)"
                    },
                    "description": {
                        "type": "string",
                        "description": "A brief description of the book"
                    },
                    "target_chapters": {
                        "type": "integer",
                        "description": "Number of chapters planned",
                        "default": 20
                    }
                },
                "required": ["title", "genre"]
            }
        ),
        Tool(
            name="list_chapters",
            description="List all chapters in a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The unique identifier of the project"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="get_chapter_content",
            description="Get the content of a specific chapter",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The unique identifier of the project"
                    },
                    "chapter_number": {
                        "type": "integer",
                        "description": "The chapter number to retrieve"
                    }
                },
                "required": ["project_id", "chapter_number"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute a tool."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        # Lazy import to avoid circular dependencies
        from backend.memory.database import Database
        
        db = Database()
        
        if name == "list_projects":
            limit = arguments.get("limit", 10)
            projects = db.list_projects()
            
            # Apply limit after fetching
            projects = projects[:limit] if limit else projects
            
            if not projects:
                return [TextContent(
                    type="text",
                    text="No projects found in the system."
                )]
            
            result = "Projects:\n"
            for proj in projects:
                result += f"\n- {proj['title']} ({proj['genre']})\n"
                result += f"  ID: {proj['id']}\n"
                result += f"  Status: {proj['status']}\n"
                if proj.get('target_chapters'):
                    result += f"  Target Chapters: {proj['target_chapters']}\n"
            
            return [TextContent(type="text", text=result)]
        
        elif name == "get_project_info":
            project_id = arguments["project_id"]
            project = db.get_project(project_id)
            
            if not project:
                return [TextContent(
                    type="text",
                    text=f"Project with ID '{project_id}' not found."
                )]
            
            result = f"Project: {project['title']}\n"
            result += f"Genre: {project['genre']}\n"
            result += f"Status: {project['status']}\n"
            result += f"Target Chapters: {project.get('target_chapters', 'Not set')}\n"
            
            if project.get('description'):
                result += f"\nDescription:\n{project['description']}\n"
            
            if project.get('vision_document'):
                result += f"\nVision Document:\n{project['vision_document'][:500]}...\n"
            
            return [TextContent(type="text", text=result)]
        
        elif name == "create_project":
            title = arguments["title"]
            genre = arguments["genre"]
            description = arguments.get("description", "")
            target_chapters = arguments.get("target_chapters", 20)
            
            project = db.create_project(
                title=title,
                genre=genre,
                description=description,
                target_chapters=target_chapters
            )
            
            result = f"Created project: {project['title']}\n"
            result += f"ID: {project['id']}\n"
            result += f"Genre: {project['genre']}\n"
            result += f"Target Chapters: {target_chapters}\n"
            
            return [TextContent(type="text", text=result)]
        
        elif name == "list_chapters":
            project_id = arguments["project_id"]
            chapters = db.get_chapters_by_project(project_id)
            
            if not chapters:
                return [TextContent(
                    type="text",
                    text=f"No chapters found for project '{project_id}'."
                )]
            
            result = f"Chapters ({len(chapters)}):\n"
            for chapter in chapters:
                result += f"\nChapter {chapter['chapter_number']}: {chapter.get('title', 'Untitled')}\n"
                result += f"  Status: {chapter['status']}\n"
                result += f"  Word Count: {chapter.get('word_count', 0)}\n"
            
            return [TextContent(type="text", text=result)]
        
        elif name == "get_chapter_content":
            project_id = arguments["project_id"]
            chapter_number = arguments["chapter_number"]
            
            chapter = db.get_chapter(project_id, chapter_number)
            
            if not chapter:
                return [TextContent(
                    type="text",
                    text=f"Chapter {chapter_number} not found in project '{project_id}'."
                )]
            
            result = f"Chapter {chapter['chapter_number']}: {chapter.get('title', 'Untitled')}\n"
            result += f"Status: {chapter['status']}\n"
            result += f"Word Count: {chapter.get('word_count', 0)}\n"
            result += f"\nContent:\n{chapter.get('content', 'No content yet.')}\n"
            
            return [TextContent(type="text", text=result)]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error executing tool: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    logger.info("Starting ScribeNet Core MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
