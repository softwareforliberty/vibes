"""Who the pull request comes from: first-time contributors, unverified or
borrowed identities, co-author lines and odd dates."""

from __future__ import annotations

import datetime
import re
from typing import Dict, Iterator, List, Set

from ..escape import ascii_only
from ..model import HIGH, INFO, REVIEW, Context, Finding

CO_AUTHOR = re.compile(r"^\s*Co-authored-by:\s*(.+)$", re.IGNORECASE | re.M)
NEWCOMERS = {"FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER", "NONE"}


def check(ctx: Context) -> Iterator[Finding]:
    pull = ctx.meta.get("pull")
    login = ""
    if isinstance(pull, dict):
        login = str((pull.get("user") or {}).get("login") or "")
        association = str(pull.get("author_association") or "")
        if association in NEWCOMERS:
            yield Finding(INFO, "history-first-time", "(pull request)", 0,
                          f"{ascii_only(login, 40)} hasn't contributed to "
                          f"the repository before ({association})")
    api: Dict[str, dict] = {}
    for item in ctx.meta.get("commits") or []:
        if isinstance(item, dict) and isinstance(item.get("sha"), str):
            api[item["sha"]] = item
    known = _contributors(ctx)
    now = datetime.datetime.now(datetime.timezone.utc)
    for commit in ctx.commits:
        where = f"(commit {commit.sha[:12]})"
        item = api.get(commit.sha, {})
        verified = bool(((item.get("commit") or {}).get("verification")
                         or {}).get("verified"))
        author_login = str((item.get("author") or {}).get("login") or "")
        if item and not verified:
            yield Finding(REVIEW, "history-unverified", where, 0,
                          "the commit isn't signed, so its author line "
                          "can say anything")
        if item and login and author_login != login:
            yield Finding(REVIEW, "history-other-author", where, 0,
                          f"authored by "
                          f"{ascii_only(author_login or 'no GitHub account', 40)}"
                          f", not {ascii_only(login, 40)}, who opened the "
                          f"pull request")
        identity = {commit.author_name.lower(), commit.author_email.lower()}
        if item and identity & known and (not verified or (
                login and author_login != login)):
            yield Finding(HIGH, "history-impersonation", where, 0,
                          f"claims to be by an existing contributor, "
                          f"{ascii_only(commit.author_name, 40)} "
                          f"<{ascii_only(commit.author_email, 60)}>, without "
                          f"a signature or account that proves it")
        for co_author in CO_AUTHOR.findall(commit.message):
            yield Finding(REVIEW, "history-co-author", where, 0,
                          f"credits a co-author: {ascii_only(co_author, 80)}")
        for label, value in (("author", commit.author_date),
                             ("commit", commit.committer_date)):
            when = _date(value)
            if when and (when > now + datetime.timedelta(days=1)
                         or when.year < 2005):
                yield Finding(REVIEW, "history-date", where, 0,
                              f"an unlikely {label} date, {ascii_only(value)}")
        if commit.author_email.lower() != commit.committer_email.lower():
            yield Finding(INFO, "history-committer", where, 0,
                          f"committed by "
                          f"{ascii_only(commit.committer_email, 60)}, not "
                          f"the author")


def _contributors(ctx: Context) -> Set[str]:
    out = ctx.git.run("log", "--no-mailmap", "-n", "2000",
                      "--format=%an%x00%ae", ctx.base, check=False)
    names: List[str] = []
    for line in out.decode("utf-8", "replace").splitlines():
        names.extend(part.lower() for part in line.split("\0") if part)
    return set(names)


def _date(value: str):
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
