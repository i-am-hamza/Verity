"""
Core scoring logic.

Design principle: this is a *disclosure/coverage* score, not a
sentiment score. "Governance needs to be improved" counts exactly the
same as "governance is strong" — presence and density of the term is
what's measured, not the polarity of the surrounding sentence. This
sidesteps the well-documented problem of generic sentiment dictionaries
misclassifying ordinary words in financial text (Loughran & McDonald,
2011) by not attempting sentiment classification at all.

Formula:
    category_score   = (sum of term.weight for every match in that category) / total_words * 1000
    composite_score   = sum(category_score * category.weight) across all categories
    institution_score = average (or recency-weighted average) of composite_score across its reports
"""
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class CategoryScoreResult:
    category_id: int
    raw_weighted_count: float
    density_per_1000_words: float


def score_report_categories(matches: list, term_lookup: dict, total_words: int) -> list[CategoryScoreResult]:
    """
    matches: list[TermMatch] from TaxonomyMatcher.match_sentences
    term_lookup: term_id -> Term ORM object (for .weight and .category_id)
    total_words: Report.total_word_count
    """
    if total_words == 0:
        return []

    weighted_by_category: dict[int, float] = defaultdict(float)
    for m in matches:
        term = term_lookup[m.term_id]
        weighted_by_category[term.category_id] += term.weight

    return [
        CategoryScoreResult(
            category_id=category_id,
            raw_weighted_count=raw,
            density_per_1000_words=(raw / total_words) * 1000,
        )
        for category_id, raw in weighted_by_category.items()
    ]


def composite_score(category_scores: list[CategoryScoreResult], category_weights: dict[int, float]) -> float:
    """Weighted sum of per-category densities -> one comparable number per report."""
    total = sum(
        cs.density_per_1000_words * category_weights.get(cs.category_id, 1.0)
        for cs in category_scores
    )
    return round(total, 3)


def aggregate_pillar_scores(
    category_scores: list[CategoryScoreResult],
    category_pillar_map: dict[int, str],   # category_id -> "Environmental" | "Social" | "Governance"
    category_weights: dict[int, float],
) -> dict[str, float]:
    """
    Groups category scores by ESG pillar rather than by category identity.
    Today each pillar has exactly one category, so this equals that
    category's density — but the grouping is by category_pillar_map, not
    by category count, so splitting a pillar into several categories later
    (e.g. Governance -> Board & Ethics / Internal Controls / IT & Security)
    needs no change here: their weighted densities just sum into the same
    pillar bucket.
    """
    pillar_totals: dict[str, float] = defaultdict(float)
    for cs in category_scores:
        pillar = category_pillar_map.get(cs.category_id)
        if pillar is None:
            continue
        pillar_totals[pillar] += cs.density_per_1000_words * category_weights.get(cs.category_id, 1.0)

    return {pillar: round(total, 3) for pillar, total in pillar_totals.items()}


def aggregate_institution_score(
    report_scores: list[tuple[int, float]],  # [(fiscal_year, composite_score), ...]
    recency_weighted: bool = False,
) -> float:
    """
    Combine an institution's per-report composite scores into one number.
    Equal-weighted average by default. Set recency_weighted=True to give
    more recent years more influence (linear ramp: oldest=1, newest=n).
    """
    if not report_scores:
        return 0.0
    if not recency_weighted or len(report_scores) == 1:
        return round(sum(s for _, s in report_scores) / len(report_scores), 3)

    ordered = sorted(report_scores, key=lambda x: x[0])  # oldest -> newest
    weights = list(range(1, len(ordered) + 1))
    weighted_sum = sum(w * s for w, (_, s) in zip(weights, ordered, strict=True))
    return round(weighted_sum / sum(weights), 3)
