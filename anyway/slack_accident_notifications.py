from dataclasses import dataclass, asdict
from typing import List

import requests
from anyway import secrets

from anyway.models import NewsFlash
from anyway.parsers.infographics_data_cache_updater import is_in_cache

INFOGRAPHIC_URL = "https://media.anyway.co.il/newsflash/"


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
        return f"<{url}|{text}>"
    return f"<{url}>"


def gen_notification(newsflash: NewsFlash) -> Notification:
    blocks = []
    title = Block(type="section", text=Text(type="plain_text", text=newsflash.title))
    blocks.append(title)
    if is_in_cache(newsflash):
        infographic_link = Block(
            type="section",
            text=Text(
                type="mrkdwn",
                text=fmt_lnk_mrkdwn(f"{INFOGRAPHIC_URL}{newsflash.id}", "infographic"),
            ),
        )
        blocks.append(infographic_link)
    return Notification(blocks=blocks)


def publish_notification(newsflash: NewsFlash):
    notification = gen_notification(newsflash)
    requests.post(secrets.get("SLACK_WEBHOOK_URL"), json=asdict(notification))
