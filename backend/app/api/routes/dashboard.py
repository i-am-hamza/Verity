"""Session 7 dashboard endpoints.

Dedicated router (`/dashboard/*`) so the UI can get exactly the shapes it
needs without churning the legacy `/scores/*`, `/institutions/*` endpoints
that upload tooling still uses. Everything here is read-only reporting
against the DB plus the frozen Session 6 sensitivity artefacts; nothing
mutates taxonomy or reprocesses.
"""
from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.institution import Institution
from app.models.provenance import Gap, SourceDocument
from app.models.report import Report, ReportStatus
from app.models.score import CategoryScore, MatchEvidence
from app.models.taxonomy import Category, TaxonomyVersion, Term
from app.schemas.dashboard import (
    CoverageCell,
    CoverageOut,
    CoverageRow,
    EvidenceOut,
    EvidenceRow,
    InstitutionDetail,
    LeaderboardMeta,
    LeaderboardOut,
    LeaderboardRow,
    PrecisionCell,
    ReportRow,
    ReviewSubmit,
    SensitivityInstitutionRow,
    SensitivityOut,
    TaxonomyCategoryView,
    TaxonomyTermView,
    TaxonomyVersionView,
)
from app.services.pipeline import PIPELINE_VERSION

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

REPO_ROOT = Path(__file__).resolve().parents[4]
SENSITIVITY_CSV = REPO_ROOT / "exports" / "sensitivity_summary.csv"
SENSITIVITY_MD = REPO_ROOT / "docs" / "SENSITIVITY_SUMMARY.md"
METHODOLOGY_MD = REPO_ROOT / "docs" / "METHODOLOGY.md"

# Keep the Rabigh artifact table in one place; mirrors scripts/build_leaderboard.py
# and docs/DECISIONS.md 2026-10-02.
KNOWN_ARTIFACTS: dict[str, tuple[int | None, str, str]] = {
    "rabigh-refining-petrochemical-co": (
        2020,
        "sentence_segmentation_artifact",
        "Sentence segmentation failed on this PDF's layout; score does not "
        "reflect actual disclosure content. See DECISIONS.md 2026-10-02.",
    ),
}


def _artifact_tag(slug: str, fy: int | None = None) -> tuple[str, str]:
    row = KNOWN_ARTIFACTS.get(slug)
    if row is None:
        return "", ""
    flag_year, tag, reason = row
    if flag_year is None or fy is None or fy == flag_year:
        return tag, reason
    return "", ""


def _latest_tv(db: Session) -> TaxonomyVersion:
    tv = (
        db.query(TaxonomyVersion)
        .order_by(TaxonomyVersion.created_at.desc(), TaxonomyVersion.id.desc())
        .first()
    )
    if tv is None:
        raise HTTPException(status_code=503, detail="No taxonomy registered yet")
    return tv


def _meta(db: Session) -> LeaderboardMeta:
    tv = _latest_tv(db)
    active = db.query(Institution).filter(Institution.active).count()
    scored_insts = (
        db.query(Report.institution_id)
        .filter(
            Report.pipeline_version == PIPELINE_VERSION,
            Report.status == ReportStatus.scored,
            Report.e_score.isnot(None),
        )
        .distinct()
        .count()
    )
    scored_reports = (
        db.query(Report.id)
        .filter(
            Report.pipeline_version == PIPELINE_VERSION,
            Report.status == ReportStatus.scored,
            Report.e_score.isnot(None),
        )
        .count()
    )
    return LeaderboardMeta(
        taxonomy_version=tv.hash,
        pipeline_version=PIPELINE_VERSION,
        data_snapshot_date=datetime.now(UTC).strftime("%Y-%m-%d"),
        scored_institutions=scored_insts,
        active_institutions=active,
        scored_reports=scored_reports,
    )


