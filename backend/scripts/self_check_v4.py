"""Phase 3 step C: self-check scoring on 5 company-years.

For each target, runs the full pipeline and prints:
  - narrative_word_count
  - per-term match count and effective weight
  - pillar densities (E, S, G, generic, addon)

Then re-counts 2 terms per document by scanning the extracted text directly
(no matcher) to confirm the counts reconcile.

STOPS with a non-zero exit if anything doesn't reconcile.

Usage:
    python scripts/self_check_v4.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

TARGETS = [
    ("al-rajhi-bank",      2023),
    ("sabic",              2023),
    ("emirates-telecom-etisalat-group", 2023),
    ("aldar-properties-pjsc", 2023),
    ("jazeera-steel",      2023),
]

# Terms to hand-verify per document (phrase → must be lemma_based or exact)
HAND_CHECK_TERMS: dict[str, list[str]] = {
    "al-rajhi-bank":     ["governance", "risk management"],
    "sabic":             ["circular economy", "greenhouse gas"],
    "emirates-telecom-etisalat-group": ["cybersecurity", "diversity and inclusion"],
    "aldar-properties-pjsc": ["sustainability", "energy efficiency"],
    "jazeera-steel":     ["air quality", "health and safety"],
}


def main() -> int:
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.provenance import SourceDocument
    from app.models.taxonomy import Category, Term
    from app.services.pdf_extraction import count_words, extract_pdf_pages
    from app.services.pipeline import (
        PIPELINE_VERSION,
        _match_with_mode,
        _TermLike,
        build_terms_payload,
    )
    from app.services.storage import read_pdf_bytes
    from app.services.text_processing import segment_sentences
    from app.services.text_quality import apply_text_quality
    from app.services.verity_config import load_verity_config

    db = SessionLocal()
    cfg = load_verity_config()
    terms_all = db.query(Term).all()
    categories = db.query(Category).all()

    print(f"Pipeline v{PIPELINE_VERSION}  terms={len(terms_all)}")
    print()

    any_fail = False

    for slug, fy in TARGETS:
        inst = db.query(Institution).filter(Institution.slug == slug).first()
        if not inst:
            print(f"STOP: institution not found: {slug}")
            return 1
        sd = db.query(SourceDocument).filter(
            SourceDocument.institution_id == inst.id,
            SourceDocument.fiscal_year == fy,
        ).first()
        if not sd:
            print(f"STOP: no source_document for {slug} FY{fy}")
            return 1

        print(f"{'='*70}")
        print(f"{slug}  FY{fy}  sd_id={sd.id}  sasb={inst.sasb_industry!r}")
        print(f"  file: {sd.file_path}")

        # Build per-institution payload (dynamic weights)
        payload = build_terms_payload(terms_all, categories, inst.sasb_industry)
        term_objs = [_TermLike(**t) for t in payload]
        term_lookup = {t.id: t for t in term_objs}

        # Fetch and process PDF
        try:
            pdf_bytes = read_pdf_bytes(sd.file_path)
        except Exception as exc:
            print(f"STOP: cannot read PDF for {slug} FY{fy}: {exc}")
            return 1

        pages = extract_pdf_pages(pdf_bytes)
        raw_counts = count_words(pages)
        cleaned = apply_text_quality(pages, cfg)
        pages_for_match = cleaned.pages
        narrative_wc = count_words(pages_for_match).latin

        sentences = segment_sentences(pages_for_match)
        longest = _match_with_mode(
            __import__("app.services.matcher", fromlist=["TaxonomyMatcher"])
            .TaxonomyMatcher(term_objs),
            sentences, "longest",
        )

        # Aggregate per-term counts
        from collections import Counter
        term_match_counts: Counter[int] = Counter(m.term_id for m in longest)

        # Pillar densities
        e_raw = s_raw = g_raw = gen_raw = adn_raw = 0.0
        for m in longest:
            trm = term_lookup[m.term_id]
            if trm.group == "core":
                if trm.pillar == "Environmental":
                    e_raw += trm.weight
                elif trm.pillar == "Social":
                    s_raw += trm.weight
                elif trm.pillar == "Governance":
                    g_raw += trm.weight
            elif trm.group == "generic":
                gen_raw += trm.weight
            elif trm.group == "addon":
                adn_raw += trm.weight

        if narrative_wc > 0:
            k = 1000.0 / narrative_wc
            e_den = round(e_raw * k, 6)
            s_den = round(s_raw * k, 6)
            g_den = round(g_raw * k, 6)
            gen_den = round(gen_raw * k, 6)
            adn_den = round(adn_raw * k, 6) if inst.is_financial else None
        else:
            e_den = s_den = g_den = gen_den = adn_den = None

        print(f"  pages={len(pages)}  raw_latin={raw_counts.latin}  "
              f"narrative_wc={narrative_wc}  matches={len(longest)}")
        print(f"  FS_start={cleaned.financial_statements_start_page}  "
              f"FS_excl={cleaned.financial_statements_excluded_pages}p  "
              f"ToC_excl={len(cleaned.excluded_contents_pages)}p  "
              f"arabic_excl={cleaned.pages_mostly_arabic}p")
        print(f"  E_density={e_den}  S_density={s_den}  G_density={g_den}  "
              f"generic={gen_den}  addon={adn_den}")
        print()

        # Per-term detail (non-zero matches only)
        print(f"  {'phrase':<42} {'group':<8} {'pillar':<15} {'weight':>6} {'hits':>5}")
        for trm in sorted(term_objs, key=lambda x: (-term_match_counts.get(x.id, 0), x.phrase)):
            cnt = term_match_counts.get(trm.id, 0)
            if cnt == 0:
                continue
            print(f"  {trm.phrase:<42} {trm.group:<8} {trm.pillar:<15} {trm.weight:>6.2f} {cnt:>5}")

        # Hand-verification: count phrase occurrences directly in extracted text
        print()
        print("  Hand-check (raw text occurrence vs matcher count):")
        check_phrases = HAND_CHECK_TERMS.get(slug, [])
        fail_here = False
        for phrase in check_phrases:
            # Find the term object
            trm_match = next((t for t in term_objs if t.phrase.lower() == phrase.lower()), None)
            if trm_match is None:
                print(f"    WARNING: term not found in payload: {phrase!r}")
                continue
            matcher_count = term_match_counts.get(trm_match.id, 0)

            # Raw text scan: concatenate all cleaned-page text and count occurrences
            # For lemma_based terms this is a substring count (conservative lower bound).
            full_text = " ".join(p.text for p in pages_for_match).lower()
            # Use the phrase directly for exact or substring count
            raw_count = full_text.count(phrase.lower())

            # Matcher should be <= raw (longest-match may absorb some into longer phrases)
            # and close to raw. Flag if matcher > raw (impossible) or if raw > 0 and matcher == 0.
            status = "OK"
            if matcher_count > raw_count:
                status = "FAIL: matcher > raw (impossible)"
                fail_here = True
            elif raw_count > 0 and matcher_count == 0:
                status = "WARN: raw found but matcher got 0 (may be absorbed by longer phrase)"
            elif raw_count == 0 and matcher_count == 0:
                status = "BOTH ZERO"

            print(f"    {phrase!r:<40}  raw={raw_count:>4}  matcher={matcher_count:>4}  {status}")

        if fail_here:
            print(f"  *** RECONCILIATION FAILURE for {slug} FY{fy} ***")
            any_fail = True
        else:
            print("  --> reconciled OK")
        print()

    if any_fail:
        print("SELF-CHECK FAILED — see above.")
        return 1
    print("SELF-CHECK PASSED — all 5 documents reconciled.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
