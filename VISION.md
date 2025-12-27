# Vision: WhatsNext

WhatsNext is a job queue and task management system designed for distributed computing environments where worker nodes may have limited capabilities.

## Core Principles

### 1. Stateless Client

The client **never** stores queue state locally. All job and queue data lives on the server with PostgreSQL backing. This design enables:

- Clients on restricted servers (no database, limited storage)
- Multiple clients consuming from the same queue
- Fault tolerance—client crashes don't lose queue state
- Simple client deployment (just Python + requests)

### 2. Runtime-Agnostic Job Definitions

A job is defined by **what** it does, not **how** it runs. Job semantics are:

- `name`: Human-readable identifier
- `task`: Which task template this job belongs to
- `parameters`: A dictionary of input values
- `priority`: Execution order preference
- `depends`: Other jobs that must complete first

The **formatter** (owned by the client) converts job parameters into executable commands. The same job can run via:

- **CLI**: Direct command execution
- **SLURM**: sbatch script generation
- **RUNAI**: Kubernetes job submission
- **Python**: In-process function call

This separation means job definitions are portable across execution environments.

### 3. Pull-Based Worker Loop

A client can start and continuously pull jobs from the queue:

```python
client = Client(server, formatter=SlurmFormatter())
client.work(project="my-project")  # Loops until queue empty or interrupted
```

The worker:
1. Fetches highest-priority pending job
2. Formats it for the local environment
3. Executes and reports status back
4. Repeats until no jobs remain

### 4. Project-Based Organization

Jobs are organized into **projects**, each containing:

- Multiple **tasks** (templates/definitions)
- A queue of **jobs** (instances of tasks with specific parameters)
- Status tracking (ACTIVE/ARCHIVED)

## Feature Goals

| Feature | Description |
|---------|-------------|
| **Stateless client** | No local database, all state on server |
| **Formatter system** | Convert job params → SLURM/CLI/RUNAI/Python commands |
| **Worker loop** | `client.work()` continuously pulls and executes jobs |
| **Priority queuing** | Higher priority jobs execute first |
| **Job dependencies** | Jobs can depend on other jobs completing |
| **Resource tracking** | CPU/GPU allocation per job |
| **Artifact management** | Track inputs/outputs of jobs |
| **Project organization** | Group related tasks and jobs |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SERVER                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   FastAPI   │───▶│  PostgreSQL │    │  Job Queue Logic    │  │
│  │   REST API  │    │  Database   │    │  (priority, deps)   │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           ▲                                      │
           │ HTTP (fetch job, report status)      │
           │                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT (Stateless)                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Worker    │───▶│  Formatter  │───▶│  Execute Command    │  │
│  │   Loop      │    │  (SLURM/CLI)│    │  (os.system/subprocess)│
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Non-Goals

- **Client-side caching**: The client does not cache jobs or queue state
- **Client-side database**: No SQLite, no local persistence
- **Execution environment in job definition**: Jobs don't know about SLURM/CLI
