from .database import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    project = Column(String, nullable=False)
    parameters = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    priority = Column(Integer, default=0)
    depends = Column(JSON, default=[])

    def __repr__(self):
        return f"<Job {self.name}>"
