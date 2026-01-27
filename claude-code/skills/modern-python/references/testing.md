# Testing with pytest

Comprehensive guide to pytest setup, patterns, and best practices.

## Installation

```bash
uv add --group test pytest pytest-cov
```

## Configuration

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
]

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

## Project Structure

```
myproject/
├── src/
│   └── myproject/
│       ├── __init__.py
│       └── core.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # shared fixtures
│   ├── test_core.py
│   └── integration/
│       └── test_api.py
└── pyproject.toml
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run specific file
uv run pytest tests/test_core.py

# Run specific test
uv run pytest tests/test_core.py::test_function_name

# Run tests matching pattern
uv run pytest -k "test_login"

# Run tests with marker
uv run pytest -m "not slow"
uv run pytest -m integration

# Stop on first failure
uv run pytest -x

# Re-run failed tests
uv run pytest --lf

# Verbose output
uv run pytest -v
```

## Coverage

```bash
# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Generate HTML report
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html

# Generate XML for CI
uv run pytest --cov=src --cov-report=xml
```

## Test Patterns

### Basic Test

```python
def test_addition():
    assert 1 + 1 == 2

def test_string_contains():
    assert "hello" in "hello world"
```

### Testing Exceptions

```python
import pytest

def test_raises_value_error():
    with pytest.raises(ValueError, match="invalid"):
        raise ValueError("invalid input")

def test_raises_any_exception():
    with pytest.raises(Exception):
        raise RuntimeError("something went wrong")
```

### Fixtures

```python
import pytest

@pytest.fixture
def sample_user():
    return {"name": "Alice", "email": "alice@example.com"}

@pytest.fixture
def database_connection():
    conn = create_connection()
    yield conn
    conn.close()  # cleanup after test

def test_user_name(sample_user):
    assert sample_user["name"] == "Alice"
```

### Shared Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest

@pytest.fixture
def app():
    """Create application instance for testing."""
    from myproject import create_app
    return create_app(testing=True)

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert input * 2 == expected

@pytest.mark.parametrize("x,y,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add(x, y, expected):
    assert x + y == expected
```

### Markers

```python
import pytest

@pytest.mark.slow
def test_large_computation():
    # Takes a long time
    pass

@pytest.mark.integration
def test_external_api():
    # Requires external service
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_specific():
    pass
```

### Async Tests

```bash
uv add --group test pytest-asyncio
```

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result == expected
```

## Property-Based Testing

```bash
uv add --group test hypothesis
```

```python
from hypothesis import given, strategies as st

@given(st.integers(), st.integers())
def test_addition_commutative(x, y):
    assert x + y == y + x

@given(st.lists(st.integers()))
def test_sort_idempotent(lst):
    assert sorted(sorted(lst)) == sorted(lst)

@given(st.text(min_size=1))
def test_string_not_empty(s):
    assert len(s) > 0
```

## Mocking

```python
from unittest.mock import Mock, patch, MagicMock

def test_with_mock():
    mock_service = Mock()
    mock_service.get_data.return_value = {"key": "value"}

    result = process_data(mock_service)

    mock_service.get_data.assert_called_once()
    assert result == expected

@patch("myproject.external.api_call")
def test_with_patch(mock_api):
    mock_api.return_value = {"status": "ok"}

    result = my_function()

    assert result["status"] == "ok"
```

## CI Configuration

GitHub Actions:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --group test

      - name: Run tests
        run: uv run pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
```

## Makefile Shortcuts

```makefile
.PHONY: test test-cov test-fast

test:
	uv run pytest

test-cov:
	uv run pytest --cov=src --cov-report=html
	open htmlcov/index.html

test-fast:
	uv run pytest --no-cov -x
```
