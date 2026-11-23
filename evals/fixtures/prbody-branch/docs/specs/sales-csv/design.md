# Design: daily sales CSV

## Components

### Totals: `reports.totals`

- **Job:** sums the day's sales per SKU, sorted by SKU (R2, R4).
- **Entry points:** `product_totals`, `ProductTotal`.

### CSV output: `reports.csv_output`

- **Job:** writes the header and one row per total (R2, R3, R4).
- **Entry points:** `write_totals`.

### Command: `reports.cli`

- **Job:** parses `csv <day>`, validates the day, and wires the rest (R1,
  R3, R5).
- **Entry points:** `main`.

## Boundary rules

- `reports.totals` never imports `reports.cli` or `reports.csv_output`.
- Outside each component, code and the component's tests use only its
  entry points.
