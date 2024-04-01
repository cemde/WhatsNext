import os
from datetime import datetime
from typing import Any, Dict, List

from .exceptions import EmptyQueueError
from .utils import random_string


class Job:
    def __init__(
        self,
        name: str,
        task: str,
        parameters: Dict[str, Any],
        priority: int = 0,
        status: str = "PENDING",
        depends: List[Any] = None,  # Any replaced by Job
        created_at: datetime = None,
        updated_at: datetime = None,
    ) -> None:
        self.id = None
        self.name = name
        self.task = task
        self.parameters = parameters
        self.priority = priority
        self.status = status
        self.depends = depends
        self.created_at = created_at
        self.updated_at = updated_at
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
            command = resource.client.formatter(self.parameters)
            os.system(command)
            self.set_status_to("completed")
        except Exception as e:
            self.set_status_to("failed")
        return 0

    def _bind_server(self, server) -> None:
        self._server = server
