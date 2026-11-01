"""
Light cleanup + sentence segmentation on top of raw extracted page text.
Sentence-level granularity is what lets the matcher capture evidence
("show me the sentence this term came from") rather than just a count.
"""
import re
from dataclasses import dataclass

import spacy

from app.config import settings

# Terminal-punctuation pattern for the sentence quality filter.
# Allows an optional closing bracket/quote (ASCII or Unicode) after the mark.
_TERMINAL_PUNCT = re.compile(r'[.!?][)\]"\'"”»]?\s*$')

_nlp = None


def get_nlp():
    """Lazy-load the spaCy pipeline (expensive to init, so do it once)."""
    global _nlp
    if _nlp is None:
        _nlp = spacy.load(settings.spacy_model, disable=["ner", "parser"])
        _nlp.enable_pipe("senter") if "senter" in _nlp.pipe_names else _nlp.add_pipe("sentencizer")
    return _nlp


@dataclass
class Sentence:
    page_number: int
    text: str


_BOILERPLATE_PATTERNS = [
    re.compile(r"^\s*page\s+\d+\s*(of\s+\d+)?\s*$", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*$"),  # bare page numbers
]


def clean_page_text(text: str) -> str:
    lines = text.splitlines()
    kept = [
        line for line in lines
        if not any(pat.match(line.strip()) for pat in _BOILERPLATE_PATTERNS)
    ]
    return "\n".join(kept)


def segment_sentences(pages) -> list[Sentence]:
    """pages: list[PageText] from pdf_extraction. Returns flattened sentences with page refs."""
    nlp = get_nlp()
    sentences: list[Sentence] = []

    for page in pages:
        cleaned = clean_page_text(page.text)
        if not cleaned.strip():
            continue
        doc = nlp(cleaned)
        for sent in doc.sents:
            s = sent.text.strip()
            if len(s) > 3:  # skip stray fragments/whitespace
                sentences.append(Sentence(page_number=page.page_number, text=s))

    return sentences


def is_sentence_quality(text: str) -> bool:
    """Return True if the sentence passes the v0.4.2 quality filter.

    Rules (Ferjancic et al. 2024):
    1. Starts with a capital letter.
    2. Ends with . ! ? (optional closing bracket/quote allowed after).
    3. At least 8 words.
    4. Fewer than 50% of words are ALL CAPS (length > 1, all-alpha-upper).
    5. Fewer than 30% of characters are non-letter.
    """
    s = text.strip()
    if not s:
        return False
    if not s[0].isupper():
        return False
    if not _TERMINAL_PUNCT.search(s):
        return False
    words = s.split()
    n = len(words)
    if n < 8:
        return False
    allcaps = sum(
        1 for w in words
        if len(w) > 1 and w.isalpha() and w.upper() == w
    )
    if allcaps / n >= 0.50:
        return False
    total_chars = len(s)
    non_letter = sum(1 for c in s if not c.isalpha())
    return not non_letter / total_chars >= 0.30


def filter_sentences(sentences: list[Sentence]) -> list[Sentence]:
    """Return only sentences that pass is_sentence_quality (pipeline 0.4.2)."""
    return [s for s in sentences if is_sentence_quality(s.text)]
