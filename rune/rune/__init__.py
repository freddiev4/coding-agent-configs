"""Rune - A coding agent harness."""

from rune.agent import Agent, AgentConfig
from rune.agents import AgentDefinition, get_agent_definition, list_agents
from rune.mcp_client import MCPManager
from rune.permissions import PermissionSet, PermissionLevel
from rune.session import Session

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
