# uv Command Reference

uv is an extremely fast Python package and project manager written in Rust. It replaces pip, virtualenv, pip-tools, pipx, and pyenv with a single tool.

## Core Principle

Always use `uv run` to execute commands. Never manually activate virtual environments.

```bash
# Good
uv run python script.py
uv run pytest

# Avoid
source .venv/bin/activate
python script.py
```

## Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Homebrew
brew install uv

# pipx
pipx install uv
```

## Project Management

### Initialize Projects

```bash
# New application
uv init myproject

# New library with src/ layout
uv init --lib mypackage

# Initialize in current directory
uv init
```

### Dependency Management

```bash
# Add dependencies
uv add requests                    # runtime dependency
uv add --group dev ruff            # dev dependency
uv add --group test pytest         # test dependency
uv add 'requests>=2.28,<3'         # with version constraints

# Remove dependencies
uv remove requests
uv remove --group dev ruff

# Update dependencies
uv lock --upgrade                  # update all
uv lock --upgrade-package requests # update specific package

# Install dependencies
uv sync                            # install all
uv sync --group test               # include specific group
uv sync --frozen                   # use exact versions from lock
```

### Running Code

```bash
# Run Python scripts
uv run python script.py
uv run python -m mypackage

# Run tools
uv run pytest
uv run ruff check .
uv run ruff format .

# Run with temporary dependency
uv run --with rich python -c "from rich import print; print('[green]Hello[/green]')"
```

## Building and Publishing

```bash
# Build package
uv build                           # creates dist/ with wheel and sdist

# Publish to PyPI
uv publish                         # interactive authentication
uv publish --token $PYPI_TOKEN     # with token
```

## Tool Management

```bash
# Install global tools
uv tool install ruff
uv tool install --python 3.12 mypy

# Run tools without installing (uvx = uv tool run)
uvx ruff check .
uvx black --check .

# Upgrade tools
uv tool upgrade ruff
uv tool upgrade --all
```

## Python Version Management

```bash
# Install Python versions
uv python install 3.12
uv python install 3.11 3.12 3.13

# Pin project Python version
uv python pin 3.12

# List installed versions
uv python list

# Run with specific version
uv run --python 3.11 python script.py
```

## PEP 723 Scripts

Run single-file scripts with inline dependencies:

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "rich"]
# ///

import requests
from rich import print

response = requests.get("https://api.example.com")
print(response.json())
```

```bash
uv run script.py  # dependencies installed automatically
```

## Cache Management

```bash
# Clear cache
uv cache clean

# Set cache directory
export UV_CACHE_DIR=/path/to/cache

# Disable cache (for CI)
export UV_NO_CACHE=1
```

## Common Workflows

### New Application

```bash
uv init myapp
cd myapp
uv add fastapi uvicorn
uv add --group dev ruff
uv add --group test pytest httpx
uv run uvicorn myapp:app --reload
```

### New Library

```bash
uv init --lib mylib
cd mylib
uv add --group dev ruff
uv add --group test pytest pytest-cov
uv run pytest
uv build
```

### CI Environment

```bash
# Fast dependency installation
uv sync --frozen --no-dev
uv run pytest

# Or with caching disabled
UV_NO_CACHE=1 uv sync --frozen
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `UV_CACHE_DIR` | Cache directory location |
| `UV_NO_CACHE` | Disable caching |
| `UV_PYTHON` | Default Python version |
| `UV_SYSTEM_PYTHON` | Allow system Python |
| `UV_INDEX_URL` | Custom package index |

## Migration from pip

```bash
# From requirements.txt
uv init
uv add $(cat requirements.txt | grep -v '^#' | grep -v '^-' | tr '\n' ' ')

# From requirements-dev.txt
uv add --group dev $(cat requirements-dev.txt | grep -v '^#' | tr '\n' ' ')
```
