from typing import List

RESOURCE_STATUS = ["active", "inactive"]


class Resource:
    def __init__(self, cpu: int, accelerator: List[str], client):
        self.cpus = cpu
        self.accelerator = accelerator
        self.client = client
        self._status = "active"

    def active(self):
        return self._status == "active"

    def set_status(self, status):
        if status not in RESOURCE_STATUS:
            raise ValueError(f"Invalid status {status}")
        self._status = status
