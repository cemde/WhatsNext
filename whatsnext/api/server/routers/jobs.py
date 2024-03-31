from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..validate_in_db import validate_project_exists, validate_task_in_project_exists

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/all", response_model=List[schemas.JobResponse])
def get_all_jobs(db: Session = Depends(get_db)):
    jobs = db.query(models.Job).all()
    return jobs


@router.get("/{id}", response_model=schemas.JobResponse)
def get_job(id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with {id=} not found.")
    return job


@router.get("/", response_model=List[schemas.JobResponse])
def get_jobs(db: Session = Depends(get_db), limit: int = 10, skip: int = 0, project_id: int = None):
    jobs = db.query(models.Job).filter(models.Job.project_id == project_id).limit(limit).offset(skip).all()
    # results = db.query(models.Job, models.Task.name).join(models.Task, models.Job.task_id == models.Task.id, isouter=True).all()
    # for r in results:
    #     r[0].task_name = r[1]
    # results = [r[0] for r in results]
    # return results
    return jobs


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.JobResponse)
def add_job(job: schemas.JobCreate, db: Session = Depends(get_db)):
    # validate that project exists
    validate_project_exists(db, job.project_id)
    # validate that task exists and is for project
    validate_task_in_project_exists(db, job.task_id, job.project_id)
    # get task_id for name
    # job = job.model_dump()
    # del job["task_name"]
    # job["task_id"] = task.id
    # create new job
    new_job = models.Job(**job.model_dump())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


@router.put("/{id}")  # status_code=status.HTTP_200_OK
def update_job(id: int, job: schemas.JobUpdate, db: Session = Depends(get_db)):
    # validate that project exists
    validate_project_exists(db, job.project_id)
    # update job
    job_query = db.query(models.Job).filter(models.Job.id == id)
    old_job = job_query.first()
    if old_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with {id=} not found.")
    print(job.model_dump())
    job_query.update(job.model_dump(), synchronize_session=False)
    db.commit()
    return {"data": job_query.first()}


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(id, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == id)
    if job.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with {id=} not found.")
    job.delete(synchronize_session=False)
    db.commit()
