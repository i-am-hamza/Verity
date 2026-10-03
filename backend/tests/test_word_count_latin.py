"""
Density denominator must count Latin-script tokens only.

The taxonomy is English-only for now. If a bilingual annual report has half
its page count in Arabic, letting Arabic tokens inflate the denominator would
artificially lower the disclosure score — the report wouldn't be scored on
what a reader looking for ESG language could actually read.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pdf_extraction import PageText, count_words


def test_count_words_returns_latin_and_arabic_separately():
    pages = [
        PageText(
            page_number=1,
            text="Corporate governance framework and disclosure practices.",
            used_ocr=False,
        ),
        # Arabic-only page (verbatim: "Corporate governance annual report").
        PageText(page_number=2, text="حوكمة الشركات التقرير السنوي", used_ocr=False),
    ]
    counts = count_words(pages)
    assert counts.latin == 6, f"expected 6 Latin tokens, got {counts.latin}"
    assert counts.arabic == 4, f"expected 4 Arabic tokens, got {counts.arabic}"


def test_mixed_token_counts_as_latin_when_it_has_any_latin_letters():
    """A bilingual number like '2023م' (Arabic year suffix) has zero Latin
    letters, so it's Arabic. But an English/Arabic sandwich like 'GRI300'
    counts as Latin. This test locks the "any Latin letter -> Latin" rule."""
    pages = [PageText(page_number=1, text="GRI300 ٢٠٢٣ ICOFR سنوي", used_ocr=False)]
    counts = count_words(pages)
    assert counts.latin == 2  # GRI300, ICOFR
    assert counts.arabic == 2  # numeric-arabic ٢٠٢٣ + سنوي


def test_purely_numeric_and_punctuation_ignored_in_both_scripts():
    pages = [PageText(page_number=1, text="2023 -- 3.5% ,,,", used_ocr=False)]
    counts = count_words(pages)
    assert counts.latin == 0
    assert counts.arabic == 0
