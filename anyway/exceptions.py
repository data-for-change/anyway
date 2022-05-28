from abc import ABC
from typing import Optional


class AnywayException(ABC, Exception):
    def __init__(self, message: str, status_code: Optional[int] = 500):
        super().__init__(message)
        self.code = status_code
