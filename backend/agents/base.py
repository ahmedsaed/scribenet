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
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens (uses config default if None)
            temperature: Sampling temperature (uses agent config if None)
            
        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.temperature
        
        response = await self.ollama.generate(
            prompt=prompt,
            model=self.model,
            temperature=temp,
            max_tokens=max_tokens,
        )
        
        return response.text

    async def chat(
        self,
        messages: list,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate chat completion using the configured model.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens (uses config default if None)
            temperature: Sampling temperature (uses agent config if None)
            
        Returns:
            Generated response text
        """
        temp = temperature if temperature is not None else self.temperature
        
        response = await self.ollama.chat_completion(
            messages=messages,
            model=self.model,
            temperature=temp,
            max_tokens=max_tokens,
        )
        
        return response.text
