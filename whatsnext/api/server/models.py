from .database import Base
import enum
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.sql.sqltypes import JSON, TIMESTAMP
from sqlalchemy.sql.expression import text


class JobStatus(enum.Enum):
    PENDING = "pending"  # Job is waiting to be scheduled
    QUEUED = "queued"  # Job is scheduled locally but not running yet.
    RUNNING = "running"  # Job is running
    COMPLETED = "completed"  # Job has completed successfully
    FAILED = "failed"  # Job has failed


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    project = Column(String, nullable=False)
    parameters = Column(JSON, nullable=False)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    priority = Column(Integer, default=0, nullable=False)
    depends = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<Job {self.name}>"


class ProjectStatus(enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.ACTIVE)

    def __repr__(self):
        return f"<Project {self.name}>"
