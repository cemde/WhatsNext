from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

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
    status: str = "pending"
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
    status: str = "active"
    description: str = ""


class ProjectUpdate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
