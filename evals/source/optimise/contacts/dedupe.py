"""Removes duplicate contacts, keeping the first row for each address."""


def normalise(email: str) -> str:
    """The form of an address that duplicates share."""
    return email.strip().lower()


def dedupe(rows: list) -> list:
    """The rows with a new address, in their original order."""
    kept = []
    seen = []
    for row in rows:
        key = normalise(row["email"])
        if not _is_seen(key, seen):
            seen.append(key)
            kept.append(row)
    return kept


def _is_seen(key: str, seen: list) -> bool:
    for other in seen:
        if other == key:
            return True
    return False
