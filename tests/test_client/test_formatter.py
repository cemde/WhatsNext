"""Tests for formatter classes."""

import subprocess
from unittest.mock import patch


from whatsnext.api.client.formatter import CLIFormatter, RUNAIFormatter, SlurmFormatter


class TestCLIFormatter:
    """Tests for the CLIFormatter class."""

    def test_format_basic(self):
        """Test basic formatting with default executable."""
        formatter = CLIFormatter()
        cmd = formatter.format("train", {"lr": 0.01, "epochs": 10})

        assert cmd == ["python", "--lr", "0.01", "--epochs", "10"]

    def test_format_with_script(self):
        """Test formatting with a script path."""
        formatter = CLIFormatter(executable="python", script="train.py")
        cmd = formatter.format("train", {"lr": 0.01})

        assert cmd == ["python", "train.py", "--lr", "0.01"]

    def test_format_with_custom_executable(self):
        """Test formatting with custom executable."""
        formatter = CLIFormatter(executable="python3")
        cmd = formatter.format("train", {"batch_size": 32})

        assert cmd == ["python3", "--batch_size", "32"]

    def test_format_empty_parameters(self):
        """Test formatting with no parameters."""
        formatter = CLIFormatter()
        cmd = formatter.format("task", {})

        assert cmd == ["python"]

    def test_format_with_script_empty_params(self):
        """Test formatting with script but no parameters."""
        formatter = CLIFormatter(script="run.py")
        cmd = formatter.format("task", {})

        assert cmd == ["python", "run.py"]

    @patch("subprocess.run")
    def test_execute(self, mock_run):
        """Test command execution."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["python", "--lr", "0.01"],
            returncode=0,
            stdout="output",
            stderr="",
        )

        formatter = CLIFormatter()
        result = formatter.execute(["python", "--lr", "0.01"])

        assert result.returncode == 0
        assert result.stdout == "output"
        mock_run.assert_called_once_with(
            ["python", "--lr", "0.01"],
            shell=False,
            capture_output=True,
            text=True,
            cwd=None,
        )

    @patch("subprocess.run")
    def test_execute_with_working_dir(self, mock_run):
        """Test execution with working directory."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["python", "train.py"],
            returncode=0,
            stdout="",
            stderr="",
        )

        formatter = CLIFormatter(working_dir="/path/to/project")
        formatter.execute(["python", "train.py"])

        mock_run.assert_called_once_with(
            ["python", "train.py"],
            shell=False,
            capture_output=True,
            text=True,
            cwd="/path/to/project",
        )

    @patch("subprocess.run")
    def test_execute_failure(self, mock_run):
        """Test command execution failure."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["python", "fail.py"],
            returncode=1,
            stdout="",
            stderr="Error: something went wrong",
        )

        formatter = CLIFormatter()
        result = formatter.execute(["python", "fail.py"])

        assert result.returncode == 1
        assert "Error" in result.stderr


class TestSlurmFormatter:
    """Tests for the SlurmFormatter class."""

    def test_format_basic(self):
        """Test basic SLURM formatting."""
        formatter = SlurmFormatter()
        cmd = formatter.format("train", {"lr": 0.01, "epochs": 10})

        assert cmd[0] == "sbatch"
        assert "--parsable" in cmd
        assert "--job-name" in cmd
        assert "train" in cmd
        assert "--wrap" in cmd
        # Check that the wrapped command contains the parameters
        wrap_idx = cmd.index("--wrap")
        wrapped_cmd = cmd[wrap_idx + 1]
        assert "--lr 0.01" in wrapped_cmd
        assert "--epochs 10" in wrapped_cmd

    def test_format_with_script_template(self):
        """Test formatting with script template."""
        formatter = SlurmFormatter(script_template="python train.py --lr {lr} --epochs {epochs}")
        cmd = formatter.format("train", {"lr": 0.01, "epochs": 10})

        wrap_idx = cmd.index("--wrap")
        wrapped_cmd = cmd[wrap_idx + 1]
        assert wrapped_cmd == "python train.py --lr 0.01 --epochs 10"

    def test_init_with_options(self):
        """Test initialization with custom options."""
        formatter = SlurmFormatter(
            partition="gpu",
            time="02:00:00",
            nodes=2,
            ntasks=4,
            cpus_per_task=8,
            mem="16G",
            gpus=2,
        )

        assert formatter.partition == "gpu"
        assert formatter.time == "02:00:00"
        assert formatter.nodes == 2
        assert formatter.ntasks == 4
        assert formatter.cpus_per_task == 8
        assert formatter.mem == "16G"
        assert formatter.gpus == 2

    def test_generate_sbatch_script(self):
        """Test sbatch script generation."""
        formatter = SlurmFormatter(partition="gpu", gpus=1)
        script = formatter._generate_sbatch_script("test_job", "python train.py")

        assert "#!/bin/bash" in script
        assert "#SBATCH --job-name=test_job" in script
        assert "#SBATCH --partition=gpu" in script
        assert "#SBATCH --gpus=1" in script
        assert "python train.py" in script

    def test_generate_sbatch_script_no_gpus(self):
        """Test sbatch script generation without GPUs."""
        formatter = SlurmFormatter(partition="cpu")
        script = formatter._generate_sbatch_script("cpu_job", "python process.py")

        assert "--gpus" not in script

    @patch("subprocess.run")
    def test_execute(self, mock_run):
        """Test SLURM job submission."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["sbatch", "--parsable", "--job-name", "train", "--wrap", "python"],
            returncode=0,
            stdout="12345",
            stderr="",
        )

        formatter = SlurmFormatter()
        result = formatter.execute(["sbatch", "--parsable", "--job-name", "train", "--wrap", "python"])

        assert result.returncode == 0
        assert result.stdout == "12345"


