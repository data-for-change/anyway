from anyway.exceptions import AnywayError


class CBSParsingFailed(AnywayError):
    def __init__(self, message: str):
        super().__init__(message=f"Exception occurred while loading the cbs data: {message}")
