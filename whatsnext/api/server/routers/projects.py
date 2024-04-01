from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/all", response_model=List[schemas.ProjectResponse])
def get_all_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    return projects


@router.get("/{id}", response_model=schemas.ProjectResponse)
def get_project(id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with {id=} not found.")
    return project


@router.get("/name/{name}", response_model=schemas.ProjectResponse)
def get_project_by_name(name: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.name == name).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with {id=} not found.")
    return project


@router.get("/", response_model=List[schemas.ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    limit: int = 10,
    skip: int = 0,
    status: str = "ACTIVE",
    # search: Optional[str] = "Inventing AGI",
):
    # Validate status # TODO move validation to pydantic schema
    if status not in models.ProjectStatus.__members__:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status {status=}")

    projects = (
        db.query(models.Project)
        .filter(models.Project.status == status)
        # .filter(models.Project.name.ilike(f"%{search}%"))
        .limit(limit)
        .offset(skip)
        .all()
    )
    return projects


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.ProjectResponse)
def add_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    new_project = models.Project(**project.model_dump())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project


@router.put("/{id}")
def update_project(id: int, project: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    project_query = db.query(models.Project).filter(models.Project.id == id)
    old_project = project_query.first()
    if old_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with {id=} not found.")
    print(project.model_dump())
    project_query.update(project.model_dump(), synchronize_session=False)
    db.commit()
    return {"data": project_query.first()}


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == id)
    if project.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with {id=} not found.")
    project.delete(synchronize_session=False)
    db.commit()


@router.delete("/name/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_by_name(name: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.name == name)
    if project.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with {id=} not found.")
    project.delete(synchronize_session=False)
    db.commit()
