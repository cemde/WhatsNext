from __future__ import annotations

from datetime import datetime
from typing import Any, List

from .exceptions import EmptyQueueError
from .project import Project
from .utils import random_string

import requests
from tabulate import tabulate

# dummy server
dummy_projects = {}
dummy_jobs = {}


class ProjectConnector:
    def __init__(self, server: Server) -> None:
        self._server = server

    def get_last_updated(self, project) -> datetime:
        return dummy_projects[project.id]["last_updated"]

    def set_last_updated(self, project, time: datetime = None) -> datetime:
        if time is None:
            time = datetime.now()
        dummy_projects[project.id]["last_updated"] = time

    def get_name(self, project) -> str:
        r = requests.get(f"{self._server._url()}/projects/{project.id}")
        return r.json()["name"]
        # return dummy_projects[project.id]["name"]

    def set_name(self, project, name: str) -> str:
        dummy_projects[project.id]["name"] = name

    def get_description(self, project) -> str:
        return dummy_projects[project.id]["description"]

    def set_description(self, project, description: str) -> str:
        r = requests.patch(f"{self._server._url()}/projects/{project.id}", json={"description": description})
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

    def set_status(self, job, status: str) -> None:
        r = requests.patch(f"{self._server._url()}/jobs/{job.id}", json={"status": status})
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

    def _url(self):
        return f"http://{self.hostname}:{self.port}"

    def list_projects(self, limit: int = 10, skip: int = 0, status: str = "ACTIVE", sort_by: str = None) -> List[Project]:
        r = requests.get(f"{self._url()}/projects?limit={limit}&skip={skip}&status={status}")
        if not r.ok:
            print(f"Error: Could not retrieve projects. HTTP Status {r.status_code}")
            return
        projects = r.json()
        headers = list(projects[0].keys())
        body = [list(p.values()) for p in projects]
        print(tabulate(body, headers=headers, tablefmt="grid"))

    def get_project(self: str, project_name: str) -> Project:
        r = requests.get(f"{self._url()}/projects/name/{project_name}")
        if not r.ok:
            print(f"Error: Could not retrieve project '{project_name}'. HTTP Status {r.status_code}")
            return
        project = r.json()
        return Project(project["id"], self)
        # for project_id, project in dummy_projects.items():
        #     if project["name"] == project_name:
        #         return Project(project_id, self)
        # raise KeyError(f"Project {project_name} not found")

    def append_project(self, name: str, description: str, **kwargs):
        r = requests.post(self._url() + "/projects", json={"name": name, "description": description})
        if r.status_code == 201:
            project = r.json()
            print(f"Project '{name}' created successfully with id: {project['id']}")
        # pars = {"name": name, "description": description, "last_updated": datetime.now(), "created_at": datetime.now(), **kwargs}
        # dummy_projects[random_string()] = pars

    def delete_project(self, project_name: str):
        r = requests.delete(f"{self._url()}/projects/name/{project_name}")
        if r.status_code == 204:
            print(f"Project '{project_name}' deleted successfully.")

    def append_queue(self, project, job: Any):
        r = requests.get(f"{self._url()}/tasks/name/{job.task}", params={"project_id": project.id})
        task_id = r.json()["id"]
        payload = {"name": job.name, "project_id": project.id, "parameters": job.parameters, "task_id": task_id, "status": job.status, "priority": job.priority, "depends": {}}
        r = requests.post(f"{self._url()}/jobs", json=payload)
        if r.status_code == 201:
            print(f"Job '{job.name}' for task '{job.task}' with priority {job.priority} added to queue for project '{project.name}'.")

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
        r = requests.get(self._url())
        # except requests.exceptions.ConnectionError:
        #    print(f"Server at {self.hostname}:{self.port} is not available")
        print(f"Sucessfully connected to server {self.hostname}:{self.port}.")

    def fetch_job(self, project: Project):
        r = requests.get(f"{self._url()}/projects/{project.id}/fetch_job")
        if r.status_code == 200:
            if r.json()["num_pending"] == 0:
                raise EmptyQueueError("No jobs in queue")
            job = r.json()
            return job
        # for job_id, job_dict in dummy_jobs.items():
        #     if job_dict["project_id"] == project.id and job_dict["job"].status == "pending":
        #         job_dict["job"].status = "queued"
        #         job_dict["job"]._bind_server(self)
        #         return job_dict["job"]
        # raise EmptyQueueError("No jobs in queue")
        # print("All Done!")

    def create_task(self, project: Project, task_name: str):
        r = requests.post(self._url() + "/tasks", json={"name": task_name, "project_id": project.id})
        if r.status_code == 201:
            print(f"Task '{task_name}' created successfully for project '{project.name}'.")
