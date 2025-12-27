from typing import Any, Dict, List, Optional

from .utils import random_string


class Task:
    """Represents a task template that jobs are based on.

    A Task defines the structure for jobs - what command to run and
    what resources are needed.
    """

    def __init__(
        self,
        name: str,
        command_template: Optional[str] = None,
        artifacts: Optional[List[str]] = None,
        resource: Optional[List[str]] = None,
    ) -> None:
        self.id = random_string()
        self.name = name
        self.artifacts = artifacts or []
        self.resource = resource or []
        self._command_template = command_template

    def format_command(self, parameters: Dict[str, Any]) -> str:
        """Format the command template with the given parameters."""
        if self._command_template is None:
            raise ValueError("No command template defined for this task")
        return self._command_template.format(**parameters)
