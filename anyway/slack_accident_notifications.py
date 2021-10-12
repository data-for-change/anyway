from dataclasses import dataclass
from typing import List

INFOGRAPHIC_URL = "https://media.anyway.co.il/newsflash/"
SLACK_WEBHOOK_URL = (
    "https://hooks.slack.com/services/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"
)

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

def fmt_lnk_mrkdwn(url: str, text: str = "") -> str:
    if text:
        return f'<{url}|{text}>'
    return f'<{url}>'

    