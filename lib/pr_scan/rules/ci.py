"""CI workflows: privileged triggers, script injection, unpinned actions,
broad permissions, self-hosted runners, caches and secrets."""

from __future__ import annotations

import re
from typing import Iterator

from ..escape import ascii_only
from ..model import HIGH, REVIEW, Context, Finding
from .common import added, matching, regex

TRIGGER = re.compile(r"\b(?:pull_request_target|workflow_run|issue_comment|"
                     r"pull_request_review_comment|discussion_comment|"
                     r"pull_request_review)\b")
INJECTION = re.compile(r"\$\{\{\s*(?:github\.event\.|github\.head_ref|"
                       r"inputs\.|env\.)")
USES = re.compile(r"\buses:\s*[\"']?([^\s\"'#]+)")
PINNED = re.compile(r"@[0-9a-f]{40}\Z")
PERMISSIONS = regex(r"\bwrite-all\b", r"\bid-token:\s*write",
                    r"\b(?:contents|packages|actions|pull-requests|"
                    r"deployments|statuses|checks|security-events|"
                    r"attestations):\s*write")
RISKY = regex(r"\bGITHUB_(?:ENV|PATH)\b", r"::set-env\b", r"::add-path\b",
              r"ACTIONS_ALLOW_UNSECURE_COMMANDS",
              r"toJSON\(\s*secrets\s*\)", r"\bself-hosted\b",
              r"\bhead\.(?:sha|ref)\b", r"\bpersist-credentials:\s*true")
CACHE = regex(r"actions/cache\b", r"\brestore-keys\b",
              r"actions/(?:upload|download)-artifact\b", r"\bsecrets\.")


def check(ctx: Context) -> Iterator[Finding]:
    changed = list(ctx.changed("ci"))
    for change in changed:
        yield Finding(HIGH, "ci-changed", change.path, 0,
                      "CI changed: on GitHub it may already have run with "
                      "this pull request's code; check the run's logs")
    yield from matching(added(ctx, "ci"), TRIGGER, HIGH, "ci-trigger",
                        "a trigger that runs with the base repository's "
                        "secrets and write access")
    yield from matching(added(ctx, "ci"), INJECTION, HIGH, "ci-injection",
                        "expands attacker-controlled text into the workflow")
    yield from matching(added(ctx, "ci"), PERMISSIONS, REVIEW,
                        "ci-permissions", "grants write access")
    yield from matching(added(ctx, "ci"), RISKY, HIGH, "ci-risky",
                        "a risky workflow feature")
    yield from matching(added(ctx, "ci"), CACHE, REVIEW, "ci-cache",
                        "a cache, artifact or secret, which another run "
                        "can be poisoned through or leak")
    for change, number, text in added(ctx, "ci"):
        match = USES.search(text)
        if not match:
            continue
        action = match.group(1)
        if action.startswith("./"):
            continue
        if action.startswith("docker://") and "@sha256:" not in action:
            yield Finding(HIGH, "ci-unpinned", change.path, number,
                          f"a container action without a digest: {ascii_only(action, 80)}")
        elif not action.startswith("docker://") and not PINNED.search(action):
            first_party = action.startswith(("actions/", "github/"))
            yield Finding(REVIEW if first_party else HIGH, "ci-unpinned",
                          change.path, number,
                          f"an action pinned to a tag or branch, which its "
                          f"owner can move: {ascii_only(action, 80)}")
