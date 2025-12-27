# WhatsNext

A job queue and task management system with client-server architecture.

## Overview

WhatsNext provides a distributed job queue system built on:

- **FastAPI Server**: REST API for managing projects, tasks, and jobs
- **Python Client**: Library for interacting with the server
- **PostgreSQL Backend**: Persistent storage for job queue state

## Features

- Project-based organization of tasks and jobs
- Priority-based job queue with status tracking
- Job dependencies support
- Resource allocation tracking (CPU/accelerators)

## Installation

```bash
# Install with uv (recommended)
uv pip install whatsnext

# Install server dependencies
uv pip install whatsnext[server]

# Install client dependencies
uv pip install whatsnext[client]

# Install everything
uv pip install whatsnext[all]
```

## Quick Example

```python
from whatsnext.api.client import Server

# Connect to the server
server = Server("http://localhost:8000")

# Get or create a project
project = server.get_project("my-project")

# Queue a job
job = project.append(name="process-data", parameters={"input": "data.csv"})

# Fetch and run jobs
while job := project.pop():
    job.run()
```

## Development

```bash
# Clone and install with dev dependencies
git clone https://github.com/cemde/WhatsNext.git
cd WhatsNext
uv sync --group dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run ty check whatsnext
```
