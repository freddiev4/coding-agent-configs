# Ruff Configuration Reference

Ruff is an extremely fast Python linter and formatter written in Rust. It replaces flake8, black, isort, pylint, and many other tools.

## Basic Setup

Add to `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
```

## Running Ruff

```bash
# Linting
uv run ruff check .                # check all files
uv run ruff check src/             # check specific directory
uv run ruff check --fix .          # auto-fix issues
uv run ruff check --fix --unsafe-fixes .  # include unsafe fixes

# Formatting
uv run ruff format .               # format all files
uv run ruff format --check .       # check without modifying
uv run ruff format --diff .        # show diff
```

## Rule Categories

| Code | Tool Equivalent | Purpose |
|------|-----------------|---------|
| E | pycodestyle | Style errors |
| W | pycodestyle | Style warnings |
| F | pyflakes | Logical errors |
| I | isort | Import sorting |
| N | pep8-naming | Naming conventions |
| D | pydocstyle | Docstring conventions |
| UP | pyupgrade | Python upgrade suggestions |
| B | flake8-bugbear | Bug detection |
| S | flake8-bandit | Security issues |
| A | flake8-builtins | Builtin shadowing |
| C4 | flake8-comprehensions | Comprehension improvements |
| DTZ | flake8-datetimez | Timezone-aware datetime |
| T10 | flake8-debugger | Debugger statements |
| T20 | flake8-print | Print statements |
| PT | flake8-pytest-style | Pytest conventions |
| Q | flake8-quotes | Quote consistency |
| SIM | flake8-simplify | Code simplification |
| ARG | flake8-unused-arguments | Unused arguments |
| PTH | flake8-use-pathlib | Pathlib usage |
| ERA | eradicate | Commented-out code |
| PL | pylint | Various checks |
| RUF | ruff-specific | Ruff-specific rules |
| ANN | flake8-annotations | Type annotation checks |

## Recommended Configuration

```toml
[tool.ruff]
line-length = 88
target-version = "py311"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "SIM",    # flake8-simplify
    "ARG",    # flake8-unused-arguments
    "PTH",    # flake8-use-pathlib
    "RUF",    # ruff-specific
]
ignore = [
    "E501",   # line too long (handled by formatter)
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = [
    "ARG001", # unused function argument (fixtures)
    "S101",   # use of assert
]
"__init__.py" = ["F401"]  # unused imports
"scripts/**" = ["T20"]    # print statements OK in scripts

[tool.ruff.lint.isort]
known-first-party = ["myproject"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true
```

## Strict Configuration

For maximum checking:

```toml
[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "D",      # pydocstyle (enable selectively)
    "ANN",    # flake8-annotations (use type checker instead)
    "COM812", # trailing comma (conflicts with formatter)
    "ISC001", # string concatenation (conflicts with formatter)
]
```

## Import Sorting

Ruff includes isort functionality:

```toml
[tool.ruff.lint.isort]
known-first-party = ["myproject"]
known-third-party = ["fastapi", "pydantic"]
section-order = ["future", "standard-library", "third-party", "first-party", "local-folder"]
force-single-line = false
lines-after-imports = 2
```

## Docstring Style

```toml
[tool.ruff.lint.pydocstyle]
convention = "google"  # or "numpy" or "pep257"
```

## Formatter Configuration

```toml
[tool.ruff.format]
quote-style = "double"           # or "single"
indent-style = "space"           # or "tab"
line-ending = "auto"             # or "lf" or "crlf"
docstring-code-format = true     # format code in docstrings
skip-magic-trailing-comma = false
```

## CI Configuration

GitHub Actions workflow:

```yaml
name: Lint

on: [push, pull_request]

jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --group dev
      - run: uv run ruff check --output-format=github .
      - run: uv run ruff format --check .
```

## Migration from Other Tools

### From flake8

```toml
# flake8 codes map directly to ruff E/W/F codes
# .flake8 max-line-length -> [tool.ruff] line-length
# .flake8 ignore -> [tool.ruff.lint] ignore
```

### From black

```toml
# black line-length -> [tool.ruff] line-length
# black target-version -> [tool.ruff] target-version
# Formatting is compatible by default
```

### From isort

```toml
# isort profile="black" -> already default
# isort known_first_party -> [tool.ruff.lint.isort] known-first-party
```

## Pre-commit Integration

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```
