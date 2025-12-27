from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .job import Job

if TYPE_CHECKING:
    from .server import Server


class Project:
    """Represents a project that contains tasks and jobs.

    A Project is a container for organizing related work. It holds tasks
    (templates) and jobs (instances of tasks to execute).
    """

    def __init__(self, id: int, _server: Optional[Server] = None) -> None:
        self.id = id
        self._server = _server

    def _check_server(self) -> Server:
        """Ensure the project is bound to a server."""
        if self._server is None:
            raise RuntimeError("Project is not bound to a server")
        return self._server

    @property
    def last_updated(self) -> datetime:
        """Get the last update timestamp from the server."""
        return self._check_server()._project_connector.get_last_updated(self)

    @property
    def name(self) -> str:
        """Get the project name from the server."""
        return self._check_server()._project_connector.get_name(self)

    @property
    def description(self) -> str:
        """Get the project description from the server."""
        return self._check_server()._project_connector.get_description(self)

    @property
    def status(self) -> str:
        """Get the project status from the server."""
        return self._check_server()._project_connector.get_status(self)

    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp from the server."""
        return self._check_server()._project_connector.get_created_at(self)

    def append_queue(self, job: Job) -> bool:
        """Add a job to the project's queue."""
        return self._check_server().append_queue(self, job)

    @property
    def queue(self) -> List[Dict[str, Any]]:
        """Get all jobs in the queue from the server."""
        return self._check_server().get_queue(self)

    def fetch_job(
        self,
        available_cpu: int = 0,
        available_accelerators: int = 0,
    ) -> Job:
        """Fetch the next pending job from the queue.

        Args:
            available_cpu: Filter jobs by available CPU (0 = no filter).
            available_accelerators: Filter jobs by available accelerators (0 = no filter).

        Returns:
            The next job to execute.

        Raises:
            EmptyQueueError: If no jobs are pending.
        """
        server = self._check_server()
        return_value = server.fetch_job(
            self,
            available_cpu=available_cpu,
            available_accelerators=available_accelerators,
        )
        job_data = return_value["job"]
        # Transform server response to Job constructor args
        del job_data["project_id"]
        del job_data["task_id"]
        job_data["task"] = job_data["task_name"]
        del job_data["task_name"]
        job = Job(**job_data)
        job._bind_server(server)
        return job

    def create_task(self, task_name: str) -> bool:
        """Create a new task in this project."""
        return self._check_server().create_task(self, task_name)

    def set_description(self, description: str) -> None:
        """Update the project description on the server."""
        self._check_server()._project_connector.set_description(self, description)

    def extend_queue(self, jobs: List[Job]) -> List[int]:
        """Add multiple jobs to the queue.

        Args:
            jobs: List of Job objects to add.

        Returns:
            List of created job IDs.
        """
        return self._check_server().extend_queue(self, jobs)

    def remove_job(self, job_id: int) -> bool:
        """Remove a specific job from the queue.

        Args:
            job_id: The ID of the job to remove.

        Returns:
            True if the job was removed, False otherwise.
        """
        return self._check_server().remove_job(self, job_id)

    def clear_queue(self) -> int:
        """Clear all pending jobs from the queue.

        Returns:
            Number of jobs deleted.
        """
        return self._check_server().clear_queue(self)

    def pop_queue(self, idx: int = 0) -> bool:
        """Remove a job from the queue by index.

        Args:
            idx: Index of the job to remove (0-based, by creation order).

        Returns:
            True if the job was removed, False otherwise.
        """
        queue = self.queue
        if idx < 0 or idx >= len(queue):
            return False
        job_id = queue[idx]["id"]
        return self.remove_job(job_id)

    def __repr__(self) -> str:
        return f"<Project {self.id}: {self.name}>"
