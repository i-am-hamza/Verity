"""Re-score Al Rajhi Bank FY2023 with the shipped scoring code and prove the
result equals the live database values. No DB rows are written: we run the
CPU-side pipeline (`_run_pipeline_cpu`) only.

Prints a side-by-side comparison of
  E_density, S_density, G_density, General_density, Addon_density,
  narrative_word_count, matches_count
and exits non-zero on any mismatch beyond 1e-5 (floating-point tolerance).
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

TARGET_SLUG = "al-rajhi-bank"
TARGET_FY = 2023
TARGET_PIPELINE_VERSION = "0.6.0"


def main() -> int:
    import app.models.company_year  # noqa: F401
    import app.models.institution   # noqa: F401
    import app.models.provenance    # noqa: F401
    import app.models.report        # noqa: F401
    import app.models.review        # noqa: F401
    import app.models.run           # noqa: F401
    import app.models.score         # noqa: F401
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.report import Report
    from app.models.taxonomy import Category, Term
    from app.services.pipeline import PIPELINE_VERSION, _run_pipeline_cpu, build_terms_payload
    from app.services.verity_config import load_verity_config

    assert PIPELINE_VERSION == TARGET_PIPELINE_VERSION, (
        f"shipped pipeline is {PIPELINE_VERSION}, expected {TARGET_PIPELINE_VERSION}"
    )

    db = SessionLocal()
    inst = db.query(Institution).filter(Institution.slug == TARGET_SLUG).first()
    assert inst, f"institution '{TARGET_SLUG}' not found"

    rep = (
        db.query(Report)
        .filter(
            Report.institution_id == inst.id,
            Report.fiscal_year == TARGET_FY,
            Report.pipeline_version == PIPELINE_VERSION,
            Report.status == "scored",
        )
        .order_by(Report.id.desc())
        .first()
    )
    assert rep, f"no scored report at pipeline={PIPELINE_VERSION} for {TARGET_SLUG} FY{TARGET_FY}"

    print(f"Target report row:")
    print(f"  Institution      : {inst.slug}  id={inst.id}  SASB={inst.sasb_industry!r}  "
          f"is_financial={inst.is_financial}")
    print(f"  Report.id        : {rep.id}  fiscal_year={rep.fiscal_year}  "
          f"pipeline={rep.pipeline_version}")
    print(f"  file_path        : {rep.file_path}")
    print(f"  source_document  : {rep.source_document_id}")
    print()

    cfg = load_verity_config()
    terms = db.query(Term).all()
    categories = db.query(Category).all()
    payload = build_terms_payload(terms, categories, sasb_industry=inst.sasb_industry)

    print(f"Running shipped pipeline (_run_pipeline_cpu) against {rep.file_path} …")
    worker = _run_pipeline_cpu(
        source_document_id=rep.source_document_id or 0,
        file_path=rep.file_path,
        terms_payload=payload,
        cfg=cfg,
        is_financial=bool(inst.is_financial),
    )

    if worker.status != "scored":
        print(f"WORKER STATUS: {worker.status}  error={worker.error_message!r}")
        db.close()
        return 2

    def diff(a: float | None, b: float | None, tol: float = 1e-5) -> str:
        if a is None and b is None:
            return "OK"
        if a is None or b is None:
            return "MISMATCH"
        d = abs(a - b)
        return f"OK (|delta|={d:.2e})" if d <= tol else f"MISMATCH (|delta|={d:.2e})"

    comparisons: list[tuple[str, float | int | None, float | int | None]] = [
        ("narrative_word_count", worker.narrative_word_count, rep.narrative_word_count),
        ("matches_count       ", worker.matches_count,        rep.matches_count),
        ("e_density           ", worker.e_density,            rep.e_density),
        ("s_density           ", worker.s_density,            rep.s_density),
        ("g_density           ", worker.g_density,            rep.g_density),
        ("general_density     ", worker.general_density,      rep.general_density),
        ("addon_density       ", worker.addon_density,        rep.addon_density),
    ]

    print(f"{'field':<22} {'re-score':>14}   {'database':>14}   check")
    print("-" * 70)
    all_ok = True
    for name, got, want in comparisons:
        status = diff(got, want)
        if "MISMATCH" in status:
            all_ok = False
        got_s = f"{got}" if not isinstance(got, float) else f"{got:.6f}"
        want_s = f"{want}" if not isinstance(want, float) else f"{want:.6f}"
        print(f"{name} {got_s:>14}   {want_s:>14}   {status}")
    print("-" * 70)

    # Composite scores (e/s/g/general_score and composite_score) are produced
    # by compute_ranks.py from the full 390-report pool and therefore can't be
    # reproduced from a single re-score. The density numerators above (E, S, G,
    # General, Add-on) are what the shipped Python code produces per-report;
    # if they match, the composite that compute_ranks.py would derive from them
    # also matches (same inputs, same deterministic ranking).
    print()
    print(f"Database per-report rank scores (produced by compute_ranks.py):")
    print(f"  e_score={rep.e_score}  s_score={rep.s_score}  g_score={rep.g_score}  "
          f"general_score={rep.general_score}")
    print(f"  composite_score={rep.composite_score}  "
          f"composite_3pillar={rep.composite_3pillar}  "
          f"composite_general_no_new3={rep.composite_general_no_new3}  "
          f"addon_rank={rep.addon_rank}")
    print()
    print("ALL DENSITIES IDENTICAL" if all_ok else "DENSITY MISMATCH DETECTED")
    db.close()
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
