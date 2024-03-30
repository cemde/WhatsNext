from typing import List
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import schemas
from .. import models
from ..database import get_db

router = APIRouter()


@router.get("/jobs/all", response_model=List[schemas.JobResponse])
def get_all_jobs(response: Response, db: Session = Depends(get_db)):
    jobs = db.query(models.Job).all()
    return jobs


@router.get("/jobs/{id}", response_model=schemas.JobResponse)
def get_job(id: int, response: Response, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with {id=} not found.")
    return job


@router.post("/jobs", status_code=status.HTTP_201_CREATED, response_model=schemas.JobResponse)
def add_job(job: schemas.JobCreate, response: Response, db: Session = Depends(get_db)):
    new_job = models.Job(**job.model_dump())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


@router.put("/jobs/{id}")  # status_code=status.HTTP_200_OK
def update_job(id: int, job: schemas.JobUpdate, response: Response, db: Session = Depends(get_db)):
    job_query = db.query(models.Job).filter(models.Job.id == id)
    old_job = job_query.first()
    if old_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with {id=} not found.")
    print(job.model_dump())
    job_query.update(job.model_dump(), synchronize_session=False)
    db.commit()
    return {"data": job_query.first()}


@router.delete("/jobs/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(id, response: Response, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == id)
    if job.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with {id=} not found.")
    job.delete(synchronize_session=False)
    db.commit()
