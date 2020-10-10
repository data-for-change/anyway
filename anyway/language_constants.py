class Hebrew(object):
    ROAD = "כביש"
    INTERCITY = "בינעירוני"

    def __init__(self, *args, **kwargs):
        super(Hebrew, self).__init__(*args, **kwargs)

    @staticmethod
    def concat(*words, sep=" "):
        return sep.join(words)

    @staticmethod
    def IN(word):
        return "ב" + word

    @staticmethod
    def AT(word):
        return "ב" + word

    @staticmethod
    def THE(word):
        return "ה" + word

    @staticmethod
    def AND(word):
        return "ו" + word

    @staticmethod
    def THAT(word):
        return "ש" + word

    @staticmethod
    def TO(word):
        return "ל" + word
