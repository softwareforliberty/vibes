"""Pinned versions, hashes, keys, lockfiles, submodules and base images.

A pin protects against tampering after it was checked, not against a
malicious release, so every change to one needs a person to check the new
release upstream.
"""

from __future__ import annotations

import posixpath
import re
from typing import Iterator, Set

from ..escape import ascii_only, excerpt
from ..model import GITLINK, HIGH, REVIEW, Context, FileChange, Finding
from .common import added, hosts

HASH = re.compile(r"(?i)\b(?:sha(?:256|384|512|1)?(?:sum)?|checksum|hash|"
                  r"digest|integrity|fingerprint|key_?id)\w*\s*[:=]\s*"
                  r"[\"']?(?:sha\d+[-:])?([0-9a-fA-F]{32,128}|"
                  r"[A-Za-z0-9+/]{40,}={0,2})")
VERSION = re.compile(r"(?i)\b\w*version\w*\s*[:=]|\btag\s*[:=]|\bref\s*[:=]|"
                     r"\brev\s*[:=]|\bcommit\s*[:=]|\bbranch\s*[:=]")
FINGERPRINT = re.compile(r"(?i)\b(?:fingerprint|key_?id|signer)\w*\s*[:=]")
KEY_FILE = re.compile(r"(?i)(?:\.(?:asc|gpg|pgp|pub|pem|crt|cer|der|p7b|"
                      r"minisig|keyring|kbx)|(?:^|/)(?:keyring[^/]*|"
                      r"trusted\.gpg[^/]*|allowed_signers|[^/]*signing[-_]"
                      r"key[^/]*|KEYS))\Z")
LOCKFILE = re.compile(r"(?:^|/)(?:package-lock\.json|npm-shrinkwrap\.json|"
                      r"yarn\.lock|pnpm-lock\.yaml|bun\.lockb?|Cargo\.lock|"
                      r"poetry\.lock|uv\.lock|Pipfile\.lock|pdm\.lock|go\.sum|"
                      r"Gemfile\.lock|composer\.lock|flake\.lock|mix\.lock|"
                      r"pubspec\.lock|Package\.resolved|packages\.lock\.json|"
                      r"gradle\.lockfile|\.terraform\.lock\.hcl|"
                      r"requirements[^/]*\.txt|constraints[^/]*\.txt)\Z")
REGISTRIES = {"registry.npmjs.org", "registry.yarnpkg.com",
              "files.pythonhosted.org", "pypi.org", "crates.io",
              "static.crates.io", "index.crates.io", "proxy.golang.org",
              "rubygems.org", "repo.packagist.org", "codeload.github.com",
              "github.com", "objects.githubusercontent.com"}
FROM = re.compile(r"(?i)^\s*FROM\s+(?:--platform=\S+\s+)?(\S+)")


def check(ctx: Context) -> Iterator[Finding]:
    for change in ctx.files:
        if change.deleted:
            continue
        if KEY_FILE.search(change.path):
            yield Finding(HIGH, "pins-key", change.path, 0,
                          "a signing key or certificate changed: check the "
                          "new key belongs to the upstream signer, out of "
                          "band")
        if posixpath.basename(change.path) == ".gitmodules":
            yield Finding(HIGH, "pins-submodule", change.path, 0,
                          "submodule sources changed")
        if change.change.new_mode == GITLINK:
            yield Finding(HIGH, "pins-submodule", change.path, 0,
                          f"the submodule now points at commit "
                          f"{change.change.new_sha[:12]}: review the "
                          f"upstream changes up to it")
        if LOCKFILE.search(change.path):
            yield from _lockfile(change)
        elif not change.binary:
            yield from _pin(change)
    for change, number, text in added(ctx):
        match = FROM.match(text)
        if match and "build" in change.classes and "@sha256:" not in text \
                and match.group(1).lower() != "scratch" \
                and not match.group(1).startswith("$"):
            yield Finding(REVIEW, "pins-image-digest", change.path, number,
                          f"a base image without a digest, which can change "
                          f"under the same tag: {excerpt(text)}")


def _pin(change: FileChange) -> Iterator[Finding]:
    added_hash = [(n, t) for n, t in change.added() if HASH.search(t)]
    removed_hash = [(n, t) for n, t in change.removed() if HASH.search(t)]
    if not added_hash and not removed_hash:
        return
    version_changed = any(VERSION.search(t) for _, t in change.added())
    number, text = (added_hash or removed_hash)[0]
    if any(FINGERPRINT.search(t) for _, t in added_hash):
        yield Finding(HIGH, "pins-signer", change.path, number,
                      f"the pinned signing key changed: {excerpt(text)}")
    elif added_hash and removed_hash and not version_changed:
        yield Finding(HIGH, "pins-hash-only", change.path, number,
                      f"a hash changed but no version did: the same release "
                      f"would now have different contents: {excerpt(text)}")
    elif not added_hash:
        yield Finding(HIGH, "pins-hash-removed", change.path, number,
                      f"a pinned hash is removed: {excerpt(text)}")
    else:
        yield Finding(REVIEW, "pins-bump", change.path, number,
                      f"a pinned release changed: check the new one by hand "
                      f"(its signature, release notes and changes from the "
                      f"old one): {excerpt(text)}")
    old_hosts: Set[str] = set(hosts(change.old_text()))
    for number, text in change.added():
        for host in hosts(text):
            if old_hosts and host not in old_hosts:
                yield Finding(HIGH, "pins-host", change.path, number,
                              f"a pinned download now comes from "
                              f"{ascii_only(host, 60)}, not "
                              f"{ascii_only(', '.join(sorted(old_hosts)), 80)}")


def _lockfile(change: FileChange) -> Iterator[Finding]:
    yield Finding(REVIEW, "pins-lockfile", change.path, 0,
                  "locked dependencies changed: check each changed package "
                  "and source")
    for number, text in change.added():
        for host in hosts(text):
            if host not in REGISTRIES and not host.endswith(
                    (".npmjs.org", ".pythonhosted.org", ".crates.io")):
                yield Finding(HIGH, "pins-lock-source", change.path, number,
                              f"a locked package from "
                              f"{ascii_only(host, 60)}, not a public "
                              f"registry: {excerpt(text)}")
                break
        if re.search(r"git\+|\bgit://|github:|#[0-9a-f]{7,40}\b", text):
            yield Finding(REVIEW, "pins-lock-git", change.path, number,
                          f"a locked package from a git repository: "
                          f"{excerpt(text)}")
