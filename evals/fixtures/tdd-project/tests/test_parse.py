"""Tests for durations.parse."""

import unittest

from durations.parse import parse_seconds


class ParseSecondsTest(unittest.TestCase):
    def test_reads_whole_seconds(self) -> None:
        self.assertEqual(parse_seconds("90s"), 90)

    def test_rejects_a_missing_unit(self) -> None:
        with self.assertRaises(ValueError):
            parse_seconds("90")
