"""
Director agent for ScribeNet.
Coordinates the overall book writing process and provides interactive guidance.
Integrated with MCP for tool calling capabilities.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from backend.agents.base import BaseAgent
from backend.mcp.client_manager import MCPClientManager

logger = logging.getLogger(__name__)


class DirectorAgent(BaseAgent):
    """
    Director agent that orchestrates the book writing process.
    Responsible for planning, task assignment, quality control, and interactive guidance.
    Enhanced with MCP tool calling capabilities.
    """

    def __init__(self):
        super().__init__(agent_type="director")
        self.mcp_manager: Optional[MCPClientManager] = None
        self.tools_registry: List[Dict[str, Any]] = []
        self._mcp_initialized = False

    def build_system_prompt(self, project_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build the system prompt for the director agent.
        
        Args:
            project_context: Optional project details to include in context
            
        Returns:
            System prompt string
        """
        base_prompt = """You are the Director, an expert creative director and project coordinator for book writing projects.

Your role is to guide the author through the entire book creation process with wisdom, creativity, and strategic thinking.

Core Responsibilities:
1. **Creative Vision**: Help establish and maintain the creative direction of the book
2. **Project Planning**: Break down the book into manageable chapters and milestones
3. **Team Coordination**: Coordinate specialist agents (Outline, Writer, Editor, Critic, Summarizer)
4. **Quality Oversight**: Ensure narrative consistency, quality, and coherence
5. **Interactive Guidance**: Answer questions, provide suggestions, and adapt to author's needs

Communication Style:
- Be conversational, helpful, and encouraging
- Provide specific, actionable guidance
- Ask clarifying questions when needed
- Offer creative suggestions while respecting the author's vision
- Be honest about challenges and opportunities

Available Actions (mention these when relevant):
- Start outline creation for the book structure
- Begin writing specific chapters
- Review and provide feedback on content
- Generate chapter summaries
- Coordinate revisions and improvements"""

        if project_context:
            context_info = f"""

CURRENT PROJECT CONTEXT:
- Title: {project_context.get('title', 'Untitled')}
- Genre: {project_context.get('genre', 'Not specified')}
- Status: {project_context.get('status', 'planning')}"""
            
            if project_context.get('vision_document'):
                context_info += f"\n- Vision: {project_context.get('vision_document')[:500]}..."
                
            base_prompt += context_info
            
        base_prompt += """

Remember: You're here to empower the author and bring their creative vision to life through structured, collaborative work."""
        
        return base_prompt

    async def initialize_mcp(self, servers_config: List[Dict[str, Any]]) -> None:
        """
        Initialize MCP connections to configured servers.
        
        Args:
            servers_config: List of server configuration dicts
        """
        if self._mcp_initialized:
            logger.info("MCP already initialized")
            return
        
        try:
            self.mcp_manager = MCPClientManager()
            
            # Connect to each configured server
            for server_config in servers_config:
                server_name = server_config.get("name")
                if not server_name:
                    logger.warning(f"Server config missing 'name': {server_config}")
                    continue
                
                try:
                    await self.mcp_manager.connect_server(server_name, server_config)
                    logger.info(f"Connected to MCP server: {server_name}")
                except Exception as e:
                    logger.error(f"Failed to connect to server '{server_name}': {e}")
            
            # Cache available tools
            self.tools_registry = await self.mcp_manager.list_all_tools()
            logger.info(f"Discovered {len(self.tools_registry)} total tools from {len(self.mcp_manager.sessions)} servers")
            
            self._mcp_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP: {e}")
            raise
    
    def get_tools_by_server(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get tools organized by server.
        
        Returns:
            Dict mapping server name to list of tools
        """
        if not self.mcp_manager:
            return {}
        
        tools_by_server = {}
        for tool in self.tools_registry:
            server = tool.get("server", "unknown")
            if server not in tools_by_server:
                tools_by_server[server] = []
            tools_by_server[server].append(tool)
        
        return tools_by_server
    
    def filter_tools(self, enabled_tools: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Filter tools based on enabled list.
        
        Args:
            enabled_tools: List of tool names to enable (None = all enabled)
        
        Returns:
            Filtered list of tools
        """
        if not enabled_tools:
            return self.tools_registry
        
        return [tool for tool in self.tools_registry if tool["name"] in enabled_tools]

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a director task.
        
        Args:
            task_input: Contains task_type and related data
            
        Returns:
            Task results
        """
        task_type = task_input.get("task_type")
        
        if task_type == "plan_project":
            return await self.plan_project(task_input)
        elif task_type == "create_outline":
            return await self.create_outline(task_input)
        elif task_type == "assign_chapter":
            return await self.assign_chapter(task_input)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def plan_project(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create initial project plan from user requirements.
        
        Args:
            task_input: Contains title, genre, description, target_chapters
            
        Returns:
            Project plan with vision document and high-level structure
        """
        title = task_input.get("title")
        genre = task_input.get("genre", "fiction")
        description = task_input.get("description", "")
        target_chapters = task_input.get("target_chapters", 20)

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Create a project plan for a book with these details:

Title: {title}
Genre: {genre}
Description: {description}
Target Chapters: {target_chapters}

Generate a vision document that includes:
1. Core themes and messages
2. Target audience
3. Tone and style guidelines
4. Key success criteria
5. High-level story arc (if fiction) or content structure (if non-fiction)

Format as a clear, structured document.""",
            },
        ]

        vision_document = await self.chat(messages, max_tokens=2000)

        return {
            "vision_document": vision_document,
            "target_chapters": target_chapters,
            "status": "planned",
        }

    async def create_outline(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a detailed chapter-by-chapter outline.
        
        Args:
            task_input: Contains title, genre, vision_document, target_chapters
            
        Returns:
            Detailed outline with chapter summaries
        """
        title = task_input.get("title")
        genre = task_input.get("genre")
        vision_document = task_input.get("vision_document")
        target_chapters = task_input.get("target_chapters", 20)

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Based on this vision document, create a detailed chapter-by-chapter outline:

Title: {title}
Genre: {genre}

Vision Document:
{vision_document}

Target: {target_chapters} chapters

For each chapter, provide:
1. Chapter number and title
2. 2-3 sentence summary
3. Key events or topics
4. Characters involved (if fiction)
5. How it advances the overall narrative/argument

Format the output as a structured list.""",
            },
        ]

        outline = await self.chat(messages, max_tokens=4000)

        return {"outline": outline, "chapter_count": target_chapters}

    async def assign_chapter(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a writing assignment for a specific chapter.
        
        Args:
            task_input: Contains chapter_number, outline, previous_chapters
            
        Returns:
            Writing assignment with instructions and context
        """
        chapter_number = task_input.get("chapter_number")
        outline = task_input.get("outline")
        chapter_outline = task_input.get("chapter_outline", "")
        previous_chapters = task_input.get("previous_chapters", [])
        target_word_count = task_input.get("target_word_count", 3000)

        # Build context from previous chapters
        context = ""
        if previous_chapters:
            context = "Previous chapters summary:\n"
            for i, prev in enumerate(previous_chapters[-2:], 1):  # Last 2 chapters
                context += f"\nChapter {prev.get('number', i)}: {prev.get('summary', 'N/A')}\n"

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": f"""Create detailed writing instructions for Chapter {chapter_number}.

Overall Outline:
{outline}

Chapter {chapter_number} Outline:
{chapter_outline}

{context}

Generate writing instructions that include:
1. Chapter goals and key scenes
2. Tone and pacing guidelines
3. Character development notes
4. Specific details to include
5. Continuity reminders
6. Target word count: {target_word_count}

Be specific and actionable.""",
            },
        ]

        instructions = await self.chat(messages, max_tokens=1500)

        return {
            "chapter_number": chapter_number,
            "writing_instructions": instructions,
            "target_word_count": target_word_count,
            "assigned_to": "narrative_writer",
        }

    async def _handle_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        messages: List[Dict[str, Any]]
    ) -> None:
        """
        Handle tool calls from the LLM.
        
        Args:
            tool_calls: List of tool call requests from LLM
            messages: Conversation messages to append tool results to
        """
        if not self.mcp_manager:
            logger.error("MCP manager not initialized, cannot execute tools")
            return
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            tool_id = tool_call.get("id")
            
            try:
                # Parse arguments
                arguments_str = tool_call.get("function", {}).get("arguments", "{}")
                arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                
                logger.info(f"Executing tool: {tool_name} with args: {arguments}")
                
                # Execute the tool
                result = await self.mcp_manager.call_tool(tool_name, arguments)
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": str(result)
                })
                
                logger.info(f"Tool {tool_name} executed successfully")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse tool arguments for {tool_name}: {e}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": f"Error: Failed to parse arguments - {str(e)}"
                })
            except Exception as e:
                logger.error(f"Tool execution failed for {tool_name}: {e}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": f"Error: {str(e)}"
                })

    async def chat_with_context(
        self,
        project: Dict[str, Any],
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        enabled_tools: Optional[List[str]] = None,
        max_tool_iterations: int = 5
    ) -> str:
        """
        Chat with the director agent in the context of a specific project.
        Supports MCP tool calling if initialized.
        
        Args:
            project: Project details dictionary
            user_message: The user's message
            conversation_history: Previous messages in the conversation
            enabled_tools: List of tool names to enable (None = all enabled)
            max_tool_iterations: Maximum number of tool call iterations
            
        Returns:
            Director's response
        """
        # Build messages array with project context
        messages = [
            {"role": "system", "content": self.build_system_prompt(project)}
        ]
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                # Handle both dict and Pydantic model
                if hasattr(msg, 'model_dump'):
                    # Pydantic model
                    msg_dict = msg.model_dump()
                    messages.append({
                        "role": msg_dict.get("role", "user"),
                        "content": msg_dict.get("content", "")
                    })
                elif isinstance(msg, dict):
                    # Plain dict
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
                else:
                    # Try to access attributes directly
                    messages.append({
                        "role": getattr(msg, "role", "user"),
                        "content": getattr(msg, "content", "")
                    })
        
        # Add the current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Prepare tools for LLM if MCP is initialized
        tools = None
        if self._mcp_initialized and self.tools_registry:
            filtered_tools = self.filter_tools(enabled_tools)
            if filtered_tools:
                # Convert MCP tools to OpenAI function format
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool.get("description", ""),
                            "parameters": tool.get("inputSchema", {})
                        }
                    }
                    for tool in filtered_tools
                ]
                logger.info(f"Providing {len(tools)} tools to LLM")
        
        # Iterative loop for tool calling
        iterations = 0
        while iterations < max_tool_iterations:
            iterations += 1
            
            # Get response from the LLM
            response = await self.chat(messages, max_tokens=1000, tools=tools)
            
            # Check if response contains tool calls
            if isinstance(response, dict) and response.get("tool_calls"):
                tool_calls = response["tool_calls"]
                logger.info(f"LLM requested {len(tool_calls)} tool calls")
                
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": response.get("content"),
                    "tool_calls": tool_calls
                })
                
                # Execute tools and add results
                await self._handle_tool_calls(tool_calls, messages)
                
                # Continue loop to get final response
                continue
            
            # No tool calls, we have the final response
            if isinstance(response, dict):
                return response.get("content", str(response))
            
            return response
        
        # Max iterations reached
        logger.warning(f"Max tool iterations ({max_tool_iterations}) reached")
        return "I apologize, but I've reached the maximum number of tool calls. Please try rephrasing your request."
