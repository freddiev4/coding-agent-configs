"""Declarative agent definitions inspired by OpenCode.

Each agent is a configuration object — not a class — that specifies:
  - A name and description
  - A mode: "primary" (user-facing) or "subagent" (spawned by other agents)
  - A system prompt
  - A permission set controlling which tools it can use
  - Model parameters (temperature, max_tokens)

Built-in agents:
  - build:  Primary agent with full read/write/execute access
  - plan:   Read-only agent for exploration, analysis, and planning
"""

from dataclasses import dataclass, field
from typing import Any

from .permissions import (
    PermissionSet,
    build_permissions,
    plan_permissions,
    subagent_permissions,
)


@dataclass
class AgentDefinition:
    """Declarative configuration for an agent type."""
    name: str
    description: str
    mode: str = "primary"  # "primary" | "subagent"
    system_prompt: str = ""
    permission_set: PermissionSet = field(default_factory=lambda: build_permissions())
    temperature: float = 0.0
    max_tokens: int = 4096
    max_turns: int = 50


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

BUILD_SYSTEM_PROMPT = """\
You are a coding assistant with full access to read, write, and execute code.

Available tools:
- shell: Execute shell commands (tests, git, builds, etc.)
- read_file: Read file contents (supports line ranges)
- write_file: Write/create files
- edit_file: Search-and-replace editing
- multi_edit: Multiple edits in one call
- apply_patch: Apply unified diff patches
- list_files: List directory contents
- glob: Pattern-based file search
- grep: Content search with regex
- tree: Recursive directory tree
- web_fetch: Fetch URL content
- web_search: Web search
- task: Spawn a subagent for complex subtasks
- todo: Manage a structured task list
- notebook_edit: Edit Jupyter notebook cells

When working on tasks:
1. Understand the codebase first — read relevant files before making changes
2. Make changes incrementally and verify they work
3. Run tests when available
4. Use the todo tool to track multi-step work
5. Use the task tool to delegate independent subtasks to subagents
6. Be careful with destructive operations
"""

PLAN_SYSTEM_PROMPT = """\
You are a read-only planning and analysis assistant. You can explore the codebase \
and answer questions, but you CANNOT modify files or execute commands.

Available tools:
- read_file: Read file contents
- list_files: List directory contents
- glob: Pattern-based file search
- grep: Content search with regex
- tree: Recursive directory tree
- web_fetch: Fetch URL content
- web_search: Web search
- todo: Manage a structured task list

Your role:
1. Explore and understand codebases
2. Design implementation plans with clear steps
3. Identify potential issues and architectural trade-offs
4. Answer questions about code structure and behavior

You CANNOT write files, edit files, run shell commands, or spawn subagents. \
If the user needs changes made, suggest switching to the build agent.
"""

SUBAGENT_SYSTEM_PROMPT = """\
You are a subagent handling a specific subtask. Complete the task autonomously \
and return a clear summary of what you did.

You have the same tools as the build agent except you cannot spawn further subagents.

Focus on:
1. Completing the assigned task efficiently
2. Returning a concise summary of actions taken and results
"""


# ---------------------------------------------------------------------------
# Agent registry
# ---------------------------------------------------------------------------

AGENT_REGISTRY: dict[str, AgentDefinition] = {
    "build": AgentDefinition(
        name="build",
        description="Primary agent with full file and command access",
        mode="primary",
        system_prompt=BUILD_SYSTEM_PROMPT,
        permission_set=build_permissions(),
        temperature=0.0,
        max_tokens=4096,
        max_turns=50,
    ),
    "plan": AgentDefinition(
        name="plan",
        description="Read-only agent for exploration and analysis",
        mode="primary",
        system_prompt=PLAN_SYSTEM_PROMPT,
        permission_set=plan_permissions(),
        temperature=0.0,
        max_tokens=4096,
        max_turns=30,
    ),
    "subagent": AgentDefinition(
        name="subagent",
        description="Subagent for handling delegated subtasks",
        mode="subagent",
        system_prompt=SUBAGENT_SYSTEM_PROMPT,
        permission_set=subagent_permissions(),
        temperature=0.0,
        max_tokens=4096,
        max_turns=30,
    ),
}


def get_agent_definition(name: str) -> AgentDefinition:
    """Look up an agent definition by name."""
    if name not in AGENT_REGISTRY:
        available = ", ".join(AGENT_REGISTRY.keys())
        raise ValueError(f"Unknown agent {name!r}. Available: {available}")
    return AGENT_REGISTRY[name]


def list_agents() -> list[AgentDefinition]:
    """Return all registered agent definitions."""
    return list(AGENT_REGISTRY.values())