def _report_pillar_densities(
    db: Session, report_id: int, tv_id: int
) -> dict[str, float]:
    out: dict[str, float] = {"Environmental": 0.0, "Social": 0.0, "Governance": 0.0}
    rows = (
        db.query(CategoryScore, Category)
        .join(Category, Category.id == CategoryScore.category_id)
        .filter(
            CategoryScore.report_id == report_id,
            CategoryScore.taxonomy_version_id == tv_id,
        )
        .all()
    )
    for cs, cat in rows:
        out[cat.pillar] = out.get(cat.pillar, 0.0) + cs.density_per_1000_words * cat.weight
    return {k: round(v, 3) for k, v in out.items()}


@router.get("/meta", response_model=LeaderboardMeta)
def get_meta(db: Session = Depends(get_db)) -> LeaderboardMeta:
    return _meta(db)


@router.get("/leaderboard", response_model=LeaderboardOut)
def get_leaderboard(
    cohort: str = Query("All", description="All | Financial | Non-financial | <industry>"),
    country: str | None = Query(None),
    fy: int | None = Query(None, description="If set, show that single-year composite instead of mean"),
    db: Session = Depends(get_db),
) -> LeaderboardOut:
    # Pull every scored report under the current pipeline version.
    # E, S, G and composite are the 0-10 rank-normalised scores set by
    # compute_ranks.py — headline numbers must all be on the same scale.
    rows = (
        db.query(Report, Institution)
        .join(Institution, Institution.id == Report.institution_id)
        .filter(
            Report.pipeline_version == PIPELINE_VERSION,
            Report.status == ReportStatus.scored,
            Institution.active,
            Report.e_score.isnot(None),
        )
        .all()
    )
    per_inst_year: dict[int, dict[int, Report]] = defaultdict(dict)
    per_inst_meta: dict[int, Institution] = {}
    for report, inst in rows:
        per_inst_meta[inst.id] = inst
        per_inst_year[inst.id][report.fiscal_year] = report

    def _pillar_vec(iid: int) -> tuple[float, float, float, float]:
        """Return (env, soc, gov, composite) as 0-10 scores based on `fy` filter."""
        if fy is not None:
            r = per_inst_year.get(iid, {}).get(fy)
            if r is None:
                return (0.0, 0.0, 0.0, 0.0)
            return (
                round(r.e_score or 0.0, 3),
                round(r.s_score or 0.0, 3),
                round(r.g_score or 0.0, 3),
                round(r.composite_score or 0.0, 3),
            )
        # mean across years
        years = sorted(per_inst_year.get(iid, {}).keys())
        if not years:
            return (0.0, 0.0, 0.0, 0.0)
        e = sum((per_inst_year[iid][y].e_score or 0.0) for y in years) / len(years)
        s = sum((per_inst_year[iid][y].s_score or 0.0) for y in years) / len(years)
        g = sum((per_inst_year[iid][y].g_score or 0.0) for y in years) / len(years)
        comp = sum((per_inst_year[iid][y].composite_score or 0.0) for y in years) / len(years)
        return (round(e, 3), round(s, 3), round(g, 3), round(comp, 3))

    # Build rows pre-filter so ranks are computed across the whole cohort.
    all_rows: list[LeaderboardRow] = []
    for iid, inst in per_inst_meta.items():
        if fy is not None and fy not in per_inst_year.get(iid, {}):
            continue
        e, s, g, comp = _pillar_vec(iid)
        tag, reason = _artifact_tag(inst.slug)
        years_cov = sorted(per_inst_year.get(iid, {}).keys())
        all_rows.append(LeaderboardRow(
            institution_id=iid, slug=inst.slug, name=inst.name,
            country=inst.country,
            sector="financial" if inst.is_financial else "non-financial",
            industry=inst.industry,
            rank_overall=0, rank_within_sector=0,
            mean_composite=comp, env=e, soc=s, gov=g,
            years_covered=years_cov,
            data_quality_flag=tag, data_quality_reason=reason,
        ))

    # Ranks (overall + within sector) computed before filtering so UI
    # filter changes don't renumber anyone — the leaderboard rank is a
    # stable property of the dataset, not of the user's current view.
    all_rows.sort(key=lambda r: -r.mean_composite)
    for i, row in enumerate(all_rows, 1):
        row.rank_overall = i
    fin_sorted = sorted(
        (r for r in all_rows if r.sector == "financial"),
        key=lambda r: -r.mean_composite,
    )
    for i, row in enumerate(fin_sorted, 1):
        row.rank_within_sector = i
    nf_sorted = sorted(
        (r for r in all_rows if r.sector == "non-financial"),
        key=lambda r: -r.mean_composite,
    )
    for i, row in enumerate(nf_sorted, 1):
        row.rank_within_sector = i

    # Apply cohort + country filters AFTER rank assignment.
    def _match_cohort(row: LeaderboardRow) -> bool:
        if cohort in ("All", "all", ""):
            return True
        if cohort.lower() == "financial":
            return row.sector == "financial"
        if cohort.lower() in ("non-financial", "other", "nonfinancial"):
            return row.sector == "non-financial"
        return (row.industry or "").lower() == cohort.lower()

    filtered = [r for r in all_rows if _match_cohort(r)]
    if country:
        filtered = [r for r in filtered if r.country.lower() == country.lower()]

    return LeaderboardOut(meta=_meta(db), rows=filtered)


