"""Tests for server API endpoints.

Note: These tests require a PostgreSQL database due to the use of PostgreSQL-specific
features (Enum types, now() function, etc.). The tests are marked with the 'server'
marker and will be skipped if the database is not available.

For unit testing without a database, see test_server/test_unit.py.
"""

import pytest

# Skip all tests in this module if fastapi or database is not available
pytest.importorskip("fastapi")


# Mark all tests as requiring server/integration setup
pytestmark = [pytest.mark.server, pytest.mark.integration]


class TestServerAPIDocumentation:
    """Placeholder tests - actual API tests require PostgreSQL.

    These tests verify that the API structure is correct.
    Full integration tests should be run with a PostgreSQL database.
    """

    def test_api_endpoints_documented(self):
        """Verify that API endpoints are properly documented."""
        from whatsnext.api.server.main import app

        # Check that routes exist
        routes = [route.path for route in app.routes if hasattr(route, "path")]

        # Root endpoints
        assert "/" in routes
        assert "/checkdb" in routes

        # Project endpoints
        assert "/projects/" in routes
        assert "/projects/{id}" in routes

        # Job endpoints
        assert "/jobs/" in routes
        assert "/jobs/{id}" in routes

        # Task endpoints
        assert "/tasks/" in routes
        assert "/tasks/{id}" in routes

        # Client endpoints
        assert "/clients/" in routes
        assert "/clients/{id}" in routes
        assert "/clients/register" in routes

    def test_openapi_schema_available(self):
        """Verify that OpenAPI schema is generated."""
        from whatsnext.api.server.main import app

        schema = app.openapi()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

        # Verify key paths exist in schema
        paths = schema["paths"]
        assert "/projects/" in paths
        assert "/jobs/" in paths
        assert "/tasks/" in paths
        assert "/clients/" in paths

    def test_project_endpoints_defined(self):
        """Verify project endpoint methods."""
        from whatsnext.api.server.main import app

        schema = app.openapi()
        paths = schema["paths"]

        # Check /projects/ has GET and POST
        assert "get" in paths["/projects/"]
        assert "post" in paths["/projects/"]

        # Check /projects/{id} has GET, PUT, DELETE
        assert "get" in paths["/projects/{id}"]
        assert "put" in paths["/projects/{id}"]
        assert "delete" in paths["/projects/{id}"]

    def test_job_endpoints_defined(self):
        """Verify job endpoint methods."""
        from whatsnext.api.server.main import app

        schema = app.openapi()
        paths = schema["paths"]

        # Check /jobs/ has GET and POST
        assert "get" in paths["/jobs/"]
        assert "post" in paths["/jobs/"]

        # Check /jobs/{id} has GET, PUT, DELETE
        assert "get" in paths["/jobs/{id}"]
        assert "put" in paths["/jobs/{id}"]
        assert "delete" in paths["/jobs/{id}"]

    def test_task_endpoints_defined(self):
        """Verify task endpoint methods."""
        from whatsnext.api.server.main import app

        schema = app.openapi()
        paths = schema["paths"]

        # Check /tasks/ has GET and POST
        assert "get" in paths["/tasks/"]
        assert "post" in paths["/tasks/"]

    def test_client_endpoints_defined(self):
        """Verify client registration endpoint methods."""
        from whatsnext.api.server.main import app

        schema = app.openapi()
        paths = schema["paths"]

        # Check /clients/register has POST
        assert "post" in paths["/clients/register"]

        # Check /clients/{id} has GET, PUT, DELETE
        assert "get" in paths["/clients/{id}"]
        assert "put" in paths["/clients/{id}"]
        assert "delete" in paths["/clients/{id}"]

    def test_fetch_job_endpoint_has_resource_params(self):
        """Verify fetch_job endpoint accepts resource parameters."""
        from whatsnext.api.server.main import app

        schema = app.openapi()
        paths = schema["paths"]

        # Check /projects/{id}/fetch_job exists and has parameters
        fetch_job_path = paths.get("/projects/{id}/fetch_job")
        assert fetch_job_path is not None
        assert "get" in fetch_job_path

        # Check parameters include resource filters
        params = fetch_job_path["get"].get("parameters", [])
        param_names = [p.get("name") for p in params]
        assert "available_cpu" in param_names
        assert "available_accelerators" in param_names
