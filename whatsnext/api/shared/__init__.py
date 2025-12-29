"""Shared components between client and server.

This module has no external dependencies.
"""

from whatsnext.api.shared.status import (
    DEFAULT_JOB_STATUS as DEFAULT_JOB_STATUS,
)
from whatsnext.api.shared.status import (
    DEFAULT_PROJECT_STATUS as DEFAULT_PROJECT_STATUS,
)
from whatsnext.api.shared.status import (
    JobStatus as JobStatus,
)
from whatsnext.api.shared.status import (
    ProjectStatus as ProjectStatus,
)

__all__ = [
    "JobStatus",
    "ProjectStatus",
    "DEFAULT_JOB_STATUS",
    "DEFAULT_PROJECT_STATUS",
]
