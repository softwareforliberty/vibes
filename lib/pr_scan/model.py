"""The scan's view of a pull request: its changes, commits, config and findings."""

from __future__ import annotations

import difflib
import posixpath
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from .gitio import ZERO, Change, Commit, Git

HIGH, REVIEW, INFO = "HIGH", "REVIEW", "INFO"
SEVERITIES = (HIGH, REVIEW, INFO)
SYMLINK, GITLINK = "120000", "160000"
# Text blobs above this size are cut short in the snapshot.
TEXT_LIMIT = 1_000_000


@dataclass(frozen=True)
class Finding:
    severity: str
    rule: str
    path: str
    line: int
    message: str


def glob_regex(pattern: str) -> "re.Pattern[str]":
    """A regex for a glob: ** matches across directories, * and ? don't.

    A pattern without a slash matches the file name in any directory, as in
    .gitignore.
    """
    if "/" not in pattern:
        pattern = "**/" + pattern
    out = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if pattern.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
            continue
        if pattern.startswith("**", index):
            out.append(".*")
            index += 2
            continue
        out.append({"*": "[^/]*", "?": "[^/]"}.get(char, re.escape(char)))
        index += 1
    return re.compile("".join(out) + r"\Z", re.IGNORECASE)


def matches(path: str, patterns: Iterable[str]) -> bool:
    return any(glob_regex(pattern).match(path) for pattern in patterns)


@dataclass
class Config:
    """.vibes-review, read from the base commit only."""

    protected: List[str] = field(default_factory=list)
    test_data: List[str] = field(default_factory=list)
    binary_allowed: List[str] = field(default_factory=list)
    allowed_hosts: List[str] = field(default_factory=list)
    errors: List[Tuple[int, str]] = field(default_factory=list)

    KINDS = {"protected": "protected", "test-data": "test_data",
             "binary-allowed": "binary_allowed",
             "allowed-host": "allowed_hosts"}

    @classmethod
    def parse(cls, text: str) -> "Config":
        config = cls()
        for number, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            kind, _, value = line.partition("\t")
            if not value:
                kind, _, value = line.partition(" ")
            attribute = cls.KINDS.get(kind.strip())
            if attribute is None or not value.strip():
                config.errors.append((number, line))
                continue
            getattr(config, attribute).append(value.strip())
        return config


CONFIG_FILE = ".vibes-review"

# Directories that hold tests, and names that mark test data within them.
TEST_DIRS = re.compile(r"(?:^|/)(?:tests?|testing|testdata|spec|__tests__|"
                       r"t)(?:/|$)", re.IGNORECASE)
DATA_DIRS = re.compile(r"(?:^|/)(?:data|files|fixtures?|testdata|references?|"
                       r"golden|samples?|corpus|assets|inputs?|expected)"
                       r"(?:/|$)", re.IGNORECASE)
TEST_FILE = re.compile(r"(?:^|/)(?:test_[^/]*|[^/]*_test\.[^/]+|[^/]*\.bats|"
                       r"[^/]*\.test\.[^/]+|[^/]*\.spec\.[^/]+|"
                       r"[^/]*Tests?\.[^/]+)\Z")
SOURCE_EXT = re.compile(r"\.(?:c|cc|cpp|cxx|h|hh|hpp|hxx|m|mm|s|S|asm|py|sh|"
                        r"bash|bats|go|rs|java|kt|scala|js|mjs|cjs|ts|tsx|jsx|"
                        r"rb|pl|pm|php|swift|zig|lua|cs|fs|vb|ex|exs|erl|hs|"
                        r"ml|jl|r|R|dart|clj|groovy|ps1|f90|cob|sql)\Z")

BUILD_NAMES = {
    "makefile", "gnumakefile", "cmakelists.txt", "configure", "configure.ac",
    "configure.in", "meson.build", "meson_options.txt", "meson.options",
    "dockerfile", "containerfile", "build.rs", "setup.py", "setup.cfg",
    "pyproject.toml", "package.json", "rakefile", "gemfile", "build.gradle",
    "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "pom.xml",
    "build", "build.bazel", "workspace", "workspace.bazel", "module.bazel",
    "sconstruct", "sconscript", "justfile", "taskfile.yml", "flake.nix",
    "default.nix", "shell.nix", "cargo.toml", "go.mod", "build.zig",
    "build.zig.zon", "conftest.py", "sitecustomize.py", "usercustomize.py",
    "noxfile.py", "tox.ini", "makefile.am", "makefile.in", "kbuild", "kconfig",
    "build.sh", "autogen.sh", "bootstrap", "install.sh", "vcpkg.json",
    "conanfile.py", "conanfile.txt", "mix.exs", "rebar.config", "cabal.project",
    "stack.yaml", "dune-project", "project.clj", "deps.edn", "build.sbt",
}
BUILD_EXT = re.compile(r"\.(?:mk|make|cmake|m4|ac|am|in|ld|lds|bzl|gemspec|"
                       r"cabal|nix|pth|dockerfile|gradle|spec)\Z", re.IGNORECASE)
