"""New dependencies, typosquats, other registries, overrides and plain HTTP."""

from __future__ import annotations

import posixpath
import re
from typing import Iterator, List, Set

from ..escape import excerpt
from ..model import HIGH, REVIEW, Context, FileChange, Finding
from .common import added, hosts, matching, regex

MANIFESTS = {"package.json", "pyproject.toml", "setup.py", "setup.cfg",
             "Cargo.toml", "go.mod", "Gemfile", "composer.json", "pom.xml",
             "build.gradle", "build.gradle.kts", "mix.exs", "pubspec.yaml",
             "Package.swift", "vcpkg.json", "conanfile.txt", "deps.edn",
             "project.clj", "build.zig.zon", "Pipfile", "environment.yml"}
REQUIREMENTS = re.compile(r"(?:^|/)requirements[^/]*\.(?:txt|in)\Z")
NAME = re.compile(
    r'^\s*"(@?[\w.\-/]+)"\s*:\s*"[~^<>=*\d]'          # package.json
    r"|^\s*[\"']?([A-Za-z][\w.\-]*)(?:\[[\w,\s]+\])?\s*(?:[<>=!~]=|>|<|@)"
    r"|^\s*([a-zA-Z][\w\-]*)\s*=\s*[{\"']"             # Cargo.toml
    r"|^\s*(?:require\s+)?([a-z0-9.\-]+\.[a-z]+/[\w.\-/]+)\s+v\d"  # go.mod
    r"|^\s*gem\s+[\"']([\w\-]+)[\"']")
POPULAR = {"requests", "urllib3", "numpy", "pandas", "django", "flask",
           "setuptools", "colorama", "cryptography", "pyyaml", "boto3",
           "lodash", "express", "react", "axios", "chalk", "commander",
           "moment", "webpack", "typescript", "serde", "tokio", "rand",
           "clap", "regex", "openssl", "libc", "rails", "nokogiri", "rake"}
REGISTRY = regex(r"--(?:extra-)?index-url\b", r"\b(?:extra-)?index-url\s*=",
                 r"\bregistry\s*=", r"@[\w\-]+:registry", r"\[\[tool\.uv\.index",
                 r"\[\[tool\.poetry\.source", r"\[source\.", r"\[registries",
                 r"^\s*source\s+[\"']https?://", r"\bGOPROXY\b", r"\bGOPRIVATE\b",
                 r"\bGONOSUMDB\b", r"\bGONOSUMCHECK\b", r"\bGOSUMDB\s*=\s*off",
                 r"\bGOINSECURE\b", r"npm_config_registry", r"PIP_INDEX_URL",
                 r"PIP_EXTRA_INDEX_URL", r"\bmaven\s*\{\s*url", r"<repository>",
                 r"\bfind-links\b", r"--find-links", r"UV_INDEX_URL",
                 r"CARGO_REGISTRIES_", r"\bpublishConfig\b",
                 flags=re.IGNORECASE)
OVERRIDE = regex(r"^\s*replace\s", r"\[patch\.", r"^\s*\[replace\]",
                 r'"(?:overrides|resolutions|pnpm\.overrides)"\s*:',
                 r"dependency_links", r"^\s*-e\s+(?:git\+|https?://|\.)",
                 r"\bpath\s*=\s*[\"']\.\.", r"\bgit\s*=\s*[\"']https?://",
                 r"\bbranch\s*=\s*[\"']")
PLAIN_HTTP = re.compile(r"\bhttp://(?!localhost\b|127\.0\.0\.1\b|0\.0\.0\.0\b|"
                        r"\[::1\]|example\.(?:com|org|net)\b|www\.w3\.org/|"
                        r"schemas\.|purl\.org/|xmlns)", re.IGNORECASE)


def distance(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 2:
        return 3
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1,
                               previous[j - 1] + (char_a != char_b)))
        previous = current
    return previous[-1]


def names(lines: List[str]) -> Set[str]:
    found = set()
    for text in lines:
        match = NAME.search(text)
        if match:
            found.add(next(group for group in match.groups() if group)
                      .lower().replace("_", "-"))
    return found


def is_manifest(change: FileChange) -> bool:
    return posixpath.basename(change.path) in MANIFESTS or bool(
        REQUIREMENTS.search(change.path))


def check(ctx: Context) -> Iterator[Finding]:
    for change in ctx.changed():
        if change.binary or not is_manifest(change):
            continue
        old = names(change.old_text().split("\n"))
        new_lines = change.added()
        for number, text in new_lines:
            for name in names([text]) - old:
                near = sorted(known for known in old | POPULAR
                              if known != name and distance(name, known) <= 2
                              and len(name) > 3)
                if near:
                    yield Finding(HIGH, "deps-typosquat", change.path, number,
                                  f"the new dependency {excerpt(name)} is "
                                  f"one or two letters from "
                                  f"{excerpt(near[0])}")
                else:
                    yield Finding(REVIEW, "deps-new", change.path, number,
                                  f"a new dependency {excerpt(name)}: check "
                                  f"who publishes it, and why it's needed")
    yield from matching(added(ctx), REGISTRY, HIGH, "deps-registry",
                        "adds a package index or registry, which can serve "
                        "a different package under the same name")
    for change, number, text in added(ctx):
        if is_manifest(change) and OVERRIDE.search(text):
            yield Finding(REVIEW, "deps-override", change.path, number,
                          f"overrides where a dependency comes from: "
                          f"{excerpt(text)}")
        if PLAIN_HTTP.search(text) and "docs" not in change.classes:
            yield Finding(HIGH if set(change.classes) & {"build", "ci"}
                          else REVIEW, "deps-plain-http", change.path, number,
                          f"a plain HTTP URL, which anyone on the network "
                          f"can change: {excerpt(text)}")
        for host in hosts(text):
            if host.startswith("xn--") or ".xn--" in host or not (
                    host.isascii()):
                yield Finding(HIGH, "deps-idn-host", change.path, number,
                              f"an internationalised host name, which can "
                              f"look like another: {excerpt(host)}")
