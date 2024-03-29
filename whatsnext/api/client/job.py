from typing import Dict, Any, List
from .utils import random_string
from datetime import datetime
import os


class Job:
    def __init__(
        self,
        name: str,
        task: str,
        parameters: Dict[str, Any],
        priority: int = 0,
        depends: List[Any] = None,  # Any replaced by Job
    ) -> None:
        self.id = None
        self.name = name
        self.task = task
        self.parameters = parameters
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.status = "pending"
        self.priority = priority
        self.depends = depends
        self._server = None

    def set_status_to(self, status: str = "completed") -> None:
        self._server._job_connector.set_status_to(self, status)
        self.status = status

    def set_priority_to(self, priority: int) -> None:
        self._server._job_connector.set_priority_to(self, priority)
        self.priority = priority

    def set_depends_to(self, depends: List["Job"]) -> None:
        self._server._job_connector.set_depends_to(self, depends)
        self.depends = depends

    def run(self, resource) -> int:
        self.set_status_to("running")
        try:
            command = resource.client.Formatter(self.task, self.parameters)
            os.system(command)
            self.set_status_to()
        except Exception as e:
            self.set_status_to("failed")
        return 0

    def _bind_server(self, server) -> None:
        self._server = server
