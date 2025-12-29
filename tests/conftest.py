"""Shared pytest fixtures for WhatsNext tests."""

from unittest.mock import MagicMock

import pytest


def pytest_collection_modifyitems(config, items):
    """Automatically apply markers based on test directory."""
    for item in items:
        # Get the path relative to tests/
        path = str(item.fspath)
        if "test_client" in path or "test_cli" in path:
            item.add_marker(pytest.mark.client)
        elif "test_server" in path:
            item.add_marker(pytest.mark.server)
        # test_init.py gets client marker (no server deps)
        elif "test_init.py" in path:
            item.add_marker(pytest.mark.client)


@pytest.fixture
def mock_server():
    """Create a mock Server for testing."""
    server = MagicMock()
    server.base_url = "http://localhost:8000"
    server.hostname = "localhost"
    server.port = 8000
    return server


@pytest.fixture
def mock_project(mock_server):
    """Create a mock Project for testing."""
    from whatsnext.api.client import Project

    project = Project(id=1, _server=mock_server)
    return project


@pytest.fixture
def sample_job_data():
    """Sample job data as returned from server."""
    return {
        "id": 1,
        "name": "test_job",
        "task": "train",
        "parameters": {"lr": 0.01, "epochs": 10},
        "priority": 0,
        "status": "PENDING",
        "depends": {},
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
