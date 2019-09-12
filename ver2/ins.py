instances = {}

def only(cls):
    global instances

    def _only(*args, **kw):
        if cls.__name__ not in instances:
            instances[cls.__name__] = cls(*args, **kw)
        return instances[cls.__name__]

    return _only

def get_only(cls, *args, **kw):
    global instances
    if cls.__name__ not in instances:
        instances[cls.__name__] = cls(*args, **kw)
    return instances[cls.__name__]