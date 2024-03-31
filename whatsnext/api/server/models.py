import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import JSON, TIMESTAMP

from .database import Base


class JobStatus(enum.Enum):
    PENDING = "pending"  # Job is waiting to be scheduled
    QUEUED = "queued"  # Job is scheduled locally but not running yet.
    RUNNING = "running"  # Job is running
    COMPLETED = "completed"  # Job has completed successfully
    FAILED = "failed"  # Job has failed


DEFAULT_JOB_STATUS = JobStatus.PENDING


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
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


DEFAULT_PROJECT_STATUS = ProjectStatus.ACTIVE


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    status = Column(Enum(ProjectStatus), nullable=False, default=DEFAULT_PROJECT_STATUS)

    def __repr__(self):
        return f"<Project {self.name}>"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    def __repr__(self):
        return f"<Task {self.name}>"
