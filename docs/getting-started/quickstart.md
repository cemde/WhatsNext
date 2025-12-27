# Quickstart

Get started with WhatsNext in a few minutes.

## Prerequisites

- Python 3.10+
- PostgreSQL 16+
- uv (recommended) or pip

## Installation

```bash
# Using uv (recommended)
uv pip install whatsnext[all]

# Or using pip
pip install whatsnext[all]
```

## Server Setup

1. Configure your database connection in `.env`:

```bash
database_hostname=localhost
database_port=5432
database_user=postgres
database_password=your_password
database_name=whatsnext
```

2. Start the server:

```bash
uvicorn whatsnext.api.server.main:app --reload
```

## Client Usage

```python
from whatsnext.api.client import Server

# Connect to the server
server = Server("http://localhost:8000")

# Create or get a project
project = server.get_project("my-project")

# Create a task
task = project.create_task("data-processing")

# Queue jobs
project.append(name="job-1", parameters={"file": "data1.csv"})
project.append(name="job-2", parameters={"file": "data2.csv"})

# Process jobs
while job := project.pop():
    print(f"Processing {job.name}")
    # Your processing logic here
    job.run()
```

## Next Steps

- Learn about [Projects and Tasks](../reference/client/project.md)
- Explore the [Server API](../reference/server/api.md)
- Understand [Job Management](../reference/client/job.md)
