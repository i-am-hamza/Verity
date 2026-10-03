"""Parser tests for the extensions Session 4 added to Session 1's
`find_annual_report_links`:

- "integrated report" / "integrated annual report" are recognised.
- The Arabic phrase for "annual report" is recognised.
- Links in `data-href` and `onclick="window.open('…')"` are discovered.
- Non-anchor elements (buttons/divs) with those attrs are discovered.
- The non-link `javascript:__doPostBack(...)` postback links on MSX are
  not followed (they aren't annual report links).

All fixtures live under tests/fixtures/html/ and are dated.
"""
from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.crawler.parse import (
    find_annual_report_links,
    find_annual_report_links_rich,
    find_followable_subpages,
)

FIXTURES = Path(__file__).parent / "fixtures" / "html"


def _load(name: str, base: str) -> tuple[BeautifulSoup, str]:
    soup = BeautifulSoup((FIXTURES / name).read_text(encoding="utf-8"), "html.parser")
    return soup, base


# ---------------------------------------------------------------------------
# IR fixtures
# ---------------------------------------------------------------------------
def test_al_rajhi_three_annual_report_pdfs_with_oracle_cdn():
    soup, base = _load("al_rajhi_ir_2026-10-01.html",
                       "https://www.alrajhibank.com.sa/en/about-alrajhi-bank/investor-relations")
    rich = find_annual_report_links_rich(soup, base)
    pdfs = [c for c in rich if c.is_pdf]
    years = {c.year for c in pdfs if c.year}
    assert years == {2025, 2024, 2023}

    kinds = {c.year: c.kind for c in pdfs if c.year}
    # "Integrated Annual Report 2025" should classify as "integrated".
    assert kinds[2025] == "integrated"
    assert kinds[2024] == "annual"

    # Oracle object-storage URLs are absolute; the relative /-/media one must
    # become absolute via urljoin.
    oracle = [c for c in pdfs if "objectstorage.me-jeddah-1.oraclecloud.com" in c.url]
    assert len(oracle) >= 2
    media = [c for c in pdfs if c.url.endswith("Annual-Report-EN-2023.pdf")]
    assert media and media[0].url.startswith("https://www.alrajhibank.com.sa/-/media/")


def test_kfh_ir_lists_five_years_of_annual_report_pdfs():
    soup, base = _load("kfh_ir_2026-10-01.html",
                       "https://kfh.com/en/home/Investor-Relations/Annual-Reports.html")
    rich = find_annual_report_links_rich(soup, base)
    years = {c.year for c in rich if c.is_pdf and c.year}
    assert years == {2025, 2024, 2023, 2022, 2021}
    # KFH uses `.pdf.pdf` double extension — the is_pdf detection must still fire.
    assert all(c.is_pdf for c in rich if c.year)


def test_dubai_investments_mixes_integrated_sustainability_and_arabic():
    soup, base = _load("dubai_investments_ir_2026-10-01.html",
                       "https://dubaiinvestments.com/investor-relations")
    rich = find_annual_report_links_rich(soup, base)

    # Integrated reports (EN) 2025 and 2024.
    integrated = {c.year for c in rich if c.kind == "integrated" and c.is_pdf}
    assert {2025, 2024}.issubset(integrated)

    # The Arabic انتخاب — التقرير السنوي 2025 — must be classified as "annual"
    # (same bucket as the English Annual Report / Integrated).
    arabic = [c for c in rich if "التقرير السنوي" in c.text]
    assert arabic, "Arabic 'annual report' link not picked up"
    assert arabic[0].kind in ("annual", "integrated")  # Arabic phrase alone -> annual
    assert arabic[0].year == 2025

    # Sustainability report must classify separately so pipeline can skip it.
    sustain = [c for c in rich if c.kind == "sustainability"]
    assert sustain and not sustain[0].is_pdf  # the fixture link is to a page, not a PDF


# ---------------------------------------------------------------------------
# Exchange fixtures
# ---------------------------------------------------------------------------
def test_dfm_disclosure_rows_use_onclick_and_data_href():
    soup, base = _load("dfm_dib_exchange_2026-10-01.html",
                       "https://www.dfm.ae/the-exchange/market-information/company/DIB/profile")
    rich = find_annual_report_links_rich(soup, base)
    # Three annual-report rows: two onclick, one data-href.
    pdfs = [c for c in rich if c.is_pdf and c.kind == "annual"]
    years = {c.year for c in pdfs}
    assert years == {2022, 2023, 2024}

    attrs = {c.source_attr for c in pdfs}
    assert "onclick" in attrs
    assert "data-href" in attrs

    # All three URLs should be absolute (feeds.dfm.ae), picked out of the attr strings.
    assert all(c.url.startswith("https://feeds.dfm.ae/documents/") for c in pdfs)


def test_msx_postbacks_are_not_treated_as_annual_report_links():
    soup, base = _load("msx_bkmb_exchange_2026-10-01.html",
                       "https://www.msx.om/snapshot.aspx?s=BKMB")
    rich = find_annual_report_links_rich(soup, base)
    # javascript:__doPostBack anchors must not appear as annual-report candidates.
    assert not any("javascript:__doPostBack" in c.url for c in rich)
    # Two legitimate PDFs expected.
    pdfs = [c for c in rich if c.is_pdf and c.kind == "annual"]
    assert {c.year for c in pdfs} == {2023, 2024}


# ---------------------------------------------------------------------------
# Shape contract — Session 1's older callers continue to work
# ---------------------------------------------------------------------------
def test_dict_shape_matches_session1_contract():
    soup, base = _load("kfh_ir_2026-10-01.html",
                       "https://kfh.com/en/home/Investor-Relations/Annual-Reports.html")
    legacy = find_annual_report_links(soup, base)
    # Session 1 dict shape: url, text, year, is_pdf.
    assert legacy and set(legacy[0].keys()) == {"url", "text", "year", "is_pdf"}


def test_followable_subpages_are_non_pdfs_only():
    html = """
    <div>
      <a href="/annual-reports.aspx">Annual Reports</a>
      <a href="/reports/annual-2023.pdf">Annual Report 2023</a>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    subs = find_followable_subpages(soup, "https://example.com")
    assert subs == ["https://example.com/annual-reports.aspx"]
