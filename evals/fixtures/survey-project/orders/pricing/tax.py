RATES = {"UK": 0.20, "EU": 0.21, "US": 0.0}


def apply_tax(cents: float, region: str) -> float:
    """The amount with the region's tax added."""
    return cents * (1 + RATES[region])
