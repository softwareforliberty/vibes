"""Where orders are kept: one small interface over SQLite."""

import json
import sqlite3


class OrderStore:
    """Saves and loads orders by number. Callers never see SQL."""

    def __init__(self, path: str) -> None:
        self._db = sqlite3.connect(path)
        self._db.execute("CREATE TABLE IF NOT EXISTS orders "
                         "(number TEXT PRIMARY KEY, body TEXT NOT NULL)")

    def save(self, number: str, order: dict) -> None:
        with self._db:
            self._db.execute("INSERT OR REPLACE INTO orders VALUES (?, ?)",
                             (number, json.dumps(order, sort_keys=True)))

    def load(self, number: str) -> dict:
        row = self._db.execute("SELECT body FROM orders WHERE number = ?",
                               (number,)).fetchone()
        if row is None:
            raise KeyError(number)
        return json.loads(row[0])

    def close(self) -> None:
        self._db.close()
