from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from . import models


# validate that project exists
def validate_project_exists(db: Session, project_id: int) -> models.Project:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Project with {project_id=} not found.")
    return project


# validate that task exists in project
def validate_task_in_project_exists(db: Session, task_id: int, project_id: int) -> models.Task:
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task is None or task.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task {task_id=} not found for project id {project_id}.")
    return task
