# WhatsNext

**A simple, powerful job queue for Python applications.**

WhatsNext helps you manage and execute background jobs across multiple machines. Think of it as a to-do list for your computer programs - you add jobs to a queue, and workers pick them up and run them.

## Why WhatsNext?

- **Simple**: Just a few lines of code to get started, or use the CLI
- **Reliable**: Jobs are stored in PostgreSQL, so nothing gets lost
- **Scalable**: Run multiple workers on different machines
- **Flexible**: Works with any Python code, SLURM clusters, or Kubernetes
- **CLI Included**: Manage jobs from your terminal with `whatsnext` or `wnxt`

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Your Code  │────>│   Server     │────>│   Worker    │
│  (add jobs) │     │  (PostgreSQL)│     │ (runs jobs) │
└─────────────┘     └──────────────┘     └─────────────┘
```

1. **You add jobs** to a project's queue
2. **The server** stores them in the database
3. **Workers** fetch jobs and execute them

## Quick Example

Here's all you need to queue and run jobs:

```python
from whatsnext.api.client import Server, Job, Client, CLIFormatter

# 1. Connect to the server
server = Server("localhost", 8000)

# 2. Get (or create) a project
project = server.get_project("my-experiments")
if project is None:
    project = server.append_project("my-experiments", "ML training jobs")

# 3. Create a task type
project.create_task("train-model")

# 4. Add jobs to the queue
project.append_queue(Job(
    name="experiment-1",
    task="train-model",
    parameters={"learning_rate": 0.01, "epochs": 100}
))

# 5. Create a worker to run jobs
formatter = CLIFormatter(executable="python", script="train.py")
client = Client(
    entity="ml-team",
    name="gpu-worker-1",
    description="GPU training worker",
    project=project,
    formatter=formatter
)

# 6. Start processing jobs
client.work()  # Runs until queue is empty
```

## Installation

=== "With uv (Recommended)"

    ```bash
    # Install everything (client + server + CLI)
    uv pip install whatsnext[all]
    ```

=== "With pip"

    ```bash
    # Install everything (client + server + CLI)
    pip install whatsnext[all]
    ```

=== "CLI Only"

    ```bash
    # If you only need the command-line interface
    pip install whatsnext[cli]
    ```

=== "Client Only"

    ```bash
    # If you only need to submit/manage jobs from Python
    pip install whatsnext[client]
    ```

=== "Server Only"

    ```bash
    # If you only need to run the API server
    pip install whatsnext[server]
    ```

## What's Next?

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Quickstart Guide](getting-started/quickstart.md)**

    ---

    Get up and running in 5 minutes with a complete working example

-   :material-console: **[Command Line Interface](getting-started/cli.md)**

    ---

    Manage jobs, projects, and workers from your terminal

-   :material-cog: **[Configuration](getting-started/configuration.md)**

    ---

    Learn how to configure the server, authentication, and security

-   :material-format-list-bulleted: **[Formatters](getting-started/formatters.md)**

    ---

    Run jobs locally, on SLURM clusters, or with RUNAI/Kubernetes

-   :material-server: **[Deployment](getting-started/deployment.md)**

    ---

    Deploy WhatsNext for production use with systemd and nginx

</div>

## Key Concepts

| Concept | What It Is | Example |
|---------|------------|---------|
| **Project** | A container for related work | "image-processing", "ml-training" |
| **Task** | A type of job that can be run | "resize-image", "train-model" |
| **Job** | A specific instance of a task | "resize image-001.jpg to 800x600" |
| **Client** | A worker that executes jobs | A GPU server running your training code |
| **Formatter** | Converts job parameters to commands | CLIFormatter, SlurmFormatter, RUNAIFormatter |

## Requirements

- **Python**: 3.10 or higher
- **PostgreSQL**: 14 or higher (for the server)
- **Operating System**: Linux, macOS, or Windows

## Getting Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/cemde/WhatsNext/issues)
- **Source Code**: [View on GitHub](https://github.com/cemde/WhatsNext)
