"""HTML parsers for discovering annual-report links.

Extends the Session-1 `find_annual_report_links` to also recognise:
  - "integrated report" and "integrated annual report"
  - the Arabic phrase for "annual report" (التقرير السنوي), common on
    bilingual MENA IR pages
  - links held in `data-href` or `onclick="…'url'"` instead of `href`
    (common on exchange and SPA report lists)

The function stays backwards-compatible: the five Session-1 tests in
tests/test_crawler_parsing.py continue to pass against this entry point.

Scope note: the parser never follows anchors. It only enumerates them so
the fetcher can decide. The decision to STAY on the company's own domain
(or an explicitly allowed_hosts entry) is enforced in pipeline.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup

# "annual report" | "integrated report" | "integrated annual report"
# | "sustainability report" + Arabic "التقرير السنوي".
# Sustainability is admitted so the parser can CLASSIFY it; the pipeline
# then chooses to skip sustainability-kind links. Catching them here beats
# silently dropping them, because an "annual + sustainability combined
# report" would otherwise be invisible to a sustainability-only filter.
_REPORT_PATTERN = re.compile(
    r"integrated\s+annual\s+report|integrated\s+report|annual\s+report|"
    r"sustainability\s+report|التقرير\s+السنوي",
    re.IGNORECASE | re.UNICODE,
)

_SUSTAINABILITY_PATTERN = re.compile(r"sustainability\s+report", re.IGNORECASE)

_YEAR_PATTERN = re.compile(r"20(1[5-9]|2[0-9])")  # 2015..2029

# Pick a URL-like string out of an onclick / data-href value. We're not
# clicking anything; we're reading the literal URL the handler would open.
_URL_IN_ATTR = re.compile(r"""['"]((?:https?:)?//[^'"\s]+|/[^'"\s]+)['"]""")


@dataclass
class CandidateLink:
    url: str
    text: str
    year: int | None
    is_pdf: bool
    kind: str  # "annual" | "integrated" | "sustainability" | "unknown"
    source_attr: str  # "href" | "data-href" | "onclick"


def _detect_kind(text: str, href: str) -> str:
    hay = f"{text} {href}".lower()
    if _SUSTAINABILITY_PATTERN.search(hay):
        return "sustainability"
    if "integrated" in hay and "annual" in hay:
        return "integrated"
    if "integrated" in hay:
        return "integrated"
    if "annual" in hay:
        return "annual"
    if "التقرير السنوي" in text or "التقرير السنوي" in href:
        return "annual"
    return "unknown"


def _text_or_label(a) -> str:
    """Visible text, with aria-label and title as fallbacks."""
    text = a.get_text(" ", strip=True) or ""
    for attr in ("aria-label", "title"):
        v = (a.get(attr) or "").strip()
        if v and v not in text:
            text = f"{text} {v}".strip()
    return text


def _extract_url_from_attr(value: str | None) -> str | None:
    if not value:
        return None
    # If the attribute itself is already a URL (common for data-href):
    v = value.strip()
    if v.startswith(("http://", "https://", "/", "./", "../")):
        return v
    # Otherwise look for a URL literal inside the string (onclick="window.open('…')").
    m = _URL_IN_ATTR.search(value)
    return m.group(1) if m else None


def find_annual_report_links(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Return candidate report-ish links on this page.

    Each entry is a dict with keys url, text, year, is_pdf — same shape
    as Session 1's output so the existing tests still pass. New callers
    can use `find_annual_report_links_rich` for the structured version.
    """
    rich = find_annual_report_links_rich(soup, base_url)
    return [
        {"url": c.url, "text": c.text, "year": c.year, "is_pdf": c.is_pdf}
        for c in rich
    ]


def find_annual_report_links_rich(
    soup: BeautifulSoup, base_url: str
) -> list[CandidateLink]:
    out: list[CandidateLink] = []
    seen: set[tuple[str, str]] = set()  # (url, source_attr) de-dupe

    for a in soup.find_all("a"):
        text = _text_or_label(a)
        # Candidate URLs: href, data-href, onclick.
        hrefs: list[tuple[str, str]] = []  # (raw_href, source_attr)
        href = (a.get("href") or "").strip()
        if href:
            hrefs.append((href, "href"))
        data_href = _extract_url_from_attr(a.get("data-href"))
        if data_href:
            hrefs.append((data_href, "data-href"))
        onclick = _extract_url_from_attr(a.get("onclick"))
        if onclick:
            hrefs.append((onclick, "onclick"))

        if not hrefs:
            continue

        for raw, source_attr in hrefs:
            # Does any version (text + any discovered URL) mention "report"?
            if not _REPORT_PATTERN.search(f"{text} {raw}"):
                continue

            abs_url = urljoin(base_url, raw)
            key = (abs_url, source_attr)
            if key in seen:
                continue
            seen.add(key)

            year_match = _YEAR_PATTERN.search(text) or _YEAR_PATTERN.search(raw)
            is_pdf = abs_url.lower().split("?")[0].endswith(".pdf")
            kind = _detect_kind(text, raw)
            out.append(CandidateLink(
                url=abs_url, text=text,
                year=int(year_match.group()) if year_match else None,
                is_pdf=is_pdf, kind=kind, source_attr=source_attr,
            ))

    # Also inspect buttons / divs with data-href or onclick that encode a
    # report URL. Exchange sites and SPAs frequently use these.
    for el in soup.find_all(["button", "div", "span", "li"]):
        text = _text_or_label(el)
        if not _REPORT_PATTERN.search(text):
            continue
        for attr in ("data-href", "onclick"):
            raw_url = _extract_url_from_attr(el.get(attr))
            if raw_url is None:
                continue
            abs_url = urljoin(base_url, raw_url)
            key = (abs_url, attr)
            if key in seen:
                continue
            seen.add(key)
            year_match = _YEAR_PATTERN.search(text) or _YEAR_PATTERN.search(raw_url)
            is_pdf = abs_url.lower().split("?")[0].endswith(".pdf")
            kind = _detect_kind(text, raw_url)
            out.append(CandidateLink(
                url=abs_url, text=text,
                year=int(year_match.group()) if year_match else None,
                is_pdf=is_pdf, kind=kind, source_attr=attr,
            ))

    return out


def find_followable_subpages(
    soup: BeautifulSoup, base_url: str
) -> list[str]:
    """Return non-PDF URLs that look like an annual-report-listing sub-page.

    This handles the two-step IR layouts (Session 1 called this out for
    Al Rajhi): the main IR page links to a sub-page, which lists the
    actual PDFs. Keep it conservative — only on text matches.
    """
    out: list[str] = []
    for c in find_annual_report_links_rich(soup, base_url):
        if not c.is_pdf and c.kind in ("annual", "integrated"):
            out.append(c.url)
    # De-dupe, keep order.
    seen: set[str] = set()
    uniq: list[str] = []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq
