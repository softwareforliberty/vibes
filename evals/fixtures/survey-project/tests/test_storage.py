import unittest

from orders.storage import OrderStore


class StorageTest(unittest.TestCase):
    def test_loads_what_it_saved(self) -> None:
        store = OrderStore(":memory:")
        store.save("A-1", {"total": 1200})
        self.assertEqual(store.load("A-1"), {"total": 1200})
        store.close()
