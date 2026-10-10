"""
Multi-phrase matching engine.

Runs two spaCy PhraseMatcher passes per sentence:
- LEMMA-attr patterns for terms marked lemma_based=True (so "governed" /
  "governing" / "governance" all count as the same hit)
- LOWER-attr (case-insensitive exact) patterns for terms marked lemma_based=False

PhraseMatcher does a single trie-style pass, so matching hundreds of
phrases against hundreds of documents stays roughly linear instead of
degrading to O(terms x pages) the way a naive `text.count(phrase)` loop
per term would.

Overlap handling (settings.matching_mode):
- "longest" (default): collapse overlapping spans across BOTH matchers and
  keep only the longest one. Avoids double-counting when the taxonomy has
  both a short and a long form of the same concept
  ("corporate governance" also matching "governance"; ICOFR also matching
  "internal control"). Implemented with spacy.util.filter_spans, which
  keeps longest and, on ties, the earlier span.
- "all": keep every match. Diagnostic use only — it inflates density.

NOTE on perf at scale: this reprocesses sentence text through the spaCy
pipeline a second time (segmentation already ran it once). Fine for a
10-15 institution pilot; if you scale, keep spaCy Span objects from
segmentation instead of plain strings and match directly on those to
avoid the double pass.
"""
from dataclasses import dataclass

from spacy.matcher import PhraseMatcher
from spacy.tokens import Span
from spacy.util import filter_spans

from app.services.text_processing import Sentence, get_nlp
from app.services.verity_config import load_verity_config


@dataclass
class TermMatch:
    term_id: int
    page_number: int
    sentence_text: str


class TaxonomyMatcher:
    def __init__(self, terms: list) -> None:
        """terms: list of Term ORM objects (id, phrase, weight, lemma_based, category_id)."""
        self.nlp = get_nlp()
        self.term_by_label: dict[str, int] = {}

        self.lemma_matcher = PhraseMatcher(self.nlp.vocab, attr="LEMMA")
        self.exact_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        for term in terms:
            label = f"term_{term.id}"
            self.term_by_label[label] = term.id
            # Full pipeline (not make_doc) so LEMMA is populated on the pattern.
            pattern_doc = self.nlp(term.phrase)
            if term.lemma_based:
                self.lemma_matcher.add(label, [pattern_doc])
            else:
                self.exact_matcher.add(label, [pattern_doc])

    def _spans(self, doc) -> list[Span]:
        """Every match from both matchers, as labelled Spans.

        The Span.label carries the phrase-matcher label id so we can
        recover the term after filter_spans.
        """
        spans: list[Span] = []
        for matcher in (self.lemma_matcher, self.exact_matcher):
            for match_id, start, end in matcher(doc):
                spans.append(Span(doc, start, end, label=match_id))
        return spans

    def match_sentences(self, sentences: list[Sentence]) -> list[TermMatch]:
        results: list[TermMatch] = []
        # Matching mode is read from config/verity.toml, not baked into code
        # (CLAUDE.md, rule 1: config over code).
        mode = load_verity_config().matching_mode
        if mode not in ("longest", "all"):
            raise ValueError(
                f"unknown matching_mode {mode!r}; expected 'longest' or 'all'"
            )

        for sent in sentences:
            # Lowercase before NLP so Title-Case / ALL-CAPS tokens get the same
            # lemma as their lowercase equivalents.  "Risk Management Committee"
            # tagged as PROPN yields lemma "Risk"/"Management"; lowercased first
            # it yields "risk"/"management", matching the pattern.  exact_matcher
            # uses attr="LOWER" so it is already case-insensitive — pre-lowercasing
            # leaves its behaviour unchanged.
            doc = self.nlp(sent.text.lower())
            spans = self._spans(doc)
            if not spans:
                continue

            # In "longest" mode, filter_spans keeps the longest span and,
            # on ties, the earliest — resolving overlaps across both matchers
            # in a single pass rather than per-matcher.
            kept = filter_spans(spans) if mode == "longest" else spans

            for span in kept:
                label = self.nlp.vocab.strings[span.label]
                term_id = self.term_by_label[label]
                results.append(
                    TermMatch(
                        term_id=term_id,
                        page_number=sent.page_number,
                        sentence_text=sent.text,  # original (not lowercased) for storage
                    )
                )
        return results
