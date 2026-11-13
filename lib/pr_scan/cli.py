"""pr-scan's commands: scan a pull request, or build the report from a review.

    pr-scan scan --repo <dir> --base <commit> --head <commit> --out <dir>
                 [--meta <dir>]
    pr-scan report --out <dir>

Both print only a fixed summary of validated SHAs and counts, so no text
from the pull request reaches the agent that runs them.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from typing import Dict, List, Optional, Sequence, Set, Tuple

from . import report, rules, snapshot
from .escape import ascii_only
from .gitio import Change, Commit, Git
from .model import (CONFIG_FILE, SEVERITIES, Config, Context, FileChange,
                    Finding)

SHA = re.compile(r"\A[0-9a-f]{40}\Z")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="pr-scan")
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan")
    scan.add_argument("--repo", required=True)
    scan.add_argument("--base", required=True)
    scan.add_argument("--head", required=True)
    scan.add_argument("--out", required=True)
    scan.add_argument("--meta")
    build = commands.add_parser("report")
    build.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "scan":
            return run_scan(args.repo, args.base, args.head, args.out,
                            args.meta)
        return report.build(args.out)
    except (RuntimeError, OSError, ValueError) as error:
        print(f"pr-scan: {ascii_only(str(error), 300)}", file=sys.stderr)
        return 2


def load_meta(directory: Optional[str]) -> Dict[str, object]:
    meta: Dict[str, object] = {}
    if not directory:
        return meta
    for key in ("pull", "commits"):
        path = os.path.join(directory, f"{key}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as stream:
                text = stream.read()
            try:
                meta[key] = json.loads(text)
            except ValueError:
                # gh --paginate --jq '.[]' writes one object per line.
                meta[key] = [json.loads(line) for line in text.splitlines()
                             if line.strip()]
    pull = meta.get("pull")
    if isinstance(pull, dict):
        meta["title"] = pull.get("title") or ""
        meta["body"] = pull.get("body") or ""
    return meta


def context(repo: str, base_name: str, head_name: str,
            meta: Dict[str, object]) -> Context:
    git = Git(repo)
    head = git.rev(head_name)
    base = git.merge_base(git.rev(base_name), head)
    for sha in (base, head):
        if not SHA.match(sha):
            raise ValueError("git returned something that isn't a commit")
    changes = git.diff(base, head)
    commits = git.commits(base, head)
    config, config_changed = read_config(git, base, changes)
    return Context(git, base, head, [FileChange(c, git) for c in changes],
                   commits, history_only(git, commits, head), config,
                   config_changed, meta)


def run_scan(repo: str, base_name: str, head_name: str, out: str,
             meta_dir: Optional[str]) -> int:
    ctx = context(repo, base_name, head_name, load_meta(meta_dir))
    base, head = ctx.base, ctx.head
    findings = rules.run(ctx)
    findings += per_commit(ctx, findings)
    os.makedirs(out, exist_ok=True)
    snapshot.write(ctx, out)
    write_scan(out, base, head, findings)
    write_guides_input(out, ctx)
    for name, value in (("base.txt", base), ("head.txt", head)):
        with open(os.path.join(out, name), "w", encoding="ascii") as stream:
            stream.write(value + "\n")
    summary(base, head, ctx, findings)
    return 1 if findings else 0


def read_config(git: Git, base: str,
                changes: List[Change]) -> Tuple[Config, bool]:
    entry = git.tree(base).get(CONFIG_FILE)
    text = git.blob(entry[1]).decode("utf-8", "replace") if entry else ""
    changed = any(CONFIG_FILE in (c.path, c.old_path) for c in changes)
    return Config.parse(text), changed


def history_only(git: Git, commits: List[Commit],
                 head: str) -> List[Tuple[Commit, Change]]:
    """Blobs a commit added that the head no longer has, once each."""
    final: Set[str] = {sha for _, sha in git.tree(head).values()}
    seen: Set[str] = set()
    found = []
    for commit in commits:
        for change in git.commit_changes(commit):
            sha = change.new_sha
            if change.status == "D" or sha in final or sha in seen or \
                    change.new_mode == "160000":
                continue
            seen.add(sha)
            found.append((commit, change))
    return found


# Families that judge the pull request as a whole, not one commit's change.
WHOLE = ("config-", "history-", "external-", "injection-metadata",
         "binary-history-only", "gitlevel-history-only", "gitlevel-merge")


def per_commit(ctx: Context, final: List[Finding]) -> List[Finding]:
    """HIGH findings in a commit's own change that the head no longer has.

    A payload added in one commit and removed in a later one stays in
    history, where an old checkout or git bisect can still run it.
    """
    if len(ctx.commits) < 2:
        return []
    known = {(f.rule, f.path, f.message) for f in final}
    found: List[Finding] = []
    for commit in ctx.commits:
        parent = commit.parents[0] if commit.parents else ctx.base
        sub = Context(ctx.git, parent, commit.sha,
                      [FileChange(c, ctx.git) for c in ctx.git.diff(
                          parent, commit.sha)],
                      [], [], ctx.config, False, {})
        for finding in rules.run(sub):
            key = (finding.rule, finding.path, finding.message)
            if finding.severity != "HIGH" or key in known or \
                    finding.rule.startswith(WHOLE):
                continue
            known.add(key)
            found.append(Finding(
                "HIGH", finding.rule, finding.path, finding.line,
                f"in commit {commit.sha[:12]} only, gone by the head: "
                f"{finding.message}"))
    return found


def write_scan(out: str, base: str, head: str,
               findings: List[Finding]) -> None:
    counts = Counter(f.severity for f in findings)
    lines = ["SCAN", f"base: {base}", f"head: {head}",
             "findings: " + ", ".join(f"{s} {counts.get(s, 0)}"
                                      for s in SEVERITIES), ""]
    for finding in findings:
        lines.append(safe(f"[{finding.severity}] {ascii_only(finding.path)}:"
                          f"{finding.line}: {finding.rule}: "
                          f"{finding.message}"))
    with open(os.path.join(out, "scan.md"), "w", encoding="ascii") as stream:
        stream.write("\n".join(lines) + "\n")


def safe(line: str) -> str:
    """A last guard: printable ASCII only, whatever a rule wrote."""
    return "".join(c if 0x20 <= ord(c) < 0x7F else "?" for c in line)


def write_guides_input(out: str, ctx: Context) -> None:
    """Each changed path and the file to read its first line from, for
    bin/pr-prepare to pass to guides::for_file."""
    with open(os.path.join(out, "guides-input.tsv"), "w",
              encoding="ascii") as stream:
        for change in ctx.changed():
            view = os.path.join(out, "blobs", f"{change.change.new_sha}.txt")
            stream.write(f"{ascii_only(change.path)}\t{view}\n")


def summary(base: str, head: str, ctx: Context,
            findings: List[Finding]) -> None:
    counts = Counter(f.severity for f in findings)
    by_rule = Counter(f.rule for f in findings)
    print(f"pr-scan: base {base} head {head}")
    print(f"pr-scan: {len(ctx.files)} files changed, {len(ctx.commits)} "
          f"commits, {len(ctx.history_only)} files only in history")
    print("pr-scan: findings " + " ".join(f"{s} {counts.get(s, 0)}"
                                          for s in SEVERITIES))
    if by_rule:
        print("pr-scan: rules " + " ".join(f"{rule}={count}" for rule, count
                                           in sorted(by_rule.items())))


if __name__ == "__main__":
    sys.exit(main())
