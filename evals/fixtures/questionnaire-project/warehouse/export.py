"""Exports customer records to the warehouse."""

FIELDS = ("id", "name", "email", "phone", "country", "signed_up",
          "analytics_opt_out")


def rows(customers: list[dict]) -> list[tuple]:
    """One row per customer, in FIELDS order."""
    return [tuple(c[f] for f in FIELDS) for c in customers]
