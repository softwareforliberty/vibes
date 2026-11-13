import unittest

from contacts.dedupe import dedupe
from contacts.summary import summary


def row(name: str, email: str) -> dict:
    return {"name": name, "email": email}


class DedupeTest(unittest.TestCase):
    def test_keeps_the_first_row_for_each_address(self) -> None:
        rows = [row("Ann", "ann@example.com"), row("Bo", "bo@example.com"),
                row("Ann 2", "ann@example.com")]
        self.assertEqual(dedupe(rows), rows[:2])

    def test_ignores_case_and_surrounding_spaces(self) -> None:
        rows = [row("Ann", "Ann@Example.com"), row("Ann 2", " ann@example.COM ")]
        self.assertEqual(dedupe(rows), rows[:1])

    def test_keeps_the_original_order(self) -> None:
        rows = [row("C", "c@x.org"), row("A", "a@x.org"), row("B", "b@x.org")]
        self.assertEqual(dedupe(rows), rows)

    def test_empty(self) -> None:
        self.assertEqual(dedupe([]), [])


class SummaryTest(unittest.TestCase):
    def test_counts_rows_addresses_and_domains(self) -> None:
        rows = [row("A", "a@x.org"), row("A2", "A@x.org"), row("B", "b@y.org")]
        self.assertEqual(summary(rows),
                         "contacts: 3 rows, 2 addresses, 2 domains")


if __name__ == "__main__":
    unittest.main()
