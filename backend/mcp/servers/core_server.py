"""
Core MCP Server for ScribeNet.
Exposes ScribeNet's core functionality as MCP tools.

This server provides tools for:
- Project management (create, list, get info)
- Chapter operations (list, get, create, write)
- Outline generation
- Story bible management
- Critique and revision
- Context search

Architecture:
This server acts as an orchestrator, delegating to modular tool classes
for clean separation of concerns.
"""

import asyncio
import sys
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from backend.mcp.tools import (
    ProjectTools,
    OutlineTools,
    ChapterTools,
    CritiqueTools,
    StoryBibleTools,
    SearchTools,
)

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

# Create MCP server
app = Server("scribenet-core")

# Initialize tool instances
project_tools = ProjectTools()
outline_tools = OutlineTools()
chapter_tools = ChapterTools()
critique_tools = CritiqueTools()
story_bible_tools = StoryBibleTools()
search_tools = SearchTools()

# Map tool names to their handlers
TOOL_HANDLERS = {}


def _build_tool_map():
    """Build mapping of tool names to their handler instances."""
    for handler in [
        project_tools,
        outline_tools,
        chapter_tools,
        critique_tools,
        story_bible_tools,
        search_tools,
    ]:
        for tool in handler.get_tools():
            TOOL_HANDLERS[tool.name] = handler


# Build the tool map on module load
_build_tool_map()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools from all tool handlers."""
    all_tools = []
    
    for handler in [
        project_tools,
        outline_tools,
        chapter_tools,
        critique_tools,
        story_bible_tools,
        search_tools,
    ]:
        all_tools.extend(handler.get_tools())
    
    logger.info(f"Listing {len(all_tools)} tools")
    return all_tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute a tool by delegating to the appropriate handler."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        # Find the handler for this tool
        handler = TOOL_HANDLERS.get(name)
        
        if not handler:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
        
        # Delegate to the appropriate tool handler
        return await handler.execute(name, arguments)
        
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
