"""Totals the day's sales per product."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductTotal:
    sku: str
    quantity: int
    total_pence: int


def product_totals(sales: Iterable[dict]) -> list[ProductTotal]:
    """One total per SKU, sorted by SKU."""
    sums: dict[str, tuple[int, int]] = {}
    for sale in sales:
        quantity, pence = sums.get(sale["sku"], (0, 0))
        sums[sale["sku"]] = (quantity + sale["quantity"],
                             pence + sale["total_pence"])
    return [ProductTotal(sku, q, p) for sku, (q, p) in sorted(sums.items())]
