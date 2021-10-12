from dataclasses import dataclass
from typing import List

@dataclass
class Text:
    type: str
    text: str


@dataclass
class Block:
    type: str
    text: Text


@dataclass
class Notification:
    blocks: List[Block]