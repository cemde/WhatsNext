# Command Line Interface

WhatsNext includes a powerful command-line interface (CLI) for managing jobs, projects, and workers without writing Python code. It's perfect for quick tasks, scripting, and CI/CD pipelines.

## Installation

The CLI is included with the full WhatsNext installation:

```bash
# Install with CLI support
pip install whatsnext[cli]

# Or install everything
pip install whatsnext[all]
```

## Quick Start

```bash
# Initialize a config file in your project
whatsnext init --server localhost --port 8000 --project my-project

# Check system status
whatsnext status

# List jobs in the queue
whatsnext queue ls

# Start a worker
whatsnext worker
```

## Command Aliases

The CLI is available under two names:

| Command | Description |
|---------|-------------|
| `whatsnext` | Full name (intuitive) |
| `wnxt` | Short alias (quick typing) |

Both commands are identical:

```bash
# These are equivalent
whatsnext projects ls
wnxt projects ls
```

## Configuration File

The CLI uses a `.whatsnext` configuration file to store default settings. This avoids repeating server addresses and project names.

### Creating a Config File

```bash
# Interactive setup
whatsnext init

# Non-interactive with options
whatsnext init --server api.example.com --port 8000 --project ml-training
```

### Config File Location

The CLI searches for `.whatsnext` in this order:

1. **Current directory** - `.whatsnext` in your working directory
2. **Git repository root** - `.whatsnext` at the root of your git repo
3. **Home directory** - `~/.whatsnext` for user-wide defaults

### Config File Format

```yaml title=".whatsnext"
# Server connection
server:
  host: localhost
  port: 8000

# Default project for commands
project: my-ml-experiments

# Optional: Worker settings (for 'whatsnext worker' command)
client:
  entity: ml-team
  name: gpu-worker-1
  cpus: 8
  accelerators: 2

# Optional: Formatter settings
formatter:
  type: cli  # or: slurm, runai
  slurm:
    partition: gpu
    time: "4:00:00"
  runai:
    project: my-runai-project
    image: python:3.11
```

## Commands Overview

```
whatsnext
├── init          # Create .whatsnext config file
├── status        # Show system status dashboard
├── worker        # Start a job worker
│
├── projects      # Manage projects
│   ├── ls        # List projects
│   ├── show      # Show project details
│   ├── create    # Create a new project
│   ├── delete    # Delete a project
│   └── archive   # Archive a project
│
├── tasks         # Manage tasks
│   ├── ls        # List tasks in a project
│   ├── show      # Show task details
│   ├── create    # Create a new task
│   └── delete    # Delete a task
│
├── jobs          # Manage individual jobs
│   ├── show      # Show job details
│   ├── add       # Add a job to the queue
│   ├── add-batch # Add jobs from YAML/JSON file
│   ├── delete    # Delete a job
│   ├── retry     # Retry a failed job
│   └── deps      # Show job dependencies
│
├── queue         # View and manage the queue
│   ├── ls        # List jobs in queue
│   ├── stats     # Show queue statistics
│   └── clear     # Clear pending jobs
│
└── clients       # View connected workers
    ├── ls        # List workers
    ├── show      # Show worker details
    ├── deactivate # Mark worker inactive
    └── delete    # Remove worker registration
```

## Command Reference

### Global Options

All commands support these options:

| Option | Short | Description |
|--------|-------|-------------|
| `--server` | `-s` | Server hostname |
| `--port` | `-p` | Server port |
| `--config` | `-c` | Config file path |
| `--help` | | Show help |

### `whatsnext init`

Create a `.whatsnext` configuration file.

```bash
# Interactive mode
whatsnext init

# With options
whatsnext init --server api.example.com --port 8000 --project my-project

# Overwrite existing
whatsnext init --force
```

### `whatsnext status`

Show a system status dashboard with server, project, queue, and worker information.

```bash
# Basic status
whatsnext status

# For a specific project
whatsnext status --project ml-training

# JSON output for scripting
whatsnext status --json
```

Example output:

```
╭─────────────────────────────────╮
│ WhatsNext Status Dashboard      │
╰─────────────────────────────────╯

Server: connected
  URL: http://localhost:8000

Project: ml-training ACTIVE

Queue Summary: 42 total jobs
  RUNNING: 3 | PENDING: 25 | COMPLETED: 12 | FAILED: 2

Workers: 2 active / 5 registered
```

### `whatsnext projects`

Manage projects.

```bash
# List all active projects
whatsnext projects ls

# Show all projects including archived
whatsnext projects ls --status all

# Show project details
whatsnext projects show ml-training

# Create a new project
whatsnext projects create new-project --description "My new project"

# Archive a project
whatsnext projects archive old-project

# Delete a project (with confirmation)
whatsnext projects delete old-project
whatsnext projects delete old-project --force  # Skip confirmation
```

### `whatsnext tasks`

Manage task types within a project.

```bash
# List tasks
whatsnext tasks ls --project ml-training

# Create a task
whatsnext tasks create train-model --project ml-training --cpu 4 --accelerators 1

# Show task details
whatsnext tasks show train-model --project ml-training

# Delete a task
whatsnext tasks delete 123  # by ID
```

