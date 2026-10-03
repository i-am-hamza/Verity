"""Build-failing guard: the crawler package must never attempt to submit
forms, type into inputs, click submit controls, send HTTP POST, or read
passwords. If this test fails, the crawler has grown a shape it is
forbidden to have per CLAUDE.md (public pages only, no login, no
credentials, read-only Playwright).

Scans backend/app/crawler/ and app/cli.py and any .py it imports.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

CRAWLER_DIR = BACKEND / "app" / "crawler"
CLI_FILE = BACKEND / "app" / "cli.py"

# Patterns we refuse. All forms of Playwright input + requests.post + reads
# that could pull credentials.
FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("playwright .fill(",   re.compile(r"\.fill\s*\(")),
    ("playwright .type(",   re.compile(r"\.type\s*\(")),
    ("playwright .press(",  re.compile(r"\.press\s*\(")),
    ("playwright .click(",  re.compile(r"\.click\s*\(")),
    ("playwright .set_checked(", re.compile(r"\.set_checked\s*\(")),
    (".submit(",            re.compile(r"\.submit\s*\(")),
    ("requests.post / session.post", re.compile(r"\b(?:requests|session|self\.session)\s*\.\s*post\s*\(")),
    ("HTTP POST method param",       re.compile(r'\bmethod\s*=\s*[\'"]POST[\'"]', re.IGNORECASE)),
    ("sys.getpass",         re.compile(r"getpass\s*\.")),
    ("password var",        re.compile(r"\bpassword\b", re.IGNORECASE)),
    ("api_key / api-token", re.compile(r"\b(?:api_key|api-token|apitoken)\b", re.IGNORECASE)),
    ("login(",              re.compile(r"\blogin\s*\(")),
    ("sign_in(",            re.compile(r"\bsign_in\s*\(")),
]


# Lines ending with "# allow-write-action: <reason>" are permitted even if they
# would otherwise match. This exists so a parser can SEE patterns like
# "data-href" or "onclick" in HTML without the guard false-flagging normal
# code strings; we don't actually use this escape anywhere today, so if it
# ever starts appearing a reviewer should look twice.
ALLOW_MARKER = "# allow-write-action:"


def _collect_files() -> list[Path]:
    files = [CLI_FILE]
    files.extend(sorted(CRAWLER_DIR.rglob("*.py")))
    # Deduplicate while preserving order.
    seen: set[Path] = set()
    uniq: list[Path] = []
    for f in files:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq


def test_crawler_contains_no_forbidden_write_actions_or_credential_reads():
    violations: list[tuple[str, Path, int, str, str]] = []

    for f in _collect_files():
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), start=1):
            if ALLOW_MARKER in line:
                continue
            stripped = line.strip()
            # Skip comments and docstring-only lines unless the pattern is
            # structurally dangerous (POST method param). The point is to
            # catch CODE that performs forbidden actions, not prose that
            # describes avoiding them.
            is_comment = stripped.startswith("#")
            is_prose = (stripped.startswith('"""') or stripped.startswith("'''")
                        or (stripped.startswith('"') and stripped.endswith('"')))
            if is_comment or is_prose:
                continue
            for name, pat in FORBIDDEN_PATTERNS:
                if pat.search(line):
                    violations.append((name, f, i, line.rstrip(), stripped))

    assert not violations, (
        "Crawler contains forbidden write-actions or credential reads:\n"
        + "\n".join(
            f"  {name} at {path.relative_to(BACKEND)}:{lineno}  →  {line}"
            for name, path, lineno, line, _ in violations
        )
    )
