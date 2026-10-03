"""Pydantic shapes for the Session 7 dashboard endpoints.

Kept in a separate module from the legacy InstitutionRankingOut / CategoryScoreOut
schemas so the dashboard contract can evolve without churning older callers.
Every field here is deliberately spelled out — nothing is Any, nothing defers
to .dict() reshaping on the frontend.
"""
from __future__ import annotations

from pydantic import BaseModel


class LeaderboardRow(BaseModel):
    institution_id: int
    slug: str
    name: str
    country: str
    sector: str  # "financial" | "non-financial"
    industry: str | None
    rank_overall: int
    rank_within_sector: int
    mean_composite: float
    env: float
    soc: float
    gov: float
    years_covered: list[int]
    data_quality_flag: str  # "" when clean
    data_quality_reason: str


class LeaderboardMeta(BaseModel):
    taxonomy_version: str
    pipeline_version: str
    data_snapshot_date: str
    scored_institutions: int
    active_institutions: int
    scored_reports: int


class LeaderboardOut(BaseModel):
    meta: LeaderboardMeta
    rows: list[LeaderboardRow]


class ReportRow(BaseModel):
    report_id: int
    fiscal_year: int
    source: str  # crawler | wayback | manual | exchange
    source_url: str
    retrieved_at: str
    sha256_prefix: str
    review_status: str  # auto_ok | needs_review | rejected
    processing_review_status: str
    page_count: int
    composite_score: float
    env: float
    soc: float
    gov: float


class InstitutionDetail(BaseModel):
    institution_id: int
    slug: str
    name: str
    country: str
    sector: str
    industry: str | None
    ticker: str | None
    market_cap_usd: int | None
    market_cap_date: str | None
    data_quality_flag: str
    data_quality_reason: str
    years_covered: list[int]
    reports: list[ReportRow]
    category_breakdown: dict[str, dict[str, float]]
    # {fiscal_year: {category_name: density}}


class CoverageCell(BaseModel):
    status: str  # "scored" | "needs_review" | "gap" | "not_attempted"
    reason: str
    source: str | None
    sha256_prefix: str | None
    source_url: str | None


class CoverageRow(BaseModel):
    slug: str
    name: str
    sector: str
    cells: dict[int, CoverageCell]
    years_covered: list[int]


class CoverageOut(BaseModel):
    meta: LeaderboardMeta
    fiscal_years: list[int]
    rows: list[CoverageRow]
    unscored_reasons: dict[str, int]  # bucket (A/B/D) -> count


class EvidenceRow(BaseModel):
    evidence_id: int
    report_id: int
    institution_slug: str
    institution_name: str
    fiscal_year: int
    pillar: str
    category: str
    term_phrase: str
    page_number: int
    sentence_text: str
    reviewed: bool
    reviewer: str | None
    reviewer_verdict: str | None  # valid | false_positive | unsure


class EvidenceOut(BaseModel):
    meta: LeaderboardMeta
    total: int
    page: int
    page_size: int
    rows: list[EvidenceRow]


class ReviewSubmit(BaseModel):
    evidence_id: int
    reviewer: str
    verdict: str  # valid | false_positive | unsure


class PrecisionCell(BaseModel):
    term_or_category: str
    reviewed: int
    valid: int
    false_positive: int
    unsure: int
    precision_point: float | None  # None if n < 1


class SensitivityInstitutionRow(BaseModel):
    slug: str
    sector: str
    years_covered: int
    baseline_rank: int
    jitter_median_rank: int
    jitter_p5_rank: int
    jitter_p95_rank: int
    jitter_interval_width: int
    equal_weights_rank: int
    toc_off_rank: int
    repeat_off_rank: int
    all_mode_rank: int
    flag_single_year_high_volatility: bool


class SensitivityOut(BaseModel):
    meta: LeaderboardMeta
    kendall_fin_median: float
    kendall_fin_p5: float
    kendall_fin_p95: float
    kendall_non_fin_median: float
    kendall_non_fin_p5: float
    kendall_non_fin_p95: float
    equal_spearman_fin: float
    equal_spearman_non_fin: float
    switch_summary: dict[str, dict[str, float]]
    rows: list[SensitivityInstitutionRow]
    summary_markdown: str


class TaxonomyTermView(BaseModel):
    term_id: int
    phrase: str
    weight: float
    lemma_based: bool


class TaxonomyCategoryView(BaseModel):
    category_id: int
    name: str
    pillar: str
    weight: float
    sourcing_note: str
    terms: list[TaxonomyTermView]


class TaxonomyVersionView(BaseModel):
    hash: str
    created_at: str
    note: str | None
    categories: list[TaxonomyCategoryView]


class ScoresLongRow(BaseModel):
    institution_slug: str
    fiscal_year: int
    pillar: str
    density: float
    composite_score: float
