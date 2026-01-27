# Modern Python Development

Guidelines for modern Python tooling and best practices using uv, ruff, and pytest.

## When to Apply

- Creating a new Python project or package
- Configuring development tools (linting, formatting, testing)
- Managing Python dependencies
- Setting up CI/CD for Python projects

## When to Skip

- User explicitly requests legacy tooling (pip, virtualenv, flake8, black)
- Project requires Python < 3.11
- Existing project with established tooling (unless migration requested)

## Tool Stack

| Purpose | Modern Tool | Replaces |
|---------|-------------|----------|
| Package/project management | uv | pip, virtualenv, pyenv, pip-tools |
| Linting + formatting | ruff | flake8, black, isort, pylint |
| Testing | pytest | unittest |

## Quick Start

```bash
# Create new project
uv init myproject
cd myproject

# Add dependencies
uv add requests           # runtime dependency
uv add --group dev ruff   # dev dependency
uv add --group test pytest pytest-cov  # test dependency

# Install all dependencies
uv sync

# Run commands (no manual venv activation needed)
uv run python main.py
uv run pytest
uv run ruff check .
```

## Project Structure

```
myproject/
├── src/
│   └── myproject/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_main.py
├── pyproject.toml
├── uv.lock
└── README.md
```

## pyproject.toml Configuration

```toml
[project]
name = "myproject"
version = "0.1.0"
description = "Project description"
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = ["ruff>=0.8"]
test = ["pytest>=8.0", "pytest-cov>=6.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
]
```

## Dependency Groups (PEP 735)

Use `[dependency-groups]` for development tools, NOT `[project.optional-dependencies]`:

```toml
[dependency-groups]
dev = ["ruff>=0.8"]
test = ["pytest>=8.0", "pytest-cov>=6.0"]
docs = ["mkdocs>=1.6"]
```

Always use `uv add` and `uv remove` to manage dependencies. Do not edit dependency sections directly.

## Common Commands

```bash
# Project management
uv init myproject           # new application
uv init --lib mypackage     # new library with src/ layout

# Dependencies
uv add package              # add runtime dependency
uv add --group dev package  # add dev dependency
uv remove package           # remove dependency
uv sync                     # install all dependencies
uv sync --group test        # install with specific group

# Running code
uv run python script.py     # run script
uv run pytest               # run tests
uv run ruff check .         # run linter
uv run ruff format .        # format code

# Building & publishing
uv build                    # build wheel and sdist
uv publish                  # publish to PyPI
```

## Migration from Legacy Tools

### From requirements.txt

```bash
uv init
uv add $(cat requirements.txt | grep -v '^#' | tr '\n' ' ')
rm requirements.txt
```

### From setup.py/setup.cfg

1. Run `uv init` to create pyproject.toml
2. Move metadata from setup.py to [project] section
3. Move dependencies to pyproject.toml
4. Delete setup.py, setup.cfg, MANIFEST.in

### From flake8 + black + isort

Replace all three with ruff in pyproject.toml:

```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "W", "I"]  # I = isort rules
```

## References

See the `references/` directory for detailed guides:
- `uv.md` - Complete uv command reference
- `ruff.md` - Ruff configuration and rules
- `testing.md` - pytest setup and patterns
- `pyproject.md` - Full pyproject.toml configuration

## Templates

See the `templates/` directory for starter configurations:
- `pre-commit-config.yaml` - Pre-commit hook setup
- `pyproject.toml` - Starter project configuration
