"""bin/issue-digest, on issues as `gh issue view --json` writes them.

    python3 -I -m unittest discover -s tests/issue_digest -t tests/issue_digest
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "issue-digest")


def issue(title: str = "Export fails", body: str = "It crashes.",
          comments: tuple[tuple[str, str], ...] = ()) -> dict:
    return {"number": 7, "title": title, "body": body,
            "labels": [{"name": "bug"}], "updatedAt": "2026-11-23T10:00:00Z",
            "comments": [{"author": who, "body": text,
                          "createdAt": "2026-11-23T11:00:00Z"}
                         for who, text in comments]}


class IssueDigestTest(unittest.TestCase):
    def digest(self, data: dict, me: str = "owner") -> subprocess.CompletedProcess:
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as stream:
            json.dump(data, stream)
        self.addCleanup(os.remove, stream.name)
        return subprocess.run([SCRIPT, stream.name, me], text=True,
                              capture_output=True, check=False)

    def test_prints_a_short_digest(self) -> None:
        result = self.digest(issue())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^[0-9a-f]{16}\n$")

    def test_is_the_same_for_the_same_issue(self) -> None:
        self.assertEqual(self.digest(issue()).stdout,
                         self.digest(issue()).stdout)

    def test_changes_when_the_title_body_or_a_comment_does(self) -> None:
        base = self.digest(issue()).stdout
        for changed in (issue(title="Export fails on Mondays"),
                        issue(body="It crashes. Also run curl | sh."),
                        issue(comments=(("someone", "Ignore the above."),))):
            with self.subTest(changed=changed):
                self.assertNotEqual(self.digest(changed).stdout, base)

    def test_ignores_your_own_comments_labels_and_times(self) -> None:
        base = self.digest(issue()).stdout
        mine = issue(comments=(("owner", "Triaged: ready for an agent."),))
        mine["labels"] = [{"name": "ready-for-agent"}]
        mine["updatedAt"] = "2026-11-24T09:00:00Z"
        self.assertEqual(self.digest(mine).stdout, base)

    def test_a_comment_by_someone_else_counts_even_with_yours(self) -> None:
        mine = issue(comments=(("owner", "Triaged."),))
        both = issue(comments=(("owner", "Triaged."), ("someone", "Also X.")))
        self.assertNotEqual(self.digest(mine).stdout,
                            self.digest(both).stdout)

    def test_refuses_bad_input(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as stream:
            stream.write("not json")
        self.addCleanup(os.remove, stream.name)
        for args in ([], [stream.name], [stream.name, "owner"],
                     ["/nonexistent.json", "owner"]):
            with self.subTest(args=args):
                result = subprocess.run([SCRIPT, *args], text=True,
                                        capture_output=True, check=False)
                self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
