"""Tests for the Project class."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from whatsnext.api.client.project import Project
from whatsnext.api.client.job import Job
from whatsnext.api.client.exceptions import EmptyQueueError


class TestProjectInit:
    """Tests for Project initialization."""

    def test_project_init_basic(self):
        """Test basic project initialization."""
        project = Project(id=1)
        assert project.id == 1
        assert project._server is None

    def test_project_init_with_server(self):
        """Test project initialization with server."""
        mock_server = MagicMock()
        project = Project(id=1, _server=mock_server)
        assert project.id == 1
        assert project._server == mock_server


class TestProjectCheckServer:
    """Tests for _check_server method."""

    def test_check_server_raises_without_server(self):
        """Test _check_server raises error without server."""
        project = Project(id=1)
        with pytest.raises(RuntimeError, match="not bound to a server"):
            project._check_server()

    def test_check_server_returns_server(self):
        """Test _check_server returns server when bound."""
        mock_server = MagicMock()
        project = Project(id=1, _server=mock_server)

        result = project._check_server()

        assert result == mock_server


class TestProjectProperties:
    """Tests for Project properties."""

    def test_last_updated(self):
        """Test last_updated property."""
        mock_server = MagicMock()
        mock_connector = MagicMock()
        expected_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_connector.get_last_updated.return_value = expected_time
        mock_server._project_connector = mock_connector

        project = Project(id=1, _server=mock_server)

        result = project.last_updated

        assert result == expected_time
        mock_connector.get_last_updated.assert_called_once_with(project)

    def test_name(self):
        """Test name property."""
        mock_server = MagicMock()
        mock_connector = MagicMock()
        mock_connector.get_name.return_value = "test-project"
        mock_server._project_connector = mock_connector

        project = Project(id=1, _server=mock_server)

        result = project.name

        assert result == "test-project"
        mock_connector.get_name.assert_called_once_with(project)

    def test_description(self):
        """Test description property."""
        mock_server = MagicMock()
        mock_connector = MagicMock()
        mock_connector.get_description.return_value = "Test description"
        mock_server._project_connector = mock_connector

        project = Project(id=1, _server=mock_server)

        result = project.description

        assert result == "Test description"

    def test_status(self):
        """Test status property."""
        mock_server = MagicMock()
        mock_connector = MagicMock()
        mock_connector.get_status.return_value = "ACTIVE"
        mock_server._project_connector = mock_connector

        project = Project(id=1, _server=mock_server)

        result = project.status

        assert result == "ACTIVE"

    def test_created_at(self):
        """Test created_at property."""
        mock_server = MagicMock()
        mock_connector = MagicMock()
        expected_time = datetime(2024, 1, 1, 10, 0, 0)
        mock_connector.get_created_at.return_value = expected_time
        mock_server._project_connector = mock_connector

        project = Project(id=1, _server=mock_server)

        result = project.created_at

        assert result == expected_time

    def test_queue(self):
        """Test queue property."""
        mock_server = MagicMock()
        mock_server.get_queue.return_value = [
            {"id": 1, "name": "job1"},
            {"id": 2, "name": "job2"}
        ]

        project = Project(id=1, _server=mock_server)

        result = project.queue

        assert len(result) == 2
        mock_server.get_queue.assert_called_once_with(project)


class TestProjectSetDescription:
    """Tests for set_description method."""

    def test_set_description(self):
        """Test setting project description."""
        mock_server = MagicMock()
        mock_connector = MagicMock()
        mock_server._project_connector = mock_connector

        project = Project(id=1, _server=mock_server)

        project.set_description("New description")

        mock_connector.set_description.assert_called_once_with(project, "New description")


class TestProjectQueueOperations:
    """Tests for Project queue operations."""

    def test_append_queue(self):
        """Test appending job to queue."""
        mock_server = MagicMock()
        mock_server.append_queue.return_value = True

        project = Project(id=1, _server=mock_server)
        job = Job(name="test", task="train", parameters={})

        result = project.append_queue(job)

        assert result is True
        mock_server.append_queue.assert_called_once_with(project, job)

    def test_extend_queue(self):
        """Test extending queue with multiple jobs."""
        mock_server = MagicMock()
        mock_server.extend_queue.return_value = [1, 2, 3]

        project = Project(id=1, _server=mock_server)
        jobs = [
            Job(name="job1", task="train", parameters={}),
            Job(name="job2", task="train", parameters={}),
            Job(name="job3", task="train", parameters={})
        ]

        result = project.extend_queue(jobs)

        assert result == [1, 2, 3]
        mock_server.extend_queue.assert_called_once_with(project, jobs)

    def test_clear_queue(self):
        """Test clearing queue."""
        mock_server = MagicMock()
        mock_server.clear_queue.return_value = 5

        project = Project(id=1, _server=mock_server)

        result = project.clear_queue()

        assert result == 5
        mock_server.clear_queue.assert_called_once_with(project)

    def test_remove_job(self):
        """Test removing specific job."""
        mock_server = MagicMock()
        mock_server.remove_job.return_value = True

        project = Project(id=1, _server=mock_server)

        result = project.remove_job(42)

        assert result is True
        mock_server.remove_job.assert_called_once_with(project, 42)

    def test_pop_queue_valid_index(self):
        """Test popping job at valid index."""
        mock_server = MagicMock()
        mock_server.get_queue.return_value = [
            {"id": 10, "name": "job1"},
            {"id": 20, "name": "job2"},
            {"id": 30, "name": "job3"}
        ]
        mock_server.remove_job.return_value = True

        project = Project(id=1, _server=mock_server)

        result = project.pop_queue(1)  # Pop second job

        assert result is True
        mock_server.remove_job.assert_called_once_with(project, 20)

    def test_pop_queue_invalid_index_negative(self):
        """Test popping job at negative index."""
        mock_server = MagicMock()
        mock_server.get_queue.return_value = [
            {"id": 10, "name": "job1"}
        ]

        project = Project(id=1, _server=mock_server)

        result = project.pop_queue(-1)

        assert result is False
        mock_server.remove_job.assert_not_called()

    def test_pop_queue_invalid_index_too_large(self):
        """Test popping job at index beyond queue length."""
        mock_server = MagicMock()
        mock_server.get_queue.return_value = [
            {"id": 10, "name": "job1"}
        ]

        project = Project(id=1, _server=mock_server)

        result = project.pop_queue(5)

        assert result is False


class TestProjectFetchJob:
    """Tests for fetch_job method."""

    def test_fetch_job_success(self):
        """Test successful job fetch."""
        mock_server = MagicMock()
        mock_server.fetch_job.return_value = {
            "job": {
                "id": 1,
                "name": "test-job",
                "task_name": "train",
                "project_id": 1,
                "task_id": 1,
                "parameters": {"lr": 0.01},
                "status": "QUEUED",
                "priority": 5,
                "depends": {}
            },
            "num_pending": 10
        }

        project = Project(id=1, _server=mock_server)

        job = project.fetch_job()

        assert isinstance(job, Job)
        assert job.id == 1
        assert job.name == "test-job"
        assert job.task == "train"
        assert job.parameters == {"lr": 0.01}
        assert job._server == mock_server

    def test_fetch_job_with_resources(self):
        """Test job fetch with resource filtering."""
        mock_server = MagicMock()
        mock_server.fetch_job.return_value = {
            "job": {
                "id": 1,
                "name": "test-job",
                "task_name": "train",
                "project_id": 1,
                "task_id": 1,
                "parameters": {},
                "status": "QUEUED",
                "priority": 0,
                "depends": {}
            },
            "num_pending": 5
        }

        project = Project(id=1, _server=mock_server)

        project.fetch_job(available_cpu=8, available_accelerators=4)

        mock_server.fetch_job.assert_called_once_with(
            project,
            available_cpu=8,
            available_accelerators=4
        )


class TestProjectCreateTask:
    """Tests for create_task method."""

    def test_create_task(self):
        """Test task creation."""
        mock_server = MagicMock()
        mock_server.create_task.return_value = True

        project = Project(id=1, _server=mock_server)

        result = project.create_task("train-model")

        assert result is True
        mock_server.create_task.assert_called_once_with(project, "train-model")


class TestProjectRepr:
    """Tests for Project repr."""

    def test_repr(self):
        """Test project string representation."""
        mock_server = MagicMock()
        mock_connector = MagicMock()
        mock_connector.get_name.return_value = "test-project"
        mock_server._project_connector = mock_connector

        project = Project(id=42, _server=mock_server)

        repr_str = repr(project)

        assert "42" in repr_str
        assert "test-project" in repr_str
