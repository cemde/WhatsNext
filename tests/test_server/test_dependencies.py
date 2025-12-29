"""Tests for server dependency resolution utilities."""

from unittest.mock import MagicMock, patch

import pytest

from whatsnext.api.server.dependencies import (
    get_dependency_ids,
    are_dependencies_completed,
    has_failed_dependency,
    detect_circular_dependency,
    propagate_failure,
    get_jobs_with_completed_dependencies,
)
from whatsnext.api.server.models import JobStatus


class TestGetDependencyIds:
    """Tests for get_dependency_ids function."""

    def test_no_dependencies(self):
        """Test job with no dependencies."""
        job = MagicMock()
        job.depends = None

        result = get_dependency_ids(job)

        assert result == []

    def test_empty_dependencies(self):
        """Test job with empty dependencies dict."""
        job = MagicMock()
        job.depends = {}

        result = get_dependency_ids(job)

        assert result == []

    def test_with_dependencies(self):
        """Test job with dependencies."""
        job = MagicMock()
        job.depends = {"1": "job-a", "2": "job-b", "3": "job-c"}

        result = get_dependency_ids(job)

        assert sorted(result) == [1, 2, 3]


class TestAreDependenciesCompleted:
    """Tests for are_dependencies_completed function."""

    def test_no_dependencies(self):
        """Test job with no dependencies returns True."""
        mock_db = MagicMock()
        job = MagicMock()
        job.depends = None

        result = are_dependencies_completed(mock_db, job)

        assert result is True

    def test_all_completed(self):
        """Test all dependencies completed."""
        mock_db = MagicMock()
        job = MagicMock()
        job.depends = {"1": "job-a", "2": "job-b"}

        dep1 = MagicMock()
        dep1.status = JobStatus.COMPLETED
        dep2 = MagicMock()
        dep2.status = JobStatus.COMPLETED

        mock_db.query.return_value.filter.return_value.all.return_value = [dep1, dep2]

        result = are_dependencies_completed(mock_db, job)

        assert result is True

    def test_some_not_completed(self):
        """Test some dependencies not completed."""
        mock_db = MagicMock()
        job = MagicMock()
        job.depends = {"1": "job-a", "2": "job-b"}

        dep1 = MagicMock()
        dep1.status = JobStatus.COMPLETED
        dep2 = MagicMock()
        dep2.status = JobStatus.RUNNING

        mock_db.query.return_value.filter.return_value.all.return_value = [dep1, dep2]

        result = are_dependencies_completed(mock_db, job)

        assert result is False

    def test_missing_dependencies(self):
        """Test some dependencies don't exist in DB."""
        mock_db = MagicMock()
        job = MagicMock()
        job.depends = {"1": "job-a", "2": "job-b", "3": "job-c"}

        # Only 2 deps returned from DB
        dep1 = MagicMock()
        dep1.status = JobStatus.COMPLETED
        dep2 = MagicMock()
        dep2.status = JobStatus.COMPLETED

        mock_db.query.return_value.filter.return_value.all.return_value = [dep1, dep2]

        result = are_dependencies_completed(mock_db, job)

        assert result is False


class TestHasFailedDependency:
    """Tests for has_failed_dependency function."""

    def test_no_dependencies(self):
        """Test job with no dependencies returns False."""
        mock_db = MagicMock()
        job = MagicMock()
        job.depends = None

        result = has_failed_dependency(mock_db, job)

        assert result is False

    def test_no_failed(self):
        """Test no failed dependencies."""
        mock_db = MagicMock()
        job = MagicMock()
        job.depends = {"1": "job-a"}

        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = has_failed_dependency(mock_db, job)

        assert result is False

    def test_has_failed(self):
        """Test has failed dependency."""
        mock_db = MagicMock()
        job = MagicMock()
        job.depends = {"1": "job-a", "2": "job-b"}

        mock_db.query.return_value.filter.return_value.count.return_value = 1

        result = has_failed_dependency(mock_db, job)

        assert result is True


