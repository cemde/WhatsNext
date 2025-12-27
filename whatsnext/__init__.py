"""WhatsNext - Job queue and task management system."""

from whatsnext.api.client.client import Client as Client
from whatsnext.api.client.job import Job as Job
from whatsnext.api.client.project import Project as Project
from whatsnext.api.client.server import Server as Server
from whatsnext.api.client.formatter import Formatter as Formatter
from whatsnext.api.client.resource import Resource as Resource
from whatsnext.api.client.exceptions import EmptyQueueError as EmptyQueueError

__all__ = [
    "Client",
    "Job",
    "Project",
    "Server",
    "Formatter",
    "Resource",
    "EmptyQueueError",
]
