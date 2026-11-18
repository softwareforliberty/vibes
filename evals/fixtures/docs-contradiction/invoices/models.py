"""Invoices and their payments."""

from dataclasses import dataclass


@dataclass
class Invoice:
    number: str
    total_cents: int
    paid_cents: int = 0
