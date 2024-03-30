from datetime import datetime
from typing import Any, Dict, Literal, List, Union

import uuid


# create random alphanumeric string
def random_string(length: int = 128) -> str:
    return str(uuid.uuid4().hex)[:length]


PROJECT_SATUS = ("active", "archieved")


class Formatter:
    pass


class SlurmFormatter(Formatter):
    pass


class BashFormatter(Formatter):
    pass


class RUNAIFormatter(Formatter):
    pass


class Status:
    def __init__(self):
        self.status = "active"
        self.client = None


class Project:
    def __init__(
        self,
        name: str,
        description: str,
        status: str = "active",
    ) -> None:
        self.id = random_string()
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.status = status
        self._server = None
        self.queue: List[Job] = []

    def append_queue(self, job: Job) -> None:
        self.updated_at = datetime.now()
        self.queue.append(job)

    def pop_queue(self, idx: int = -1) -> Job:
        self.updated_at = datetime.now()
        return self.queue.pop(idx)

    def extend_queue(self, jobs: List[Job]) -> None:
        self.updated_at = datetime.now()
        self.queue.extend(jobs)

    def remove_queue(self, job: Job) -> None:
        self.updated_at = datetime.now()
        self.queue.remove(job)

    def clear_queue(self) -> None:
        self.updated_at = datetime.now()
        self.queue.clear()

    def _bind_server(self, server) -> None:
        self._server = server

    def fetch_job(self):
        for job in self.queue:
            if job.status == "pending":
                return job
        raise RuntimeError("All jobs done.")
