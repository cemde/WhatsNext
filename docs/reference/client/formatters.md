# Formatters

Formatters convert job parameters into executable commands for different execution environments.

## Overview

WhatsNext provides three built-in formatters:

| Formatter | Use Case |
|-----------|----------|
| [CLIFormatter](#cliformatter) | Direct command-line execution |
| [SlurmFormatter](#slurmformatter) | SLURM HPC cluster submission |
| [RUNAIFormatter](#runaiformatter) | Kubernetes/RUNAI submission |

## CLIFormatter

Executes jobs directly via subprocess.

### Basic Usage

```python
from whatsnext.api.client import CLIFormatter

formatter = CLIFormatter(
    executable="python",
    script="train.py",
    working_dir="/path/to/project"
)

# Job parameters: {"lr": 0.01, "epochs": 100}
# Generates: python train.py --lr 0.01 --epochs 100
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `executable` | str | `"python"` | The command to run |
| `script` | str | `None` | Script path to execute |
| `working_dir` | str | `None` | Working directory |

### How It Works

1. **format()**: Converts parameters to CLI arguments
   ```python
   formatter.format("train", {"lr": 0.01, "epochs": 100})
   # Returns: ["python", "train.py", "--lr", "0.01", "--epochs", "100"]
   ```

2. **execute()**: Runs via subprocess
   ```python
   result = formatter.execute(["python", "train.py", "--lr", "0.01"])
   print(result.returncode)  # 0 = success
   print(result.stdout)      # Command output
   ```

## SlurmFormatter

Submits jobs to SLURM HPC clusters using `sbatch`.

### Basic Usage

```python
from whatsnext.api.client import SlurmFormatter

formatter = SlurmFormatter(
    partition="gpu",
    time="04:00:00",
    nodes=1,
    cpus_per_task=8,
    mem="32G",
    gpus=4,
    script_template="python train.py --lr {lr} --epochs {epochs}"
)
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `partition` | str | `"default"` | SLURM partition |
| `time` | str | `"01:00:00"` | Wall time limit (HH:MM:SS) |
| `nodes` | int | `1` | Number of nodes |
| `ntasks` | int | `1` | Number of tasks |
| `cpus_per_task` | int | `1` | CPUs per task |
| `mem` | str | `"4G"` | Memory per node |
| `gpus` | int | `None` | Number of GPUs |
| `script_template` | str | `None` | Command template with placeholders |

### Script Template

Use Python format strings to inject parameters:

```python
formatter = SlurmFormatter(
    partition="gpu",
    gpus=2,
    script_template="python train.py --lr {learning_rate} --batch {batch_size}"
)

# Job parameters: {"learning_rate": 0.001, "batch_size": 32}
# Generates sbatch command that runs:
#   python train.py --lr 0.001 --batch 32
```

### Generated Command

```python
formatter.format("my-job", {"lr": 0.01})
# Returns: ["sbatch", "--parsable", "--job-name", "my-job", "--wrap", "python --lr 0.01"]
```

## RUNAIFormatter

Submits jobs to RUNAI on Kubernetes clusters.

### Basic Usage

```python
from whatsnext.api.client import RUNAIFormatter

formatter = RUNAIFormatter(
    project="ml-team",
    image="pytorch/pytorch:2.0-cuda11.8",
    gpu=4,
    cpu=16,
    memory="64Gi",
    working_dir="/workspace",
    environment={"WANDB_API_KEY": "xxx"}
)
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project` | str | *required* | RUNAI project name |
| `image` | str | *required* | Docker image |
| `gpu` | int | `1` | Number of GPUs |
| `cpu` | int | `1` | Number of CPUs |
| `memory` | str | `"4Gi"` | Memory limit |
| `working_dir` | str | `None` | Container working directory |
| `environment` | dict | `None` | Environment variables |

### Environment Variables

Job parameters are passed as uppercase environment variables:

```python
# Job parameters: {"learning_rate": 0.01, "batch_size": 32}
# Sets in container:
#   LEARNING_RATE=0.01
#   BATCH_SIZE=32
```

### Generated Command

```python
formatter.format("train-job", {"lr": 0.01})
# Returns: [
#   "runai", "submit", "train-job",
#   "--project", "ml-team",
#   "--image", "pytorch/pytorch:2.0-cuda11.8",
#   "--gpu", "4",
#   "--cpu", "16",
#   "--memory", "64Gi",
#   "-e", "LR=0.01"
# ]
```

## Creating Custom Formatters

Extend the `Formatter` base class:

```python
from whatsnext.api.client import Formatter
import subprocess
from typing import Any, Dict, List

class MyFormatter(Formatter):
    def __init__(self, **options):
        self.options = options

    def format(self, task: str, parameters: Dict[str, Any]) -> List[str]:
        """Convert parameters to a command."""
        cmd = ["my-tool", task]
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

## API Reference

::: whatsnext.api.client.formatter.Formatter

::: whatsnext.api.client.formatter.CLIFormatter

::: whatsnext.api.client.formatter.SlurmFormatter

::: whatsnext.api.client.formatter.RUNAIFormatter
