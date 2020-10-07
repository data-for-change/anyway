class Map(dict):
    def __init__(self, dct, value_func=None, *args, **kwargs):
        super(Map, self).__init__(*args, **kwargs)
        if value_func is None: value_func = lambda x: x
        for k, v in dct.items():
            self[k] = value_func(v)

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(Map, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(Map, self).__delitem__(key)
        del self.__dict__[key]
