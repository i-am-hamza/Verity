"""
Smoke-test the end-to-end pipeline on ONE real PDF, bypassing the HTTP layer.

Reports timings per stage, page/word counts, OCR-triggered pages, top matched
terms with two example sentences per term, and the per-category density.

Run from backend/:
    python scripts/smoke_pipeline.py tests/fixtures/real/kfh_annual_report_2023.pdf
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# Allow running from anywhere.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.matcher import TaxonomyMatcher  # noqa: E402
from app.services.pdf_extraction import count_words, extract_pdf_pages  # noqa: E402
from app.services.scoring import score_report_categories  # noqa: E402
from app.services.text_processing import segment_sentences  # noqa: E402


class SeedTerm:
    """Duck-type of app.models.taxonomy.Term for the matcher/scorer.

    Kept off the ORM on purpose: this script runs on the raw pipeline
    without any database.
    """
    __slots__ = ("id", "phrase", "weight", "lemma_based", "category_id", "category_name")

    def __init__(self, id: int, phrase: str, weight: float, lemma_based: bool,
                 category_id: int, category_name: str) -> None:
        self.id = id
        self.phrase = phrase
        self.weight = weight
        self.lemma_based = lemma_based
        self.category_id = category_id
        self.category_name = category_name


def load_seed_terms(seed_path: Path) -> list[SeedTerm]:
    categories = json.loads(seed_path.read_text(encoding="utf-8"))
    terms: list[SeedTerm] = []
    next_term_id = 1
    for cat_id, cat in enumerate(categories, start=1):
        for t in cat["terms"]:
            terms.append(SeedTerm(
                id=next_term_id,
                phrase=t["phrase"],
                weight=float(t.get("weight", 1.0)),
                lemma_based=bool(t.get("lemma_based", True)),
                category_id=cat_id,
                category_name=cat["name"],
            ))
            next_term_id += 1
    return terms


def main(pdf_path: Path) -> int:
    seed_path = ROOT / "seed" / "taxonomy_starter.json"
    terms = load_seed_terms(seed_path)
    term_lookup = {t.id: t for t in terms}

    print(f"PDF: {pdf_path}")
    print(f"size: {pdf_path.stat().st_size:,} bytes")

    t0 = time.time()
    pages = extract_pdf_pages(pdf_path)
    t_extract = time.time() - t0

    ocr_pages = [p.page_number for p in pages if p.used_ocr]
    counts = count_words(pages)

    t1 = time.time()
    sentences = segment_sentences(pages)
    t_segment = time.time() - t1

    t2 = time.time()
    matcher = TaxonomyMatcher(terms)
    t_matcher_init = time.time() - t2

    t3 = time.time()
    matches = matcher.match_sentences(sentences)
    t_match = time.time() - t3

    t4 = time.time()
    category_scores = score_report_categories(matches, term_lookup, counts.latin)
    t_score = time.time() - t4

    print()
    print("=== extraction ===")
    print(f"pages: {len(pages)}")
    print(f"native-text pages: {len(pages) - len(ocr_pages)}")
    print(f"OCR pages: {len(ocr_pages)} -> {ocr_pages[:20]}{'...' if len(ocr_pages) > 20 else ''}")
    print(f"Latin words (density denominator): {counts.latin:,}")
    print(f"Arabic words (not scored): {counts.arabic:,}")
    print(f"extract seconds: {t_extract:.2f}")

    print()
    print("=== segmentation ===")
    print(f"sentences: {len(sentences):,}")
    print(f"segment seconds: {t_segment:.2f}")

    print()
    print("=== matching ===")
    print(f"matcher init seconds: {t_matcher_init:.2f}")
    print(f"match seconds: {t_match:.2f}")
    print(f"total matches: {len(matches):,}")

    print()
    print("=== scoring ===")
    print(f"score seconds: {t_score:.2f}")
    for cs in category_scores:
        cat_name = next((t.category_name for t in terms if t.category_id == cs.category_id), "?")
        print(f"  cat={cat_name!r} raw={cs.raw_weighted_count:.2f} density_per_1000w={cs.density_per_1000_words:.3f}")

    print()
    print("=== top 15 matched terms with 2 example sentences ===")
    by_term_count: Counter[int] = Counter()
    examples: dict[int, list[str]] = defaultdict(list)
    for m in matches:
        by_term_count[m.term_id] += 1
        if len(examples[m.term_id]) < 2:
            examples[m.term_id].append(f"p{m.page_number}: {m.sentence_text[:220].replace(chr(10),' ')}")
    for term_id, count in by_term_count.most_common(15):
        t = term_lookup[term_id]
        print(f"- {t.phrase!r} ({t.category_name}) x{count}")
        for ex in examples[term_id]:
            print(f"    {ex}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", type=Path)
    args = parser.parse_args()
    sys.exit(main(args.pdf_path))
