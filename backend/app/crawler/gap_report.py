"""Write docs/GAP_REPORT.md after a crawl run.

Columns: institution x fiscal_year matrix with cell content indicating
source (crawler/exchange/wayback/manual) or the reason it's blank.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.crawler.config import GAP_REPORT_PATH
from app.models.institution import Institution
from app.models.provenance import Gap, SourceDocument


def write_gap_report(db: Session, *, target_years: list[int], only_slugs: list[str] | None = None) -> Path:
    years = sorted(target_years)

    inst_q = db.query(Institution).order_by(Institution.wave.desc(), Institution.rank.asc())
    if only_slugs:
        inst_q = inst_q.filter(Institution.slug.in_(only_slugs))
    institutions = inst_q.all()

    # Keyed by (institution_id, fiscal_year) → source doc (latest wins if several).
    docs = db.query(SourceDocument).all()
    docs_by_key: dict[tuple[int, int], SourceDocument] = {}
    for d in docs:
        docs_by_key[(d.institution_id, d.fiscal_year)] = d

    gaps = db.query(Gap).all()
    gaps_by_key: dict[tuple[int, int], Gap] = {(g.institution_id, g.fiscal_year): g for g in gaps}

    lines: list[str] = []
    lines.append("# Gap report")
    lines.append("")
    lines.append("Matrix: institution x fiscal year. A filled cell shows the "
                 "`source` that produced the file (`crawler` = IR page, `exchange` = "
                 "listing exchange page, `wayback` = Wayback Machine capture via the "
                 "approved-ingest flow, `manual` = human-dropped file). A dash is a "
                 "gap — see the Gaps section below for the reason and next-tier action.")
    lines.append("")
    lines.append("## Coverage matrix")
    lines.append("")
    header = "| institution |" + "".join(f" FY{y} |" for y in years)
    sep = "|---|" + "---|" * len(years)
    lines.append(header)
    lines.append(sep)
    source_label = {
        "crawler": "crawler",
        "exchange": "exchange",
        "wayback": "wayback",
        "manual": "manual",
    }
    for inst in institutions:
        cells: list[str] = []
        for y in years:
            doc = docs_by_key.get((inst.id, y))
            if doc is None:
                cells.append("—")
            else:
                marker = source_label.get(doc.source.value, doc.source.value)
                if doc.review_status.value != "auto_ok":
                    marker = f"{marker} ⚠"
                cells.append(marker)
        lines.append(f"| `{inst.slug}` | " + " | ".join(cells) + " |")

    # Gap table.
    lines.append("")
    lines.append("## Gaps (institution x FY) and next-tier recommendation")
    lines.append("")
    lines.append("| institution | FY | reason | tier_tried | next_action |")
    lines.append("|---|---|---|---|---|")
    for (iid, y), g in sorted(gaps_by_key.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        gap_inst = next((i for i in institutions if i.id == iid), None)
        if gap_inst is None:
            continue
        if only_slugs and gap_inst.slug not in only_slugs:
            continue
        next_action = (g.next_action or "").replace("\n", " ")
        lines.append(f"| `{gap_inst.slug}` | {y} | {g.reason.value} | {g.tier_tried or ''} | {next_action} |")

    GAP_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    GAP_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return GAP_REPORT_PATH
