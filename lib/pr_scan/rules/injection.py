"""Text written to steer an AI reviewer or agent, hidden text in Markdown and
SVG, and links whose text names another site."""

from __future__ import annotations

import re
from typing import Iterator, List, Tuple

from .. import binfmt
from ..escape import BIDI, INVISIBLE, TAGS, excerpt
from ..model import HIGH, REVIEW, Context, Finding
from .common import added, hosts

PHRASES = re.compile(
    r"\b(?:ignore|disregard|forget|override|bypass)\b.{0,40}\b(?:previous|"
    r"prior|above|earlier|all|any|your|the)\b.{0,40}\b(?:instructions?|"
    r"prompts?|rules|guidelines|directives|context|findings)"
    r"|\b(?:AI|LLM|language model|assistant|agent|claude|chatgpt|gpt-?\d*|"
    r"copilot|gemini|code ?rabbit|reviewer bot|automated reviewers?|bots?)\b"
    r".{0,60}\b(?:must|should|shall|please|approve|ignore|skip|do not|don't|"
    r"never|always|instructed|told|allowed)\b"
    r"|\b(?:note|message|instructions?|attention|important)\s+(?:to|for)\s+"
    r"(?:the\s+)?(?:AI|LLM|reviewers?|assistants?|models?|agents?|bots?)\b"
    r"|\bsystem prompt\b|\bdeveloper message\b|\byou are (?:now )?(?:an? |the )"
    r"(?:helpful|AI|assistant|reviewer|security)|\bact as (?:an? |the )"
    r"|\bnew instructions\b|\bBEGIN (?:SYSTEM|INSTRUCTIONS|PROMPT)\b"
    r"|</?(?:system|instructions?|assistant|user|human|tool_result|"
    r"function_results|antml:[a-z_]+)>|\[/?INST\]|<\|im_(?:start|end)\|>|"
    r"<\|endoftext\|>|<\|(?:system|user|assistant)\|>"
    r"|\b(?:approve|LGTM|mark (?:it|this) as safe|report no (?:issues|findings)|"
    r"has been (?:audited|reviewed|approved|vetted)|already (?:audited|"
    r"reviewed|approved))\b.{0,40}\b(?:this|automatically|without)\b"
    r"|\b(?:do not|don't|never)\s+(?:flag|report|mention|review|scan)\b"
    r"|ignorez? (?:les|toutes les) instructions|ignoriere .{0,20}anweisungen|"
    r"ignora (?:las|le|todas) (?:instrucciones|istruzioni)|игнорируй|"
    r"忽略.{0,6}(?:指令|说明|指示)|以前の指示|이전 지시",
    re.IGNORECASE)
HTML_COMMENT = re.compile(r"<!--(.*?)(?:-->|$)", re.DOTALL)
SVG_ACTIVE = re.compile(r"<script\b|\bon[a-z]+\s*=|<foreignObject\b|"
                        r"javascript:|<iframe\b|<embed\b|<object\b",
                        re.IGNORECASE)
SVG_HIDDEN = re.compile(r"(?:opacity|fill-opacity)\s*[:=]\s*[\"']?0(?:\.0+)?"
                        r"[\"';\s]|font-size\s*[:=]\s*[\"']?0(?:px)?[\"';\s]|"
                        r"display\s*[:=]\s*[\"']?none|visibility\s*[:=]\s*"
                        r"[\"']?hidden", re.IGNORECASE)
LINK = re.compile(r"\[([^\]]*https?://[^\]]*)\]\((https?://[^)\s]+)")


def check(ctx: Context) -> Iterator[Finding]:
    for change, number, text in added(ctx):
        if PHRASES.search(text):
            yield Finding(HIGH, "injection-text", change.path, number,
                          f"text addressed to an AI reviewer or agent: "
                          f"{excerpt(text)}")
        for shown, target in LINK.findall(text):
            shown_hosts = set(hosts(shown))
            target_hosts = set(hosts(target))
            if shown_hosts and target_hosts and not (shown_hosts &
                                                     target_hosts):
                yield Finding(HIGH, "injection-link", change.path, number,
                              f"a link that shows one site but goes to "
                              f"another: {excerpt(text)}")
    for change in ctx.text_files():
        name = change.path.lower()
        if name.endswith((".md", ".markdown", ".mdx", ".html", ".htm")):
            old = change.old_text()
            for comment in HTML_COMMENT.findall(change.new_text()):
                if comment.strip() and comment not in old:
                    severity = HIGH if PHRASES.search(comment) else REVIEW
                    yield Finding(severity, "injection-hidden-comment",
                                  change.path, _line(change.new_text(),
                                                     comment),
                                  f"a comment readers of the rendered page "
                                  f"won't see: {excerpt(comment)}")
        if name.endswith(".svg"):
            text = change.new_text()
            if SVG_ACTIVE.search(text):
                yield Finding(HIGH, "injection-svg-script", change.path, 0,
                              "an SVG with script, event handlers or "
                              "embedded content")
            if SVG_HIDDEN.search(text):
                yield Finding(REVIEW, "injection-svg-hidden", change.path, 0,
                              "an SVG with invisible text or shapes")
    for change in ctx.changed():
        if change.binary:
            for found in binfmt.printable_strings(change.new()):
                if PHRASES.search(found):
                    yield Finding(HIGH, "injection-in-binary", change.path, 0,
                                  f"text in a binary addressed to an AI "
                                  f"reviewer or agent: {excerpt(found)}")
                    break
    yield from _metadata(ctx)


def _line(text: str, fragment: str) -> int:
    index = text.find(fragment)
    return text.count("\n", 0, index) + 1 if index >= 0 else 0


def _metadata(ctx: Context) -> Iterator[Finding]:
    """The pull request's title and description, and every commit message."""
    texts: List[Tuple[str, str]] = []
    for key in ("title", "body"):
        value = ctx.meta.get(key)
        if isinstance(value, str):
            texts.append((f"(pull request {key})", value))
    for commit in ctx.commits:
        texts.append((f"(commit {commit.sha[:12]})", commit.message))
        texts.append((f"(commit {commit.sha[:12]} author)",
                      f"{commit.author_name} <{commit.author_email}>"))
    for where, text in texts:
        codes = [ord(char) for char in text]
        if any(code in BIDI or code in INVISIBLE or code in TAGS
               for code in codes):
            yield Finding(HIGH, "injection-metadata-hidden", where, 0,
                          "hidden or bidirectional characters")
        for line in text.split("\n"):
            if PHRASES.search(line):
                yield Finding(HIGH, "injection-metadata", where, 0,
                              f"text addressed to an AI reviewer or agent: "
                              f"{excerpt(line)}")
                break
        for comment in HTML_COMMENT.findall(text):
            if comment.strip():
                yield Finding(REVIEW, "injection-metadata-comment", where, 0,
                              f"a hidden comment: {excerpt(comment)}")
                break
