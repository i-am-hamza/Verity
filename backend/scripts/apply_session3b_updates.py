"""Apply Session 3b Playwright findings to data/ir_sources.json.

This script is idempotent: each slug's record is updated in-place to the
new state. Running it twice produces the same output. No merging; the
override field set here is authoritative.

Also writes data/alafco_gaps.json: one row per target year for ALAFCO,
feeding Session 4's Wayback helper.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IR_SOURCES = REPO / "data" / "ir_sources.json"
ALAFCO_GAPS_FILE = REPO / "data" / "alafco_gaps.json"
TODAY = "2026-10-01"


# ---------------------------------------------------------------------------
# EXCHANGE updates (per slug)
# ---------------------------------------------------------------------------
# Tadawul (24 slugs): both financial + other wave KSA listings. All 403'd by
# Akamai even via Playwright + VerityResearchBot UA. Downgrade from
# needs_human (Session 3) to unreachable (Session 3b evidence).
TADAWUL_SLUGS = {
    # Financial
    "al-rajhi-bank", "the-saudi-national-bank", "riyad-bank", "alinma-bank",
    "bank-albilad", "bupa-arabia-for-cooperative-insurance-company",
    "saudi-industrial-investment-group",
    # Other
    "saudi-aramco", "sabic", "saudi-telecom-company", "maaden", "saudi-electricity",
    "yanbu-cement-company", "saudi-arabian-fertilizer-company", "almarai",
    "etihad-etisalat-mobily", "savola-group", "yanbu-national-petrochemical",
    "dar-al-arkan-real-estate-development-company", "emaar-the-economic-city",
    "advanced-petrochemical", "saudi-kayan-petrochemical-company",
    "mouwasat-medical-services-company", "saudi-airlines-catering-company-catrion",
    "national-industrialization-co", "rabigh-refining-petrochemical-co",
    "sahara-international-petrochemical-co", "mobile-telecommunications-co-saudi-arabia-zain",
    "jarir-marketing-co", "saudi-cement", "abdullah-al-othaim-markets",
}

TADAWUL_NOTE = (
    "Tadawul (saudiexchange.sa) returned HTTP 403 to Playwright with Chromium + the "
    "VerityResearchBot UA — Akamai bot detection, UA-based. CLAUDE.md rule 3 "
    "says 'if a site blocks you, stop for that domain, log it, move on' — "
    "Session 4 will not auto-crawl Tadawul. KSA exchange evidence must come from "
    "company IR pages or Tier 3/4 paths."
)

# Boursa Kuwait numeric-id profile URLs — 403 to Playwright too.
BK_SLUGS = {
    "kuwait-finance-house": "108",
    "national-bank-of-kuwait": "101",
    "boubyan-bank": "109",
    "zain-mobile-telecommunications-company": "605",
    "kuwait-telecommunications-company": "822",
    "tamdeen-real-estate-company": "406",
}

BK_NOTE = (
    "Boursa Kuwait /stock/<id>/profile returned HTTP 403 to Playwright + "
    "VerityResearchBot UA. The numeric ID is confirmed from search-surfaced "
    "docs.boursakuwait.com.kw NewsPDF URLs but the profile page itself is "
    "blocked to automated access. Session 4 to retry via Tier 3/4 or human browsing."
)

# Verified exchange URLs — status 200 via Playwright, final_url preserved.
VERIFIED_EXCHANGE: dict[str, str] = {
    # ADX
    "first-abu-dhabi-bank": "https://www.adx.ae/en/main-market/company-profile/overview?symbols=FAB&secCode=FAB",
    "abu-dhabi-commercial-bank": "https://www.adx.ae/en/main-market/company-profile/overview?symbols=ADCB&secCode=ADCB",
    "the-national-bank-of-ras-al-khaimah": "https://www.adx.ae/en/main-market/company-profile/overview?symbols=RAKBANK&secCode=RAKBANK",
    "abu-dhabi-national-oil-company-for-distribution": "https://www.adx.ae/en/main-market/company-profile/overview?symbols=ADNOCDIST&secCode=ADNOCDIST",
    "emirates-telecom-etisalat-group": "https://www.adx.ae/en/main-market/company-profile/overview?symbols=EAND&secCode=EAND",
    "abu-dhabi-national-energy-company": "https://www.adx.ae/en/main-market/company-profile/overview?symbols=TAQA&secCode=TAQA",
    "aldar-properties-pjsc": "https://www.adx.ae/en/main-market/company-profile/overview?symbols=ALDAR&secCode=ALDAR",
    # DFM (previously-verified kept + new)
    "dubai-islamic-bank": "https://www.dfm.ae/the-exchange/market-information/company/DIB/profile",
    "emirates-nbd-pjsc": "https://www.dfm.ae/the-exchange/market-information/company/EMIRATESNBD/profile",
    "dubai-investment": "https://www.dfm.ae/the-exchange/market-information/company/DIC/profile",
    "emaar-properties": "https://www.dfm.ae/the-exchange/market-information/company/EMAAR/profile",
    "air-arabia-pjsc": "https://www.dfm.ae/the-exchange/market-information/company/AIRARABIA/profile",
    # QSE
    "qnb-qatar-national-bank": "https://www.qe.com.qa/company-profile?InformationCategory=Company&InformationType=News&CompanyCode=QNBK",
    "industries-qatar": "https://www.qe.com.qa/company-profile?InformationCategory=Company&InformationType=News&CompanyCode=IQCD",
    "ooredoo-q-p-s-c": "https://www.qe.com.qa/company-profile?InformationCategory=Company&InformationType=News&CompanyCode=ORDS",
    "qatar-fuel-company-woqod": "https://www.qe.com.qa/company-profile?InformationCategory=Company&InformationType=News&CompanyCode=QFLS",
    "baladna": "https://www.qe.com.qa/company-profile?InformationCategory=Company&InformationType=News&CompanyCode=BLDN",
    "gulf-international-services": "https://www.qe.com.qa/company-profile?InformationCategory=Company&InformationType=News&CompanyCode=GISS",
    "qatar-gas-transport-co-nakilat": "https://www.qe.com.qa/company-profile?InformationCategory=Company&InformationType=News&CompanyCode=QGTS",
    # MSX
    "bank-muscat-bkmb": "https://www.msx.om/snapshot.aspx?s=BKMB",
    "oman-international-development-and-investment-company": "https://www.msx.om/snapshot.aspx?s=OMVS",
    "sohar-international-bank": "https://www.msx.om/snapshot.aspx?s=BKSB",
    "bank-dhofar": "https://www.msx.om/snapshot.aspx?s=BKDB",
    "oman-telecommunications-company-otel": "https://www.msx.om/snapshot.aspx?s=OTEL",
    # Bahrain Bourse
    "national-bank-of-bahrain": "https://bahrainbourse.com/en/companyprofile?CompanyNameSymbol=NBB",
    "bahrain-telecommunications-beyon": "https://bahrainbourse.com/en/companyprofile?CompanyNameSymbol=BEYON",
    "aluminium-bahrain-alba": "https://bahrainbourse.com/en/companyprofile?CompanyNameSymbol=ALBH",
}

VERIFIED_EXCHANGE_NOTE = (
    "Verified via Playwright (Chromium) with the VerityResearchBot UA from "
    "CLAUDE.md on 2026-10-01: HTTP 200 and final URL preserved (no redirect to "
    "homepage). Company-specific data on these pages is loaded via XHR by the "
    "SPA, so the shared ticker-scroll dominates a plain inner-text grab — the "
    "URL being honoured by the server is what proves the per-company page exists."
)


# ---------------------------------------------------------------------------
# IR updates (Session 3b Playwright pass on the deferred rows + SNB)
# ---------------------------------------------------------------------------
IR_UPGRADES_VERIFIED: list[dict] = [
    # Each: slug, (optional) new ir_url if changed, title seen, notes
    {"slug": "the-saudi-national-bank", "status": 200, "title": "Investor Relations | Saudi National Bank"},
    {"slug": "maaden", "status": 200, "title": "Saudi Arabian Mining Company (Maaden) - Leading Mining & Metals Company"},
    {"slug": "sahara-international-petrochemical-co", "status": 200, "title": "Sipchem home (Arabic-primary)", "arabic_primary": True},
    {"slug": "mobile-telecommunications-co-saudi-arabia-zain", "status": 200, "title": "(interactive microsite shell; empty title)", "js_required": True},
    {"slug": "saudi-cement", "status": 200, "title": "Annual Reports | Saudi Cement"},
    {"slug": "abdullah-al-othaim-markets", "status": 200, "title": "Investor Relations | (othaim-markets.eurolandir.com)"},
    {"slug": "emirates-telecom-etisalat-group",
     "new_ir_url": "https://www.eand.com/en/investors/annual-reports.html",
     "status": 200, "title": "e& (etisalat and ) | Global technology group | Annual..."},
    {"slug": "abu-dhabi-national-energy-company", "status": 200, "title": "(empty title; JS-heavy)", "js_required": True},
    {"slug": "emaar-properties", "status": 200, "title": "Real Estate Investor Relations"},
    {"slug": "air-arabia-pjsc",
     "new_ir_url": "https://www.airarabia.com/en/about-us/investor-relations",
     "status": 200, "title": "Investor Relations"},
    {"slug": "industries-qatar", "status": 200, "title": "Investor Relations | Industries Qatar Q.P.S.C"},
    {"slug": "ooredoo-q-p-s-c", "status": 200, "title": "Annual reports | Ooredoo corporate"},
    {"slug": "qatar-fuel-company-woqod", "status": 200, "title": "Investor Relations"},
    {"slug": "baladna", "status": 200, "title": "Annual Reports | Baladna Financial Performance..."},
    {"slug": "gulf-international-services", "status": 200, "title": "Financial Statements | GIS"},
    {"slug": "qatar-gas-transport-co-nakilat", "status": 200, "title": "Home - Nakilat"},
    {"slug": "zain-mobile-telecommunications-company", "status": 200, "title": "Investor Relations"},
    {"slug": "bahrain-telecommunications-beyon", "status": 200, "title": "Annual Reports - Beyon"},
    {"slug": "aluminium-bahrain-alba", "status": 200, "title": "Annual Report - Aluminium Bahrain (Alba)"},
]

# These rows had a candidate URL but the fetch failed → mark unreachable
# (promotes from needs_human to a definitive block state).
IR_DOWNGRADES_UNREACHABLE: list[dict] = [
    {"slug": "saudi-arabian-fertilizer-company", "status": 500, "note": "WAF 'URL blocked' response"},
    {"slug": "rabigh-refining-petrochemical-co", "status": 403, "note": "Server 403 to Playwright + honest UA"},
    {"slug": "abu-dhabi-national-oil-company-for-distribution", "status": 403, "note": "Access Denied"},
    {"slug": "aldar-properties-pjsc", "status": 403, "note": "Access Denied"},
    {"slug": "kuwait-telecommunications-company", "status": 403, "note": "Access Denied"},
    {"slug": "oman-telecommunications-company-otel", "status": 200, "note": "The /Investors/investors-annual-report URL redirects to the homepage — the specific annual-reports path returned by Session 3 search does not exist. Needs a different IR URL."},
]


# ---------------------------------------------------------------------------
# ALAFCO: special case, both unreachable + gap rows
# ---------------------------------------------------------------------------
ALAFCO_NOTES = (
    "Delisted from Boursa Kuwait 2025-03-05. alafco.com returned Cloudflare 523 in "
    "Session 3 and remains unreachable. Boursa Kuwait /stock/<id>/profile would also "
    "return 403. Wayback Machine has 36 snapshots of alafco.com/en/investors between "
    "2021-03-05 and 2025-05-23 (confirmed via web.archive.org/web/2*/alafco.com/en/investors). "
    "Fiscal years for which annual reports were published: FY2020 through FY2024 "
    "(fiscal year ends September 30; delisted before FY2025 close so FY2025 report "
    "was not expected / not published). Target years 2021-2024 (per config/verity.toml) "
    "should go to Tier 3 Wayback; 2025 is confirmed data non-existence."
)

ALAFCO_GAP_ROWS = [
    {"institution_slug": "alafco-aviation-lease-and-finance-company", "fiscal_year": 2021,
     "reason": "unreachable", "tier_tried": "live",
     "next_action": "Tier 3 Wayback Machine (36 captures of alafco.com/en/investors available)"},
    {"institution_slug": "alafco-aviation-lease-and-finance-company", "fiscal_year": 2022,
     "reason": "unreachable", "tier_tried": "live",
     "next_action": "Tier 3 Wayback Machine"},
    {"institution_slug": "alafco-aviation-lease-and-finance-company", "fiscal_year": 2023,
     "reason": "unreachable", "tier_tried": "live",
     "next_action": "Tier 3 Wayback Machine"},
    {"institution_slug": "alafco-aviation-lease-and-finance-company", "fiscal_year": 2024,
     "reason": "unreachable", "tier_tried": "live",
     "next_action": "Tier 3 Wayback Machine (last published year pre-delisting)"},
    {"institution_slug": "alafco-aviation-lease-and-finance-company", "fiscal_year": 2025,
     "reason": "not_found", "tier_tried": "live",
     "next_action": "Confirmed non-existent: delisted 2025-03-05, before FY2025 (ending Sep 2025) closed"},
]


# ---------------------------------------------------------------------------
# Apply updates
# ---------------------------------------------------------------------------
def main() -> None:
    rows = json.loads(IR_SOURCES.read_text(encoding="utf-8"))
    by_slug = {r["slug"]: r for r in rows}

    # 1. Tadawul: mark all 24 as exchange unreachable with the new note.
    for slug in TADAWUL_SLUGS:
        r = by_slug[slug]
        r["exchange_status"] = "unreachable"
        r["evidence"]["exchange"] = {
            "fetched_at": TODAY,
            "note": TADAWUL_NOTE,
        }

    # 2. Boursa Kuwait numeric-id slugs: 403 even via Playwright.
    for slug, bk_id in BK_SLUGS.items():
        r = by_slug[slug]
        r["exchange_company_url"] = f"https://www.boursakuwait.com.kw/stock/{bk_id}/profile"
        r["exchange_status"] = "unreachable"
        r["evidence"]["exchange"] = {
            "fetched_at": TODAY,
            "note": BK_NOTE + f" (numeric id = {bk_id})",
        }

    # 3. Verified exchange URLs (ADX / DFM / QSE / MSX / Bahrain Bourse).
    for slug, url in VERIFIED_EXCHANGE.items():
        r = by_slug[slug]
        r["exchange_company_url"] = url
        r["exchange_status"] = "verified"
        r["evidence"]["exchange"] = {
            "fetched_at": TODAY,
            "note": VERIFIED_EXCHANGE_NOTE,
        }

    # 4. IR upgrades to verified.
    for entry in IR_UPGRADES_VERIFIED:
        r = by_slug[entry["slug"]]
        if "new_ir_url" in entry:
            r["ir_url"] = entry["new_ir_url"]
        r["ir_status"] = "verified"
        prior_pdfs = r["evidence"]["ir"].get("sample_report_links", [])
        r["evidence"]["ir"] = {
            "fetched_at": TODAY,
            "sample_report_links": prior_pdfs,
            "note": (f"Playwright verified: HTTP {entry['status']}, title: {entry['title']}. "
                     + (" Arabic-primary site; English version via language toggle." if entry.get("arabic_primary") else "")
                     + (" JS required to populate the full report list." if entry.get("js_required") else "")),
        }

    # 5. IR downgrades to unreachable.
    for entry in IR_DOWNGRADES_UNREACHABLE:
        r = by_slug[entry["slug"]]
        r["ir_status"] = "unreachable"
        prior_pdfs = r["evidence"]["ir"].get("sample_report_links", [])
        r["evidence"]["ir"] = {
            "fetched_at": TODAY,
            "sample_report_links": prior_pdfs,
            "note": f"Playwright: HTTP {entry['status']}. {entry['note']}",
        }

    # 6. ALAFCO special case: both unreachable, add Wayback evidence.
    alafco = by_slug["alafco-aviation-lease-and-finance-company"]
    alafco["ir_status"] = "unreachable"
    alafco["exchange_status"] = "unreachable"
    alafco["evidence"]["ir"] = {
        "fetched_at": TODAY,
        "sample_report_links": [
            "https://web.archive.org/web/2*/alafco.com/en/investors",
        ],
        "note": "Delisted — see notes.",
    }
    alafco["evidence"]["exchange"] = {
        "fetched_at": TODAY,
        "note": "Delisted from Boursa Kuwait 2025-03-05; profile page would also return 403.",
    }
    alafco["notes"] = ALAFCO_NOTES

    # 7. Write everything.
    IR_SOURCES.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ALAFCO_GAPS_FILE.write_text(json.dumps(ALAFCO_GAP_ROWS, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"wrote {len(rows)} rows -> {IR_SOURCES}")
    print(f"wrote {len(ALAFCO_GAP_ROWS)} alafco gap rows -> {ALAFCO_GAPS_FILE}")


if __name__ == "__main__":
    main()
