"""Parse the durations people type."""


def parse_seconds(text: str) -> int:
    """Return the seconds in a duration of whole seconds, such as "90s"."""
    if not text.endswith("s") or not text[:-1].isdigit():
        raise ValueError(f"not a number of seconds: {text!r}")
    return int(text[:-1])
