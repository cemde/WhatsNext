# Quickstart Guide

This guide will walk you through setting up WhatsNext from scratch. By the end, you'll have a working job queue system.

## What You'll Build

We'll create a simple system that:

1. Runs a WhatsNext server
2. Submits jobs to process "data files"
3. Has a worker that runs those jobs

## Architecture Overview

WhatsNext uses a **client-server architecture**. This quickstart covers both:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         YOUR SETUP                                   │
│                                                                     │
│  ┌─────────────────────────┐     ┌─────────────────────────────────┐│
│  │     SERVER SIDE         │     │         CLIENT SIDE              ││
│  │    (Steps 1-4)          │     │        (Steps 5-7)               ││
│  │                         │     │                                   ││
│  │  • PostgreSQL database  │◄───►│  • Submit jobs (Python/CLI)      ││
│  │  • WhatsNext API        │HTTP │  • Run workers                    ││
│  │                         │     │                                   ││
│  └─────────────────────────┘     └─────────────────────────────────┘│
│                                                                     │
│  Run on: Your server,           Run on: Your laptop, GPU nodes,     │
│          Docker container,               HPC clusters, anywhere      │
│          cloud VM                        with network access         │
└─────────────────────────────────────────────────────────────────────┘
```

!!! tip "Already have a server?"
    If someone else is running the server, skip to [Client Setup](install-client.md) to learn how to submit jobs.

## Prerequisites

Before starting, make sure you have:

- **Python 3.10+** installed
- **PostgreSQL** running (we'll show you how to set it up) - **SERVER SIDE ONLY**
- **10 minutes** of your time

---

# Part 1: Server Setup

These steps set up the WhatsNext server. Do this once on the machine that will host the API.

!!! note "Skip if using existing server"
    If a server is already running, skip to [Part 2: Client Setup](#part-2-client-setup).

## Step 1: Install WhatsNext

Open your terminal and run:

```bash
# Create a new project directory
mkdir my-job-queue
cd my-job-queue

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install WhatsNext with all dependencies
pip install whatsnext[all]
```

!!! tip "Using uv?"
    If you prefer uv (faster package manager):
    ```bash
    uv add whatsnext[all]
    ```

## Step 2: Set Up PostgreSQL

WhatsNext needs a PostgreSQL database to store jobs. Here are your options:

=== "Docker (Easiest)"

    ```bash
    # Start PostgreSQL in Docker
    docker run -d \
      --name whatsnext-db \
      -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=postgres \
      -e POSTGRES_DB=whatsnext \
      -p 5432:5432 \
      postgres:16
    ```

=== "Local PostgreSQL"

    If PostgreSQL is already installed:
    ```bash
    # Create the database
    createdb whatsnext
    ```

=== "macOS (Homebrew)"

    ```bash
    # Install PostgreSQL
    brew install postgresql@16
    brew services start postgresql@16

    # Create the database
    createdb whatsnext
    ```

## Step 3: Configure the Server

Create a `.env` file in your project directory:

```bash title=".env"
# Database connection
database_hostname=localhost
database_port=5432
database_user=postgres
database_password=postgres
database_name=whatsnext
```

!!! warning "Security Note"
    In production, use strong passwords and consider enabling API authentication. See the [Configuration Guide](configuration.md) for details.

## Step 4: Start the Server

Run the WhatsNext server:

```bash
uvicorn whatsnext.api.server.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

