from datetime import datetime
from typing import TYPE_CHECKING, List

from .formatter import Formatter
from .resource import Resource
from .utils import random_string

if TYPE_CHECKING:
    from .project import Project


class Client:
    """Represents a worker client that executes jobs.

    A Client manages resources (CPU/GPU) and uses a formatter to convert
    job parameters into executable commands.
    """

    def __init__(
        self,
        entity: str,
        name: str,
        description: str,
        project: "Project",
        formatter: Formatter,
    ) -> None:
        self.id = random_string()
        self.entity = entity
        self.name = name
        self.project = project
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.formatter = formatter
        self.active_resources: List[Resource] = []

    def allocate_resource(self, cpu: int, accelerator: List[str]) -> Resource:
        """Allocate a resource for job execution.

        Args:
            cpu: Number of CPUs to allocate.
            accelerator: List of accelerator device IDs (e.g., ["0", "1"] for GPUs).

        Returns:
            The allocated Resource.
        """
        resource = Resource(cpu, accelerator, self)
        self.active_resources.append(resource)
        return resource

    def free_resource(self, resource: Resource) -> None:
        """Release a previously allocated resource."""
        self.active_resources.remove(resource)
