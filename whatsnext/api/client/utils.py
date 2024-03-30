import uuid


# create random alphanumeric string
def random_string(length: int = 128) -> str:
    return str(uuid.uuid4().hex)[:length]


class Status:
    def __init__(self):
        self.status = "active"
        self.client = None
