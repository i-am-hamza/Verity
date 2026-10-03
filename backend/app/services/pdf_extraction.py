"""
PDF -> per-page text extraction.

Strategy:
1. Try native text extraction (PyMuPDF) — fast, accurate, works for
   digitally-produced annual reports (the majority of large-institution PDFs).
2. If a page yields almost no text, assume it's a scanned image and fall
   back to OCR (Tesseract) on a rasterized version of that page.

This mixed strategy matters for this domain specifically: MENA annual
reports are often bilingual (Arabic/English) and older filings are
sometimes scanned rather than digitally typeset.
"""
from __future__ import annotations

import io
import os
import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image

from app.config import settings

_ocr_configured = False

# Any Latin letter A-Z anywhere in a whitespace-separated token = Latin token.
# Any Arabic-block letter (U+0600..U+06FF, U+0750..U+077F) present with no
# Latin letters = Arabic token. Tokens with neither (bare numbers,
# punctuation) are ignored: they can't push English density either way.
_LATIN_LETTER = re.compile(r"[A-Za-z]")
_ARABIC_LETTER = re.compile(r"[؀-ۿݐ-ݿ]")


def _configure_ocr() -> None:
    """Point pytesseract at the configured executable and tessdata dir once."""
    global _ocr_configured
    if _ocr_configured:
        return
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    if settings.tessdata_prefix:
        os.environ["TESSDATA_PREFIX"] = str(settings.tessdata_prefix)
    _ocr_configured = True


@dataclass
class PageText:
    page_number: int  # 1-indexed
    text: str
    used_ocr: bool


@dataclass
class WordCounts:
    latin: int
    arabic: int

    @property
    def total(self) -> int:
        return self.latin + self.arabic


def extract_pdf_pages(source: str | Path | bytes) -> list[PageText]:
    """Open a PDF and return per-page text.

    `source` can be a local path (legacy / dev) or raw bytes (the Session
    9 production path, where PDFs live in R2 and the pipeline hands
    bytes straight from `read_pdf_bytes` to pymupdf). pymupdf.open takes
    `stream=` for in-memory bytes which avoids a tempfile round-trip.
    """
    _configure_ocr()

    if isinstance(source, (bytes, bytearray)):
        doc = pymupdf.open(stream=bytes(source), filetype="pdf")
    else:
        doc = pymupdf.open(str(source))
    pages: list[PageText] = []

    for i, page in enumerate(doc, start=1):
        native_text = page.get_text("text").strip()

        if len(native_text) >= settings.ocr_trigger_char_threshold:
            pages.append(PageText(page_number=i, text=native_text, used_ocr=False))
            continue

        # Likely a scanned page — rasterize and OCR it. Latin+Arabic by default
        # (settings.ocr_langs) because MENA annual reports are commonly bilingual.
        # Tesseract picks up the data dir from TESSDATA_PREFIX (set in _configure_ocr).
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr_text = pytesseract.image_to_string(img, lang=settings.ocr_langs).strip()
        pages.append(PageText(page_number=i, text=ocr_text, used_ocr=True))

    doc.close()
    return pages


def count_words(pages: list[PageText]) -> WordCounts:
    """Split every page on whitespace, then bucket tokens by script.

    Rule: any Latin letter in the token wins Latin (handles "GRI300"); no
    Latin letters but at least one Arabic letter wins Arabic; anything else
    (bare numbers, punctuation, whitespace) is dropped.
    """
    latin = 0
    arabic = 0
    for page in pages:
        for token in page.text.split():
            if _LATIN_LETTER.search(token):
                latin += 1
            elif _ARABIC_LETTER.search(token):
                arabic += 1
    return WordCounts(latin=latin, arabic=arabic)


def total_word_count(pages: list[PageText]) -> int:
    """Historic API — total tokens (Latin + Arabic), not used for density.

    Kept for callers that just want a rough size figure. Scoring density
    goes through count_words().latin instead (CLAUDE.md, Method).
    """
    return sum(len(p.text.split()) for p in pages)
