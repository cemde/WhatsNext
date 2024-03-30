from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

from .models import DEFAULT_PROJECT_STATUS, DEFAULT_JOB_STATUS

# class Job(BaseModel):
#     id: int = None
#     name: str
#     project: str
#     parameters: Dict[str, Any]
#     status: str = None
#     created_at: str = None
#     updated_at: str = None
#     priority: int = 0
#     depends: Dict[str, Any] = None


class JobBase(BaseModel):
    name: str
    project: str
    parameters: Dict[str, Any]


class JobCreate(JobBase):
    status: str = DEFAULT_JOB_STATUS
    priority: int = 0
    depends: Dict[str, Any] = {}


class JobUpdate(JobBase):
    status: str
    priority: int
    depends: Dict[str, Any]


class JobResponse(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    name: str
    description: str
    status: str


class ProjectCreate(ProjectBase):
    status: str = DEFAULT_PROJECT_STATUS
    description: str = ""


class ProjectUpdate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
