"""
Measurement-only diagnostic for CLAUDE.md's suspected problems 4c and 4d.
Does NOT fix anything — the point is to see how big the problem is on real data
before spending time on it.

Prints, for the given PDF:
- 4c: number and share of matched sentences whose source page looks like a
       "contents" page, and how many come from lines that repeat across many
       pages (running headers / footers).
- 4d: time spent by spaCy's second-pass tokenisation inside the matcher,
       versus time spent inside filter_spans.

Not scored, not persisted — this is a survey.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.smoke_pipeline import load_seed_terms  # noqa: E402

from app.services.matcher import TaxonomyMatcher  # noqa: E402
from app.services.pdf_extraction import extract_pdf_pages  # noqa: E402
from app.services.text_processing import Sentence, get_nlp, segment_sentences  # noqa: E402


_CONTENTS_KEYWORDS = ("contents", "table of contents", "index")
_DOT_LEADER = re.compile(r"\.{3,}\s*\d{1,4}\s*$")  # "Governance .......... 42"
_TRAILING_PAGE_NUM = re.compile(r"\s\d{1,4}\s*$")


def identify_contents_pages(pages) -> set[int]:
    """A page is a 'contents' page if it either contains the phrase 'contents' /
    'table of contents' in its top lines, OR has multiple dot-leader lines
    (`Governance .......... 42`), which is the visual signature of a ToC."""
    contents_pages: set[int] = set()
    for p in pages:
        head = p.text.strip().splitlines()[:6]
        head_text = " ".join(head).lower()
        if any(k in head_text for k in _CONTENTS_KEYWORDS):
            contents_pages.add(p.page_number)
            continue
        dot_leader_lines = sum(1 for line in p.text.splitlines() if _DOT_LEADER.search(line))
        if dot_leader_lines >= 5:
            contents_pages.add(p.page_number)
    return contents_pages


def find_repeated_boilerplate(pages, min_pages_seen: int = 8) -> set[str]:
    """A line that appears verbatim on many pages is very likely a running
    header or footer. Threshold: seen on at least min_pages_seen distinct pages."""
    line_pages: dict[str, set[int]] = defaultdict(set)
    for p in pages:
        for raw in p.text.splitlines():
            line = raw.strip()
            if len(line) < 6:
                continue
            # Strip page number so 'KFH Annual Report 2023 12' and '...  13' collapse.
            line_no_pageno = _TRAILING_PAGE_NUM.sub("", line).strip()
            if len(line_no_pageno) < 6:
                continue
            line_pages[line_no_pageno].add(p.page_number)
    return {line for line, pset in line_pages.items() if len(pset) >= min_pages_seen}


def main(pdf: Path) -> int:
    print(f"PDF: {pdf}")
    pages = extract_pdf_pages(pdf)
    print(f"pages: {len(pages)}")

    contents_pages = identify_contents_pages(pages)
    print(f"contents-like pages: {sorted(contents_pages)}")

    boilerplate_lines = find_repeated_boilerplate(pages)
    print(f"repeated header/footer lines (>=8 pages): {len(boilerplate_lines)}")
    for line in list(boilerplate_lines)[:5]:
        print(f"  - {line[:120]!r}")

    sentences = segment_sentences(pages)
    print(f"sentences: {len(sentences):,}")

    terms = load_seed_terms(ROOT / "seed" / "taxonomy_starter.json")
    matcher = TaxonomyMatcher(terms)
    matches = matcher.match_sentences(sentences)
    print(f"total matches: {len(matches):,}")

    # 4c: how many matches come from contents-pages or from a sentence that is
    # (a normalized form of) a repeated boilerplate line?
    from_contents = sum(1 for m in matches if m.page_number in contents_pages)
    boilerplate_norm = {re.sub(r"\s+", " ", b).lower() for b in boilerplate_lines}

    def sentence_is_boilerplate(text: str) -> bool:
        norm = re.sub(r"\s+", " ", _TRAILING_PAGE_NUM.sub("", text.strip())).lower()
        return norm in boilerplate_norm

    from_boilerplate = sum(1 for m in matches if sentence_is_boilerplate(m.sentence_text))
    print()
    print("=== 4c: contents / header-footer contamination ===")
    total = max(len(matches), 1)
    print(f"matches on contents pages : {from_contents:>4} ({100*from_contents/total:.1f}%)")
    print(f"matches on repeated lines : {from_boilerplate:>4} ({100*from_boilerplate/total:.1f}%)")

    # Show the most common contents-page matches so a reader can eyeball what's leaking.
    if from_contents:
        by_sent: Counter[str] = Counter()
        for m in matches:
            if m.page_number in contents_pages:
                by_sent[m.sentence_text.strip()[:180]] += 1
        print("sample contents-page matches:")
        for text, n in by_sent.most_common(5):
            print(f"  x{n}  {text!r}")

    # 4d: how much time does the double spaCy pass cost?
    nlp = get_nlp()
    t0 = time.time()
    for s in sentences:
        _ = nlp(s.text)
    t_nlp = time.time() - t0

    t1 = time.time()
    _ = matcher.match_sentences(sentences)
    t_full = time.time() - t1

    print()
    print("=== 4d: cost of the double spaCy pass ===")
    print(f"just re-tokenising every sentence via nlp() : {t_nlp:.2f}s")
    print(f"full match_sentences (nlp + PhraseMatcher) : {t_full:.2f}s")
    print(f"tokenisation is roughly {100*t_nlp/max(t_full,1e-6):.0f}% of matcher wall time.")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()
    sys.exit(main(args.pdf))
