"""
Pull 25 random matches for a report and dump them so a human can judge each
one as true topical mention or false positive.

Reads from the SQLite DB the API/pipeline wrote to (report_id passed on the
command line). Deterministic under a seed so re-runs stay comparable.
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal  # noqa: E402
from app.models import institution, report, score, taxonomy  # noqa: E402, F401 — register mappers
from app.models.score import MatchEvidence  # noqa: E402
from app.models.taxonomy import Term  # noqa: E402


def main(report_id: int, seed: int, n: int) -> int:
    db = SessionLocal()
    try:
        all_matches = db.query(MatchEvidence).filter(MatchEvidence.report_id == report_id).all()
        if not all_matches:
            print(f"No matches for report {report_id}")
            return 1

        rng = random.Random(seed)
        picks = rng.sample(all_matches, k=min(n, len(all_matches)))

        term_cache: dict[int, str] = {}

        def term_phrase(term_id: int) -> str:
            if term_id not in term_cache:
                t = db.get(Term, term_id)
                term_cache[term_id] = t.phrase if t else "?"
            return term_cache[term_id]

        print(f"Total matches in report {report_id}: {len(all_matches)}")
        print(f"Sampling {len(picks)} at random (seed={seed}).")
        print()

        for i, m in enumerate(picks, start=1):
            print(f"[{i:02d}] term={term_phrase(m.term_id)!r}  page={m.page_number}")
            print(f"     {m.sentence_text.strip()}")
            print()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-id", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n", type=int, default=25)
    args = parser.parse_args()
    sys.exit(main(args.report_id, args.seed, args.n))
