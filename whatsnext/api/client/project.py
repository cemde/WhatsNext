from datetime import datetime
from typing import List
from .utils import random_string
from .job import Job

class Project:
    def __init__(
            self,
            id: str = None,
            _server = None
            ) -> None:
        if id is None:
            self.id = random_string()
        else:
            self.id = id
        self._server = _server

    @property
    def last_updated(self) -> datetime:
        self._server._project_connector.get_last_updated(self)

    @property
    def name(self) -> str:
        return self._server._project_connector.get_name(self)
    
    @property
    def description(self) -> str:
        return self._server._project_connector.get_description(self)
    
    @property
    def status(self) -> str:
        return self._server._project_connector.get_status(self)
    
    @property
    def created_at(self) -> datetime:
        return self._server._project_connector.get_created_at(self)

    def append_queue(self, job: Job) -> None:
        self._server.append_queue(self, job)

    def pop_queue(self, idx: int = -1) -> Job:
        return self._server.pop_queue(self, idx)

    def extend_queue(self, jobs: List[Job]) -> None:
        self._server.extend_queue(self, jobs)

    def remove_queue(self, job: Job) -> None:
        self._server.remove_queue(self, job)

    def clear_queue(self) -> None:
        self._server.clear_queue(self)

    def _bind_server(self, server) -> None:
        self._server = server

    @property
    def queue(self) -> List[Job]:
        self._server.get_queue(self)

    def fetch_job(self):
        for job in self.queue:
            if job.status == "pending":
                return job
        raise RuntimeError("All jobs done.")
