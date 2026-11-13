"""Git metadata that hides diffs, runs drivers or changes release tarballs."""

from __future__ import annotations

import posixpath
import re
from typing import Iterator

from ..escape import excerpt
from ..model import HIGH, REVIEW, Context, Finding

HIDING = re.compile(r"linguist-(?:generated|vendored|documentation)|"
                    r"(?:^|\s)-diff\b|(?:^|\s)binary\b|(?:^|\s)-text\b|"
                    r"\b(?:filter|diff|merge)=|working-tree-encoding|"
                    r"export-ignore|export-subst|\bident\b")
WHY = {
    "linguist": "hides the file's diff on GitHub by default",
    "diff": "hides the file's diff",
    "binary": "makes git treat text as binary, hiding its diff",
    "text": "makes git treat text as binary, hiding its diff",
    "filter": "names a filter or driver that runs a command",
    "merge": "names a merge driver that runs a command",
    "working-tree-encoding": "changes the file's encoding on checkout",
    "export": "makes release tarballs differ from the repository, the other "
              "half of XZ",
    "ident": "rewrites the file on checkout",
}


def check(ctx: Context) -> Iterator[Finding]:
    for change in ctx.files:
        name = posixpath.basename(change.path)
        if name == ".gitattributes":
            for number, text in change.added():
                match = HIDING.search(text)
                if match:
                    word = match.group().strip().lstrip("-")
                    reason = next((why for key, why in WHY.items()
                                   if word.startswith(key)), WHY["filter"])
                    yield Finding(HIGH, "gitattrs-attribute", change.path,
                                  number, f"{reason}: {excerpt(text)}")
        elif name in (".lfsconfig", ".gitconfig"):
            yield Finding(HIGH, "gitattrs-config", change.path, 0,
                          "git configuration in the repository")
        elif name == "CODEOWNERS":
            yield Finding(HIGH, "gitattrs-codeowners", change.path, 0,
                          "changes who must approve changes")
        elif name == ".mailmap":
            yield Finding(REVIEW, "gitattrs-mailmap", change.path, 0,
                          "rewrites who commits appear to be by")
        elif name == ".git-blame-ignore-revs":
            yield Finding(REVIEW, "gitattrs-blame-ignore", change.path, 0,
                          "hides commits from git blame")
