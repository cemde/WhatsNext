<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo-light.svg">
    <img src="assets/logo-light.svg" alt="WhatsNext logo" width="280" />
  </picture>
</p>

> **Warning**
> This is a private project in early development. It has not been security audited and is strongly advised against running on public-facing servers. Use only in trusted, internal environments. You may also experience several bugs at this time due to the early development stage of this project.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/whatsnext.svg)](https://badge.fury.io/py/whatsnext)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://whatsnext.readthedocs.io/)
[![Tests](https://github.com/cemde/WhatsNext/actions/workflows/test.yml/badge.svg)](https://github.com/cemde/WhatsNext/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![CLI](https://img.shields.io/badge/CLI-supported-orange.svg)](https://cemde.github.io/WhatsNext/getting-started/cli/)

A simple, powerful job queue for Python applications.

WhatsNext helps you manage and execute background jobs across multiple machines. Add jobs to a queue, and workers pick them up and run them.

## Features

- **Simple**: Just a few lines of code to get started
- **Reliable**: Jobs are stored in PostgreSQL, so nothing gets lost
- **Scalable**: Run multiple workers on different machines
- **Flexible**: Works with any Python code, SLURM clusters, or Kubernetes
- **Lightweight Client**: No database, no caching, no background processes - the client is pure HTTP and runs in restricted environments

## Quick Example

```python
from whatsnext.api.client import Server, Job, Client, CLIFormatter

# Connect and get a project
server = Server("localhost", 8000)
project = server.get_project("my-experiments")

# Add a job to the queue
project.append_queue(Job(
    name="experiment-1",
    task="train-model",
    parameters={"learning_rate": 0.01, "epochs": 100}
))

# Create a worker and process jobs
formatter = CLIFormatter(executable="python", script="train.py")
client = Client(
    entity="ml-team",
    name="gpu-worker-1",
    project=project,
    formatter=formatter
)
client.work()
```

## Installation

```bash
# Install with uv (recommended)
uv add whatsnext[all]

# Or with pip
pip install whatsnext[all]
```

## Requirements

- Python 3.10+
- PostgreSQL 14+

## Running the Server

1. Create a `.env` file with your database configuration:

```bash
database_hostname=localhost
database_port=5432
database_user=postgres
database_password=postgres
database_name=whatsnext
```

2. Start the server:

```bash
uvicorn whatsnext.api.server.main:app --reload
```

3. Visit http://localhost:8000/docs for interactive API documentation.

## Documentation

Full documentation is available at the project docs site. Build locally with:

```bash
uv run mkdocs serve
```

## Development

```bash
# Install dependencies
uv sync --all-extras --all-groups

# Run quality checks
uv run ruff format .
uv run ruff check . --fix
uv run ty check whatsnext
uv run pytest -v
```

## License

AGPL-3.0 - See [LICENSE](LICENSE) for details.
