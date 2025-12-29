from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import JSON, TIMESTAMP

from ..shared.status import DEFAULT_PROJECT_STATUS, JobStatus, ProjectStatus
from .database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    parameters = Column(JSON, nullable=False)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), server_onupdate=text("now()"))
    priority = Column(Integer, default=0, nullable=False)
    depends = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<Job {self.name}>"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), server_onupdate=text("now()"))
    status = Column(Enum(ProjectStatus), nullable=False, default=DEFAULT_PROJECT_STATUS)

    def __repr__(self):
        return f"<Project {self.name}>"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    command_template = Column(String, nullable=True)
    required_cpu = Column(Integer, default=1, nullable=False)
    required_accelerators = Column(Integer, default=0, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), server_onupdate=text("now()"))

    __table_args__ = (UniqueConstraint("name", "project_id", name="unique_task_name_project_id"),)

    def __repr__(self):
        return f"<Task {self.name}>"


class Client(Base):
    __tablename__ = "clients"

    id = Column(String, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    entity = Column(String, nullable=False)
    description = Column(String, nullable=True)
    available_cpu = Column(Integer, default=0, nullable=False)
    available_accelerators = Column(Integer, default=0, nullable=False)
    last_heartbeat = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    is_active = Column(Integer, default=1, nullable=False)

    def __repr__(self):
        return f"<Client {self.name}>"