### `whatsnext queue`

View and manage the job queue.

```bash
# List jobs in queue
whatsnext queue ls

# Filter by status
whatsnext queue ls --status PENDING
whatsnext queue ls --status RUNNING
whatsnext queue ls --status FAILED

# Filter by task
whatsnext queue ls --task train-model

# Show more jobs
whatsnext queue ls --limit 100

# Queue statistics
whatsnext queue stats

# Clear all pending jobs (with confirmation)
whatsnext queue clear
whatsnext queue clear --force
```

### `whatsnext jobs`

Manage individual jobs.

```bash
# Show job details
whatsnext jobs show 123

# Add a single job
whatsnext jobs add train-model \
  --project ml-training \
  --name "experiment-v1" \
  --param lr=0.001 \
  --param epochs=100 \
  --priority 5

# Add jobs with dependencies
whatsnext jobs add evaluate-model \
  --project ml-training \
  --depends 123 \
  --depends 124

# Add multiple jobs from file
whatsnext jobs add-batch jobs.yaml --project ml-training

# Retry a failed job
whatsnext jobs retry 123

# Delete a job
whatsnext jobs delete 123

# Show job dependencies
whatsnext jobs deps 123
```

#### Batch Job File Format

```yaml title="jobs.yaml"
jobs:
  - name: train-v1
    task: train-model
    parameters:
      lr: 0.01
      epochs: 100
    priority: 5

  - name: train-v2
    task: train-model
    parameters:
      lr: 0.001
      epochs: 200
    priority: 3

  - name: evaluate
    task: evaluate-model
    depends:
      train-v1: "0"
      train-v2: "1"
```

### `whatsnext worker`

Start a worker to process jobs.

```bash
# Start with defaults from config
whatsnext worker

# Specify project and resources
whatsnext worker \
  --project ml-training \
  --cpus 8 \
  --accelerators 2

# Use a specific formatter
whatsnext worker --formatter slurm
whatsnext worker --formatter runai

# Process one job and exit
whatsnext worker --once

# Custom poll interval (seconds)
whatsnext worker --poll-interval 60
```

### `whatsnext clients`

View connected workers/clients.

```bash
# List active workers
whatsnext clients ls

# List all workers (including inactive)
whatsnext clients ls --all

# Show worker details
whatsnext clients show abc123

# Mark a worker as inactive
whatsnext clients deactivate abc123

# Remove worker registration
whatsnext clients delete abc123
```

## Scripting and Automation

### JSON Output

Most commands support `--json` for machine-readable output:

```bash
# Get queue status as JSON
whatsnext queue ls --json | jq '.[] | select(.status == "FAILED")'

# Count pending jobs
whatsnext queue ls --status PENDING --json | jq 'length'

# Get project info
whatsnext projects show ml-training --json
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (check stderr) |
| `2` | Invalid arguments |

### CI/CD Integration

Example GitHub Actions workflow:

```yaml title=".github/workflows/submit-jobs.yml"
name: Submit Training Jobs

on:
  push:
    branches: [main]

jobs:
  submit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install WhatsNext CLI
        run: pip install whatsnext[cli]

      - name: Submit jobs
        env:
          WHATSNEXT_SERVER: ${{ secrets.WHATSNEXT_SERVER }}
        run: |
          whatsnext jobs add-batch training-jobs.yaml \
            --server $WHATSNEXT_SERVER \
            --project ml-training
```

## Shell Completion

Enable tab completion for your shell:

```bash
# Bash
whatsnext --install-completion bash

# Zsh
whatsnext --install-completion zsh

# Fish
whatsnext --install-completion fish
```

After installation, restart your shell or source your profile.

## Examples

### Monitor Job Progress

```bash
#!/bin/bash
# watch-queue.sh - Monitor queue until empty

while true; do
    clear
    whatsnext status --project ml-training
    echo ""
    whatsnext queue ls --project ml-training --limit 10

    # Check if queue is empty
    pending=$(whatsnext queue ls --status PENDING --json | jq 'length')
    running=$(whatsnext queue ls --status RUNNING --json | jq 'length')

    if [ "$pending" -eq 0 ] && [ "$running" -eq 0 ]; then
        echo "All jobs complete!"
        break
    fi

    sleep 30
done
```

### Hyperparameter Sweep

```bash
#!/bin/bash
# sweep.sh - Submit hyperparameter sweep

PROJECT="ml-training"
TASK="train-model"

for lr in 0.1 0.01 0.001 0.0001; do
    for batch_size in 32 64 128; do
        whatsnext jobs add $TASK \
            --project $PROJECT \
            --name "sweep-lr${lr}-bs${batch_size}" \
            --param learning_rate=$lr \
            --param batch_size=$batch_size
    done
done

echo "Submitted $(whatsnext queue ls --status PENDING --json | jq 'length') jobs"
```

### Failed Job Report

```bash
#!/bin/bash
# report-failures.sh - Generate failure report

echo "# Failed Jobs Report"
echo "Generated: $(date)"
echo ""

whatsnext queue ls --status FAILED --json | jq -r '.[] | "## Job \(.id): \(.name)\n- Task: \(.task_id)\n- Created: \(.created_at)\n"'
```
