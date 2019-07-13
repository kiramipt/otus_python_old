import functools
import time


def retry(max_retries=3, silent=True):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except ConnectionError:
                    time.sleep(1)
            if not silent:
                raise ConnectionError
        return wrapper
    return decorator
