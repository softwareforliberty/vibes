"""The forge's own record of a pull request, in one shape for every forge.

bin/pr-prepare saves what a forge's CLI says about a pull request, raw, in
the review's meta/ directory; `pr-scan record` turns it into pr.json:

    {"forge": "github", "title": "...", "body": "...", "author": "login",
     "first_time": true, "head": "<sha>", "base_ref": "main",
     "clone_url": "https://...",
     "commits": [{"sha": "<sha>", "verified": false, "author": "login"}]}

A field the forge doesn't give is null: first_time when it can't say
whether the author is new, a commit's verified when it can't say whether
it's signed, and its author when it doesn't link commits to accounts. An
empty author means the forge says the commit has no account. commits is
null when the forge didn't list them. The checks that need a field report
that they couldn't check it, rather than pass.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

SHA = re.compile(r"\A[0-9a-f]{40}\Z")
REF = re.compile(r"\A[A-Za-z0-9._/-]+\Z")
CLONE_URL = re.compile(r"\Ahttps://[A-Za-z0-9.-]+(:[0-9]+)?/[A-Za-z0-9._/~-]+\Z")
# GitHub's author_association values for someone who hasn't contributed.
NEWCOMERS = {"FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER", "NONE"}

Record = Dict[str, Any]


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def from_github(pull: Any, commits: Any) -> Record:
    """From GET /repos/{owner}/{repo}/pulls/{n} and its commits."""
    pull = _dict(pull)
    association = _text(pull.get("author_association"))
    listed: Optional[List[Record]] = None
    if isinstance(commits, list):
        listed = []
        for item in commits:
            item = _dict(item)
            if not isinstance(item.get("sha"), str):
                continue
            verification = _dict(_dict(item.get("commit")).get("verification"))
            listed.append({
                "sha": item["sha"],
                "verified": bool(verification.get("verified")),
                "author": _text(_dict(item.get("author")).get("login")),
            })
    return {
        "forge": "github",
        "title": _text(pull.get("title")),
        "body": _text(pull.get("body")),
        "author": _text(_dict(pull.get("user")).get("login")),
        "first_time": association in NEWCOMERS if association else None,
        "head": _text(_dict(pull.get("head")).get("sha")),
        "base_ref": _text(_dict(pull.get("base")).get("ref")),
        "clone_url": _text(_dict(_dict(pull.get("base")).get("repo"))
                           .get("clone_url")),
        "commits": listed,
    }


# GitLab's verification_status values for a signature it verified.
GITLAB_VERIFIED = {"verified", "verified_system", "verified_ca"}


def from_gitlab(merge_request: Any, commits: Any, project: Any,
                signatures: Dict[str, Any]) -> Record:
    """From GET /projects/:id/merge_requests/:iid, its commits, the target
    project, and each commit's signature. GitLab doesn't link commits to
    accounts, and a commit with no signature has none here."""
    merge_request = _dict(merge_request)
    first = merge_request.get("first_contribution")
    listed: Optional[List[Record]] = None
    if isinstance(commits, list):
        listed = []
        for item in commits:
            item = _dict(item)
            sha = item.get("id")
            if not isinstance(sha, str):
                continue
            verified: Optional[bool] = None
            signature = signatures.get(sha)
            if isinstance(signature, dict):
                status = signature.get("verification_status")
                if isinstance(status, str):
                    verified = status in GITLAB_VERIFIED
            listed.append({"sha": sha, "verified": verified, "author": None})
    return {
        "forge": "gitlab",
        "title": _text(merge_request.get("title")),
        "body": _text(merge_request.get("description")),
        "author": _text(_dict(merge_request.get("author")).get("username")),
        "first_time": first if isinstance(first, bool) else None,
        "head": _text(merge_request.get("sha")),
        "base_ref": _text(merge_request.get("target_branch")),
        "clone_url": _text(_dict(project).get("http_url_to_repo")),
        "commits": listed,
    }


def from_forgejo(pull: Any, pages: Optional[List[Any]]) -> Record:
    """From Forgejo's or Gitea's GET /repos/{owner}/{repo}/pulls/{n} and the
    pages of its commits. Neither says whether the author is new, and both
    link a commit to an account by its email address alone."""
    pull = _dict(pull)
    listed: Optional[List[Record]] = None
    if pages is not None:
        listed = []
        for page in pages:
            for item in page if isinstance(page, list) else []:
                item = _dict(item)
                if not isinstance(item.get("sha"), str):
                    continue
                verification = _dict(_dict(item.get("commit"))
                                     .get("verification"))
                listed.append({
                    "sha": item["sha"],
                    "verified": bool(verification.get("verified")),
                    "author": _text(_dict(item.get("author")).get("login")),
                })
    return {
        "forge": "forgejo",
        "title": _text(pull.get("title")),
        "body": _text(pull.get("body")),
        "author": _text(_dict(pull.get("user")).get("login")),
        "first_time": None,
        "head": _text(_dict(pull.get("head")).get("sha")),
        "base_ref": _text(_dict(pull.get("base")).get("ref")),
        "clone_url": _text(_dict(_dict(pull.get("base")).get("repo"))
                           .get("clone_url")),
        "commits": listed,
    }


def _items(value: Any) -> Optional[List[Any]]:
    """A list of commits: one object per line with a single line reads as
    that object, not a list of one."""
    if isinstance(value, dict):
        return [value]
    return value if isinstance(value, list) else None


def _json(path: str) -> Any:
    """A JSON file, or one JSON object per line, as gh --jq '.[]' writes."""
    with open(path, encoding="utf-8") as stream:
        text = stream.read()
    try:
        return json.loads(text)
    except ValueError:
        return [json.loads(line) for line in text.splitlines()
                if line.strip()]


def load(forge: str, directory: str) -> Record:
    """The record, from the raw files pr-prepare saved for a forge."""
    def raw(name: str) -> Any:
        path = os.path.join(directory, name)
        return _json(path) if os.path.exists(path) else None

    if forge == "github":
        return from_github(raw("pull.json"), _items(raw("commits.json")))
    if forge == "gitlab":
        signatures: Dict[str, Any] = {}
        folder = os.path.join(directory, "signatures")
        if os.path.isdir(folder):
            for name in os.listdir(folder):
                sha = name[:-len(".json")]
                if name.endswith(".json") and SHA.match(sha):
                    try:
                        signatures[sha] = _json(os.path.join(folder, name))
                    except ValueError:
                        pass
        return from_gitlab(raw("merge-request.json"),
                           _items(raw("commits.json")), raw("project.json"),
                           signatures)
    if forge == "forgejo":
        pages: Optional[List[Any]] = []
        number = 1
        while os.path.exists(os.path.join(directory,
                                          f"commits-{number}.json")):
            page = raw(f"commits-{number}.json")
            if not isinstance(page, list) or pages is None:
                pages = None
                break
            pages.append(page)
            number += 1
        return from_forgejo(raw("pull.json"), pages if number > 1 else None)
    raise ValueError(f"unknown forge: {forge}")


def shas(forge: str, directory: str) -> List[str]:
    """The commits the forge listed, for fetching each one's signature."""
    found = []
    path = os.path.join(directory, "commits.json")
    if forge == "gitlab" and os.path.exists(path):
        for item in _items(_json(path)) or []:
            sha = _dict(item).get("id")
            if isinstance(sha, str) and SHA.match(sha):
                found.append(sha)
    return found


def checked(record: Record) -> Record:
    """The record, once the fields git is given are what they must be."""
    if not SHA.match(record.get("head") or ""):
        raise ValueError("the forge's head commit isn't a commit")
    if not REF.match(record.get("base_ref") or ""):
        raise ValueError("the forge's base branch isn't a branch name")
    if not CLONE_URL.match(record.get("clone_url") or ""):
        raise ValueError("the forge's clone address isn't an https address")
    return record
