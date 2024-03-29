from datetime import datetime
from .project import Project
from .utils import random_string


class Client:
    def __init__(
            self,
            entity: str,
            name: str,
            description: str,
            project: Project,
            ) -> None:
        self.id = random_string()
        self.entity = entity
        self.name = name
        self.project = project
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.active_resources = []

    def allocate_resource(self, cpu: int, accelerator: List[int]) -> Resource:  # TODO:
        resource = Resource(cpu, accelerator, self)
        self.active_resources.append(resource)
        return resource

    def append_artifact(self, artifact: Artifact):
        pass

    def extend_artifacts(self, artifacts: List[Artifact]):
        pass