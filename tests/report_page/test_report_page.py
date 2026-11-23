"""bin/report-page, on small reports.

    python3 -I -m unittest discover -s tests/report_page -t tests/report_page
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "report-page")

REPORT = """# Survey: orders

```mermaid
graph LR
  A --> B
```

A quoted line of code: `</script><script>alert(1)</script>`
"""


class ReportPageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.mkdtemp()
        self.source = os.path.join(self.directory, "survey.md")
        self.target = os.path.join(self.directory, "survey.html")
        with open(self.source, "w", encoding="utf-8") as stream:
            stream.write(REPORT)

    def tearDown(self) -> None:
        shutil.rmtree(self.directory)

    def build(self) -> str:
        found = subprocess.run([SCRIPT, self.source, self.target],
                               capture_output=True, text=True, check=False)
        self.assertEqual(found.returncode, 0, found.stderr)
        with open(self.target, encoding="utf-8") as stream:
            return stream.read()

    def test_titles_the_page_with_the_first_heading(self) -> None:
        self.assertIn("<title>Survey: orders</title>", self.build())

    def test_the_report_cannot_end_its_script_early(self) -> None:
        text = self.build()
        self.assertEqual(text.count("</script>"), 5)
        source = re.search(r"const SOURCE = (.*?);</script>", text).group(1)
        self.assertEqual(json.loads(source), REPORT)

    def test_shows_the_text_without_the_libraries(self) -> None:
        self.assertIn('<pre id="fallback"># Survey: orders', self.build())
        self.assertIn("&lt;/script&gt;&lt;script&gt;alert(1)", self.build())

    def test_pins_and_checks_every_library(self) -> None:
        for tag in re.findall(r"<script src=[^>]*>", self.build()):
            with self.subTest(tag=tag):
                self.assertRegex(tag, r'src="https://cdn\.jsdelivr\.net/npm/'
                                      r'[a-z]+@\d+\.\d+\.\d+/')
                self.assertRegex(tag, r'integrity="sha384-[A-Za-z0-9+/=]+"')

    def test_errors_exit_2(self) -> None:
        for args in ((), (self.source,), ("/no/such.md", self.target)):
            with self.subTest(args=args):
                self.assertEqual(subprocess.run(
                    [SCRIPT, *args], capture_output=True,
                    check=False).returncode, 2)


if __name__ == "__main__":
    unittest.main()
