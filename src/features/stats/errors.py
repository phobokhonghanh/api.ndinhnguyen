class StatsValidationError(Exception):
    def __init__(self, code: str):
        self.code = code


class StatsStorageError(Exception):
    pass
