"""The reports command line."""

import re
import sys

from reports.csv_output import write_totals
from reports.fetch import daily_sales
from reports.totals import product_totals

BASE_URL = "https://shop.example.invalid/api"
DAY = re.compile(r"\d{4}-\d{2}-\d{2}")


def main(argv: list[str]) -> int:
    """Run `csv <day>`."""
    if len(argv) != 2 or argv[0] != "csv" or not DAY.fullmatch(argv[1]):
        print("usage: reports csv YYYY-MM-DD", file=sys.stderr)
        return 2
    day = argv[1]
    sales = daily_sales(BASE_URL, day)["sales"]
    with open(f"sales-{day}.csv", "w", newline="", encoding="utf-8") as out:
        write_totals(product_totals(sales), out)
    return 0
