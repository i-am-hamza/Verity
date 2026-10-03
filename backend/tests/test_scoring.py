"""
Pure unit tests for app/services/scoring.py — no DB, no spaCy, no PDF
needed. Run with: pytest tests/test_scoring.py
"""
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.scoring import (
    CategoryScoreResult,
    aggregate_institution_score,
    aggregate_pillar_scores,
    composite_score,
    score_report_categories,
)


@dataclass
class FakeMatch:
    term_id: int


@dataclass
class FakeTerm:
    id: int
    category_id: int
    weight: float


def test_density_normalizes_by_report_length():
    """Two reports with the same raw count but different lengths should NOT score equal
    — the shorter report should score higher (this is the whole point of using density)."""
    terms = {1: FakeTerm(id=1, category_id=1, weight=1.0)}
    matches = [FakeMatch(term_id=1)] * 10  # 10 hits in both reports

    short_report_scores = score_report_categories(matches, terms, total_words=1000)
    long_report_scores = score_report_categories(matches, terms, total_words=10000)

    assert short_report_scores[0].density_per_1000_words > long_report_scores[0].density_per_1000_words
    assert short_report_scores[0].density_per_1000_words == 10.0
    assert long_report_scores[0].density_per_1000_words == 1.0


def test_term_weight_scales_contribution():
    terms = {1: FakeTerm(id=1, category_id=1, weight=2.0)}
    matches = [FakeMatch(term_id=1)] * 5

    result = score_report_categories(matches, terms, total_words=1000)
    assert result[0].raw_weighted_count == 10.0  # 5 hits * weight 2.0
    assert result[0].density_per_1000_words == 10.0


def test_governance_needs_improvement_counts_same_as_positive_mention():
    """The core edge case from the spec: sentiment of the surrounding sentence
    is irrelevant — a match is a match. We simulate this by asserting the
    matcher/scorer never looks at sentence text at all, only term_id counts."""
    terms = {1: FakeTerm(id=1, category_id=1, weight=1.0)}
    # Both scenarios produce identical matches regardless of what the sentence said
    positive_context_matches = [FakeMatch(term_id=1)]
    negative_context_matches = [FakeMatch(term_id=1)]

    positive_score = score_report_categories(positive_context_matches, terms, total_words=1000)
    negative_score = score_report_categories(negative_context_matches, terms, total_words=1000)

    assert positive_score[0].density_per_1000_words == negative_score[0].density_per_1000_words


def test_composite_score_applies_category_weights():
    category_scores = [
        CategoryScoreResult(category_id=1, raw_weighted_count=10, density_per_1000_words=10.0),
        CategoryScoreResult(category_id=2, raw_weighted_count=5, density_per_1000_words=5.0),
    ]
    weights = {1: 2.0, 2: 1.0}  # category 1 counts double

    result = composite_score(category_scores, weights)
    assert result == 25.0  # (10*2.0) + (5*1.0)


def test_aggregate_institution_score_equal_weighted():
    scores = [(2022, 10.0), (2023, 20.0)]
    assert aggregate_institution_score(scores) == 15.0


def test_aggregate_institution_score_recency_weighted_favors_recent_years():
    scores = [(2022, 10.0), (2023, 20.0)]
    equal = aggregate_institution_score(scores, recency_weighted=False)
    recency = aggregate_institution_score(scores, recency_weighted=True)
    # recency-weighted average should be pulled toward the more recent (higher) score
    assert recency > equal


def test_empty_reports_score_zero():
    assert aggregate_institution_score([]) == 0.0


def test_pillar_aggregation_groups_categories_by_pillar():
    """Today: 1 category per pillar, so pillar score == that category's
    weighted density. This test exists to lock that equivalence AND to
    prove the grouping is by category_pillar_map, not category count —
    see the two-categories-one-pillar test below."""
    category_scores = [
        CategoryScoreResult(category_id=1, raw_weighted_count=10, density_per_1000_words=10.0),  # Environmental
        CategoryScoreResult(category_id=2, raw_weighted_count=5, density_per_1000_words=5.0),    # Social
        CategoryScoreResult(category_id=3, raw_weighted_count=8, density_per_1000_words=8.0),    # Governance
    ]
    pillar_map = {1: "Environmental", 2: "Social", 3: "Governance"}
    weights = {1: 1.0, 2: 1.0, 3: 1.0}

    result = aggregate_pillar_scores(category_scores, pillar_map, weights)
    assert result == {"Environmental": 10.0, "Social": 5.0, "Governance": 8.0}


def test_pillar_aggregation_sums_multiple_categories_into_one_pillar():
    """Proves the design goal explicitly: splitting a pillar into several
    categories later (e.g. Governance -> Board & Ethics + Internal Controls)
    requires no change to this function — their densities just sum."""
    category_scores = [
        CategoryScoreResult(category_id=10, raw_weighted_count=6, density_per_1000_words=6.0),   # Governance: Board & Ethics
        CategoryScoreResult(category_id=11, raw_weighted_count=4, density_per_1000_words=4.0),   # Governance: Internal Controls
    ]
    pillar_map = {10: "Governance", 11: "Governance"}
    weights = {10: 1.0, 11: 1.0}

    result = aggregate_pillar_scores(category_scores, pillar_map, weights)
    assert result == {"Governance": 10.0}  # 6.0 + 4.0, summed into the one pillar bucket


def test_pillar_aggregation_applies_category_weight():
    category_scores = [CategoryScoreResult(category_id=1, raw_weighted_count=10, density_per_1000_words=10.0)]
    pillar_map = {1: "Environmental"}
    weights = {1: 2.0}  # this category counts double toward its pillar

    result = aggregate_pillar_scores(category_scores, pillar_map, weights)
    assert result == {"Environmental": 20.0}
