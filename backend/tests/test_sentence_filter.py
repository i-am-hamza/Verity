"""Unit tests for the v0.4.2 sentence quality filter.

Covers is_sentence_quality and filter_sentences from text_processing.
No DB, no spaCy, no PDF needed.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.text_processing import Sentence, filter_sentences, is_sentence_quality

# ---------------------------------------------------------------------------
# is_sentence_quality — positive cases
# ---------------------------------------------------------------------------

def test_valid_sentence_passes():
    assert is_sentence_quality(
        "The company reduced its greenhouse gas emissions by fifteen percent in 2023."
    )


def test_sentence_with_closing_quote_passes():
    assert is_sentence_quality(
        'The board confirmed that "all governance policies were reviewed and updated."'
    )


def test_sentence_with_closing_bracket_passes():
    assert is_sentence_quality(
        "Carbon emissions declined significantly during the reporting period (see Annex A.)"
    )


def test_sentence_with_exclamation_passes():
    assert is_sentence_quality(
        "Our sustainability commitments were independently verified and certified!"
    )


def test_sentence_with_question_passes():
    assert is_sentence_quality(
        "How does the company manage its environmental and social responsibilities?"
    )


def test_sentence_with_a_few_acronyms_passes():
    # ESG, GHG are ALL CAPS but 2 of 12 = 17% < 50%
    assert is_sentence_quality(
        "Our ESG and GHG reporting follows internationally recognised frameworks and standards."
    )


# ---------------------------------------------------------------------------
# is_sentence_quality — negative cases
# ---------------------------------------------------------------------------

def test_starts_lowercase_fails():
    assert not is_sentence_quality(
        "the company disclosed its environmental performance in the annual report."
    )


def test_no_terminal_punctuation_fails():
    assert not is_sentence_quality(
        "The company disclosed its environmental performance in the annual report"
    )


def test_ends_with_comma_fails():
    assert not is_sentence_quality(
        "The company disclosed its environmental performance in the annual report,"
    )


def test_ends_with_colon_fails():
    assert not is_sentence_quality(
        "The company disclosed its environmental performance in the annual report:"
    )


def test_too_few_words_fails():
    # Exactly 7 words
    assert not is_sentence_quality("Board governance audit committee annual review.")


def test_exactly_eight_words_passes():
    assert is_sentence_quality(
        "The board reviewed all governance policies and procedures."
    )


def test_all_caps_majority_fails():
    # 6 of 8 words are ALL CAPS => 75% >= 50%
    assert not is_sentence_quality(
        "BOARD GOVERNANCE AUDIT COMMITTEE ANNUAL REVIEW POLICY STATEMENT."
    )


def test_all_caps_exactly_50pct_fails():
    # 4 of 8 words ALL CAPS => 50% >= 50%
    assert not is_sentence_quality(
        "BOARD GOVERNANCE COMMITTEE ANNUAL review policy framework statement."
    )


def test_all_caps_below_50pct_passes():
    # 3 of 9 = 33% < 50%
    assert is_sentence_quality(
        "The BOARD GOVERNANCE COMMITTEE met quarterly and reviewed all policy statements."
    )


def test_high_non_letter_ratio_fails():
    # Numbers and symbols dominate: "2.3 | 14.7 | 22.1 | 8.4 | 99.0 | 1.2 | 3.4 | 0.9."
    assert not is_sentence_quality(
        "2.3 | 14.7 | 22.1 | 8.4 | 99.0 | 1.2 | 3.4 | 0.9."
    )


def test_sentence_with_numbers_in_context_passes():
    # A normal sentence mentioning a year and percentage — should pass
    assert is_sentence_quality(
        "In 2023 the company achieved a reduction of fifteen percent in total emissions."
    )


def test_empty_string_fails():
    assert not is_sentence_quality("")


def test_whitespace_only_fails():
    assert not is_sentence_quality("   ")


# ---------------------------------------------------------------------------
# filter_sentences
# ---------------------------------------------------------------------------

def test_filter_removes_heading():
    heading = Sentence(page_number=1, text="BOARD GOVERNANCE AUDIT COMMITTEE.")
    good = Sentence(
        page_number=2,
        text="The board reviewed all governance and sustainability policies annually.",
    )
    result = filter_sentences([heading, good])
    assert result == [good]


def test_filter_empty_list():
    assert filter_sentences([]) == []


def test_filter_all_pass():
    sents = [
        Sentence(1, "The company reduced its greenhouse gas emissions by fifteen percent."),
        Sentence(2, "Environmental targets are reviewed and updated each financial year."),
    ]
    assert filter_sentences(sents) == sents


def test_filter_all_fail():
    sents = [
        Sentence(1, "HEADING LABEL ENTRY."),
        Sentence(2, "short sentence."),
    ]
    assert filter_sentences(sents) == []


def test_filter_preserves_order():
    sents = [
        Sentence(1, "HEADING ONLY."),
        Sentence(2, "The board approved the sustainability framework and reviewed key ESG metrics."),
        Sentence(3, "no capital and no terminal"),
        Sentence(4, "Governance disclosures are aligned with internationally recognised reporting standards."),
    ]
    result = filter_sentences(sents)
    assert len(result) == 2
    assert result[0].page_number == 2
    assert result[1].page_number == 4
