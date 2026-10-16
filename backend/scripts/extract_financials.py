#!/usr/bin/env python3
"""
extract_financials.py -- financial ratio inputs from annual reports in R2.

Reads CONSOLIDATED financial statements from each company-year's own report.
No web access; no ESG data touched; no schema changes.

Pilot (--pilot):  6 company-years; detailed terminal output.
Full  (--all):    all 390 -> docs/exports/financials_extracted.{xlsx,csv}.
Single (--slug X --fy N): one company-year.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

import app.models.institution  # noqa: F401
import app.models.provenance   # noqa: F401
import app.models.report       # noqa: F401
import app.models.review       # noqa: F401
import app.models.run          # noqa: F401
import app.models.score        # noqa: F401
import app.models.taxonomy     # noqa: F401

from app.database import SessionLocal
from app.models.institution import Institution, InstitutionType
from app.models.provenance import SourceDocument
from app.services.pdf_extraction import PageText, extract_pdf_pages
from app.services.storage import read_pdf_bytes
from sqlalchemy import select

# ---- number utilities -------------------------------------------------------

_AMOUNT_RE = re.compile(
    r"(?<![.\d,])"
    r"(\()?"
    r"("
    r"\d{1,3}(?:[,\xa0 ]\d{3})+"
    r"(?:[.,]\d+)?"
    r"|\d+[.,]\d{2,}"
    r"|\d{5,}"
    r")"
    r"(\))?"
    r"(?![.,\d])",
    re.UNICODE,
)


def _parse_number(raw: str) -> Optional[float]:
    s = raw.strip()
    negative = (s.startswith("(") and s.endswith(")")) or s.startswith("-")
    s = s.strip("()").lstrip("-").strip()
    s = s.replace("\xa0", "").replace(" ", "")
    n_periods = s.count(".")
    n_commas = s.count(",")
    if n_periods >= 2:
        s = s.replace(".", "")
    elif n_periods == 1 and n_commas > 0:
        s = s.replace(",", "")
    else:
        s = s.replace(",", "")
    try:
        val = float(s)
        return -val if negative else val
    except ValueError:
        return None


def _first_number(
    text: str, min_abs: float = 0.0, skip: int = 0
) -> Optional[tuple[str, float]]:
    seen = 0
    for m in _AMOUNT_RE.finditer(text):
        raw = m.group(0)
        val = _parse_number(raw)
        if val is not None and abs(val) >= min_abs:
            if seen >= skip:
                return (raw, val)
            seen += 1
    return None


# ---- data classes -----------------------------------------------------------

@dataclass
class ExtractedValue:
    label_as_printed: str
    value: Optional[float]
    page: int
    context: str = ""
    confidence: str = "high"
    note: str = ""


@dataclass
class FinancialRow:
    slug: str
    fiscal_year: int
    r2_key: str
    is_bank: bool = False

    currency: Optional[str] = None
    unit: Optional[str] = None
    currency_page: Optional[int] = None

    total_assets: Optional[ExtractedValue] = None
    total_liabilities: Optional[ExtractedValue] = None
    total_liabilities_computed: bool = False
    total_equity: Optional[ExtractedValue] = None
    equity_attributable: Optional[ExtractedValue] = None

    revenue: Optional[ExtractedValue] = None
    net_profit: Optional[ExtractedValue] = None
    net_profit_attributable: Optional[ExtractedValue] = None

    basic_eps: Optional[ExtractedValue] = None
    # Primary share count: issued shares from the share capital note.
    shares_outstanding: Optional[ExtractedValue] = None
    # Supplementary: weighted-average shares from the EPS note (for cross-check).
    shares_eps_note: Optional[ExtractedValue] = None
    # Profit used as EPS numerator (after AT1/Tier-1 sukuk cost deduction).
    eps_numerator: Optional[ExtractedValue] = None
    # Banks: gross financing / special-commission income (top IS line).
    gross_income_bank: Optional[ExtractedValue] = None
    # Total interest-bearing debt / sukuk / bonds (for leverage recomputation).
    total_borrowings: Optional[ExtractedValue] = None
    # Market data stated in the report.
    share_price_year_end: Optional[ExtractedValue] = None
    market_cap: Optional[ExtractedValue] = None
    # AT1 / Tier-1 sukuk shown inside equity (excluded from ordinary equity).
    at1_equity: Optional[ExtractedValue] = None

    year_of_incorporation: Optional[ExtractedValue] = None
    year_of_listing: Optional[ExtractedValue] = None

    flags: list[str] = field(default_factory=list)
    ocr_heavy: bool = False

    leverage: Optional[float] = None
    roa: Optional[float] = None
    roe: Optional[float] = None
    roe_eps_based: bool = False  # True = RoE uses eps_numerator / equity_ordinary
    equity_ordinary: Optional[float] = None  # EA - AT1 (RoE denominator)
    net_profit_margin: Optional[float] = None
    firm_age: Optional[int] = None
    listing_age: Optional[int] = None


# ---- label patterns ---------------------------------------------------------

_PATTERNS: dict[str, list[str]] = {
    "total_assets": [
        r"^total\s+assets\s*$",
        r"^total\s+assets\b",
    ],
    "total_liabilities": [
        r"^total\s+liabilities\s*$",
        r"^total\s+liabilities\b(?!\s+and\b)",
    ],
    "total_liabilities_and_equity": [
        r"total\s+liabilities\s+and\s+(?:shareholders['\s]*)?equity",
        r"total\s+equity\s+and\s+liabilities",
        r"total\s+liabilities\s+and\s+owners[']\s+equity",
    ],
    "total_equity": [
        r"^total\s+(?:shareholders['\s]*)?equity\s*$",
        r"^total\s+owners[']\s+equity\s*$",
        r"^total\s+equity\s*$",
        r"\btotal\s+(?:shareholders['\s]*)?equity\s*$",
        r"\btotal\s+equity\b(?!\s+attributable)",
    ],
    # Two-tier: "total equity attributable" patterns first (preferred),
    # then section-header patterns as fallback.
    "equity_attributable_total": [
        r"^total\s+equity\s+attributable\s+to\s+(?:equity\s+holders|shareholders|owners)\s+of\s+the\s+(?:parent|company|bank|group)",
        r"^total\s+equity\s+attributable\s+to\s+(?:equity\s+holders|shareholders|owners)\s+of\s+(?:parent|company|bank|group)",
        r"^total\s+equity\s+attributable\s+to\s+the\s+(?:shareholders|owners)\b",
    ],
    "equity_attributable_fallback": [
        r"^equity\s+attributable\s+to\s+(?:equity\s+holders|shareholders|owners)\s+of\s+the\s+(?:parent|company|bank|group)",
        r"^equity\s+attributable\s+to\s+(?:equity\s+holders|shareholders|owners)\s+of\s+(?:parent|company|bank|group)",
        r"^equity\s+attributable\s+to\s+the\s+(?:shareholders|owners)\b",
    ],
    "non_controlling_interests": [
        r"^non-?controlling\s+interests?\s*$",
        r"^non-?controlling\s+interest\s*$",
        r"^minority\s+interests?\s*$",
        r"^minority\s+interest\s*$",
    ],
    "revenue_bank": [
        r"^total\s+operating\s+income\s*$",
        r"^net\s+operating\s+income\s*$",
        r"^total\s+income\s*$",
    ],
    "revenue_nonbank": [
        r"^(?:total\s+)?revenues?\s*$",
        r"^net\s+revenues?\s*$",
        r"^net\s+sales\s*$",
        r"^operating\s+revenues?\s*$",
        r"^revenues?\s*:",  # "Revenue:" or "Revenues:"
    ],
    "net_profit": [
        r"^(?:net\s+)?profit\s+for\s+the\s+(?:year|period)\s*$",
        r"^(?:net\s+)?income\s+for\s+the\s+(?:year|period)\s*$",
        # Negative lookahead excludes "... for the year before Zakat/Tax" which is
        # a pre-tax sub-total in Islamic banks. We want the true bottom-line NP.
        r"^net\s+profit\s+for\s+the\s+year(?!\s+before\b)",
        r"^net\s+income\s+for\s+the\s+year(?!\s+before\b)",
        r"^net\s+profit\s+for\s+the\s+period(?!\s+before\b)",
        r"^net\s+income\s+for\s+the\s+period(?!\s+before\b)",
        r"^net\s+profit\s*$",
        r"^net\s+income\s*$",
        r"^profit\s+for\s+the\s+year\s*$",
        r"^income\s+for\s+the\s+year\s*$",
        r"^net\s+profit\s+for\s+the\s+(?:year|period)",
    ],
    "net_profit_attributable": [
        # Explicit combined label (any company)
        r"^(?:net\s+)?(?:profit|income)\s+attributable\s+to\s+(?:shareholders|equity\s+holders|owners)\s+of\s+the\s+(?:parent|company|bank|group)",
        r"^(?:net\s+)?(?:profit|income|loss)\s+attributable\s+to\s+(?:equity\s+holders|shareholders|owners)\s+of\s+(?:parent|company|bank|group)",
        r"^profit\s+attributable\s+to\s+shareholders\s+of\s+the\s+parent",
        r"^income\s+attributable\s+to\s+equity\s+holders",
        # "Attributable to:" section header fallback -> first sub-line
        r"^(?:net\s+)?(?:profit|income)\s+attributable\s+to:",
        # Sub-line after "ATTRIBUTABLE TO:" header: "Owners of the parent"
        r"^owners\s+of\s+the\s+(?:parent\s+company|parent|company)\s*$",
        r"^equity\s+holders\s+of\s+the\s+(?:parent|company)\s*$",
        r"^shareholders\s+of\s+the\s+(?:parent\s+company|parent|company)\s*$",
        r"^shareholders\s+of\s+the\s+bank\s*$",
    ],
    "basic_eps": [
        # All patterns anchored with ^ to avoid matching label lines that contain
        # "basic earnings per share" as a suffix (e.g. "Weighted avg shares ... for basic EPS").
        r"^basic\s+(?:earnings|profit|income|loss)\s+per\s+share",
        r"^earnings\s+per\s+share\s*[-–—:]\s*basic",
        r"^basic\s+EPS\b",
        r"^basic\s+(?:earnings|profit)\s+per\s+ordinary\s+share",
        r"^(?:earnings|profit)\s+per\s+share\s*[-–—:]\s*basic",
        r"^(?:basic\s+and\s+diluted|diluted\s+and\s+basic)\s+earnings\s+per\s+share",
        r"^earnings\s+per\s+share\s+\(fils?\)\s*[-–—]\s*basic",  # Jazeera format
    ],
    # Primary: issued/outstanding shares from the share capital note (not EPS note).
    # Searched in the FS notes section (after the FS boundary).
    "shares_outstanding": [
        r"^issued\s+and\s+(?:fully\s+)?paid[\s-]up\s*$",
        r"^(?:number\s+of\s+)?(?:issued\s+and\s+(?:fully\s+)?paid[\s-]up|issued\s+and\s+outstanding)\s+(?:ordinary\s+)?shares?\s*$",
        r"^(?:ordinary\s+)?shares?\s+issued\s+and\s+(?:fully\s+)?paid[\s-]up\s*$",
        r"^shares?\s+in\s+issue\s*$",
        r"^(?:total\s+)?(?:number\s+of\s+)?(?:ordinary\s+)?shares?\s+outstanding\s*$",
        r"^number\s+of\s+(?:issued\s+and\s+)?outstanding\s+(?:ordinary\s+)?shares?\s*$",
        r"^(?:total\s+)?issued\s+(?:and\s+(?:fully\s+)?paid[\s-]up\s+)?(?:ordinary\s+)?shares?\s*$",
        r"^number\s+of\s+shares\s*$",  # compact header in many GCC tables
    ],
    # Supplementary: weighted-average shares from the EPS note (cross-check only).
    "shares_eps_note": [
        r"^weighted\s+average\s+number\s+of\s+(?:ordinary\s+)?shares?\s+outstanding\s+for\s+(?:basic|diluted|earnings)",
        r"^weighted\s+average\s+(?:number\s+of\s+)?(?:ordinary\s+)?shares?\s+used\s+(?:in|for)",
        r"^weighted\s+average\s+(?:ordinary\s+)?shares?\s+outstanding\s*$",
    ],
    # Profit used as the EPS numerator after AT1 / Tier-1 sukuk cost deduction.
    "eps_numerator": [
        r"^(?:net\s+)?(?:income|profit)\s+(?:attributable\s+to\s+(?:ordinary\s+|equity\s+)?(?:holders|shareholders)\s+)?(?:after\s+(?:deducting\s+)?)?(?:tier\s+1|AT1|additional\s+tier\s+1)\s+(?:sukuk|capital)",
        r"^(?:net\s+)?(?:income|profit)\s+used\s+(?:for|in)\s+(?:(?:basic|diluted|the)\s+)?(?:earnings\s+per\s+share|EPS)\s+(?:calculation|computation|numerator)?",
        r"^(?:net\s+)?(?:income|profit)\s+for\s+(?:basic\s+)?EPS\b",
        r"^numerator\s*[-:–]?\s*(?:net\s+)?(?:income|profit)\b",
        r"^profit\s+for\s+(?:basic\s+)?(?:earnings\s+per\s+share|EPS)",
    ],
    # Banks: gross financing / special-commission income (first line of IS).
    "gross_income_bank": [
        r"^gross\s+financing\s+(?:and\s+investment\s+)?income\s*$",
        r"^gross\s+financing\s+income\s*$",
        r"^special\s+commission\s+income\s*$",
        r"^total\s+income\s+from\s+(?:islamic\s+)?(?:financing|banking)\b",
        r"^financing\s+income\s+from\s+(?:customers|banks|islamic)",
        r"^income\s+from\s+(?:islamic\s+)?(?:financing|investments?|banking)\s*$",
        r"^total\s+gross\s+income\s*$",
    ],
    # Total interest-bearing borrowings / sukuk / bonds.
    "total_borrowings": [
        r"^total\s+(?:interest[\s-]bearing\s+)?(?:loans?\s+and\s+)?borrowings?\s*$",
        r"^total\s+borrowings?\s+and\s+(?:lease|finance)\s+liabilities\s*$",
        r"^(?:loans?\s+and\s+)?borrowings?\s*$",
        r"^sukuk\s+(?:financings?|payable|issued)\s*$",
        r"^term\s+(?:loans?\s+and\s+)?financing\s+facilities?\s*$",
        r"^bonds?\s+(?:and\s+sukuk)?\s*$",
    ],
    # Share price at year-end (stated in the report's market data section).
    "share_price": [
        r"^(?:closing\s+|year[\s-]end\s+)?market\s+price\s+per\s+(?:ordinary\s+)?share\s*$",
        r"^market\s+price\s+per\s+share\s+as\s+at\b",
        r"^(?:closing\s+)?share\s+price\s*(?:per\s+share)?\s*$",
        r"^share\s+price\s+(?:as\s+at|at)\s+31\b",
        r"^market\s+value\s+per\s+share\s*$",
    ],
    # Market capitalisation as stated in the report.
    "market_cap": [
        r"^market\s+capitaliz(?:ation|isation)\s*$",
        r"^market\s+cap(?:ital(?:ization|isation))?\s*$",
        r"^market\s+value\s+(?:of\s+)?(?:the\s+)?(?:company|group|bank)\s*$",
    ],
    # AT1 / Additional Tier-1 sukuk carried inside the equity section of the BS.
    "at1_equity": [
        r"^(?:additional\s+)?tier\s+1\s+sukuk\s*$",
        r"^tier\s+1\s+sukuk\s+(?:certificates?|notes?|capital)?\s*$",
        r"^AT1\s+(?:sukuk|capital|instruments?)\s*$",
        r"^perpetual\s+(?:sukuk|notes?|bonds?)\s*$",
        r"^additional\s+tier\s+1\s+(?:capital|instruments?|notes?)\s*$",
    ],
    "year_incorporation": [
        r"(?:the\s+)?(?:company|bank|group)\s+was\s+incorporated",
        r"(?:the\s+)?(?:company|bank|group)\s+was\s+established",
        r"(?:the\s+)?(?:company|bank|group)\s+was\s+formed",
        r"incorporated\s+(?:in|on)\s+(?:the\s+Kingdom|the\s+State|the\s+Emirate|\d)",
        r"established\s+(?:in|on)\s+(?:the\s+Kingdom|the\s+State|the\s+Emirate|\d)",
        r"date\s+of\s+incorporation\s*:",
        r"\bwas\s+incorporated\b",   # catches "Company') was incorporated" (Kuwaiti format)
        r"\bwas\s+established\b",    # broad fallback
    ],
    "year_listing": [
        r"(?:company|bank|shares?)\s+(?:were?\s+)?listed\s+on\s+the\s+\w+\s+(?:stock\s+)?exchange",
        r"(?:company|bank|shares?)\s+(?:were?\s+)?listed\s+on\s+the\s+\w+\s+\w+\s+(?:stock\s+)?exchange",
        r"shares?\s+(?:were\s+)?admitted\s+to\s+(?:trading|listing)\s+on",
        r"(?:initial\s+public\s+offering|IPO)\s+(?:was\s+)?(?:completed|conducted|launched)\s+in",
    ],
}

# Markers that signal the start of the AUDITED financial statements section.
_FS_MARKERS = [
    # All apostrophe/plural forms of "Independent Auditor(s') Report"
    r"independent\s+auditors?['s]*\s*report",
    r"report\s+of\s+the\s+independent\s+auditors?",
    r"(?:consolidated\s+)?statement\s+of\s+financial\s+position",
    r"(?:consolidated\s+)?statement\s+of\s+comprehensive\s+income",
    r"(?:consolidated\s+)?statement\s+of\s+cash\s+flows",
    r"(?:consolidated\s+)?statement\s+of\s+changes\s+in\s+equity",
    r"notes\s+to\s+the\s+(?:consolidated\s+)?financial\s+statements",
]

# Markers for the income statement page specifically.
# All patterns end with \s*$ or (?:\s*$|\s+\d) to avoid matching mid-sentence
# uses of "consolidated income statement in ..." in notes text.
_IS_MARKERS = [
    r"^consolidated\s+(?:income\s+statement|statement\s+of\s+income)(?:\s*$|\s+\d)",
    r"^consolidated\s+statement\s+of\s+profit\s+or\s+loss\s*$",
    r"^consolidated\s+statement\s+of\s+profit\s*$",
    r"^income\s+statement$",
    r"^statement\s+of\s+income$",
    r"^statement\s+of\s+profit\s+or\s+loss$",
    r"^consolidated\s+statement\s+of\s+financial\s+performance\s*$",
    r"^consolidated\s+statement\s+of\s+income\s+and\s+comprehensive",
]

# Currency codes and common abbreviations used in GCC reports.
_CURRENCIES = ["SAR", "AED", "QAR", "KWD", "OMR", "BHD", "EGP", "USD"]
_CURRENCY_ALIASES: dict[str, str] = {
    "KD": "KWD",
    "RO": "OMR",
    "BD": "BHD",
    "SR": "SAR",
}

# PDF typographic ligatures (single codepoints) to ASCII equivalents.
# Applying this before regex matching lets "Proﬁt" match /profit/ and
# "ﬁls" (Kuwaiti currency "fils") match /fils/.
_LIGATURE_MAP = str.maketrans({
    "ﬀ": "ff",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "ﬅ": "st",
    "ﬆ": "st",
})


# ---- extractor --------------------------------------------------------------


class PDFFinancialExtractor:

    def __init__(
        self, slug: str, fiscal_year: int, r2_key: str, is_bank: bool = False
    ):
        self.slug = slug
        self.fiscal_year = fiscal_year
        self.r2_key = r2_key
        self.is_bank = is_bank
        self.pages: list[PageText] = []
        self._lines: list[tuple[int, str]] = []
        self._fs_start: int = 0
        self._is_start: int = 0   # income statement section start
        self._pdf_bytes: Optional[bytes] = None
        self.result = FinancialRow(
            slug=slug, fiscal_year=fiscal_year, r2_key=r2_key, is_bank=is_bank
        )

    # ---- loading ------------------------------------------------------------

    def load(self) -> None:
        self._pdf_bytes = read_pdf_bytes(self.r2_key)
        self.pages = extract_pdf_pages(self._pdf_bytes)
        for p in self.pages:
            for raw_line in p.text.split("\n"):
                stripped = raw_line.strip().translate(_LIGATURE_MAP)
                if stripped:
                    self._lines.append((p.page_number, stripped))
        ocr = sum(1 for p in self.pages if p.used_ocr)
        self.result.ocr_heavy = bool(self.pages) and (ocr / len(self.pages)) > 0.30
        self._fs_start = self._find_fs_boundary()
        self._is_start = self._find_income_statement_start()

    def _find_fs_boundary(self) -> int:
        # Try the two combined auditor-report patterns from the very start
        # (no skip) — they are unambiguous across any TOC entry.
        for pat in (_FS_MARKERS[0], _FS_MARKERS[1]):
            hit = self._find_first([pat])
            if hit:
                return hit[0]

        # Split-line variant: some PDFs print "independent" on one line and
        # "auditors' report" (alone) on the very next line or within 3 lines
        # (e.g. Al Rajhi Bank).  TOC entries use the same split, so we only
        # search from the 30% mark — financial statements never start in the
        # first third of an annual report.
        # Non-ASCII apostrophes (Windows smart-quotes, U+FFFD decoding artefacts)
        # mean a literal `'` char-class won't match. Use \W* to absorb any
        # non-word character(s) between "auditors" and "report".
        _INDEP = re.compile(r"^independent\s*$", re.IGNORECASE)
        _ARPT  = re.compile(r"^auditors?\W*report\s*$", re.IGNORECASE)
        split_start = len(self._lines) * 30 // 100
        for i in range(split_start, len(self._lines)):
            line = self._lines[i][1]
            if _INDEP.match(line):
                for j in range(i + 1, min(i + 4, len(self._lines))):
                    if _ARPT.match(self._lines[j][1]):
                        return i
            if _ARPT.match(line):
                for j in range(max(split_start, i - 3), i):
                    if _INDEP.match(self._lines[j][1]):
                        return j

        skip = max(0, len(self._lines) // 10)
        hit = self._find_first(_FS_MARKERS, start=skip)
        return hit[0] if hit else 0

    def _find_income_statement_start(self) -> int:
        """Find the consolidated income statement page within the FS section.

        Some PDFs extract blocks in non-reading order so the IS page header
        appears at the END of that page's linearised text lines.  We scan back
        to the FIRST line on the same page so revenue / NP searches don't start
        past the actual values.
        """
        hit = self._find_first(_IS_MARKERS, start=self._fs_start)
        if hit is None:
            return self._fs_start
        line_idx, page_no, _ = hit
        # Walk back to the first line on this page.
        first_on_page = line_idx
        while first_on_page > 0 and self._lines[first_on_page - 1][0] == page_no:
            first_on_page -= 1
        return first_on_page

    # ---- text helpers -------------------------------------------------------

    def _find_first(
        self,
        patterns: list[str],
        start: int = 0,
        stop: Optional[int] = None,
    ) -> Optional[tuple[int, int, str]]:
        end = stop if stop is not None else len(self._lines)
        for i in range(start, end):
            page_no, line = self._lines[i]
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    return (i, page_no, line)
        return None

    def _context_str(self, start: int, window: int = 5) -> str:
        parts = [
            self._lines[j][1]
            for j in range(start, min(start + window, len(self._lines)))
        ]
        return "  |  ".join(parts)

    # ---- fallback: pymupdf table extraction ---------------------------------

    def _ev_from_table(
        self, page_no: int, patterns: list[str], min_abs: float = 0
    ) -> Optional[ExtractedValue]:
        if not self._pdf_bytes:
            return None
        import pymupdf
        import warnings

        doc = pymupdf.open(stream=self._pdf_bytes, filetype="pdf")
        if page_no < 1 or page_no > len(doc):
            return None
        page = doc[page_no - 1]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                finder = page.find_tables()
                tables = finder.tables
            except Exception:
                return None

        for tbl in tables:
            try:
                rows = tbl.extract()
            except Exception:
                continue
            for row in rows:
                if not row:
                    continue
                first_cell = str(row[0] or "").strip()
                for pat in patterns:
                    if re.search(pat, first_cell, re.IGNORECASE):
                        for cell in row[1:]:
                            cell_str = str(cell or "").strip()
                            found = _first_number(cell_str, min_abs=min_abs)
                            if found:
                                return ExtractedValue(
                                    label_as_printed=first_cell,
                                    value=found[1],
                                    page=page_no,
                                    context=f"table: {first_cell} | {cell_str}",
                                    confidence="medium" if self.result.ocr_heavy else "high",
                                    note="table extraction",
                                )
        return None

    # ---- fallback: coordinate-based extraction (multi-column PDFs) ----------

    def _ev_from_coords(
        self, page_no: int, patterns: list[str], min_abs: float = 0
    ) -> Optional[ExtractedValue]:
        """Use bounding-box positions to find numbers on the same row as the
        label. Uses 'dict' mode (not 'rawdict') because PyMuPDF 1.28+ only
        places 'text' in spans under dict mode — rawdict uses 'chars' only."""
        if not self._pdf_bytes:
            return None
        import pymupdf

        doc = pymupdf.open(stream=self._pdf_bytes, filetype="pdf")
        if page_no < 1 or page_no > len(doc):
            return None
        page = doc[page_no - 1]

        try:
            raw = page.get_text("dict")
        except Exception:
            return None

        spans: list[tuple[str, float, float, float, float]] = []
        for block in raw.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    txt = span.get("text", "").strip().translate(_LIGATURE_MAP)
                    if txt:
                        bbox = span["bbox"]
                        spans.append((txt, bbox[0], bbox[1], bbox[2], bbox[3]))

        label_span: Optional[tuple[str, float, float, float, float]] = None
        for txt, x0, y0, x1, y1 in spans:
            for pat in patterns:
                if re.search(pat, txt, re.IGNORECASE):
                    label_span = (txt, x0, y0, x1, y1)
                    break
            if label_span:
                break

        if label_span is None:
            return None

        _, lx0, ly0, lx1, ly1 = label_span
        label_y_mid = (ly0 + ly1) / 2
        row_tolerance = max((ly1 - ly0) * 1.2, 4.0)  # wider tolerance than before

        candidates: list[tuple[float, str, float]] = []
        for txt, x0, y0, x1, y1 in spans:
            span_y_mid = (y0 + y1) / 2
            if abs(span_y_mid - label_y_mid) <= row_tolerance and x0 > lx1 - 5:
                found = _first_number(txt, min_abs=min_abs)
                if found:
                    candidates.append((x0, found[0], found[1]))

        if not candidates:
            return None

        candidates.sort(key=lambda c: c[0])
        _, raw_num, val = candidates[0]
        label_txt = label_span[0]
        return ExtractedValue(
            label_as_printed=label_txt,
            value=val,
            page=page_no,
            context=f"coord-row: {label_txt} | {raw_num}",
            confidence="medium" if self.result.ocr_heavy else "high",
            note="coordinate extraction",
        )

    # ---- main extraction helper (with retry loop) ---------------------------

    def _extract_ev(
        self,
        patterns: list[str],
        min_abs: float = 100.0,
        start: int = 0,
        stop: Optional[int] = None,
        window: int = 5,
        skip: int = 0,
        year_mode: bool = False,
        max_tries: int = 8,
    ) -> Optional[ExtractedValue]:
        """Find the first label match that yields a valid number >= min_abs.

        Retries up to max_tries times. Falls back to table then coordinate
        extraction when text linearization gives no number (multi-column PDFs).
        """
        search_from = start
        last_ev: Optional[ExtractedValue] = None

        for _ in range(max_tries):
            hit = self._find_first(patterns, search_from, stop)
            if hit is None:
                break
            line_idx, page_no, label_line = hit

            if year_mode:
                ctx = self._context_str(line_idx, window)
                m = re.search(r"\b(19\d{2}|20[012]\d)\b", ctx)
                if m:
                    yr = float(m.group(1))
                    return ExtractedValue(
                        label_as_printed=label_line,
                        value=yr,
                        page=page_no,
                        context=ctx[:150],
                        confidence="low" if self.result.ocr_heavy else "medium",
                    )
                search_from = line_idx + 1
                continue

            ctx = self._context_str(line_idx, window)
            found = _first_number(ctx, min_abs=min_abs, skip=skip)
            if found is None:
                ctx = self._context_str(line_idx, window * 2)
                found = _first_number(ctx, min_abs=min_abs, skip=skip)

            if found is not None:
                _, val = found
                return ExtractedValue(
                    label_as_printed=label_line,
                    value=val,
                    page=page_no,
                    context=ctx[:150],
                    confidence="low" if self.result.ocr_heavy else "high",
                )

            # Text gave no number: try structured table extraction.
            ev_tbl = self._ev_from_table(page_no, patterns, min_abs=min_abs)
            if ev_tbl:
                return ev_tbl

            # Try coordinate extraction (multi-column / split-block PDFs).
            ev_coord = self._ev_from_coords(page_no, patterns, min_abs=min_abs)
            if ev_coord:
                return ev_coord

            last_ev = ExtractedValue(
                label_as_printed=label_line,
                value=None,
                page=page_no,
                context=ctx[:150],
                confidence="low",
                note="label found but no number extracted",
            )
            search_from = line_idx + 1

        return last_ev

    # ---- extraction passes --------------------------------------------------

    def _extract_currency_unit(self) -> None:
        r = self.result

        # High-priority: look for explicit "in [CURRENCY] thousands/millions"
        # or "[CURRENCY] thousands" on the same line (FS header style).
        explicit_re = re.compile(
            r"\b(in|expressed\s+in|amounts?\s+(?:are\s+)?in)\b.*\b"
            r"(thousands?|millions?|billions?)\b",
            re.IGNORECASE,
        )
        unit_re = re.compile(
            r"\b(thousands?|millions?|billions?|'000s?|,000s?)\b", re.IGNORECASE
        )

        scan_ranges = []
        if self._fs_start:
            scan_ranges.append(self._lines[self._fs_start: self._fs_start + 800])
        scan_ranges.append(self._lines[:800])

        for scan in scan_ranges:
            for page_no, line in scan:
                lc = line.lower()

                # Try to detect currency and unit together on the same line.
                line_cur: Optional[str] = None
                for cur in _CURRENCIES:
                    if re.search(rf"\b{cur}\b", line):
                        line_cur = cur
                        break
                # Also check aliases (KD, RO, BD, SR).
                if line_cur is None:
                    for alias, canon in _CURRENCY_ALIASES.items():
                        if re.search(rf"\b{alias}\b", line):
                            line_cur = canon
                            break

                line_unit: Optional[str] = None
                if re.search(r"'000s?|,000s?|\(000\)|in\s+thousands?|thousands?\s+of", lc):
                    line_unit = "thousands"
                elif re.search(r"in\s+millions?|millions?\s+of\b", lc):
                    line_unit = "millions"
                elif re.search(r"in\s+billions?", lc):
                    line_unit = "billions"

                # If both are on the same line, very high confidence.
                if line_cur and line_unit:
                    if r.currency is None:
                        r.currency = line_cur
                        r.currency_page = page_no
                    if r.unit is None:
                        r.unit = line_unit
                    break

            if r.currency and r.unit:
                break

        # Second pass: find unit and currency separately if not found together.
        if r.unit is None or r.currency is None:
            for scan in scan_ranges:
                for page_no, line in scan:
                    lc = line.lower()
                    if r.unit is None:
                        if re.search(r"'000s?|,000s?|\(000\)|in\s+thousands?|thousands?\s+of", lc):
                            r.unit = "thousands"
                        elif re.search(r"in\s+millions?|millions?\s+of\b", lc):
                            r.unit = "millions"
                        elif re.search(r"in\s+billions?", lc):
                            r.unit = "billions"
                    if r.currency is None:
                        for cur in _CURRENCIES:
                            if re.search(rf"\b{cur}\b", line):
                                r.currency = cur
                                r.currency_page = page_no
                                break
                        if r.currency is None:
                            for alias, canon in _CURRENCY_ALIASES.items():
                                if re.search(rf"\b{alias}\b", line):
                                    r.currency = canon
                                    r.currency_page = page_no
                                    break
                    if r.currency and r.unit:
                        break
                if r.currency and r.unit:
                    break

        # Last resort: any currency mention anywhere.
        if r.currency is None:
            for page_no, line in self._lines:
                for cur in _CURRENCIES:
                    if re.search(rf"\b{cur}\b", line):
                        r.currency = cur
                        r.currency_page = page_no
                        break
                if r.currency is None:
                    for alias, canon in _CURRENCY_ALIASES.items():
                        if re.search(rf"\b{alias}\b", line):
                            r.currency = canon
                            r.currency_page = page_no
                            break
                if r.currency:
                    break

    def _extract_balance_sheet(self) -> None:
        r = self.result
        fs = self._fs_start
        r.total_assets = self._extract_ev(
            _PATTERNS["total_assets"], min_abs=1_000, start=fs
        )
        r.total_liabilities = self._extract_ev(
            _PATTERNS["total_liabilities"], min_abs=1_000, start=fs
        )
        r.total_equity = self._extract_ev(
            _PATTERNS["total_equity"], min_abs=1_000, start=fs
        )

        # equity_attributable: try total-prefixed labels first.
        r.equity_attributable = self._extract_ev(
            _PATTERNS["equity_attributable_total"], min_abs=1_000, start=fs
        )
        if r.equity_attributable is None or r.equity_attributable.value is None:
            r.equity_attributable = self._extract_ev(
                _PATTERNS["equity_attributable_fallback"], min_abs=1_000, start=fs
            )

        # Compute equity_attributable from TE - NCI when:
        # (a) not found explicitly, OR
        # (b) the fallback value is suspiciously small (< 50% of TE) — this happens
        #     when the "Equity attributable to owners" section header is matched and
        #     the first child number (share capital) is returned instead of the total.
        ea_val = r.equity_attributable.value if r.equity_attributable else None
        te_val = r.total_equity.value if r.total_equity else None
        suspicious = (
            ea_val is not None
            and te_val is not None
            and "computed" not in (r.equity_attributable.label_as_printed or "")
            and ea_val < 0.5 * te_val
        )
        if (r.equity_attributable is None or r.equity_attributable.value is None
                or suspicious):
            # Search for NCI starting from TE's page to prefer the EQUITY section
            # NCI over the IS "attributable to NCI" line (which appears on an earlier
            # page when the income statement precedes the balance sheet).
            nci_start = fs
            if r.total_equity and r.total_equity.page:
                for _i, (_pg, _) in enumerate(self._lines):
                    if _pg == r.total_equity.page:
                        nci_start = _i
                        break
            nci = self._extract_ev(
                _PATTERNS["non_controlling_interests"], min_abs=100, start=nci_start
            )
            if nci and nci.value is not None and r.total_equity and r.total_equity.value:
                derived = r.total_equity.value - nci.value
                if ea_val is None or derived > ea_val:
                    r.equity_attributable = ExtractedValue(
                        label_as_printed="(computed: total_equity - non_controlling_interests)",
                        value=derived,
                        page=r.total_equity.page,
                        context=f"TE={r.total_equity.value:.0f}  NCI={nci.value:.0f}",
                        confidence="medium",
                        note="computed from TE - NCI",
                    )

        # Last-resort: no NCI found → assume 100% parent ownership (EA = TE).
        # Marked low-confidence; the full-run EPS consistency check will flag
        # anomalies when a real NCI exists.
        if (r.equity_attributable is None or r.equity_attributable.value is None):
            if r.total_equity and r.total_equity.value:
                r.equity_attributable = ExtractedValue(
                    label_as_printed="(assumed: no NCI found, EA = TE)",
                    value=r.total_equity.value,
                    page=r.total_equity.page,
                    context=f"TE={r.total_equity.value:.0f}",
                    confidence="low",
                    note="assumed 100% parent ownership (no NCI row found)",
                )

        # Compute total_liabilities from balancing equation if missing.
        if r.total_liabilities is None:
            tl_eq = self._extract_ev(
                _PATTERNS["total_liabilities_and_equity"], min_abs=1_000, start=fs
            )
            if tl_eq and tl_eq.value and r.total_equity and r.total_equity.value:
                derived = tl_eq.value - r.total_equity.value
                r.total_liabilities = ExtractedValue(
                    label_as_printed="(computed: total-liab-and-equity - total-equity)",
                    value=derived,
                    page=tl_eq.page,
                    context=tl_eq.context,
                    confidence="medium",
                    note="computed",
                )
                r.total_liabilities_computed = True

        # If we have TA, TE, and TL but the balance sheet does not balance
        # (gap > 20%), recompute TL = TA - TE.  This handles formats like
        # Jazeera Airways where the "Total liabilities" label refers only to
        # current liabilities and the non-current block has no labelled total.
        if (r.total_assets and r.total_assets.value
                and r.total_equity and r.total_equity.value
                and r.total_liabilities and r.total_liabilities.value):
            _ta = r.total_assets.value
            _te = r.total_equity.value
            _tl = r.total_liabilities.value
            if abs(_tl + _te - _ta) / _ta > 0.20:
                r.total_liabilities = ExtractedValue(
                    label_as_printed="(computed: total_assets - total_equity)",
                    value=_ta - _te,
                    page=r.total_assets.page,
                    context=f"TA={_ta:.0f}  TE={_te:.0f}",
                    confidence="medium",
                    note="computed from TA - TE (BS_MISMATCH > 20%)",
                )
                r.total_liabilities_computed = True

    def _extract_income_statement(self) -> None:
        """Use the income statement section start for revenue so infographic
        pages before the FS are not matched. Net profit and NPA also search
        from the IS section to avoid segment analysis tables later in the FS."""
        r = self.result
        is_start = self._is_start
        rev_patterns = (
            _PATTERNS["revenue_bank"] if r.is_bank else _PATTERNS["revenue_nonbank"]
        )
        r.revenue = self._extract_ev(rev_patterns, min_abs=1_000, start=is_start)
        r.net_profit = self._extract_ev(
            _PATTERNS["net_profit"], min_abs=100, start=is_start
        )
        r.net_profit_attributable = self._extract_ev(
            _PATTERNS["net_profit_attributable"], min_abs=100, start=is_start
        )
        # Fallback: if no explicit NPA attribution line found (e.g. 100%-parent
        # companies or Islamic banks that don't split by NCI), use NP as NPA.
        if (r.net_profit_attributable is None or r.net_profit_attributable.value is None):
            if r.net_profit and r.net_profit.value is not None:
                r.net_profit_attributable = ExtractedValue(
                    label_as_printed="(assumed: no NCI attribution found, NPA = NP)",
                    value=r.net_profit.value,
                    page=r.net_profit.page,
                    context=f"NP={r.net_profit.value:.0f}",
                    confidence="low",
                    note="assumed 100% parent NP (no NCI attribution row found)",
                )

    def _extract_per_share(self) -> None:
        r = self.result
        r.basic_eps = self._extract_ev(
            _PATTERNS["basic_eps"], min_abs=0.0, window=6, start=self._is_start
        )
        # Primary shares: issued/outstanding from share capital note (FS section).
        # Use min_abs=1_000 to skip par-value numbers (e.g. SAR 10 per share).
        r.shares_outstanding = self._extract_ev(
            _PATTERNS["shares_outstanding"], min_abs=1_000, window=6,
            start=self._fs_start,
        )
        # Supplementary: weighted-average shares from the EPS note.
        r.shares_eps_note = self._extract_ev(
            _PATTERNS["shares_eps_note"], min_abs=1_000, window=6,
            start=self._is_start,
        )
        # EPS numerator: profit after AT1 deductions used for basic EPS.
        r.eps_numerator = self._extract_ev(
            _PATTERNS["eps_numerator"], min_abs=100, window=6,
            start=self._is_start,
        )

    def _extract_supplementary(self) -> None:
        """Extract items that complement the core FS: gross bank income,
        borrowings, market data, AT1 equity.  Share price and market cap
        are often in the highlights section BEFORE the FS boundary, so we
        scan the full document for those two items."""
        r = self.result
        fs = self._fs_start
        is_s = self._is_start

        if r.is_bank:
            r.gross_income_bank = self._extract_ev(
                _PATTERNS["gross_income_bank"], min_abs=1_000, start=is_s
            )

        r.total_borrowings = self._extract_ev(
            _PATTERNS["total_borrowings"], min_abs=1_000, start=fs
        )

        # AT1 / Tier-1 sukuk in equity: search from TE's page to stay in the
        # equity section of the BS and avoid picking up AT1 income-statement lines.
        at1_start = fs
        if r.total_equity and r.total_equity.page:
            for _i, (_pg, _) in enumerate(self._lines):
                if _pg == r.total_equity.page:
                    at1_start = _i
                    break
        r.at1_equity = self._extract_ev(
            _PATTERNS["at1_equity"], min_abs=100, start=at1_start
        )

        # Share price and market cap may appear in the highlights / KPI section
        # which is before the FS boundary → search from line 0.
        r.share_price_year_end = self._extract_ev(
            _PATTERNS["share_price"], min_abs=0.01, start=0
        )
        r.market_cap = self._extract_ev(
            _PATTERNS["market_cap"], min_abs=1_000, start=0
        )

    def _extract_history(self) -> None:
        r = self.result
        fs = self._fs_start
        r.year_of_incorporation = self._extract_ev(
            _PATTERNS["year_incorporation"], year_mode=True, window=8, start=fs
        )
        r.year_of_listing = self._extract_ev(
            _PATTERNS["year_listing"], year_mode=True, window=8, start=fs
        )

    # ---- checks and ratios --------------------------------------------------

    def _check_flags(self) -> None:
        r = self.result
        flags = r.flags

        def v(ev: Optional[ExtractedValue]) -> Optional[float]:
            return ev.value if ev and ev.value is not None else None

        ta = v(r.total_assets)
        tl = v(r.total_liabilities)
        te = v(r.total_equity)

        if ta and tl is not None and te is not None:
            lhs = tl + te
            gap = abs(lhs - ta) / ta if ta else 0
            if gap > 0.01:
                flags.append(
                    f"BS_MISMATCH: assets={ta:,.0f}  liab+equity={lhs:,.0f}"
                    f"  ({gap:.1%} off)"
                )

        np_ = v(r.net_profit)
        npa = v(r.net_profit_attributable)
        if np_ is not None and npa is not None:
            if abs(npa) > abs(np_) * 1.001:
                flags.append(
                    f"NP_ATTR_GT_TOTAL: attributable={npa:,.0f}  total={np_:,.0f}"
                )

        eps = v(r.basic_eps)
        # Use EPS numerator if available; fall back to NPA.
        eps_num = v(r.eps_numerator)
        shr = v(r.shares_outstanding)
        # If primary share count not found, try EPS-note shares for consistency check.
        if shr is None:
            shr = v(r.shares_eps_note)
        if eps is not None and shr is not None and shr > 0:
            unit_mult = {
                "thousands": 1_000,
                "millions": 1_000_000,
                "billions": 1_000_000_000,
            }.get(r.unit or "", 1)
            numerator = eps_num if eps_num is not None else npa
            if numerator is not None and abs(eps) > 0:
                # Shares may be in individual units OR in the same financial
                # unit (thousands/millions). Try both; if either is within the
                # tolerance, accept it. Tolerance = max(15%, absolute 0.05) to
                # avoid false positives when EPS is reported to only 2 d.p.
                src = "eps_num" if eps_num is not None else "NPA"
                c_with = (numerator * unit_mult) / shr   # shares in individual units
                c_bare  = numerator / shr                # shares in financial units
                tol = max(abs(eps) * 0.15, 0.05)
                ok_with = abs(c_with - eps) <= tol
                ok_bare  = abs(c_bare  - eps) <= tol
                if not ok_with and not ok_bare:
                    flags.append(
                        f"EPS_MISMATCH: reported={eps:.4f}  "
                        f"computed_ind={c_with:.4f}  computed_fin={c_bare:.4f}"
                        f"  ({src}/shares)"
                    )

        if r.ocr_heavy:
            flags.append("OCR_HEAVY: values may be low confidence")

        if self._fs_start == 0:
            flags.append(
                "FS_BOUNDARY_NOT_FOUND: no auditor's report / FS section detected; "
                "PDF may contain only narrative/governance pages without FS"
            )

    def _compute_ratios(self) -> None:
        r = self.result

        def v(ev: Optional[ExtractedValue]) -> Optional[float]:
            return ev.value if ev and ev.value is not None else None

        ta   = v(r.total_assets)
        tl   = v(r.total_liabilities)
        te   = v(r.total_equity)
        ea   = v(r.equity_attributable)
        rev  = v(r.revenue)
        np_  = v(r.net_profit)
        npa  = v(r.net_profit_attributable)
        at1  = v(r.at1_equity) or 0.0
        eps_num = v(r.eps_numerator)

        if tl is not None and ta and ta != 0:
            r.leverage = round(tl / ta, 4)
        if np_ is not None and ta and ta != 0:
            r.roa = round(np_ / ta, 4)
        if np_ is not None and rev and rev != 0:
            r.net_profit_margin = round(np_ / rev, 4)

        # RoE: primary uses eps_numerator / (equity_attributable - AT1).
        # Fallback uses npa / equity_attributable when eps_numerator not found.
        eq_base = ea if ea is not None else te
        if eq_base:
            eq_ord = eq_base - at1
            r.equity_ordinary = round(eq_ord, 0) if eq_ord > 0 else None
        else:
            eq_ord = None
            r.equity_ordinary = None

        if eps_num is not None and eq_ord and eq_ord > 0:
            r.roe = round(eps_num / eq_ord, 4)
            r.roe_eps_based = True
        elif npa is not None and eq_ord and eq_ord > 0:
            r.roe = round(npa / eq_ord, 4)
            r.roe_eps_based = False
            if at1 > 0:
                r.flags.append(
                    "ROE_NPA_FALLBACK: EPS numerator not found; RoE uses NPA/equity_ordinary"
                )

        inc = v(r.year_of_incorporation)
        lst = v(r.year_of_listing)
        if inc:
            r.firm_age = r.fiscal_year - int(inc)
        if lst:
            r.listing_age = r.fiscal_year - int(lst)

    # ---- public entry point -------------------------------------------------

    def extract(self) -> FinancialRow:
        self.load()
        self._extract_currency_unit()
        self._extract_balance_sheet()
        self._extract_income_statement()
        self._extract_per_share()
        self._extract_supplementary()
        self._extract_history()
        self._check_flags()
        self._compute_ratios()
        return self.result


# ---- DB manifest ------------------------------------------------------------


def _load_manifest() -> list[dict]:
    db = SessionLocal()
    try:
        rows = db.execute(
            select(
                Institution.slug,
                Institution.name,
                Institution.is_financial,
                Institution.institution_type,
                SourceDocument.fiscal_year,
                SourceDocument.file_path,
                SourceDocument.sha256,
            )
            .join(SourceDocument, SourceDocument.institution_id == Institution.id)
            .where(Institution.active.is_(True))
            .where(SourceDocument.superseded_by_id.is_(None))
            .order_by(Institution.slug, SourceDocument.fiscal_year)
        ).all()
    finally:
        db.close()

    out = []
    for slug, name, is_fin, inst_type, fy, fp, sha in rows:
        is_bank = inst_type == InstitutionType.bank or (is_fin and inst_type is None)
        out.append(
            {
                "slug": slug,
                "name": name,
                "is_bank": is_bank,
                "fiscal_year": fy,
                "r2_key": fp or "",
                "sha256": sha,
            }
        )
    return out


# ---- terminal output (pilot) ------------------------------------------------

_SEP = "-" * 80


def _fmt_ev(label: str, ev: Optional[ExtractedValue]) -> str:
    if ev is None:
        return f"  {label:<30}  NOT FOUND"
    val_str = (
        f"{ev.value:>20,.2f}" if ev.value is not None else f"  {'(no value)':>18}"
    )
    conf = f"[{ev.confidence}]" if ev.confidence != "high" else ""
    note = f"  <- {ev.note}" if ev.note else ""
    ctx_preview = ev.context[:80].replace("\n", " ")
    return (
        f"  {label:<30}  {val_str}  p.{ev.page:<4}  {conf}{note}\n"
        f"    label: {ev.label_as_printed[:70]}\n"
        f"    ctx  : {ctx_preview}"
    )


def _fmt_ratio(label: str, val: Optional[float], pct: bool = False) -> str:
    if val is None:
        return f"  {label:<25}  n/a"
    if pct:
        return f"  {label:<25}  {val * 100:>8.2f}%"
    return f"  {label:<25}  {val:>10.4f}"


def print_pilot_result(row: FinancialRow) -> None:
    print(_SEP)
    print(f"  {row.slug}  FY{row.fiscal_year}  {'(BANK)' if row.is_bank else ''}")
    print(_SEP)
    print(f"  Currency / unit  : {row.currency or '?'} {row.unit or 'whole-units'}  (p.{row.currency_page})")
    print(f"  OCR-heavy        : {row.ocr_heavy}")
    print()

    print("  -- Balance sheet " + "-" * 62)
    print(_fmt_ev("Total assets", row.total_assets))
    liab_label = (
        "Total liabilities [computed]"
        if row.total_liabilities_computed
        else "Total liabilities"
    )
    print(_fmt_ev(liab_label, row.total_liabilities))
    print(_fmt_ev("Total equity", row.total_equity))
    print(_fmt_ev("Equity attributable", row.equity_attributable))
    print()

    print("  -- Income statement " + "-" * 59)
    rev_label = "Revenue (total oper. income)" if row.is_bank else "Revenue"
    print(_fmt_ev(rev_label, row.revenue))
    if row.is_bank:
        print(_fmt_ev("Gross income (bank)", row.gross_income_bank))
    print(_fmt_ev("Net profit (total)", row.net_profit))
    print(_fmt_ev("Net profit attributable", row.net_profit_attributable))
    print(_fmt_ev("EPS numerator", row.eps_numerator))
    print()

    print("  -- Per share & shares " + "-" * 57)
    print(_fmt_ev("Basic EPS (as reported)", row.basic_eps))
    print(_fmt_ev("Shares issued (cap note)", row.shares_outstanding))
    print(_fmt_ev("Shares wtd-avg (EPS note)", row.shares_eps_note))
    print()

    print("  -- Supplementary " + "-" * 62)
    print(_fmt_ev("Total borrowings", row.total_borrowings))
    print(_fmt_ev("AT1 / Tier-1 sukuk (equity)", row.at1_equity))
    print(_fmt_ev("Share price year-end", row.share_price_year_end))
    print(_fmt_ev("Market cap", row.market_cap))
    print()

    print("  -- Corporate history " + "-" * 58)
    print(_fmt_ev("Year of incorporation", row.year_of_incorporation))
    print(_fmt_ev("Year of listing", row.year_of_listing))
    print()

    roe_method = "(eps_num/eq_ord)" if row.roe_eps_based else "(NPA/eq_ord)"
    eq_ord_str = f"{row.equity_ordinary:,.0f}" if row.equity_ordinary else "n/a"
    print("  -- Ratios " + "-" * 69)
    print(_fmt_ratio("Leverage (TL/TA)", row.leverage))
    print(_fmt_ratio("RoA (NP/TA)", row.roa, pct=True))
    print(f"  {'RoE '+roe_method:<25}  "
          + (f"{row.roe * 100:>8.2f}%" if row.roe is not None else "    n/a"))
    print(f"  {'Equity ordinary':<25}  {eq_ord_str:>12}")
    print(_fmt_ratio("Net profit margin", row.net_profit_margin, pct=True))
    print(_fmt_ratio("Firm age (FY - incorp.)", row.firm_age))
    print(_fmt_ratio("Listing age (FY - listing)", row.listing_age))
    print()

    if row.flags:
        print("  -- Flags " + "-" * 70)
        for f in row.flags:
            print(f"    [FLAG]  {f}")
    else:
        print("  -- Flags: none")
    print()


# ---- Excel / CSV export (full run) ------------------------------------------

def _ev_cols(prefix: str, ev: Optional[ExtractedValue]) -> dict:
    if ev is None:
        return {
            f"{prefix}_value": None,
            f"{prefix}_page": None,
            f"{prefix}_label": None,
            f"{prefix}_confidence": None,
            f"{prefix}_note": None,
        }
    return {
        f"{prefix}_value": ev.value,
        f"{prefix}_page": ev.page,
        f"{prefix}_label": ev.label_as_printed[:120],
        f"{prefix}_confidence": ev.confidence,
        f"{prefix}_note": ev.note or None,
    }


def row_to_dict(row: FinancialRow) -> dict:
    d: dict = {
        "slug": row.slug,
        "fiscal_year": row.fiscal_year,
        "r2_key": row.r2_key,
        "is_bank": row.is_bank,
        "currency": row.currency,
        "unit": row.unit,
        "currency_page": row.currency_page,
        "total_liabilities_computed": row.total_liabilities_computed,
        "ocr_heavy": row.ocr_heavy,
        # Computed ratios
        "leverage": row.leverage,
        "roa": row.roa,
        "roe": row.roe,
        "roe_eps_based": row.roe_eps_based,
        "equity_ordinary": row.equity_ordinary,
        "net_profit_margin": row.net_profit_margin,
        "firm_age": row.firm_age,
        "listing_age": row.listing_age,
        "flags": "; ".join(row.flags) if row.flags else None,
    }
    for prefix, ev in [
        ("total_assets",             row.total_assets),
        ("total_liabilities",        row.total_liabilities),
        ("total_equity",             row.total_equity),
        ("equity_attributable",      row.equity_attributable),
        ("revenue",                  row.revenue),
        ("gross_income_bank",        row.gross_income_bank),
        ("net_profit",               row.net_profit),
        ("net_profit_attributable",  row.net_profit_attributable),
        ("eps_numerator",            row.eps_numerator),
        ("basic_eps",                row.basic_eps),
        ("shares_outstanding",       row.shares_outstanding),   # share capital note
        ("shares_eps_note",          row.shares_eps_note),      # EPS note wtd-avg
        ("total_borrowings",         row.total_borrowings),
        ("at1_equity",               row.at1_equity),
        ("share_price_year_end",     row.share_price_year_end),
        ("market_cap",               row.market_cap),
        ("year_of_incorporation",    row.year_of_incorporation),
        ("year_of_listing",          row.year_of_listing),
    ]:
        d.update(_ev_cols(prefix, ev))
    return d


# Characters that openpyxl rejects as illegal in XML/xlsx (control chars,
# U+FFFD replacement char that PyMuPDF emits for undecodable bytes, etc.)
_ILLEGAL_XML_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f�￾￿]")


def _xl(val: object) -> object:
    """Sanitize a value for openpyxl: strip illegal XML characters from strings."""
    if isinstance(val, str):
        return _ILLEGAL_XML_RE.sub("", val)
    return val


def _write_xlsx(records: list[dict], xlsx_path: Path) -> None:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "financials"

    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(bold=True, color="FFFFFF")
    cols = list(records[0].keys())
    for col_i, col_name in enumerate(cols, start=1):
        cell = ws.cell(row=1, column=col_i, value=col_name)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for row_i, rec in enumerate(records, start=2):
        for col_i, col_name in enumerate(cols, start=1):
            ws.cell(row=row_i, column=col_i, value=_xl(rec[col_name]))

    for col_i, col_name in enumerate(cols, start=1):
        ws.column_dimensions[
            openpyxl.utils.get_column_letter(col_i)
        ].width = max(12, min(40, len(col_name) + 4))

    wb.save(xlsx_path)
    print(f"XLSX -> {xlsx_path}")


def write_excel_csv(rows: list[FinancialRow]) -> None:
    import csv

    out_dir = REPO_ROOT / "docs" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = out_dir / "financials_extracted.xlsx"
    csv_path  = out_dir / "financials_extracted.csv"

    records = [row_to_dict(r) for r in rows]
    if not records:
        print("No rows to export.")
        return

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    print(f"CSV  -> {csv_path}")

    _write_xlsx(records, xlsx_path)


def write_xlsx_from_csv(csv_path: Path, xlsx_path: Path) -> None:
    """Read the existing CSV and write xlsx — avoids re-running the full extraction."""
    import csv

    _NUMERIC_COLS = {
        "fiscal_year", "currency_page", "leverage", "roa", "roe",
        "equity_ordinary", "net_profit_margin", "firm_age", "listing_age",
        "total_assets_value", "total_liabilities_value", "total_equity_value",
        "equity_attributable_value", "revenue_value", "gross_income_bank_value",
        "net_profit_value", "net_profit_attributable_value", "eps_numerator_value",
        "basic_eps_value", "shares_outstanding_value", "shares_eps_note_value",
        "total_borrowings_value", "at1_equity_value", "share_price_year_end_value",
        "market_cap_value", "year_of_incorporation_value", "year_of_listing_value",
        "total_assets_page", "total_liabilities_page", "total_equity_page",
        "equity_attributable_page", "revenue_page", "gross_income_bank_page",
        "net_profit_page", "net_profit_attributable_page", "eps_numerator_page",
        "basic_eps_page", "shares_outstanding_page", "shares_eps_note_page",
        "total_borrowings_page", "at1_equity_page", "share_price_year_end_page",
        "market_cap_page", "year_of_incorporation_page", "year_of_listing_page",
    }
    _BOOL_COLS = {
        "is_bank", "total_liabilities_computed", "ocr_heavy", "roe_eps_based",
    }

    def _coerce(col: str, raw: str) -> object:
        if raw == "":
            return None
        if col in _BOOL_COLS:
            return raw.lower() == "true"
        if col in _NUMERIC_COLS:
            try:
                return float(raw)
            except ValueError:
                return raw
        return raw

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        records = [
            {col: _coerce(col, val or "") for col, val in row.items()}
            for row in reader
        ]

    if not records:
        print("CSV is empty.")
        return

    _write_xlsx(records, xlsx_path)


# ---- main -------------------------------------------------------------------

PILOT_CASES = [
    ("al-rajhi-bank",       2023),
    ("sabic",               2022),
    ("ooredoo-q-p-s-c",    2021),
    ("emaar-properties",    2024),
    ("jarir-marketing-co",  2020),
    ("jazeera-airways",     2025),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--all",   action="store_true")
    ap.add_argument("--write-xlsx", action="store_true",
                    help="Write xlsx from the existing CSV without re-running extraction")
    ap.add_argument("--slug")
    ap.add_argument("--fy", type=int)
    args = ap.parse_args()

    if args.write_xlsx:
        csv_path  = REPO_ROOT / "docs" / "exports" / "financials_extracted.csv"
        xlsx_path = REPO_ROOT / "docs" / "exports" / "financials_extracted.xlsx"
        write_xlsx_from_csv(csv_path, xlsx_path)
        return 0

    manifest = _load_manifest()
    by_key = {(m["slug"], m["fiscal_year"]): m for m in manifest}

    if args.pilot:
        cases = PILOT_CASES
    elif args.all:
        cases = [(m["slug"], m["fiscal_year"]) for m in manifest]
    elif args.slug and args.fy:
        cases = [(args.slug, args.fy)]
    else:
        ap.print_help()
        return 1

    results: list[FinancialRow] = []
    errors: list[str] = []

    for slug, fy in cases:
        meta = by_key.get((slug, fy))
        if meta is None:
            msg = f"NOT IN DB: {slug} FY{fy}"
            print(msg)
            errors.append(msg)
            continue
        r2_key = meta["r2_key"]
        if not r2_key:
            msg = f"NO R2 KEY: {slug} FY{fy}"
            print(msg)
            errors.append(msg)
            continue

        print(f"Extracting {slug} FY{fy} ...", flush=True)
        try:
            row = PDFFinancialExtractor(
                slug=slug, fiscal_year=fy, r2_key=r2_key, is_bank=meta["is_bank"]
            ).extract()
        except Exception as exc:
            msg = f"ERROR {slug} FY{fy}: {exc}"
            print(msg)
            errors.append(msg)
            continue

        results.append(row)
        if args.pilot or (args.slug and args.fy):
            print_pilot_result(row)

    if args.all:
        write_excel_csv(results)

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  {e}")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
