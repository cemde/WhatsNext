"""Tests for client model classes: Artifact, Task, Resource, Job, utils."""

import subprocess
from unittest.mock import MagicMock

import pytest

from whatsnext.api.client.artifact import Artifact
from whatsnext.api.client.job import Job
from whatsnext.api.client.resource import RESOURCE_STATUS, Resource
from whatsnext.api.client.task import Task
from whatsnext.api.client.utils import Status, random_string


class TestArtifact:
    """Tests for the Artifact class."""

    def test_artifact_instantiation(self):
        """Test that Artifact can be instantiated."""
        artifact = Artifact()
        assert artifact is not None
        assert isinstance(artifact, Artifact)


class TestTask:
    """Tests for the Task class."""

    def test_task_basic_init(self):
        """Test basic task initialization."""
        task = Task(name="train-model")
        assert task.name == "train-model"
        assert task.id is not None
        assert len(task.id) > 0
        assert task.artifacts == []
        assert task.resource == []
        assert task._command_template is None

    def test_task_with_command_template(self):
        """Test task with command template."""
        task = Task(name="train", command_template="python train.py --lr {lr} --epochs {epochs}")
        assert task._command_template == "python train.py --lr {lr} --epochs {epochs}"

    def test_task_with_artifacts_and_resource(self):
        """Test task with artifacts and resources."""
        task = Task(name="train", artifacts=["model.pt", "logs/"], resource=["gpu:1", "cpu:4"])
        assert task.artifacts == ["model.pt", "logs/"]
        assert task.resource == ["gpu:1", "cpu:4"]

    def test_format_command_success(self):
        """Test successful command formatting."""
        task = Task(name="train", command_template="python train.py --lr {lr} --epochs {epochs}")
        command = task.format_command({"lr": 0.01, "epochs": 100})
        assert command == "python train.py --lr 0.01 --epochs 100"

    def test_format_command_no_template(self):
        """Test that format_command raises error without template."""
        task = Task(name="train")
        with pytest.raises(ValueError, match="No command template defined"):
            task.format_command({"lr": 0.01})

    def test_format_command_missing_param(self):
        """Test format_command with missing parameter."""
        task = Task(name="train", command_template="python train.py --lr {lr} --epochs {epochs}")
        with pytest.raises(KeyError):
            task.format_command({"lr": 0.01})  # missing epochs


class TestResource:
    """Tests for the Resource class."""

    def test_resource_init(self):
        """Test resource initialization."""
        mock_client = MagicMock()
        resource = Resource(cpu=4, accelerator=["0", "1"], client=mock_client)

        assert resource.cpus == 4
        assert resource.accelerator == ["0", "1"]
        assert resource.client == mock_client
        assert resource._status == "active"

    def test_resource_active(self):
        """Test resource active check."""
        mock_client = MagicMock()
        resource = Resource(cpu=1, accelerator=[], client=mock_client)

        assert resource.active() is True
        resource._status = "inactive"
        assert resource.active() is False

    def test_set_status_valid(self):
        """Test setting valid status."""
        mock_client = MagicMock()
        resource = Resource(cpu=1, accelerator=[], client=mock_client)

        resource.set_status("inactive")
        assert resource._status == "inactive"

        resource.set_status("active")
        assert resource._status == "active"

    def test_set_status_invalid(self):
        """Test setting invalid status raises error."""
        mock_client = MagicMock()
        resource = Resource(cpu=1, accelerator=[], client=mock_client)

        with pytest.raises(ValueError, match="Invalid status"):
            resource.set_status("unknown")

    def test_resource_status_constants(self):
        """Test RESOURCE_STATUS constants."""
        assert "active" in RESOURCE_STATUS
        assert "inactive" in RESOURCE_STATUS
        assert len(RESOURCE_STATUS) == 2


class TestUtils:
    """Tests for utility functions."""

    def test_random_string_default_length(self):
        """Test random_string with default length."""
        s = random_string()
        assert isinstance(s, str)
        assert len(s) > 0
        # UUID hex is 32 chars, default length is 128 but limited by UUID
        assert len(s) <= 32

    def test_random_string_custom_length(self):
        """Test random_string with custom length."""
        s = random_string(length=8)
        assert len(s) == 8

    def test_random_string_uniqueness(self):
        """Test that random_string generates unique values."""
        strings = [random_string() for _ in range(100)]
        assert len(set(strings)) == 100  # All unique

    def test_status_class(self):
        """Test Status class initialization."""
        status = Status()
        assert status.status == "active"
        assert status.client is None


