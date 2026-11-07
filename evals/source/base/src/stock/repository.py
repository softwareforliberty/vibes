"""Store and load items in SQLite."""

import sqlite3

from stock.models import Item


class ItemNotFoundError(LookupError):
    """Raised when no item has the requested SKU."""


class ItemRepository:
    """Store and load items in an SQLite database."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Use the given database connection."""
        self._connection = connection

    def get(self, sku: str) -> Item:
        """Load the item with the given SKU.

        Raises:
            ItemNotFoundError: If no item has that SKU.
        """
        row = self._connection.execute(
            "SELECT sku, name, quantity FROM item WHERE sku = ?",
            (sku,),
        ).fetchone()
        if row is None:
            raise ItemNotFoundError(sku)
        return Item(*row)

    def save(self, item: Item) -> None:
        """Save the item, replacing any item stored with its SKU."""
        with self._connection:
            self._connection.execute(
                "INSERT OR REPLACE INTO item (sku, name, quantity) VALUES (?, ?, ?)",
                (item.sku, item.name, item.quantity),
            )
