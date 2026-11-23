"""Writes product totals as CSV."""

import csv
from collections.abc import Iterable
from typing import TextIO

from reports.totals import ProductTotal

HEADER = ("sku", "quantity", "total_pence")


def write_totals(totals: Iterable[ProductTotal], stream: TextIO) -> None:
    """The header, then one row per total, in the order given."""
    writer = csv.writer(stream)
    writer.writerow(HEADER)
    for total in totals:
        writer.writerow((total.sku, total.quantity, total.total_pence))
