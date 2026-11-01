"""Verify docs/scoring_code/ copies are byte-identical to production.

Prints the sha256 for every pair and exits non-zero on any mismatch.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

PAIRS: list[tuple[str, str]] = [
    ("backend/app/services/pdf_extraction.py",
     "docs/scoring_code/backend/app/services/pdf_extraction.py"),
    ("backend/app/services/text_quality.py",
     "docs/scoring_code/backend/app/services/text_quality.py"),
    ("backend/app/services/text_processing.py",
     "docs/scoring_code/backend/app/services/text_processing.py"),
    ("backend/app/services/matcher.py",
     "docs/scoring_code/backend/app/services/matcher.py"),
    ("backend/app/services/sasb_materiality.py",
     "docs/scoring_code/backend/app/services/sasb_materiality.py"),
    ("backend/app/services/scoring.py",
     "docs/scoring_code/backend/app/services/scoring.py"),
    ("backend/app/services/pipeline.py",
     "docs/scoring_code/backend/app/services/pipeline.py"),
    ("backend/app/services/verity_config.py",
     "docs/scoring_code/backend/app/services/verity_config.py"),
    ("backend/app/services/taxonomy_hash.py",
     "docs/scoring_code/backend/app/services/taxonomy_hash.py"),
    ("backend/app/models/taxonomy.py",
     "docs/scoring_code/backend/app/models/taxonomy.py"),
    ("backend/app/models/score.py",
     "docs/scoring_code/backend/app/models/score.py"),
    ("backend/app/models/report.py",
     "docs/scoring_code/backend/app/models/report.py"),
    ("backend/app/config.py",
     "docs/scoring_code/backend/app/config.py"),
    ("backend/scripts/compute_ranks.py",
     "docs/scoring_code/backend/scripts/compute_ranks.py"),
    ("backend/scripts/seed_taxonomy_v6.py",
     "docs/scoring_code/backend/scripts/seed_taxonomy_v6.py"),
    ("config/verity.toml",
     "docs/scoring_code/config/verity.toml"),
]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    all_ok = True
    print(f"{'file':<60}  {'sha256':<64}  status")
    print("-" * 140)
    for src_rel, dst_rel in PAIRS:
        src = REPO / src_rel
        dst = REPO / dst_rel
        src_h = sha256_of(src)
        dst_h = sha256_of(dst)
        ok = src_h == dst_h
        all_ok = all_ok and ok
        marker = "OK " if ok else "MISMATCH"
        print(f"{dst_rel:<60}  {dst_h}  {marker}")
        if not ok:
            print(f"  source: {src_rel}  {src_h}")
    print("-" * 140)
    print(f"{'ALL IDENTICAL' if all_ok else 'MISMATCH DETECTED'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
