"""Job dependency resolution and validation utilities."""

from typing import Dict, List, Set

from sqlalchemy.orm import Session

from . import models


def get_dependency_ids(job: models.Job) -> List[int]:
    """Extract dependency job IDs from a job's depends field.

    Args:
        job: The job to get dependencies for.

    Returns:
        List of job IDs that this job depends on.
    """
    if not job.depends:
        return []
    # depends is stored as {str(job_id): job_name}
    return [int(job_id) for job_id in job.depends.keys()]


def are_dependencies_completed(db: Session, job: models.Job) -> bool:
    """Check if all dependencies for a job are completed.

    Args:
        db: Database session.
        job: The job to check dependencies for.

    Returns:
        True if all dependencies are COMPLETED, False otherwise.
    """
    dep_ids = get_dependency_ids(job)
    if not dep_ids:
        return True

    # Query all dependency jobs
    dep_jobs = db.query(models.Job).filter(models.Job.id.in_(dep_ids)).all()

    # All dependencies must exist and be COMPLETED
    if len(dep_jobs) != len(dep_ids):
        return False  # Some dependencies don't exist

    return all(dep.status == models.JobStatus.COMPLETED for dep in dep_jobs)


def has_failed_dependency(db: Session, job: models.Job) -> bool:
    """Check if any dependency for a job has failed.

    Args:
        db: Database session.
        job: The job to check dependencies for.

    Returns:
        True if any dependency is FAILED or BLOCKED, False otherwise.
    """
    dep_ids = get_dependency_ids(job)
    if not dep_ids:
        return False

    # Check if any dependency is FAILED or BLOCKED
    failed_count = (
        db.query(models.Job)
        .filter(
            models.Job.id.in_(dep_ids),
            models.Job.status.in_([models.JobStatus.FAILED, models.JobStatus.BLOCKED]),
        )
        .count()
    )

    return failed_count > 0


def detect_circular_dependency(
    db: Session,
    job_id: int,
    new_depends: Dict[str, str],
    project_id: int,
) -> bool:
    """Detect if adding new dependencies would create a circular dependency.

    Args:
        db: Database session.
        job_id: The ID of the job being updated (0 for new jobs).
        new_depends: The proposed new dependencies {job_id: job_name}.
        project_id: The project ID to scope the check.

    Returns:
        True if a circular dependency would be created, False otherwise.
    """
    if not new_depends:
        return False

    new_dep_ids = {int(dep_id) for dep_id in new_depends.keys()}

    # If we're adding a dependency on ourselves, that's circular
    if job_id in new_dep_ids:
        return True

    # Build the dependency graph for this project
    all_jobs = db.query(models.Job).filter(models.Job.project_id == project_id).all()
    job_deps: Dict[int, Set[int]] = {}

    for job in all_jobs:
        job_deps[job.id] = set(get_dependency_ids(job))

    # Add/update the proposed dependencies
    job_deps[job_id] = new_dep_ids

    # DFS to detect cycles
    visited: Set[int] = set()
    rec_stack: Set[int] = set()

    def has_cycle(node: int) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for dep_id in job_deps.get(node, set()):
            if dep_id not in visited:
                if has_cycle(dep_id):
                    return True
            elif dep_id in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    # Check for cycles starting from the job being updated
    return has_cycle(job_id)


def propagate_failure(db: Session, failed_job: models.Job) -> int:
    """Mark all jobs that depend on a failed job as BLOCKED.

    Args:
        db: Database session.
        failed_job: The job that failed.

    Returns:
        Number of jobs marked as BLOCKED.
    """
    blocked_count = 0
    failed_job_id: int = failed_job.id  # type: ignore[assignment]
    jobs_to_check: List[int] = [failed_job_id]
    processed: Set[int] = set()

    while jobs_to_check:
        current_id = jobs_to_check.pop(0)
        if current_id in processed:
            continue
        processed.add(current_id)

        # Find all PENDING jobs that depend on this job
        dependent_jobs = (
            db.query(models.Job)
            .filter(
                models.Job.project_id == failed_job.project_id,
                models.Job.status == models.JobStatus.PENDING,
            )
            .all()
        )

        for job in dependent_jobs:
            dep_ids = get_dependency_ids(job)
            if current_id in dep_ids:
                # This job depends on the failed job, mark it as BLOCKED
                job.status = models.JobStatus.BLOCKED
                blocked_count += 1
                # Also propagate to jobs that depend on this one
                job_id: int = job.id  # type: ignore[assignment]
                jobs_to_check.append(job_id)

    return blocked_count


def get_jobs_with_completed_dependencies(
    db: Session,
    project_id: int,
    available_cpu: int = 0,
    available_accelerators: int = 0,
) -> List[models.Job]:
    """Get all PENDING jobs whose dependencies are all COMPLETED.

    Args:
        db: Database session.
        project_id: The project to query.
        available_cpu: Filter by CPU requirement (0 = no filter).
        available_accelerators: Filter by accelerator requirement (0 = no filter).

    Returns:
        List of jobs ready to be executed.
    """
    pending_jobs = (
        db.query(models.Job)
        .filter(
            models.Job.project_id == project_id,
            models.Job.status == models.JobStatus.PENDING,
        )
        .order_by(models.Job.priority.desc())
        .all()
    )

    ready_jobs = []
    for job in pending_jobs:
        if are_dependencies_completed(db, job):
            # Check resource requirements if filters are provided
            if available_cpu > 0 or available_accelerators > 0:
                task = db.query(models.Task).filter(models.Task.id == job.task_id).first()
                if task:
                    if available_cpu > 0 and task.required_cpu > available_cpu:
                        continue  # Job requires more CPU than available
                    if available_accelerators > 0 and task.required_accelerators > available_accelerators:
                        continue  # Job requires more accelerators than available
            ready_jobs.append(job)
        elif has_failed_dependency(db, job):
            # Mark as blocked if a dependency failed
            job.status = models.JobStatus.BLOCKED
            db.flush()

    return ready_jobs
