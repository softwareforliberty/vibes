"""Export stock reports."""

import csv
from collections.abc import Iterable
from pathlib import Path

from stock.models import Item

# Spreadsheets run a cell that starts with one of these as a formula.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _neutralise(text: str) -> str:
    """Stop a spreadsheet from running text as a formula."""
    return f"'{text}" if text.startswith(_FORMULA_PREFIXES) else text


def export_low_stock_csv(items: Iterable[Item], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["sku", "name", "quantity"])
        for item in items:
            writer.writerow(
                [_neutralise(item.sku), _neutralise(item.name), item.quantity]
            )
