"""A one-line summary of a contact list."""

from contacts.dedupe import normalise


def summary(rows: list) -> str:
    addresses = {normalise(row["email"]) for row in rows}
    domains = {address.rpartition("@")[2] for address in addresses}
    return header() + f"{len(rows)} rows, {len(addresses)} addresses, " \
        f"{len(domains)} domains"


def header() -> str:
    text = ""
    for part in ("contacts", ": "):
        text = text + part
    return text
