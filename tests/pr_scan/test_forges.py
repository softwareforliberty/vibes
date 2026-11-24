"""The forge's record of a pull request, from GitHub, GitLab and Forgejo,
and pr-prepare choosing each forge's CLI.

Run with: python3 -I -m unittest discover -s tests/pr_scan -t tests/pr_scan
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from support import Repo, rules_of

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "lib"))
from pr_scan import forge  # noqa: E402

PREPARE = os.path.join(ROOT, "bin", "pr-prepare")
SCAN = os.path.join(ROOT, "bin", "pr-scan")
HEAD = "a" * 40
OTHER = "b" * 40

MERGE_REQUEST = {"iid": 7, "title": "Fix", "description": "Body",
                 "author": {"username": "newcomer"}, "sha": HEAD,
                 "target_branch": "main", "first_contribution": True}
PROJECT = {"http_url_to_repo": "https://gitlab.example/group/app.git"}
PULL = {"title": "Fix", "body": "Body", "user": {"login": "newcomer"},
        "head": {"sha": HEAD}, "base": {"ref": "main", "repo": {
            "clone_url": "https://codeberg.org/group/app.git"}}}


def write(directory: str, name: str, value: object) -> None:
    path = os.path.join(directory, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            json.dump(value, stream)


class RecordTest(unittest.TestCase):
    def setUp(self) -> None:
        self.meta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.meta)

    def record(self, name: str) -> subprocess.CompletedProcess:
        return subprocess.run([SCAN, "record", "--forge", name, "--meta",
                               self.meta], text=True, capture_output=True,
                              check=False)

    def test_gitlab(self) -> None:
        write(self.meta, "merge-request.json", MERGE_REQUEST)
        write(self.meta, "project.json", PROJECT)
        write(self.meta, "commits.json",
              json.dumps({"id": HEAD}) + "\n" + json.dumps({"id": OTHER}))
        write(self.meta, f"signatures/{HEAD}.json",
              {"verification_status": "verified"})
        result = self.record("gitlab")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            f"HEAD {HEAD}", "BASE main",
            "URL https://gitlab.example/group/app.git"])
        with open(os.path.join(self.meta, "pr.json"),
                  encoding="utf-8") as stream:
            record = json.load(stream)
        self.assertEqual((record["author"], record["first_time"]),
                         ("newcomer", True))
        # Signed and verified, and unsigned: GitLab's 404 left no file.
        self.assertEqual(record["commits"], [
            {"sha": HEAD, "verified": True, "author": None},
            {"sha": OTHER, "verified": None, "author": None}])

    def test_forgejo(self) -> None:
        write(self.meta, "pull.json", PULL)
        write(self.meta, "commits-1.json", [
            {"sha": HEAD, "author": {"login": "newcomer"},
             "commit": {"verification": {"verified": True}}},
            {"sha": OTHER, "author": None,
             "commit": {"verification": {"verified": False}}}])
        write(self.meta, "commits-2.json", [])
        self.assertEqual(self.record("forgejo").returncode, 0)
        record = forge.load("forgejo", self.meta)
        self.assertIsNone(record["first_time"])
        self.assertEqual(record["commits"], [
            {"sha": HEAD, "verified": True, "author": "newcomer"},
            {"sha": OTHER, "verified": False, "author": ""}])

    def test_one_commit_is_still_a_list(self) -> None:
        write(self.meta, "pull.json", {"user": {"login": "a"}})
        write(self.meta, "commits.json", json.dumps(
            {"sha": HEAD, "author": {"login": "a"},
             "commit": {"verification": {"verified": True}}}) + "\n")
        self.assertEqual(forge.load("github", self.meta)["commits"],
                         [{"sha": HEAD, "verified": True, "author": "a"}])

    def test_an_error_page_means_no_commits_listed(self) -> None:
        write(self.meta, "pull.json", PULL)
        write(self.meta, "commits-1.json", {"message": "not found"})
        self.assertIsNone(forge.load("forgejo", self.meta)["commits"])

    def test_refuses_what_git_would_be_given_badly(self) -> None:
        for change in ({"head": {"sha": "--upload-pack=x"}},
                       {"base": {"ref": "main;rm", "repo": PULL["base"]
                                 ["repo"]}},
                       {"base": {"ref": "main", "repo": {
                           "clone_url": "http://codeberg.org/a/b.git"}}},
                       {"base": {"ref": "main", "repo": {
                           "clone_url": "file:///etc"}}}):
            with self.subTest(change=change):
                write(self.meta, "pull.json", {**PULL, **change})
                result = self.record("forgejo")
                self.assertEqual(result.returncode, 2)
                self.assertFalse(os.path.exists(
                    os.path.join(self.meta, "pr.json")))

    def test_an_error_answer_from_tea_is_refused(self) -> None:
        write(self.meta, "pull.json", {"message": "The target couldn't be "
                                       "found.", "url": "https://x"})
        self.assertEqual(self.record("forgejo").returncode, 2)


class HistoryTest(unittest.TestCase):
    """The history checks, from each forge's record."""

    def scan(self, record: dict) -> set:
        repo = Repo({"src/main.c": "int main(void) { return 0; }\n"})
        try:
            repo.write({"src/x.c": "int x;\n"})
            sha = repo.commit("Change", "Base Author <base@example.com>")
            for item in record.get("commits") or []:
                item["sha"] = sha
            return rules_of(repo.scan({"record": record}))
        finally:
            repo.cleanup()

    def test_gitlab_unsigned_claim_is_impersonation(self) -> None:
        found = self.scan(forge.from_gitlab(
            MERGE_REQUEST, [{"id": HEAD}], PROJECT, {}))
        self.assertIn("history-impersonation", found)
        self.assertIn("history-unverified", found)
        self.assertIn("history-first-time", found)
        # GitLab links no commit to an account: said, never passed.
        self.assertIn("history-unchecked", found)
        self.assertNotIn("history-other-author", found)

    def test_forgejo_says_it_cant_tell_who_is_new(self) -> None:
        found = self.scan(forge.from_forgejo(PULL, [[
            {"sha": HEAD, "author": {"login": "someone-else"},
             "commit": {"verification": {"verified": True}}}]]))
        self.assertIn("history-unchecked", found)
        self.assertIn("history-other-author", found)
        self.assertIn("history-impersonation", found)

    def test_unlisted_commits_are_said_to_be_unchecked(self) -> None:
        found = self.scan(forge.from_forgejo(PULL, None))
        self.assertIn("history-unchecked", found)


