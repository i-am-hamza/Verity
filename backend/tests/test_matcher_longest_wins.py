"""
Nested-phrase deduplication: when the taxonomy contains both a short and a
long form of the same concept, one span in the text must only count once.

Two overlap flavours matter here:

1) Within a single matcher: "corporate governance" contains "governance",
   both LEMMA-based.
2) Across matchers: "internal control over financial reporting" is an exact
   (lower-attr) term, while "internal control" is lemma-based. The exact
   matcher will find the long phrase; the lemma matcher will find the short
   one nested inside it. In "longest" mode, only the long one counts.

These tests are written against the real TaxonomyMatcher with a real spaCy
model — no mocks — because the whole point is that spacy.util.filter_spans
is what implements longest-wins, and stubbing it out proves nothing.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services import matcher as matcher_module
from app.services.matcher import TaxonomyMatcher
from app.services.text_processing import Sentence
from app.services.verity_config import VerityConfig


@dataclass
class FakeTerm:
    id: int
    phrase: str
    weight: float
    lemma_based: bool
    category_id: int


def _sent(text: str, page: int = 1) -> Sentence:
    return Sentence(page_number=page, text=text)


def _use_mode(monkeypatch, mode: str) -> None:
    """Force the matcher to use a specific matching_mode without touching disk."""
    forced = VerityConfig(matching_mode=mode)
    monkeypatch.setattr(matcher_module, "load_verity_config", lambda: forced)


def test_longest_match_wins_within_lemma_matcher(monkeypatch):
    _use_mode(monkeypatch, "longest")
    terms = [
        FakeTerm(id=1, phrase="governance", weight=1.0, lemma_based=True, category_id=1),
        FakeTerm(id=2, phrase="corporate governance", weight=1.2, lemma_based=True, category_id=1),
    ]
    matcher = TaxonomyMatcher(terms)
    matches = matcher.match_sentences([_sent("Our corporate governance framework is documented.")])

    matched_term_ids = [m.term_id for m in matches]
    assert matched_term_ids == [2], (
        f"expected only the longer 'corporate governance' to survive; got {matched_term_ids}"
    )


def test_longest_match_wins_across_lemma_and_exact_matchers(monkeypatch):
    """The long ICOFR phrase is exact-cased; the short one is lemma-based.
    Longest-wins must apply across both matchers, not per-matcher."""
    _use_mode(monkeypatch, "longest")
    terms = [
        FakeTerm(id=10, phrase="internal control", weight=1.0, lemma_based=True, category_id=1),
        FakeTerm(
            id=11, phrase="internal control over financial reporting",
            weight=1.4, lemma_based=False, category_id=1,
        ),
    ]
    matcher = TaxonomyMatcher(terms)
    matches = matcher.match_sentences(
        [_sent("We maintain internal control over financial reporting under COSO.")]
    )

    matched_term_ids = [m.term_id for m in matches]
    assert matched_term_ids == [11], (
        f"expected only the longer ICOFR term to survive cross-matcher; got {matched_term_ids}"
    )


def test_all_mode_keeps_overlapping_matches(monkeypatch):
    """`all` mode is diagnostic — every overlap is recorded, no filtering."""
    _use_mode(monkeypatch, "all")
    terms = [
        FakeTerm(id=1, phrase="governance", weight=1.0, lemma_based=True, category_id=1),
        FakeTerm(id=2, phrase="corporate governance", weight=1.2, lemma_based=True, category_id=1),
    ]
    matcher = TaxonomyMatcher(terms)
    matches = matcher.match_sentences([_sent("Our corporate governance framework is documented.")])
    assert sorted(m.term_id for m in matches) == [1, 2]


def test_non_overlapping_matches_all_kept(monkeypatch):
    """Longest-wins must not collapse legitimately distinct matches."""
    _use_mode(monkeypatch, "longest")
    terms = [
        FakeTerm(id=1, phrase="governance", weight=1.0, lemma_based=True, category_id=1),
        FakeTerm(id=2, phrase="risk management", weight=1.0, lemma_based=True, category_id=1),
    ]
    matcher = TaxonomyMatcher(terms)
    matches = matcher.match_sentences(
        [_sent("The board covers governance and risk management as separate committee remits.")]
    )
    assert sorted(m.term_id for m in matches) == [1, 2]
