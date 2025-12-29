from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_jobs_with_completed_dependencies

# Maximum items per page to prevent DoS via large queries
MAX_PAGE_SIZE = 1000

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/{id}", response_model=schemas.ProjectResponse)
def get_project(id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {id} not found.")
    return project


@router.get("/name/{name}", response_model=schemas.ProjectResponse)
def get_project_by_name(name: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.name == name).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with name '{name}' not found.")
    return project


@router.get("/", response_model=List[schemas.ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=MAX_PAGE_SIZE, description="Maximum number of items to return"),
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    status_filter: Optional[str] = "ACTIVE",
):
    if status_filter and status_filter not in models.ProjectStatus.__members__:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status '{status_filter}'")

    query = db.query(models.Project)
    if status_filter:
        query = query.filter(models.Project.status == status_filter)
    projects = query.limit(limit).offset(skip).all()
    return projects


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.ProjectResponse)
def add_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    new_project = models.Project(**project.model_dump())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project


@router.put("/{id}", status_code=status.HTTP_200_OK)
def update_project(id: int, project: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    project_query = db.query(models.Project).filter(models.Project.id == id)
    old_project = project_query.first()
    if old_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {id} not found.")
    project_query.update(project.model_dump(), synchronize_session=False)
    db.commit()
    return {"data": project_query.first()}


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == id)
    if project.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {id} not found.")
    project.delete(synchronize_session=False)
    db.commit()


@router.delete("/name/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_by_name(name: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.name == name)
    if project.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with name '{name}' not found.")
    project.delete(synchronize_session=False)
    db.commit()


@router.get("/{id}/fetch_job", response_model=schemas.JobAndCountResponse)
def fetch_job(
    id: int,
    db: Session = Depends(get_db),
    available_cpu: int = 0,
    available_accelerators: int = 0,
):
    """Fetch the next job ready for execution.

    Only returns jobs whose dependencies are all COMPLETED.
    Jobs with failed dependencies are automatically marked as BLOCKED.

    Args:
        id: Project ID.
        available_cpu: Filter jobs by available CPU (0 = no filter).
        available_accelerators: Filter jobs by available accelerators (0 = no filter).
    """
    # Get jobs with completed dependencies (this also marks blocked jobs)
    ready_jobs = get_jobs_with_completed_dependencies(db, id, available_cpu=available_cpu, available_accelerators=available_accelerators)

    # Count all pending jobs (including those waiting for dependencies)
    job_count = db.query(models.Job).filter(models.Job.project_id == id).filter(models.Job.status == models.JobStatus.PENDING).count()

    if not ready_jobs:
        db.commit()  # Commit any status changes from dependency check
        return {"job": None, "num_pending": job_count}

    # Get the highest priority job from ready jobs
    job = ready_jobs[0]

    # Get the task name
    task = db.query(models.Task).filter(models.Task.id == job.task_id).first()
    task_name = task.name if task else None

    # Mark job as QUEUED
    db.query(models.Job).filter(models.Job.id == job.id).update({"status": models.JobStatus.QUEUED}, synchronize_session=False)
    db.commit()
    db.refresh(job)
    job.task_name = task_name
    return {"job": job, "num_pending": job_count}


@router.delete("/{project_id}/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_job(project_id: int, job_id: int, db: Session = Depends(get_db)):
    """Remove a specific job from a project's queue."""
    job = db.query(models.Job).filter(models.Job.id == job_id, models.Job.project_id == project_id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with id {job_id} not found in project {project_id}.")
    db.delete(job)
    db.commit()


@router.delete("/{id}/queue", response_model=schemas.QueueClearResponse)
def clear_project_queue(id: int, db: Session = Depends(get_db)):
    """Clear all pending jobs from a project's queue."""
    project = db.query(models.Project).filter(models.Project.id == id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {id} not found.")

    deleted_count = (
        db.query(models.Job)
        .filter(models.Job.project_id == id, models.Job.status == models.JobStatus.PENDING)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"deleted": deleted_count}


@router.post("/{id}/jobs/batch", status_code=status.HTTP_201_CREATED, response_model=schemas.JobBatchResponse)
def add_jobs_batch(id: int, batch: schemas.JobBatchCreate, db: Session = Depends(get_db)):
    """Add multiple jobs to a project's queue in a single request."""
    project = db.query(models.Project).filter(models.Project.id == id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {id} not found.")

    created_ids = []
    for job_item in batch.jobs:
        new_job = models.Job(
            name=job_item.name,
            project_id=id,
            task_id=job_item.task_id,
            parameters=job_item.parameters,
            priority=job_item.priority,
            depends=job_item.depends,
            status=models.JobStatus.PENDING,
        )
        db.add(new_job)
        db.flush()  # Flush to get the ID
        created_ids.append(new_job.id)

    db.commit()
    return {"created": len(created_ids), "job_ids": created_ids}
