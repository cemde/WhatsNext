class Task:
    def __init__(
        self,
        artifacts: List[str] = None,
        resource: List[str] = None,
        command_template: str = None,
    ) -> None:
        self.id = random_string()
        self.artifacts = artifacts
        self.resource = resource
        self._command_template = command_template

    def run(self, parameters: str):
        # get formatter
        return
