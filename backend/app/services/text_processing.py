"""
Light cleanup + sentence segmentation on top of raw extracted page text.
Sentence-level granularity is what lets the matcher capture evidence
("show me the sentence this term came from") rather than just a count.
"""
import re
from dataclasses import dataclass

import spacy

from app.config import settings

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
