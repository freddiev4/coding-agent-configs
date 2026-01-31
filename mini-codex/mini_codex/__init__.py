"""Mini Codex - A coding agent harness inspired by OpenCode."""

from .agent import Agent, AgentConfig
from .agents import AgentDefinition, get_agent_definition, list_agents
from .mcp_client import MCPManager
from .permissions import PermissionSet, PermissionLevel
from .session import Session

__version__ = "0.2.0"
__all__ = [
    "Agent",
    "AgentConfig",
    "AgentDefinition",
    "MCPManager",
    "PermissionLevel",
    "PermissionSet",
    "Session",
    "get_agent_definition",
    "list_agents",
]
