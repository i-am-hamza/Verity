"""Static code audit of app/crawler/.

CLAUDE.md rules 1-3 forbid:
  - account creation / login
  - CAPTCHA solving / bot-check evasion
  - IP or UA rotation to dodge a block
  - keyboard typing or form submission (because the sites we hit are
    public static pages — anything that *types* into a page is reaching
    for authenticated or interactive flows we're not meant to touch)

This test grep's every source file under app/crawler/ for the signature
patterns of those operations. Any match fails the build. The pattern
list is intentionally conservative — Playwright has a `.fill()` and
`.type()` that are the usual stand-ins for form submission, and
`page.click("input[type=submit]")` is the usual way to submit, so those
are the ones that must stay absent.
"""
from __future__ import annotations

import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
CRAWLER_DIR = BACKEND / "app" / "crawler"

# Each entry = (compiled regex, human description used in failure msg).
# Patterns look for syntactic markers, not substrings, so they don't false-
# positive on comments that explain what we *don't* do.
_FORBIDDEN = [
    (re.compile(r"\bpage\.type\s*\("), "Playwright .type() keystrokes — forbidden"),
    (re.compile(r"\bpage\.fill\s*\("), "Playwright .fill() form fill — forbidden"),
    (re.compile(r"\bpage\.press\s*\("), "Playwright .press() keystroke — forbidden"),
    (re.compile(r"\bpage\.click\s*\([^)]*(?:login|sign[-_ ]?in|submit)",
                re.IGNORECASE), "Playwright click targeting a login/submit — forbidden"),
    (re.compile(r"\bgoto\s*\([^)]*(?:login|sign[-_ ]?in|account|register)",
                re.IGNORECASE), "navigation to a login/register URL — forbidden"),
    (re.compile(r"form_submit|form\.submit|submit\s*=\s*True",
                re.IGNORECASE), "form submission — forbidden"),
    # CAPTCHA SOLVING signatures only — the word "captcha" is allowed in
    # block-marker DETECTION lists (fetch.py:BLOCK_MARKERS looks for the
    # substring "captcha" in response bodies to know when to stop). What's
    # forbidden is any active interaction with a CAPTCHA service.
    (re.compile(r"solve_captcha|captcha_solver|2captcha|anti[-_]?captcha|"
                r"captcha_token|recaptcha_response|hcaptcha_response",
                re.IGNORECASE),
     "CAPTCHA solver / bypass — forbidden (we stop for the domain instead)"),
    (re.compile(r"username\s*[:=]|password\s*[:=]|api[_-]?key\s*[:=]",
                re.IGNORECASE),
     "credentials — forbidden (public pages only)"),
    (re.compile(r"user_agents\s*=\s*\[|ROTATING_UA|rotate_ua",
                re.IGNORECASE),
     "UA rotation — forbidden (identify honestly)"),
    (re.compile(r"proxy\s*=|proxies\s*=\s*\{", re.IGNORECASE),
     "proxy configuration — forbidden (no IP rotation)"),
]

# Allow mentions in docstrings and comment-only files (block-markers list etc.).
_COMMENT_LINE = re.compile(r"^\s*(#|/\*|\*|\"\"\"|''')")


def _lines_of(path: Path) -> list[tuple[int, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, str]] = []
    in_docstring = False
    docstring_quote = None
    for n, line in enumerate(lines, 1):
        # Skip triple-quoted docstring blocks when deciding whether a
        # pattern is "in code" vs "in a comment that documents what we
        # *don't* do". Non-trivial to do perfectly without a parser;
        # we do a best-effort pass that handles the common case.
        stripped = line.strip()
        if in_docstring:
            if docstring_quote and docstring_quote in stripped:
                in_docstring = False
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            quote = stripped[:3]
            # Could be a one-liner """x""".
            if stripped.count(quote) >= 2:
                continue
            in_docstring = True
            docstring_quote = quote
            continue
        if _COMMENT_LINE.match(line):
            continue
        out.append((n, line))
    return out


def test_crawler_has_no_forbidden_patterns():
    violations: list[str] = []
    for path in sorted(CRAWLER_DIR.rglob("*.py")):
        for lineno, line in _lines_of(path):
            for pattern, reason in _FORBIDDEN:
                if pattern.search(line):
                    rel = path.relative_to(BACKEND)
                    violations.append(f"{rel}:{lineno}  {reason}\n    {line.rstrip()}")
    assert not violations, (
        "CLAUDE.md rules 1-3 violations in crawler/:\n  "
        + "\n  ".join(violations)
    )


# Also assert that CLAUDE.md's "sustainabilityreports.com" exclusion is
# materialised somewhere in the data layer so a future contributor can't
# re-enable it without noticing. Kept here rather than in the crawler
# because the exclusion is a *data* decision (which domains we touch),
# not a code one.
def test_sustainabilityreports_is_recorded_as_excluded():
    log = (BACKEND.parent / "docs" / "DATA_SOURCING_LOG.md")
    text = log.read_text(encoding="utf-8") if log.exists() else ""
    assert "sustainabilityreports.com" in text and "excluded" in text.lower(), (
        "DATA_SOURCING_LOG.md must record the sustainabilityreports.com "
        "exclusion (CLAUDE.md rule 4). Current log does not mention it."
    )
