import enum


class JobStatus(enum.Enum):
    PENDING = "pending"  # Job is waiting to be scheduled
    QUEUED = "queued"  # Job is scheduled locally but not running yet.
    RUNNING = "running"  # Job is running
    COMPLETED = "completed"  # Job has completed successfully
    FAILED = "failed"  # Job has failed
    BLOCKED = "blocked"  # Job is blocked because a dependency failed


DEFAULT_JOB_STATUS = JobStatus.PENDING


class ProjectStatus(enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


DEFAULT_PROJECT_STATUS = ProjectStatus.ACTIVE