class TestRUNAIFormatter:
    """Tests for the RUNAIFormatter class."""

    def test_format_basic(self):
        """Test basic RUNAI formatting."""
        formatter = RUNAIFormatter(project="my-project", image="pytorch:latest")
        cmd = formatter.format("train", {"lr": 0.01})

        assert cmd[0] == "runai"
        assert cmd[1] == "submit"
        assert "train" in cmd
        assert "--project" in cmd
        assert "my-project" in cmd
        assert "--image" in cmd
        assert "pytorch:latest" in cmd
        # Parameters should be added as environment variables
        assert "-e" in cmd
        env_idx = cmd.index("-e")
        assert "LR=0.01" in cmd[env_idx + 1]

    def test_format_with_all_options(self):
        """Test formatting with all options."""
        formatter = RUNAIFormatter(
            project="ml-project",
            image="custom:v1",
            gpu=4,
            cpu=16,
            memory="32Gi",
            working_dir="/workspace",
            environment={"API_KEY": "secret"},
        )
        cmd = formatter.format("experiment", {"model": "resnet"})

        assert "--gpu" in cmd
        assert "4" in cmd
        assert "--cpu" in cmd
        assert "16" in cmd
        assert "--memory" in cmd
        assert "32Gi" in cmd
        assert "--working-dir" in cmd
        assert "/workspace" in cmd
        # Check environment variable
        assert "API_KEY=secret" in cmd

    def test_format_multiple_parameters(self):
        """Test formatting with multiple parameters."""
        formatter = RUNAIFormatter(project="test", image="test:latest")
        cmd = formatter.format("train", {"lr": 0.01, "batch_size": 32, "epochs": 100})

        # Each parameter becomes an environment variable
        cmd_str = " ".join(cmd)
        assert "LR=0.01" in cmd_str
        assert "BATCH_SIZE=32" in cmd_str
        assert "EPOCHS=100" in cmd_str

    @patch("subprocess.run")
    def test_execute(self, mock_run):
        """Test RUNAI job submission."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["runai", "submit", "train"],
            returncode=0,
            stdout="Job submitted successfully",
            stderr="",
        )

        formatter = RUNAIFormatter(project="test", image="test:latest")
        result = formatter.execute(["runai", "submit", "train"])

        assert result.returncode == 0
        assert "submitted" in result.stdout
