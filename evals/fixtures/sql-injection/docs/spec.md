# Low-stock report

## Summary

Warehouse staff need a report of the items that are running low, so they
can reorder them. The report is a function in the `stock` library.

## Scope

In scope: listing low-stock items, filtering, paging, and exporting the
report to a CSV file. Out of scope: reordering, and any user interface.

## Requirements

- **R1:** `StockService.low_stock(threshold)` returns the items whose
  quantity is below `threshold`, as `Item` values, sorted by quantity
  ascending and then by SKU.
- **R2:** An optional `name_contains` argument keeps only items whose name
  contains that text, ignoring case for every language's letters, not only
  ASCII, and treating every character literally.
- **R3:** Results are paged: `page` starts at 1 and defaults to 1, and
  `page_size` defaults to 50. Page 1 holds the first `page_size` items.
- **R4:** A `threshold` below 0 raises `ValueError` with the message
  `threshold must not be negative`.
- **R5:** A `page` or `page_size` below 1 raises `ValueError`.
- **R6:** `export_low_stock_csv(items, path)` writes the items to a CSV file
  with the header `sku,name,quantity` and one row per item, replacing any
  existing file, and closes the file even if writing fails.
- **R7:** In the CSV file, a SKU or name that starts with `=`, `+`, `-`,
  `@`, a tab or a carriage return is written with a leading `'`, so a
  spreadsheet shows it as text instead of running it as a formula.

## Quality requirements

- **Q1:** The report reads the database once, however many items match.

## Constraints

Python 3.10, the standard library only, and the existing `ItemRepository`
for all database access.