CI_PATH = re.compile(
    r"^(?:\.github/workflows/|\.github/actions/|\.circleci/|\.buildkite/|"
    r"\.gitlab/|\.woodpecker|\.forgejo/workflows/|\.gitea/workflows/)|"
    r"^(?:\.gitlab-ci\.yml|Jenkinsfile|\.travis\.yml|azure-pipelines\.yml|"
    r"\.drone\.yml|bitbucket-pipelines\.yml|\.cirrus\.yml|appveyor\.yml|"
    r"\.github/action\.ya?ml|action\.ya?ml)\Z")
AGENT_CONFIG = re.compile(
    r"(?:^|/)(?:CLAUDE(?:\.local)?\.md|AGENTS\.md|AGENT\.md|GEMINI\.md|"
    r"\.claude(?:/|\Z)|\.mcp\.json|\.cursor(?:/|\Z)|\.cursorrules|\.cursorignore|"
    r"\.windsurfrules|\.windsurf(?:/|\Z)|\.clinerules|\.roo(?:/|\Z)|"
    r"\.aider[^/]*|\.continue(?:/|\Z)|\.github/copilot-instructions\.md|"
    r"\.github/instructions(?:/|\Z)|\.github/prompts(?:/|\Z)|\.vscode(?:/|\Z)|"
    r"\.devcontainer(?:/|\Z)|devcontainer\.json|\.envrc|\.env(?:\.[^/]*)?\Z|"
    r"\.idea(?:/|\Z)|\.zed(?:/|\Z)|\.nvim\.lua|\.exrc|\.vimrc|\.tool-versions|"
    r"\.mise\.toml|mise\.toml|\.direnv(?:/|\Z)|\.gitpod\.yml|\.replit)",
    re.IGNORECASE)
GIT_META = re.compile(r"(?:^|/)(?:\.gitattributes|\.gitmodules|\.lfsconfig|"
                      r"\.mailmap|CODEOWNERS|\.gitconfig|\.git-blame-ignore-revs)"
                      r"\Z")
GATE_PATH = re.compile(
    r"(?:^|/)(?:scripts/(?:check|audit|check-requirements)|"
    r"\.pre-commit-config\.ya?ml|\.pre-commit-hooks\.ya?ml|\.clang-tidy|"
    r"\.clang-format|\.shellcheckrc|ruff\.toml|\.ruff\.toml|mypy\.ini|"
    r"\.flake8|\.pylintrc|pylintrc|\.eslintrc[^/]*|eslint\.config\.[^/]+|"
    r"\.golangci\.[^/]+|clippy\.toml|\.rubocop\.yml|phpstan\.neon[^/]*|"
    r"\.swiftlint\.yml|\.editorconfig|\.trivyignore|\.gitleaksignore|"
    r"\.gitleaks\.toml|\.semgrepignore|\.opengrep[^/]*|\.snyk|\.bandit|"
    r"vulture_whitelist\.py|\.codecov\.ya?ml|codecov\.ya?ml|\.coveragerc|"
    r"gcovr\.cfg|mull\.ya?ml|checkmake\.ini|trivy\.yaml|\.jscpd\.json|"
    r"\.markdownlint[^/]*|\.yamllint[^/]*|\.hadolint\.ya?ml|stryker\.conf[^/]*|"
    r"\.cargo/config(?:\.toml)?|\.npmrc|\.yarnrc(?:\.yml)?|\.pypirc|pip\.conf|"
    r"\.bazelrc|deny\.toml|osv-scanner\.toml)\Z")


