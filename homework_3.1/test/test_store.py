import unittest

from store import Store, RedisStorage
from test.utils import cases


class TestStore(unittest.TestCase):

    def setUp(self):
        self.store = Store(RedisStorage())

    @cases([('key_0', 0), ('key_1', 1), ('key_2', 2)])
    def test_store_set_cache_get(self, key, value):
        self.store.cache_set(key, value, 1)
        cache_value = self.store.cache_get(key).decode('utf-8')
        self.assertEqual(cache_value, str(value))

    @cases([('key_3', 0), ('key_4', 1), ('key_5', 2)])
    def test_store_set_get(self, key, value):
        self.store.cache_set(key, value, 1)
        cache_value = self.store.get(key).decode('utf-8')
        self.assertEqual(cache_value, str(value))

    def test_cache_get_and_set_not_raise_connection_error(self):
        # create store with incorrect port for redis
        store = Store(RedisStorage(port=6378))
        # try to get and set cache value in not working storage
        self.assertEqual(store.cache_get('key_0'), None)
        self.assertEqual(store.cache_set('key_0', 0), None)

    def test_get_raise_connection_error(self):
        # create store with incorrect port for redis
        store = Store(RedisStorage(port=6378))
        # try to get value in not working storage
        self.assertRaises(ConnectionError, store.get, 'key_0')
