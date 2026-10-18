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

    # Non-bank debt components (each with page + label)
    st_borrowings: Optional[ExtractedValue] = None       # short-term / current borrowings
    lt_borrowings: Optional[ExtractedValue] = None       # long-term / non-current borrowings
    sukuk_bonds_notes: Optional[ExtractedValue] = None   # sukuk, bonds, notes payable
    lease_liabilities_nb: Optional[ExtractedValue] = None  # IFRS 16 lease liabilities
    # Bank debt components
    due_to_banks_fi: Optional[ExtractedValue] = None     # due to banks & financial institutions
    sukuk_issued_bank: Optional[ExtractedValue] = None   # sukuk / debt securities issued by bank
    subordinated_debt_bank: Optional[ExtractedValue] = None  # tier-2 / subordinated notes

    total_debt: Optional[float] = None
    total_debt_status: str = "not_found"  # "extracted" | "zero" | "not_found"
    eps_in_fils_baisa: bool = False

    leverage: Optional[float] = None      # primary: total_debt / equity_attributable
    leverage_alt: Optional[float] = None  # secondary: total_liabilities / total_assets
    roa: Optional[float] = None           # NP/TA × 100 (%)
    roe: Optional[float] = None           # NPA/eq_ord × 100 (%)
    roe_eps_based: bool = False  # True = RoE uses eps_numerator / equity_ordinary
    equity_ordinary: Optional[float] = None  # EA - AT1 (RoE denominator)
    net_profit_margin: Optional[float] = None   # primary: NP/rev×100 non-banks; NP/gross_inc×100 banks
    net_margin_alt: Optional[float] = None      # NP/total_oper_income×100 banks; same as primary non-banks
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
        # Islamic / GCC aggregated labels
        r"^total\s+(?:bank\s+)?(?:facilities?|financing)\s*$",
        r"^total\s+(?:murabaha|tawarruq|wakala|islamic)\s+(?:financing\s+)?(?:facilities?|payables?|loans?)\s*$",
        r"^total\s+loans?\s+and\s+(?:bank\s+)?facilities?\s*$",
        r"^loans?\s+and\s+(?:bank\s+)?facilities?\s*$",
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
    # ---- Non-bank debt components (balance sheet) --------------------------------
    "st_borrowings": [
        r"^short[\s-]?term\s+(?:bank\s+)?(?:loans?\s+and\s+)?borrowings?\s*$",
        r"^bank\s+(?:loans?\s+and\s+)?borrowings?\s*$",
        r"^overdrafts?\s+(?:and\s+short[\s-]?term\s+loans?)?\s*$",
        r"^current\s+portion\s+of\s+(?:long[\s-]?term\s+)?(?:loans?|borrowings?|financing)\s*$",
        r"^due\s+to\s+banks?\s*$",
        r"^bank\s+overdrafts?\s*$",
        r"^short[\s-]?term\s+financing\s+facilities?\s*$",
        # Islamic / GCC labels
        r"^(?:short[\s-]?term\s+)?(?:murabaha|tawarruq|wakala)\s+(?:financing\s+)?(?:facilities?|payables?)\s*$",
        r"^current\s+(?:portion\s+of\s+)?(?:murabaha|tawarruq|wakala|islamic)\s+(?:financing|facilities?|payables?)\s*$",
        r"^bank\s+facilities?\s*$",
        r"^banking\s+facilities?\s*$",
        r"^loans?\s+and\s+banking\s+facilities?\s*$",
        r"^credit\s+facilities?\s*$",
        r"^revolving\s+credit\s+(?:facilities?|lines?)\s*$",
        r"^short[\s-]?term\s+loans?\s*$",
    ],
    "lt_borrowings": [
        r"^long[\s-]?term\s+(?:bank\s+)?(?:loans?\s+and\s+)?borrowings?\s*$",
        r"^long[\s-]?term\s+(?:term\s+)?(?:loans?|financing)\s+facilities?\s*$",
        r"^non[\s-]?current\s+(?:portion\s+of\s+)?(?:loans?\s+and\s+)?borrowings?\s*$",
        r"^term\s+(?:loans?\s+and\s+)?financing\s+facilities?\s*$",
        r"^murabaha\s+financing\s+(?:facilities?|payables?)\s*$",
        r"^long[\s-]?term\s+debt\s*$",
        # Islamic / GCC labels
        r"^(?:long[\s-]?term\s+|non[\s-]?current\s+)?(?:murabaha|tawarruq|wakala)\s+(?:financing\s+)?(?:facilities?|payables?)\s*$",
        r"^(?:long[\s-]?term\s+|non[\s-]?current\s+)?islamic\s+(?:financing|facilities?|loans?)\s*$",
        r"^islamic\s+(?:term\s+)?(?:financing|facilities?)\s*$",
        r"^(?:SIDF|sidf)\s+(?:loans?|financing)\s*$",
        r"^syndicated\s+(?:facilities?|loans?|financing)\s*$",
        r"^bilateral\s+(?:facilities?|loans?|financing)\s*$",
        r"^medium[\s-]?term\s+(?:loans?|facilities?|financing)\s*$",
        r"^long[\s-]?term\s+loans?\s*$",
        r"^term\s+loans?\s*$",
    ],
    "sukuk_bonds_notes": [
        r"^sukuk\s+(?:financings?|payable|issued|bonds?)\s*$",
        r"^bonds?\s+payable\s*$",
        r"^bonds?\s+and\s+sukuk\s*$",
        r"^sukuk\s*$",
        r"^notes?\s+payable\s*$",
        r"^(?:listed\s+)?(?:islamic\s+)?bonds?\s*$",
        r"^sukuk\s+(?:certificates?\s+)?payable\s*$",
        r"^Islamic\s+sukuk\s*$",
        r"^trust\s+(?:certificates?|notes?)\s*$",
    ],
    "lease_liabilities_nb": [
        r"^lease\s+liabilities?\s*$",
        r"^right[\s-]?of[\s-]?use\s+liabilities?\s*$",
        r"^finance\s+(?:and\s+operating\s+)?lease\s+(?:obligations?|liabilities?)\s*$",
        r"^(?:total\s+)?lease\s+liabilities?\s*$",
        r"^operating\s+lease\s+liabilities?\s*$",
        r"^ifrs\s+16\s+lease\s+liabilities?\s*$",
    ],
    # ---- Bank debt components (balance sheet) ------------------------------------
    "due_to_banks_fi": [
        r"^due\s+to\s+banks?\s+and\s+(?:other\s+)?financial\s+institutions?\s*$",
        r"^due\s+to\s+(?:financial\s+institutions?|banks?)\s*$",
        # Saudi / Islamic banks: SAMA appears before "banks" in the label
        r"^due\s+to\s+SAMA,?\s+banks?\s+and\s+(?:other\s+)?financial\s+institutions?\s*$",
        r"^due\s+to\s+(?:SAMA\s+and\s+)?banks?\s+and\s+(?:other\s+)?financial\s+institutions?\s*$",
        r"^amounts?\s+due\s+to\s+banks?\s+and\s+(?:other\s+)?financial\s+institutions?\s*$",
        r"^deposits?\s+from\s+(?:banks?|financial\s+institutions?)\s*$",
        r"^borrowings?\s+from\s+(?:banks?|financial\s+institutions?)\s*$",
        r"^inter[\s-]?bank\s+(?:deposits?|borrowings?|liabilities?)\s*$",
        r"^placements?\s+from\s+banks?\s+and\s+(?:other\s+)?financial\s+institutions?\s*$",
        r"^money\s+market\s+deposits?\s*$",
        r"^due\s+to\s+banks?\s*$",
    ],
    "sukuk_issued_bank": [
        r"^sukuk\s+(?:certificates?\s+)?issued\s*$",
        r"^debt\s+securities?\s+issued\s*$",
        r"^(?:medium[\s-]?term\s+)?notes?\s+(?:programme\s+)?issued\s*$",
        r"^bonds?\s+issued\s*$",
        r"^sukuk\s+financing\s+programs?\s*$",
        r"^tier\s+2\s+sukuk\s*$",
        r"^(?:issued\s+)?sukuk\s+(?:and\s+bonds?)?\s*$",
    ],
    "subordinated_debt_bank": [
        r"^subordinated\s+(?:debt|loans?|bonds?|notes?|liabilities?)\s*$",
        r"^subordinated\s+term\s+(?:finance|loans?)\s*$",
        r"^tier\s+2\s+(?:capital\s+)?(?:instruments?|notes?|bonds?|sukuk)\s*$",
        r"^tier\s+2\s+sukuk\s+(?:certificates?|notes?|capital)?\s*$",
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

# EPS sub-unit detection: Kuwait/Bahrain fils = 1/1000 main; Oman baisa = 1/1000 main.
_FILS_BAISA_RE = re.compile(
    r"\b(?:fils?|baisa|baiza|bahraini\s+fils?)\b", re.IGNORECASE
)
_FILS_BAISA_CURRENCIES = {"KWD", "BHD", "OMR"}

# Lightweight scanner for small fils/baisa values (e.g. "44.0", "43.6", "50").
# _AMOUNT_RE requires 2+ decimal digits or 5+ integer digits and misses these.
_FILS_SCAN_RE = re.compile(
    r"(?<![.\d,])"
    r"(\()?"
    r"(\d+(?:[.,]\d+)?)"
    r"(\))?"
    r"(?![.,\d])",
    re.UNICODE,
)


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
        # Split-line variant: "Independent Auditors' Report" printed as 2 or 3
        # separate lines. Saudi/GCC PDFs commonly use the 3-line form:
        #   "Independent" / "Auditors'" / "Report"
        # Only search from the 30% mark to skip TOC entries.
        _INDEP = re.compile(r"^(?:the\s+)?independent\s*$", re.IGNORECASE)
        _AUD   = re.compile(r"auditor", re.IGNORECASE)
        _RPT   = re.compile(r"\breport\b", re.IGNORECASE)
        _ARPT  = re.compile(r"^auditors?\W*report\s*$", re.IGNORECASE)
        split_start = len(self._lines) * 30 // 100
        for i in range(split_start, len(self._lines)):
            line = self._lines[i][1]
            if _INDEP.match(line):
                found_aud_j = -1
                for j in range(i + 1, min(i + 8, len(self._lines))):
                    wl = self._lines[j][1]
                    if len(wl) > 120:  # long line: not a split heading
                        break
                    if _AUD.search(wl):
                        if _RPT.search(wl):
                            return i  # 2-line: "Independent" / "Auditors' Report"
                        found_aud_j = j
                    elif found_aud_j >= 0 and _RPT.search(wl):
                        return i  # 3-line: "Independent" / "Auditors'" / "Report"
            if _ARPT.match(line):
                for j in range(max(split_start, i - 3), i):
                    if _INDEP.match(self._lines[j][1]):
                        return j

        # Extended fallback: external auditors' report (Qatar/Bahrain formats) and
        # "Financial Statements" section header seen in many GCC PDFs.
        skip = max(0, len(self._lines) // 10)
        _extended_markers = _FS_MARKERS + [
            r"external\s+auditors?\W*report",
            r"report\s+of\s+(?:the\s+)?external\s+auditors?",
            r"^financial\s+statements\s*$",
            r"^(?:the\s+)?financial\s+statements\b",
        ]
        hit = self._find_first(_extended_markers, start=skip)
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

    def _page_range_to_line_range(
        self,
        page_min: int,
        page_max: int,
        start_floor: int = 0,
    ) -> tuple[int, Optional[int]]:
        """Return (start_idx, stop_idx) into self._lines for pages [page_min, page_max].

        start_floor is a minimum index (e.g. self._fs_start) to never start before.
        stop_idx is None when the range covers the rest of the document.
        """
        start_idx: Optional[int] = None
        stop_idx: Optional[int] = None
        for i, (pg, _) in enumerate(self._lines):
            if start_idx is None and pg >= page_min:
                start_idx = max(start_floor, i)
            if stop_idx is None and start_idx is not None and pg > page_max:
                stop_idx = i
                break
        return (start_idx if start_idx is not None else start_floor, stop_idx)

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

    def _ev_from_coords_fils(
        self, page_no: int, patterns: list[str]
    ) -> Optional[ExtractedValue]:
        """Coordinate-based EPS extraction for fils/baisa currencies.

        Identical to _ev_from_coords but scans each same-row span with
        _FILS_SCAN_RE (which matches single-decimal values like "44.0") and
        picks the first span whose value is in the fils/baisa plausible range
        (0.001 < abs(v) < 1000), preferring values with an explicit decimal
        point (skipping bare integers that are likely note references).
        """
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
        row_tolerance = max((ly1 - ly0) * 1.2, 4.0)

        # Collect all numeric spans on the same row, sorted left to right.
        row_candidates: list[tuple[float, str, float, bool]] = []  # x0, raw_text, val, has_dot
        for txt, x0, y0, x1, y1 in spans:
            if abs((y0 + y1) / 2 - label_y_mid) <= row_tolerance and x0 > lx1 - 5:
                for m in _FILS_SCAN_RE.finditer(txt):
                    v = _parse_number(m.group(0))
                    if v is not None and 0.001 < abs(v) < 1000:
                        row_candidates.append((x0, m.group(0), v, "." in m.group(0)))
        if not row_candidates:
            return None

        row_candidates.sort(key=lambda c: c[0])
        # Prefer a candidate with an explicit decimal point.
        for _, raw_num, v, has_dot in row_candidates:
            if has_dot:
                return ExtractedValue(
                    label_as_printed=label_span[0],
                    value=v,
                    page=page_no,
                    context=f"coord-fils: {label_span[0]} | {raw_num}",
                    confidence="medium" if self.result.ocr_heavy else "high",
                    note="coordinate fils extraction",
                )
        # No decimal found: take the second candidate (skip likely note reference).
        _, raw_num, v, _ = row_candidates[min(1, len(row_candidates) - 1)]
        return ExtractedValue(
            label_as_printed=label_span[0],
            value=v,
            page=page_no,
            context=f"coord-fils: {label_span[0]} | {raw_num}",
            confidence="medium" if self.result.ocr_heavy else "high",
            note="coordinate fils extraction (no decimal)",
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
        # Constrain TL and TE to within ±20 pages of TA so that notes-section
        # lines (30-80 pages away) are not picked ahead of the BS page.
        if r.total_assets and r.total_assets.page:
            ta_pg = r.total_assets.page
            bs_start, bs_stop = self._page_range_to_line_range(
                ta_pg - 3, ta_pg + 20, start_floor=fs
            )
            r.total_liabilities = self._extract_ev(
                _PATTERNS["total_liabilities"], min_abs=1_000,
                start=bs_start, stop=bs_stop,
            )
            r.total_equity = self._extract_ev(
                _PATTERNS["total_equity"], min_abs=1_000,
                start=bs_start, stop=bs_stop,
            )
            # Validate: if neither TL nor TE were found in the TA ±20-page window
            # the "Total Assets" hit is likely from a financial summary / highlights
            # table in the Board Report (GCC annual reports often embed a 5-year
            # summary before the actual FS pages). Retry with the next TA occurrence.
            if r.total_liabilities is None and r.total_equity is None:
                ta_retry = self._extract_ev(
                    _PATTERNS["total_assets"], min_abs=1_000, start=bs_start + 1
                )
                if ta_retry and ta_retry.page and ta_retry.page != ta_pg:
                    ta_pg_r = ta_retry.page
                    bs_start_r, bs_stop_r = self._page_range_to_line_range(
                        ta_pg_r - 3, ta_pg_r + 20, start_floor=fs
                    )
                    tl_r = self._extract_ev(
                        _PATTERNS["total_liabilities"], min_abs=1_000,
                        start=bs_start_r, stop=bs_stop_r,
                    )
                    te_r = self._extract_ev(
                        _PATTERNS["total_equity"], min_abs=1_000,
                        start=bs_start_r, stop=bs_stop_r,
                    )
                    if tl_r is not None or te_r is not None:
                        r.total_assets = ta_retry
                        ta_pg = ta_pg_r
                        bs_start, bs_stop = bs_start_r, bs_stop_r
                        r.total_liabilities = tl_r
                        r.total_equity = te_r

            if r.total_liabilities is None:
                r.total_liabilities = self._extract_ev(
                    _PATTERNS["total_liabilities"], min_abs=1_000, start=fs
                )
            if r.total_equity is None:
                r.total_equity = self._extract_ev(
                    _PATTERNS["total_equity"], min_abs=1_000, start=fs
                )
        else:
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
        # Constrain NPA to the income statement section: tight range (same page ±5)
        # first so the IS attribution is preferred over the BS equity section
        # (Jazeera Airways FY2023-2024: "shareholders of the parent" appeared in the
        # equity section within 25 pages and was wrongly picked).
        np_val = r.net_profit.value if r.net_profit else None
        if r.net_profit and r.net_profit.page:
            np_pg = r.net_profit.page
            # Tight pass: IS attribution should be on the same page or within 5 pages.
            npa_start_t, npa_stop_t = self._page_range_to_line_range(
                np_pg - 3, np_pg + 5, start_floor=is_start
            )
            r.net_profit_attributable = self._extract_ev(
                _PATTERNS["net_profit_attributable"], min_abs=100,
                start=npa_start_t, stop=npa_stop_t,
            )
            # Wider fallback (up to +15 pages) using only explicit combined-label patterns
            # (patterns 0-4) to avoid matching the equity section "shareholders of the parent".
            if r.net_profit_attributable is None:
                npa_start_w, npa_stop_w = self._page_range_to_line_range(
                    np_pg - 5, np_pg + 15, start_floor=is_start
                )
                r.net_profit_attributable = self._extract_ev(
                    _PATTERNS["net_profit_attributable"][:5], min_abs=100,
                    start=npa_start_w, stop=npa_stop_w,
                )
            # Broadest fallback from IS start.
            if r.net_profit_attributable is None:
                r.net_profit_attributable = self._extract_ev(
                    _PATTERNS["net_profit_attributable"], min_abs=100, start=is_start
                )
            # Reject any NPA that exceeds NP by more than 5% — this catches cases
            # where the equity section "shareholders of parent" label was matched
            # instead of the IS attribution row.
            npa_val = (
                r.net_profit_attributable.value
                if r.net_profit_attributable else None
            )
            if (np_val is not None and npa_val is not None
                    and abs(npa_val) > abs(np_val) * 1.05):
                r.net_profit_attributable = None  # will fall through to NPA=NP below
        else:
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

    def _find_fils_eps_value(self, line_idx: int) -> Optional[float]:
        """Scan 20 lines from the EPS label for the actual fils/baisa value.

        EPS calculation notes list: large profit → large share count → small EPS.
        We find the first number in the fils/baisa range (0.001, 999) that appears
        AFTER at least one large number (the profit numerator), so profit-like numbers
        are skipped and the actual EPS figure is returned.
        Uses _FILS_SCAN_RE to also catch single-decimal values like "44.0" that
        _AMOUNT_RE misses (requires 2+ decimal digits).
        """
        ctx = self._context_str(line_idx, window=20)
        seen_large = False
        for m in _FILS_SCAN_RE.finditer(ctx):
            v = _parse_number(m.group(0))
            if v is None:
                continue
            if abs(v) >= 1000:
                seen_large = True
            elif 0.001 < abs(v) < 1000 and seen_large:
                return v
        # Fallback: return first small number even without a preceding large one.
        for m in _FILS_SCAN_RE.finditer(ctx):
            v = _parse_number(m.group(0))
            if v is not None and 0.001 < abs(v) < 1000:
                return v
        return None

    @staticmethod
    def _fils_value_from_ctx_str(ctx: str) -> Optional[float]:
        """Pick a plausible fils/baisa EPS from a short context string.

        Annual-report format: "<label> | <note_ref_int> | <eps_fils> | <prior_eps_fils>"
        Note references are typically bare integers (e.g. 30); EPS values often carry a
        decimal point (e.g. 44.0).  Strategy:
          1. Prefer the first number that has an explicit decimal point in the text.
          2. Fall back: if all are integers, skip the first (likely note ref) when there
             are multiple candidates, otherwise return the sole candidate.
        Uses _FILS_SCAN_RE (not _AMOUNT_RE) so single-decimal values like "44.0" are found.
        """
        candidates: list[tuple[float, bool]] = []  # (parsed_value, has_decimal_in_text)
        for m in _FILS_SCAN_RE.finditer(ctx):
            v = _parse_number(m.group(0))
            if v is not None and 0.001 < abs(v) < 1000:
                candidates.append((v, "." in m.group(0)))
        if not candidates:
            return None
        for v, has_dec in candidates:
            if has_dec:
                return v
        # No decimal point found — skip the first candidate (likely note reference)
        # and return the second if available, otherwise return the first.
        return candidates[1][0] if len(candidates) >= 2 else candidates[0][0]

    def _extract_per_share(self) -> None:
        r = self.result
        r.basic_eps = self._extract_ev(
            _PATTERNS["basic_eps"], min_abs=0.0, window=6, start=self._is_start
        )
        # Sanity: |EPS| > 500 suggests a non-EPS number was captured (e.g.
        # a share count appearing in the same context window). Retry picking
        # the second number in the label's context — the actual EPS is often
        # the smaller value on the same row, displaced by a prior-year column.
        if (r.basic_eps and r.basic_eps.value is not None
                and abs(r.basic_eps.value) > 500):
            alt = self._extract_ev(
                _PATTERNS["basic_eps"], min_abs=0.0, window=6,
                start=self._is_start, skip=1, max_tries=4,
            )
            if alt and alt.value is not None and abs(alt.value) <= 500:
                r.basic_eps = alt

        # Fils / baisa conversion: Kuwait fils = 1/1000 KWD; Bahrain fils = 1/1000 BHD;
        # Oman baisa = 1/1000 OMR. GCC reports commonly label EPS as "X fils" but may
        # also bury the sub-unit keyword in the surrounding note text.
        # Also triggers when value=None but label carries a fils/baisa marker — in that
        # case we attempt recovery regardless of the initial extraction result.
        if r.basic_eps and r.currency in _FILS_BAISA_CURRENCIES:
            label = r.basic_eps.label_as_printed or ""
            ctx_short = r.basic_eps.context or ""
            # Build eps_line_idx: prefer the EPS page for accuracy; fall back to
            # _find_first which may land on an unrelated earlier pattern match.
            eps_line_idx = self._is_start
            if r.basic_eps.page:
                pg_s, pg_e = self._page_range_to_line_range(
                    r.basic_eps.page, r.basic_eps.page, start_floor=self._is_start
                )
                hit_pg = self._find_first(_PATTERNS["basic_eps"], start=pg_s, stop=pg_e)
                if hit_pg:
                    eps_line_idx = hit_pg[0]
                else:
                    hit = self._find_first(_PATTERNS["basic_eps"], start=self._is_start)
                    if hit:
                        eps_line_idx = hit[0]
            else:
                hit = self._find_first(_PATTERNS["basic_eps"], start=self._is_start)
                if hit:
                    eps_line_idx = hit[0]
            ctx_wide = self._context_str(eps_line_idx, window=20)
            is_fils = bool(
                _FILS_BAISA_RE.search(label)
                or _FILS_BAISA_RE.search(ctx_short)
                or _FILS_BAISA_RE.search(ctx_wide)
            )
            if is_fils:
                val = r.basic_eps.value
                if val is None or abs(val) > 999:
                    # Value missing or too large — likely captured the profit numerator.
                    # Try 1: scan ctx_short directly (it's the 6-line window captured by
                    #         _extract_ev, so it's closest to the actual EPS label line).
                    recovered = self._fils_value_from_ctx_str(ctx_short)
                    # Try 2: coordinate extraction with fils-aware scanner on the EPS page.
                    if recovered is None and r.basic_eps.page:
                        ev_fils = self._ev_from_coords_fils(
                            r.basic_eps.page, _PATTERNS["basic_eps"]
                        )
                        if ev_fils and ev_fils.value is not None:
                            recovered = ev_fils.value
                    # Try 3: wider 20-line window pinned to the correct EPS page.
                    if recovered is None:
                        recovered = self._find_fils_eps_value(eps_line_idx)
                    if recovered is not None:
                        orig_note = f"orig={val:.0f}" if val is not None else "orig=None"
                        r.basic_eps = ExtractedValue(
                            label_as_printed=label,
                            value=round(recovered / 1000, 6),
                            page=r.basic_eps.page,
                            context=ctx_wide[:200],
                            confidence="medium",
                            note=(
                                f"fils/baisa→{r.currency}: recovered "
                                f"({orig_note}, fils={recovered:.3f})"
                            ),
                        )
                        r.eps_in_fils_baisa = True
                    else:
                        orig_note = f"{val:.0f}" if val is not None else "None"
                        r.basic_eps = ExtractedValue(
                            label_as_printed=label,
                            value=None,
                            page=r.basic_eps.page,
                            context=ctx_wide[:200],
                            confidence="low",
                            note=(
                                f"fils/baisa: value {orig_note}; "
                                f"no valid fils found in context"
                            ),
                        )
                elif 0 < abs(val) <= 999:
                    # Value is already a plausible fils/baisa number; convert to main unit.
                    r.basic_eps = ExtractedValue(
                        label_as_printed=label,
                        value=round(val / 1000, 6),
                        page=r.basic_eps.page,
                        context=ctx_short,
                        confidence=r.basic_eps.confidence,
                        note=f"fils/baisa→{r.currency}: ÷1000 (was {val:.3f})",
                    )
                    r.eps_in_fils_baisa = True

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

    def _extract_debt_components(self) -> None:
        """Extract individual debt components from the balance sheet.

        Non-banks: short-term borrowings, long-term borrowings, sukuk/bonds/notes,
        lease liabilities.
        Banks: due to banks/FIs, sukuk issued, subordinated debt.
        Customer deposits are NOT debt; they are excluded.

        Sets total_debt (sum of found components) and total_debt_status.
        Searches within TA page ±20 to stay in the balance sheet section.
        If no components found in the ±20 window, falls back to a wider ±40-page
        search (handles banks whose Board-Report summary is before the actual FS).
        """
        r = self.result
        fs = self._fs_start
        ta_pg = r.total_assets.page if r.total_assets and r.total_assets.page else None

        if ta_pg:
            bs_start, bs_stop = self._page_range_to_line_range(
                ta_pg - 3, ta_pg + 20, start_floor=fs
            )
        else:
            bs_start, bs_stop = fs, None

        def _search_components(start: int, stop: Optional[int]) -> tuple[list[float], bool]:
            comps: list[float] = []
            found = False
            if r.is_bank:
                r.due_to_banks_fi = self._extract_ev(
                    _PATTERNS["due_to_banks_fi"], min_abs=0, start=start, stop=stop
                )
                r.sukuk_issued_bank = self._extract_ev(
                    _PATTERNS["sukuk_issued_bank"], min_abs=0, start=start, stop=stop
                )
                r.subordinated_debt_bank = self._extract_ev(
                    _PATTERNS["subordinated_debt_bank"], min_abs=0, start=start, stop=stop
                )
                for ev in (r.due_to_banks_fi, r.sukuk_issued_bank, r.subordinated_debt_bank):
                    if ev is not None:
                        found = True
                        if ev.value is not None and ev.value > 0:
                            comps.append(ev.value)
            else:
                r.st_borrowings = self._extract_ev(
                    _PATTERNS["st_borrowings"], min_abs=0, start=start, stop=stop
                )
                r.lt_borrowings = self._extract_ev(
                    _PATTERNS["lt_borrowings"], min_abs=0, start=start, stop=stop
                )
                r.sukuk_bonds_notes = self._extract_ev(
                    _PATTERNS["sukuk_bonds_notes"], min_abs=0, start=start, stop=stop
                )
                r.lease_liabilities_nb = self._extract_ev(
                    _PATTERNS["lease_liabilities_nb"], min_abs=0, start=start, stop=stop
                )
                for ev in (r.st_borrowings, r.lt_borrowings,
                           r.sukuk_bonds_notes, r.lease_liabilities_nb):
                    if ev is not None:
                        found = True
                        if ev.value is not None and ev.value > 0:
                            comps.append(ev.value)
            return comps, found

        components, found_any = _search_components(bs_start, bs_stop)

        # Wider fallback (±40 pages) for documents where the FS summary table
        # precedes the actual consolidated statement of financial position.
        if not components and not found_any and ta_pg:
            bs_start_w, bs_stop_w = self._page_range_to_line_range(
                ta_pg - 5, ta_pg + 40, start_floor=fs
            )
            if bs_stop_w != bs_stop:
                components, found_any = _search_components(bs_start_w, bs_stop_w)

        # Also consider total_borrowings already extracted in _extract_supplementary.
        # If no components found but total_borrowings is, use it as the total directly.
        tb = r.total_borrowings.value if r.total_borrowings and r.total_borrowings.value else None

        if components:
            r.total_debt = round(sum(components), 0)
            r.total_debt_status = "extracted"
        elif tb is not None and tb > 0:
            r.total_debt = tb
            r.total_debt_status = "extracted"
        elif found_any:
            # Patterns matched but all values were zero → explicitly zero borrowings.
            r.total_debt = 0.0
            r.total_debt_status = "zero"
        elif tb == 0.0:
            r.total_debt = 0.0
            r.total_debt_status = "zero"
        else:
            # If TA, TL and TE are all extracted and the balance sheet balances
            # (within 2%), the balance sheet search was valid — no debt line items
            # means the company genuinely has no financial borrowings.
            ta_v = r.total_assets.value if r.total_assets else None
            tl_v = r.total_liabilities.value if r.total_liabilities else None
            te_v = r.total_equity.value if r.total_equity else None
            if (ta_v and tl_v is not None and te_v is not None
                    and ta_v > 0
                    and abs(tl_v + te_v - ta_v) / ta_v <= 0.02):
                r.total_debt = 0.0
                r.total_debt_status = "zero"
            else:
                r.total_debt = None
                r.total_debt_status = "not_found"

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

        # Leverage: flag when equity attributable is zero or negative.
        ea_lev = v(r.equity_attributable) or v(r.total_equity)
        if ea_lev is not None and ea_lev <= 0 and r.total_debt is not None:
            flags.append(
                f"LEVERAGE_NEGATIVE_EQUITY: EA={ea_lev:,.0f}  leverage undefined"
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

        ta      = v(r.total_assets)
        tl      = v(r.total_liabilities)
        te      = v(r.total_equity)
        ea      = v(r.equity_attributable)
        rev     = v(r.revenue)
        np_     = v(r.net_profit)
        npa     = v(r.net_profit_attributable)
        at1     = v(r.at1_equity) or 0.0
        eps_num = v(r.eps_numerator)
        gib     = v(r.gross_income_bank)  # gross income before funding costs (banks)

        # Leverage (primary): total_debt / equity_attributable.
        # leverage_alt: total_liabilities / total_assets (old formula, kept as secondary).
        ea_lev = ea if ea is not None else te
        if r.total_debt is not None and ea_lev is not None and ea_lev > 0:
            r.leverage = round(r.total_debt / ea_lev, 4)
        elif r.total_debt == 0.0:
            r.leverage = 0.0
        if tl is not None and ta and ta != 0:
            r.leverage_alt = round(tl / ta, 4)

        # RoA: NP / TA × 100 (%).
        if np_ is not None and ta and ta != 0:
            r.roa = round(np_ / ta * 100, 4)

        # Net margin (× 100):
        # Non-banks: NP / revenue.
        # Banks: NP / gross_income_bank (financing+fees+other, before funding costs).
        #        net_margin_alt = NP / total_operating_income (old bank formula).
        if r.is_bank:
            if np_ is not None and gib and gib != 0:
                r.net_profit_margin = round(np_ / gib * 100, 4)
            if np_ is not None and rev and rev != 0:
                r.net_margin_alt = round(np_ / rev * 100, 4)
        else:
            if np_ is not None and rev and rev != 0:
                r.net_profit_margin = round(np_ / rev * 100, 4)
            r.net_margin_alt = r.net_profit_margin

        # RoE (× 100): primary uses eps_numerator / (equity_attributable - AT1).
        # Fallback uses npa / equity_attributable when eps_numerator not found.
        eq_base = ea if ea is not None else te
        if eq_base:
            eq_ord = eq_base - at1
            r.equity_ordinary = round(eq_ord, 0) if eq_ord > 0 else None
        else:
            eq_ord = None
            r.equity_ordinary = None

        if eps_num is not None and eq_ord and eq_ord > 0:
            r.roe = round(eps_num / eq_ord * 100, 4)
            r.roe_eps_based = True
        elif npa is not None and eq_ord and eq_ord > 0:
            r.roe = round(npa / eq_ord * 100, 4)
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
        self._extract_debt_components()
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
        return f"  {label:<28}  n/a"
    if pct:
        return f"  {label:<28}  {val:>8.2f}%"
    return f"  {label:<28}  {val:>10.4f}"


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
    fils_note = "  [fils/baisa converted]" if row.eps_in_fils_baisa else ""
    print(_fmt_ev("Basic EPS (main currency)", row.basic_eps) + fils_note)
    print(_fmt_ev("Shares issued (cap note)", row.shares_outstanding))
    print(_fmt_ev("Shares wtd-avg (EPS note)", row.shares_eps_note))
    print()

    print("  -- Debt components " + "-" * 60)
    print(f"  {'Total debt':<30}  {row.total_debt:>20,.0f}  [{row.total_debt_status}]"
          if row.total_debt is not None else
          f"  {'Total debt':<30}  {'not extracted':>20}  [{row.total_debt_status}]")
    if row.is_bank:
        print(_fmt_ev("Due to banks & FIs", row.due_to_banks_fi))
        print(_fmt_ev("Sukuk issued (bank)", row.sukuk_issued_bank))
        print(_fmt_ev("Subordinated debt", row.subordinated_debt_bank))
    else:
        print(_fmt_ev("Short-term borrowings", row.st_borrowings))
        print(_fmt_ev("Long-term borrowings", row.lt_borrowings))
        print(_fmt_ev("Sukuk / bonds / notes", row.sukuk_bonds_notes))
        print(_fmt_ev("Lease liabilities", row.lease_liabilities_nb))
    print(_fmt_ev("Total borrowings (check)", row.total_borrowings))
    print(_fmt_ev("AT1 / Tier-1 sukuk (equity)", row.at1_equity))
    print()

    print("  -- Market data & history " + "-" * 54)
    print(_fmt_ev("Share price year-end", row.share_price_year_end))
    print(_fmt_ev("Market cap", row.market_cap))
    print(_fmt_ev("Year of incorporation", row.year_of_incorporation))
    print(_fmt_ev("Year of listing", row.year_of_listing))
    print()

    roe_method = "(eps_num/eq_ord)" if row.roe_eps_based else "(NPA/eq_ord)"
    eq_ord_str = f"{row.equity_ordinary:,.0f}" if row.equity_ordinary else "n/a"
    print("  -- Ratios " + "-" * 69)
    print(_fmt_ratio("Leverage (debt/EA)", row.leverage))
    print(_fmt_ratio("Leverage alt (TL/TA)", row.leverage_alt))
    print(_fmt_ratio("RoA (NP/TA %)", row.roa, pct=True))
    print(f"  {'RoE % '+roe_method:<28}  "
          + (f"{row.roe:>8.2f}%" if row.roe is not None else "     n/a"))
    print(f"  {'Equity ordinary':<28}  {eq_ord_str:>12}")
    print(_fmt_ratio("Net margin % (primary)", row.net_profit_margin, pct=True))
    print(_fmt_ratio("Net margin alt %", row.net_margin_alt, pct=True))
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
        "eps_in_fils_baisa": row.eps_in_fils_baisa,
        # Debt summary
        "total_debt": row.total_debt,
        "total_debt_status": row.total_debt_status,
        # Ratios (RoA/RoE/margins are in %, leverage is ratio)
        "leverage": row.leverage,           # total_debt / equity_attributable
        "leverage_alt": row.leverage_alt,   # total_liabilities / total_assets
        "roa": row.roa,                     # NP/TA × 100
        "roe": row.roe,                     # NPA/eq_ord × 100
        "roe_eps_based": row.roe_eps_based,
        "equity_ordinary": row.equity_ordinary,
        "net_profit_margin": row.net_profit_margin,  # primary (see is_bank)
        "net_margin_alt": row.net_margin_alt,        # NP/total_oper_income×100 banks
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
        ("shares_outstanding",       row.shares_outstanding),
        ("shares_eps_note",          row.shares_eps_note),
        ("total_borrowings",         row.total_borrowings),
        # Debt components (non-banks)
        ("st_borrowings",            row.st_borrowings),
        ("lt_borrowings",            row.lt_borrowings),
        ("sukuk_bonds_notes",        row.sukuk_bonds_notes),
        ("lease_liabilities_nb",     row.lease_liabilities_nb),
        # Debt components (banks)
        ("due_to_banks_fi",          row.due_to_banks_fi),
        ("sukuk_issued_bank",        row.sukuk_issued_bank),
        ("subordinated_debt_bank",   row.subordinated_debt_bank),
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
        "fiscal_year", "currency_page", "leverage", "leverage_alt", "roa", "roe",
        "equity_ordinary", "net_profit_margin", "net_margin_alt", "firm_age", "listing_age",
        "total_debt",
        "total_assets_value", "total_liabilities_value", "total_equity_value",
        "equity_attributable_value", "revenue_value", "gross_income_bank_value",
        "net_profit_value", "net_profit_attributable_value", "eps_numerator_value",
        "basic_eps_value", "shares_outstanding_value", "shares_eps_note_value",
        "total_borrowings_value",
        "st_borrowings_value", "lt_borrowings_value", "sukuk_bonds_notes_value",
        "lease_liabilities_nb_value",
        "due_to_banks_fi_value", "sukuk_issued_bank_value", "subordinated_debt_bank_value",
        "at1_equity_value", "share_price_year_end_value",
        "market_cap_value", "year_of_incorporation_value", "year_of_listing_value",
        "total_assets_page", "total_liabilities_page", "total_equity_page",
        "equity_attributable_page", "revenue_page", "gross_income_bank_page",
        "net_profit_page", "net_profit_attributable_page", "eps_numerator_page",
        "basic_eps_page", "shares_outstanding_page", "shares_eps_note_page",
        "total_borrowings_page",
        "st_borrowings_page", "lt_borrowings_page", "sukuk_bonds_notes_page",
        "lease_liabilities_nb_page",
        "due_to_banks_fi_page", "sukuk_issued_bank_page", "subordinated_debt_bank_page",
        "at1_equity_page", "share_price_year_end_page",
        "market_cap_page", "year_of_incorporation_page", "year_of_listing_page",
    }
    _BOOL_COLS = {
        "is_bank", "total_liabilities_computed", "ocr_heavy", "roe_eps_based",
        "eps_in_fils_baisa",
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


# ---- no-FS company-year listing ---------------------------------------------


def list_no_fs(csv_path: Path) -> None:
    """Print and return all company-years with FS_BOUNDARY_NOT_FOUND, with page count."""
    import csv as _csv
    from sqlalchemy import select

    db = SessionLocal()
    try:
        rows_db = db.execute(
            select(
                Institution.slug,
                Institution.name,
                SourceDocument.fiscal_year,
                SourceDocument.page_count,
            )
            .join(SourceDocument, SourceDocument.institution_id == Institution.id)
            .where(Institution.active.is_(True))
            .where(SourceDocument.superseded_by_id.is_(None))
        ).all()
    finally:
        db.close()

    page_map = {(slug, fy): (name, pg) for slug, name, fy, pg in rows_db}

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = _csv.DictReader(fh)
        no_fs = [
            r for r in reader
            if "FS_BOUNDARY_NOT_FOUND" in (r.get("flags") or "")
        ]

    print(f"\n{'Company':<55} {'FY':<6} {'Pages'}")
    print("-" * 70)
    for r in sorted(no_fs, key=lambda x: (x["slug"], x["fiscal_year"])):
        slug, fy = r["slug"], int(r["fiscal_year"])
        name, pages = page_map.get((slug, fy), ("?", None))
        pages_str = str(pages) if pages else "?"
        print(f"  {name:<53} {fy:<6} {pages_str}")
    print(f"\nTotal: {len(no_fs)} company-years with no financial statements in the PDF.\n")


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
    ap.add_argument("--no-fs", action="store_true",
                    help="List company-years with no FS in PDF (from existing CSV)")
    ap.add_argument("--slug")
    ap.add_argument("--fy", type=int)
    args = ap.parse_args()

    if args.write_xlsx:
        csv_path  = REPO_ROOT / "docs" / "exports" / "financials_extracted.csv"
        xlsx_path = REPO_ROOT / "docs" / "exports" / "financials_extracted.xlsx"
        write_xlsx_from_csv(csv_path, xlsx_path)
        return 0

    if args.no_fs:
        csv_path = REPO_ROOT / "docs" / "exports" / "financials_extracted.csv"
        list_no_fs(csv_path)
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
