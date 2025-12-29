# Command Line Interface Reference

Complete reference for the WhatsNext CLI (`whatsnext` / `wnxt`).

## Global Options

These options are available for all commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-V` | Show version and exit |
| `--help` | | Show help for any command |

## Configuration

Most commands accept these configuration options:

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--server` | `-s` | Server hostname | `localhost` |
| `--port` | `-p` | Server port | `8000` |
| `--config` | `-c` | Config file path | `.whatsnext` |
| `--project` | | Project name | From config |
| `--api-key` | `-k` | API key for authentication | From config |

Configuration is loaded in this order (later overrides earlier):
1. Default values
2. Config file (`.whatsnext`)
3. Environment variables
4. Command line options

---

## Commands

### init

Initialize a configuration file.

```bash
whatsnext init [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--server` | `-s` | Server hostname |
| `--port` | `-p` | Server port |
| `--project` | | Default project name |
| `--api-key` | `-k` | API key for authentication |
| `--output` | `-o` | Output file path (default: `.whatsnext`) |

**Examples:**

```bash
# Interactive setup
whatsnext init

# Non-interactive setup
whatsnext init --server api.example.com --port 443 --project myproject

# With API key
whatsnext init --server api.example.com --api-key "secret-key" -o .whatsnext
```

---

### status

Show server status and overview.

```bash
whatsnext status [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--server` | `-s` | Server hostname |
| `--port` | `-p` | Server port |
| `--config` | `-c` | Config file path |

**Example:**

```bash
whatsnext status --server localhost --port 8000
```

**Output:**

```
WhatsNext Server Status
━━━━━━━━━━━━━━━━━━━━━━━━

Server: http://localhost:8000
Status: Online

Projects: 3
  - data-pipeline (5 jobs queued)
  - ml-training (12 jobs running)
  - batch-processing (0 jobs)

Connected Clients: 4
```

---

### test-auth

Test authentication with the server.

```bash
whatsnext test-auth [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--api-key` | `-k` | API key to test |
| `--server` | `-s` | Server hostname |
| `--port` | `-p` | Server port |
| `--config` | `-c` | Config file path |

**Example:**

```bash
# Test with API key
whatsnext test-auth --api-key my-secret-key --server localhost --port 8000

# Test using config file
whatsnext test-auth
```

**Output:**

```
Testing connection to http://localhost:8000

Step 1: Testing basic connectivity...
  OK - Server is reachable
Step 2: Testing database connectivity...
  OK - Database is connected
Step 3: Checking if authentication is required...
  OK - API key is valid
  Found 3 project(s)
Step 4: Testing API access...
  OK - Full API access confirmed
  Found 2 registered client(s)

Authentication test passed!

Server: http://localhost:8000
API Key: my-s****-key
```

---

### worker

Start a worker to process jobs.

```bash
whatsnext worker [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--project` | | Project to work on (required) |
| `--entity` | `-e` | Entity/team name |
| `--name` | `-n` | Worker name |
| `--executable` | | Executable to run (default: `python`) |
| `--script` | | Script path (required) |
| `--formatter` | `-f` | Formatter type: `cli`, `slurm`, `runai` |
| `--register/--no-register` | | Register with server |
| `--server` | `-s` | Server hostname |
| `--port` | `-p` | Server port |
| `--config` | `-c` | Config file path |

**Example:**

```bash
# Basic worker
whatsnext worker --project ml-training --script train.py

# Named worker with custom executable
whatsnext worker \
    --project data-pipeline \
    --entity my-team \
    --name gpu-worker-1 \
    --executable /usr/bin/python3.11 \
    --script process.py
```

---

## Project Commands

### projects list

List all projects.

```bash
whatsnext projects list [OPTIONS]
# or
whatsnext projects ls [OPTIONS]
```

**Example:**

```bash
whatsnext projects ls
```

**Output:**

```
Projects
┏━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ ID ┃ Name             ┃ Description          ┃ Status ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 1  │ data-pipeline    │ Process data files   │ active │
│ 2  │ ml-training      │ Train ML models      │ active │
│ 3  │ batch-processing │ Batch job processor  │ paused │
└────┴──────────────────┴──────────────────────┴────────┘
```

---

### projects create

Create a new project.

```bash
whatsnext projects create NAME [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `NAME` | Project name (required) |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--description` | `-d` | Project description |

**Example:**

```bash
whatsnext projects create ml-training --description "Train machine learning models"
```

---

### projects show

Show project details.

```bash
whatsnext projects show NAME [OPTIONS]
```

**Example:**

```bash
whatsnext projects show ml-training
```

---

### projects delete

Delete a project.

```bash
whatsnext projects delete NAME [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--force` | Skip confirmation prompt |

---

## Task Commands

### tasks list

List tasks in a project.

```bash
whatsnext tasks list [OPTIONS]
# or
whatsnext tasks ls [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--project` | Project name (uses default if not specified) |

---

### tasks create

Create a new task.

