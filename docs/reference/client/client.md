# Client

The `Client` class represents a worker that fetches and executes jobs from a project's queue.

## Usage

```python
from whatsnext.api.client import Server, Client, CLIFormatter

# Connect to server and get project
server = Server("http://localhost:8000")
project = server.get_project("my-project")

# Create a formatter for job execution
formatter = CLIFormatter(executable="python", script="train.py")

# Create a worker client
client = Client(
    entity="ml-team",
    name="gpu-worker-1",
    description="Training server with 4 GPUs",
    project=project,
    formatter=formatter,
    available_cpu=16,
    available_accelerators=4,
)

# Start processing jobs
client.work()
```

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `entity` | str | *required* | Organization or team name |
| `name` | str | *required* | Unique name for this worker |
| `description` | str | *required* | Human-readable description |
| `project` | Project | *required* | Project to fetch jobs from |
| `formatter` | Formatter | *required* | Formatter for command execution |
| `available_cpu` | int | `1` | Number of CPUs available |
| `available_accelerators` | int | `0` | Number of GPUs/accelerators available |
| `register_with_server` | bool | `True` | Register client with the server |

## Methods

### work()

Continuously fetch and execute jobs until the queue is empty.

```python
jobs_completed = client.work(
    poll_interval=5.0,      # Seconds between polls when run_forever=True
    run_forever=False,      # If True, wait for new jobs instead of exiting
    use_resource_filter=True  # Only fetch jobs matching client resources
)
print(f"Completed {jobs_completed} jobs")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resource` | Resource | `None` | Resource to use (auto-allocated if None) |
| `poll_interval` | float | `5.0` | Seconds to wait between queue checks |
| `run_forever` | bool | `False` | Keep running even when queue is empty |
| `use_resource_filter` | bool | `True` | Filter jobs by resource requirements |

**Returns:** Number of jobs executed.

### stop()

Request the worker to stop gracefully after the current job completes.

```python
# In a signal handler or from another thread
client.stop()
```

## Resource Matching

When `use_resource_filter=True`, the client only fetches jobs whose task requirements match the client's available resources:

```python
# This client has 4 GPUs
client = Client(
    ...,
    available_cpu=16,
    available_accelerators=4,
)

# Only fetches jobs where:
# - task.required_cpu <= 16
# - task.required_accelerators <= 4
client.work(use_resource_filter=True)
```

## Graceful Shutdown

The client handles `SIGINT` (Ctrl+C) and `SIGTERM` signals gracefully:

1. Finishes the current job
2. Deactivates on the server
3. Returns the number of completed jobs

```python
# Worker script
try:
    jobs = client.work(run_forever=True)
except KeyboardInterrupt:
    print("Interrupted")
finally:
    print(f"Completed {jobs} jobs")
```

## Server Registration

When `register_with_server=True`, the client:

1. Registers with the server on creation
2. Reports its available resources
3. Deactivates when `work()` completes or `stop()` is called

This allows the server to track active workers and their capabilities.

## Example: Long-Running Worker

```python
import logging

logging.basicConfig(level=logging.INFO)

from whatsnext.api.client import Server, Client, CLIFormatter

# Setup
server = Server("http://localhost:8000")
project = server.get_project("ml-training")
formatter = CLIFormatter(executable="python", script="train.py")

# Create worker
client = Client(
    entity="research",
    name="worker-01",
    description="GPU training node",
    project=project,
    formatter=formatter,
    available_cpu=32,
    available_accelerators=8,
)

# Run until interrupted
print("Starting worker (Ctrl+C to stop)...")
jobs = client.work(run_forever=True, poll_interval=10.0)
print(f"Worker stopped after {jobs} jobs")
```

## API Reference

::: whatsnext.api.client.client.Client
