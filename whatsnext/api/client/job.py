from typing import Dict, Any, List
from .utils import random_string
from datetime import datetime
from .client import client
import os

class Job:
    def __init__(
            self,
            name: str,
            task: str,
            parameters: Dict[str, Any],
            priority: int = 0,
            depends: List[Any] = None, # Any replaced by Job
            ) -> None:

        self.id = random_string()
        self.name = name
        self.task = task
        self.parameters = parameters
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.status = "pending"
        self.priority = priority
        self.depends = depends

    def run(self) -> int:
        self.set_status_to()
        command = client.Formatter(self.task, self.parameters)
        os.system(command)
        self.set_status_to()
        return 0