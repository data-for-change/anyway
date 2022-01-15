from enum import Enum
from typing import Iterable, List


class LabeledCode(Enum):
    def get_label(self) -> str:
        return type(self).labels()[self]

    @classmethod
    def codes(cls: Iterable) -> List[int]:
        if isinstance(cls, Iterable):
            return [a.value for a in cls]
        else:
            raise NotImplementedError(f"{cls}: needs to be derived from Enum")

    @classmethod
    def labels(cls):
        return {}