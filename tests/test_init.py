"""Tests for the whatsnext package __init__.py."""

import pytest


class TestPackageInit:
    """Tests for the package initialization and lazy imports."""

    def test_job_status_import(self):
        """Test that JobStatus is always available."""
        from whatsnext import JobStatus

        assert JobStatus is not None
        assert hasattr(JobStatus, "PENDING")
        assert hasattr(JobStatus, "COMPLETED")
        assert hasattr(JobStatus, "FAILED")

    def test_project_status_import(self):
        """Test that ProjectStatus is always available."""
        from whatsnext import ProjectStatus

        assert ProjectStatus is not None
        assert hasattr(ProjectStatus, "ACTIVE")
        assert hasattr(ProjectStatus, "ARCHIVED")

    def test_default_status_constants(self):
        """Test that default status constants are available."""
        from whatsnext import DEFAULT_JOB_STATUS, DEFAULT_PROJECT_STATUS

        assert DEFAULT_JOB_STATUS is not None
        assert DEFAULT_PROJECT_STATUS is not None

    def test_lazy_import_client(self):
        """Test lazy import of Client class."""
        from whatsnext import Client

        assert Client is not None

    def test_lazy_import_server(self):
        """Test lazy import of Server class."""
        from whatsnext import Server

        assert Server is not None

    def test_lazy_import_project(self):
        """Test lazy import of Project class."""
        from whatsnext import Project

        assert Project is not None

    def test_lazy_import_job(self):
        """Test lazy import of Job class."""
        from whatsnext import Job

        assert Job is not None

    def test_lazy_import_formatter(self):
        """Test lazy import of Formatter class."""
        from whatsnext import Formatter

        assert Formatter is not None

    def test_lazy_import_resource(self):
        """Test lazy import of Resource class."""
        from whatsnext import Resource

        assert Resource is not None

    def test_lazy_import_empty_queue_error(self):
        """Test lazy import of EmptyQueueError exception."""
        from whatsnext import EmptyQueueError

        assert EmptyQueueError is not None
        assert issubclass(EmptyQueueError, Exception)

    def test_invalid_attribute_error(self):
        """Test that invalid attributes raise AttributeError."""
        import whatsnext

        with pytest.raises(AttributeError) as exc_info:
            _ = whatsnext.NonExistentAttribute

        assert "has no attribute 'NonExistentAttribute'" in str(exc_info.value)
