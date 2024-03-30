from __future__ import annotations

from datetime import datetime
from typing import Any, List

from .exceptions import EmptyQueueError
from .project import Project
from .utils import random_string

# dummy server
dummy_projects = {}
dummy_jobs = {}


class ProjectConnector:
    def __init__(self, server: Server) -> None:
        pass

    def get_last_updated(self, project) -> datetime:
        return dummy_projects[project.id]["last_updated"]

    def set_last_updated(self, project, time: datetime = None) -> datetime:
        if time is None:
            time = datetime.now()
        dummy_projects[project.id]["last_updated"] = time

    def get_name(self, project) -> str:
        return dummy_projects[project.id]["name"]

    def set_name(self, project, name: str) -> str:
        dummy_projects[project.id]["name"] = name

    def get_description(self, project) -> str:
        return dummy_projects[project.id]["description"]

    def set_description(self, project, description: str) -> str:
        dummy_projects[project.id]["description"] = description

    def get_status(self, project) -> str:
        return dummy_projects[project.id]["status"]

    def set_status(self, project, status: str) -> str:
        dummy_projects[project.id]["status"] = status

    def get_created_at(self, project) -> datetime:
        return dummy_projects[project.id]["created_at"]


class JobConnector:
    def __init__(self, server: Server) -> None:
        pass

    def set_status_to(self, job, status: str) -> None:
        dummy_jobs[job.id]["status"] = status


#### This is a dummy class until the FastAPI server is implemented


# this class handles all communcation with the server
class Server:
    def __init__(self, hostname: str, port: int):
        self.hostname = hostname
        self.port = port
        self._project_connector = ProjectConnector(self)
        self._job_connector = JobConnector(self)
        self._test_connection()

    def list_projects(self) -> List[Project]:
        for p in dummy_projects.values():
            print(f"Project: {p['name']} - {p['description']}")

    def get_project(self: str, project_name: str) -> Project:
        for project_id, project in dummy_projects.items():
            if project["name"] == project_name:
                return Project(project_id, self)
        raise KeyError(f"Project {project_name} not found")

    def append_project(self, name: str, description: str, **kwargs):
        pars = {"name": name, "description": description, "last_updated": datetime.now(), "created_at": datetime.now(), **kwargs}
        dummy_projects[random_string()] = pars

    def delete_project(self, project_name: str):
        print("Not implemented")

    def append_queue(self, project, job: Any):
        job.id = random_string()
        dummy_jobs[job.id] = {"job": job, "project_id": project.id}

    def pop_queue(self, project, idx: int = -1):
        print("Not implemented")

    def extend_queue(self, project, jobs: List[Any]):
        print("Not implemented")

    def remove_queue(self, project, job: Any):
        print("Not implemented")

    def clear_queue(self, project):
        print("Not implemented")

    def get_queue(self, project) -> List[Any]:
        return [j for j in dummy_jobs if j["project_id"] == project.id]

    def _test_connection(self):
        print(f"Server at {self.hostname}:{self.port}")
        print("Connecting...")
        print("Sucessful!")
        return True

    def fetch_job(self, project: Project):
        for job_id, job_dict in dummy_jobs.items():
            if job_dict["project_id"] == project.id and job_dict["job"].status == "pending":
                job_dict["job"].status = "queued"
                job_dict["job"]._bind_server(self)
                return job_dict["job"]
        raise EmptyQueueError("No jobs in queue")
        print("All Done!")
