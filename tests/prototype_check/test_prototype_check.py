"""bin/prototype-check, on logic prototypes that keep and break its rules.

    python3 -I -m unittest discover -s tests/prototype_check -t tests/prototype_check
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "prototype-check")

LOGIC = """
export function step(state, action) {
  if (action === "cancel" && state.shipped > 0) return state;
  return { ...state, status: action };
}
"""

GOOD = """<!doctype html>
<html><head><meta charset="utf-8"><title>Cancelling orders</title>
<style>body { font-family: sans-serif; }</style></head>
<body>
<p id="question">Can an order be cancelled once part of it has shipped?</p>
<div id="state"></div>
<button data-action="cancel">Cancel the order</button>
<section data-scenario="Nothing shipped yet">
  <p>Cancel before anything ships.</p>
  <button data-step="1">Cancel the order</button>
</section>
<section data-scenario="Part shipped">
  <p>Ship one parcel, then try to cancel.</p>
  <button data-step="1">Ship a parcel</button>
  <button data-step="2">Cancel the order</button>
</section>
<script id="logic">LOGIC</script>
<script>
  document.querySelector("#state").textContent = "ready";
</script>
</body></html>
""".replace("LOGIC", LOGIC)


def check(html: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                     encoding="utf-8") as stream:
        stream.write(html)
    try:
        return subprocess.run([SCRIPT, stream.name], text=True,
                              capture_output=True, check=False)
    finally:
        os.remove(stream.name)


class PrototypeCheckTest(unittest.TestCase):
    def test_passes_a_self_contained_prototype(self) -> None:
        result = check(GOOD)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout,
                         "PROTOTYPE OK: 2 scenarios, 3 steps\n")

    def test_fails_anything_loaded_from_outside(self) -> None:
        for extra in ('<script src="https://cdn.example/x.js"></script>',
                      '<link rel="stylesheet" href="https://f.example/a.css">',
                      '<img src="http://example.com/a.png">',
                      '<style>@import url("https://f.example/b.css");</style>',
                      '<script>fetch("/api/orders")</script>'):
            with self.subTest(extra=extra):
                result = check(GOOD.replace("</body>", extra + "</body>"))
                self.assertEqual(result.returncode, 1)
                self.assertIn("loads from outside", result.stdout)

    def test_the_logic_never_touches_the_page(self) -> None:
        for leak in ("document.title = 'x';", "window.state = 1;",
                     "el.addEventListener('click', f);",
                     "localStorage.setItem('a', 1);"):
            with self.subTest(leak=leak):
                result = check(GOOD.replace(LOGIC, LOGIC + leak))
                self.assertEqual(result.returncode, 1)
                self.assertIn("the logic touches the page", result.stdout)

    def test_needs_the_logic_the_question_and_two_scenarios(self) -> None:
        cases = {
            "no logic block": GOOD.replace('<script id="logic">', "<script>"),
            "no question": GOOD.replace('id="question"', 'id="intro"'),
            "fewer than two scenarios": GOOD.replace(
                'data-scenario="Part shipped"', 'class="x"'),
            "a scenario with no steps": GOOD.replace(
                '<button data-step="1">Cancel the order</button>', ""),
        }
        for problem, html in cases.items():
            with self.subTest(problem=problem):
                result = check(html)
                self.assertEqual(result.returncode, 1)
                self.assertIn(problem, result.stdout)

    def test_refuses_bad_arguments(self) -> None:
        for args in ([], ["/nonexistent.html"], ["a.html", "b.html"]):
            with self.subTest(args=args):
                result = subprocess.run([SCRIPT, *args], text=True,
                                        capture_output=True, check=False)
                self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
