"""Configuration management for ScribeNet."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Project configuration."""
    default_word_count_per_chapter: int = 3000
    max_revision_iterations: int = 3
    quality_threshold: float = 7.0
    recent_chapters_in_context: int = 2


class AgentConfig(BaseModel):
    """Agent configuration."""
    model: str
    temperature: float


class WritersConfig(BaseModel):
    """Writers configuration."""
    narrative: AgentConfig
    dialogue: AgentConfig
    description: AgentConfig


class EditorsConfig(BaseModel):
    """Editors configuration."""
    grammar: AgentConfig
    style: AgentConfig
    continuity: AgentConfig


class SummarizerConfig(AgentConfig):
    """Summarizer configuration."""
    compression_ratio: int = 10


class AgentsConfig(BaseModel):
    """All agents configuration."""
    director: AgentConfig
    outline: AgentConfig
    writers: WritersConfig
    editors: EditorsConfig
    critic: AgentConfig
    summarizer: SummarizerConfig


class MemoryConfig(BaseModel):
    """Memory configuration."""
    chroma_collection: str = "scribenet"
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_search_top_k: int = 5
    context_window_threshold: float = 0.8


class LLMConfig(BaseModel):
    """LLM configuration."""
    mode: str = "single"  # single mode (best for consumer GPUs)
    single_model: str = "llama3.1:8b"
    ollama_url: str = "http://localhost:11434"
    max_tokens: int = 8192
    timeout: int = 120
    num_ctx: int = 32768  # Context window size


class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str = "data/scribenet.db"


class GitConfig(BaseModel):
    """Git configuration."""
    auto_commit: bool = True
    commit_on: list = Field(default_factory=lambda: ["chapter_complete", "outline_update"])
    projects_path: str = "data/projects"


class ChromaConfig(BaseModel):
    """ChromaDB configuration."""
    persist_directory: str = "data/chroma"


class MCPServerConfig(BaseModel):
    """MCP Server configuration."""
    name: str
    type: str = "stdio"  # "stdio" or "http"
    command: Optional[str] = None
    args: Optional[list[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None
    auth: Optional[Dict[str, str]] = None


class MCPConfig(BaseModel):
    """MCP configuration."""
    enabled: bool = True
    servers: list[MCPServerConfig] = Field(default_factory=list)


class Config(BaseModel):
    """Main configuration."""
    project: ProjectConfig
    agents: AgentsConfig
    memory: MemoryConfig
    llm: LLMConfig
    database: DatabaseConfig
    git: GitConfig
    chroma: ChromaConfig
    mcp: Optional[MCPConfig] = None


class ConfigManager:
    """Configuration manager."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config: Optional[Config] = None

    def load(self) -> Config:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            config_dict = yaml.safe_load(f)

        self._config = Config(**config_dict)
        return self._config

    @property
    def config(self) -> Config:
        """Get configuration, loading if necessary."""
        if self._config is None:
            self.load()
        return self._config

    def get_agent_config(self, agent_type: str, agent_name: Optional[str] = None) -> AgentConfig:
        """Get configuration for a specific agent."""
        config = self.config
        
        if agent_name:
            # Handle nested configs like writers.narrative
            agent_group = getattr(config.agents, agent_type)
            return getattr(agent_group, agent_name)
        else:
            # Handle direct configs like director
            return getattr(config.agents, agent_type)


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get the global configuration."""
    return config_manager.config
