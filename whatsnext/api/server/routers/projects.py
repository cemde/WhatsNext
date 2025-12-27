from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

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
    limit: int = 10,
    skip: int = 0,
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
def fetch_job(id: int, db: Session = Depends(get_db)):
    job_count = db.query(models.Job).filter(models.Job.project_id == id).filter(models.Job.status == models.JobStatus.PENDING).count()
    if job_count == 0:
        return {"job": None, "num_pending": 0}
    job, task_name = (
        db.query(models.Job, models.Task.name)
        .join(models.Task, models.Job.task_id == models.Task.id, isouter=True)
        .filter(models.Job.project_id == id)
        .filter(models.Job.status == models.JobStatus.PENDING)
        .order_by(models.Job.priority.desc())
        .first()
    )
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
