RATES = {"standard": 0.0, "silver": 0.05, "gold": 0.10}


def apply_discount(cents: float, tier: str) -> float:
    """The amount after the customer tier's discount."""
    return cents * (1 - RATES[tier])
