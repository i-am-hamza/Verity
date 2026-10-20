"""Check how many v5 reports are in DB and identify any missing ones."""
from __future__ import annotations
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv
load_dotenv(BACKEND / ".env")


def main() -> None:
    import app.models.institution
    import app.models.provenance
    import app.models.report
    import app.models.review
    import app.models.run
    import app.models.score
    import app.models.taxonomy
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.provenance import ReviewStatus, SourceDocument
    from app.models.report import Report, ReportStatus

    db = SessionLocal()

    v5 = (
        db.query(Report)
        .filter(Report.pipeline_version == "0.5.0", Report.status == ReportStatus.scored)
        .all()
    )
    print(f"v5 scored reports in DB: {len(v5)}")
    v5_sdids = {r.source_document_id for r in v5}
    print(f"distinct source_doc_ids: {len(v5_sdids)}")

    all_sd = (
        db.query(SourceDocument)
        .join(Institution)
        .filter(
            Institution.active.is_(True),
            SourceDocument.review_status == ReviewStatus.auto_ok,
            SourceDocument.superseded_by_id.is_(None),
        )
        .all()
    )
    print(f"total eligible source_documents: {len(all_sd)}")

    all_sdids = {sd.id for sd in all_sd}
    missing_sdids = all_sdids - v5_sdids
    print(f"missing from v5: {len(missing_sdids)}")
    if missing_sdids:
        inst_map = {i.id: i for i in db.query(Institution).filter(Institution.active.is_(True)).all()}
        missing_sds = [sd for sd in all_sd if sd.id in missing_sdids]
        for sd in sorted(missing_sds, key=lambda x: x.id):
            inst = inst_map.get(sd.institution_id)
            slug = inst.slug if inst else str(sd.institution_id)
            print(f"  sd_id={sd.id}  {slug}  FY{sd.fiscal_year}")

    db.close()


if __name__ == "__main__":
    main()
