"""
Orchestrates the full per-report processing pipeline:

  PDF file -> OCR pre-check -> extract pages -> text-quality cleaning
  -> segment into sentences -> match phrases -> compute category scores
  -> persist CategoryScore + MatchEvidence rows and the audit on Report.

Reprocessing under a new (taxonomy_version, pipeline_version) APPENDS new
score / evidence rows rather than deleting the old ones — old numbers
stay traceable and comparable.

The CPU-heavy work (extract/segment/match) is wrapped by run_report_worker,
which the batch runner can hand to a ProcessPoolExecutor. DB writes always
happen in the main process so SQLite's write serialisation stays sane.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.report import Report, ReportStatus
from app.models.score import CategoryScore, MatchEvidence
from app.models.taxonomy import Category, TaxonomyVersion, Term
from app.services.matcher import TaxonomyMatcher
from app.services.pdf_extraction import count_words, extract_pdf_pages
from app.services.scoring import composite_score, score_report_categories
from app.services.storage import read_pdf_bytes
from app.services.taxonomy_hash import compute_taxonomy_hash
from app.services.text_processing import segment_sentences
from app.services.text_quality import apply_text_quality, estimate_ocr_fraction
from app.services.verity_config import VerityConfig, load_verity_config

# Bumped whenever cleaning or matching logic changes. Stored on every
# CategoryScore / MatchEvidence row so historical scores stay linked to the
# code path that produced them. 0.3.0 adds the Session 5 text-quality
# switches (header/footer removal, contents detection, FS boundary).
PIPELINE_VERSION = "0.3.0"


# --------------------------------------------------------------------------- #
# Worker-return struct. Everything a worker computes but can't persist (DB
# sessions aren't shared across processes) ships back in this dataclass.
# --------------------------------------------------------------------------- #


@dataclass
class TermMatchRow:
    term_id: int
    page_number: int
    sentence_text: str


@dataclass
class CategoryScoreRow:
    category_id: int
    raw_weighted_count: float
    density_per_1000_words: float


@dataclass
class WorkerResult:
    source_document_id: int
    file_path: str
    status: str  # "scored" | "needs_review" | "error"
    error_message: str | None = None

    # Timings in seconds. Any stage that didn't run stays None.
    extract_seconds: float | None = None
    segment_seconds: float | None = None
    match_seconds: float | None = None
    total_seconds: float | None = None

    # Page/word stats
    page_count: int = 0
    latin_word_count: int = 0
    arabic_word_count: int = 0

    # OCR cap bookkeeping
    ocr_page_count: int = 0
    ocr_page_ratio: float | None = None

    # Text-quality audit
    repeated_lines_removed: int = 0
    excluded_contents_pages: list[int] = field(default_factory=list)
    pages_mostly_arabic: int = 0
    financial_statements_start_page: int | None = None
    financial_statements_excluded_pages: int = 0

    # Matching diagnostic
    matches_count: int = 0
    all_mode_extra_matches: int | None = None

    # Payloads for DB writer
    matches: list[TermMatchRow] = field(default_factory=list)
    category_scores: list[CategoryScoreRow] = field(default_factory=list)
    composite: float | None = None

    # Review bookkeeping specific to processing (vs source_document review).
    processing_review_status: str = "auto_ok"
    processing_review_reason: str | None = None


# --------------------------------------------------------------------------- #
# Pure CPU worker. No DB access, no logger spam — safe for ProcessPoolExecutor.
# Returns a WorkerResult the main process can commit under one transaction.
# --------------------------------------------------------------------------- #


def _run_pipeline_cpu(
    *,
    source_document_id: int,
    file_path: str,
    terms_payload: list[dict],
    cfg: VerityConfig,
) -> WorkerResult:
    """CPU-side of the pipeline. terms_payload is a plain-dict snapshot of
    the Term rows so this function stays serialisable across processes.
    Each dict: {id, phrase, weight, lemma_based, category_id}.
    """
    t_total = time.monotonic()
    result = WorkerResult(source_document_id=source_document_id, file_path=file_path,
                          status="scored")

    # Session 9: PDFs live in R2. Fetch bytes once and hand the same buffer
    # to both the OCR pre-check and the full extraction so a report is one
    # network round trip, not two. `file_path` is now the R2 object key
    # (e.g. "al-rajhi-bank/2025_integrated_e66e4adf.pdf"); local-disk paths
    # also work for dev / tests via the storage module's filesystem fallback.
    try:
        pdf_bytes = read_pdf_bytes(file_path)
    except Exception as exc:
        result.status = "error"
        result.error_message = f"fetch pdf bytes failed: {exc}"
        result.total_seconds = time.monotonic() - t_total
        return result

    # OCR pre-check: cheap scan of native-text yield per page. If too much
    # of the report would need OCR, skip the slow pass and flag the file
    # as heavily scanned rather than spending hours on it.
    from app.config import settings
    try:
        ocr_fraction, total_pages = estimate_ocr_fraction(
            pdf_bytes, settings.ocr_trigger_char_threshold
        )
    except Exception as exc:
        result.status = "error"
        result.error_message = f"ocr pre-check failed: {exc}"
        result.total_seconds = time.monotonic() - t_total
        return result

    result.ocr_page_ratio = ocr_fraction
    result.page_count = total_pages

    if ocr_fraction > cfg.ocr_max_page_ratio:
        result.status = "needs_review"
        result.processing_review_status = "needs_review"
        result.processing_review_reason = (
            f"heavily scanned: {ocr_fraction:.0%} of {total_pages} pages would need "
            f"OCR (> {cfg.ocr_max_page_ratio:.0%} cap); skipped to avoid multi-hour run"
        )
        result.total_seconds = time.monotonic() - t_total
        return result

    # Extract
    t = time.monotonic()
    try:
        pages = extract_pdf_pages(pdf_bytes)
    except Exception as exc:
        result.status = "error"
        result.error_message = f"extract_pdf_pages failed: {exc}"
        result.total_seconds = time.monotonic() - t_total
        return result
    result.extract_seconds = time.monotonic() - t
    result.page_count = len(pages)
    result.ocr_page_count = sum(1 for p in pages if p.used_ocr)

    counts = count_words(pages)
    result.latin_word_count = counts.latin
    result.arabic_word_count = counts.arabic

    # Text-quality cleaning (every switch logs its effect on `result`).
    cleaned = apply_text_quality(pages, cfg)
    result.repeated_lines_removed = cleaned.repeated_lines_removed
    result.excluded_contents_pages = cleaned.excluded_contents_pages
    result.pages_mostly_arabic = cleaned.pages_mostly_arabic
    result.financial_statements_start_page = cleaned.financial_statements_start_page
    result.financial_statements_excluded_pages = cleaned.financial_statements_excluded_pages
    pages_for_match = cleaned.pages

    # Segment
    t = time.monotonic()
    sentences = segment_sentences(pages_for_match)
    result.segment_seconds = time.monotonic() - t

    # Match. We run longest-mode (what we score) and, if enabled, a shadow
    # all-mode pass purely to report "how many extra would 'all' have added".
    # Shadow needs its own matcher config, so swap the config via a cheap
    # context manager that monkey-patches the module-level loader.
    terms = [_TermLike(**t) for t in terms_payload]
    t = time.monotonic()
    longest_matcher = TaxonomyMatcher(terms)
    # Force longest-mode even if the file's config says otherwise, so the
    # scored matches follow the primary mode consistently.
    longest = _match_with_mode(longest_matcher, sentences, "longest")
    result.match_seconds = time.monotonic() - t
    result.matches_count = len(longest)

    if cfg.log_all_mode_diff:
        all_matches = _match_with_mode(longest_matcher, sentences, "all")
        result.all_mode_extra_matches = max(0, len(all_matches) - len(longest))

    # Score (density per 1000 Latin words — denominator is the FULL report's
    # Latin word count, matching Session 1's definition; cleaning changes
    # which sentences are matched, not the denominator).
    term_lookup = {t.id: t for t in terms}
    category_results = score_report_categories(longest, term_lookup, counts.latin)
    result.category_scores = [
        CategoryScoreRow(category_id=c.category_id,
                         raw_weighted_count=c.raw_weighted_count,
                         density_per_1000_words=c.density_per_1000_words)
        for c in category_results
    ]
    # Convenience composite: sum of (density * category_weight). The scorer
    # expects a {category_id: weight} dict so pass taxonomy-stored weights.
    cat_weights = {t.category_id: t.category_weight for t in terms}
    # Collapse duplicates (same category_id across many terms with the same weight).
    cat_weights = dict(cat_weights.items())
    result.composite = composite_score(category_results, cat_weights)

    result.matches = [
        TermMatchRow(term_id=m.term_id, page_number=m.page_number,
                     sentence_text=m.sentence_text)
        for m in longest
    ]
    result.total_seconds = time.monotonic() - t_total
    return result


class _TermLike:
    """Plain object stand-in for Term ORM rows inside workers — needed
    because ORM instances aren't pickleable across process boundaries.
    """
    __slots__ = ("category_id", "category_weight", "id", "lemma_based", "phrase", "weight")

    def __init__(self, id: int, phrase: str, weight: float, lemma_based: bool,
                 category_id: int, category_weight: float) -> None:
        self.id = id
        self.phrase = phrase
        self.weight = weight
        self.lemma_based = lemma_based
        self.category_id = category_id
        self.category_weight = category_weight


def _match_with_mode(matcher: TaxonomyMatcher, sentences: list, mode: str):
    """Call matcher.match_sentences with a locally-forced matching mode.

    TaxonomyMatcher reads mode from `load_verity_config()` on every call,
    so we temporarily replace that in the matcher module.
    """
    from app.services import matcher as matcher_module

    original = matcher_module.load_verity_config
    try:
        matcher_module.load_verity_config = lambda path=None: VerityConfig(matching_mode=mode)
        return matcher.match_sentences(sentences)
    finally:
        matcher_module.load_verity_config = original


def build_terms_payload(terms: list[Term], categories: list[Category]) -> list[dict]:
    """Snapshot every Term as a plain dict (+ its category weight so
    the worker can compute composite without a DB session)."""
    cat_weight = {c.id: c.weight for c in categories}
    return [
        {
            "id": t.id,
            "phrase": t.phrase,
            "weight": float(t.weight),
            "lemma_based": bool(t.lemma_based),
            "category_id": t.category_id,
            "category_weight": float(cat_weight.get(t.category_id, 1.0)),
        }
        for t in terms
    ]


# --------------------------------------------------------------------------- #
# DB side. Idempotency key: (source_document.sha256, taxonomy_version_id,
# pipeline_version). An existing Report under that key is skipped unless
# --force was passed.
# --------------------------------------------------------------------------- #


def _current_taxonomy_version(db: Session) -> TaxonomyVersion:
    categories = db.query(Category).all()
    payload = [
        {
            "name": c.name,
            "pillar": c.pillar,
            "weight": c.weight,
            "terms": [
                {"phrase": t.phrase, "weight": t.weight, "lemma_based": t.lemma_based}
                for t in c.terms
            ],
        }
        for c in categories
    ]
    h = compute_taxonomy_hash(payload)
    existing = db.query(TaxonomyVersion).filter(TaxonomyVersion.hash == h).first()
    if existing:
        return existing
    row = TaxonomyVersion(hash=h, note="autoregistered by pipeline")
    db.add(row)
    db.flush()
    return row


def existing_report_for(
    db: Session, *, source_document_id: int, taxonomy_version_id: int,
    pipeline_version: str,
) -> Report | None:
    """Idempotency check. The Report → CategoryScore link stores the
    taxonomy/pipeline version pair, so we join through there."""
    q = (
        db.query(Report)
        .join(CategoryScore, CategoryScore.report_id == Report.id)
        .filter(
            Report.source_document_id == source_document_id,
            CategoryScore.taxonomy_version_id == taxonomy_version_id,
            CategoryScore.pipeline_version == pipeline_version,
        )
    )
    return q.first()


def persist_worker_result(
    db: Session, *, worker_result: WorkerResult,
    institution_id: int, fiscal_year: int,
    taxonomy_version: TaxonomyVersion,
) -> Report:
    """Commit a WorkerResult to the DB in one transaction. Returns the Report
    row (created or updated).
    """
    report = Report(
        institution_id=institution_id,
        source_document_id=worker_result.source_document_id,
        fiscal_year=fiscal_year,
        file_path=worker_result.file_path,
        page_count=worker_result.page_count,
        latin_word_count=worker_result.latin_word_count,
        arabic_word_count=worker_result.arabic_word_count,
        total_word_count=worker_result.latin_word_count + worker_result.arabic_word_count,
        status=(ReportStatus.scored if worker_result.status == "scored"
                else ReportStatus.error if worker_result.status == "error"
                else ReportStatus.uploaded),
        error_message=worker_result.error_message,
        taxonomy_version=taxonomy_version.hash,
        pipeline_version=PIPELINE_VERSION,
        extract_seconds=worker_result.extract_seconds,
        segment_seconds=worker_result.segment_seconds,
        match_seconds=worker_result.match_seconds,
        total_seconds=worker_result.total_seconds,
        ocr_page_count=worker_result.ocr_page_count,
        ocr_page_ratio=worker_result.ocr_page_ratio,
        repeated_lines_removed=worker_result.repeated_lines_removed,
        excluded_contents_pages=worker_result.excluded_contents_pages or None,
        pages_mostly_arabic=worker_result.pages_mostly_arabic,
        financial_statements_start_page=worker_result.financial_statements_start_page,
        financial_statements_excluded_pages=worker_result.financial_statements_excluded_pages,
        matches_count=worker_result.matches_count,
        all_mode_extra_matches=worker_result.all_mode_extra_matches,
        composite_score=worker_result.composite,
        processing_review_status=worker_result.processing_review_status,
        processing_review_reason=worker_result.processing_review_reason,
    )
    db.add(report)
    db.flush()  # need report.id

    for cs in worker_result.category_scores:
        db.add(CategoryScore(
            report_id=report.id,
            category_id=cs.category_id,
            raw_weighted_count=cs.raw_weighted_count,
            density_per_1000_words=cs.density_per_1000_words,
            taxonomy_version_id=taxonomy_version.id,
            taxonomy_version=taxonomy_version.hash,
            pipeline_version=PIPELINE_VERSION,
        ))
    for m in worker_result.matches:
        db.add(MatchEvidence(
            report_id=report.id,
            term_id=m.term_id,
            page_number=m.page_number,
            sentence_text=m.sentence_text,
            taxonomy_version_id=taxonomy_version.id,
            pipeline_version=PIPELINE_VERSION,
        ))
    db.commit()
    db.refresh(report)
    return report


# --------------------------------------------------------------------------- #
# Legacy single-report entrypoint. Kept for callers that already pass in a
# pre-created Report ORM instance (upload handler). Routes through the
# worker/persist pair but inside the same process.
# --------------------------------------------------------------------------- #


def process_report(db: Session, report: Report) -> Report:
    """Run the full pipeline synchronously against an existing Report."""
    cfg = load_verity_config()
    terms = db.query(Term).all()
    categories = db.query(Category).all()
    if not terms:
        raise ValueError(
            "No taxonomy terms defined yet — add categories/terms before scoring reports."
        )
    payload = build_terms_payload(terms, categories)
    tv = _current_taxonomy_version(db)
    worker = _run_pipeline_cpu(
        source_document_id=report.source_document_id or 0,
        file_path=report.file_path, terms_payload=payload, cfg=cfg,
    )
    # Fold the worker result back onto the existing Report row.
    for col in ("extract_seconds", "segment_seconds", "match_seconds", "total_seconds",
                "page_count", "latin_word_count", "arabic_word_count",
                "ocr_page_count", "ocr_page_ratio",
                "repeated_lines_removed", "pages_mostly_arabic",
                "financial_statements_start_page", "financial_statements_excluded_pages",
                "matches_count", "all_mode_extra_matches",
                "processing_review_status", "processing_review_reason"):
        setattr(report, col, getattr(worker, col))
    report.excluded_contents_pages = worker.excluded_contents_pages or None
    report.composite_score = worker.composite
    report.taxonomy_version = tv.hash
    report.pipeline_version = PIPELINE_VERSION
    report.status = (ReportStatus.scored if worker.status == "scored"
                     else ReportStatus.error if worker.status == "error"
                     else ReportStatus.uploaded)
    report.error_message = worker.error_message

    for cs in worker.category_scores:
        db.add(CategoryScore(
            report_id=report.id, category_id=cs.category_id,
            raw_weighted_count=cs.raw_weighted_count,
            density_per_1000_words=cs.density_per_1000_words,
            taxonomy_version_id=tv.id, taxonomy_version=tv.hash,
            pipeline_version=PIPELINE_VERSION,
        ))
    for m in worker.matches:
        db.add(MatchEvidence(
            report_id=report.id, term_id=m.term_id,
            page_number=m.page_number, sentence_text=m.sentence_text,
            taxonomy_version_id=tv.id, pipeline_version=PIPELINE_VERSION,
        ))
    db.commit()
    db.refresh(report)
    return report
