"""Fetches the day's sales from the shop."""

from vendor.tinyhttp import client


def daily_sales(base_url: str, day: str) -> dict:
    """The day's sales, as the shop's API returns them."""
    return client.get_json(f"{base_url}/sales/{day}")
