"""Session 7 provenance audit.

For each source_document: file exists, sha256 matches, URL + retrieved_at
non-null. For each scored Report: linked to a source_document. For each
MatchEvidence: linked to a Report, page_number in [1, report.page_count].

Prints a human-readable report and exits 0 iff zero violations.
"""
from __future__ import annotations

import hashlib
import os
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.stdout.reconfigure(encoding="utf-8")

from app.crawler import register_all_mappers  # noqa: E402

register_all_mappers()

from app.database import SessionLocal  # noqa: E402
from app.models.institution import Institution  # noqa: E402
from app.models.provenance import SourceDocument  # noqa: E402
from app.models.report import Report  # noqa: E402
from app.models.score import MatchEvidence  # noqa: E402


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    db = SessionLocal()
    violations: dict[str, list[str]] = defaultdict(list)
    try:
        print("=== provenance audit ===")
        sds = db.query(SourceDocument).all()
        print(f"source_documents checked: {len(sds)}")
        sha_mismatch = 0
        missing_file = 0
        missing_url = 0
        missing_retrieved = 0
        for sd in sds:
            if not sd.source_url:
                violations["missing_source_url"].append(f"sd_id={sd.id}")
                missing_url += 1
            if not sd.retrieved_at:
                violations["missing_retrieved_at"].append(f"sd_id={sd.id}")
                missing_retrieved += 1
            if not sd.file_path or not os.path.exists(sd.file_path):
                violations["missing_file"].append(
                    f"sd_id={sd.id} path={sd.file_path!r}"
                )
                missing_file += 1
                continue
            actual = _sha256(sd.file_path)
            if actual != sd.sha256:
                violations["sha256_mismatch"].append(
                    f"sd_id={sd.id} stored={sd.sha256[:12]} actual={actual[:12]}"
                )
                sha_mismatch += 1

        print(f"  missing source_url     : {missing_url}")
        print(f"  missing retrieved_at   : {missing_retrieved}")
        print(f"  missing file on disk   : {missing_file}")
        print(f"  sha256 mismatch        : {sha_mismatch}")

        reports = db.query(Report).all()
        print(f"\nreports checked: {len(reports)}")
        no_sd = 0
        for r in reports:
            if r.source_document_id is None:
                violations["report_no_source_document"].append(
                    f"report_id={r.id} fiscal_year={r.fiscal_year}"
                )
                no_sd += 1
        print(f"  reports with no source_document_id : {no_sd}")

        evidence = db.query(MatchEvidence, Report).join(
            Report, Report.id == MatchEvidence.report_id,
            isouter=True,
        ).all()
        print(f"\nmatch_evidence rows checked: {len(evidence)}")
        orphan_evidence = 0
        bad_page = 0
        for me, rpt in evidence:
            if rpt is None:
                violations["evidence_no_report"].append(f"evidence_id={me.id}")
                orphan_evidence += 1
                continue
            pg = me.page_number
            if pg < 1 or (rpt.page_count and pg > rpt.page_count):
                violations["evidence_bad_page"].append(
                    f"evidence_id={me.id} page={pg} report_pages={rpt.page_count}"
                )
                bad_page += 1
        print(f"  orphan evidence (no report)   : {orphan_evidence}")
        print(f"  page_number out of range      : {bad_page}")

        total = sum(len(v) for v in violations.values())
        print()
        print(f"total violations: {total}")
        if violations:
            for cat, items in violations.items():
                print(f"\n[{cat}]  n={len(items)}")
                for item in items[:10]:
                    print(f"  - {item}")
                if len(items) > 10:
                    print(f"  ... and {len(items) - 10} more")
        _ = Institution  # keep import referenced
        return 0 if total == 0 else 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
