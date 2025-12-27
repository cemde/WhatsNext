# Formatters Guide

Formatters are the bridge between WhatsNext and your execution environment. They convert job parameters into executable commands.

## What is a Formatter?

When you create a job with parameters like `{"learning_rate": 0.01, "epochs": 100}`, the formatter converts these into a command that can be run:

```
Job Parameters  ──►  Formatter  ──►  Command
{"lr": 0.01}    ──►  CLI        ──►  python train.py --lr 0.01
```

WhatsNext includes three formatters:

| Formatter | Use Case | Runs On |
|-----------|----------|---------|
| `CLIFormatter` | Local scripts | Your machine |
| `SlurmFormatter` | HPC clusters | SLURM scheduler |
| `RUNAIFormatter` | Kubernetes | RUNAI/K8s |

## CLIFormatter

The most common formatter - runs Python scripts or any command-line program.

### Basic Usage

```python
from whatsnext.api.client import CLIFormatter

# Simple: just specify the executable
formatter = CLIFormatter(executable="python")

# With a script
formatter = CLIFormatter(
    executable="python",
    script="train.py"
)

# With a working directory
formatter = CLIFormatter(
    executable="python",
    script="train.py",
    working_dir="/path/to/project"
)
```

### How It Works

The formatter takes job parameters and converts them to command-line arguments:

```python
# Job parameters
parameters = {"learning_rate": 0.01, "epochs": 100, "model": "resnet50"}

# CLIFormatter generates:
# python train.py --learning_rate 0.01 --epochs 100 --model resnet50
```

### Complete Example

```python title="worker.py"
from whatsnext.api.client import Server, Client, CLIFormatter

# Create a formatter for your training script
formatter = CLIFormatter(
    executable="python",
    script="train.py",
    working_dir="/home/user/ml-project"
)

# Connect and create client
server = Server("localhost", 8000)
project = server.get_project("ml-training")

client = Client(
    entity="ml-team",
    name="training-worker",
    description="ML training worker",
    project=project,
    formatter=formatter
)

# Start processing jobs
client.work()
```

Your `train.py` should accept command-line arguments:

```python title="train.py"
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--learning_rate", type=float, required=True)
parser.add_argument("--epochs", type=int, required=True)
parser.add_argument("--model", type=str, default="resnet50")
args = parser.parse_args()

# Your training code here
print(f"Training {args.model} for {args.epochs} epochs at lr={args.learning_rate}")
```

## SlurmFormatter

For running jobs on HPC clusters using the SLURM scheduler.

### Basic Usage

```python
from whatsnext.api.client import SlurmFormatter

formatter = SlurmFormatter(
    partition="gpu",          # SLURM partition
    time="04:00:00",          # Max runtime (HH:MM:SS)
    nodes=1,                  # Number of nodes
    ntasks=1,                 # Number of tasks
    cpus_per_task=8,          # CPUs per task
    mem="32G",                # Memory
    gpus=1                    # Number of GPUs (optional)
)
```

### How It Works

The formatter creates an sbatch command with your job parameters:

```python
# Job parameters
parameters = {"learning_rate": 0.01, "epochs": 100}

# SlurmFormatter generates:
# sbatch --parsable --job-name train --wrap "python --learning_rate 0.01 --epochs 100"
```

### With Script Template

For more control over the command, use a script template:

```python
formatter = SlurmFormatter(
    partition="gpu",
    time="04:00:00",
    gpus=1,
    script_template="python train.py --lr {learning_rate} --epochs {epochs}"
)
```

Now job parameters are substituted into the template:

```python
parameters = {"learning_rate": 0.01, "epochs": 100}
# Generates: sbatch ... --wrap "python train.py --lr 0.01 --epochs 100"
```

### Complete Example

```python title="slurm_worker.py"
from whatsnext.api.client import Server, Client, SlurmFormatter

# Configure for your SLURM cluster
formatter = SlurmFormatter(
    partition="gpu-a100",
    time="08:00:00",
    nodes=1,
    cpus_per_task=16,
    mem="64G",
    gpus=4,
    script_template="python /home/user/train.py --lr {lr} --epochs {epochs} --batch_size {batch_size}"
)

# Connect and run
server = Server("localhost", 8000)
project = server.get_project("large-scale-training")

client = Client(
    entity="research-lab",
    name="slurm-submitter",
    description="Submits jobs to SLURM",
    project=project,
    formatter=formatter,
    available_cpu=16,
    available_accelerators=4
)

# Submit and monitor jobs
client.work(run_forever=True)
```

!!! info "How SLURM Jobs Work"
    The SlurmFormatter submits jobs to SLURM using `sbatch`. The job runs asynchronously on the cluster - the worker doesn't wait for completion.

### Common SLURM Options

| Option | Description | Example |
|--------|-------------|---------|
| `partition` | Queue/partition to submit to | `"gpu"`, `"compute"` |
| `time` | Maximum wall time | `"04:00:00"` (4 hours) |
| `nodes` | Number of compute nodes | `1` |
| `ntasks` | Number of parallel tasks | `1` |
| `cpus_per_task` | CPU cores per task | `8` |
| `mem` | Memory per node | `"32G"` |
| `gpus` | Number of GPUs | `4` |

## RUNAIFormatter

For running jobs on Kubernetes clusters using RUNAI.