```bash
whatsnext tasks create NAME [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `NAME` | Task name (required) |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--project` | | Project name |
| `--description` | `-d` | Task description |
| `--cpu` | | Required CPU cores |
| `--memory` | | Required memory (GB) |
| `--accelerators` | | Required accelerators/GPUs |

**Example:**

```bash
whatsnext tasks create gpu-training \
    --project ml-training \
    --description "Train with GPU" \
    --cpu 8 \
    --accelerators 4
```

---

### tasks show

Show task details.

```bash
whatsnext tasks show NAME [OPTIONS]
```

---

### tasks delete

Delete a task.

```bash
whatsnext tasks delete NAME [OPTIONS]
```

---

## Job Commands

### jobs list

List jobs in a project.

```bash
whatsnext jobs list [OPTIONS]
# or
whatsnext jobs ls [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--project` | | Project name |
| `--status` | | Filter by status |
| `--task` | | Filter by task |
| `--limit` | `-n` | Maximum jobs to show (default: 50) |

**Example:**

```bash
# List all jobs
whatsnext jobs ls --project ml-training

# List only running jobs
whatsnext jobs ls --project ml-training --status running

# List last 10 jobs
whatsnext jobs ls -n 10
```

---

### jobs add

Add a job to the queue.

```bash
whatsnext jobs add TASK [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `TASK` | Task name (required) |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--project` | | Project name |
| `--name` | `-n` | Job name |
| `--param` | | Parameter in `key=value` format (repeatable) |
| `--priority` | | Job priority (higher = runs first) |

**Example:**

```bash
whatsnext jobs add process-file \
    --project data-pipeline \
    --name "Process sales data" \
    --param input=sales.csv \
    --param output=results.json \
    --param format=json \
    --priority 10
```

---

### jobs show

Show job details.

```bash
whatsnext jobs show JOB_ID [OPTIONS]
```

**Example:**

```bash
whatsnext jobs show 42
```

---

### jobs cancel

Cancel a pending or running job.

```bash
whatsnext jobs cancel JOB_ID [OPTIONS]
```

---

### jobs retry

Retry a failed job.

```bash
whatsnext jobs retry JOB_ID [OPTIONS]
```

---

## Queue Commands

### queue list

Show the job queue.

```bash
whatsnext queue list [OPTIONS]
# or
whatsnext queue ls [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--project` | | Project name |
| `--limit` | `-n` | Maximum jobs to show |

**Output:**

```
Job Queue: ml-training
┏━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID  ┃ Name              ┃ Task         ┃ Priority ┃ Status   ┃
┡━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 101 │ Train model v2    │ gpu-training │ 100      │ running  │
│ 102 │ Train model v3    │ gpu-training │ 50       │ queued   │
│ 103 │ Process dataset   │ data-prep    │ 10       │ pending  │
└─────┴───────────────────┴──────────────┴──────────┴──────────┘
```

---

### queue clear

Clear the job queue.

```bash
whatsnext queue clear [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--project` | Project name |
| `--status` | Only clear jobs with this status |
| `--force` | Skip confirmation |

---

### queue stats

Show queue statistics.

```bash
whatsnext queue stats [OPTIONS]
```

**Output:**

```
Queue Statistics: ml-training

By Status:
  pending:   15 jobs
  queued:     8 jobs
  running:    4 jobs
  completed: 142 jobs
  failed:     3 jobs

By Task:
  gpu-training: 120 jobs
  data-prep:    52 jobs
```

---

## Client Commands

### clients list

List registered clients/workers.

```bash
whatsnext clients list [OPTIONS]
# or
whatsnext clients ls [OPTIONS]
```

**Output:**

```
Registered Clients
┏━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ ID ┃ Name          ┃ Entity   ┃ Last Seen          ┃ Status ┃
┡━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 1  │ gpu-worker-1  │ ml-team  │ 2024-01-15 10:30   │ active │
│ 2  │ gpu-worker-2  │ ml-team  │ 2024-01-15 10:28   │ active │
│ 3  │ cpu-worker    │ data-team│ 2024-01-14 18:00   │ idle   │
└────┴───────────────┴──────────┴────────────────────┴────────┘
```

---

### clients show

Show client details.

```bash
whatsnext clients show CLIENT_ID [OPTIONS]
```

---

### clients deactivate

Deactivate a client.

```bash
whatsnext clients deactivate CLIENT_ID [OPTIONS]
```

---

### clients delete

Delete a client registration.

```bash
whatsnext clients delete CLIENT_ID [OPTIONS]
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `WHATSNEXT_SERVER` | Default server hostname |
| `WHATSNEXT_PORT` | Default server port |
| `WHATSNEXT_API_KEY` | API key for authentication |
| `WHATSNEXT_PROJECT` | Default project name |

---

## Config File Format

The `.whatsnext` configuration file uses YAML format:

```yaml
server:
  host: localhost
  port: 8000
  api_key: your-api-key-here  # optional

project: my-default-project  # optional
```

The CLI searches for config files in this order:
1. Path specified with `--config`
2. `.whatsnext` in current directory
3. `.whatsnext` in parent directories (up to home)
4. `~/.whatsnext`
