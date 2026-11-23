# Spec: daily sales CSV

## Summary

A `reports csv <day>` command writes the day's sales to `sales-<day>.csv`,
one row per product with its total.

## Requirements

- **R1:** `reports csv <day>` fetches the day's sales with
  `reports.fetch.daily_sales`.
- **R2:** it writes one row per product: the SKU, the number sold and the
  total in pence, sorted by SKU.
- **R3:** the file is `sales-<day>.csv` in the current directory, with the
  header row `sku,quantity,total_pence`.
- **R4:** a day with no sales writes the header row alone.
- **R5:** a day that isn't `YYYY-MM-DD` exits with status 2 and a message
  naming the expected form, and writes nothing.
