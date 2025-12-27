import logging
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Formatter(ABC):
    """Abstract base class for job formatters.

    A Formatter converts job parameters into executable commands and handles
    their execution. Different formatters support different execution
    environments (CLI, SLURM, RUNAI, etc.).
    """

    @abstractmethod
    def format(self, task: str, parameters: Dict[str, Any]) -> List[str]:
        """Convert job parameters to an executable command.

        Args:
            task: The task name/template identifier.
            parameters: Dictionary of job parameters.

        Returns:
            Command as a list of arguments (for subprocess).
        """
        pass

    @abstractmethod
    def execute(self, command: List[str]) -> subprocess.CompletedProcess:
        """Execute the formatted command.

        Args:
            command: Command as a list of arguments.

        Returns:
            CompletedProcess with return code, stdout, and stderr.
        """
        pass


class CLIFormatter(Formatter):
    """Formatter for direct command-line execution.

    Formats jobs as CLI commands and executes them via subprocess.
    """

    def __init__(
        self,
        executable: str = "python",
        script: Optional[str] = None,
        working_dir: Optional[str] = None,
    ) -> None:
        """Initialize a CLI formatter.

        Args:
            executable: The executable to run (e.g., "python", "bash").
            script: Optional script path to run.
            working_dir: Optional working directory for command execution.
        """
        self.executable = executable
        self.script = script
        self.working_dir = working_dir

    def format(self, task: str, parameters: Dict[str, Any]) -> List[str]:
        """Format parameters as CLI arguments.

        Args:
            task: The task name (used to look up command templates).
            parameters: Dictionary of parameters to pass as CLI args.

        Returns:
            Command as list of arguments, e.g. ["python", "train.py", "--lr", "0.01"]
        """
        cmd = [self.executable]
        if self.script:
            cmd.append(self.script)

        for key, value in parameters.items():
            cmd.append(f"--{key}")
            cmd.append(str(value))

        return cmd

    def execute(self, command: List[str]) -> subprocess.CompletedProcess:
        """Execute command via subprocess.

        Args:
            command: Command as list of arguments.

        Returns:
            CompletedProcess with return code, stdout, and stderr.
        """
        logger.info(f"Executing: {' '.join(command)}")
        return subprocess.run(
            command,
            shell=False,
            capture_output=True,
            text=True,
            cwd=self.working_dir,
        )


class SlurmFormatter(Formatter):
    """Formatter for SLURM batch job submission.

    Generates sbatch scripts and submits them to SLURM.
    """

    def __init__(
        self,
        partition: str = "default",
        time: str = "01:00:00",
        nodes: int = 1,
        ntasks: int = 1,
        cpus_per_task: int = 1,
        mem: str = "4G",
        gpus: Optional[int] = None,
        script_template: Optional[str] = None,
    ) -> None:
        """Initialize a SLURM formatter.

        Args:
            partition: SLURM partition to submit to.
            time: Maximum wall time (HH:MM:SS).
            nodes: Number of nodes to request.
            ntasks: Number of tasks.
            cpus_per_task: CPUs per task.
            mem: Memory per node.
            gpus: Number of GPUs (if any).
            script_template: Template for the job script body.
        """
        self.partition = partition
        self.time = time
        self.nodes = nodes
        self.ntasks = ntasks
        self.cpus_per_task = cpus_per_task
        self.mem = mem
        self.gpus = gpus
        self.script_template = script_template

    def _generate_sbatch_script(self, job_name: str, command: str) -> str:
        """Generate an sbatch script.

        Args:
            job_name: Name for the SLURM job.
            command: Command to run in the job.

        Returns:
            Complete sbatch script as a string.
        """
        lines = [
            "#!/bin/bash",
            f"#SBATCH --job-name={job_name}",
            f"#SBATCH --partition={self.partition}",
            f"#SBATCH --time={self.time}",
            f"#SBATCH --nodes={self.nodes}",
            f"#SBATCH --ntasks={self.ntasks}",
            f"#SBATCH --cpus-per-task={self.cpus_per_task}",
            f"#SBATCH --mem={self.mem}",
        ]
        if self.gpus:
            lines.append(f"#SBATCH --gpus={self.gpus}")

        lines.append("")
        lines.append(command)
        return "\n".join(lines)

    def format(self, task: str, parameters: Dict[str, Any]) -> List[str]:
        """Format parameters as a SLURM submission command.

        Args:
            task: The task name.
            parameters: Dictionary of job parameters.

        Returns:
            sbatch command with inline script.
        """
        # Build the command to run inside SLURM
        if self.script_template:
            inner_cmd = self.script_template.format(**parameters)
        else:
            # Default: python with CLI args
            inner_cmd = "python"
            for key, value in parameters.items():
                inner_cmd += f" --{key} {value}"

        # Use sbatch with --wrap for inline command execution
        return ["sbatch", "--parsable", "--job-name", task, "--wrap", inner_cmd]

    def execute(self, command: List[str]) -> subprocess.CompletedProcess:
        """Submit to SLURM via sbatch.

        Args:
            command: sbatch command with arguments.

        Returns:
            CompletedProcess with SLURM job ID in stdout on success.
        """
        logger.info(f"Submitting to SLURM: {' '.join(command)}")
        return subprocess.run(command, shell=False, capture_output=True, text=True)


class RUNAIFormatter(Formatter):
    """Formatter for RUNAI job submission.

    Submits jobs to RUNAI on Kubernetes clusters.
    """

    def __init__(
        self,
        project: str,
        image: str,
        gpu: int = 1,
        cpu: int = 1,
        memory: str = "4Gi",
        working_dir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize a RUNAI formatter.

        Args:
            project: RUNAI project name.
            image: Docker image to use.
            gpu: Number of GPUs to request.
            cpu: Number of CPUs to request.
            memory: Memory limit (e.g., "4Gi").
            working_dir: Working directory inside container.
            environment: Environment variables to set.
        """
        self.project = project
        self.image = image
        self.gpu = gpu
        self.cpu = cpu
        self.memory = memory
        self.working_dir = working_dir
        self.environment = environment or {}

    def format(self, task: str, parameters: Dict[str, Any]) -> List[str]:
        """Format parameters as a RUNAI submit command.

        Args:
            task: The task name (used as job name).
            parameters: Dictionary of job parameters.

        Returns:
            runai submit command.
        """
        cmd = [
            "runai",
            "submit",
            task,
            "--project",
            self.project,
            "--image",
            self.image,
            "--gpu",
            str(self.gpu),
            "--cpu",
            str(self.cpu),
            "--memory",
            self.memory,
        ]

        if self.working_dir:
            cmd.extend(["--working-dir", self.working_dir])

        for key, value in self.environment.items():
            cmd.extend(["-e", f"{key}={value}"])

        # Add job parameters as environment variables
        for key, value in parameters.items():
            cmd.extend(["-e", f"{key.upper()}={value}"])

        return cmd

    def execute(self, command: List[str]) -> subprocess.CompletedProcess:
        """Submit to RUNAI.

        Args:
            command: runai submit command.

        Returns:
            CompletedProcess with job submission result.
        """
        logger.info(f"Submitting to RUNAI: {' '.join(command)}")
        return subprocess.run(command, shell=False, capture_output=True, text=True)