# Records what it's run with, then prints the answer the test gave for it.
FAKE_CLI = """#!/bin/sh
printf '%s\\n' "$*" >> "{log}"
case "$*" in
{cases}
  *) echo '{{}}' ;;
esac
"""


class PrepareTest(unittest.TestCase):
    """pr-prepare picks the forge and its CLI, and fetches from the address
    the forge's record gives."""

    def setUp(self) -> None:
        self.dir = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        self.repo = os.path.join(self.dir, "repo")
        self.bin = os.path.join(self.dir, "bin")
        self.log = os.path.join(self.dir, "calls.log")
        os.makedirs(self.bin)
        subprocess.run(["git", "init", "-q", "-b", "main", self.repo],
                       check=True)
        subprocess.run(["git", "-C", self.repo, "-c", "user.name=t", "-c",
                        "user.email=t@example.com", "commit", "-q",
                        "--allow-empty", "-m", "Start"], check=True)

    def cli(self, name: str, cases: dict) -> None:
        body = "\n".join(f"  *'{pattern}'*) cat <<'JSON'\n"
                         f"{json.dumps(answer)}\nJSON\n  ;;"
                         for pattern, answer in cases.items())
        path = os.path.join(self.bin, name)
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(FAKE_CLI.format(log=self.log, cases=body))
        os.chmod(path, 0o755)

    def remote(self, url: str) -> None:
        subprocess.run(["git", "-C", self.repo, "remote", "add", "origin",
                        url], check=True)

    def prepare(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [PREPARE, *args], cwd=self.repo, text=True, capture_output=True,
            check=False, env={**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}",
                              "GIT_TERMINAL_PROMPT": "0"})

    def calls(self) -> list[str]:
        with open(self.log, encoding="utf-8") as stream:
            return stream.read().splitlines()

    def prepare_log(self, number: str) -> str:
        with open(os.path.join(self.repo, ".vibes", f"pr-{number}",
                               "prepare.log"), encoding="utf-8") as stream:
            return stream.read()

    def test_gitlab_by_its_address(self) -> None:
        self.cli("glab", {"merge_requests/7/commits": {"id": HEAD},
                          "merge_requests/7": MERGE_REQUEST,
                          "/signature": {"verification_status": "verified"},
                          "projects/:fullpath": PROJECT})
        result = self.prepare("https://gitlab.example/group/app/-/"
                              "merge_requests/7/diffs")
        self.assertEqual(result.returncode, 2)
        self.assertIn("git couldn't fetch", result.stderr)
        calls = self.calls()
        self.assertIn("api projects/:fullpath/merge_requests/7", calls)
        self.assertIn(f"api projects/:fullpath/repository/commits/{HEAD}/"
                      "signature", calls)
        self.assertIn("gitlab.example/group/app.git", self.prepare_log("7"))
        with open(os.path.join(self.repo, ".vibes", "pr-7", "meta",
                               "pr.json"), encoding="utf-8") as stream:
            self.assertEqual(json.load(stream)["forge"], "gitlab")

    def test_forgejo_by_the_remote(self) -> None:
        self.remote("git@codeberg.org:group/app.git")
        self.cli("tea", {"api --help": {}, "commits?page=1": [],
                         "pulls/12": PULL})
        result = self.prepare("12")
        self.assertEqual(result.returncode, 2)
        self.assertIn("git couldn't fetch", result.stderr)
        self.assertIn("api /repos/{owner}/{repo}/pulls/12", self.calls())
        with open(os.path.join(self.repo, ".vibes", "pr-12", "meta",
                               "pr.json"), encoding="utf-8") as stream:
            record = json.load(stream)
        self.assertEqual((record["forge"], record["commits"]),
                         ("forgejo", []))

    def test_a_record_that_fails_its_checks_fetches_nothing(self) -> None:
        self.remote("https://codeberg.org/group/app.git")
        self.cli("tea", {"api --help": {}, "pulls/12": {"message": "no"}})
        result = self.prepare("12")
        self.assertEqual(result.returncode, 2)
        self.assertIn("didn't check out", result.stderr)

    def test_an_unknown_forge_needs_telling(self) -> None:
        self.remote("https://git.example.org/group/app.git")
        result = self.prepare("12")
        self.assertEqual(result.returncode, 2)
        self.assertIn("can't tell which forge", result.stderr)

    def test_a_named_forge_wins(self) -> None:
        self.remote("https://git.example.org/group/app.git")
        self.cli("tea", {"api --help": {}, "pulls/12": PULL})
        self.prepare("--forge", "forgejo", "12")
        self.assertIn("api /repos/{owner}/{repo}/pulls/12", self.calls())

    def test_fetch_checks_its_ref(self) -> None:
        self.remote("https://git.example.org/group/app.git")
        for ref in ("--upload-pack=x", "a..b", "refs/x;y"):
            with self.subTest(ref=ref):
                result = self.prepare("--fetch", "origin", ref)
                self.assertEqual(result.returncode, 2)
                self.assertIn("not a ref", result.stderr)
        result = self.prepare("--fetch", "nowhere", "refs/pull/1/head")
        self.assertIn("no such remote", result.stderr)


if __name__ == "__main__":
    unittest.main()
