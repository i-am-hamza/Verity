"""Validate a downloaded PDF before it counts as a successful fetch.

Returns a Validation struct the pipeline uses to decide review_status
and whether to write a gap row. Never raises on bad input — a corrupt
PDF or a non-PDF body is a validation outcome, not an exception.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

import pymupdf

from app.crawler.config import MIN_ANNUAL_REPORT_PAGES, MIN_PDF_BYTES

# Report-type phrases that live in page text or filename.
#
# Arabic equivalents matter because many ME banks publish Arabic editions on
# the same IR page; Wayback often captures those alongside the English PDFs.
# Arabic word boundaries are tricky (no spaces inside compound words), so
# the regexes allow the Arabic definite article prefix "ال" ("the") to be
# optional and admit a single intervening whitespace.
_SUSTAINABILITY_RX = re.compile(
    r"sustainability\s+report|تقرير\s*ال?استدامة",
    re.IGNORECASE,
)
_INTEGRATED_RX = re.compile(
    r"integrated\s+(annual\s+)?report|ال?تقرير\s*ال?متكامل",
    re.IGNORECASE,
)
_FINANCIAL_RX = re.compile(
    r"(financial\s+statements|consolidated\s+financial)"
    r"|ال?(?:قوائم|بيانات)\s*ال?مالية",
    re.IGNORECASE,
)
_ANNUAL_RX = re.compile(
    r"annual\s+report|ال?تقرير\s*ال?سنوي",
    re.IGNORECASE,
)

# Independent auditor's report signature. Corporate PDFs sometimes typeset
# the apostrophe as the Unicode smart quote U+2019; the regex admits both
# via the alternation. The escape form avoids a literal U+2019 in source,
# which keeps ruff's ambiguous-character rule happy.
_SMART_APOS = chr(0x2019)
_AUDITOR_RX = re.compile(
    "independent\\s+auditor(?:'|" + _SMART_APOS + ")?s\\s+report"
    "|report\\s+of\\s+the\\s+independent\\s+auditor",
    re.IGNORECASE,
)

# "annual report 2023", "for the year ended 31 December 2023", "fiscal year 2023".
_YEAR_FROM_TEXT_RX = re.compile(
    r"(?:annual\s+report|for\s+the\s+(?:fiscal\s+)?year\s+ended\s+\d+\s+\w+|fiscal\s+year)\s+(20\d{2})",
    re.IGNORECASE,
)
_PLAIN_YEAR_RX = re.compile(r"(20\d{2})")


@dataclass
class Validation:
    ok: bool
    sha256: str
    byte_count: int
    page_count: int | None
    report_type: str  # "annual" | "integrated" | "sustainability" | "financial_statements" | "other" | "unknown"
    includes_financial_statements: bool | None
    inferred_year: int | None
    reason: str | None = None  # populated when ok=False
    review_status: str = "auto_ok"  # "auto_ok" | "needs_review" | "rejected"


def _hash(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _detect_report_type(filename: str, head_text: str) -> str:
    # Priority order: annual > integrated > sustainability > financial.
    # Session 6 finding (NBB, Maaden): a cover that mentions BOTH "Annual
    # Report" and "Sustainability Report" previously classified as
    # sustainability (first-match-wins order was Sust → Int → Annual).
    # Real annual reports often lead with sustainability wording on the
    # cover; the filename is "Annual Report" and the body is a full AR.
    # Annual therefore takes precedence; the earlier ambiguity is resolved
    # in favour of the stricter scoring type.
    hay = f"{filename}\n{head_text}"
    if _ANNUAL_RX.search(hay):
        return "annual"
    if _INTEGRATED_RX.search(hay):
        return "integrated"
    if _SUSTAINABILITY_RX.search(hay):
        return "sustainability"
    if _FINANCIAL_RX.search(hay):
        return "financial_statements"
    return "unknown"


def _detect_year_in_text(text: str) -> int | None:
    # Prefer the explicit "annual report / fiscal year / year ended .. 20NN"
    # pattern over a bare 20NN which appears everywhere in a financial PDF.
    m = _YEAR_FROM_TEXT_RX.search(text)
    if m:
        return int(m.group(1))
    # Last-resort: find the latest-looking 20NN in the first 1500 chars.
    candidates = {int(y) for y in _PLAIN_YEAR_RX.findall(text[:1500])}
    if candidates:
        plausible = [y for y in candidates if 2010 <= y <= 2030]
        if plausible:
            return max(plausible)
    return None


def _detect_structured_year(text: str) -> int | None:
    """Return the year from a clear reporting-period phrase only.

    Uses _YEAR_FROM_TEXT_RX (patterns like "Annual Report 2023" or
    "for the year ended 31 December 2023"). Returns None if no such
    phrase is found — bare 20XX occurrences such as "Vision 2030" are
    not a stated reporting period and must not trigger the mismatch flag.
    """
    m = _YEAR_FROM_TEXT_RX.search(text)
    return int(m.group(1)) if m else None


def validate_pdf(body: bytes, *, source_filename: str, expected_year: int | None) -> Validation:
    sha = _hash(body)
    size = len(body)

    # Shape checks.
    if size < MIN_PDF_BYTES:
        return Validation(ok=False, sha256=sha, byte_count=size, page_count=None,
                          report_type="unknown", includes_financial_statements=None,
                          inferred_year=None, reason=f"too small: {size} < {MIN_PDF_BYTES}",
                          review_status="rejected")
    if not body.startswith(b"%PDF"):
        return Validation(ok=False, sha256=sha, byte_count=size, page_count=None,
                          report_type="unknown", includes_financial_statements=None,
                          inferred_year=None, reason="body does not start with %PDF",
                          review_status="rejected")

    try:
        doc = pymupdf.open(stream=body, filetype="pdf")
    except Exception as exc:
        return Validation(ok=False, sha256=sha, byte_count=size, page_count=None,
                          report_type="unknown", includes_financial_statements=None,
                          inferred_year=None, reason=f"pymupdf open failed: {exc}",
                          review_status="rejected")

    try:
        page_count = doc.page_count
        head_text_chunks: list[str] = []
        for i in range(min(3, page_count)):
            try:
                head_text_chunks.append(doc[i].get_text("text") or "")
            except Exception:
                head_text_chunks.append("")
        head_text = "\n".join(head_text_chunks)
        # Scan the whole doc only for the auditor's-report marker; it's
        # usually in the back half, not in the first 3 pages.
        full_text_for_scan = "\n".join(
            (doc[i].get_text("text") or "") for i in range(page_count)
        )
    finally:
        doc.close()

    report_type = _detect_report_type(source_filename, head_text)
    includes_fs = bool(_AUDITOR_RX.search(full_text_for_scan))
    inferred_year = _detect_year_in_text(head_text)

    # Thresholds / review classification.
    review = "auto_ok"
    reason: str | None = None

    if report_type in ("annual", "integrated") and page_count < MIN_ANNUAL_REPORT_PAGES:
        review = "needs_review"
        reason = (f"{report_type} report but only {page_count} pages "
                  f"(< {MIN_ANNUAL_REPORT_PAGES}); may be a summary / highlights")

    if report_type == "unknown":
        review = "needs_review"
        reason = reason or "report_type unknown from filename and first 3 pages"

    # Year check: if the document's cover text contains a clear reporting-period
    # phrase ("Annual Report YYYY", "for the year ended DD Month YYYY", etc.) and
    # its year differs from expected_year, flag for review with evidence.
    #
    # Only _YEAR_FROM_TEXT_RX matches (structured phrases) trigger the flag.
    # Plain 20XX occurrences — "Vision 2030", comparative-column headers,
    # chairman anecdotes — are not a stated reporting period and do not fire.
    # The previous window-based suppression (in-window → never flag) is removed:
    # a genuine cover-page mislabel should be caught regardless of which year
    # the filename claims.
    structured_year = _detect_structured_year(head_text)
    if (
        expected_year is not None
        and structured_year is not None
        and expected_year != structured_year
    ):
        review = "needs_review"
        yr_note = (
            f"year mismatch: document says FY{structured_year}, "
            f"assigned FY{expected_year}"
        )
        reason = f"{reason}; {yr_note}" if reason else yr_note

    return Validation(
        ok=True, sha256=sha, byte_count=size, page_count=page_count,
        report_type=report_type, includes_financial_statements=includes_fs,
        inferred_year=inferred_year, reason=reason,
        review_status="needs_review" if review == "needs_review" else "auto_ok",
    )
