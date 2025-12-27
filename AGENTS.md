# AGENTS.md

## Project Overview

WhatsNext is a job queue and task management system with a client-server architecture. It provides a FastAPI-based REST API server for managing projects, tasks, and jobs, along with a Python client library for interacting with the server.

**Key Architecture:** Server and client in one package with shared status enums. The server uses PostgreSQL for persistence, and the client communicates via HTTP.

The library is in early development, so breaking changes that are parsimonious are strongly preferred.

## Setup Commands

```bash
# Sync environment with all dependencies (creates .venv automatically)
uv sync --all-extras --all-groups

# Activate environment
source .venv/bin/activate

# Or use uv run for individual commands (no activation needed)
uv run pytest tests/
uv run uvicorn whatsnext.api.server.main:app --reload
```

## Code Style and Quality

- Line length: 144 characters
- Tool: `ruff`
- All checks must pass in CI before merge

```bash
# Format code
uv run ruff format .

# Lint and auto-fix issues
uv run ruff check . --fix
```

## Testing Instructions

- Tests use pytest markers: `server`, `client`, `integration`
- All tests must pass before PR merge
- Add/update tests for code changes
- Fix type errors and lint issues until suite is green

```bash
# Run all tests
uv run pytest -v

# Server tests only
uv run pytest -m server -v

# Client tests only
uv run pytest -m client -v

# Integration tests
uv run pytest -m integration -v
```

## Coverage

```bash
# Run with coverage report
uv run pytest --cov=whatsnext --cov-report=term-missing

# HTML coverage report
uv run pytest --cov=whatsnext --cov-report=html
```

## Typing

### Type Checker

The project uses the `ty` type checker.

```bash
# Check types across the project
uv run ty check whatsnext

# View documentation
uv run ty --help
```

Documentation: [https://docs.astral.sh/ty/](https://docs.astral.sh/ty/)

### Syntax Rules

- **Unions:** Use `A | B` notation (not `Union[A, B]`)
- **Optional:** Prefer `Optional[X]` over `X | None` for explicitness
- **Collections:** Use `List[...]`, `Dict[..., ...]`, `Sequence[...]` instead of `list`, `dict`, `sequence`

**Example:**

```python
def process_job(
    parameters: Dict[str, Any],
    priority: Optional[int] = None
) -> str | int:
    ...
```

## Dependency Management

Three types of dependencies:

- **Core** (`[project.dependencies]`): Required, installed with `pip install whatsnext`. Keep minimal!
- **Optional** (`[project.optional-dependencies]`): Published for end users. Server and client dependencies. Uses self-references (e.g., `whatsnext[all]`) to avoid duplication.
- **Dev Groups** (`[dependency-groups]`): NOT published. Only for contributors. Tools like `pytest`, `ruff`, `mkdocs`.

```bash
# Add core dependency (use sparingly!)
uv add <package-name>

# Add optional dependency for end users
uv add --optional <extra-name> <package-name>

# Add development dependency (not published - dev tools only)
uv add --group dev <package-name>

# Remove any dependency
uv remove <package-name>
```

**Important:** `uv add` automatically updates both `pyproject.toml` and `uv.lock`. Never edit lockfile manually.

**Understanding `uv sync` options:**

- `uv sync`: Installs only core dependencies
- `uv sync --extra server`: Adds server dependencies (FastAPI, SQLAlchemy, etc.)
- `uv sync --extra client`: Adds client dependencies (requests, tabulate)
- `uv sync --all-extras`: Installs ALL optional dependencies
- `uv sync --group dev`: Adds dev tools (pytest, ruff, ty)
- `uv sync --group docs`: Adds documentation tools (mkdocs)
- `uv sync --all-extras --all-groups`: Full contributor setup with everything

## Architecture

### Package Structure

```
whatsnext/
├── api/
│   ├── client/          # Python client library
│   │   ├── server.py    # Server connector (main entry point)
│   │   ├── project.py   # Project class with job queue operations
│   │   ├── job.py       # Job execution and status tracking
│   │   ├── client.py    # Resource management
│   │   └── ...
│   ├── server/          # FastAPI REST API
│   │   ├── main.py      # FastAPI app and routes
│   │   ├── models.py    # SQLAlchemy ORM models
│   │   ├── schemas.py   # Pydantic request/response schemas
│   │   ├── database.py  # PostgreSQL connection
│   │   └── routers/     # API endpoint handlers
│   └── shared/          # Shared code (status enums)
└── models.py            # Shared data models
```

### Data Flow

1. **Client** connects to server via HTTP
2. **Server** manages PostgreSQL database
3. **Projects** contain **Tasks** and **Jobs**
4. **Jobs** progress through states: PENDING → QUEUED → RUNNING → COMPLETED/FAILED

### Database Configuration

Configure via `.env` file:

```bash
database_hostname=localhost
database_port=5432
database_user=postgres
database_password=your_password
database_name=whatsnext
```

## Documentation

- Built with MkDocs Material theme + mkdocstrings
- Source files in `docs/`, config in `mkdocs.yml`

```bash
# Build with strict checking (catches broken links)
uv run mkdocs build --strict

# Serve locally at http://127.0.0.1:8000
uv run mkdocs serve
```

## Contribution Workflow

1. Create a feature branch (never commit to `main`)
2. Make changes following code style guidelines
3. Run formatters and linters: `uv run ruff format . && uv run ruff check . --fix`
4. Run tests: `uv run pytest -v`
5. Update documentation if needed
6. Open PR against `main` branch

## Project-Specific Conventions

- Minimum Python: 3.10 (Primary development: 3.12)
- Package manager: `uv` exclusively (don't use `pip install` in development)
- Commit guidelines: Reference issues, keep commits focused, run full test suite before pushing

## Common Tasks Quick Reference

```bash
# Fresh environment setup
uv sync --all-extras --all-groups

# Before committing
uv run ruff format . && uv run ruff check . --fix && uv run pytest -v && uv run ty check whatsnext

# Start development server
uv run uvicorn whatsnext.api.server.main:app --reload

# Update after pulling changes
uv sync --all-extras --all-groups

# Check specific test file
uv run pytest tests/test_client/test_project.py -v
```

## Docstrings

Write docstrings for **users**, not about your implementation process.

### Rules

- Describe what the code does and how to use it
- Explain parameters, return values, and behavior
- Never write narratives: "I did...", "First we...", "Then I..."
- Never include quality claims: "rigorously tested", "well-optimized"
- Omit implementation details users don't need

### Example

```python
def fetch_job(project_id: int) -> Optional[Job]:
    """
    Fetch the next pending job from a project's queue.

    Jobs are returned in priority order (highest first).

    Args:
        project_id: ID of the project to fetch from

    Returns:
        Next job in queue, or None if queue is empty

    Raises:
        HTTPException: If project not found
    """
```

## Early-Release Status

**This project is early-release. Clean, maintainable code is the priority - not backwards compatibility.**

- Break APIs if it improves design
- Refactor poor implementations
- Remove technical debt as soon as you identify it
- Don't preserve bad patterns for compatibility reasons
- Focus on getting it right, not keeping it the same

We have zero obligation to maintain backwards compatibility. If you find code messy, propose a fix.
