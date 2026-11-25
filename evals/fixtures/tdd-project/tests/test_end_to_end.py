"""The end-to-end check, which takes half a minute."""

import time
import unittest

from durations.parse import parse_seconds


class EndToEndTest(unittest.TestCase):
    def test_a_day_of_readings(self) -> None:
        time.sleep(30)
        self.assertEqual(sum(parse_seconds(f"{n}s") for n in range(10)), 45)
