from typing import List


class Resource:
    def __init__(self, cpu: int, accelerator: List[str], client):
        self.cpus = cpu
        self.accelerator = accelerator
        self.client = client
        self._status = "active"

    def active(self):
        return self._status == "active"
