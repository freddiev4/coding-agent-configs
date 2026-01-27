# Agent Configurations

Plugins, skills, hooks, and scripts for AI coding agents (Claude Code, Cursor, Windsurf, etc.).

## Directory Structure

```
.
├── plugins/              # Agent plugins
│   ├── ralph/           # Ralph Wiggum iterative loop technique
│   └── prd/             # PRD generation from brain dumps
├── skills/              # Reference documentation and templates
│   └── modern-python/   # Modern Python tooling (uv, ruff, pytest)
├── .claude/
│   ├── agents/          # Custom agent definitions
│   ├── hooks/           # Hook implementations
│   └── settings.json    # Agent settings
└── install-claude-git-guard.sh
```

## Plugins

### Ralph Wiggum (`plugins/ralph/`)

Iterative, self-referential AI development loops. Claude runs in a continuous feedback loop until task completion.

**Commands:**
- `/ralph-loop "<prompt>" --max-iterations <n> --completion-promise "<text>"` - Start loop
- `/cancel-ralph` - Cancel active loop
- `/help` - Documentation

**Best for:**
- Tasks with clear success criteria (tests pass, linter clean)
- Iterative refinement and debugging
- Autonomous implementation of well-defined features

**Example:**
```bash
/ralph-loop "Build a REST API with CRUD operations and tests. Output <promise>DONE</promise> when complete." --completion-promise "DONE" --max-iterations 50
```

### PRD Generator (`plugins/prd/`)

Transform brain dumps into structured Product Requirements Documents.

**Commands:**
- `/generate-prd "your idea here"` - Generate structured PRD

Creates `prd.md` with problem statement, requirements, success criteria, and task breakdown. Designed to work with Ralph Wiggum for iterative execution.

## Skills

### Modern Python (`skills/modern-python/`)

Guidelines and references for modern Python development using uv, ruff, and pytest.

**Contents:**
- `SKILL.md` - Quick start guide and overview
- `references/uv.md` - uv command reference
- `references/ruff.md` - Ruff linting/formatting configuration
- `references/testing.md` - pytest setup and patterns
- `references/pyproject.md` - pyproject.toml configuration
- `templates/` - Starter configurations

**Tool Stack:**
| Purpose | Tool | Replaces |
|---------|------|----------|
| Package management | uv | pip, virtualenv, pyenv |
| Linting + formatting | ruff | flake8, black, isort |
| Testing | pytest | unittest |

## Hooks

### Git Safety Guard

Blocks destructive git and filesystem commands to prevent accidental data loss.

**Install:**
```bash
./install-claude-git-guard.sh          # project-local
./install-claude-git-guard.sh --global # global
```

**Blocked operations:**
- `git reset --hard` - Loss of uncommitted changes
- `git push --force` - Rewriting remote history
- `git clean -fd` - Deleting untracked files
- `rm -rf` - Recursive deletion

## Resources

- [Claude Code](https://github.com/anthropics/claude-code)
- [Ralph Wiggum Technique](https://ghuntley.com/ralph/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
