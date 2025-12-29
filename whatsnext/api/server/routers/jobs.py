from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import (
    are_dependencies_completed,
    detect_circular_dependency,
    get_dependency_ids,
    has_failed_dependency,
    propagate_failure,
)
from ..validate_in_db import validate_project_exists, validate_task_in_project_exists

# Maximum items per page to prevent DoS via large queries
MAX_PAGE_SIZE = 1000

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{id}", response_model=schemas.JobResponse)
def get_job(id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with id {id} not found.")
    return job


@router.get("/", response_model=List[schemas.JobResponse])
def get_jobs(
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=MAX_PAGE_SIZE, description="Maximum number of items to return"),
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    project_id: Optional[int] = None,
):
    query = db.query(models.Job)
    if project_id is not None:
        query = query.filter(models.Job.project_id == project_id)
    jobs = query.limit(limit).offset(skip).all()
    return jobs


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.JobResponse)
def add_job(job: schemas.JobCreate, db: Session = Depends(get_db)):
    """Create a new job.

    Validates that the project and task exist, and that the dependencies
    don't create a circular dependency.
    """
    validate_project_exists(db, job.project_id)
    validate_task_in_project_exists(db, job.task_id, job.project_id)

    # Check for circular dependencies (use 0 as placeholder for new job ID)
    if job.depends and detect_circular_dependency(db, 0, job.depends, job.project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Circular dependency detected. Cannot create job with these dependencies.",
        )

    new_job = models.Job(**job.model_dump())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


@router.put("/{id}", status_code=status.HTTP_200_OK)
def update_job(id: int, job: schemas.JobUpdate, db: Session = Depends(get_db)):
    """Update a job.

    Validates circular dependencies and propagates failure status to dependent jobs.
    """
    validate_project_exists(db, job.project_id)
    job_query = db.query(models.Job).filter(models.Job.id == id)
    old_job = job_query.first()
    if old_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with id {id} not found.")

    # Check for circular dependencies if depends is being updated
    if job.depends and detect_circular_dependency(db, id, job.depends, job.project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Circular dependency detected. Cannot update job with these dependencies.",
        )

    old_status = old_job.status
    job_query.update(job.model_dump(), synchronize_session=False)
    db.commit()

    # If job status changed to FAILED, propagate to dependent jobs
    updated_job = job_query.first()
    if old_status != models.JobStatus.FAILED and job.status == models.JobStatus.FAILED.value:
        propagate_failure(db, updated_job)
        db.commit()

    return {"data": updated_job}


@router.get("/{id}/dependencies", response_model=schemas.JobDependencyStatusResponse)
def get_job_dependencies(id: int, db: Session = Depends(get_db)):
    """Get the dependency status for a job."""
    job = db.query(models.Job).filter(models.Job.id == id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with id {id} not found.")

    dep_ids = get_dependency_ids(job)
    dependencies = []

    if dep_ids:
        dep_jobs = db.query(models.Job).filter(models.Job.id.in_(dep_ids)).all()
        for dep_job in dep_jobs:
            dependencies.append(
                {
                    "job_id": dep_job.id,
                    "job_name": dep_job.name,
                    "status": dep_job.status.value,
                }
            )

    return {
        "job_id": job.id,
        "job_name": job.name,
        "status": job.status.value,
        "dependencies": dependencies,
        "all_completed": are_dependencies_completed(db, job),
        "has_failed": has_failed_dependency(db, job),
    }


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == id)
    if job.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with id {id} not found.")
    job.delete(synchronize_session=False)
    db.commit()
