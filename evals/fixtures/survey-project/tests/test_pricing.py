import unittest

from orders.pricing.discount import apply_discount
from orders.pricing.rounding import round_cents
from orders.pricing.tax import apply_tax


class PricingTest(unittest.TestCase):
    def test_gold_gets_ten_percent(self) -> None:
        self.assertEqual(apply_discount(1000, "gold"), 900)

    def test_uk_tax_is_twenty_percent(self) -> None:
        self.assertEqual(apply_tax(1000, "UK"), 1200)

    def test_rounds_half_up(self) -> None:
        self.assertEqual(round_cents(10.5), 11)
