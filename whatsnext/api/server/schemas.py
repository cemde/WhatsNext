from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel

from .models import DEFAULT_JOB_STATUS, DEFAULT_PROJECT_STATUS


class JobBase(BaseModel):
    name: str
    project_id: int
    parameters: Dict[str, Any]
    task_id: int


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
    task_name: str

    class Config:
        from_attributes = True


class JobAndCountResponse(BaseModel):
    job: JobResponse
    num_pending: int

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


class TaskBase(BaseModel):
    name: str
    project_id: int


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
