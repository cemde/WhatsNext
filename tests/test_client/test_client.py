"""Tests for the Client class."""

import signal
from unittest.mock import MagicMock

from whatsnext.api.client.client import Client
from whatsnext.api.client.exceptions import EmptyQueueError
from whatsnext.api.client.formatter import CLIFormatter
from whatsnext.api.client.resource import Resource


class TestClientInit:
    """Tests for Client initialization."""

    def test_client_init_basic(self):
        """Test basic client initialization without server registration."""
        mock_project = MagicMock()
        mock_project._server = None
        formatter = CLIFormatter()

        client = Client(
            entity="test-entity",
            name="test-client",
            description="Test client",
            project=mock_project,
            formatter=formatter,
            register_with_server=False,
        )

        assert client.entity == "test-entity"
        assert client.name == "test-client"
        assert client.description == "Test client"
        assert client.project == mock_project
        assert client.formatter == formatter
        assert client.available_cpu == 1
        assert client.available_accelerators == 0
        assert client._shutdown_requested is False
        assert client._registered is False
        assert len(client.active_resources) == 0
        assert client.id is not None

    def test_client_init_with_resources(self):
        """Test client initialization with custom resources."""
        mock_project = MagicMock()
        mock_project._server = None
        formatter = CLIFormatter()

        client = Client(
            entity="ml-team",
            name="gpu-worker",
            description="GPU worker",
            project=mock_project,
            formatter=formatter,
            available_cpu=16,
            available_accelerators=4,
            register_with_server=False,
        )

        assert client.available_cpu == 16
        assert client.available_accelerators == 4

    def test_client_init_with_registration(self):
        """Test client initialization with server registration."""
        mock_project = MagicMock()
        mock_server = MagicMock()
        mock_server.register_client.return_value = True
        mock_project._server = mock_server
        formatter = CLIFormatter()

        client = Client(
            entity="ml-team", name="worker", description="Worker", project=mock_project, formatter=formatter, register_with_server=True
        )

        assert client._registered is True
        mock_server.register_client.assert_called_once()

    def test_client_init_registration_failure(self):
        """Test client initialization when registration fails."""
        mock_project = MagicMock()
        mock_server = MagicMock()
        mock_server.register_client.return_value = False
        mock_project._server = mock_server
        formatter = CLIFormatter()

        client = Client(
            entity="ml-team", name="worker", description="Worker", project=mock_project, formatter=formatter, register_with_server=True
        )

        assert client._registered is False

    def test_client_init_no_server(self):
        """Test client registration when project has no server."""
        mock_project = MagicMock()
        mock_project._server = None
        formatter = CLIFormatter()

        client = Client(
            entity="ml-team",
            name="worker",
            description="Worker",
            project=mock_project,
            formatter=formatter,
            register_with_server=True,  # Will be skipped since no server
        )

        assert client._registered is False


class TestClientResourceManagement:
    """Tests for Client resource management."""

    def test_allocate_resource(self):
        """Test resource allocation."""
        mock_project = MagicMock()
        mock_project._server = None
        formatter = CLIFormatter()

        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        resource = client.allocate_resource(cpu=4, accelerator=["0", "1"])

        assert isinstance(resource, Resource)
        assert resource.cpus == 4
        assert resource.accelerator == ["0", "1"]
        assert resource.client == client
        assert resource in client.active_resources

    def test_free_resource(self):
        """Test resource freeing."""
        mock_project = MagicMock()
        mock_project._server = None
        formatter = CLIFormatter()

        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        resource = client.allocate_resource(cpu=4, accelerator=[])
        assert len(client.active_resources) == 1

        client.free_resource(resource)
        assert len(client.active_resources) == 0


