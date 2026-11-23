"""Invoices and their lines."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Invoice:
    """An invoice, with its total in cents."""

    number: str
    customer: str
    total_cents: int
