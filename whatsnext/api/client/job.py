import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Job:
    """Represents a job to be executed.

    A Job is a data object containing execution parameters. The actual execution
    is handled by a Formatter, keeping job definitions runtime-agnostic.
    """

    def __init__(
        self,
        name: str,
        task: str,
        parameters: Dict[str, Any],
        priority: int = 0,
        status: str = "PENDING",
        depends: Optional[List["Job"]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        id: Optional[int] = None,
    ) -> None:
        self.id = id
        self.name = name
        self.task = task
        self.parameters = parameters
        self.priority = priority
        self.status = status
        self.depends = depends
        self.created_at = created_at
        self.updated_at = updated_at
        self._server = None

    def set_status(self, status: str) -> None:
        """Update job status on the server."""
        self._server._job_connector.set_status(self, status)
        self.status = status

    def set_priority_to(self, priority: int) -> None:
        """Update job priority on the server."""
        self._server._job_connector.set_priority_to(self, priority)
        self.priority = priority

    def set_depends_to(self, depends: List["Job"]) -> None:
        """Update job dependencies on the server."""
        self._server._job_connector.set_depends_to(self, depends)
        self.depends = depends

    def run(self, resource) -> int:
        """Execute the job using the resource's formatter.

        Args:
            resource: Resource containing the client and formatter to use.

        Returns:
            Exit code from the command execution.
        """
        self.set_status("RUNNING")
        try:
            command = resource.client.formatter.format(self.task, self.parameters)
            # Use subprocess with shell=False to prevent command injection
            result = subprocess.run(command, shell=False, capture_output=True, text=True)
            if result.returncode == 0:
                self.set_status("COMPLETED")
            else:
                logger.error(f"Job {self.id} failed with exit code {result.returncode}: {result.stderr}")
                self.set_status("FAILED")
            return result.returncode
        except Exception as e:
            logger.exception(f"Job {self.id} execution error: {e}")
            self.set_status("FAILED")
            return 1

    def _bind_server(self, server) -> None:
        """Bind this job to a server for status updates."""
        self._server = server

    def __repr__(self) -> str:
        return f"<Job {self.id}: {self.name} of Task '{self.task}' [{self.priority}]>"
