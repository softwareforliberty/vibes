"""report-page's command.

    report-page <report.md> <report.html>

Writes a self-contained page holding the report. In a browser it renders
the Markdown, and each `mermaid` code block as a diagram, with pinned
libraries checked against their hashes, and sanitises the result, since a
report can quote untrusted code. Without the network it shows the
Markdown as plain text. The title is the report's first heading. Exits 0
when it worked and 2 on an error.
"""

from __future__ import annotations

import html
import json
import sys
from typing import Optional, Sequence

# Pinned versions, each with its subresource integrity hash.
SCRIPTS = (
    ("https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js",
     "sha384-/TQbtLCAerC3jgaim+N78RZSDYV7ryeoBCVqTuzRrFec2akfBkHS7ACQ3PQhvMVi"),
    ("https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js",
     "sha384-+VfUPEb0PdtChMwmBcBmykRMDd+v6D/oFmB3rZM/puCMDYcIvF968OimRh4KQY9a"),
    ("https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js",
     "sha384-WmdflGW9aGfoBdHc4rRyWzYuAjEmDwMdGdiPNacbwfGKxBW/SO6guzuQ76qjnSlr"),
)

STYLE = """
:root { color-scheme: light dark; --bg: #fdfdfc; --fg: #1f2328;
  --muted: #59636e; --line: #d1d9e0; --code: #f3f4f6; --accent: #0969da; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #0f1115; --fg: #e6e8eb; --muted: #9aa4af; --line: #30363d;
    --code: #1a1e24; --accent: #4493f8; } }
body { margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 60rem; margin: 0 auto; padding: 2rem 1rem 4rem; }
h1, h2, h3 { line-height: 1.25; } h2 { border-bottom: 1px solid var(--line);
  padding-bottom: .3rem; margin-top: 2.5rem; }
a { color: var(--accent); }
code, pre { font: 14px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
  background: var(--code); border-radius: 6px; }
code { padding: .1rem .3rem; } pre { padding: 1rem; overflow-x: auto; }
pre code { padding: 0; background: none; }
table { border-collapse: collapse; display: block; overflow-x: auto; }
th, td { border: 1px solid var(--line); padding: .4rem .7rem; }
blockquote { margin: 0; padding: 0 1rem; color: var(--muted);
  border-left: 3px solid var(--line); }
.mermaid { background: var(--code); border-radius: 6px; padding: 1rem;
  margin: 1rem 0; overflow-x: auto; text-align: center; }
#fallback { white-space: pre-wrap; }
"""

RENDER = """
try {
  const page = document.getElementById("page");
  page.innerHTML = DOMPurify.sanitize(marked.parse(SOURCE));
  for (const code of page.querySelectorAll("code.language-mermaid")) {
    const diagram = document.createElement("div");
    diagram.className = "mermaid";
    diagram.textContent = code.textContent;
    code.parentElement.replaceWith(diagram);
  }
  const dark = matchMedia("(prefers-color-scheme: dark)").matches;
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict",
                       theme: dark ? "dark" : "default" });
  mermaid.run();
} catch (error) {
  // Without the libraries, the plain text stays.
}
"""


def title(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Report"


def page(markdown: str) -> str:
    # In JSON, "</" may be written "<\\/", so the report can't end the
    # script element early.
    source = json.dumps(markdown).replace("</", "<\\/")
    scripts = "\n".join(
        f'<script src="{url}" integrity="{digest}" crossorigin="anonymous"'
        ' referrerpolicy="no-referrer"></script>' for url, digest in SCRIPTS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title(markdown))}</title>
<style>{STYLE}</style>
</head>
<body>
<main id="page"><pre id="fallback">{html.escape(markdown)}</pre></main>
<script>const SOURCE = {source};</script>
{scripts}
<script>{RENDER}</script>
</body>
</html>
"""


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(argv or [])
    if len(args) != 2:
        print("usage: report-page <report.md> <report.html>", file=sys.stderr)
        return 2
    try:
        with open(args[0], encoding="utf-8") as stream:
            markdown = stream.read()
        with open(args[1], "w", encoding="utf-8") as stream:
            stream.write(page(markdown))
    except OSError as error:
        print(f"report-page: {error}", file=sys.stderr)
        return 2
    return 0
