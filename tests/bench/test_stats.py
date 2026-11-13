"""bench's statistics and verdicts, on made-up samples.

    python3 -I -m unittest discover -s tests/bench -t tests/bench
"""

from __future__ import annotations

import json
import os
import random
import tempfile
import unittest

from support import measurement

from bench import samples, stats, verdict


def noisy(centre: float, spread: float, count: int, seed: int):
    generator = random.Random(seed)
    return [centre * (1 + generator.uniform(-spread, spread))
            for _ in range(count)]


class StatsTest(unittest.TestCase):
    def test_median(self) -> None:
        self.assertEqual(stats.median([3, 1, 2]), 2)
        self.assertEqual(stats.median([4, 1, 2, 3]), 2.5)
        with self.assertRaises(ValueError):
            stats.median([])

    def test_paired_ratio_and_interval(self) -> None:
        a = noisy(1.0, 0.01, 20, 1)
        b = [x * 0.5 for x in a]
        found = stats.paired(a, b)
        self.assertAlmostEqual(found.ratio, 0.5)
        self.assertAlmostEqual(found.low, 0.5)
        self.assertAlmostEqual(found.high, 0.5)
        self.assertEqual(found.count, 20)

    def test_paired_is_repeatable(self) -> None:
        a, b = noisy(1.0, 0.1, 15, 2), noisy(1.0, 0.1, 15, 3)
        self.assertEqual(stats.paired(a, b), stats.paired(a, b))

    def test_paired_needs_equal_counts_and_positive_samples(self) -> None:
        with self.assertRaises(ValueError):
            stats.paired([1.0, 2.0], [1.0])
        with self.assertRaises(ValueError):
            stats.paired([0.0], [1.0])

    def test_unpaired_ratio_of_medians(self) -> None:
        found = stats.unpaired([2.0, 2.0, 2.0], [1.0, 1.0, 1.0, 1.0])
        self.assertEqual((found.ratio, found.low, found.high), (0.5, 0.5, 0.5))
        self.assertEqual(found.count, 3)


class VerdictTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = self._tmp.name
        a = noisy(1.0, 0.01, 20, 4)
        self.noise = measurement(os.path.join(self.root, "aa"), a,
                                 noisy(1.0, 0.01, 20, 5))

    def decide(self, a, b, **options) -> verdict.Verdict:
        directory = measurement(os.path.join(self.root, "m"), a, b,
                                **options.pop("measured", {}))
        return verdict.decide(directory, self.noise, **options)

    def test_improved(self) -> None:
        a = noisy(1.0, 0.01, 10, 6)
        found = self.decide(a, [x * 0.7 for x in a])
        self.assertEqual(found.word, verdict.IMPROVED)
        self.assertIn("-30.0%", found.line)

    def test_regressed(self) -> None:
        a = noisy(1.0, 0.01, 10, 7)
        self.assertEqual(self.decide(a, [x * 1.2 for x in a]).word,
                         verdict.REGRESSED)

    def test_no_change_within_noise(self) -> None:
        a = noisy(1.0, 0.01, 20, 8)
        self.assertEqual(self.decide(a, noisy(1.0, 0.01, 20, 9)).word,
                         verdict.NO_CHANGE)

    def test_a_gain_smaller_than_the_minimum_effect_is_no_change(self) -> None:
        a = noisy(1.0, 0.001, 20, 10)
        self.assertEqual(self.decide(a, [x * 0.99 for x in a]).word,
                         verdict.NO_CHANGE)

    def test_inconclusive_when_too_noisy(self) -> None:
        a = noisy(1.0, 0.4, 10, 11)
        self.assertEqual(self.decide(a, noisy(1.0, 0.4, 10, 12)).word,
                         verdict.INCONCLUSIVE)

    def test_broken_comes_before_timing(self) -> None:
        a = noisy(1.0, 0.01, 10, 13)
        found = self.decide(a, [x * 0.5 for x in a],
                            measured={"broken": ["output differs"]})
        self.assertEqual(found.word, verdict.BROKEN)
        self.assertIn("output differs", found.line)

    def test_failed_tests_are_broken(self) -> None:
        a = noisy(1.0, 0.01, 10, 14)
        directory = measurement(os.path.join(self.root, "t"), a,
                                [x * 0.5 for x in a])
        samples.write_json(directory, samples.TESTS,
                           {"passed": False, "status": 1})
        self.assertEqual(verdict.decide(directory, self.noise).word,
                         verdict.BROKEN)

    def test_higher_is_better(self) -> None:
        a = noisy(100.0, 0.01, 10, 15)
        found = self.decide(a, [x * 1.5 for x in a], higher_is_better=True)
        self.assertEqual(found.word, verdict.IMPROVED)

    def test_guard_fails_on_growth_over_its_limit(self) -> None:
        a = noisy(1.0, 0.01, 10, 16)
        rss = noisy(1000.0, 0.01, 10, 17)
        found = self.decide(
            a, [x * 0.5 for x in a], guards={"rss_kib": 0.10},
            measured={"extra": {"rss_kib": [rss, [x * 1.5 for x in rss]]}})
        self.assertEqual(found.word, verdict.IMPROVED)
        self.assertIn("GUARD FAILED", found.line)
        self.assertTrue(found.data["guards_failed"])

    def test_min_effect_is_twice_the_noise_with_a_floor(self) -> None:
        self.assertEqual(verdict.min_effect(None), 0.02)
        self.assertEqual(verdict.min_effect(0.001), 0.02)
        self.assertAlmostEqual(verdict.min_effect(0.05), 0.10)


class ValuesTest(unittest.TestCase):
    def test_hyperfine_json_and_plain_lines(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            hyperfine = os.path.join(root, "h.json")
            with open(hyperfine, "w", encoding="utf-8") as stream:
                json.dump({"results": [{"times": [1.0, 2.0]},
                                       {"times": [3.0]}]}, stream)
            plain = os.path.join(root, "p.txt")
            with open(plain, "w", encoding="utf-8") as stream:
                stream.write("0.5\n0.25\n\n")
            self.assertEqual(samples.read_values(hyperfine), [1.0, 2.0])
            self.assertEqual(samples.read_values(f"{hyperfine}#1"), [3.0])
            self.assertEqual(samples.read_values(plain), [0.5, 0.25])
            with self.assertRaises(ValueError):
                samples.read_values(f"{plain}#1")


if __name__ == "__main__":
    unittest.main()
