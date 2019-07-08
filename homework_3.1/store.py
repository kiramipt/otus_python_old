import functools
import time
import redis


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


class RedisStorage:

    def __init__(self, host="localhost", port=6379, timeout=3):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.conn = redis.Redis(
            host=self.host,
            port=self.port,
            socket_connect_timeout=self.timeout,
            socket_timeout=self.timeout
        )

    def get(self, key):
        try:
            value = self.conn.get(key)
            return value
        except (redis.exceptions.TimeoutError, redis.RedisError):
            raise ConnectionError

    def set(self, key, value, expires=0):
        try:
            return self.conn.set(key, value, ex=expires)
        except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError):
            raise ConnectionError


class Store:
    max_retries = 3

    def __init__(self, storage):
        self.storage = storage

    @retry(max_retries=max_retries, silent=False)
    def get(self, key):
        return self.storage.get(key)

    @retry(max_retries=max_retries, silent=True)
    def cache_get(self, key):
        return self.storage.get(key)

    @retry(max_retries=max_retries, silent=True)
    def cache_set(self, key, value, expires=0):
        return self.storage.set(key, value, expires)


if __name__ == '__main__':

    storage = RedisStorage()

    res = storage.get('test')
    print(res)

    # storage.set('next', 'value', expires=10)
    res = storage.get('next')
    print(res)

    storage = Store(RedisStorage())
    res = storage.get('test')
    print(res)
