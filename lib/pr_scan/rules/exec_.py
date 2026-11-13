"""Code that decodes and runs other code, or downloads and runs it.

XZ's build script pulled its payload out of a test file with tr, head and
xz -d, and ran it with eval.
"""

from __future__ import annotations

import re
from typing import Iterator

from ..escape import excerpt
from ..model import HIGH, REVIEW, Context, Finding
from .common import added, matching, regex, severity_for

PIPE_TO_SHELL = regex(
    r"\b(?:curl|wget|fetch|aria2c|http)\b[^|;]*\|\s*(?:sudo\s+)?(?:ba|z|k|da)?sh\b",
    r"\b(?:curl|wget)\b[^|;]*\|\s*(?:python\d?|perl|ruby|node|php|bash|eval)\b",
    r"(?:\bsource|\.|\bbash|\bsh)\s+<\(", r"\bsh\s+-c\s+[\"']?\$\((?:curl|wget)",
    r"\beval\s+[\"']?\$\((?:curl|wget)", r"\|\s*(?:ba)?sh\s*(?:-s)?\s*$",
    r"\|\s*eval\b", r"\biex\s*\(\s*(?:New-Object|iwr|Invoke-WebRequest|irm)",
    r"Invoke-Expression")
DECODE = regex(r"\bbase64\s+(?:-d|--decode|-D)\b", r"\bxxd\s+-r\b",
               r"\bopenssl\s+(?:enc|base64)\b.*-d\b", r"\buudecode\b",
               r"\btr\s+[\"']?\\?[\w\\]+-", r"\btr\s+[\"'][^\"']*\\[tnr0-7]",
               r"\bhead\s+-c\s*\+?\d", r"\btail\s+-c\s*\+?\d",
               r"\bdd\b.*\b(?:skip|seek|bs|count)=",
               r"\b(?:xz|lzma|gzip|bzip2|zstd|lz4|brotli)\s+[^|;]*-(?:d|dc|cd)\b",
               r"\b(?:unxz|xzcat|unlzma|lzcat|gunzip|zcat|bunzip2|bzcat|unzstd|"
               r"zstdcat|uncompress)\b", r"\bcpio\s+-i", r"\btar\s+\S*x",
               r"\bunzip\b", r"\bperl\s+-(?:pe|ne|e)\b.*\bunpack\b",
               r"\bprintf\s+[\"'](?:\\x[0-9a-fA-F]{2}|\\[0-7]{3}){4}")
RUN_STRING = regex(r"(?<![\w.])eval\s*[\(\"'$`]", r"(?<![\w.])exec\s*\(",
                   r"\bcompile\s*\([^)]*[\"']exec[\"']", r"\bnew\s+Function\s*\(",
                   r"\bsetTimeout\s*\(\s*[\"'`]", r"\bsetInterval\s*\(\s*[\"'`]",
                   r"\bvm\.runIn\w+\(", r"\bmarshal\.loads\(",
                   r"\b__import__\s*\(", r"\bimportlib\.import_module\s*\(",
                   r"\bpickle\.loads?\(", r"\bInstance_eval\b|\binstance_eval\b",
                   r"\bclass_eval\b", r"\bsend\s*\(\s*:", r"\bassert\s*\(\s*\$",
                   r"\bcreate_function\s*\(", r"\bScriptEngineManager\b",
                   r"\bRuntime\.getRuntime\(\)\.exec\b", r"\bloadstring\s*\(",
                   r"\bload\s*\(\s*[\"'\[]", r"\bdofile\s*\(",
                   r"\bInvoke-Expression\b|\biex\b")
DECODED_INPUT = re.compile(r"b64decode|base64|atob\(|Buffer\.from\([^)]*['\"]"
                           r"(?:base64|hex)|decompress|zlib|gzip|lzma|bz2|"
                           r"marshal|codecs\.decode|fromCharCode|unhexlify|"
                           r"bytes\.fromhex|\\x[0-9a-fA-F]{2}|rot_?13|"
                           r"\[::-1\]|reverse\(", re.IGNORECASE)
INLINE = regex(r"\b(?:python\d?(?:\.\d+)?|perl|ruby|node|php|deno|bun)\s+"
               r"-[A-Za-z]*[ceE]\b", r"\bpowershell\b.*-(?:e|enc|EncodedCommand)\b",
               r"\bbash\s+-c\b", r"\bsh\s+-c\b")
DOWNLOAD = regex(r"\b(?:curl|wget|aria2c)\b", r"\bgit\s+clone\b",
                 r"^\s*ADD\s+https?://", r"\bInvoke-WebRequest\b|\biwr\b",
                 r"\burllib\.request\b", r"\brequests\.get\(", r"\bfetch\(",
                 r"\bfile\s*\(\s*DOWNLOAD", r"\bFetchContent_Declare\b",
                 r"\bgo\s+install\b.*@", r"\bpip\s+install\b",
                 r"\bnpm\s+(?:install|i|exec)\b|\bnpx\b",
                 r"\bcargo\s+install\b", r"\bgem\s+install\b",
                 r"\bapt(?:-get)?\s+install\b|\bapk\s+add\b|\bdnf\s+install\b|"
                 r"\byum\s+install\b|\bbrew\s+install\b")
MAKE_EXECUTABLE = re.compile(r"\bchmod\s+(?:[ugoa]*\+[rwx]*x|[0-7]?[0-7]*[1357]"
                             r"[0-7]{0,2})\b")


def check(ctx: Context) -> Iterator[Finding]:
    yield from matching(added(ctx), PIPE_TO_SHELL, HIGH, "exec-pipe-to-shell",
                        "runs downloaded or piped text as a program")
    risky = ("build", "ci", "test", "gate")
    for change, number, text in added(ctx):
        if "docs" in change.classes:
            continue
        if DECODE.search(text):
            yield Finding(severity_for(change, risky, REVIEW), "exec-decode",
                          change.path, number,
                          f"decodes, decompresses or slices bytes, as XZ's "
                          f"build script did: {excerpt(text)}")
        if RUN_STRING.search(text):
            decoded = DECODED_INPUT.search(text)
            yield Finding(HIGH if decoded else REVIEW, "exec-run-string",
                          change.path, number,
                          f"runs a string or data as code"
                          f"{', after decoding it' if decoded else ''}: "
                          f"{excerpt(text)}")
    yield from matching(added(ctx, "build", "ci", "gate"), INLINE, REVIEW,
                        "exec-inline", "runs an inline program")
    yield from matching(added(ctx, "build", "ci", "gate"), DOWNLOAD, REVIEW,
                        "exec-download", "downloads or installs something")
    yield from matching(added(ctx, "build", "ci", "gate", "test"),
                        MAKE_EXECUTABLE, REVIEW, "exec-chmod",
                        "makes a file executable")
