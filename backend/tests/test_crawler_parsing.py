"""
Tests for the crawler's link-parsing logic (the part that can be unit
tested without a live network call). Fixtures below are modeled on the
actual page structures observed during research for this pilot, not made
up: KFH's Annual-Reports.html lists years with a "Download" link per year;
Al Rajhi's IR page links out to a separate Annual Reports sub-page rather
than linking PDFs directly -- which is exactly why the crawler supports a
second crawl depth.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bs4 import BeautifulSoup

from app.crawler.parse import find_annual_report_links

KFH_STYLE_HTML = """
<html><body>
<div class="reports-list">
  <h3>2023</h3><a href="/dam/reports/kfh_annual_report_2023.pdf">Annual Report 2023 Download</a>
  <h3>2022</h3><a href="/dam/reports/kfh_annual_report_2022.pdf">Annual Report 2022 Download</a>
  <h3>2021</h3><a href="/dam/reports/kfh_annual_report_2021.pdf">Annual Report 2021 Download</a>
</div>
</body></html>
"""

ALRAJHI_IR_PAGE_HTML = """
<html><body>
<nav>
  <a href="/en/investor-relations/pages/annual_reports.aspx">Annual Reports</a>
  <a href="/en/investor-relations/pages/quarterly.aspx">Quarterly Results</a>
</nav>
</body></html>
"""

ALRAJHI_SUBPAGE_HTML = """
<html><body>
<ul>
  <li><a href="/en/ir/ar/annual_report_2023.pdf">2023 Annual Report</a></li>
  <li><a href="/en/ir/ar/annual_report_2022.pdf">2022 Annual Report</a></li>
</ul>
</body></html>
"""


def test_finds_direct_pdf_links_with_year_in_text():
    soup = BeautifulSoup(KFH_STYLE_HTML, "html.parser")
    links = find_annual_report_links(soup, "https://kfh.com/en/home/Investor-Relations/Annual-Reports.html")
    years_found = {link["year"] for link in links}
    assert years_found == {2023, 2022, 2021}
    assert all(link["is_pdf"] for link in links)


def test_identifies_listing_subpage_as_non_pdf_candidate():
    """This is the case the crawler's second depth level exists for --
    the IR page links to a sub-page, not a PDF, so it must be flagged
    as non-PDF and followed."""
    soup = BeautifulSoup(ALRAJHI_IR_PAGE_HTML, "html.parser")
    links = find_annual_report_links(soup, "https://www.alrajhibank.com.sa/en/about-alrajhi-bank/investor-relations")
    assert len(links) == 1
    assert links[0]["is_pdf"] is False
    assert links[0]["url"] == "https://www.alrajhibank.com.sa/en/investor-relations/pages/annual_reports.aspx"


def test_subpage_yields_the_actual_pdfs():
    soup = BeautifulSoup(ALRAJHI_SUBPAGE_HTML, "html.parser")
    links = find_annual_report_links(soup, "https://www.alrajhibank.com.sa/en/investor-relations/pages/annual_reports.aspx")
    years_found = {link["year"] for link in links if link["is_pdf"]}
    assert years_found == {2023, 2022}


def test_ignores_unrelated_links():
    html = '<a href="/quarterly-results">Q3 2023 Results</a><a href="/careers">Careers</a>'
    soup = BeautifulSoup(html, "html.parser")
    links = find_annual_report_links(soup, "https://example.com")
    assert links == []


def test_relative_urls_resolved_against_base():
    html = '<a href="/reports/ar2023.pdf">Annual Report 2023</a>'
    soup = BeautifulSoup(html, "html.parser")
    links = find_annual_report_links(soup, "https://bank.example.com/investor-relations")
    assert links[0]["url"] == "https://bank.example.com/reports/ar2023.pdf"
