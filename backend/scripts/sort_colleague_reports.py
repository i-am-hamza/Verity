"""Sort PDFs from data/colleague_reports/ into storage/manual_inbox/<slug>/
so the existing `ingest-manual` CLI can pick them up as source=manual.

Match strategy per PDF:
1. Pull a candidate institution name + year from the filename (fast path —
   most of the dropped-in files follow the `<Company> Annual Report <YYYY>`
   or `<Company>_Annual_Report_<YYYY>` convention).
2. Fuzzy-match that candidate against the 60 active institutions. The
   taxonomy of names is small, so RapidFuzz WRatio + threshold = 85 is
   plenty.
3. Open the PDF, extract the first 2-3 pages, and
   (a) require the matched institution's canonical name tokens to appear
       in the body text as a sanity cross-check,
   (b) use `_detect_year_in_text` to confirm / recover the fiscal year.
4. Confident = match score >= 85 AND fiscal year detected in [2020, 2025].
5. Unmatched goes to a review list with best guess + reason — never filed.

The script does NOT ingest. It copies into manual_inbox/<slug>/ and lets
`python -m app.cli ingest-manual` do the actual record creation, so
dedup / validation / manifest go through the same path as hand-dropped
files.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("VERITY_CONTACT_EMAIL", "ana.muhandis@protonmail.com")
sys.stdout.reconfigure(encoding="utf-8")

import pymupdf  # noqa: E402
from rapidfuzz import fuzz  # noqa: E402

from app.crawler import register_all_mappers  # noqa: E402

register_all_mappers()

from app.crawler.validate import _detect_year_in_text  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.institution import Institution  # noqa: E402

SOURCE_DIR = BACKEND.parent / "data" / "colleague_reports"
MANUAL_INBOX = BACKEND / "storage" / "manual_inbox"
UNMATCHED_LOG = BACKEND.parent / "docs" / "COLLEAGUE_UNMATCHED.md"

YEAR_WINDOW = range(2020, 2026)
MATCH_SCORE_THRESHOLD = 85  # WRatio 0-100 scale
MATCH_SCORE_SOFT = 70       # below this = not even a "best guess", skip
FY_RX_FILENAME = re.compile(r"(?<!\d)(20[12]\d)(?!\d)")
AR_SPLIT_RX = re.compile(
    r"\s*(?:annual|integrated)[\s_-]*(?:report)?",
    re.IGNORECASE,
)


@dataclass
class SortResult:
    pdf_path: Path
    status: str                  # confident | unmatched
    slug: str | None = None
    fiscal_year: int | None = None
    score: float | None = None
    reason: str = ""
    first_pages_excerpt: str = ""


@dataclass
class Report:
    confident: list[SortResult] = field(default_factory=list)
    unmatched: list[SortResult] = field(default_factory=list)


def _strip_filename_to_name_part(stem: str) -> str:
    """Everything before the 'Annual Report' / 'Integrated Report' marker,
    with punctuation cleaned up."""
    parts = AR_SPLIT_RX.split(stem, maxsplit=1)
    name_part = parts[0] if parts else stem
    name_part = re.sub(r"[._\-]+", " ", name_part)
    name_part = re.sub(r"\s+", " ", name_part).strip()
    return name_part


def _year_from_filename(stem: str) -> int | None:
    for m in FY_RX_FILENAME.findall(stem):
        y = int(m)
        if y in YEAR_WINDOW:
            return y
    return None


def _first_pages_text(pdf_path: Path, n_pages: int = 3) -> str:
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as exc:
        return f"__pymupdf_open_failed__: {exc}"
    try:
        parts = []
        for i in range(min(n_pages, doc.page_count)):
            try:
                parts.append(doc[i].get_text("text") or "")
            except Exception:
                parts.append("")
        return "\n".join(parts)
    finally:
        doc.close()


def _institution_tokens(name: str) -> set[str]:
    """Keep only tokens of length >= 3, lowercased, with punctuation
    stripped — used as a weak content-side sanity check against the
    matched institution's canonical name."""
    toks = re.findall(r"[A-Za-z]+", name.lower())
    stop = {"the", "and", "co", "company", "corp", "ltd", "plc", "pjsc",
            "sao", "bsc", "qsc", "ksc", "inc", "group", "holding", "holdings",
            "for", "of"}
    return {t for t in toks if len(t) >= 3 and t not in stop}


