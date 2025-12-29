from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..shared.status import DEFAULT_JOB_STATUS, DEFAULT_PROJECT_STATUS, JobStatus, ProjectStatus

# Valid status values for validation
JOB_STATUS_VALUES = tuple(s.value for s in JobStatus)
PROJECT_STATUS_VALUES = tuple(s.value for s in ProjectStatus)


class JobBase(BaseModel):
    name: str
    project_id: int
    parameters: Dict[str, Any]
    task_id: int


class JobCreate(JobBase):
    status: str = DEFAULT_JOB_STATUS.value
    priority: int = 0
    depends: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        # Normalize to lowercase for comparison
        v_lower = v.lower()
        if v_lower not in JOB_STATUS_VALUES:
            raise ValueError(f"Invalid status '{v}'. Must be one of: {', '.join(JOB_STATUS_VALUES)}")
        return v_lower


class JobUpdate(JobBase):
    status: str
    priority: int
    depends: Dict[str, Any]

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        # Normalize to lowercase for comparison
        v_lower = v.lower()
        if v_lower not in JOB_STATUS_VALUES:
            raise ValueError(f"Invalid status '{v}'. Must be one of: {', '.join(JOB_STATUS_VALUES)}")
        return v_lower


class JobResponse(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class JobWithTaskNameResponse(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    task_name: str


class JobAndCountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job: Optional[JobWithTaskNameResponse] = None
    num_pending: int


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

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        # Normalize to lowercase for comparison
        v_lower = v.lower()
        if v_lower not in PROJECT_STATUS_VALUES:
            raise ValueError(f"Invalid status '{v}'. Must be one of: {', '.join(PROJECT_STATUS_VALUES)}")
        return v_lower


class ProjectUpdate(ProjectBase):
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        # Normalize to lowercase for comparison
        v_lower = v.lower()
        if v_lower not in PROJECT_STATUS_VALUES:
            raise ValueError(f"Invalid status '{v}'. Must be one of: {', '.join(PROJECT_STATUS_VALUES)}")
        return v_lower


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class TaskBase(BaseModel):
    name: str
    project_id: int


class TaskCreate(TaskBase):
    command_template: Optional[str] = None
    required_cpu: int = 1
    required_accelerators: int = 0


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    project_id: Optional[int] = None
    command_template: Optional[str] = None
    required_cpu: Optional[int] = None
    required_accelerators: Optional[int] = None


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    command_template: Optional[str] = None
    required_cpu: int
    required_accelerators: int
    created_at: datetime
    updated_at: datetime


class ClientBase(BaseModel):
    name: str
    entity: str
    description: Optional[str] = None
    available_cpu: int = 0
    available_accelerators: int = 0


class ClientRegister(ClientBase):
    id: str


class ClientUpdate(BaseModel):
    available_cpu: Optional[int] = None
    available_accelerators: Optional[int] = None
    is_active: Optional[int] = None


class ClientResponse(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    last_heartbeat: datetime
    created_at: datetime
    is_active: int
