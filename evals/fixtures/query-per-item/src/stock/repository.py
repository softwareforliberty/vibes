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
        # SQLite only folds the case of ASCII letters, so name searches
        # use Python's full Unicode case folding instead.
        connection.create_function("casefold", 1, str.casefold, deterministic=True)

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

    def find_low_stock(
        self,
        threshold: int,
        *,
        name_contains: str | None,
        limit: int,
        offset: int,
    ) -> list[Item]:
        """Load items with fewer than threshold on hand, fewest first.

        Args:
            threshold: Items with a quantity below this are included.
            name_contains: If given, keep only items whose name contains
                this text, ignoring case.
            limit: The most items to return.
            offset: How many matching items to skip.

        Returns:
            The matching items, sorted by quantity and then by SKU.
        """
        needle = "" if name_contains is None else name_contains.casefold()
        rows = self._connection.execute(
            "SELECT sku FROM item"
            " WHERE quantity < ? AND instr(casefold(name), ?) > 0"
            " ORDER BY quantity, sku LIMIT ? OFFSET ?",
            (threshold, needle, limit, offset),
        ).fetchall()
        return [self.get(sku) for (sku,) in rows]
