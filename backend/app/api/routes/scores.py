from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.institution import Institution
from app.models.report import Report, ReportStatus
from app.models.score import CategoryScore
from app.models.taxonomy import Category, TaxonomyVersion
from app.schemas.score import CategoryScoreOut, InstitutionRankingOut, ReportScoreOut
from app.services.scoring import (
    CategoryScoreResult,
    aggregate_institution_score,
    aggregate_pillar_scores,
    composite_score,
)

router = APIRouter(prefix="/scores", tags=["scores"])


def _category_weights(db: Session) -> dict[int, float]:
    return {c.id: c.weight for c in db.query(Category).all()}


def _category_pillars(db: Session) -> dict[int, str]:
    return {c.id: c.pillar for c in db.query(Category).all()}


def _category_breakdown(db: Session, category_scores: list[CategoryScore]) -> list[CategoryScoreOut]:
    breakdown: list[CategoryScoreOut] = []
    for cs in category_scores:
        category = db.get(Category, cs.category_id)
        breakdown.append(CategoryScoreOut(
            category_id=cs.category_id,
            category_name=category.name if category else "unknown",
            raw_weighted_count=cs.raw_weighted_count,
            density_per_1000_words=cs.density_per_1000_words,
        ))
    return breakdown


def _resolve_version_id(db: Session, taxonomy_version_id: int | None) -> int | None:
    """Resolve the taxonomy version to score against.

    None -> the latest version by created_at (falls back to None if the
    taxonomy_versions table is empty, in which case legacy rows with a NULL
    version_id are returned).
    """
    if taxonomy_version_id is not None:
        return taxonomy_version_id
    latest = (
        db.query(TaxonomyVersion)
        .order_by(TaxonomyVersion.created_at.desc(), TaxonomyVersion.id.desc())
        .first()
    )
    return latest.id if latest else None


def _scores_for_report(
    db: Session, report_id: int, taxonomy_version_id: int | None
) -> list[CategoryScore]:
    """Rows for the given report AND the resolved version. If no rows exist
    at the requested version, fall through to the union of every version —
    otherwise a legacy report processed once under NULL taxonomy_version_id
    would silently score zero."""
    if taxonomy_version_id is None:
        return db.query(CategoryScore).filter(CategoryScore.report_id == report_id).all()
    rows = (
        db.query(CategoryScore)
        .filter(
            CategoryScore.report_id == report_id,
            CategoryScore.taxonomy_version_id == taxonomy_version_id,
        )
        .all()
    )
    if rows:
        return rows
    # Legacy fallback: return the latest rows regardless of version so
    # a pre-versioning report doesn't disappear from the API.
    return db.query(CategoryScore).filter(CategoryScore.report_id == report_id).all()


@router.get("/reports/{report_id}", response_model=ReportScoreOut)
def get_report_score(
    report_id: int,
    taxonomy_version_id: int | None = Query(None, description="Defaults to the latest version"),
    db: Session = Depends(get_db),
) -> ReportScoreOut:
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != ReportStatus.scored:
        raise HTTPException(
            status_code=409, detail=f"Report is not scored yet (status: {report.status})"
        )

    version_id = _resolve_version_id(db, taxonomy_version_id)
    category_scores = _scores_for_report(db, report_id, version_id)
    weights = _category_weights(db)
    pillars = _category_pillars(db)

    score_results = [
        CategoryScoreResult(cs.category_id, cs.raw_weighted_count, cs.density_per_1000_words)
        for cs in category_scores
    ]
    return ReportScoreOut(
        report_id=report.id,
        fiscal_year=report.fiscal_year,
        composite_score=composite_score(score_results, weights),
        pillar_scores=aggregate_pillar_scores(score_results, pillars, weights),
        category_scores=_category_breakdown(db, category_scores),
    )


@router.get("/institutions/{institution_id}", response_model=InstitutionRankingOut)
def get_institution_score(
    institution_id: int,
    recency_weighted: bool = False,
    taxonomy_version_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> InstitutionRankingOut:
    institution = db.get(Institution, institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    reports = db.query(Report).filter(
        Report.institution_id == institution_id, Report.status == ReportStatus.scored
    ).all()
    if not reports:
        raise HTTPException(status_code=409, detail="No scored reports for this institution yet")

    version_id = _resolve_version_id(db, taxonomy_version_id)
    weights = _category_weights(db)
    pillars = _category_pillars(db)
    report_scores: list[tuple[int, float]] = []
    pillar_scores_per_year: list[dict[str, float]] = []
    all_category_scores: list[CategoryScore] = []

    for report in reports:
        category_scores = _scores_for_report(db, report.id, version_id)
        all_category_scores.extend(category_scores)
        score_results = [
            CategoryScoreResult(cs.category_id, cs.raw_weighted_count, cs.density_per_1000_words)
            for cs in category_scores
        ]
        report_scores.append((report.fiscal_year, composite_score(score_results, weights)))
        pillar_scores_per_year.append(aggregate_pillar_scores(score_results, pillars, weights))

    institution_score = aggregate_institution_score(report_scores, recency_weighted=recency_weighted)

    pillar_totals: dict[str, list[float]] = {}
    for year_pillars in pillar_scores_per_year:
        for pillar, score in year_pillars.items():
            pillar_totals.setdefault(pillar, []).append(score)
    pillar_breakdown = {p: round(sum(vals) / len(vals), 3) for p, vals in pillar_totals.items()}

    by_category: dict[int, list[float]] = {}
    for cs in all_category_scores:
        by_category.setdefault(cs.category_id, []).append(cs.density_per_1000_words)

    breakdown: list[CategoryScoreOut] = []
    for category_id, densities in by_category.items():
        category = db.get(Category, category_id)
        breakdown.append(CategoryScoreOut(
            category_id=category_id,
            category_name=category.name if category else "unknown",
            raw_weighted_count=0.0,
            density_per_1000_words=round(sum(densities) / len(densities), 3),
        ))

    return InstitutionRankingOut(
        institution_id=institution.id,
        institution_name=institution.name,
        country=institution.country,
        institution_score=institution_score,
        years_scored=len(reports),
        pillar_breakdown=pillar_breakdown,
        category_breakdown=breakdown,
    )


@router.get("/rankings", response_model=list[InstitutionRankingOut])
def get_rankings(
    recency_weighted: bool = False,
    taxonomy_version_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> list[InstitutionRankingOut]:
    """Full leaderboard across every institution with at least one scored report."""
    institutions = db.query(Institution).all()
    results: list[InstitutionRankingOut] = []
    for institution in institutions:
        try:
            results.append(
                get_institution_score(institution.id, recency_weighted, taxonomy_version_id, db)
            )
        except HTTPException:
            continue  # skip institutions with no scored reports yet
    return sorted(results, key=lambda r: r.institution_score, reverse=True)
