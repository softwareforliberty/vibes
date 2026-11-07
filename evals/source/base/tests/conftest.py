import sqlite3
from collections.abc import Iterator

import pytest

from stock.repository import ItemRepository

SCHEMA = (
    "CREATE TABLE item"
    " (sku TEXT PRIMARY KEY, name TEXT NOT NULL, quantity INTEGER NOT NULL)"
)


@pytest.fixture
def connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(":memory:")
    connection.execute(SCHEMA)
    yield connection
    connection.close()


@pytest.fixture
def repository(connection: sqlite3.Connection) -> ItemRepository:
    return ItemRepository(connection)
