"""The things an order is made of."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    sku: str
    price_cents: int


@dataclass(frozen=True)
class Customer:
    name: str
    tier: str  # "standard", "silver" or "gold"
    region: str  # "UK", "EU" or "US"


@dataclass(frozen=True)
class Line:
    product: Product
    quantity: int
