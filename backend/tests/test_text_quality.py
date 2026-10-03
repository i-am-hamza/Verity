"""Unit tests for each text-quality switch — one per switch, each shows
the difference it makes on invented page text. Fixtures are invented
because this is pure logic (CLAUDE.md rule 4 — real fixtures only for
network code).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pdf_extraction import PageText
from app.services.text_quality import (
    apply_text_quality,
    count_pages_mostly_arabic,
    detect_contents_pages,
    detect_financial_statements_start,
    remove_repeated_header_footer,
    repeated_line_report,
)
from app.services.verity_config import VerityConfig


def _pages(bodies: list[str]) -> list[PageText]:
    return [PageText(page_number=i + 1, text=b, used_ocr=False)
            for i, b in enumerate(bodies)]


# ----------------------------- a) header / footer ---------------------------


def test_repeated_header_footer_dropped_above_ratio():
    # 5 pages; header "Alinma Bank Annual Report 2023" + page-N on all of them.
    # Target: all 5 "Alinma Bank..." lines dropped; both bodies kept.
    bodies = [
        "Alinma Bank Annual Report 2023\nStrategic highlights\nPage 1 of 5\n"
        "The group delivered strong growth across all segments.",
        "Alinma Bank Annual Report 2023\nSustainability framework\nPage 2 of 5\n"
        "Three climate-aligned products launched during the year.",
        "Alinma Bank Annual Report 2023\nGovernance\nPage 3 of 5\n"
        "The Board reviewed the Code of Conduct in December.",
        "Alinma Bank Annual Report 2023\nRisk\nPage 4 of 5\n"
        "Operational risk framework updated to COSO 2017.",
        "Alinma Bank Annual Report 2023\nFinancial statements\nPage 5 of 5\n"
        "Consolidated statement of financial position.",
    ]
    cleaned, removed = remove_repeated_header_footer(_pages(bodies), min_ratio=0.30)
    assert removed == 10  # 5 header + 5 "Page N of 5"
    for p in cleaned:
        assert "Alinma Bank Annual Report 2023" not in p.text
        assert "Page " not in p.text
    # Non-repeating body text survives.
    joined = "\n".join(p.text for p in cleaned)
    assert "operational risk framework" in joined.lower()


def test_header_footer_leaves_body_lines_alone_at_low_repeat():
    # A line that appears on exactly one page must not be removed, even if
    # min_ratio is low — threshold floor is max(2, round(ratio*n_pages)).
    bodies = [
        "ONLY ON PAGE ONE\nbody text here",
        "generic footer\nmore body",
        "generic footer\nstill more body",
    ]
    cleaned, removed = remove_repeated_header_footer(_pages(bodies), min_ratio=0.30)
    joined = "\n".join(p.text for p in cleaned)
    assert "ONLY ON PAGE ONE" in joined
    assert "generic footer" not in joined
    assert removed == 2


def test_numeric_only_lines_are_not_treated_as_boilerplate():
    """Session 5 finding on bank-muscat FY2025: lines like '120,000', '0', '-'
    were being flagged as repeated headers/footers by the digit-normaliser
    (`'#,#'` on 137 pages). They are isolated table cells, not boilerplate.
    The fix: require the normalised line to carry at least one letter."""
    # 10 pages, each with a bare number line + a shared text header, each
    # with a UNIQUE body sentence so only the header + numbers are "repeats".
    unique_phrases = [
        "The chairman addressed the shareholders.",
        "Our governance structure was refreshed this year.",
        "Risk appetite moved higher following the merger.",
        "Branch footprint expanded across the Northern region.",
        "A new cybersecurity framework replaces the legacy stack.",
        "Climate transition risk was assessed by the ESG committee.",
        "Employee engagement scores exceeded targets for three quarters.",
        "The audit opinion was unqualified for the sixth consecutive year.",
        "Zakat and philanthropy spending reached a decade high.",
        "A dividend of forty halalas per share was proposed.",
    ]
    cells = ["120,000", "0", "245,241", "-", "16,826", "70,000",
             "3,246", "2,659", "20,621", "122,746"]
    bodies = [f"ANNUAL REPORT 2025\n{c}\n{p}" for c, p in zip(cells, unique_phrases, strict=True)]
    cleaned, removed = remove_repeated_header_footer(_pages(bodies), min_ratio=0.30)
    # Expected: 10 "ANNUAL REPORT 2025" headers removed; numeric cells SURVIVE.
    assert removed == 10, f"expected exactly 10 real-header removals, got {removed}"
    joined = "\n".join(p.text for p in cleaned)
    assert "ANNUAL REPORT 2025" not in joined
    # Every numeric cell should still be present.
    for cell in ("120,000", "0", "245,241", "-", "122,746"):
        assert cell in joined, f"numeric cell {cell!r} should have survived; it's not boilerplate"


def test_repeated_line_report_counts_pages_not_occurrences():
    # The diagnostic should count UNIQUE pages the line is on, not total
    # occurrences, so a header repeated twice on the same page doesn't inflate.
    pages = _pages([
        "head\nhead\nbody1",
        "head\nbody2",
        "head\nbody3",
        "head\nbody4",
    ])
    rep = repeated_line_report(pages, min_ratio=0.30)
    assert rep.get("head") == 4


# ----------------------------- b) contents detection ------------------------


def test_contents_page_detected_by_dot_leaders():
    """Dot leaders are the strongest signal — a page with ≥4 dot-leader lines
    is a contents page even without the header word 'Contents'."""
    page = (
        "Chair's statement .......................... 4\n"
        "Strategic report ........................... 8\n"
        "Governance ................................ 18\n"
        "Risk management ............................ 42\n"
        "Financial review .......................... 60\n"
    )
    pages = _pages([page] + ["real body"] * 20)
    assert detect_contents_pages(pages) == [1]


def test_contents_page_detected_by_dense_numeric_column():
    page = (
        "Section A 5\nSection B 7\nSection C 12\nSection D 18\n"
        "Section E 20\nSection F 24\nSection G 29\nAn introduction follows.\n"
    )
    pages = _pages([page] + ["narrative"] * 20)
    assert 1 in detect_contents_pages(pages)


def test_body_page_not_flagged_as_contents():
    """A normal page with occasional numbers should NOT be flagged."""
    page = (
        "The Group reported record profits of 1,234 million in 2023.\n"
        "Our risk management framework was refreshed in July.\n"
        "Diversity and inclusion remain board priorities.\n"
    )
    pages = _pages([page] * 20)
    assert detect_contents_pages(pages) == []


# ----------------------------- c) Arabic page classifier --------------------


def test_count_pages_mostly_arabic():
    pages = _pages([
        "The board governance framework was reviewed in detail this year.",
        "تقرير سنوي للبنك عام ألفين وثلاثة وعشرون صفحة واحدة من مئة وثلاث عشرة",
        "Mixed page: governance التقرير management framework التحوكمة والمخاطر",
    ])
    # Page 1 all Latin -> no. Page 2 all Arabic -> yes. Page 3 mixed -> depends on ratio.
    arabic_pages = count_pages_mostly_arabic(pages, ratio=0.50)
    assert arabic_pages == 1


# ----------------------------- d) matching mode (ref via apply_text_quality,
#     but the diagnostic itself is in pipeline._match_with_mode — not here) --


# ----------------------------- e) financial statements boundary -------------


def test_financial_statements_boundary_detected_in_back_half():
    markers = ["independent auditor's report", "consolidated statement of financial position"]
    # 20 narrative pages, then auditor's report at page 15 (back half).
    bodies = ["narrative content " + str(i) for i in range(1, 15)]
    bodies.append("INDEPENDENT AUDITOR'S REPORT\nTo the shareholders...")
    bodies += ["Statements and notes " + str(i) for i in range(16, 21)]
    assert detect_financial_statements_start(_pages(bodies), markers) == 15


def test_financial_statements_boundary_ignores_toc_mention_in_front_matter():
    """The TOC mentions 'Independent Auditor's Report' near the front; the
    detector must NOT accept that — it only scans the back three-quarters."""
    markers = ["independent auditor's report"]
    bodies = [
        "Table of Contents\nIndependent Auditor's Report ..... 92",
        "Chair's letter",
    ] + ["narrative"] * 20  # auditor marker never appears again
    assert detect_financial_statements_start(_pages(bodies), markers) is None


def test_financial_statements_boundary_matches_arabic_marker_normalised():
    markers = ["البيانات المالية الموحدة"]
    bodies = ["narrative"] * 10 + [
        # Deliberately include Arabic PRESENTATION FORMS the way PyMuPDF
        # extracts them; NFKC normalisation must collapse to the base form
        # before the marker check.
        "ﻼﺎﻟﺒﻴﺎﻧﺎت اﳌﺎﻟﻴﺔ اﳌﻮﺣﺪة\n(auditor section)"
    ] + ["notes"] * 5
    # Page 11 should hit after NFKC normalisation. Expected: 11.
    got = detect_financial_statements_start(_pages(bodies), markers)
    assert got == 11, f"expected 11, got {got}"


# ----------------------------- end-to-end apply_text_quality ----------------


def test_apply_text_quality_wires_switches_from_config():
    """A single orchestration call should apply every enabled switch and
    return consistent audit numbers."""
    cfg = VerityConfig(
        exclude_toc_pages=True, exclude_repeated_lines=True,
        exclude_financial_statement_pages=True,
        header_footer_repeat_ratio=0.30,
        arabic_page_token_ratio=0.50,
        financial_statement_boundary_markers=["independent auditor's report"],
    )
    toc = (
        "Chair's statement .......................... 4\n"
        "Strategic report ........................... 8\n"
        "Governance ................................ 18\n"
        "Risk management ............................ 42\n"
        "Financial review .......................... 60\n"
    )
    body = "Running Footer\nGovernance disclosure sentence."
    body_arabic = "Running Footer\nتقرير سنوي للبنك عام ألفين وثلاثة وعشرون"
    bodies = [toc, body, body, body_arabic, body, body,
              "INDEPENDENT AUDITOR'S REPORT\nback matter"]
    cleaned = apply_text_quality(_pages(bodies), cfg)
    assert 1 in cleaned.excluded_contents_pages
    # 7 pages total; "Running Footer" is on pages 2..6 = 5 pages = 5/7 ≈ 71%,
    # above the 30% threshold => dropped.
    joined = "\n".join(p.text for p in cleaned.pages)
    assert "Running Footer" not in joined
    assert cleaned.repeated_lines_removed >= 5
    assert cleaned.pages_mostly_arabic == 1
    assert cleaned.financial_statements_start_page == 7
    # FS boundary at page 7 => page 7 excluded.
    assert cleaned.financial_statements_excluded_pages == 1
