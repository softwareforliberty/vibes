"""Who the pull request comes from: first-time contributors, unverified or
borrowed identities, co-author lines and odd dates."""

from __future__ import annotations

import datetime
import re
from typing import Dict, Iterator, List, Set

from ..escape import ascii_only
from ..model import HIGH, INFO, REVIEW, Context, Finding

CO_AUTHOR = re.compile(r"^\s*Co-authored-by:\s*(.+)$", re.IGNORECASE | re.M)


def check(ctx: Context) -> Iterator[Finding]:
    record = ctx.meta.get("record")
    record = record if isinstance(record, dict) else {}
    login = str(record.get("author") or "")
    listed = record.get("commits")
    if record:
        yield from _about_the_author(record, login)
        if not isinstance(listed, list):
            yield Finding(INFO, "history-unchecked", "(pull request)", 0,
                          "the forge didn't list the commits, so their "
                          "signatures and accounts weren't checked")
    api: Dict[str, dict] = {}
    for item in listed if isinstance(listed, list) else []:
        if isinstance(item, dict) and isinstance(item.get("sha"), str):
            api[item["sha"]] = item
    known = _contributors(ctx)
    now = datetime.datetime.now(datetime.timezone.utc)
    for commit in ctx.commits:
        where = f"(commit {commit.sha[:12]})"
        item = api.get(commit.sha, {})
        # True, False, or None when the forge can't say.
        verified = item.get("verified")
        # A login, "" for no account, or None when the forge doesn't link
        # commits to accounts.
        author_login = item.get("author")
        if item and verified is False:
            yield Finding(REVIEW, "history-unverified", where, 0,
                          "the commit isn't signed, so its author line "
                          "can say anything")
        elif item and verified is None:
            yield Finding(REVIEW, "history-unverified", where, 0,
                          "the forge doesn't say whether the commit is "
                          "signed, so its author line can say anything")
        other = (item and login and author_login is not None
                 and author_login != login)
        if other:
            yield Finding(REVIEW, "history-other-author", where, 0,
                          f"authored by "
                          f"{ascii_only(author_login or 'no account', 40)}"
                          f", not {ascii_only(login, 40)}, who opened the "
                          f"pull request")
        identity = {commit.author_name.lower(), commit.author_email.lower()}
        if item and identity & known and (verified is not True or other):
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


def _about_the_author(record: dict, login: str) -> Iterator[Finding]:
    """Whether the person who opened the pull request is new, if the forge
    says."""
    first_time = record.get("first_time")
    if first_time is True:
        yield Finding(INFO, "history-first-time", "(pull request)", 0,
                      f"{ascii_only(login or 'the author', 40)} hasn't "
                      f"contributed to the repository before")
    elif first_time is None:
        yield Finding(INFO, "history-unchecked", "(pull request)", 0,
                      "the forge doesn't say whether the author has "
                      "contributed before")
    if record.get("commits") and not any(
            isinstance(item, dict) and item.get("author") is not None
            for item in record["commits"]):
        yield Finding(INFO, "history-unchecked", "(pull request)", 0,
                      "the forge doesn't link commits to accounts, so "
                      "whether they're by the author wasn't checked")


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
