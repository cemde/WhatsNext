# Project

The `Project` class represents a project in WhatsNext and provides methods for managing jobs.

## Usage

```python
from whatsnext.api.client import Server

server = Server("http://localhost:8000")
project = server.get_project("my-project")

# Queue jobs
project.append(name="job-1", parameters={"key": "value"})

# Get next job from queue
job = project.pop()

# List all jobs
jobs = project.jobs
```

## API Reference

::: whatsnext.api.client.project.Project
