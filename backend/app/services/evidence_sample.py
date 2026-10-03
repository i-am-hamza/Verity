"""Face-validity sample: write exports/evidence_sample.csv with up to N
random MatchEvidence rows per pillar (seeded, reproducible). Leaves a
reviewer_verdict column empty so the supervisor can mark each row
valid / false_positive / unsure.
"""
from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.models.report import Report
from app.models.score import MatchEvidence
from app.models.taxonomy import Category, Term
from app.services.verity_config import load_verity_config


@dataclass
class ExportResult:
    path: Path
    per_pillar_available: dict[str, int]
    per_pillar_sampled: dict[str, int]


def export_evidence_sample(db: Session, out_path: Path | None = None) -> ExportResult:
    cfg = load_verity_config()
    out = out_path or (Path(__file__).resolve().parents[3] / "exports" / "evidence_sample.csv")

    # Join MatchEvidence → Term → Category to filter / group by pillar.
    rows = (
        db.query(MatchEvidence, Term, Category, Report, Institution)
        .join(Term, Term.id == MatchEvidence.term_id)
        .join(Category, Category.id == Term.category_id)
        .join(Report, Report.id == MatchEvidence.report_id)
        .join(Institution, Institution.id == Report.institution_id)
        .all()
    )

    by_pillar: dict[str, list[tuple]] = {}
    for me, term, cat, report, inst in rows:
        by_pillar.setdefault(cat.pillar, []).append(
            (inst.slug, report.fiscal_year, me.page_number, term.phrase,
             cat.name, cat.pillar, me.sentence_text)
        )

    rng = random.Random(cfg.evidence_sample_seed)
    picked: list[tuple] = []
    per_pillar_available: dict[str, int] = {}
    per_pillar_sampled: dict[str, int] = {}
    for pillar, items in sorted(by_pillar.items()):
        per_pillar_available[pillar] = len(items)
        if len(items) <= cfg.evidence_sample_per_pillar:
            picked.extend(items)
            per_pillar_sampled[pillar] = len(items)
        else:
            sampled = rng.sample(items, cfg.evidence_sample_per_pillar)
            picked.extend(sampled)
            per_pillar_sampled[pillar] = cfg.evidence_sample_per_pillar

    # Deterministic row order within file (seed + sorted picks for stable diff).
    picked.sort(key=lambda t: (t[5], t[0], t[1], t[2], t[3]))

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([
            "institution_slug", "fiscal_year", "page", "term",
            "category", "pillar", "sentence", "reviewer_verdict",
        ])
        for row in picked:
            w.writerow([*row, ""])

    return ExportResult(path=out, per_pillar_available=per_pillar_available,
                        per_pillar_sampled=per_pillar_sampled)


__all__ = ["ExportResult", "export_evidence_sample"]
