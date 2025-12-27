# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

WhatsNext is a job queue and task management system with client-server architecture in one package. FastAPI server with PostgreSQL backend, Python client library communicating via HTTP. Pre-release status—breaking changes are acceptable.

## Commands

```bash
# Setup
uv sync --all-extras --all-groups

# Development server
uv run uvicorn whatsnext.api.server.main:app --reload

# Quality checks
uv run ruff format .
uv run ruff check . --fix
uv run ty check whatsnext
uv run pytest -v

# Single test file
uv run pytest tests/test_client/test_project.py -v

# Test by marker
uv run pytest -m server -v
uv run pytest -m client -v
uv run pytest -m integration -v

# Documentation
uv run mkdocs serve
uv run mkdocs build --strict
```

## Architecture

```
whatsnext/api/
├── client/     # Python client: Server (entry point) → Project → Job
├── server/     # FastAPI: main.py, models.py (SQLAlchemy), schemas.py (Pydantic), routers/
└── shared/     # Status enums (JobStatus, ProjectStatus)
```

**Data flow:** Client HTTP → Server REST API → PostgreSQL

**Job states:** PENDING → QUEUED → RUNNING → COMPLETED/FAILED

**Database config:** `.env` file with `database_hostname`, `database_port`, `database_user`, `database_password`, `database_name`

## Code Style

- Line length: 144 chars
- Type hints: `Optional[X]` for optional, `A | B` for unions, `List[...]`/`Dict[...]` for collections
- Type checker: `ty` (not mypy)
- Package manager: `uv` exclusively

## See Also

[AGENTS.md](AGENTS.md) contains detailed dependency management, docstring conventions, and contribution workflow.
