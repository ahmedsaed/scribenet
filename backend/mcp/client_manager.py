"""
MCP Client Manager for ScribeNet.
Manages connections to multiple MCP servers and provides a unified interface for tool calling.
"""

from typing import Dict, List, Optional, Any
import asyncio
import logging
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from backend.mcp.errors import (
    ServerConnectionError,
    ToolNotFoundError,
    ToolExecutionError,
    ServerConfigurationError,
)

logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    Manages connections to multiple MCP servers.
    
    Features:
    - Connect to multiple MCP servers (stdio and http transports)
    - Dynamic tool discovery and caching
    - Unified tool calling interface
    - Connection lifecycle management
    - Error handling and logging
    """
    
    def __init__(self):
        """Initialize the MCP client manager."""
        self.sessions: Dict[str, ClientSession] = {}
        self.contexts: Dict[str, Any] = {}  # Store context managers
        self.tools_cache: Dict[str, List[dict]] = {}  # server_name -> tools
        self.tool_to_server: Dict[str, str] = {}  # tool_name -> server_name
        self._initialized = False
        logger.info("MCPClientManager initialized")
    
    async def connect_server(self, name: str, server_config: dict) -> None:
        """
        Connect to an MCP server.
        
        Args:
            name: Unique server identifier
            server_config: Server configuration dict with keys:
                - type: "stdio" or "http"
                - command: Command to run (for stdio)
                - args: Command arguments (for stdio)
                - env: Environment variables (optional)
                - url: Server URL (for http)
                - auth: Authentication config (for http)
        
        Raises:
            ServerConnectionError: If connection fails
            ServerConfigurationError: If configuration is invalid
        """
        try:
            server_type = server_config.get("type", "stdio")
            
            if server_type == "stdio":
                await self._connect_stdio_server(name, server_config)
            elif server_type == "http":
                await self._connect_http_server(name, server_config)
            else:
                raise ServerConfigurationError(
                    f"Unknown server type: {server_type}. Must be 'stdio' or 'http'"
                )
            
            # Discover and cache tools after successful connection
            await self._refresh_tools_for_server(name)
            
            logger.info(f"Successfully connected to MCP server: {name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{name}': {e}")
            raise ServerConnectionError(f"Failed to connect to server '{name}': {e}")
    
    async def _connect_stdio_server(self, name: str, config: dict) -> None:
        """Connect to a stdio-based MCP server."""
        command = config.get("command")
        args = config.get("args", [])
        env = config.get("env", {})
        
        if not command:
            raise ServerConfigurationError(
                f"Server '{name}': 'command' is required for stdio servers"
            )
        
        # Create server parameters
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env if env else None
        )
        
        # Create context manager for stdio client
        stdio_context = stdio_client(server_params)
        
        # Enter the context and store it
        read, write = await stdio_context.__aenter__()
        self.contexts[name] = stdio_context
        
        # Create and initialize session
        session = ClientSession(read, write)
        await session.__aenter__()
        
        # Initialize the session
        await session.initialize()
        
        self.sessions[name] = session
    
    async def _connect_http_server(self, name: str, config: dict) -> None:
        """Connect to an HTTP-based MCP server."""
        # HTTP transport implementation
        # For now, we'll focus on stdio which is more common for local servers
        raise NotImplementedError(
            "HTTP transport not yet implemented. Use stdio servers for now."
        )
    
    async def _refresh_tools_for_server(self, server_name: str) -> None:
        """Refresh tool list for a specific server."""
        session = self.sessions.get(server_name)
        if not session:
            logger.warning(f"Cannot refresh tools: server '{server_name}' not connected")
            return
        
        try:
            # List tools from the server
            tools_result = await session.list_tools()
            tools = []
            
            for tool in tools_result.tools:
                tool_dict = {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                    "server": server_name,
                }
                tools.append(tool_dict)
                
                # Map tool name to server
                self.tool_to_server[tool.name] = server_name
            
            self.tools_cache[server_name] = tools
            logger.info(f"Discovered {len(tools)} tools from server '{server_name}'")
            
        except Exception as e:
            logger.error(f"Failed to list tools from server '{server_name}': {e}")
            raise ToolExecutionError(f"Failed to list tools from '{server_name}': {e}")
    
    async def list_all_tools(self) -> List[dict]:
        """
        Get all available tools from all connected servers.
        
        Returns:
            List of tool definitions with schema
        """
        all_tools = []
        for server_name, tools in self.tools_cache.items():
            all_tools.extend(tools)
        
        logger.debug(f"Listed {len(all_tools)} total tools from {len(self.sessions)} servers")
        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments as dict
        
        Returns:
            Tool execution result
        
        Raises:
            ToolNotFoundError: If tool doesn't exist
            ToolExecutionError: If execution fails
        """
        # Find which server has this tool
        server_name = self.tool_to_server.get(tool_name)
        
        if not server_name:
            available_tools = ", ".join(self.tool_to_server.keys())
            raise ToolNotFoundError(
                f"Tool '{tool_name}' not found. Available tools: {available_tools}"
            )
        
        session = self.sessions.get(server_name)
        if not session:
            raise ServerConnectionError(
                f"Server '{server_name}' for tool '{tool_name}' is not connected"
            )
        
        try:
            logger.info(f"Calling tool '{tool_name}' on server '{server_name}'")
            logger.debug(f"Tool arguments: {arguments}")
            
            # Call the tool
            result = await session.call_tool(tool_name, arguments)
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            logger.debug(f"Tool result: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {e}")
            raise ToolExecutionError(f"Failed to execute tool '{tool_name}': {e}")
    
    async def disconnect_server(self, name: str) -> None:
        """
        Disconnect from a specific MCP server.
        
        Args:
            name: Server identifier
        """
        if name in self.sessions:
            try:
                session = self.sessions[name]
                await session.__aexit__(None, None, None)
                
                # Exit context if exists
                if name in self.contexts:
                    context = self.contexts[name]
                    await context.__aexit__(None, None, None)
                    del self.contexts[name]
                
                del self.sessions[name]
                
                # Clean up tool cache
                if name in self.tools_cache:
                    # Remove tool mappings
                    for tool in self.tools_cache[name]:
                        tool_name = tool["name"]
                        if tool_name in self.tool_to_server:
                            del self.tool_to_server[tool_name]
                    
                    del self.tools_cache[name]
                
                logger.info(f"Disconnected from server: {name}")
                
            except Exception as e:
                logger.error(f"Error disconnecting from server '{name}': {e}")
    
    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        server_names = list(self.sessions.keys())
        for name in server_names:
            await self.disconnect_server(name)
        
        logger.info("Disconnected from all MCP servers")
    
    async def refresh_all_tools(self) -> None:
        """Refresh tool lists from all connected servers."""
        for server_name in list(self.sessions.keys()):
            try:
                await self._refresh_tools_for_server(server_name)
            except Exception as e:
                logger.error(f"Failed to refresh tools from '{server_name}': {e}")
    
    def get_server_info(self) -> Dict[str, dict]:
        """
        Get information about connected servers.
        
        Returns:
            Dict mapping server names to info (connected, tool count)
        """
        info = {}
        for name in self.sessions.keys():
            tool_count = len(self.tools_cache.get(name, []))
            info[name] = {
                "name": name,
                "connected": True,
                "tool_count": tool_count,
                "tools": [t["name"] for t in self.tools_cache.get(name, [])]
            }
        return info
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect_all()
