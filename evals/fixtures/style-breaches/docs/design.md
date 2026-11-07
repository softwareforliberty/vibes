# Low-stock report design

## Kind of software

A library: the core logic in `stock.service`, with SQLite access confined to
`stock.repository`.

## Components

- `ItemRepository.find_low_stock(threshold, *, name_contains, limit,
  offset) -> list[Item]`: one parameterised query that filters, sorts and
  pages in SQL. Names are matched with `instr` on a `casefold` SQL function
  the repository registers, because SQLite only folds ASCII case.
- `StockService.low_stock(threshold, *, name_contains=None, page=1,
  page_size=50) -> list[Item]`: validates its arguments, turns the page
  into a limit and offset, and calls the repository.
- `stock.report.export_low_stock_csv(items, path) -> None`: writes the CSV
  with the `csv` module, prefixing text that would run as a formula.

## Traceability

| Id | Components |
| --- | --- |
| R1, R2, R3, Q1 | `ItemRepository.find_low_stock`, `StockService.low_stock` |
| R4, R5 | `StockService.low_stock` |
| R6, R7 | `stock.report.export_low_stock_csv` |
