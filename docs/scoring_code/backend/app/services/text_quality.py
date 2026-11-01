"""Text-quality switches applied between PDF extraction and matching.

Each switch is independently toggleable from config/verity.toml and each
emits per-report audit numbers that end up in Report fields and in
docs/PROCESSING_QA.md. All functions here are pure: given the extracted
pages, return (new_pages, metadata). Nothing is read from disk; nothing
is written to the DB; the pipeline module is what wires them together.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

from app.services.pdf_extraction import PageText

# --------------------------------------------------------------------------- #
# a) Repeated header / footer removal.
#
# A running header/footer is any line that appears on at least
# `header_footer_repeat_ratio` of the pages (default 30%). To collapse
# "Page 1 of 113" and "Page 2 of 113" into the same line, we digit-normalise
# before hashing: all digit runs become "#". A removed line's original form
# is still logged for traceability.
# --------------------------------------------------------------------------- #

_DIGIT_RUN_RX = re.compile(r"\d+")
_WS_RX = re.compile(r"\s+")
_LETTER_RX = re.compile(r"[^\W\d_]", re.UNICODE)  # any Unicode letter


def _normalise_line(line: str) -> str:
    s = _DIGIT_RUN_RX.sub("#", line.strip())
    s = _WS_RX.sub(" ", s).lower()
    return s


def _is_dedup_candidate(normalised: str) -> bool:
    """True when the normalised line is worth considering for repeat-removal.

    Must contain at least one Unicode letter. A line that normalises to
    just digit-placeholders, separators and punctuation (e.g. '#', '#,#',
    '-', '# | #') is almost always a bare page number, table cell or
    separator glyph — the removal is harmless to scoring (density counts
    only Latin-letter tokens) but inflating `repeated_lines_removed` with
    thousands of them makes the audit telemetry useless. Session 5
    bank-muscat FY2025: 9,483 'removals' were really ~400 running
    headers plus ~9,000 isolated numeric table cells; this gate restores
    the number to the ~400 that actually represents boilerplate.
    """
    return bool(_LETTER_RX.search(normalised))


def remove_repeated_header_footer(
    pages: list[PageText], min_ratio: float
) -> tuple[list[PageText], int]:
    """Drop lines whose digit-normalised form appears on ≥ min_ratio of
    pages. Returns (new_pages, lines_removed_count).

    A single page would otherwise keep everything (no "repeat" possible).
    """
    if len(pages) < 2 or min_ratio <= 0:
        return pages, 0

    # Which pages (by index) does each normalised line appear on? A line
    # appearing twice on the same page still counts as one page. Lines
    # whose normalised form has no letters are excluded from the dedup
    # pool entirely (see _is_dedup_candidate for the rationale).
    line_pages: dict[str, set[int]] = {}
    for i, page in enumerate(pages):
        for raw in page.text.splitlines():
            norm = _normalise_line(raw)
            if not norm or not _is_dedup_candidate(norm):
                continue
            line_pages.setdefault(norm, set()).add(i)

    threshold = max(2, round(min_ratio * len(pages)))
    repeated = {norm for norm, idx_set in line_pages.items() if len(idx_set) >= threshold}
    if not repeated:
        return pages, 0

    cleaned: list[PageText] = []
    total_removed = 0
    for page in pages:
        kept_lines: list[str] = []
        for raw in page.text.splitlines():
            if _normalise_line(raw) in repeated and raw.strip():
                total_removed += 1
                continue
            kept_lines.append(raw)
        cleaned.append(PageText(
            page_number=page.page_number,
            text="\n".join(kept_lines),
            used_ocr=page.used_ocr,
        ))
    return cleaned, total_removed


# --------------------------------------------------------------------------- #
# b) Contents / index page detection.
#
# A contents page tends to:
#   * have many short lines ending in a page number,
#   * use dot leaders (". . . . ." or "..........") between a label and the
#     page number,
#   * list "GRI content index" / "SASB index" sections,
#   * sit near the front of the report (first ~15% of pages).
#
# We flag a page as a contents page when it hits ANY of:
#   - ≥ 6 lines ending in a 1-3 digit number AND ≥ 40% of its non-empty lines
#     end that way (dense page-number column),
#   - a dot leader on at least 4 lines (strong signal),
#   - an index-table marker in the first few lines.
# --------------------------------------------------------------------------- #

_LINE_END_NUM_RX = re.compile(r"\s(\d{1,3})\s*$")
_DOT_LEADER_RX = re.compile(r"\.{4,}|\.(?:\s*\.){3,}")
_INDEX_HEADERS = (
    "table of contents",
    "contents",
    "gri content index",
    "gri index",
    "sasb index",
    "sasb content index",
    "index",
)


def _page_looks_like_contents(text: str) -> bool:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False
    # Index-table header check (first 6 non-empty lines). Only accept
    # header-based detection if the page also looks "indexy": at least 3
    # lines ending in a page number. Avoids tripping on a chapter title
    # that happens to be "Contents".
    head_lo = "\n".join(lines[:6]).lower()
    header_hit = any(h in head_lo for h in _INDEX_HEADERS)
    if header_hit and sum(1 for ln in lines if _LINE_END_NUM_RX.search(ln)) >= 3:
        return True
    # Dot-leader check.
    dot_leader_hits = sum(1 for ln in lines if _DOT_LEADER_RX.search(ln))
    if dot_leader_hits >= 4:
        return True
    # Dense page-number column.
    numeric_tail_hits = sum(1 for ln in lines if _LINE_END_NUM_RX.search(ln))
    return numeric_tail_hits >= 6 and numeric_tail_hits / max(1, len(lines)) >= 0.40


def detect_contents_pages(pages: list[PageText]) -> list[int]:
    """Return 1-indexed page numbers that look like contents / index pages."""
    if not pages:
        return []
    # Scan the first ~15% of the report but at least the first 10 pages.
    scan_upto = max(10, round(0.15 * len(pages)))
    out: list[int] = []
    for p in pages[:scan_upto]:
        if _page_looks_like_contents(p.text):
            out.append(p.page_number)
    return out


# --------------------------------------------------------------------------- #
# c) Latin-only denominator — Session 1. The actual Latin/Arabic word count
# lives in pdf_extraction.count_words; this module only exposes a helper
# that counts how many pages are MOSTLY Arabic, for the audit column.
# --------------------------------------------------------------------------- #

_LATIN_LETTER_RX = re.compile(r"[A-Za-z]")
_ARABIC_LETTER_RX = re.compile(r"[؀-ۿݐ-ݿ]")


def count_pages_mostly_arabic(pages: list[PageText], ratio: float) -> int:
    """Count how many pages have > `ratio` of their script tokens Arabic.

    Script tokens = tokens that have at least one letter (Latin or Arabic).
    Pure-digit / punctuation tokens don't vote.
    """
    n = 0
    for page in pages:
        latin = 0
        arabic = 0
        for tok in page.text.split():
            if _LATIN_LETTER_RX.search(tok):
                latin += 1
            elif _ARABIC_LETTER_RX.search(tok):
                arabic += 1
        total = latin + arabic
        if total and (arabic / total) > ratio:
            n += 1
    return n


# --------------------------------------------------------------------------- #
# e) Financial-statements boundary detection.
#
# The first page whose text contains ANY of the configured boundary markers
# is treated as the start of the financial statements section. Everything
# from that page onward is excluded from matching. Markers are compared
# against text that has been NFKC-normalised (so Arabic presentation
# forms collapse to normal letters) and lowercased.
# --------------------------------------------------------------------------- #


def _norm(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower()


def detect_financial_statements_start(
    pages: list[PageText], markers: list[str]
) -> int | None:
    """Return the 1-indexed page number where the FS section starts, or None.

    We only start scanning after 25% of the report has elapsed — the auditor's
    report wording also appears in table-of-contents entries near the front
    and in forward-looking statements. 25% is a conservative floor that
    still catches genuine FS sections, which almost always sit in the back
    half of the document.
    """
    if not pages or not markers:
        return None
    norm_markers = [_norm(m) for m in markers]
    start_idx = max(0, int(0.25 * len(pages)))
    for p in pages[start_idx:]:
        nt = _norm(p.text)
        if any(m in nt for m in norm_markers):
            return p.page_number
    return None


def exclude_pages_from(pages: list[PageText], from_page: int) -> list[PageText]:
    """Drop every page whose page_number is >= from_page. Returns the kept
    pages — the caller tracks how many were excluded separately.
    """
    return [p for p in pages if p.page_number < from_page]


# --------------------------------------------------------------------------- #
# Convenience: full cleaner that applies every switch per config and returns
# both cleaned pages and the audit numbers the pipeline needs.
# --------------------------------------------------------------------------- #


@dataclass
class CleanedPages:
    pages: list[PageText]
    repeated_lines_removed: int = 0
    excluded_contents_pages: list[int] = field(default_factory=list)
    pages_mostly_arabic: int = 0
    financial_statements_start_page: int | None = None
    financial_statements_excluded_pages: int = 0


def apply_text_quality(pages: list[PageText], cfg) -> CleanedPages:
    """Apply every enabled switch in the right order and return a CleanedPages
    with the audit numbers that end up on Report.
    """
    result = CleanedPages(pages=pages)
    result.pages_mostly_arabic = count_pages_mostly_arabic(
        pages, cfg.arabic_page_token_ratio
    )

    # a) Headers/footers first — they're the noisiest.
    if cfg.exclude_repeated_lines:
        result.pages, result.repeated_lines_removed = remove_repeated_header_footer(
            result.pages, cfg.header_footer_repeat_ratio
        )

    # b) Contents pages: detect, then DROP them from the kept list.
    if cfg.exclude_toc_pages:
        toc_nums = detect_contents_pages(result.pages)
        result.excluded_contents_pages = toc_nums
        if toc_nums:
            toc_set = set(toc_nums)
            result.pages = [p for p in result.pages if p.page_number not in toc_set]

    # e) Financial-statements boundary.
    if cfg.exclude_financial_statement_pages:
        fs_start = detect_financial_statements_start(
            result.pages, cfg.financial_statement_boundary_markers
        )
        if fs_start is not None:
            result.financial_statements_start_page = fs_start
            before = len(result.pages)
            result.pages = exclude_pages_from(result.pages, fs_start)
            result.financial_statements_excluded_pages = before - len(result.pages)

    return result


# --------------------------------------------------------------------------- #
# OCR pre-check. Rasterising and OCR-ing hundreds of pages is slow. Before
# the pipeline commits to it, cheap-scan every page for native text and
# compute the fraction that would need OCR. If that fraction exceeds
# config.ocr_max_page_ratio, the pipeline marks the report "heavily scanned"
# and skips OCR entirely (sets review_status=needs_review).
# --------------------------------------------------------------------------- #


def estimate_ocr_fraction(source: str | bytes, char_threshold: int) -> tuple[float, int]:
    """Open the PDF with pymupdf and return (ocr_fraction, total_pages).

    ocr_fraction = share of pages whose native text yield is below the
    char threshold (same test extract_pdf_pages uses to trigger OCR).
    Does NOT render or OCR anything.

    Accepts a path (legacy / dev) or bytes (Session 9 R2 path).
    """
    import pymupdf
    if isinstance(source, (bytes, bytearray)):
        doc = pymupdf.open(stream=bytes(source), filetype="pdf")
    else:
        doc = pymupdf.open(source)
    try:
        total = doc.page_count
        if total == 0:
            return 0.0, 0
        would_ocr = 0
        for i in range(total):
            try:
                txt = doc[i].get_text("text") or ""
            except Exception:
                txt = ""
            if len(txt.strip()) < char_threshold:
                would_ocr += 1
        return would_ocr / total, total
    finally:
        doc.close()


# --------------------------------------------------------------------------- #
# Repeated-line and contents detection are also used by test fixtures as a
# way to show the switch's effect; export a diagnostic that just lists what
# repeat-group each line falls into without actually removing anything.
# --------------------------------------------------------------------------- #


def repeated_line_report(pages: list[PageText], min_ratio: float) -> Counter:
    """Diagnostic: Counter of normalised_line -> number of pages it appears on,
    filtered to those meeting the repeat threshold. Used by tests to prove
    the switch catches what the config says it should.
    """
    counts: Counter = Counter()
    pageset: dict[str, set[int]] = {}
    for i, p in enumerate(pages):
        for raw in p.text.splitlines():
            n = _normalise_line(raw)
            if n and _is_dedup_candidate(n):
                pageset.setdefault(n, set()).add(i)
    threshold = max(2, round(min_ratio * len(pages)))
    for n, idxs in pageset.items():
        if len(idxs) >= threshold:
            counts[n] = len(idxs)
    return counts
