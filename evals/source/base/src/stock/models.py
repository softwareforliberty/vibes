"""The stock domain model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    """A stocked item and how many of it are on hand."""

    sku: str
    name: str
    quantity: int
