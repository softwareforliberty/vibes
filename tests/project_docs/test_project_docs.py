"""bin/project-docs, given paths as git ls-files prints them.

    python3 -I -m unittest discover -s tests/project_docs -t tests/project_docs
"""

from __future__ import annotations

import os
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "project-docs")


def docs(*paths: str, args: tuple[str, ...] = ()) -> list[str]:
    result = subprocess.run([SCRIPT, *args], input="\n".join(paths) + "\n",
                            text=True, capture_output=True, check=True)
    return result.stdout.splitlines()


class ProjectDocsTest(unittest.TestCase):
    def test_finds_guidance_anywhere(self) -> None:
        found = ("ARCHITECTURE.md", "CLAUDE.md", "README.md",
                 "docs/adr/0001-use-postgres.md", "docs/build.txt",
                 "docs/specs/display-core/spec.md", "guide/index.rst",
                 "src/parser/README.adoc", ".cursorrules",
                 ".cursor/rules/style.mdc")
        self.assertEqual(docs(*found, "src/main.c", "Makefile"),
                         sorted(found))

    def test_skips_records_licences_and_templates(self) -> None:
        self.assertEqual(docs("CHANGELOG.md", "LICENSE.md", "COPYING",
                              "NOTICE.txt", "AUTHORS.md",
                              "CODE_OF_CONDUCT.md", "HISTORY.rst",
                              ".github/PULL_REQUEST_TEMPLATE.md",
                              ".github/ISSUE_TEMPLATE/bug.md"), [])

    def test_skips_other_peoples_docs_and_test_data(self) -> None:
        self.assertEqual(docs("node_modules/left-pad/README.md",
                              "vendor/zlib/README.md",
                              "third_party/qemu/docs/boot.rst",
                              "tests/fixtures/sample.md",
                              "pkg/testdata/input.md",
                              ".vibes/task/state.md"), [])

    def test_plain_text_only_in_doc_directories(self) -> None:
        self.assertEqual(docs("requirements.txt", "CMakeLists.txt",
                              "docs/notes.txt", "adr/0002.txt"),
                         ["adr/0002.txt", "docs/notes.txt"])

    def test_excludes_the_tasks_own_spec(self) -> None:
        self.assertEqual(
            docs("docs/specs/export/spec.md", "docs/specs/export/design.md",
                 "docs/specs/export-v2/spec.md", "README.md",
                 args=("--exclude", "./docs/specs/export/")),
            ["README.md", "docs/specs/export-v2/spec.md"])

    def test_prints_nothing_without_docs(self) -> None:
        self.assertEqual(docs("src/main.py", "pyproject.toml"), [])
        self.assertEqual(docs(), [])

    def test_takes_paths_as_arguments(self) -> None:
        result = subprocess.run([SCRIPT, "README.md", "src/a.py"], text=True,
                                capture_output=True, check=True)
        self.assertEqual(result.stdout, "README.md\n")


if __name__ == "__main__":
    unittest.main()
