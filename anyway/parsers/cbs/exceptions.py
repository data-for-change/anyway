from anyway.exceptions import AnywayException


class CBSParsingFailed(AnywayException):
    def __init__(self, message: str):
        super().__init__(message=f"Exception occurred while loading the cbs data: {message}")
