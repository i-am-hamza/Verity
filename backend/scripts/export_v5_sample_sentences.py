"""Export 20 random kept narrative sentences for 'innovation', 'feedback',
and 'digital services' to docs/term-evidence/v5_sample_sentences.xlsx.

Sampling rules:
  - Seed 42 for reproducibility.
  - At most 2 sentences per company per term.
  - 20 sentences per term drawn across different companies and years.
  - Source: v5 MatchEvidence (pipeline 0.5.0, taxonomy v5).

Output columns:
  term | company | year | sentence | About ESG? | Pillar it fits | Note
"""
from __future__ import annotations

import random
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

TERMS = ["innovation", "feedback", "digital services"]
TARGET_PER_TERM = 20
MAX_PER_COMPANY = 2
SEED = 42
V5_PIPELINE = "0.5.0"

OUT_PATH = BACKEND.parent / "docs" / "term-evidence" / "v5_sample_sentences.xlsx"


def main() -> int:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    import app.models.institution
    import app.models.provenance
    import app.models.report
    import app.models.review
    import app.models.run
    import app.models.score
    import app.models.taxonomy
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.report import Report, ReportStatus
    from app.models.score import MatchEvidence
    from app.models.taxonomy import TaxonomyVersion, Term

    db = SessionLocal()

    tv_v5 = db.query(TaxonomyVersion).filter(TaxonomyVersion.note.like("v5:%")).first()
    if not tv_v5:
        print("ERROR: v5 taxonomy version not found")
        db.close()
        return 1

    # Dedup v5 reports (keep highest id per source_document_id)
    raw_reports = (
        db.query(Report)
        .join(Institution)
        .filter(
            Report.status == ReportStatus.scored,
            Report.pipeline_version == V5_PIPELINE,
            Institution.active.is_(True),
        )
        .order_by(Report.source_document_id, Report.id)
        .all()
    )
    deduped: dict[int, Report] = {}
    for r in raw_reports:
        if r.source_document_id:
            deduped[r.source_document_id] = r  # keeps last (highest id)
    v5_reports = list(deduped.values())
    rid_to_report: dict[int, Report] = {r.id: r for r in v5_reports}
    v5_report_ids = list(rid_to_report)

    inst_map: dict[int, Institution] = {
        i.id: i for i in db.query(Institution).filter(Institution.active.is_(True)).all()
    }

    # phrase -> term_id
    all_terms = db.query(Term).all()
    phrase_to_tid: dict[str, int] = {t.phrase: t.id for t in all_terms}

    rng = random.Random(SEED)

    rows: list[dict] = []

    for term_phrase in TERMS:
        tid = phrase_to_tid.get(term_phrase)
        if tid is None:
            print(f"WARNING: phrase '{term_phrase}' not found in taxonomy")
            continue

        # Load all MatchEvidence rows for this term in v5 reports
        me_rows = (
            db.query(MatchEvidence)
            .filter(
                MatchEvidence.pipeline_version == V5_PIPELINE,
                MatchEvidence.taxonomy_version_id == tv_v5.id,
                MatchEvidence.term_id == tid,
                MatchEvidence.report_id.in_(v5_report_ids),
            )
            .all()
        )

        # Group by (institution_id, fiscal_year) to enforce the per-company cap
        by_company_year: dict[tuple[int, int], list[MatchEvidence]] = defaultdict(list)
        for me in me_rows:
            rep = rid_to_report.get(me.report_id)
            if rep is None:
                continue
            key = (rep.institution_id, rep.fiscal_year)
            by_company_year[key].append(me)

        # Shuffle within each (company, year), then pick up to MAX_PER_COMPANY
        pool: list[tuple[str, int, int, str]] = []  # (slug, year, page, sentence)
        for (iid, fy), mes in by_company_year.items():
            rng.shuffle(mes)
            selected = mes[:MAX_PER_COMPANY]
            slug = inst_map[iid].slug if iid in inst_map else str(iid)
            for me in selected:
                pool.append((slug, fy, me.page_number, me.sentence_text))

        # Shuffle the full pool and draw TARGET_PER_TERM sentences, preferring spread
        rng.shuffle(pool)

        # Spread across companies: round-robin by company until we have enough
        by_slug: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
        for slug, fy, pg, sent in pool:
            by_slug[slug].append((fy, pg, sent))

        slugs = list(by_slug)
        rng.shuffle(slugs)

        sample: list[tuple[str, int, int, str]] = []
        slug_cycle = list(slugs)
        while len(sample) < TARGET_PER_TERM and slug_cycle:
            next_cycle: list[str] = []
            for s in slug_cycle:
                if len(sample) >= TARGET_PER_TERM:
                    break
                if by_slug[s]:
                    fy, pg, sent = by_slug[s].pop(0)
                    sample.append((s, fy, pg, sent))
                if by_slug[s]:
                    next_cycle.append(s)
            slug_cycle = next_cycle

        if len(sample) < TARGET_PER_TERM:
            print(f"  WARNING: only {len(sample)} sentences available for '{term_phrase}' "
                  f"(fewer than {TARGET_PER_TERM})")

        for slug, fy, _pg, sent in sample:
            rows.append({
                "term": term_phrase,
                "company": slug,
                "year": fy,
                "sentence": sent.strip(),
                "About ESG?": "",
                "Pillar it fits": "",
                "Note": "",
            })

    db.close()

    # ------------------------------------------------------------------
    # Write Excel
    # ------------------------------------------------------------------
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sample sentences"

    headers = ["term", "company", "year", "sentence", "About ESG?", "Pillar it fits", "Note"]
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F497D")

    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for row_idx, row in enumerate(rows, start=2):
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=row[h])
            cell.alignment = Alignment(vertical="top", wrap_text=(h == "sentence"))

    # Column widths
    col_widths = {
        "term": 20,
        "company": 42,
        "year": 7,
        "sentence": 90,
        "About ESG?": 14,
        "Pillar it fits": 16,
        "Note": 24,
    }
    for col_idx, h in enumerate(headers, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = col_widths.get(h, 20)

    ws.freeze_panes = "A2"
    wb.save(OUT_PATH)
    print(f"Written {len(rows)} rows to {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
