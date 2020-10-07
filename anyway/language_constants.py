from anyway.map_class import Map

_WORDS = {}


class HebrewWord(str):
    value = None

    def __new__(cls, value):
        obj = str.__new__(cls, value)
        obj.value = value
        return obj

    @property
    def IN(self):
        return HebrewWord("ב" + self.value)

    @property
    def AT(self):
        return HebrewWord("ב" + self.value)

    @property
    def THE(self):
        return HebrewWord("ה" + self.value)

    @property
    def AND(self):
        return HebrewWord("ו" + self.value)

    @property
    def THAT(self):
        return HebrewWord("ש" + self.value)

    @property
    def TO(self):
        return HebrewWord("ל" + self.value)


class HebrewConstants(Map):
    def __init__(self):
        super(HebrewConstants, self).__init__(_WORDS, value_func=lambda x: HebrewWord(x))

    @staticmethod
    def concat(*words, sep=" "):
        return sep.join(words)


hebrew = HebrewConstants()
