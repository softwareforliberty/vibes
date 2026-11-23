from orders.model import Line


def base_price(line: Line) -> int:
    """The line's price before discount and tax, in cents."""
    return line.product.price_cents * line.quantity