class TestDetectCircularDependency:
    """Tests for detect_circular_dependency function."""

    def test_no_dependencies(self):
        """Test no circular dependency when no deps."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = detect_circular_dependency(mock_db, 1, {}, 1)

        assert result is False

    def test_self_dependency(self):
        """Test self-dependency is detected as circular."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = detect_circular_dependency(mock_db, 1, {"1": "self"}, 1)

        assert result is True

    def test_simple_chain_no_cycle(self):
        """Test simple dependency chain without cycle."""
        mock_db = MagicMock()

        # Job 1 -> Job 2 -> Job 3 (no cycle)
        job1 = MagicMock()
        job1.id = 1
        job1.depends = {}

        job2 = MagicMock()
        job2.id = 2
        job2.depends = {"1": "job1"}

        job3 = MagicMock()
        job3.id = 3
        job3.depends = {"2": "job2"}

        mock_db.query.return_value.filter.return_value.all.return_value = [job1, job2, job3]

        # Adding job4 that depends on job3
        result = detect_circular_dependency(mock_db, 4, {"3": "job3"}, 1)

        assert result is False

    def test_cycle_detected(self):
        """Test cycle is detected."""
        mock_db = MagicMock()

        # Job 1 -> Job 2, and we want to add Job 2 -> Job 1 (cycle)
        job1 = MagicMock()
        job1.id = 1
        job1.depends = {}

        job2 = MagicMock()
        job2.id = 2
        job2.depends = {"1": "job1"}

        mock_db.query.return_value.filter.return_value.all.return_value = [job1, job2]

        # Try to make job1 depend on job2 (creates cycle)
        result = detect_circular_dependency(mock_db, 1, {"2": "job2"}, 1)

        assert result is True


class TestPropagateFailure:
    """Tests for propagate_failure function."""

    def test_no_dependent_jobs(self):
        """Test no jobs depend on failed job."""
        mock_db = MagicMock()
        failed_job = MagicMock()
        failed_job.id = 1
        failed_job.project_id = 1

        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = propagate_failure(mock_db, failed_job)

        assert result == 0

    def test_blocks_dependent_jobs(self):
        """Test dependent jobs are blocked."""
        mock_db = MagicMock()
        failed_job = MagicMock()
        failed_job.id = 1
        failed_job.project_id = 1

        dependent_job = MagicMock()
        dependent_job.id = 2
        dependent_job.depends = {"1": "failed-job"}
        dependent_job.status = JobStatus.PENDING

        # First iteration finds dependent_job, second returns empty
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [dependent_job],
            []
        ]

        result = propagate_failure(mock_db, failed_job)

        assert result == 1
        assert dependent_job.status == JobStatus.BLOCKED


class TestGetJobsWithCompletedDependencies:
    """Tests for get_jobs_with_completed_dependencies function."""

    def test_no_pending_jobs(self):
        """Test no pending jobs."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_jobs_with_completed_dependencies(mock_db, 1)

        assert result == []

    def test_job_with_no_deps(self):
        """Test job with no dependencies is returned."""
        mock_db = MagicMock()

        job = MagicMock()
        job.depends = None
        job.status = JobStatus.PENDING

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [job]

        result = get_jobs_with_completed_dependencies(mock_db, 1)

        assert job in result

    def test_job_with_completed_deps(self):
        """Test job with completed dependencies is returned."""
        mock_db = MagicMock()

        job = MagicMock()
        job.depends = {"1": "prereq"}
        job.status = JobStatus.PENDING

        prereq = MagicMock()
        prereq.status = JobStatus.COMPLETED

        # For pending jobs query
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [job]
        # For dependency check
        mock_db.query.return_value.filter.return_value.all.return_value = [prereq]
        # For failed dependency check
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = get_jobs_with_completed_dependencies(mock_db, 1)

        assert job in result

    def test_job_with_resource_filtering(self):
        """Test job filtering by resources."""
        mock_db = MagicMock()

        job = MagicMock()
        job.depends = None
        job.task_id = 1
        job.status = JobStatus.PENDING

        task = MagicMock()
        task.required_cpu = 4
        task.required_accelerators = 1

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [job]
        mock_db.query.return_value.filter.return_value.first.return_value = task

        # Client has 2 CPUs - not enough
        result = get_jobs_with_completed_dependencies(mock_db, 1, available_cpu=2)

        assert job not in result

    def test_job_with_sufficient_resources(self):
        """Test job passes resource filtering."""
        mock_db = MagicMock()

        job = MagicMock()
        job.depends = None
        job.task_id = 1
        job.status = JobStatus.PENDING

        task = MagicMock()
        task.required_cpu = 4
        task.required_accelerators = 1

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [job]
        mock_db.query.return_value.filter.return_value.first.return_value = task

        # Client has 8 CPUs - enough
        result = get_jobs_with_completed_dependencies(mock_db, 1, available_cpu=8, available_accelerators=2)

        assert job in result

    def test_job_blocked_on_failed_dependency(self):
        """Test job with failed dependency is blocked."""
        mock_db = MagicMock()

        job = MagicMock()
        job.depends = {"1": "failed-job"}
        job.status = JobStatus.PENDING

        prereq = MagicMock()
        prereq.status = JobStatus.FAILED

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [job]
        mock_db.query.return_value.filter.return_value.all.return_value = [prereq]
        mock_db.query.return_value.filter.return_value.count.return_value = 1

        result = get_jobs_with_completed_dependencies(mock_db, 1)

        assert job not in result
        assert job.status == JobStatus.BLOCKED
