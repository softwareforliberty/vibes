from orders.model import Customer, Line
from orders.pricing.calculator import PriceCalculator


def quote(customer: Customer, lines: list[Line]) -> int:
    """A quote for the lines, in cents."""
    calculator = PriceCalculator()
    calculator.set_customer(customer)
    calculator.set_region(customer.region)
    return calculator.total(lines)
