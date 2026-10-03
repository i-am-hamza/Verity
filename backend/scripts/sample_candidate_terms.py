"""Pull 15 random match sentences each for 'sustainable' and 'nature'
across the 6 reports used in the Session 5 recall audit, so a human can
classify ESG-related vs generic usage.

Deterministic (seed 42). Scoring pipeline is not touched.
"""
from __future__ import annotations

import os
import random
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("VERITY_CONTACT_EMAIL", "ana.muhandis@protonmail.com")
sys.stdout.reconfigure(encoding="utf-8")

import pymupdf  # noqa: E402

import app.models  # noqa: E402,F401
from app.database import engine  # noqa: E402
from sqlalchemy import text as sql_text  # noqa: E402

TARGETS: list[tuple[str, int]] = [
    ("al-rajhi-bank", 2025),
    ("kuwait-finance-house", 2024),
    ("first-abu-dhabi-bank", 2025),
    ("bank-muscat-bkmb", 2025),
    ("the-saudi-national-bank", 2025),
    ("bupa-arabia-for-cooperative-insurance-company", 2022),
]
TERMS = ["sustainable", "nature"]
N_PER_TERM = 15
SEED = 42


def _report_paths() -> list[tuple[str, int, str]]:
    with engine.connect() as c:
        rows = list(c.execute(sql_text("""
            SELECT i.slug, r.fiscal_year, r.file_path
            FROM reports r JOIN institutions i ON i.id = r.institution_id
            WHERE r.status = 'scored'
        """)))
    by_key = {(r[0], r[1]): r[2] for r in rows}
    out: list[tuple[str, int, str]] = []
    for slug, fy in TARGETS:
        p = by_key.get((slug, fy))
        if p:
            out.append((slug, fy, p))
    return out


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def _sentences_with_term(text: str, term: str) -> list[str]:
    """Return every sentence that contains `term` (word-boundary,
    case-insensitive). Sentences are split with a cheap regex rather than
    the full spaCy pipeline — this is a sampling helper, not a scorer.
    """
    pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
    out: list[str] = []
    # Flatten the whole doc to one text block separated by \n, then split.
    for raw_sent in _SENT_SPLIT.split(text):
        s = raw_sent.strip().replace("\n", " ")
        s = re.sub(r"\s+", " ", s)
        if 10 < len(s) < 500 and pattern.search(s):
            out.append(s)
    return out


def main() -> int:
    paths = _report_paths()
    print(f"found {len(paths)} report files")
    # Extract once per report.
    texts: dict[tuple[str, int], str] = {}
    for slug, fy, path in paths:
        doc = pymupdf.open(path)
        try:
            texts[(slug, fy)] = "\n".join(
                (doc[i].get_text("text") or "") for i in range(doc.page_count)
            )
        finally:
            doc.close()

    rng = random.Random(SEED)
    out_lines: list[str] = []
    out_lines.append("# Candidate-term sample: sustainable + nature\n")
    out_lines.append(f"15 random sentences per term across the 6 recall-audit "
                     f"reports. Seed {SEED}.\n")

    for term in TERMS:
        pool: list[tuple[str, int, str]] = []
        for (slug, fy), txt in texts.items():
            for s in _sentences_with_term(txt, term):
                pool.append((slug, fy, s))
        rng.shuffle(pool)
        chosen = pool[:N_PER_TERM]
        out_lines.append(f"\n## `{term}` (pool: {len(pool)}, chose first {len(chosen)})\n")
        out_lines.append("| # | slug | FY | sentence | verdict |")
        out_lines.append("|---|---|---|---|---|")
        for i, (slug, fy, s) in enumerate(chosen, start=1):
            cleaned = s.replace("|", "/")
            out_lines.append(f"| {i} | `{slug}` | {fy} | {cleaned} |  |")

    out = Path(BACKEND).parent / "docs" / "SAMPLE_SUSTAINABLE_NATURE.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
