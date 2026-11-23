"""tinyhttp's client: GET a URL and decode the JSON it returns."""

import json
import urllib.request

# Seconds before a request gives up, unless the caller passes timeout=.
DEFAULT_TIMEOUT = 10


def get_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """GET the URL and decode its JSON body."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read())