@router.get("/institutions/{slug}", response_model=InstitutionDetail)
def get_institution_detail(
    slug: str, db: Session = Depends(get_db)
) -> InstitutionDetail:
    inst = db.query(Institution).filter(Institution.slug == slug).one_or_none()
    if inst is None:
        raise HTTPException(status_code=404, detail=f"Institution {slug!r} not found")
    tv = _latest_tv(db)
    reports = (
        db.query(Report)
        .filter(
            Report.institution_id == inst.id,
            Report.pipeline_version == PIPELINE_VERSION,
            Report.status == ReportStatus.scored,
            Report.e_score.isnot(None),
        )
        .order_by(Report.fiscal_year)
        .all()
    )
    sds_by_sha = {
        sd.sha256: sd
        for sd in db.query(SourceDocument)
        .filter(SourceDocument.institution_id == inst.id).all()
    }
    report_rows: list[ReportRow] = []
    category_breakdown: dict[str, dict[str, float]] = {}
    for r in reports:
        pillar_d = _report_pillar_densities(db, r.id, tv.id)
        sd = None
        if r.source_document_id:
            sd = db.get(SourceDocument, r.source_document_id)
        sha_prefix = ""
        source = "manual"
        source_url = ""
        retrieved = ""
        rs = "auto_ok"
        if sd is not None:
            sha_prefix = (sd.sha256 or "")[:12]
            source = sd.source.value if sd.source else "manual"
            source_url = sd.source_url or ""
            retrieved = sd.retrieved_at.isoformat() if sd.retrieved_at else ""
            rs = sd.review_status.value if sd.review_status else "auto_ok"
        _unused_sds_by_sha = sds_by_sha  # legacy lookup kept bound
        report_rows.append(ReportRow(
            report_id=r.id, fiscal_year=r.fiscal_year,
            source=source, source_url=source_url,
            retrieved_at=retrieved, sha256_prefix=sha_prefix,
            review_status=rs,
            processing_review_status=r.processing_review_status or "auto_ok",
            page_count=r.page_count or 0,
            composite_score=round(r.composite_score or 0.0, 3),
            e_score=round(r.e_score or 0.0, 3),
            s_score=round(r.s_score or 0.0, 3),
            g_score=round(r.g_score or 0.0, 3),
            env=pillar_d.get("Environmental", 0.0),
            soc=pillar_d.get("Social", 0.0),
            gov=pillar_d.get("Governance", 0.0),
        ))
        # Category breakdown per year
        cs_rows = (
            db.query(CategoryScore, Category)
            .join(Category, Category.id == CategoryScore.category_id)
            .filter(
                CategoryScore.report_id == r.id,
                CategoryScore.taxonomy_version_id == tv.id,
            )
            .all()
        )
        year_bd: dict[str, float] = {}
        for cs, cat in cs_rows:
            year_bd[cat.name] = round(cs.density_per_1000_words, 3)
        category_breakdown[str(r.fiscal_year)] = year_bd

    tag, reason = _artifact_tag(inst.slug)
    return InstitutionDetail(
        institution_id=inst.id, slug=inst.slug, name=inst.name,
        country=inst.country,
        sector="financial" if inst.is_financial else "non-financial",
        industry=inst.industry,
        ticker=inst.ticker,
        market_cap_usd=inst.market_cap_usd,
        market_cap_date=inst.market_cap_date.isoformat() if inst.market_cap_date else None,
        data_quality_flag=tag, data_quality_reason=reason,
        years_covered=sorted(r.fiscal_year for r in reports),
        reports=report_rows, category_breakdown=category_breakdown,
    )


