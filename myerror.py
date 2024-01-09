class CustomError(Exception):
    def __init__(self, message, status, extra_data={}):
        super().__init__(message)
        self.status = status
        self.extra_data = extra_data
