"""Tests for server routers using FastAPI TestClient with mocked database."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from whatsnext.api.server import models, schemas
from whatsnext.api.server.main import app
from whatsnext.api.server.database import get_db


# Create a mock database session
@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def client(mock_db):
    """Create a test client with mocked database."""
    def override_get_db():
        return mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestProjectRoutes:
    """Tests for project routes."""

    def test_get_project_success(self, client, mock_db):
        """Test getting a project by ID."""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "test-project"
        mock_project.description = "Test description"
        mock_project.status = models.ProjectStatus.ACTIVE
        mock_project.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_project.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        response = client.get("/projects/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "test-project"

    def test_get_project_not_found(self, client, mock_db):
        """Test getting a non-existent project."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/projects/999")

        assert response.status_code == 404

    def test_get_project_by_name_success(self, client, mock_db):
        """Test getting a project by name."""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "test-project"
        mock_project.description = "Test"
        mock_project.status = models.ProjectStatus.ACTIVE
        mock_project.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_project.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        response = client.get("/projects/name/test-project")

        assert response.status_code == 200

    def test_get_project_by_name_not_found(self, client, mock_db):
        """Test getting a non-existent project by name."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/projects/name/nonexistent")

        assert response.status_code == 404

    def test_list_projects(self, client, mock_db):
        """Test listing projects."""
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.name = "project1"
        mock_project1.description = "Desc 1"
        mock_project1.status = models.ProjectStatus.ACTIVE
        mock_project1.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_project1.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.query.return_value.filter.return_value.limit.return_value.offset.return_value.all.return_value = [
            mock_project1
        ]

        response = client.get("/projects/")

        assert response.status_code == 200

    def test_list_projects_invalid_status(self, client, mock_db):
        """Test listing projects with invalid status filter."""
        response = client.get("/projects/?status_filter=INVALID")

        assert response.status_code == 400

    def test_create_project(self, client, mock_db):
        """Test creating a project."""
        def refresh_side_effect(obj):
            obj.id = 1
            obj.name = "new-project"
            obj.description = "New description"
            obj.status = "ACTIVE"
            obj.created_at = datetime(2024, 1, 1, 0, 0, 0)
            obj.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.refresh.side_effect = refresh_side_effect
        mock_db.add.return_value = None
        mock_db.commit.return_value = None

        response = client.post(
            "/projects/",
            json={"name": "new-project", "description": "New description"}
        )

        assert response.status_code == 201

    def test_update_project(self, client, mock_db):
        """Test updating a project."""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "updated"

        mock_query = MagicMock()
        mock_query.first.return_value = mock_project
        mock_query.update.return_value = 1
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.put(
            "/projects/1",
            json={"name": "updated", "description": "Updated desc", "status": "ACTIVE"}
        )

        assert response.status_code == 200

    def test_update_project_not_found(self, client, mock_db):
        """Test updating a non-existent project."""
        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.put(
            "/projects/999",
            json={"name": "updated", "description": "desc", "status": "ACTIVE"}
        )

        assert response.status_code == 404

    def test_delete_project(self, client, mock_db):
        """Test deleting a project."""
        mock_project = MagicMock()
        mock_query = MagicMock()
        mock_query.first.return_value = mock_project
        mock_query.delete.return_value = 1
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.delete("/projects/1")

        assert response.status_code == 204

    def test_delete_project_not_found(self, client, mock_db):
        """Test deleting a non-existent project."""
        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.delete("/projects/999")

        assert response.status_code == 404

    def test_delete_project_by_name(self, client, mock_db):
        """Test deleting a project by name."""
        mock_project = MagicMock()
        mock_query = MagicMock()
        mock_query.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.delete("/projects/name/test-project")

        assert response.status_code == 204

    def test_delete_project_by_name_not_found(self, client, mock_db):
        """Test deleting a non-existent project by name."""
        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.delete("/projects/name/nonexistent")

        assert response.status_code == 404

    def test_clear_project_queue(self, client, mock_db):
        """Test clearing project queue."""
        mock_project = MagicMock()
        mock_project.id = 1

        # Create properly chained mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.filter.return_value.delete.return_value = 5

        response = client.delete("/projects/1/queue")

        assert response.status_code == 200
        # Verify the response has the deleted key
        assert "deleted" in response.json()

    def test_clear_project_queue_not_found(self, client, mock_db):
        """Test clearing queue for non-existent project."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.delete("/projects/999/queue")

        assert response.status_code == 404

    def test_delete_project_job(self, client, mock_db):
        """Test deleting a job from project."""
        mock_job = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        response = client.delete("/projects/1/jobs/1")

        assert response.status_code == 204

    def test_delete_project_job_not_found(self, client, mock_db):
        """Test deleting non-existent job from project."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.delete("/projects/1/jobs/999")

        assert response.status_code == 404

    @patch("whatsnext.api.server.routers.projects.get_jobs_with_completed_dependencies")
    def test_fetch_job_empty(self, mock_get_jobs, client, mock_db):
        """Test fetching job when queue is empty."""
        mock_get_jobs.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0

        response = client.get("/projects/1/fetch_job")

        assert response.status_code == 200
        data = response.json()
        assert data["job"] is None
        assert data["num_pending"] == 0

    @patch("whatsnext.api.server.routers.projects.get_jobs_with_completed_dependencies")
    def test_fetch_job_success(self, mock_get_jobs, client, mock_db):
        """Test fetching a job successfully."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "test-job"
        mock_job.project_id = 1
        mock_job.task_id = 1
        mock_job.parameters = {}
        mock_job.status = models.JobStatus.PENDING
        mock_job.priority = 0
        mock_job.depends = {}
        mock_job.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_job.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_task = MagicMock()
        mock_task.name = "train"

        mock_get_jobs.return_value = [mock_job]
        mock_db.query.return_value.filter.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task
        mock_db.query.return_value.filter.return_value.update.return_value = 1

        response = client.get("/projects/1/fetch_job")

        assert response.status_code == 200

    def test_add_jobs_batch(self, client, mock_db):
        """Test adding batch of jobs."""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        job_id_counter = [0]

        def add_side_effect(obj):
            job_id_counter[0] += 1
            obj.id = job_id_counter[0]

        mock_db.add.side_effect = add_side_effect

        response = client.post(
            "/projects/1/jobs/batch",
            json={
                "jobs": [
                    {"name": "job1", "task_id": 1, "parameters": {}, "priority": 0, "depends": {}},
                    {"name": "job2", "task_id": 1, "parameters": {}, "priority": 0, "depends": {}}
                ]
            }
        )

        assert response.status_code == 201

    def test_add_jobs_batch_project_not_found(self, client, mock_db):
        """Test adding batch to non-existent project."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.post(
            "/projects/999/jobs/batch",
            json={"jobs": [{"name": "job1", "task_id": 1, "parameters": {}}]}
        )

        assert response.status_code == 404


class TestJobRoutes:
    """Tests for job routes."""

    def test_get_job_success(self, client, mock_db):
        """Test getting a job by ID."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "test-job"
        mock_job.project_id = 1
        mock_job.task_id = 1
        mock_job.parameters = {"lr": 0.01}
        mock_job.status = models.JobStatus.PENDING
        mock_job.priority = 5
        mock_job.depends = {}
        mock_job.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_job.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        response = client.get("/jobs/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_get_job_not_found(self, client, mock_db):
        """Test getting a non-existent job."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/jobs/999")

        assert response.status_code == 404

    def test_list_jobs_with_filter(self, client, mock_db):
        """Test listing jobs with project filter."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "job1"
        mock_job.project_id = 1
        mock_job.task_id = 1
        mock_job.parameters = {}
        mock_job.status = models.JobStatus.PENDING
        mock_job.priority = 0
        mock_job.depends = {}
        mock_job.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_job.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.query.return_value.filter.return_value.limit.return_value.offset.return_value.all.return_value = [mock_job]

        response = client.get("/jobs/?project_id=1")

        assert response.status_code == 200

    def test_list_jobs_without_filter(self, client, mock_db):
        """Test listing jobs without project filter."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "job1"
        mock_job.project_id = 1
        mock_job.task_id = 1
        mock_job.parameters = {}
        mock_job.status = models.JobStatus.PENDING
        mock_job.priority = 0
        mock_job.depends = {}
        mock_job.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_job.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.query.return_value.limit.return_value.offset.return_value.all.return_value = [mock_job]

        response = client.get("/jobs/")

        assert response.status_code == 200

    @patch("whatsnext.api.server.routers.jobs.validate_project_exists")
    @patch("whatsnext.api.server.routers.jobs.validate_task_in_project_exists")
    @patch("whatsnext.api.server.routers.jobs.detect_circular_dependency")
    def test_create_job(self, mock_detect, mock_validate_task, mock_validate_project, client, mock_db):
        """Test creating a job."""
        mock_validate_project.return_value = MagicMock()
        mock_validate_task.return_value = MagicMock()
        mock_detect.return_value = False

        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "new-job"
        mock_job.project_id = 1
        mock_job.task_id = 1
        mock_job.parameters = {}
        mock_job.status = models.JobStatus.PENDING
        mock_job.priority = 0
        mock_job.depends = {}
        mock_job.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_job.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        def set_id_on_refresh(obj):
            obj.id = 1
            obj.created_at = datetime(2024, 1, 1, 0, 0, 0)
            obj.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.refresh.side_effect = set_id_on_refresh

        response = client.post(
            "/jobs/",
            json={
                "name": "new-job",
                "project_id": 1,
                "task_id": 1,
                "parameters": {},
                "status": "PENDING",
                "priority": 0,
                "depends": {}
            }
        )

        assert response.status_code == 201

    @patch("whatsnext.api.server.routers.jobs.validate_project_exists")
    @patch("whatsnext.api.server.routers.jobs.validate_task_in_project_exists")
    @patch("whatsnext.api.server.routers.jobs.detect_circular_dependency")
    def test_create_job_circular_dep(self, mock_detect, mock_validate_task, mock_validate_project, client, mock_db):
        """Test creating a job with circular dependency."""
        mock_validate_project.return_value = MagicMock()
        mock_validate_task.return_value = MagicMock()
        mock_detect.return_value = True  # Circular dependency detected

        response = client.post(
            "/jobs/",
            json={
                "name": "new-job",
                "project_id": 1,
                "task_id": 1,
                "parameters": {},
                "status": "PENDING",
                "priority": 0,
                "depends": {"1": "other-job"}
            }
        )

        assert response.status_code == 400
        assert "Circular dependency" in response.json()["detail"]

    @patch("whatsnext.api.server.routers.jobs.validate_project_exists")
    @patch("whatsnext.api.server.routers.jobs.detect_circular_dependency")
    def test_update_job(self, mock_detect, mock_validate_project, client, mock_db):
        """Test updating a job."""
        mock_validate_project.return_value = MagicMock()
        mock_detect.return_value = False

        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.status = models.JobStatus.PENDING

        mock_query = MagicMock()
        mock_query.first.return_value = mock_job
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.put(
            "/jobs/1",
            json={
                "name": "updated-job",
                "project_id": 1,
                "task_id": 1,
                "parameters": {},
                "status": "RUNNING",
                "priority": 10,
                "depends": {}
            }
        )

        assert response.status_code == 200

    @patch("whatsnext.api.server.routers.jobs.validate_project_exists")
    def test_update_job_not_found(self, mock_validate_project, client, mock_db):
        """Test updating a non-existent job."""
        mock_validate_project.return_value = MagicMock()

        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.put(
            "/jobs/999",
            json={
                "name": "updated",
                "project_id": 1,
                "task_id": 1,
                "parameters": {},
                "status": "PENDING",
                "priority": 0,
                "depends": {}
            }
        )

        assert response.status_code == 404

    @patch("whatsnext.api.server.routers.jobs.validate_project_exists")
    @patch("whatsnext.api.server.routers.jobs.detect_circular_dependency")
    def test_update_job_to_failed_status(self, mock_detect, mock_validate_project, client, mock_db):
        """Test updating a job to FAILED status."""
        mock_validate_project.return_value = MagicMock()
        mock_detect.return_value = False

        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "failed-job"
        mock_job.project_id = 1
        mock_job.task_id = 1
        mock_job.parameters = {}
        mock_job.status = models.JobStatus.RUNNING  # Old status
        mock_job.priority = 0
        mock_job.depends = {}
        mock_job.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_job.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_query = MagicMock()
        mock_query.first.return_value = mock_job
        mock_query.update.return_value = 1
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.put(
            "/jobs/1",
            json={
                "name": "failed-job",
                "project_id": 1,
                "task_id": 1,
                "parameters": {},
                "status": "FAILED",
                "priority": 0,
                "depends": {}
            }
        )

        assert response.status_code == 200

    @patch("whatsnext.api.server.routers.jobs.get_dependency_ids")
    @patch("whatsnext.api.server.routers.jobs.are_dependencies_completed")
    @patch("whatsnext.api.server.routers.jobs.has_failed_dependency")
    def test_get_job_dependencies(self, mock_has_failed, mock_are_completed, mock_get_deps, client, mock_db):
        """Test getting job dependencies."""
        mock_get_deps.return_value = [2, 3]
        mock_are_completed.return_value = True
        mock_has_failed.return_value = False

        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "test-job"
        mock_job.status = models.JobStatus.PENDING

        mock_dep1 = MagicMock()
        mock_dep1.id = 2
        mock_dep1.name = "dep1"
        mock_dep1.status = models.JobStatus.COMPLETED

        mock_dep2 = MagicMock()
        mock_dep2.id = 3
        mock_dep2.name = "dep2"
        mock_dep2.status = models.JobStatus.COMPLETED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_dep1, mock_dep2]

        response = client.get("/jobs/1/dependencies")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == 1
        assert data["all_completed"] is True

    @patch("whatsnext.api.server.routers.jobs.get_dependency_ids")
    @patch("whatsnext.api.server.routers.jobs.are_dependencies_completed")
    @patch("whatsnext.api.server.routers.jobs.has_failed_dependency")
    def test_get_job_dependencies_empty(self, mock_has_failed, mock_are_completed, mock_get_deps, client, mock_db):
        """Test getting job dependencies when none exist."""
        mock_get_deps.return_value = []
        mock_are_completed.return_value = True
        mock_has_failed.return_value = False

        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "test-job"
        mock_job.status = models.JobStatus.PENDING

        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        response = client.get("/jobs/1/dependencies")

        assert response.status_code == 200
        data = response.json()
        assert len(data["dependencies"]) == 0

    def test_get_job_dependencies_not_found(self, client, mock_db):
        """Test getting dependencies for non-existent job."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/jobs/999/dependencies")

        assert response.status_code == 404

    def test_delete_job(self, client, mock_db):
        """Test deleting a job."""
        mock_job = MagicMock()
        mock_query = MagicMock()
        mock_query.first.return_value = mock_job
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.delete("/jobs/1")

        assert response.status_code == 204

    def test_delete_job_not_found(self, client, mock_db):
        """Test deleting a non-existent job."""
        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.delete("/jobs/999")

        assert response.status_code == 404


