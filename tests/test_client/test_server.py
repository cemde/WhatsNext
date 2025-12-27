"""Tests for the Server and connector classes."""

from unittest.mock import MagicMock, patch

import pytest

from whatsnext.api.client.exceptions import EmptyQueueError
from whatsnext.api.client.job import Job
from whatsnext.api.client.project import Project
from whatsnext.api.client.server import DEFAULT_TIMEOUT, JobConnector, ProjectConnector, Server


class TestServer:
    """Tests for the Server class."""

    @patch("whatsnext.api.client.server.requests")
    def test_init_success(self, mock_requests):
        """Test successful server initialization."""
        mock_requests.get.return_value.raise_for_status = MagicMock()

        server = Server("localhost", 8000)

        assert server.hostname == "localhost"
        assert server.port == 8000
        assert server.base_url == "http://localhost:8000"
        mock_requests.get.assert_called_once_with("http://localhost:8000", timeout=DEFAULT_TIMEOUT)

    @patch("whatsnext.api.client.server.requests")
    def test_init_connection_error(self, mock_requests):
        """Test server initialization with connection error."""
        from requests.exceptions import ConnectionError

        mock_requests.get.side_effect = ConnectionError()
        mock_requests.exceptions.ConnectionError = ConnectionError

        with pytest.raises(ConnectionError):
            Server("localhost", 8000)

    @patch("whatsnext.api.client.server.requests")
    def test_init_timeout_error(self, mock_requests):
        """Test server initialization with timeout."""
        from requests.exceptions import Timeout

        mock_requests.get.side_effect = Timeout()
        mock_requests.exceptions.Timeout = Timeout

        with pytest.raises(Timeout):
            Server("localhost", 8000)

    @patch("whatsnext.api.client.server.requests")
    def test_list_projects(self, mock_requests, capsys):
        """Test listing projects."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.get.return_value.ok = True
        mock_requests.get.return_value.json.return_value = [
            {"id": 1, "name": "project1", "description": "desc1", "status": "ACTIVE"},
            {"id": 2, "name": "project2", "description": "desc2", "status": "ACTIVE"},
        ]

        server = Server("localhost", 8000)
        server.list_projects()

        captured = capsys.readouterr()
        assert "project1" in captured.out
        assert "project2" in captured.out

    @patch("whatsnext.api.client.server.requests")
    def test_list_projects_empty(self, mock_requests, capsys):
        """Test listing projects when none exist."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.get.return_value.ok = True
        mock_requests.get.return_value.json.return_value = []

        server = Server("localhost", 8000)
        server.list_projects()

        captured = capsys.readouterr()
        assert "No projects found" in captured.out

    @patch("whatsnext.api.client.server.requests")
    def test_get_project(self, mock_requests):
        """Test getting a project by name."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.get.return_value.ok = True
        mock_requests.get.return_value.json.return_value = {"id": 1, "name": "test_project"}

        server = Server("localhost", 8000)
        project = server.get_project("test_project")

        assert project is not None
        assert project.id == 1

    @patch("whatsnext.api.client.server.requests")
    def test_get_project_not_found(self, mock_requests):
        """Test getting a non-existent project."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        # First call succeeds (connection test), second call fails
        mock_requests.get.return_value.ok = False
        mock_requests.get.return_value.status_code = 404

        server = Server.__new__(Server)
        server.hostname = "localhost"
        server.port = 8000
        server.base_url = "http://localhost:8000"
        server._project_connector = ProjectConnector(server)
        server._job_connector = JobConnector(server)

        project = server.get_project("nonexistent")
        assert project is None

    @patch("whatsnext.api.client.server.requests")
    def test_append_project(self, mock_requests):
        """Test creating a new project."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.post.return_value.status_code = 201
        mock_requests.post.return_value.json.return_value = {"id": 1, "name": "new_project"}

        server = Server("localhost", 8000)
        project = server.append_project("new_project", "A new project")

        assert project is not None
        assert project.id == 1
        mock_requests.post.assert_called()

    @patch("whatsnext.api.client.server.requests")
    def test_delete_project(self, mock_requests):
        """Test deleting a project."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.delete.return_value.status_code = 204

        server = Server("localhost", 8000)
        result = server.delete_project("test_project")

        assert result is True
        mock_requests.delete.assert_called()

    @patch("whatsnext.api.client.server.requests")
    def test_fetch_job_success(self, mock_requests):
        """Test fetching a job from the queue."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.get.return_value.json.return_value = {
            "job": {"id": 1, "name": "job1"},
            "num_pending": 5,
        }

        server = Server("localhost", 8000)
        project = Project(1, server)

        result = server.fetch_job(project)

        assert result["job"]["id"] == 1
        assert result["num_pending"] == 5

    @patch("whatsnext.api.client.server.requests")
    def test_fetch_job_empty_queue(self, mock_requests):
        """Test fetching from an empty queue."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.get.return_value.json.return_value = {
            "job": None,
            "num_pending": 0,
        }

        server = Server("localhost", 8000)
        project = Project(1, server)

        with pytest.raises(EmptyQueueError):
            server.fetch_job(project)

    @patch("whatsnext.api.client.server.requests")
    def test_fetch_job_with_resources(self, mock_requests):
        """Test fetching a job with resource filters."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.get.return_value.json.return_value = {
            "job": {"id": 1, "name": "job1"},
            "num_pending": 3,
        }

        server = Server("localhost", 8000)
        project = Project(1, server)

        server.fetch_job(project, available_cpu=4, available_accelerators=2)

        # Check that the request included resource parameters
        call_args = mock_requests.get.call_args
        assert call_args[1]["params"]["available_cpu"] == 4
        assert call_args[1]["params"]["available_accelerators"] == 2

    @patch("whatsnext.api.client.server.requests")
    def test_register_client(self, mock_requests):
        """Test client registration."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.post.return_value.status_code = 201

        server = Server("localhost", 8000)
        result = server.register_client(
            client_id="client123",
            name="worker1",
            entity="team1",
            description="Test worker",
            available_cpu=8,
            available_accelerators=2,
        )

        assert result is True
        mock_requests.post.assert_called()
        call_args = mock_requests.post.call_args
        assert call_args[1]["json"]["id"] == "client123"
        assert call_args[1]["json"]["available_cpu"] == 8

    @patch("whatsnext.api.client.server.requests")
    def test_client_heartbeat(self, mock_requests):
        """Test client heartbeat."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.post.return_value.ok = True

        server = Server("localhost", 8000)
        result = server.client_heartbeat("client123")

        assert result is True

    @patch("whatsnext.api.client.server.requests")
    def test_deactivate_client(self, mock_requests):
        """Test client deactivation."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.post.return_value.ok = True

        server = Server("localhost", 8000)
        result = server.deactivate_client("client123")

        assert result is True

    @patch("whatsnext.api.client.server.requests")
    def test_append_queue(self, mock_requests):
        """Test adding a job to the queue."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.get.return_value.ok = True
        mock_requests.get.return_value.json.return_value = {"id": 1}
        mock_requests.post.return_value.status_code = 201

        server = Server("localhost", 8000)
        project = Project(1, server)
        job = Job(name="test_job", task="train", parameters={"lr": 0.01})

        result = server.append_queue(project, job)

        assert result is True

    @patch("whatsnext.api.client.server.requests")
    def test_clear_queue(self, mock_requests):
        """Test clearing the queue."""
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.delete.return_value.ok = True
        mock_requests.delete.return_value.json.return_value = {"deleted": 5}

        server = Server("localhost", 8000)
        project = Project(1, server)

        result = server.clear_queue(project)

        assert result == 5


class TestProjectConnector:
    """Tests for the ProjectConnector class."""

    @patch("whatsnext.api.client.server.requests")
    def test_get_project_data(self, mock_requests):
        """Test fetching project data."""
        mock_server = MagicMock()
        mock_server.base_url = "http://localhost:8000"
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.get.return_value.json.return_value = {
            "id": 1,
            "name": "test",
            "description": "desc",
            "status": "ACTIVE",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        connector = ProjectConnector(mock_server)
        project = MagicMock()
        project.id = 1

        data = connector._get_project_data(project)

        assert data["name"] == "test"
        assert data["status"] == "ACTIVE"


class TestJobConnector:
    """Tests for the JobConnector class."""

    @patch("whatsnext.api.client.server.requests")
    def test_set_status(self, mock_requests):
        """Test setting job status."""
        mock_server = MagicMock()
        mock_server.base_url = "http://localhost:8000"
        mock_requests.get.return_value.raise_for_status = MagicMock()
        mock_requests.get.return_value.json.return_value = {
            "id": 1,
            "name": "job1",
            "project_id": 1,
            "task_id": 1,
            "parameters": {},
            "status": "PENDING",
            "priority": 0,
            "depends": {},
        }
        mock_requests.put.return_value.raise_for_status = MagicMock()

        connector = JobConnector(mock_server)
        job = Job(id=1, name="job1", task="train", parameters={})

        connector.set_status(job, "RUNNING")

        mock_requests.put.assert_called()
        call_args = mock_requests.put.call_args
        assert call_args[1]["json"]["status"] == "RUNNING"