class TestJob:
    """Tests for the Job class."""

    def test_job_basic_init(self):
        """Test basic job initialization."""
        job = Job(name="experiment-1", task="train-model", parameters={"lr": 0.01})
        assert job.name == "experiment-1"
        assert job.task == "train-model"
        assert job.parameters == {"lr": 0.01}
        assert job.priority == 0
        assert job.status == "PENDING"
        assert job.depends is None
        assert job.id is None
        assert job._server is None

    def test_job_full_init(self):
        """Test job initialization with all parameters."""
        from datetime import datetime

        now = datetime.now()
        job = Job(
            name="experiment-1",
            task="train",
            parameters={"lr": 0.01},
            priority=10,
            status="QUEUED",
            depends=[],
            created_at=now,
            updated_at=now,
            id=42,
        )
        assert job.id == 42
        assert job.priority == 10
        assert job.status == "QUEUED"
        assert job.depends == []
        assert job.created_at == now
        assert job.updated_at == now

    def test_job_repr(self):
        """Test job string representation."""
        job = Job(id=42, name="experiment-1", task="train", parameters={}, priority=5)
        repr_str = repr(job)
        assert "42" in repr_str
        assert "experiment-1" in repr_str
        assert "train" in repr_str
        assert "5" in repr_str

    def test_job_bind_server(self):
        """Test binding job to server."""
        job = Job(name="test", task="task", parameters={})
        mock_server = MagicMock()

        job._bind_server(mock_server)

        assert job._server == mock_server

    def test_set_status_without_server(self):
        """Test set_status raises error without server."""
        job = Job(name="test", task="task", parameters={})

        with pytest.raises(RuntimeError, match="not bound to a server"):
            job.set_status("RUNNING")

    def test_set_status_with_server(self):
        """Test set_status with server."""
        job = Job(name="test", task="task", parameters={})
        mock_server = MagicMock()
        job._bind_server(mock_server)

        job.set_status("RUNNING")

        mock_server._job_connector.set_status.assert_called_once_with(job, "RUNNING")
        assert job.status == "RUNNING"

    def test_set_priority_without_server(self):
        """Test set_priority_to raises error without server."""
        job = Job(name="test", task="task", parameters={})

        with pytest.raises(RuntimeError, match="not bound to a server"):
            job.set_priority_to(10)

    def test_set_priority_with_server(self):
        """Test set_priority_to with server."""
        job = Job(name="test", task="task", parameters={})
        mock_server = MagicMock()
        job._bind_server(mock_server)

        job.set_priority_to(10)

        mock_server._job_connector.set_priority_to.assert_called_once_with(job, 10)
        assert job.priority == 10

    def test_set_depends_without_server(self):
        """Test set_depends_to raises error without server."""
        job = Job(name="test", task="task", parameters={})

        with pytest.raises(RuntimeError, match="not bound to a server"):
            job.set_depends_to([])

    def test_set_depends_with_server(self):
        """Test set_depends_to with server."""
        job = Job(name="test", task="task", parameters={})
        mock_server = MagicMock()
        job._bind_server(mock_server)

        dep_job = Job(id=1, name="dep", task="other", parameters={})
        job.set_depends_to([dep_job])

        mock_server._job_connector.set_depends_to.assert_called_once_with(job, [dep_job])
        assert job.depends == [dep_job]

    def test_job_run_success(self):
        """Test successful job run."""
        job = Job(id=1, name="test", task="task", parameters={"x": 1})
        mock_server = MagicMock()
        job._bind_server(mock_server)

        mock_resource = MagicMock()
        mock_formatter = MagicMock()
        mock_resource.client.formatter = mock_formatter
        mock_formatter.format.return_value = ["python", "script.py"]
        mock_formatter.execute.return_value = subprocess.CompletedProcess(
            args=["python", "script.py"], returncode=0, stdout="output", stderr=""
        )

        exit_code = job.run(mock_resource)

        assert exit_code == 0
        mock_formatter.format.assert_called_once_with("task", {"x": 1})
        mock_formatter.execute.assert_called_once()
        # Status should have been set to RUNNING then COMPLETED
        assert mock_server._job_connector.set_status.call_count == 2

    def test_job_run_failure(self):
        """Test failed job run."""
        job = Job(id=1, name="test", task="task", parameters={})
        mock_server = MagicMock()
        job._bind_server(mock_server)

        mock_resource = MagicMock()
        mock_formatter = MagicMock()
        mock_resource.client.formatter = mock_formatter
        mock_formatter.format.return_value = ["python", "script.py"]
        mock_formatter.execute.return_value = subprocess.CompletedProcess(
            args=["python", "script.py"], returncode=1, stdout="", stderr="Error occurred"
        )

        exit_code = job.run(mock_resource)

        assert exit_code == 1

    def test_job_run_exception(self):
        """Test job run with exception."""
        job = Job(id=1, name="test", task="task", parameters={})
        mock_server = MagicMock()
        job._bind_server(mock_server)

        mock_resource = MagicMock()
        mock_formatter = MagicMock()
        mock_resource.client.formatter = mock_formatter
        mock_formatter.format.side_effect = Exception("Format error")

        exit_code = job.run(mock_resource)

        assert exit_code == 1
