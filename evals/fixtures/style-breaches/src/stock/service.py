"""Receive and ship stock."""

from dataclasses import replace
from typing import Optional

from stock.models import Item
from stock.repository import ItemRepository

DEFAULT_PAGE_SIZE = 50


class InsufficientStockError(ValueError):
    """Raised when a shipment needs more than is on hand."""


class StockService:
    """Change stock levels as goods arrive and leave."""

    def __init__(self, repository: ItemRepository) -> None:
        """Use the given repository for stock levels."""
        self._repository = repository

    def receive(self, sku: str, quantity: int) -> Item:
        """Add received goods to an item's stock."""
        if quantity < 1:
            raise ValueError("quantity must be at least 1")
        item = self._repository.get(sku)
        updated = replace(item, quantity=item.quantity + quantity)
        self._repository.save(updated)
        return updated

    def ship(self, sku: str, quantity: int) -> Item:
        """Remove shipped goods from an item's stock.

        Raises:
            InsufficientStockError: If fewer than quantity are on hand.
        """
        if quantity < 1:
            raise ValueError("quantity must be at least 1")
        item = self._repository.get(sku)
        if item.quantity < quantity:
            raise InsufficientStockError(sku)
        updated = replace(item, quantity=item.quantity - quantity)
        self._repository.save(updated)
        return updated

    def low_stock(
        self,
        threshold: int,
        name_contains: Optional[str] = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[Item]:
        """List the items running low, fewest on hand first.

        Args:
            threshold: Items with a quantity below this are included.
            name_contains: If given, keep only items whose name contains
                this text, ignoring case.
            page: Which page of results to return, starting at 1.
            page_size: How many items a page holds.

        Returns:
            One page of matching items, sorted by quantity and then by SKU.

        Raises:
            ValueError: If threshold is negative, or page or page_size is
                below 1.
        """
        if threshold < 0:
            raise ValueError("threshold must not be negative")
        if page < 1 or page_size < 1:
            raise ValueError("page and page_size must be at least 1")
        return self._repository.find_low_stock(
            threshold,
            name_contains=name_contains,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
