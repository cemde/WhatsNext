"""WhatsNext client library.

Requires: pip install whatsnext[client]
"""

from whatsnext.api.client.client import Client as Client
from whatsnext.api.client.exceptions import EmptyQueueError as EmptyQueueError
from whatsnext.api.client.formatter import CLIFormatter as CLIFormatter
from whatsnext.api.client.formatter import Formatter as Formatter
from whatsnext.api.client.formatter import RUNAIFormatter as RUNAIFormatter
from whatsnext.api.client.formatter import SlurmFormatter as SlurmFormatter
from whatsnext.api.client.job import Job as Job
from whatsnext.api.client.project import Project as Project
from whatsnext.api.client.resource import Resource as Resource
from whatsnext.api.client.server import Server as Server

__all__ = [
    "Client",
    "Job",
    "Project",
    "Server",
    "Formatter",
    "CLIFormatter",
    "SlurmFormatter",
    "RUNAIFormatter",
    "Resource",
    "EmptyQueueError",
]
