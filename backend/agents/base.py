"""
Base agent class for ScribeNet agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from backend.llm.ollama_client import get_ollama_client
from backend.utils.config import get_config, AgentConfig


class BaseAgent(ABC):
    """Base class for all ScribeNet agents."""

    def __init__(self, agent_type: str, agent_name: Optional[str] = None):
        """
        Initialize agent.
        
        Args:
            agent_type: Type of agent (e.g., 'director', 'writers')
            agent_name: Specific agent name for nested configs (e.g., 'narrative')
        """
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.config = get_config()
        self.ollama = get_ollama_client()
        self.project_id: Optional[str] = None  # Set by caller when context is available
        
        # Get agent-specific configuration
        config_manager = self.config
        if agent_name:
            agent_group = getattr(config_manager.agents, agent_type)
            self.agent_config: AgentConfig = getattr(agent_group, agent_name)
        else:
            self.agent_config: AgentConfig = getattr(config_manager.agents, agent_type)

    @property
    def model(self) -> str:
        """Get the model name for this agent."""
        return self.agent_config.model

    @property
    def temperature(self) -> float:
        """Get the temperature for this agent."""
        return self.agent_config.temperature

    @abstractmethod
    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task.
        
        Args:
            task_input: Input data for the task
            
        Returns:
            Task output data
        """
        pass

    def build_system_prompt(self) -> str:
        """
        Build the system prompt for this agent.
        Override in subclasses for agent-specific prompts.
        
        Returns:
            System prompt string
        """
        return "You are a helpful AI assistant."

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate text using the configured model.
        Automatically emits status updates via WebSocket if project_id is set.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens (uses config default if None)
            temperature: Sampling temperature (uses agent config if None)
            
        Returns:
            Generated text
        """
        # Emit working status
        await self.emit_status("working", "Generating content...")
        
        try:
            temp = temperature if temperature is not None else self.temperature
            
            response = await self.ollama.generate(
                prompt=prompt,
                model=self.model,
                temperature=temp,
                max_tokens=max_tokens,
            )
            
            # Emit completed status
            await self.emit_status("completed", "Content generated")
            
            return response.text
            
        except Exception as e:
            # Emit error status
            await self.emit_status("error", f"Generation failed: {str(e)}")
            raise

    async def chat(
        self,
        messages: list,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[list] = None,
    ):
        """
        Generate chat completion using the configured model.
        Automatically emits status updates via WebSocket if project_id is set.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens (uses config default if None)
            temperature: Sampling temperature (uses agent config if None)
            tools: Optional list of tools/functions for tool calling
            
        Returns:
            Generated response text (str) or dict with tool_calls
        """
        # Emit working status
        await self.emit_status("working", "Processing request...")
        
        try:
            temp = temperature if temperature is not None else self.temperature
            
            response = await self.ollama.chat_completion(
                messages=messages,
                model=self.model,
                temperature=temp,
                max_tokens=max_tokens,
                tools=tools,
            )
            
            # Emit completed status
            await self.emit_status("completed", "Response generated")
            
            # If tool calls are present, return them along with content
            if response.tool_calls:
                return {
                    "content": response.text,
                    "tool_calls": response.tool_calls
                }
            
            return response.text
            
        except Exception as e:
            # Emit error status
            await self.emit_status("error", f"Chat failed: {str(e)}")
            raise
    
    async def emit_status(self, status: str, message: str = "", progress: Optional[int] = None):
        """
        Emit agent status via WebSocket.
        
        Args:
            status: Status type ('working', 'completed', 'error', 'idle')
            message: Status message describing current task
            progress: Optional progress percentage (0-100)
        """
        if not self.project_id:
            return
        
        try:
            from backend.api.websockets import emit_event
            
            event_type = f"agent_{status}"
            data = {
                "agent_type": self.agent_type,
                "message": message,
            }
            
            if progress is not None:
                data["progress"] = progress
            
            await emit_event(event_type, data, self.project_id)
        except Exception as e:
            # Don't fail the agent operation if WebSocket fails
            import logging
            logging.warning(f"Failed to emit agent status: {e}")
