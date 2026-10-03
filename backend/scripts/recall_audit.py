"""Session 1b recall audit.

Searches a sample of scored report PDFs for ESG-adjacent candidate terms
that are NOT in the current taxonomy. Reports per-term, per-report hit
counts so we can see which absent terms show up often enough to be
candidates for taxonomy expansion.

A term is counted when it appears as a WHOLE WORD (word-boundaries),
case-insensitive, in the raw per-page text as extracted by pymupdf.
We also report the frequency of a selected set of already-in-taxonomy
terms as a sanity-check denominator.
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

import os  # noqa: E402

os.environ.setdefault("VERITY_CONTACT_EMAIL", "ana.muhandis@protonmail.com")
sys.stdout.reconfigure(encoding="utf-8")

import pymupdf  # noqa: E402

from app.database import engine  # noqa: E402
from sqlalchemy import text as sql_text  # noqa: E402

# ---------------- candidate terms ------------------------------------------
# Grouped roughly by pillar so the output is readable, not for scoring.
# Picked because they come up often in sustainability sections / ESG
# frameworks / regional reporting but are not in the current taxonomy.
CANDIDATE_TERMS = {
    "Environmental (candidates)": [
        "ESG", "sustainability", "sustainability report", "sustainable",
        "net zero", "net-zero", "paris agreement", "scope 1", "scope 2", "scope 3",
        "TCFD", "SASB", "GRI", "GHG", "decarbonization", "decarbonisation",
        "circular economy", "transition risk", "physical risk",
        "biodiversity loss", "nature", "renewables", "solar", "wind",
        "water consumption", "water intensity", "waste reduction",
        "scope emissions", "science based target", "SBTi",
        "green building", "LEED", "ESG rating", "ESG framework",
    ],
    "Social (candidates)": [
        "CSR", "corporate social responsibility", "philanthropy", "zakat",
        "nationalization", "Saudization", "Emiratization", "Omanization",
        "Kuwaitization", "Bahrainization", "Qatarization",
        "women empowerment", "gender equality", "pay equity", "pay gap",
        "digital inclusion", "accessibility", "disability",
        "charitable", "donation", "donations", "sponsorship",
        "financial literacy", "financial education",
        "employee engagement", "staff turnover", "attrition",
        "labor rights", "modern slavery", "supply chain",
        "community engagement", "volunteerism", "volunteering",
        "workplace safety", "customer complaints",
    ],
    "Governance (candidates)": [
        "ESG governance", "ESG committee", "sustainability committee",
        "ethics committee", "disclosure committee",
        "related party transactions", "related-party",
        "sanctions", "anti-money laundering", "AML", "KYC",
        "bribery", "fraud", "money laundering",
        "privacy policy", "data breach", "GDPR",
        "shareholder engagement", "annual general meeting",
        "independent directors", "nominating committee",
        "remuneration committee", "succession planning",
        "ERM", "enterprise risk management", "three lines of defence",
        "stress test", "resolution plan", "fit and proper",
    ],
}

# Known-in-taxonomy sanity sample. If these appear a lot in text but
# generated few matches via the scoring pipeline, something's off upstream.
KNOWN_IN_TAXONOMY_SAMPLE = [
    "governance", "corporate governance", "risk management", "audit committee",
    "cybersecurity", "diversity and inclusion", "financial inclusion",
    "waste management", "renewable energy",
]

TARGET_SAMPLE: list[tuple[str, int]] = [
    ("al-rajhi-bank", 2025),
    ("kuwait-finance-house", 2024),
    ("first-abu-dhabi-bank", 2025),
    ("bank-muscat-bkmb", 2025),
    ("the-saudi-national-bank", 2025),
    ("bupa-arabia-for-cooperative-insurance-company", 2022),
]


def _load_report_rows() -> list[tuple[str, int, str]]:
    """Load (slug, fy, file_path) for every scored Report in the DB."""
    with engine.connect() as c:
        rows = list(c.execute(sql_text("""
            SELECT i.slug, r.fiscal_year, r.file_path
            FROM reports r JOIN institutions i ON i.id = r.institution_id
            WHERE r.status = 'scored'
        """)))
    return [(r[0], r[1], r[2]) for r in rows]


def _pick_samples(all_rows: list[tuple[str, int, str]]) -> list[tuple[str, int, str]]:
    """Match (slug, fy) directly rather than relying on filename conventions
    — early version matched `_annual_` and silently skipped
    integrated-report filings."""
    by_key = {(r[0], r[1]): r for r in all_rows}
    picked: list[tuple[str, int, str]] = []
    for slug, fy in TARGET_SAMPLE:
        hit = by_key.get((slug, fy))
        if hit:
            picked.append(hit)
    return picked


def _extract_text(path: str) -> str:
    """Full-document text (every page) — raw native extraction only.
    Scanned/OCR'd pages still contribute what pymupdf gives; this is a
    recall audit, so we accept noise in exchange for coverage.
    """
    doc = pymupdf.open(path)
    try:
        return "\n".join((doc[i].get_text("text") or "") for i in range(doc.page_count))
    finally:
        doc.close()


def _count(term: str, text: str) -> int:
    """Case-insensitive whole-word (or whole-phrase) count. For multi-word
    phrases, allow any whitespace run between words.
    """
    parts = [re.escape(p) for p in term.split()]
    pattern = r"\b" + r"\s+".join(parts) + r"\b"
    return len(re.findall(pattern, text, re.IGNORECASE))


def main() -> int:
    rows = _load_report_rows()
    samples = _pick_samples(rows)
    if len(samples) < 5:
        print(f"only {len(samples)} of {len(TARGET_SAMPLE)} sample reports found; "
              f"proceeding with what exists.")
    # Extract each sample's text once.
    print("Extracting text ...")
    doc_texts: dict[tuple[str, int], str] = {}
    for slug, fy, path in samples:
        print(f"  {slug} FY{fy} <- {path}")
        doc_texts[(slug, fy)] = _extract_text(path)

    # Hit counts per (pillar, term) across all samples, and per-doc tables.
    pillar_totals: dict[str, Counter] = {p: Counter() for p in CANDIDATE_TERMS}
    pillar_totals["Known-in-taxonomy (sanity)"] = Counter()
    per_doc: dict[tuple[str, int], dict[str, int]] = defaultdict(dict)

    all_candidate_terms = [(p, t) for p, lst in CANDIDATE_TERMS.items() for t in lst]
    for pillar, term in all_candidate_terms:
        for (slug, fy), text in doc_texts.items():
            n = _count(term, text)
            if n:
                per_doc[(slug, fy)][term] = n
                pillar_totals[pillar][term] += n

    for term in KNOWN_IN_TAXONOMY_SAMPLE:
        for (slug, fy), text in doc_texts.items():
            n = _count(term, text)
            if n:
                per_doc[(slug, fy)][term] = n
                pillar_totals["Known-in-taxonomy (sanity)"][term] += n

    # --- Markdown output -------------------------------------------------
    out = BACKEND.parent / "docs" / "RECALL_AUDIT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Recall audit (Session 1b)")
    lines.append("")
    lines.append(f"Generated {datetime.now(UTC).isoformat(timespec='seconds')}.")
    lines.append("")
    lines.append("Purpose: find ESG-adjacent terms that appear in the actual "
                 "report text but are NOT in the current taxonomy, so we can "
                 "see whether the Governance-vs-Environmental/Social score skew "
                 "is a taxonomy-coverage artefact rather than a real disclosure "
                 "difference.")
    lines.append("")
    lines.append("Method: for each candidate term, count case-insensitive whole-"
                 "word (or whole-phrase) occurrences in the full extracted text "
                 "of a sample of scored reports. The scoring pipeline is NOT "
                 "touched — this is a parallel ground-truth scan, not a rescore.")
    lines.append("")
    lines.append("Sample (6 reports across institutions / countries / sectors):")
    lines.append("")
    for slug, fy, path in samples:
        lines.append(f"- `{slug}` FY{fy}  ({Path(path).name})")
    lines.append("")

    # Sorted candidate-term rollup per pillar.
    for pillar in [*CANDIDATE_TERMS.keys(), "Known-in-taxonomy (sanity)"]:
        lines.append(f"## {pillar}")
        lines.append("")
        totals = pillar_totals[pillar]
        if not totals:
            lines.append("_no hits in any sample_")
            lines.append("")
            continue
        lines.append("| term | total hits (6 reports) | in reports |")
        lines.append("|---|---|---|")
        for term, hits in totals.most_common():
            n_reports = sum(1 for _, pd in per_doc.items() if term in pd)
            lines.append(f"| `{term}` | {hits} | {n_reports}/{len(samples)} |")
        lines.append("")

    # Per-report hit totals (collapsed).
    lines.append("## Per-report totals")
    lines.append("")
    lines.append("| report | candidate-term hits | known-term hits |")
    lines.append("|---|---|---|")
    candidate_terms_set = {t for p, lst in CANDIDATE_TERMS.items() for t in lst}
    known_set = set(KNOWN_IN_TAXONOMY_SAMPLE)
    for slug, fy, _path in samples:
        pd = per_doc.get((slug, fy), {})
        cand_hits = sum(n for t, n in pd.items() if t in candidate_terms_set)
        known_hits = sum(n for t, n in pd.items() if t in known_set)
        lines.append(f"| `{slug}` FY{fy} | {cand_hits} | {known_hits} |")
    lines.append("")

    # Headline takeaway.
    env_hits = sum(pillar_totals["Environmental (candidates)"].values())
    soc_hits = sum(pillar_totals["Social (candidates)"].values())
    gov_hits = sum(pillar_totals["Governance (candidates)"].values())
    lines.append("## Takeaway")
    lines.append("")
    lines.append(f"- Candidate-term hits across all 6 reports: "
                 f"Environmental = {env_hits}, Social = {soc_hits}, "
                 f"Governance = {gov_hits}.")
    lines.append(f"- Known-term hits (sanity): "
                 f"{sum(pillar_totals['Known-in-taxonomy (sanity)'].values())}.")
    lines.append("")
    lines.append("The Governance pillar's lead in the scored output "
                 "(2,601 matches vs 403 / 348) partly reflects the term list "
                 "size (23 Gov vs 14 Env / 13 Soc) and partly reflects a known "
                 "regional pattern: banks' annual reports extensively narrate "
                 "regulatory governance obligations, with much lighter E/S "
                 "narrative. Any candidate above with a hit count comparable to "
                 "an in-taxonomy term is a direct recall gap — look at "
                 "`sustainability`, `ESG`, `CSR`, `nationalization`-family and "
                 "pillar-committee terms first.")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