# ---------------------------- coverage matrix -----------------------------


@router.get("/coverage", response_model=CoverageOut)
def get_coverage(db: Session = Depends(get_db)) -> CoverageOut:
    fys = [2020, 2021, 2022, 2023, 2024, 2025]
    insts = (
        db.query(Institution)
        .filter(Institution.active)
        .order_by(Institution.rank)
        .all()
    )
    # Scored reports for the matrix — current pipeline version only so each
    # (institution, fiscal_year) appears exactly once.
    scored_rows = (
        db.query(Report, Institution, SourceDocument)
        .join(Institution, Institution.id == Report.institution_id)
        .outerjoin(SourceDocument, SourceDocument.id == Report.source_document_id)
        .filter(
            Report.pipeline_version == PIPELINE_VERSION,
            Report.status == ReportStatus.scored,
        )
        .all()
    )
    scored_by_key: dict[tuple[int, int], tuple[Report, SourceDocument | None]] = {}
    for r, inst, sd in scored_rows:
        scored_by_key[(inst.id, r.fiscal_year)] = (r, sd)

    # Source documents (not necessarily scored) for the "needs_review" and
    # "gap-but-file-exists" cases.
    sd_rows = (
        db.query(SourceDocument, Institution)
        .join(Institution, Institution.id == SourceDocument.institution_id)
        .filter(Institution.active)
        .all()
    )
    sds_by_key: dict[tuple[int, int], list[SourceDocument]] = defaultdict(list)
    # Also group by institution so the unscored-bucket classifier below
    # doesn't emit a per-institution SELECT (was 18 extra round trips to
    # Supabase on every /coverage hit — the dominant cost in the ~16 s
    # pre-fix response time).
    sds_by_inst: dict[int, list[SourceDocument]] = defaultdict(list)
    for sd, inst in sd_rows:
        if sd.superseded_by_id is None:
            sds_by_key[(inst.id, sd.fiscal_year)].append(sd)
            sds_by_inst[inst.id].append(sd)

    gaps_by_key: dict[tuple[int, int], Gap] = {
        (g.institution_id, g.fiscal_year): g
        for g in db.query(Gap).all()
    }

    def _cell(iid: int, fy: int) -> CoverageCell:
        key = (iid, fy)
        if key in scored_by_key:
            _report, sd = scored_by_key[key]
            source = sd.source.value if sd else "manual"
            return CoverageCell(
                status="scored", reason="",
                source=source,
                sha256_prefix=(sd.sha256[:12] if sd else None),
                source_url=(sd.source_url if sd else None),
            )
        if sds := sds_by_key.get(key):
            # Pick the strictest reason — if any file is needs_review, surface that.
            sd = sds[0]
            review = sd.review_status.value if sd.review_status else "needs_review"
            rpt_type = sd.report_type.value if sd.report_type else "unknown"
            reason = (f"{sd.source.value} file present but "
                      f"review_status={review}, report_type={rpt_type}")
            return CoverageCell(
                status="needs_review" if review != "auto_ok" else "scored",
                reason=reason, source=sd.source.value,
                sha256_prefix=sd.sha256[:12], source_url=sd.source_url,
            )
        g = gaps_by_key.get(key)
        if g is not None:
            return CoverageCell(
                status="gap",
                reason=f"{g.reason.value}{': ' + (g.next_action or '') if g.next_action else ''}",
                source=None, sha256_prefix=None, source_url=None,
            )
        return CoverageCell(
            status="not_attempted", reason="not attempted (no file, no gap row)",
            source=None, sha256_prefix=None, source_url=None,
        )

    out_rows: list[CoverageRow] = []
    unscored_buckets = {"A_no_file": 0, "B_wayback_only_blocked": 0,
                        "D_page_threshold": 0}
    scored_inst_ids = {k[0] for k in scored_by_key}
    for inst in insts:
        cells = {fy: _cell(inst.id, fy) for fy in fys}
        years_cov = sorted(fy for fy, c in cells.items() if c.status == "scored")
        out_rows.append(CoverageRow(
            slug=inst.slug, name=inst.name,
            sector="financial" if inst.is_financial else "non-financial",
            cells=cells, years_covered=years_cov,
        ))
        if inst.id not in scored_inst_ids:
            # Bucket this not-covered institution. Uses the pre-built
            # sds_by_inst dict so we don't fire a fresh SELECT per
            # institution.
            all_sds = sds_by_inst.get(inst.id, [])
            if not all_sds:
                unscored_buckets["A_no_file"] += 1
                continue
            page_thr_hit = any(
                (sd.report_type and sd.report_type.value in ("annual", "integrated"))
                and (sd.page_count or 0) < 30
                and "pages (<" in (sd.review_note or "")
                for sd in all_sds
            )
            if page_thr_hit:
                unscored_buckets["D_page_threshold"] += 1
            else:
                unscored_buckets["B_wayback_only_blocked"] += 1

    return CoverageOut(
        meta=_meta(db), fiscal_years=fys, rows=out_rows,
        unscored_reasons=unscored_buckets,
    )


