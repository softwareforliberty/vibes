# Architecture

## Money

Every amount of money is an `int` number of cents, in every layer: models,
storage and the public API. Never use `float` or `Decimal` for money, and
never store or return dollars. Round only when converting a rate to cents,
half up, to the nearest cent.

## Storage

Only `invoices/repository.py` runs SQL. Services call the repository.
