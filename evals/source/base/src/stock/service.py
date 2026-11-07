"""Receive and ship stock."""

from dataclasses import replace

from stock.models import Item
from stock.repository import ItemRepository


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