# ---------------------------- evidence + reviews ---------------------------


@router.get("/evidence", response_model=EvidenceOut)
def get_evidence(
    institution_slug: str | None = Query(None),
    fiscal_year: int | None = Query(None),
    pillar: str | None = Query(None),
    category: str | None = Query(None),
    term: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> EvidenceOut:
    tv = _latest_tv(db)
    q = (
        db.query(MatchEvidence, Term, Category, Report, Institution)
        .join(Term, Term.id == MatchEvidence.term_id)
        .join(Category, Category.id == Term.category_id)
        .join(Report, Report.id == MatchEvidence.report_id)
        .join(Institution, Institution.id == Report.institution_id)
        .filter(
            MatchEvidence.taxonomy_version_id == tv.id,
            MatchEvidence.pipeline_version == PIPELINE_VERSION,
        )
    )
    if institution_slug:
        q = q.filter(Institution.slug == institution_slug)
    if fiscal_year:
        q = q.filter(Report.fiscal_year == fiscal_year)
    if pillar:
        q = q.filter(Category.pillar == pillar)
    if category:
        q = q.filter(Category.name == category)
    if term:
        q = q.filter(Term.phrase == term)
    total = q.count()
    q = q.order_by(Institution.slug, Report.fiscal_year, MatchEvidence.page_number)
    rows_raw = q.offset((page - 1) * page_size).limit(page_size).all()
    reviews = {rv.evidence_id: rv for rv in _load_reviews(
        db, [me.id for me, *_ in rows_raw]
    )}
    rows = []
    for me, t, cat, rpt, inst in rows_raw:
        rv = reviews.get(me.id)
        rows.append(EvidenceRow(
            evidence_id=me.id, report_id=rpt.id,
            institution_slug=inst.slug, institution_name=inst.name,
            fiscal_year=rpt.fiscal_year, pillar=cat.pillar,
            category=cat.name, term_phrase=t.phrase,
            page_number=me.page_number, sentence_text=me.sentence_text,
            reviewed=rv is not None,
            reviewer=rv.reviewer if rv else None,
            reviewer_verdict=rv.verdict if rv else None,
        ))
    return EvidenceOut(
        meta=_meta(db), total=total, page=page, page_size=page_size, rows=rows
    )


def _load_reviews(db: Session, evidence_ids: list[int]):
    # Light wrapper so the Review table missing doesn't blow up the view
    # on an un-migrated environment.
    from sqlalchemy import inspect as sa_inspect
    if not evidence_ids:
        return []
    bind = db.bind
    if bind is None:
        return []
    insp = sa_inspect(bind)
    if "match_reviews" not in insp.get_table_names():
        return []
    from app.models.review import MatchReview
    return (
        db.query(MatchReview)
        .filter(MatchReview.evidence_id.in_(evidence_ids))
        .all()
    )


@router.post("/evidence/review")
def post_evidence_review(payload: ReviewSubmit, db: Session = Depends(get_db)):
    if payload.verdict not in {"valid", "false_positive", "unsure"}:
        raise HTTPException(status_code=422, detail=f"bad verdict: {payload.verdict}")
    from app.models.review import MatchReview
    existing = (
        db.query(MatchReview)
        .filter(MatchReview.evidence_id == payload.evidence_id)
        .one_or_none()
    )
    if existing is not None:
        existing.verdict = payload.verdict
        existing.reviewer = payload.reviewer
        existing.reviewed_at = datetime.now(UTC)
    else:
        rv = MatchReview(
            evidence_id=payload.evidence_id, reviewer=payload.reviewer,
            verdict=payload.verdict, reviewed_at=datetime.now(UTC),
        )
        db.add(rv)
    db.commit()
    return {"ok": True}


@router.get("/evidence/precision", response_model=list[PrecisionCell])
def get_precision(
    group: str = Query("term", description="term | category | pillar"),
    db: Session = Depends(get_db),
) -> list[PrecisionCell]:
    tv = _latest_tv(db)
    from app.models.review import MatchReview
    rows = (
        db.query(MatchReview, Term, Category, MatchEvidence)
        .join(MatchEvidence, MatchEvidence.id == MatchReview.evidence_id)
        .join(Term, Term.id == MatchEvidence.term_id)
        .join(Category, Category.id == Term.category_id)
        .filter(MatchEvidence.taxonomy_version_id == tv.id)
        .all()
    )
    bucket: dict[str, dict[str, int]] = defaultdict(
        lambda: {"reviewed": 0, "valid": 0, "false_positive": 0, "unsure": 0}
    )
    for rv, t, cat, _me in rows:
        key = {"term": t.phrase, "category": cat.name, "pillar": cat.pillar}[group]
        bucket[key]["reviewed"] += 1
        bucket[key][rv.verdict] += 1
    out = []
    for key, counts in sorted(bucket.items()):
        p = (
            counts["valid"] / (counts["valid"] + counts["false_positive"])
            if (counts["valid"] + counts["false_positive"])
            else None
        )
        out.append(PrecisionCell(
            term_or_category=key, reviewed=counts["reviewed"],
            valid=counts["valid"],
            false_positive=counts["false_positive"],
            unsure=counts["unsure"],
            precision_point=round(p, 3) if p is not None else None,
        ))
    return out


# ---------------------------- PDF range serve ------------------------------


@router.get("/pdf/{report_id}")
def get_pdf(report_id: int, db: Session = Depends(get_db)):
    rpt = db.get(Report, report_id)
    if rpt is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if not rpt.file_path:
        raise HTTPException(status_code=404, detail="PDF file missing on disk")
    from app.services.storage import open_pdf_stream, pdf_exists
    if not pdf_exists(rpt.file_path):
        raise HTTPException(status_code=404, detail="PDF file missing on disk")
    # Session 9: `file_path` is an R2 object key; stream it through
    # FastAPI's StreamingResponse rather than FileResponse-on-disk.
    return StreamingResponse(open_pdf_stream(rpt.file_path),
                             media_type="application/pdf")


# ---------------------------- sensitivity ----------------------------------


@router.get("/sensitivity", response_model=SensitivityOut)
def get_sensitivity(db: Session = Depends(get_db)) -> SensitivityOut:
    if not SENSITIVITY_CSV.exists():
        raise HTTPException(status_code=404,
                            detail="sensitivity_summary.csv not generated yet")
    rows: list[SensitivityInstitutionRow] = []
    with SENSITIVITY_CSV.open("r", encoding="utf-8") as fh:
        first = fh.readline()
        if not first.startswith("#"):
            fh.seek(0)
        for r in csv.DictReader(fh):
            rows.append(SensitivityInstitutionRow(
                slug=r["slug"], sector=r["sector"],
                years_covered=int(r["years_covered"]),
                baseline_rank=int(r["baseline_rank"]),
                jitter_median_rank=int(r["jitter_median_rank"]),
                jitter_p5_rank=int(r["jitter_p5_rank"]),
                jitter_p95_rank=int(r["jitter_p95_rank"]),
                jitter_interval_width=int(r["jitter_interval_width"]),
                equal_weights_rank=int(r["equal_weights_rank"]),
                toc_off_rank=int(r["toc_off_rank"]),
                repeat_off_rank=int(r["repeat_off_rank"]),
                all_mode_rank=int(r["all_mode_rank"]),
                flag_single_year_high_volatility=(r.get(
                    "flag_single_year_high_volatility", "") == "YES"),
            ))

    # Scrape headline stats from the markdown (fine for Session 7+ — the
    # MD is author-controlled, generated by sensitivity_analysis.py, not
    # user-input). Session 10 presentation pass extends this to also
    # pick up the 5-95% jitter intervals and per-switch spearmans so the
    # UI's stat callouts don't have to re-parse the markdown.
    import re
    md = SENSITIVITY_MD.read_text(encoding="utf-8") if SENSITIVITY_MD.exists() else ""

    def _num_after(label: str) -> float:
        m = re.search(label + r"[^0-9\-]*(-?\d+\.\d+)", md)
        return float(m.group(1)) if m else 0.0

    def _jitter_median_and_interval(sector_label: str) -> tuple[float, float, float]:
        """Return (median, p5, p95) for the `sector_label` jitter line.
        Matches the string shape produced by sensitivity_analysis.py:
            `<sector_label> sector: median = **0.985**, 5-95% = [0.970, 0.985].`"""
        pattern = (
            rf"{sector_label} sector: median = \*\*(?P<median>-?\d+\.\d+)\*\*"
            r",\s*5-95%\s*=\s*\[(?P<p5>-?\d+\.\d+),\s*(?P<p95>-?\d+\.\d+)\]"
        )
        m = re.search(pattern, md)
        if not m:
            return 0.0, 0.0, 0.0
        return float(m["median"]), float(m["p5"]), float(m["p95"])

    def _switch_summary() -> dict[str, dict[str, float]]:
        """Pull per-switch spearman pairs out of each `### `<switch>`` block:
            `- Spearman fin = **1.000**, non-fin = **1.000**`"""
        out: dict[str, dict[str, float]] = {}
        for match in re.finditer(
            r"###\s*`(?P<name>[a-z_]+)`[\s\S]*?Spearman\s+fin\s*=\s*\*\*"
            r"(?P<fin>-?\d+\.\d+)\*\*,\s*non-fin\s*=\s*\*\*"
            r"(?P<non_fin>-?\d+\.\d+)\*\*",
            md,
        ):
            out[match["name"]] = {
                "spearman_fin": float(match["fin"]),
                "spearman_non_fin": float(match["non_fin"]),
            }
        return out

    fin_med, fin_p5, fin_p95 = _jitter_median_and_interval("financial")
    nf_med, nf_p5, nf_p95 = _jitter_median_and_interval("non-financial")

    return SensitivityOut(
        meta=_meta(db),
        kendall_fin_median=fin_med,
        kendall_fin_p5=fin_p5,
        kendall_fin_p95=fin_p95,
        kendall_non_fin_median=nf_med,
        kendall_non_fin_p5=nf_p5,
        kendall_non_fin_p95=nf_p95,
        equal_spearman_fin=_num_after("financial sector: \\*\\*"),
        equal_spearman_non_fin=_num_after("non-financial sector: \\*\\*"),
        switch_summary=_switch_summary(),
        rows=rows,
        summary_markdown=md,
    )


# ---------------------------- taxonomy -------------------------------------


@router.get("/taxonomy/versions", response_model=list[TaxonomyVersionView])
def list_tv_versions(db: Session = Depends(get_db)) -> list[TaxonomyVersionView]:
    out: list[TaxonomyVersionView] = []
    for tv in db.query(TaxonomyVersion).order_by(TaxonomyVersion.created_at).all():
        out.append(TaxonomyVersionView(
            hash=tv.hash,
            created_at=tv.created_at.isoformat() if tv.created_at else "",
            note=tv.note, categories=[],
        ))
    return out


@router.get("/taxonomy/current", response_model=TaxonomyVersionView)
def get_current_taxonomy(db: Session = Depends(get_db)) -> TaxonomyVersionView:
    tv = _latest_tv(db)
    cats = db.query(Category).order_by(Category.id).all()
    out_cats: list[TaxonomyCategoryView] = []
    for c in cats:
        terms = sorted(c.terms, key=lambda t: t.phrase)
        out_cats.append(TaxonomyCategoryView(
            category_id=c.id, name=c.name, pillar=c.pillar, weight=c.weight,
            sourcing_note="",
            terms=[TaxonomyTermView(term_id=t.id, phrase=t.phrase,
                                    weight=t.weight, lemma_based=t.lemma_based)
                   for t in terms],
        ))
    return TaxonomyVersionView(
        hash=tv.hash, created_at=tv.created_at.isoformat() if tv.created_at else "",
        note=tv.note, categories=out_cats,
    )


# ---------------------------- methodology ----------------------------------


@router.get("/methodology")
def get_methodology():
    if METHODOLOGY_MD.exists():
        return Response(
            content=METHODOLOGY_MD.read_text(encoding="utf-8"),
            media_type="text/markdown",
        )
    return Response(
        content=("# Methodology\n\n"
                 "_(docs/METHODOLOGY.md hasn't been written yet; this view will "
                 "render it as soon as the file exists.)_\n"),
        media_type="text/markdown",
    )


# ---------------------------- benchmark upload stub -----------------------


@router.get("/benchmark/status")
def benchmark_status():
    """Session 7 stub: no benchmark data imported yet. The UI should render
    the empty-state 'upload a CSV to compare' prompt — NOT an error."""
    return {"imported": False, "rows": 0,
            "message": "No benchmark data imported. Upload a CSV via the "
                       "/benchmark view to begin."}


@router.post("/benchmark/upload")
def benchmark_upload():
    raise HTTPException(
        status_code=501,
        detail="Benchmark upload server-side validation is deferred to Session 8. "
               "The UI shows the empty-state prompt until that's wired up.",
    )


# ---------------------------- CSV exports ----------------------------------


@router.get("/export/leaderboard.csv")
def export_leaderboard(db: Session = Depends(get_db)):
    lb = get_leaderboard(db=db)
    buf = io.StringIO()
    buf.write(f"# taxonomy={lb.meta.taxonomy_version} pipeline={lb.meta.pipeline_version} "
              f"snapshot={lb.meta.data_snapshot_date}\n")
    w = csv.writer(buf)
    w.writerow(["rank_overall", "rank_within_sector", "slug", "name", "sector",
                "country", "industry", "mean_composite", "env", "soc", "gov",
                "years_covered", "data_quality_flag"])
    for r in lb.rows:
        w.writerow([r.rank_overall, r.rank_within_sector, r.slug, r.name,
                    r.sector, r.country, r.industry or "", r.mean_composite,
                    r.env, r.soc, r.gov,
                    ";".join(str(y) for y in r.years_covered),
                    r.data_quality_flag])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=leaderboard.csv"})
