from datetime import datetime
from typing import Any, Dict, List

from .job import Job


class Project:
    """Represents a project that contains tasks and jobs.

    A Project is a container for organizing related work. It holds tasks
    (templates) and jobs (instances of tasks to execute).
    """

    def __init__(self, id: int, _server=None) -> None:
        self.id = id
        self._server = _server

    @property
    def last_updated(self) -> datetime:
        """Get the last update timestamp from the server."""
        return self._server._project_connector.get_last_updated(self)

    @property
    def name(self) -> str:
        """Get the project name from the server."""
        return self._server._project_connector.get_name(self)

    @property
    def description(self) -> str:
        """Get the project description from the server."""
        return self._server._project_connector.get_description(self)

    @property
    def status(self) -> str:
        """Get the project status from the server."""
        return self._server._project_connector.get_status(self)

    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp from the server."""
        return self._server._project_connector.get_created_at(self)

    def append_queue(self, job: Job) -> bool:
        """Add a job to the project's queue."""
        return self._server.append_queue(self, job)

    @property
    def queue(self) -> List[Dict[str, Any]]:
        """Get all jobs in the queue from the server."""
        return self._server.get_queue(self)

    def fetch_job(self) -> Job:
        """Fetch the next pending job from the queue.

        Returns:
            The next job to execute.

        Raises:
            EmptyQueueError: If no jobs are pending.
        """
        return_value = self._server.fetch_job(self)
        job_data = return_value["job"]
        # Transform server response to Job constructor args
        del job_data["project_id"]
        del job_data["task_id"]
        job_data["task"] = job_data["task_name"]
        del job_data["task_name"]
        job = Job(**job_data)
        job._bind_server(self._server)
        return job

    def create_task(self, task_name: str) -> bool:
        """Create a new task in this project."""
        return self._server.create_task(self, task_name)

    def set_description(self, description: str) -> None:
        """Update the project description on the server."""
        self._server._project_connector.set_description(self, description)

    def __repr__(self) -> str:
        return f"<Project {self.id}: {self.name}>"
