# Mini Codex

A coding agent harness inspired by [OpenCode](https://github.com/anomalyco/opencode), demonstrating production-grade harness patterns in ~1000 lines of Python.

## What's in the Harness

| Feature | Module | Description |
|---------|--------|-------------|
| **15 Built-in Tools** | `tools.py` | shell, read_file, write_file, edit_file, multi_edit, apply_patch, list_files, glob, grep, tree, web_fetch, web_search, task, todo, notebook_edit |
| **MCP Support** | `mcp_client.py` | Load external tool servers via the Model Context Protocol |
| **Permissions** | `permissions.py` | Per-agent tool access control (allow / ask / deny) |
| **Agent Definitions** | `agents.py` | Declarative `build` (full access) and `plan` (read-only) agents |
| **Subagent Spawning** | `agent.py` | The `task` tool spawns a child agent with its own session |
| **Session Management** | `session.py` | Forking, compaction, token usage tracking, save/load |
| **Agent Loop** | `agent.py` | Core loop with permission checks, MCP routing, auto-compaction |

## Architecture

```
User Input
  │
  ▼
Agent.run()  ─── loads AgentDefinition (build / plan / subagent)
  │
  ├─► _get_permitted_tools()  ── filters by PermissionSet
  ├─► _build_system_prompt()  ── includes MCP tool list
  │
  ▼
_call_model()  ── OpenAI API with permitted tools
  │
  ├─► tool_calls?
  │     ├─► permission check (allow / ask / deny)
  │     ├─► MCP tool? → MCPManager.call_tool()
  │     ├─► built-in? → ToolExecutor.execute()
  │     │     └─► "task" tool? → _spawn_subagent()
  │     │           └─► fork session → new Agent(subagent) → run_sync()
  │     └─► add results to session → loop
  │
  ├─► needs_compaction? → summarize + compact session
  │
  └─► final response → return
```

## Installation

```bash
pip install -e .
```

## Usage

### Interactive Mode

```bash
# Build agent (full access - default)
mini-codex

# Plan agent (read-only)
mini-codex --agent plan

# With MCP tool servers
mini-codex --mcp-config mcp.json
```

### Single Prompt

```bash
mini-codex -p "find all TODO comments in this project"
```

### REPL Commands

| Command | Description |
|---------|-------------|
| `exit` / `quit` | Exit |
| `reset` | Clear session history |
| `history` | Show conversation |
| `status` | Show session stats (turns, tokens, etc.) |
| `agents` | List available agent types |
| `switch build` / `switch plan` | Switch agent type |

### CLI Options

```
-d, --directory     Working directory (default: current)
-p, --prompt        Single prompt (non-interactive)
--model             OpenAI model (default: gpt-4o)
--agent             Agent type: build or plan (default: build)
--mcp-config        Path to MCP server config JSON
--no-auto-approve   Require confirmation for tool execution
```

## MCP Configuration

Create an `mcp.json` file:

```json
{
  "servers": {
    "my-tools": {
      "command": "npx",
      "args": ["-y", "@example/mcp-server"],
      "env": {"API_KEY": "..."}
    }
  }
}
```

Tools from MCP servers are automatically discovered and added to the agent's available tools.

## Tools

| # | Tool | Description |
|---|------|-------------|
| 1 | `shell` | Execute shell commands |
| 2 | `read_file` | Read files (with line range support) |
| 3 | `write_file` | Write/create files |
| 4 | `edit_file` | Search-and-replace editing |
| 5 | `multi_edit` | Multiple edits in one call |
| 6 | `apply_patch` | Apply unified diff patches |
| 7 | `list_files` | List directory contents |
| 8 | `glob` | Pattern-based file search |
| 9 | `grep` | Regex content search |
| 10 | `tree` | Recursive directory tree |
| 11 | `web_fetch` | Fetch URL content |
| 12 | `web_search` | Web search (needs API key) |
| 13 | `task` | Spawn a subagent |
| 14 | `todo` | Structured task list |
| 15 | `notebook_edit` | Edit Jupyter notebook cells |

## Agents

### Build Agent
Full read/write/execute access. Can spawn subagents. Shell commands require approval when `--no-auto-approve` is set.

### Plan Agent
Read-only. Can explore the codebase (read, list, glob, grep, tree) and search the web, but cannot modify files, run commands, or spawn subagents.

### Subagent
Spawned by the build agent via the `task` tool. Same permissions as build but cannot spawn further subagents (prevents infinite recursion).

## Programmatic Usage

```python
from mini_codex import Agent, AgentConfig

# Build agent with MCP
agent = Agent(
    working_dir="/path/to/project",
    config=AgentConfig(
        model="gpt-4o",
        agent_name="build",
        mcp_config_path="mcp.json",
    ),
)

# Run synchronously
response = agent.run_sync("What files are in this project?")
print(response)

# Switch to plan mode
agent.switch_agent("plan")

# Stream turns
for turn in agent.run("Analyze the architecture"):
    if turn.tool_calls:
        print(f"[{turn.agent_name}] Using {len(turn.tool_calls)} tools...")
    if turn.finished:
        print(turn.response)

# Clean up
agent.shutdown()
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## Credits

Inspired by [OpenCode](https://github.com/anomalyco/opencode) and [OpenAI Codex](https://github.com/openai/codex).