class TestTaskRoutes:
    """Tests for task routes."""

    def test_get_task_success(self, client, mock_db):
        """Test getting a task by ID."""
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.name = "train"
        mock_task.project_id = 1
        mock_task.command_template = None
        mock_task.required_cpu = 4
        mock_task.required_accelerators = 1
        mock_task.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_task.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        response = client.get("/tasks/1")

        assert response.status_code == 200

    def test_get_task_not_found(self, client, mock_db):
        """Test getting a non-existent task."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/tasks/999")

        assert response.status_code == 404

    def test_get_task_by_name(self, client, mock_db):
        """Test getting a task by name."""
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.name = "train"
        mock_task.project_id = 1
        mock_task.command_template = None
        mock_task.required_cpu = 4
        mock_task.required_accelerators = 1
        mock_task.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_task.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_task

        response = client.get("/tasks/name/train?project_id=1")

        assert response.status_code == 200

    def test_get_task_by_name_not_found(self, client, mock_db):
        """Test getting a non-existent task by name."""
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        response = client.get("/tasks/name/nonexistent?project_id=1")

        assert response.status_code == 404

    def test_list_tasks(self, client, mock_db):
        """Test listing tasks."""
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.name = "task1"
        mock_task.project_id = 1
        mock_task.command_template = None
        mock_task.required_cpu = 1
        mock_task.required_accelerators = 0
        mock_task.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_task.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.query.return_value.filter.return_value.limit.return_value.offset.return_value.all.return_value = [mock_task]

        response = client.get("/tasks/?project_id=1")

        assert response.status_code == 200

    def test_create_task(self, client, mock_db):
        """Test creating a task."""
        def refresh_side_effect(obj):
            obj.id = 1
            obj.name = "new-task"
            obj.project_id = 1
            obj.command_template = None
            obj.required_cpu = 1
            obj.required_accelerators = 0
            obj.created_at = datetime(2024, 1, 1, 0, 0, 0)
            obj.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = refresh_side_effect

        response = client.post(
            "/tasks/",
            json={"name": "new-task", "project_id": 1}
        )

        assert response.status_code == 201

    def test_update_task(self, client, mock_db):
        """Test updating a task."""
        mock_task = MagicMock()
        mock_query = MagicMock()
        mock_query.first.return_value = mock_task
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.put(
            "/tasks/1",
            json={"name": "updated-task", "project_id": 1, "required_cpu": 8}
        )

        assert response.status_code == 200

    def test_update_task_not_found(self, client, mock_db):
        """Test updating a non-existent task."""
        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.put(
            "/tasks/999",
            json={"name": "updated", "project_id": 1}
        )

        assert response.status_code == 404

    def test_delete_task(self, client, mock_db):
        """Test deleting a task."""
        mock_task = MagicMock()
        mock_query = MagicMock()
        mock_query.first.return_value = mock_task
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.delete("/tasks/1")

        assert response.status_code == 204

    def test_delete_task_not_found(self, client, mock_db):
        """Test deleting a non-existent task."""
        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.delete("/tasks/999")

        assert response.status_code == 404


class TestClientRoutes:
    """Tests for client routes."""

    def test_get_client_success(self, client, mock_db):
        """Test getting a client by ID."""
        mock_client = MagicMock()
        mock_client.id = "client-123"
        mock_client.name = "worker1"
        mock_client.entity = "team1"
        mock_client.description = "Test worker"
        mock_client.is_active = 1
        mock_client.available_cpu = 8
        mock_client.available_accelerators = 2
        mock_client.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_client.last_heartbeat = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        response = client.get("/clients/client-123")

        assert response.status_code == 200

    def test_get_client_not_found(self, client, mock_db):
        """Test getting a non-existent client."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/clients/nonexistent")

        assert response.status_code == 404

    def test_list_clients(self, client, mock_db):
        """Test listing clients."""
        mock_client = MagicMock()
        mock_client.id = "client-1"
        mock_client.name = "worker"
        mock_client.entity = "team"
        mock_client.description = ""
        mock_client.is_active = 1
        mock_client.available_cpu = 4
        mock_client.available_accelerators = 0
        mock_client.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_client.last_heartbeat = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.query.return_value.limit.return_value.offset.return_value.all.return_value = [mock_client]

        response = client.get("/clients/")

        assert response.status_code == 200

    def test_register_client(self, client, mock_db):
        """Test registering a client."""
        def refresh_side_effect(obj):
            obj.id = "new-client"
            obj.name = "worker1"
            obj.entity = "team1"
            obj.description = "New worker"
            obj.available_cpu = 8
            obj.available_accelerators = 2
            obj.is_active = 1
            obj.created_at = datetime(2024, 1, 1, 0, 0, 0)
            obj.last_heartbeat = datetime(2024, 1, 1, 0, 0, 0)

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = refresh_side_effect

        response = client.post(
            "/clients/register",
            json={
                "id": "new-client",
                "name": "worker1",
                "entity": "team1",
                "description": "New worker",
                "available_cpu": 8,
                "available_accelerators": 2
            }
        )

        assert response.status_code == 201

    def test_update_client(self, client, mock_db):
        """Test updating a client."""
        mock_client_obj = MagicMock()
        mock_query = MagicMock()
        mock_query.first.return_value = mock_client_obj
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.put(
            "/clients/client-123",
            json={"available_cpu": 16}
        )

        assert response.status_code == 200

    def test_update_client_not_found(self, client, mock_db):
        """Test updating a non-existent client."""
        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.put(
            "/clients/nonexistent",
            json={"available_cpu": 8}
        )

        assert response.status_code == 404

    def test_delete_client(self, client, mock_db):
        """Test deleting a client."""
        mock_client_obj = MagicMock()
        mock_query = MagicMock()
        mock_query.first.return_value = mock_client_obj
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.delete("/clients/client-123")

        assert response.status_code == 204

    def test_delete_client_not_found(self, client, mock_db):
        """Test deleting a non-existent client."""
        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.delete("/clients/nonexistent")

        assert response.status_code == 404

    def test_client_heartbeat(self, client, mock_db):
        """Test client heartbeat."""
        mock_client_obj = MagicMock()
        mock_query = MagicMock()
        mock_query.first.return_value = mock_client_obj
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.post("/clients/client-123/heartbeat")

        assert response.status_code == 200

    def test_client_heartbeat_not_found(self, client, mock_db):
        """Test heartbeat for non-existent client."""
        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.post("/clients/nonexistent/heartbeat")

        assert response.status_code == 404

    def test_deactivate_client(self, client, mock_db):
        """Test deactivating a client."""
        mock_client_obj = MagicMock()
        mock_query = MagicMock()
        mock_query.first.return_value = mock_client_obj
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.post("/clients/client-123/deactivate")

        assert response.status_code == 200

    def test_deactivate_client_not_found(self, client, mock_db):
        """Test deactivating a non-existent client."""
        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query

        response = client.post("/clients/nonexistent/deactivate")

        assert response.status_code == 404
