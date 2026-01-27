# pyproject.toml Configuration Reference

Complete guide to configuring modern Python projects with pyproject.toml.

## Core Sections

### [project] - Package Metadata (PEP 621)

```toml
[project]
name = "myproject"
version = "0.1.0"
description = "A short description of the project"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
authors = [
    { name = "Your Name", email = "you@example.com" }
]
maintainers = [
    { name = "Maintainer", email = "maintainer@example.com" }
]
keywords = ["keyword1", "keyword2"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "requests>=2.28",
    "pydantic>=2.0",
]
```

### [project.urls]

```toml
[project.urls]
Homepage = "https://github.com/username/myproject"
Repository = "https://github.com/username/myproject"
Documentation = "https://myproject.readthedocs.io"
Changelog = "https://github.com/username/myproject/blob/main/CHANGELOG.md"
```

### [project.scripts] - CLI Entry Points

```toml
[project.scripts]
mycommand = "myproject.cli:main"
another-cmd = "myproject.commands:run"
```

### [project.optional-dependencies]

**For optional runtime features only** (NOT dev tools):

```toml
[project.optional-dependencies]
postgres = ["psycopg2>=2.9"]
redis = ["redis>=4.0"]
all = ["psycopg2>=2.9", "redis>=4.0"]
```

Users install with: `uv add myproject[postgres]`

## [dependency-groups] - Dev Dependencies (PEP 735)

**For development tools** (NOT installed by end users):

```toml
[dependency-groups]
dev = [
    "ruff>=0.8",
    "pre-commit>=4.0",
]
test = [
    "pytest>=8.0",
    "pytest-cov>=6.0",
    "hypothesis>=6.0",
]
docs = [
    "mkdocs>=1.6",
    "mkdocs-material>=9.0",
]
```

Install with: `uv sync --group test`

## [build-system]

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Common build backends:
- `hatchling` - Modern, fast (recommended)
- `setuptools` - Traditional, widely supported
- `flit_core` - Simple, minimal
- `pdm-backend` - PDM's backend

### Hatch Build Configuration

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/myproject"]

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/tests",
]
```

## [tool.uv]

```toml
[tool.uv]
default-groups = ["dev", "test"]
python-preference = "managed"
```

## Version Constraints

| Pattern | Meaning |
|---------|---------|
| `>=1.0` | Version 1.0 or higher |
| `>=1.0,<2` | Version 1.x only |
| `~=1.4.2` | Compatible release (>=1.4.2,<1.5.0) |
| `==1.4.2` | Exact version |
| `!=1.4.3` | Exclude version |

## Lock File

- **Applications**: Commit `uv.lock` for reproducible deployments
- **Libraries**: Add `uv.lock` to `.gitignore`

## Example: Library Package

```toml
[project]
name = "mylib"
version = "1.0.0"
description = "A reusable library"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
dependencies = []  # minimal dependencies for libraries

[dependency-groups]
dev = ["ruff>=0.8"]
test = ["pytest>=8.0", "pytest-cov>=6.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mylib"]
```

## Example: Application

```toml
[project]
name = "myapp"
version = "0.1.0"
description = "A web application"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn>=0.32",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
]

[dependency-groups]
dev = ["ruff>=0.8"]
test = ["pytest>=8.0", "pytest-cov>=6.0", "httpx>=0.27"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Example: CLI Tool

```toml
[project]
name = "mycli"
version = "1.0.0"
description = "A command-line tool"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
]

[project.scripts]
mycli = "mycli.main:cli"

[dependency-groups]
dev = ["ruff>=0.8"]
test = ["pytest>=8.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Dynamic Version from Git

```toml
[project]
name = "myproject"
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"

[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"
```

## Important Guidelines

1. **Always use `uv add` and `uv remove`** to manage dependencies. Don't edit dependency sections directly.

2. **dependency-groups vs optional-dependencies**:
   - `[dependency-groups]`: Dev tools (NOT installed by users)
   - `[project.optional-dependencies]`: Optional runtime features (installed by users)

3. **Lock file strategy**:
   - Applications: Commit `uv.lock`
   - Libraries: Gitignore `uv.lock`

4. **Version constraints**:
   - Use `>=X.Y,<X+1` for automatic minor updates
   - Use `>=X.Y` for flexibility
   - Pin exact versions only when necessary
