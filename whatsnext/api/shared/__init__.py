"""Shared components between client and server.

This module has no external dependencies.
"""

from whatsnext.api.shared.status import (
    DEFAULT_JOB_STATUS as DEFAULT_JOB_STATUS,
    DEFAULT_PROJECT_STATUS as DEFAULT_PROJECT_STATUS,
    JobStatus as JobStatus,
    ProjectStatus as ProjectStatus,
)

__all__ = [
    "JobStatus",
    "ProjectStatus",
    "DEFAULT_JOB_STATUS",
    "DEFAULT_PROJECT_STATUS",
]