def classes(path: str) -> Tuple[str, ...]:
    """The kinds of file a path is, such as build, ci or test-data."""
    name = posixpath.basename(path)
    lower = name.lower()
    found = []
    if (lower in BUILD_NAMES or BUILD_EXT.search(name)
            or lower.startswith(("dockerfile", "containerfile", "makefile"))):
        found.append("build")
    if CI_PATH.search(path):
        found.append("ci")
    if AGENT_CONFIG.search(path):
        found.append("agent-config")
    if GIT_META.search(path):
        found.append("git-meta")
    if GATE_PATH.search(path):
        found.append("gate")
    if TEST_DIRS.search(path) or TEST_FILE.search(path):
        found.append("test")
        if DATA_DIRS.search(path) or not SOURCE_EXT.search(name):
            found.append("test-data")
    if lower.endswith((".md", ".rst", ".txt", ".adoc")) or path.startswith(
            ("docs/", "doc/")):
        found.append("docs")
    if path.startswith(("vendor/", "third_party/", "third-party/", "external/",
                        "deps/", "extern/")):
        found.append("vendor")
    if SOURCE_EXT.search(name):
        found.append("source")
    return tuple(found)


def is_binary(data: bytes) -> bool:
    return b"\0" in data[:8000] or (b"\0" in data and len(data) > 8000)


@dataclass
class FileChange:
    """A changed file, with its old and new content loaded on demand."""

    change: Change
    git: Git
    _added: Optional[List[Tuple[int, str]]] = None
    _removed: Optional[List[Tuple[int, str]]] = None

    @property
    def path(self) -> str:
        return self.change.path

    @property
    def status(self) -> str:
        return self.change.status

    @property
    def classes(self) -> Tuple[str, ...]:
        return classes(self.path)

    @property
    def is_symlink(self) -> bool:
        return self.change.new_mode == SYMLINK

    @property
    def is_gitlink(self) -> bool:
        return self.change.new_mode == GITLINK

    @property
    def deleted(self) -> bool:
        return self.change.status == "D"

    def new(self) -> bytes:
        if self.deleted or self.is_gitlink:
            return b""
        return self.git.blob(self.change.new_sha)

    def old(self) -> bytes:
        if self.change.old_sha == ZERO or self.change.old_mode == GITLINK:
            return b""
        return self.git.blob(self.change.old_sha)

    @property
    def binary(self) -> bool:
        return not self.is_symlink and not self.is_gitlink and is_binary(
            self.new() or self.old())

    def new_text(self) -> str:
        return self.new().decode("utf-8", "replace")

    def old_text(self) -> str:
        return self.old().decode("utf-8", "replace")

    def _diff(self) -> None:
        old = self.old_text().split("\n") if self.old() else []
        new = self.new_text().split("\n") if self.new() else []
        added: List[Tuple[int, str]] = []
        removed: List[Tuple[int, str]] = []
        matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ("replace", "delete"):
                removed.extend((i + 1, old[i]) for i in range(i1, i2))
            if tag in ("replace", "insert"):
                added.extend((j + 1, new[j]) for j in range(j1, j2))
        self._added, self._removed = added, removed

    def added(self) -> List[Tuple[int, str]]:
        """The lines this change adds, with their line numbers."""
        if self.binary or self.is_symlink or self.is_gitlink:
            return []
        if self._added is None:
            self._diff()
        assert self._added is not None
        return self._added

    def removed(self) -> List[Tuple[int, str]]:
        if self.binary or self.is_symlink or self.is_gitlink:
            return []
        if self._removed is None:
            self._diff()
        assert self._removed is not None
        return self._removed


@dataclass
class Context:
    """Everything the rules see."""

    git: Git
    base: str
    head: str
    files: List[FileChange]
    commits: List[Commit]
    # Text and binary blobs added by any commit, but gone by the head.
    history_only: List[Tuple[Commit, Change]]
    config: Config
    config_changed: bool
    meta: Dict[str, object]
    _base_tree: Optional[Dict[str, Tuple[str, str]]] = None
    _head_tree: Optional[Dict[str, Tuple[str, str]]] = None

    def base_tree(self) -> Dict[str, Tuple[str, str]]:
        if self._base_tree is None:
            self._base_tree = self.git.tree(self.base)
        return self._base_tree

    def head_tree(self) -> Dict[str, Tuple[str, str]]:
        if self._head_tree is None:
            self._head_tree = self.git.tree(self.head)
        return self._head_tree

    def changed(self, *wanted: str) -> Iterator[FileChange]:
        """The changed files that aren't deleted, of any of the given kinds."""
        for change in self.files:
            if change.deleted:
                continue
            if not wanted or set(wanted) & set(change.classes):
                yield change

    def text_files(self) -> Iterator[FileChange]:
        for change in self.changed():
            if not change.binary and not change.is_symlink and not (
                    change.is_gitlink):
                yield change

    def is_test_data(self, path: str) -> bool:
        return "test-data" in classes(path) or matches(path,
                                                       self.config.test_data)
