# Job

The `Job` class represents a queued job and provides methods for execution and status management.

## Usage

```python
from whatsnext.api.client import Server

server = Server("http://localhost:8000")
project = server.get_project("my-project")

# Get next job
job = project.pop()

if job:
    print(f"Processing: {job.name}")
    print(f"Parameters: {job.parameters}")
    print(f"Status: {job.status}")

    # Execute the job
    job.run()
```

## Job Status

Jobs progress through the following states:

- `PENDING` - Job created but not queued
- `QUEUED` - Job in queue waiting to be processed
- `RUNNING` - Job currently being executed
- `COMPLETED` - Job finished successfully
- `FAILED` - Job execution failed

## API Reference

::: whatsnext.api.client.job.Job