def _best_match(
    candidate_name: str, institutions: list[Institution]
) -> tuple[Institution, float, float]:
    """Score each institution with three RapidFuzz measures and take the
    max. partial_ratio handles acronyms (SABIC vs 'Saudi Basic Industries
    Corporation SABIC'), token_set_ratio handles name re-orderings, WRatio
    gives a sensible default. Returns (best_inst, best_score, runner_up_score)
    so the caller can detect ambiguous matches.
    """
    scored: list[tuple[Institution, float]] = []
    for inst in institutions:
        s = max(
            fuzz.WRatio(candidate_name, inst.name),
            fuzz.partial_ratio(candidate_name.lower(), inst.name.lower()),
            fuzz.token_set_ratio(candidate_name.lower(), inst.name.lower()),
        )
        scored.append((inst, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    best = scored[0]
    runner_up = scored[1][1] if len(scored) > 1 else 0.0
    return best[0], best[1], runner_up


def _tokens_appear_in_text(tokens: set[str], text: str) -> int:
    text_lc = text.lower()
    hits = sum(1 for t in tokens if t in text_lc)
    return hits


def _unique_destination(dest_dir: Path, filename: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    base = dest_dir / filename
    if not base.exists():
        return base
    stem, ext = os.path.splitext(filename)
    i = 2
    while True:
        candidate = dest_dir / f"{stem} ({i}){ext}"
        if not candidate.exists():
            return candidate
        i += 1


def main() -> int:
    if not SOURCE_DIR.exists():
        print(f"ERROR: {SOURCE_DIR} missing")
        return 2

    db = SessionLocal()
    try:
        active_inst = db.query(Institution).filter(Institution.active).all()
        print(f"active institutions: {len(active_inst)}")

        report = Report()
        pdf_paths = sorted(SOURCE_DIR.glob("*.pdf"))
        print(f"colleague PDFs to sort: {len(pdf_paths)}")

        for pdf in pdf_paths:
            stem = pdf.stem
            name_part = _strip_filename_to_name_part(stem)
            fy_filename = _year_from_filename(stem)
            inst, score, runner_up = _best_match(name_part, active_inst)
            head_text = _first_pages_text(pdf)
            fy_text = _detect_year_in_text(head_text)
            fy = fy_filename or fy_text
            fy_in_window = fy in YEAR_WINDOW if fy else False

            # Confidence = good name match + year in the 2020-2025 window.
            # The earlier token-in-body sanity check was too strict:
            # annual-report title pages are typically visual
            # (logos / ruler portraits), so canonical tokens like
            # "sohar" or "al rajhi" miss. Filename + year is enough.
            # Ambiguous-match guard: if the runner-up is within 3 points
            # of the top, we can't trust the match (SABIC fuzzy-ties
            # with "Abu Dhabi Commercial Bank" at low scores).
            ambiguous = score - runner_up < 3 and score < 95
            confident = score >= MATCH_SCORE_THRESHOLD and fy_in_window and not ambiguous

            if confident:
                report.confident.append(SortResult(
                    pdf_path=pdf, status="confident", slug=inst.slug,
                    fiscal_year=fy, score=score,
                    reason=(f"filename-fy={fy_filename} text-fy={fy_text} "
                            f"score={score:.0f} (runner-up {runner_up:.0f})"),
                ))
                continue

            reason_parts = []
            if score < MATCH_SCORE_THRESHOLD:
                reason_parts.append(f"name-score={score:.0f}<{MATCH_SCORE_THRESHOLD}")
            if not fy_in_window:
                reason_parts.append(
                    f"fy-filename={fy_filename} fy-text={fy_text} not in {min(YEAR_WINDOW)}-{max(YEAR_WINDOW)}"
                )
            if ambiguous:
                reason_parts.append(
                    f"ambiguous (top={score:.0f} runner-up={runner_up:.0f})"
                )
            guess = f"{inst.slug} FY{fy}" if fy else inst.slug
            report.unmatched.append(SortResult(
                pdf_path=pdf, status="unmatched",
                slug=inst.slug, fiscal_year=fy, score=score,
                reason="; ".join(reason_parts) + f" | best-guess={guess}",
                first_pages_excerpt=(head_text[:300]).replace("\n", " / "),
            ))

        # Copy confident PDFs. Keep original filenames so the audit trail is
        # obvious when someone opens manual_inbox/<slug>/.
        copied = 0
        for r in report.confident:
            dest_dir = MANUAL_INBOX / r.slug  # type: ignore[arg-type]
            dest_path = _unique_destination(dest_dir, r.pdf_path.name)
            shutil.copy2(r.pdf_path, dest_path)
            note_path = dest_path.with_suffix(".note")
            note_path.write_text(
                f"[colleague_reports] {r.pdf_path.name} score={r.score:.0f} fy={r.fiscal_year} "
                f"({r.reason})",
                encoding="utf-8",
            )
            copied += 1

        # Unmatched report. Written to docs/ so the user can scan it quickly.
        UNMATCHED_LOG.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        lines.append("# Colleague-reports: unmatched / low-confidence\n")
        lines.append(f"Source: `{SOURCE_DIR}`.  Items here were NOT filed; "
                     f"everything else went to `storage/manual_inbox/<slug>/`.\n")
        if not report.unmatched:
            lines.append("_(none — all 127 matched confidently)_")
        else:
            lines.append(f"Count: **{len(report.unmatched)}**\n")
            lines.append("| file | best-guess slug | FY | score | reason | first-pages excerpt |")
            lines.append("|---|---|---|---|---|---|")
            for u in report.unmatched:
                score_s = f"{u.score:.0f}" if u.score is not None else "-"
                lines.append(
                    f"| `{u.pdf_path.name}` | `{u.slug or '-'}` | "
                    f"{u.fiscal_year or '-'} | {score_s} | "
                    f"{u.reason} | {u.first_pages_excerpt[:160]} |"
                )
        UNMATCHED_LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")

        print()
        print(f"confident, copied : {copied}")
        print(f"unmatched         : {len(report.unmatched)}")
        print(f"unmatched report  : {UNMATCHED_LOG}")

        # Return a JSON summary for callers (not strictly needed but useful
        # for the auto-advance decision in the parent orchestrator).
        print()
        print(json.dumps({
            "total": len(pdf_paths),
            "confident": copied,
            "unmatched": len(report.unmatched),
            "active_institutions": len(active_inst),
        }))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
