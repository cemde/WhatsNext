from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import ConnectionError, Timeout
from tabulate import tabulate

from .exceptions import EmptyQueueError
from .job import Job
from .project import Project

logger = logging.getLogger(__name__)

# Default timeout for HTTP requests (seconds)
DEFAULT_TIMEOUT = 30


class ProjectConnector:
    """Handles project-related HTTP requests to the server."""

    def __init__(self, server: Server) -> None:
        self._server = server

    def _get_project_data(self, project) -> Dict[str, Any]:
        """Fetch full project data from server."""
        r = requests.get(
            f"{self._server.base_url}/projects/{project.id}",
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()

    def get_last_updated(self, project) -> datetime:
        data = self._get_project_data(project)
        return datetime.fromisoformat(data["updated_at"])

    def get_name(self, project) -> str:
        data = self._get_project_data(project)
        return data["name"]

    def set_name(self, project, name: str) -> None:
        r = requests.put(
            f"{self._server.base_url}/projects/{project.id}",
            json={"name": name, "description": project.description, "status": project.status},
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()

    def get_description(self, project) -> str:
        data = self._get_project_data(project)
        return data["description"]

    def set_description(self, project, description: str) -> None:
        r = requests.put(
            f"{self._server.base_url}/projects/{project.id}",
            json={"name": project.name, "description": description, "status": project.status},
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()

    def get_status(self, project) -> str:
        data = self._get_project_data(project)
        return data["status"]

    def set_status(self, project, status: str) -> None:
        r = requests.put(
            f"{self._server.base_url}/projects/{project.id}",
            json={"name": project.name, "description": project.description, "status": status},
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()

    def get_created_at(self, project) -> datetime:
        data = self._get_project_data(project)
        return datetime.fromisoformat(data["created_at"])


class JobConnector:
    """Handles job-related HTTP requests to the server."""

    def __init__(self, server: Server) -> None:
        self._server = server

    def _get_job_data(self, job: Job) -> Dict[str, Any]:
        """Fetch full job data from server."""
        r = requests.get(
            f"{self._server.base_url}/jobs/{job.id}",
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()

    def set_status(self, job: Job, status: str) -> None:
        # First get current job data to preserve other fields
        data = self._get_job_data(job)
        data["status"] = status
        r = requests.put(
            f"{self._server.base_url}/jobs/{job.id}",
            json=data,
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()

    def set_priority_to(self, job: Job, priority: int) -> None:
        data = self._get_job_data(job)
        data["priority"] = priority
        r = requests.put(
            f"{self._server.base_url}/jobs/{job.id}",
            json=data,
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()

    def set_depends_to(self, job: Job, depends: List[Job]) -> None:
        data = self._get_job_data(job)
        data["depends"] = {str(j.id): j.name for j in depends}
        r = requests.put(
            f"{self._server.base_url}/jobs/{job.id}",
            json=data,
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()


class Server:
    """Client interface to the WhatsNext server.

    Handles all HTTP communication with the server. This class is stateless -
    all job and project data is stored on the server.
    """

    def __init__(self, hostname: str, port: int) -> None:
        self.hostname = hostname
        self.port = port
        self.base_url = f"http://{hostname}:{port}"
        self._project_connector = ProjectConnector(self)
        self._job_connector = JobConnector(self)
        self._test_connection()

    def _test_connection(self) -> None:
        """Test connection to the server."""
        try:
            r = requests.get(self.base_url, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            logger.info(f"Connected to server at {self.hostname}:{self.port}")
        except ConnectionError:
            raise ConnectionError(f"Cannot connect to server at {self.hostname}:{self.port}")
        except Timeout:
            raise Timeout(f"Connection to server at {self.hostname}:{self.port} timed out")

    def list_projects(
        self,
        limit: int = 10,
        skip: int = 0,
        status: str = "ACTIVE",
    ) -> None:
        """Print a formatted table of projects."""
        r = requests.get(
            f"{self.base_url}/projects",
            params={"limit": limit, "skip": skip, "status_filter": status},
            timeout=DEFAULT_TIMEOUT,
        )
        if not r.ok:
            logger.error(f"Failed to retrieve projects: HTTP {r.status_code}")
            return
        projects = r.json()
        if not projects:
            print("No projects found.")
            return
        headers = list(projects[0].keys())
        body = [list(p.values()) for p in projects]
        print(tabulate(body, headers=headers, tablefmt="grid"))

    def get_project(self, project_name: str) -> Optional[Project]:
        """Get a project by name."""
        r = requests.get(
            f"{self.base_url}/projects/name/{project_name}",
            timeout=DEFAULT_TIMEOUT,
        )
        if not r.ok:
            logger.error(f"Failed to retrieve project '{project_name}': HTTP {r.status_code}")
            return None
        project_data = r.json()
        return Project(project_data["id"], self)

    def append_project(self, name: str, description: str = "") -> Optional[Project]:
        """Create a new project."""
        r = requests.post(
            f"{self.base_url}/projects",
            json={"name": name, "description": description},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 201:
            project_data = r.json()
            logger.info(f"Created project '{name}' with id {project_data['id']}")
            return Project(project_data["id"], self)
        logger.error(f"Failed to create project: HTTP {r.status_code}")
        return None

    def delete_project(self, project_name: str) -> bool:
        """Delete a project by name."""
        r = requests.delete(
            f"{self.base_url}/projects/name/{project_name}",
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 204:
            logger.info(f"Deleted project '{project_name}'")
            return True
        logger.error(f"Failed to delete project: HTTP {r.status_code}")
        return False

    def append_queue(self, project: Project, job: Job) -> bool:
        """Add a job to the project's queue."""
        # First get the task ID
        r = requests.get(
            f"{self.base_url}/tasks/name/{job.task}",
            params={"project_id": project.id},
            timeout=DEFAULT_TIMEOUT,
        )
        if not r.ok:
            logger.error(f"Task '{job.task}' not found for project")
            return False
        task_id = r.json()["id"]

        payload = {
            "name": job.name,
            "project_id": project.id,
            "parameters": job.parameters,
            "task_id": task_id,
            "status": job.status,
            "priority": job.priority,
            "depends": {},
        }
        r = requests.post(
            f"{self.base_url}/jobs",
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 201:
            logger.info(f"Added job '{job.name}' to queue (priority: {job.priority})")
            return True
        logger.error(f"Failed to add job: HTTP {r.status_code}")
        return False

    def get_queue(self, project: Project) -> List[Dict[str, Any]]:
        """Get all pending jobs for a project."""
        r = requests.get(
            f"{self.base_url}/jobs",
            params={"project_id": project.id},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.ok:
            return r.json()
        return []

    def fetch_job(
        self,
        project: Project,
        available_cpu: int = 0,
        available_accelerators: int = 0,
    ) -> Dict[str, Any]:
        """Fetch the next pending job from the queue.

        Args:
            project: The project to fetch jobs from.
            available_cpu: Filter jobs by available CPU (0 = no filter).
            available_accelerators: Filter jobs by available accelerators (0 = no filter).

        Raises:
            EmptyQueueError: If no jobs are pending.
        """
        params: Dict[str, Any] = {}
        if available_cpu > 0:
            params["available_cpu"] = available_cpu
        if available_accelerators > 0:
            params["available_accelerators"] = available_accelerators

        r = requests.get(
            f"{self.base_url}/projects/{project.id}/fetch_job",
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if data["num_pending"] == 0:
            raise EmptyQueueError("No jobs in queue")
        return data

    def create_task(self, project: Project, task_name: str) -> bool:
        """Create a new task for a project."""
        r = requests.post(
            f"{self.base_url}/tasks",
            json={"name": task_name, "project_id": project.id},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 201:
            logger.info(f"Created task '{task_name}' for project")
            return True
        logger.error(f"Failed to create task: HTTP {r.status_code}")
        return False

    def remove_job(self, project: Project, job_id: int) -> bool:
        """Remove a specific job from a project's queue.

        Args:
            project: The project containing the job.
            job_id: The ID of the job to remove.

        Returns:
            True if the job was removed, False otherwise.
        """
        r = requests.delete(
            f"{self.base_url}/projects/{project.id}/jobs/{job_id}",
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 204:
            logger.info(f"Removed job {job_id} from project {project.id}")
            return True
        logger.error(f"Failed to remove job: HTTP {r.status_code}")
        return False

    def clear_queue(self, project: Project) -> int:
        """Clear all pending jobs from a project's queue.

        Args:
            project: The project whose queue to clear.

        Returns:
            Number of jobs deleted.
        """
        r = requests.delete(
            f"{self.base_url}/projects/{project.id}/queue",
            timeout=DEFAULT_TIMEOUT,
        )
        if r.ok:
            data = r.json()
            logger.info(f"Cleared {data['deleted']} jobs from project {project.id}")
            return data["deleted"]
        logger.error(f"Failed to clear queue: HTTP {r.status_code}")
        return 0

    def extend_queue(self, project: Project, jobs: List[Job]) -> List[int]:
        """Add multiple jobs to a project's queue.

        Args:
            project: The project to add jobs to.
            jobs: List of Job objects to add.

        Returns:
            List of created job IDs.
        """
        # Get task IDs for each job
        job_items = []
        for job in jobs:
            r = requests.get(
                f"{self.base_url}/tasks/name/{job.task}",
                params={"project_id": project.id},
                timeout=DEFAULT_TIMEOUT,
            )
            if not r.ok:
                logger.error(f"Task '{job.task}' not found for project")
                continue
            task_id = r.json()["id"]
            job_items.append(
                {
                    "name": job.name,
                    "task_id": task_id,
                    "parameters": job.parameters,
                    "priority": job.priority,
                    "depends": {},
                }
            )

        if not job_items:
            return []

        r = requests.post(
            f"{self.base_url}/projects/{project.id}/jobs/batch",
            json={"jobs": job_items},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 201:
            data = r.json()
            logger.info(f"Added {data['created']} jobs to project {project.id}")
            return data["job_ids"]
        logger.error(f"Failed to add jobs: HTTP {r.status_code}")
        return []

    def register_client(
        self,
        client_id: str,
        name: str,
        entity: str,
        description: str = "",
        available_cpu: int = 0,
        available_accelerators: int = 0,
    ) -> bool:
        """Register a client with the server.

        Args:
            client_id: Unique client identifier.
            name: Human-readable name.
            entity: Entity/organization the client belongs to.
            description: Optional description.
            available_cpu: Number of available CPUs.
            available_accelerators: Number of available accelerators.

        Returns:
            True if registration successful, False otherwise.
        """
        r = requests.post(
            f"{self.base_url}/clients/register",
            json={
                "id": client_id,
                "name": name,
                "entity": entity,
                "description": description,
                "available_cpu": available_cpu,
                "available_accelerators": available_accelerators,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 201:
            logger.info(f"Registered client '{name}' with id {client_id}")
            return True
        logger.error(f"Failed to register client: HTTP {r.status_code}")
        return False

    def client_heartbeat(self, client_id: str) -> bool:
        """Send a heartbeat for a registered client.

        Args:
            client_id: The client ID.

        Returns:
            True if heartbeat successful, False otherwise.
        """
        r = requests.post(
            f"{self.base_url}/clients/{client_id}/heartbeat",
            timeout=DEFAULT_TIMEOUT,
        )
        if r.ok:
            return True
        logger.warning(f"Failed to send heartbeat for client {client_id}: HTTP {r.status_code}")
        return False

    def deactivate_client(self, client_id: str) -> bool:
        """Deactivate a client (graceful disconnect).

        Args:
            client_id: The client ID.

        Returns:
            True if deactivation successful, False otherwise.
        """
        r = requests.post(
            f"{self.base_url}/clients/{client_id}/deactivate",
            timeout=DEFAULT_TIMEOUT,
        )
        if r.ok:
            logger.info(f"Deactivated client {client_id}")
            return True
        logger.error(f"Failed to deactivate client: HTTP {r.status_code}")
        return False

    def update_client_resources(
        self,
        client_id: str,
        available_cpu: Optional[int] = None,
        available_accelerators: Optional[int] = None,
    ) -> bool:
        """Update a client's available resources.

        Args:
            client_id: The client ID.
            available_cpu: New available CPU count (None = no change).
            available_accelerators: New available accelerator count (None = no change).

        Returns:
            True if update successful, False otherwise.
        """
        payload: Dict[str, Any] = {}
        if available_cpu is not None:
            payload["available_cpu"] = available_cpu
        if available_accelerators is not None:
            payload["available_accelerators"] = available_accelerators

        if not payload:
            return True  # Nothing to update

        r = requests.put(
            f"{self.base_url}/clients/{client_id}",
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        if r.ok:
            logger.info(f"Updated resources for client {client_id}")
            return True
        logger.error(f"Failed to update client resources: HTTP {r.status_code}")
        return False
