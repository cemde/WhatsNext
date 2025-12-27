from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..shared.status import DEFAULT_JOB_STATUS, DEFAULT_PROJECT_STATUS


class JobBase(BaseModel):
    name: str
    project_id: int
    parameters: Dict[str, Any]
    task_id: int


class JobCreate(JobBase):
    status: str = DEFAULT_JOB_STATUS.value
    priority: int = 0
    depends: Dict[str, Any] = Field(default_factory=dict)


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


class JobWithTaskNameResponse(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime
    task_name: str

    class Config:
        from_attributes = True


class JobAndCountResponse(BaseModel):
    job: Optional[JobWithTaskNameResponse] = None
    num_pending: int

    class Config:
        from_attributes = True


class JobBatchItem(BaseModel):
    name: str
    task_id: int
    parameters: Dict[str, Any]
    priority: int = 0
    depends: Dict[str, Any] = Field(default_factory=dict)


class JobBatchCreate(BaseModel):
    jobs: List[JobBatchItem]


class JobBatchResponse(BaseModel):
    created: int
    job_ids: List[int]


class QueueClearResponse(BaseModel):
    deleted: int


class DependencyInfo(BaseModel):
    job_id: int
    job_name: str
    status: str


class JobDependencyStatusResponse(BaseModel):
    job_id: int
    job_name: str
    status: str
    dependencies: List[DependencyInfo]
    all_completed: bool
    has_failed: bool


class ProjectBase(BaseModel):
    name: str
    description: str
    status: str


class ProjectCreate(ProjectBase):
    status: str = DEFAULT_PROJECT_STATUS.value
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
