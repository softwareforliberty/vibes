"""Makes untrusted text safe to show to a person or an agent.

Everything the scan prints passes through here, so a path, a commit message
or an excerpt can't carry hidden characters or instructions in a form that
looks like the scan's own output.
"""

from __future__ import annotations

import unicodedata

# Code points that change how text displays, or hide text, without being
# visible themselves: bidirectional controls, zero-width characters, tag
# characters, variation selectors and other format characters.
BIDI = frozenset(
    [0x061C, 0x200E, 0x200F]
    + list(range(0x202A, 0x202F))
    + list(range(0x2066, 0x206A))
)
INVISIBLE = frozenset(
    [0x00AD, 0x034F, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x180E, 0x3164, 0xFFA0]
    + list(range(0x200B, 0x200E))
    + list(range(0x2060, 0x2065))
    + [0xFEFF]
)
TAGS = range(0xE0000, 0xE0080)
VARIATION_SELECTORS = frozenset(
    list(range(0xFE00, 0xFE10)) + list(range(0xE0100, 0xE01F0))
)


def is_hidden(code: int) -> bool:
    """Whether a code point is invisible or changes the display of text."""
    return (
        code in BIDI
        or code in INVISIBLE
        or code in TAGS
        or code in VARIATION_SELECTORS
        or (code < 0x20 and code not in (0x09, 0x0A))
        or 0x7F <= code < 0xA0
        or unicodedata.category(chr(code)) in ("Cf", "Co", "Cs", "Cn")
    )


def visible(text: str) -> str:
    """Replaces hidden code points with \\u{XXXX}, keeping line breaks.

    Used for the snapshot of each changed file, so a reviewer sees every
    hidden character, and the line numbers stay the same. Other non-ASCII
    text is kept, so the files stay readable.
    """
    out = []
    length = len(text)
    for index, char in enumerate(text):
        code = ord(char)
        if char == "\r" and index + 1 < length and text[index + 1] == "\n":
            out.append(char)
        elif char == "\\" and text.startswith("\\u{", index):
            # Mark a literal \u{ so it can't pass for one of ours.
            out.append("\\u{005C}")
        elif is_hidden(code):
            out.append(f"\\u{{{code:04X}}}")
        else:
            out.append(char)
    return "".join(out)


def ascii_only(text: str, limit: int = 0) -> str:
    """Escapes everything outside printable ASCII, and shortens long text.

    Used for every line of scan.md and the report: paths, excerpts, commit
    messages and names.
    """
    out = []
    for char in text:
        code = ord(char)
        if 0x20 <= code < 0x7F and char != "\\":
            out.append(char)
        elif char == "\\":
            out.append("\\\\")
        elif char == "\t":
            out.append("\\t")
        else:
            out.append(f"\\u{{{code:04X}}}")
    escaped = "".join(out)
    if limit and len(escaped) > limit:
        return escaped[: limit - 3] + "..."
    return escaped


def excerpt(text: str, limit: int = 80) -> str:
    """A short, escaped excerpt of a line, in backquotes."""
    return "`" + ascii_only(text.strip(), limit).replace("`", "'") + "`"
