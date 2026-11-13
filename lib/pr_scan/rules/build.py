"""Build machinery, and build code that reads test data (XZ's path in)."""

from __future__ import annotations

import posixpath
import re
from typing import Iterator

from ..escape import ascii_only, excerpt
from ..model import HIGH, REVIEW, Context, Finding, classes
from .common import added, matching, regex
from .exec_ import DECODE, PIPE_TO_SHELL

TEST_PATH = re.compile(r"(?:^|[\s\"'=/$({:,])(?:tests?|testdata|test-data|"
                       r"testing|fixtures?|t)/", re.IGNORECASE)
MAKE_SHELL = regex(r"^\s*SHELL\s*[:?+!]?=", r"^\s*\.SHELLFLAGS\s*[:?+!]?=")
MAKE_RISKY = regex(r"^\s*\.ONESHELL\b", r"^\s*MAKEFLAGS\s*\+?=",
                   r"^\s*-?include\s+\S*\$")
CMAKE_RUN = regex(r"\bexecute_process\s*\(", r"\bfile\s*\(\s*DOWNLOAD\b",
                  r"\bExternalProject_Add\s*\(", r"\bFetchContent_Declare\s*\(",
                  r"\badd_custom_command\s*\(.*\bPRE_BUILD\b",
                  flags=re.IGNORECASE)
INSTALL_SCRIPTS = re.compile(r'"(?:pre|post)?install"\s*:|"prepare"\s*:|'
                             r'"prepublish(?:Only)?"\s*:|"prepack"\s*:')
AUTO_RUN = re.compile(r"(?:^|/)(?:conftest\.py|sitecustomize\.py|"
                      r"usercustomize\.py|[^/]+\.pth|\.pythonstartup)\Z")


def check(ctx: Context) -> Iterator[Finding]:
    for change in ctx.changed("build"):
        yield Finding(REVIEW, "build-changed", change.path, 0,
                      "build machinery changed: it runs on every machine "
                      "that builds the project")
    for change in ctx.changed():
        if AUTO_RUN.search(change.path):
            yield Finding(HIGH, "build-auto-run", change.path, 0,
                          "a file the language runs automatically, before "
                          "any test or program")
        if change.path.endswith((".patch", ".diff")):
            yield Finding(REVIEW, "build-patch", change.path, 0,
                          "a patch file: it's code applied at build time, "
                          "so read every hunk")
    yield from matching(added(ctx, "build"), MAKE_SHELL, HIGH,
                        "build-make-shell",
                        "changes the shell Make runs recipes with")
    yield from matching(added(ctx, "build"), MAKE_RISKY, REVIEW,
                        "build-make-risky", "changes how Make runs")
    yield from matching(added(ctx, "build"), CMAKE_RUN, REVIEW,
                        "build-cmake-run",
                        "runs or downloads something while configuring")
    for change, number, text in added(ctx, "build"):
        name = posixpath.basename(change.path)
        if name == "package.json" and INSTALL_SCRIPTS.search(text):
            yield Finding(HIGH, "build-install-script", change.path, number,
                          f"an install script, which runs on every "
                          f"install: {excerpt(text)}")
        if name == "pyproject.toml" and "build-backend" in text:
            yield Finding(HIGH, "build-backend", change.path, number,
                          f"the build backend changed: {excerpt(text)}")
        if name == "setup.py" and "cmdclass" in text:
            yield Finding(HIGH, "build-setup-command", change.path, number,
                          f"custom setup.py commands: {excerpt(text)}")
    yield from _reads_test_data(ctx)
    yield from _unused_test_data(ctx)


def _reads_test_data(ctx: Context) -> Iterator[Finding]:
    """Build or CI code that names a test directory or a changed test file."""
    for change, number, text in added(ctx, "build", "ci"):
        if not TEST_PATH.search(text) or "test" in change.classes:
            continue
        # A build file that already ran the tests, such as a check target,
        # is only worth a look; decoding or running test data never is.
        usual = TEST_PATH.search(change.old_text()) and not (
            DECODE.search(text) or PIPE_TO_SHELL.search(text))
        like_xz = "" if usual else ", as XZ's backdoor did"
        yield Finding(REVIEW if usual else HIGH, "build-reads-test-data",
                      change.path, number,
                      f"build code that refers to test files{like_xz}: "
                      f"{excerpt(text)}")
    for change in ctx.changed():
        if not ctx.is_test_data(change.path):
            continue
        name = posixpath.basename(change.path)
        if len(name) < 4:
            continue
        for path in ctx.git.grep(ctx.head, name):
            kinds = classes(path)
            if ("build" in kinds or "ci" in kinds) and "test" not in kinds:
                yield Finding(HIGH, "build-reads-test-data", change.path, 0,
                              f"test data named by build code in "
                              f"{ascii_only(path, 80)}")


def _unused_test_data(ctx: Context) -> Iterator[Finding]:
    """Test data no test names, by file or by directory."""
    for change in ctx.changed():
        if change.status != "A" or not ctx.is_test_data(change.path):
            continue
        name = posixpath.basename(change.path)
        directory = posixpath.dirname(change.path)
        users = [path for path in ctx.git.grep(ctx.head, name)
                 + (ctx.git.grep(ctx.head, posixpath.basename(directory))
                    if directory else [])
                 if path != change.path and "test" in classes(path)
                 and "test-data" not in classes(path)]
        if not users:
            yield Finding(REVIEW, "build-unused-test-data", change.path, 0,
                          "new test data that no test names, by file or "
                          "directory: ask what uses it")
