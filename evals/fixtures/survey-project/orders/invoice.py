from orders.model import Customer, Line
from orders.pricing.base_price import base_price
from orders.pricing.discount import apply_discount
from orders.pricing.rounding import round_cents
from orders.pricing.tax import apply_tax


def invoice_lines(customer: Customer, lines: list[Line]) -> list[int]:
    """Each line's price on the invoice, in cents."""
    prices = []
    for line in lines:
        cents = apply_tax(base_price(line), customer.region)
        cents = apply_discount(cents, customer.tier)
        prices.append(round_cents(cents))
    return prices
