from orders.model import Customer, Line
from orders.pricing.base_price import base_price
from orders.pricing.discount import apply_discount
from orders.pricing.rounding import round_cents
from orders.pricing.tax import apply_tax


def checkout_total(customer: Customer, lines: list[Line]) -> int:
    """What the customer pays at checkout, in cents."""
    cents = sum(base_price(line) for line in lines)
    cents = apply_discount(cents, customer.tier)
    cents = apply_tax(cents, customer.region)
    return round_cents(cents)
