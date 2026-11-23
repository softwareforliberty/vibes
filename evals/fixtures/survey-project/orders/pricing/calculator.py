from orders.model import Customer, Line
from orders.pricing.base_price import base_price
from orders.pricing.discount import apply_discount
from orders.pricing.rounding import round_cents
from orders.pricing.tax import apply_tax


class PriceCalculator:
    """Prices lines. Call set_customer, then set_region, before total."""

    def __init__(self) -> None:
        self.tier = None
        self.region = None

    def set_customer(self, customer: Customer) -> None:
        self.tier = customer.tier

    def set_region(self, region: str) -> None:
        self.region = region

    def total(self, lines: list[Line]) -> int:
        cents = sum(base_price(line) for line in lines)
        cents = apply_discount(cents, self.tier)
        cents = apply_tax(cents, self.region)
        return round_cents(cents)
