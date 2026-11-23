"""Exports invoices as CSV."""

import csv
import io

from invoices.models import Invoice


def export(invoices: list[Invoice]) -> str:
    """The invoices as CSV, one row each, with a header."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["number", "customer", "total_cents"])
    for invoice in invoices:
        writer.writerow([invoice.number, invoice.customer, invoice.total_cents])
    return out.getvalue()
