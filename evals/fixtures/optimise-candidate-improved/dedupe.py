"""Removes duplicate contacts, keeping the first row for each address."""


def normalise(email: str) -> str:
    """The form of an address that duplicates share."""
    return email.strip().lower()


def dedupe(rows: list) -> list:
    """The rows with a new address, in their original order."""
    kept = []
    seen = set()
    for row in rows:
        key = normalise(row["email"])
        if key not in seen:
            seen.add(key)
            kept.append(row)
    return kept
