import functools


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


class MockStore:

    def __init__(self):
        self.storage = {}

    def get(self, key):
        return self.storage.get(key, None)

    def cache_get(self, key):
        return self.storage.get(key, None)

    def cache_set(self, key, value, expires=0):
        self.storage[key] = str(value)
