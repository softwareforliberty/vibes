# tinyhttp

A tiny HTTP client.

    from tinyhttp import client
    client.get_json(url)

Requests time out after 30 seconds by default; pass `timeout=` to change
it.
