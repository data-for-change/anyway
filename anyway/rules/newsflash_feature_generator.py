import datetime

from anyway.models import NewsFlash, NewsflashFeatures


class NewsflashFeatureGenerator:

    VERSION = 1

    def __init__(self):
        pass

    @classmethod
    def generate(cls, newsflash: NewsFlash) -> NewsflashFeatures:
        result = NewsflashFeatures()
        result.newsflash_id = newsflash.id
        result.version = NewsflashFeatureGenerator.VERSION
        result.timestamp = datetime.datetime.utcnow()

        # TODO replace this with a real implementation
        result.is_urban = newsflash.id % 2 == 0

        return result
