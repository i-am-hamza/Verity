"""PDF validator tests. PDFs are generated inside each test with
PyMuPDF — no live data dependency and no fixture binaries.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.crawler.validate import validate_pdf


def _make_pdf(first_page_text: str, *, pages: int = 40, auditor_marker: bool = False) -> bytes:
    """Build a PDF of `pages` pages with enough unique text per page that
    even a 10-pager clears the 100 KB validator floor.
    """
    doc = pymupdf.open()
    first = doc.new_page(width=612, height=792)
    first.insert_text((72, 72), first_page_text, fontsize=11)
    for i in range(pages - 1):
        p = doc.new_page(width=612, height=792)
        # ~90 rows x ~140 unique chars = ~12 KB raw per page before compression.
        for row in range(90):
            p.insert_text((72, 54 + row * 8), f"page{i:03d}-row{row:03d} " * 14, fontsize=6)
    if auditor_marker:
        p = doc.new_page(width=612, height=792)
        p.insert_text(
            (72, 72),
            "Independent Auditor's Report\nTo the shareholders of ACME ...",
            fontsize=10,
        )
    buf = io.BytesIO()
    doc.save(buf, deflate=True)
    doc.close()
    return buf.getvalue()


def test_rejects_body_that_doesnt_start_with_pdf_magic():
    body = b"<!doctype html><html>oops</html>" * 10_000  # >100KB
    v = validate_pdf(body, source_filename="x.pdf", expected_year=2023)
    assert not v.ok
    assert "%PDF" in (v.reason or "")
    assert v.review_status == "rejected"


def test_rejects_too_small_pdf():
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "tiny")
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    body = buf.getvalue()
    v = validate_pdf(body, source_filename="x.pdf", expected_year=2023)
    assert not v.ok
    assert v.review_status == "rejected"
    assert "too small" in (v.reason or "")


def test_rejects_corrupt_pdf():
    body = b"%PDF-1.4\n" + b"X" * 200_000
    v = validate_pdf(body, source_filename="x.pdf", expected_year=2023)
    assert not v.ok
    assert "pymupdf open failed" in (v.reason or "")


def test_classifies_integrated_annual_report_prefers_annual_over_integrated():
    """Session 6 priority change: when both 'Annual Report' and
    'Integrated Report' match in the first-three-pages text, 'annual'
    wins. See the comment in _detect_report_type — real annual reports
    often lead with 'Integrated / Sustainability' wording on the cover
    but are structurally annual reports, so the stricter scoring
    classification (annual) is preferred."""
    body = _make_pdf(
        "ACME CORP\nIntegrated Annual Report 2023\nFor the year ended 31 December 2023",
        pages=45,
    )
    v = validate_pdf(body, source_filename="acme_integrated_annual_report_2023.pdf",
                     expected_year=2023)
    assert v.ok, v.reason
    assert v.report_type == "annual"
    assert v.inferred_year == 2023
    assert v.review_status == "auto_ok"
    assert v.page_count and v.page_count >= 30


def test_flags_short_annual_report_as_needs_review():
    body = _make_pdf("ACME CORP\nAnnual Report 2024", pages=10)
    v = validate_pdf(body, source_filename="acme_annual_report_2024.pdf", expected_year=2024)
    assert v.ok
    assert v.report_type == "annual"
    assert v.review_status == "needs_review"
    assert "pages" in (v.reason or "")


def test_detects_auditors_report_marker_sets_includes_financial_statements():
    body = _make_pdf(
        "ACME CORP\nAnnual Report 2022\nFor the year ended 31 December 2022",
        pages=40,
        auditor_marker=True,
    )
    v = validate_pdf(body, source_filename="acme_annual_report_2022.pdf", expected_year=2022)
    assert v.ok
    assert v.includes_financial_statements is True


def test_year_mismatch_marks_needs_review_when_expected_outside_window():
    """Mismatch flag still fires when the caller's expected_year is NOT
    in the configured reporting window — in that case the filename isn't
    treated as authoritative, so a body-year disagreement still means
    needs_review."""
    body = _make_pdf(
        "ACME CORP\nAnnual Report 2022\nFor the year ended 31 December 2022",
        pages=40,
    )
    # expected_year=2015 is well outside the 2020-2025 window.
    v = validate_pdf(body, source_filename="acme_annual_report.pdf", expected_year=2015)
    assert v.ok, v.reason
    assert v.inferred_year == 2022
    assert v.review_status == "needs_review"


def test_stray_year_in_body_does_not_trigger_mismatch():
    """A plain 20XX occurrence such as 'Vision 2030' in body text must not
    flag needs_review. Only structured phrases ('Annual Report YYYY',
    'for the year ended DD Month YYYY') count as a stated reporting period.
    The mismatch check uses _detect_structured_year, not the plain fallback."""
    body = _make_pdf(
        "ACME CORP\n"
        "Saudi Arabia remains committed to Vision 2030 for sustainable development.",
        pages=40,
    )
    v = validate_pdf(body, source_filename="acme annual report 2024.pdf",
                     expected_year=2024)
    assert v.ok, v.reason
    assert v.inferred_year == 2030   # plain fallback still returns 2030
    assert v.review_status == "auto_ok"  # no structured year found → no mismatch


def test_year_mismatch_within_window_now_flagged():
    """The previous window-based suppression (in-window years → never flag)
    is removed. A document whose cover text clearly states 'Annual Report 2022'
    but is assigned FY2023 is flagged needs_review, even though both years
    are inside the 2020-2025 scoring window."""
    body = _make_pdf(
        "ACME CORP\nAnnual Report 2022\nFor the year ended 31 December 2022",
        pages=40,
    )
    v = validate_pdf(body, source_filename="acme_annual_report.pdf", expected_year=2023)
    assert v.ok, v.reason
    assert v.inferred_year == 2022
    assert v.review_status == "needs_review"
    assert v.reason is not None
    assert "2022" in v.reason and "2023" in v.reason


def test_year_match_within_window_is_auto_ok():
    """Document cover text matches assigned year → auto_ok."""
    body = _make_pdf(
        "ACME CORP\nAnnual Report 2023\nFor the year ended 31 December 2023",
        pages=40,
    )
    v = validate_pdf(body, source_filename="acme_annual_report.pdf", expected_year=2023)
    assert v.ok, v.reason
    assert v.inferred_year == 2023
    assert v.review_status == "auto_ok"