class TestClientWork:
    """Tests for Client work loop."""

    def test_work_single_job(self):
        """Test work loop processing single job."""
        mock_project = MagicMock()
        mock_project._server = None
        mock_project.id = 1

        # Create a mock job that succeeds
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "test-job"
        mock_job.run.return_value = 0

        # First call returns job, second raises EmptyQueueError
        mock_project.fetch_job.side_effect = [mock_job, EmptyQueueError("No jobs")]

        formatter = CLIFormatter()
        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        jobs_done = client.work()

        assert jobs_done == 1
        mock_job.run.assert_called_once()

    def test_work_multiple_jobs(self):
        """Test work loop processing multiple jobs."""
        mock_project = MagicMock()
        mock_project._server = None
        mock_project.id = 1

        mock_jobs = []
        for i in range(3):
            job = MagicMock()
            job.id = i + 1
            job.name = f"job-{i}"
            job.run.return_value = 0
            mock_jobs.append(job)

        mock_project.fetch_job.side_effect = mock_jobs + [EmptyQueueError("No jobs")]

        formatter = CLIFormatter()
        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        jobs_done = client.work()

        assert jobs_done == 3

    def test_work_job_failure(self):
        """Test work loop with job failure."""
        mock_project = MagicMock()
        mock_project._server = None
        mock_project.id = 1

        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "failing-job"
        mock_job.run.return_value = 1  # Non-zero exit code

        mock_project.fetch_job.side_effect = [mock_job, EmptyQueueError("No jobs")]

        formatter = CLIFormatter()
        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        jobs_done = client.work()

        assert jobs_done == 1  # Job was processed even though it failed

    def test_work_empty_queue(self):
        """Test work loop with empty queue."""
        mock_project = MagicMock()
        mock_project._server = None
        mock_project.id = 1
        mock_project.fetch_job.side_effect = EmptyQueueError("No jobs")

        formatter = CLIFormatter()
        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        jobs_done = client.work()

        assert jobs_done == 0

    def test_work_with_resource_filter(self):
        """Test work loop with resource filtering."""
        mock_project = MagicMock()
        mock_project._server = None
        mock_project.id = 1
        mock_project.fetch_job.side_effect = EmptyQueueError("No jobs")

        formatter = CLIFormatter()
        client = Client(
            entity="test",
            name="client",
            description="test",
            project=mock_project,
            formatter=formatter,
            available_cpu=8,
            available_accelerators=2,
            register_with_server=False,
        )

        client.work(use_resource_filter=True)

        mock_project.fetch_job.assert_called_with(available_cpu=8, available_accelerators=2)

    def test_work_without_resource_filter(self):
        """Test work loop without resource filtering."""
        mock_project = MagicMock()
        mock_project._server = None
        mock_project.id = 1
        mock_project.fetch_job.side_effect = EmptyQueueError("No jobs")

        formatter = CLIFormatter()
        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        client.work(use_resource_filter=False)

        mock_project.fetch_job.assert_called_with()

    def test_work_with_provided_resource(self):
        """Test work loop with externally provided resource."""
        mock_project = MagicMock()
        mock_project._server = None
        mock_project.id = 1
        mock_project.fetch_job.side_effect = EmptyQueueError("No jobs")

        formatter = CLIFormatter()
        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        external_resource = Resource(cpu=2, accelerator=[], client=client)
        client.work(resource=external_resource)

        # Resource should have been marked inactive
        assert external_resource._status == "inactive"

    def test_work_exception_handling(self):
        """Test work loop handles exceptions gracefully."""
        mock_project = MagicMock()
        mock_project._server = None
        mock_project.id = 1

        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "error-job"
        mock_job.run.side_effect = Exception("Unexpected error")

        mock_project.fetch_job.side_effect = [mock_job, EmptyQueueError("No jobs")]

        formatter = CLIFormatter()
        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        # Should not raise, just exit cleanly
        jobs_done = client.work()
        assert jobs_done == 0  # Job wasn't counted as executed due to exception

    def test_work_deactivates_client(self):
        """Test that work deactivates registered client on completion."""
        mock_project = MagicMock()
        mock_server = MagicMock()
        mock_server.register_client.return_value = True
        mock_server.deactivate_client.return_value = True
        mock_project._server = mock_server
        mock_project.id = 1
        mock_project.fetch_job.side_effect = EmptyQueueError("No jobs")

        formatter = CLIFormatter()
        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=True)

        client.work()

        mock_server.deactivate_client.assert_called_once_with(client.id)


class TestClientSignalHandling:
    """Tests for Client signal handling."""

    def test_signal_handler(self):
        """Test signal handler sets shutdown flag."""
        mock_project = MagicMock()
        mock_project._server = None
        formatter = CLIFormatter()

        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        assert client._shutdown_requested is False

        # Simulate signal
        client._signal_handler(signal.SIGINT, None)

        assert client._shutdown_requested is True

    def test_stop_method(self):
        """Test stop method sets shutdown flag."""
        mock_project = MagicMock()
        mock_project._server = None
        formatter = CLIFormatter()

        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        assert client._shutdown_requested is False

        client.stop()

        assert client._shutdown_requested is True


class TestClientDeactivation:
    """Tests for Client deactivation."""

    def test_deactivate_registered_client(self):
        """Test deactivating a registered client."""
        mock_project = MagicMock()
        mock_server = MagicMock()
        mock_server.register_client.return_value = True
        mock_server.deactivate_client.return_value = True
        mock_project._server = mock_server

        formatter = CLIFormatter()
        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=True)

        assert client._registered is True

        client._deactivate()

        assert client._registered is False
        mock_server.deactivate_client.assert_called_once_with(client.id)

    def test_deactivate_unregistered_client(self):
        """Test deactivating an unregistered client does nothing."""
        mock_project = MagicMock()
        mock_project._server = None

        formatter = CLIFormatter()
        client = Client(entity="test", name="client", description="test", project=mock_project, formatter=formatter, register_with_server=False)

        # Should not raise
        client._deactivate()

        assert client._registered is False
