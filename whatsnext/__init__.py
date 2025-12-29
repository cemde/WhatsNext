"""WhatsNext - Job queue and task management system.

This package provides optional components that require additional dependencies:

- Client components (Client, Job, Project, Server, Formatter, Resource):
  Install with: pip install whatsnext[client]

- Server components (app, models, schemas):
  Install with: pip install whatsnext[server]

- All components:
  Install with: pip install whatsnext[all]

Shared components (JobStatus, ProjectStatus) are always available.
"""

from typing import TYPE_CHECKING

# Shared module has no external dependencies - always available
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

# Type hints for IDE support (resolved at runtime only if deps available)
if TYPE_CHECKING:
    from whatsnext.api.client.client import Client as Client
    from whatsnext.api.client.exceptions import EmptyQueueError as EmptyQueueError
    from whatsnext.api.client.formatter import Formatter as Formatter
    from whatsnext.api.client.job import Job as Job
    from whatsnext.api.client.project import Project as Project
    from whatsnext.api.client.resource import Resource as Resource
    from whatsnext.api.client.server import Server as Server

__all__ = [
    # Always available (shared)
    "JobStatus",
    "ProjectStatus",
    "DEFAULT_JOB_STATUS",
    "DEFAULT_PROJECT_STATUS",
    # Client components (require whatsnext[client])
    "Client",
    "Job",
    "Project",
    "Server",
    "Formatter",
    "Resource",
    "EmptyQueueError",
]


def __getattr__(name: str):
    """Lazy import for optional dependencies.

    This allows importing client components only when actually accessed,
    and provides helpful error messages when dependencies are missing.
    """
    # Client components
    client_components = {
        "Client": ("whatsnext.api.client.client", "Client"),
        "Job": ("whatsnext.api.client.job", "Job"),
        "Project": ("whatsnext.api.client.project", "Project"),
        "Server": ("whatsnext.api.client.server", "Server"),
        "Formatter": ("whatsnext.api.client.formatter", "Formatter"),
        "Resource": ("whatsnext.api.client.resource", "Resource"),
        "EmptyQueueError": ("whatsnext.api.client.exceptions", "EmptyQueueError"),
    }

    if name in client_components:
        module_path, attr = client_components[name]
        try:
            import importlib

            module = importlib.import_module(module_path)
            return getattr(module, attr)
        except ImportError as e:
            raise ImportError(f"'{name}' requires client dependencies. Install with: pip install whatsnext[client]\nOriginal error: {e}") from e

    raise AttributeError(f"module 'whatsnext' has no attribute '{name}'")
