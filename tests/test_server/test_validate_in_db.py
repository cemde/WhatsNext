"""Tests for database validation utilities."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from whatsnext.api.server.validate_in_db import (
    validate_project_exists,
    validate_task_in_project_exists,
)


class TestValidateProjectExists:
    """Tests for validate_project_exists function."""

    def test_project_exists(self):
        """Test validation passes when project exists."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "test-project"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = validate_project_exists(mock_db, 1)

        assert result == mock_project

    def test_project_not_found(self):
        """Test validation raises 400 when project doesn't exist."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            validate_project_exists(mock_db, 999)

        assert exc_info.value.status_code == 400
        assert "not found" in exc_info.value.detail


class TestValidateTaskInProjectExists:
    """Tests for validate_task_in_project_exists function."""

    def test_task_exists_in_project(self):
        """Test validation passes when task exists in project."""
        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.project_id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        result = validate_task_in_project_exists(mock_db, 1, 1)

        assert result == mock_task

    def test_task_not_found(self):
        """Test validation raises 400 when task doesn't exist."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            validate_task_in_project_exists(mock_db, 999, 1)

        assert exc_info.value.status_code == 400
        assert "not found" in exc_info.value.detail

    def test_task_in_wrong_project(self):
        """Test validation raises 400 when task is in different project."""
        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.project_id = 2  # Wrong project

        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        with pytest.raises(HTTPException) as exc_info:
            validate_task_in_project_exists(mock_db, 1, 1)  # Expecting project 1

        assert exc_info.value.status_code == 400
        assert "not found" in exc_info.value.detail
