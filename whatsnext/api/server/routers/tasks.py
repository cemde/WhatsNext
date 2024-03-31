from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

from ..validate_in_db import validate_project_exists

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/all", response_model=List[schemas.TaskResponse])
def get_all_tasks(db: Session = Depends(get_db)):
    tasks = db.query(models.Project).all()
    return tasks


@router.get("/", response_model=List[schemas.TaskResponse])
def get_tasks(db: Session = Depends(get_db), limit: int = 10, skip: int = 0, project_id: Optional[int] = None):
    # validate project
    project = validate_project_exists(db, project_id)
    if project.status == models.ProjectStatus.ARCHIVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Project with {project_id=} is archived.")

    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).limit(limit).offset(skip).all()
    return tasks


@router.get("/{id}", response_model=schemas.TaskResponse)
def get_task(id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with {id=} not found.")
    return task


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.TaskResponse)
def add_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    # validate that project exists
    validate_project_exists(db, task.project_id)
    # create new job
    new_task = models.Task(**task.model_dump())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.put("/{id}")
def update_task(id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    pass


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with {id=} not found.")
    db.delete(task, synchronize_session=False)
    db.commit()
