from anyway.models import NewsFlash, NewsflashFeatures


class NewsflashFeatureGenerator:

    VERSION = 1

    def __init__(self):
        pass

    def generate(self, newsflash: NewsFlash) -> NewsflashFeatures:
        return NewsflashFeatures()
