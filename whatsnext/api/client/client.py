from datetime import datetime
from typing import List

from .utils import random_string
from .resource import Resource
from .formatter import Formatter


class Client:
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
        self.active_resources = []

    def allocate_resource(self, cpu: int, accelerator: List[int]) -> "Resource":
        resource = Resource(cpu, accelerator, self)
        self.active_resources.append(resource)
        return resource

    def free_resource(self, resource: "Resource") -> None:
        self.active_resources.remove(resource)

    def append_artifact(self, artifact: "Artifact"):
        pass

    def extend_artifacts(self, artifacts: List["Artifact"]):
        pass