### Basic Usage

```python
from whatsnext.api.client import RUNAIFormatter

formatter = RUNAIFormatter(
    project="ml-team",                    # RUNAI project
    image="pytorch/pytorch:2.0-cuda11.8", # Docker image
    gpu=1,                                # Number of GPUs
    cpu=4,                                # Number of CPUs
    memory="16Gi"                         # Memory limit
)
```

### How It Works

The formatter creates a `runai submit` command:

```python
# Job parameters
parameters = {"learning_rate": 0.01, "epochs": 100}

# RUNAIFormatter generates:
# runai submit train --project ml-team --image pytorch:2.0 --gpu 1 \
#   -e LEARNING_RATE=0.01 -e EPOCHS=100
```

Parameters become environment variables in the container.

### With Environment Variables

```python
formatter = RUNAIFormatter(
    project="ml-team",
    image="myregistry/training:latest",
    gpu=4,
    cpu=16,
    memory="64Gi",
    working_dir="/workspace",
    environment={
        "WANDB_API_KEY": "your-key",
        "CUDA_VISIBLE_DEVICES": "0,1,2,3"
    }
)
```

### Complete Example

```python title="runai_worker.py"
from whatsnext.api.client import Server, Client, RUNAIFormatter

# Configure for RUNAI cluster
formatter = RUNAIFormatter(
    project="deep-learning",
    image="myregistry.io/ml-training:v2.0",
    gpu=8,
    cpu=32,
    memory="128Gi",
    working_dir="/workspace/training",
    environment={
        "WANDB_PROJECT": "my-experiments",
        "NCCL_DEBUG": "INFO"
    }
)

# Connect and run
server = Server("localhost", 8000)
project = server.get_project("distributed-training")

client = Client(
    entity="research-team",
    name="runai-submitter",
    description="Submits to RUNAI",
    project=project,
    formatter=formatter,
    available_cpu=32,
    available_accelerators=8
)

client.work(run_forever=True)
```

### Common RUNAI Options

| Option | Description | Example |
|--------|-------------|---------|
| `project` | RUNAI project name | `"ml-team"` |
| `image` | Docker image | `"pytorch:2.0"` |
| `gpu` | Number of GPUs | `4` |
| `cpu` | Number of CPUs | `16` |
| `memory` | Memory limit | `"64Gi"` |
| `working_dir` | Container working directory | `"/workspace"` |
| `environment` | Environment variables | `{"KEY": "value"}` |

## Creating Custom Formatters

You can create your own formatter by extending the base class:

```python
from whatsnext.api.client.formatter import Formatter
import subprocess
from typing import Any, Dict, List

class MyCustomFormatter(Formatter):
    """Custom formatter for my execution environment."""

    def __init__(self, config_file: str):
        self.config_file = config_file

    def format(self, task: str, parameters: Dict[str, Any]) -> List[str]:
        """Convert parameters to a command."""
        cmd = ["my-runner", "--config", self.config_file, "--task", task]
        for key, value in parameters.items():
            cmd.extend([f"--{key}", str(value)])
        return cmd

    def execute(self, command: List[str]) -> subprocess.CompletedProcess:
        """Run the command."""
        return subprocess.run(
            command,
            capture_output=True,
            text=True
        )
```

Use it like any other formatter:

```python
formatter = MyCustomFormatter(config_file="/path/to/config.yaml")
client = Client(
    entity="my-team",
    name="worker",
    project=project,
    formatter=formatter,
    ...
)
```

## Best Practices

### 1. Use Script Templates for Complex Commands

Instead of relying on automatic parameter conversion:

```python
# Automatic conversion (simple cases)
formatter = CLIFormatter(executable="python", script="train.py")
# Generates: python train.py --param1 value1 --param2 value2

# Script template (complex commands)
formatter = SlurmFormatter(
    script_template="cd /project && source venv/bin/activate && python train.py --lr {lr}"
)
```

### 2. Match Worker Resources to Task Requirements

When creating tasks, specify resource requirements:

```python
# Create task with resource requirements
response = requests.post(
    "http://localhost:8000/tasks/",
    json={
        "name": "gpu-training",
        "project_id": project.id,
        "required_cpu": 8,
        "required_accelerators": 4  # 4 GPUs required
    }
)

# Worker with matching resources
client = Client(
    ...,
    available_cpu=16,
    available_accelerators=4
)
```

### 3. Use run_forever for Long-Running Workers

```python
# For production workers
client.work(run_forever=True, poll_interval=10)

# Worker will:
# - Process jobs when available
# - Wait 10 seconds when queue is empty
# - Continue until Ctrl+C or SIGTERM
```

### 4. Handle Graceful Shutdown

Workers automatically handle SIGINT and SIGTERM:

```bash
# Stop gracefully (waits for current job to finish)
kill -SIGTERM <worker_pid>

# Or use Ctrl+C in the terminal
```

## Troubleshooting

### CLIFormatter: Command not found

```python
# Make sure the executable is in PATH or use full path
formatter = CLIFormatter(
    executable="/usr/local/bin/python3",
    script="/full/path/to/script.py"
)
```

### SlurmFormatter: Jobs not appearing

Check SLURM output:
```bash
squeue -u $USER
```

### RUNAIFormatter: Image pull errors

Ensure you're logged in to your container registry:
```bash
runai login
```
