from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..validate_in_db import validate_project_exists

# Maximum items per page to prevent DoS via large queries
MAX_PAGE_SIZE = 1000

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=List[schemas.TaskResponse])
def get_tasks(
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=MAX_PAGE_SIZE, description="Maximum number of items to return"),
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    project_id: Optional[int] = None,
):
    if project_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")

    project = validate_project_exists(db, project_id)
    if project.status == models.ProjectStatus.ARCHIVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Project with id {project_id} is archived.")

    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).limit(limit).offset(skip).all()
    return tasks


@router.get("/{id}", response_model=schemas.TaskResponse)
def get_task(id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {id} not found.")
    return task


@router.get("/name/{name}", response_model=schemas.TaskResponse)
def get_task_by_name(name: str, db: Session = Depends(get_db), project_id: Optional[int] = None):
    query = db.query(models.Task).filter(models.Task.name == name)
    if project_id is not None:
        query = query.filter(models.Task.project_id == project_id)
    task = query.first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with name '{name}' not found.")
    return task


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.TaskResponse)
def add_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    validate_project_exists(db, task.project_id)
    new_task = models.Task(**task.model_dump())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.put("/{id}", status_code=status.HTTP_200_OK)
def update_task(id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task_query = db.query(models.Task).filter(models.Task.id == id)
    old_task = task_query.first()
    if old_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {id} not found.")

    update_data = {k: v for k, v in task.model_dump().items() if v is not None}
    if update_data:
        task_query.update(update_data, synchronize_session=False)
        db.commit()
    return {"data": task_query.first()}


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == id)
    if task.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {id} not found.")
    task.delete(synchronize_session=False)
    db.commit()