!!! success "Server Running!"
    Open [http://localhost:8000/docs](http://localhost:8000/docs) to see the API documentation.

---

# Part 2: Client Setup

These steps are done on client machines (your laptop, worker nodes, etc.). The server must be running first.

## Step 5: Create Your First Job Script

Create a simple Python script that will be run by jobs:

```python title="process_data.py"
#!/usr/bin/env python3
"""A simple script that processes data files."""

import argparse
import time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input file name")
    parser.add_argument("--output", required=True, help="Output file name")
    args = parser.parse_args()

    print(f"Processing {args.input}...")
    time.sleep(2)  # Simulate work
    print(f"Saved results to {args.output}")
    print("Done!")

if __name__ == "__main__":
    main()
```

## Step 6: Submit Jobs

Create a script to add jobs to the queue:

```python title="submit_jobs.py"
#!/usr/bin/env python3
"""Submit jobs to the WhatsNext queue."""

from whatsnext.api.client import Server, Job

def main():
    # Connect to the server
    print("Connecting to server...")
    server = Server("localhost", 8000)

    # Create or get a project
    project = server.get_project("data-processing")
    if project is None:
        print("Creating new project...")
        project = server.append_project(
            name="data-processing",
            description="Process data files"
        )
    else:
        print(f"Using existing project: {project.name}")

    # Create a task (only needed once)
    project.create_task("process-file")

    # Add some jobs to the queue
    files = ["data1.csv", "data2.csv", "data3.csv"]

    for filename in files:
        job = Job(
            name=f"process-{filename}",
            task="process-file",
            parameters={
                "input": filename,
                "output": f"output_{filename}"
            }
        )
        project.append_queue(job)
        print(f"  Queued: {job.name}")

    print(f"\nQueued {len(files)} jobs!")
    print("Run 'python run_worker.py' to process them.")

if __name__ == "__main__":
    main()
```

Run it:

```bash
python submit_jobs.py
```

Output:

```
Connecting to server...
Creating new project...
  Queued: process-data1.csv
  Queued: process-data2.csv
  Queued: process-data3.csv

Queued 3 jobs!
Run 'python run_worker.py' to process them.
```

## Step 7: Run a Worker

Create a worker script to process jobs:

```python title="run_worker.py"
#!/usr/bin/env python3
"""Run a worker to process jobs from the queue."""

from whatsnext.api.client import Server, Client, CLIFormatter

def main():
    # Connect to the server
    print("Connecting to server...")
    server = Server("localhost", 8000)

    # Get the project
    project = server.get_project("data-processing")
    if project is None:
        print("Error: Project 'data-processing' not found!")
        print("Run 'python submit_jobs.py' first.")
        return

    # Create a formatter that runs our script
    formatter = CLIFormatter(
        executable="python",
        script="process_data.py"
    )

    # Create a worker client
    client = Client(
        entity="my-team",
        name="worker-1",
        description="Local worker",
        project=project,
        formatter=formatter,
        register_with_server=False  # Skip server registration for local testing
    )

    # Process all jobs in the queue
    print(f"Starting worker for project: {project.name}")
    print("Press Ctrl+C to stop\n")

    jobs_done = client.work()
    print(f"\nCompleted {jobs_done} jobs!")

if __name__ == "__main__":
    main()
```

Run it:

```bash
python run_worker.py
```

Output:

```
Connecting to server...
Starting worker for project: data-processing
Press Ctrl+C to stop

Fetched job 1: process-data1.csv
Processing data1.csv...
Saved results to output_data1.csv
Done!
Job 1 completed successfully

Fetched job 2: process-data2.csv
Processing data2.csv...
Saved results to output_data2.csv
Done!
Job 2 completed successfully

Fetched job 3: process-data3.csv
Processing data3.csv...
Saved results to output_data3.csv
Done!
Job 3 completed successfully

Queue empty, worker exiting

Completed 3 jobs!
```

## What Just Happened?

1. **submit_jobs.py** connected to the server and added 3 jobs to the queue
2. Each job has a name, task type, and parameters
3. **run_worker.py** connected to the same project
4. The worker fetched each job, converted parameters to command-line arguments, and ran `process_data.py`

## Project Structure

Your project should now look like this:

```
my-job-queue/
├── .env                 # Database configuration
├── .venv/               # Virtual environment
├── process_data.py      # Your job script
├── submit_jobs.py       # Add jobs to queue
└── run_worker.py        # Process jobs from queue
```

## Alternative: Using the CLI

If you prefer working from the command line, you can do everything above using the WhatsNext CLI:

```bash
# Initialize a config file
whatsnext init --server localhost --port 8000 --project data-processing

# Create the project
whatsnext projects create data-processing --description "Process data files"

# Create a task
whatsnext tasks create process-file --project data-processing

# Add jobs to the queue
whatsnext jobs add process-file --project data-processing \
    --name "process-data1.csv" \
    --param input=data1.csv \
    --param output=output_data1.csv

whatsnext jobs add process-file --project data-processing \
    --name "process-data2.csv" \
    --param input=data2.csv \
    --param output=output_data2.csv

# Check the queue
whatsnext queue ls

# Start a worker
whatsnext worker --project data-processing
```

See the [CLI documentation](cli.md) for more details.

## Next Steps

Now that you have the basics working:

- **[Add job priorities](../reference/client/job.md)** - Run important jobs first
- **[Use job dependencies](../reference/index.md#job-dependencies)** - Job B waits for Job A
- **[Run on SLURM](formatters.md#slurmformatter)** - Submit to HPC clusters
- **[Add authentication](configuration.md#authentication)** - Secure your API
- **[Deploy to production](deployment.md)** - Use systemd and nginx

## Troubleshooting

### "Connection refused" error

Make sure the server is running:
```bash
uvicorn whatsnext.api.server.main:app --reload
```

### "Database connection failed"

Check your `.env` file and make sure PostgreSQL is running:
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432
```

### Jobs not running

Check that:

1. Jobs were added to the queue: Check [http://localhost:8000/jobs/](http://localhost:8000/jobs/)
2. Your worker script path is correct
3. The task name in the job matches what you created

### Getting more help

- Check the [API docs](http://localhost:8000/docs) for available endpoints
- See the [Reference documentation](../reference/index.md) for detailed API info
- [Open an issue](https://github.com/cemde/WhatsNext/issues) on GitHub
