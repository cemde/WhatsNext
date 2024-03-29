class EmptyQueueError(Exception):
    def __init__(self, message="Queue is empty"):
        self.message = message
        super().__init__(self.message)
