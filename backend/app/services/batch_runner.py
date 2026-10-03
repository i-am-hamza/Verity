"""Batch runner for `python -m app.cli process`.

Separated from app.cli because it coordinates ProcessPoolExecutor workers,
SQLite writes and progress reporting — too big to live inline next to
argparse glue. The CLI layer just parses flags and calls `run_batch`.

Design:
- Worker processes do the CPU-heavy stage (extract → clean → segment →
  match). They never touch the DB; they return a WorkerResult.
- The main process holds the single SQLite session and commits each
  WorkerResult as it arrives, so SQLite's writer-serialisation stays sane.
- One bad PDF never stops the batch: the worker catches, the main process
  records the error on the Report row and keeps going.
- Idempotency: skip when a Report already exists under the current
  (sha256, taxonomy_version, pipeline_version) triplet unless --force.
- Resumability: after a crash, re-run the same command. Finished reports
  are skipped by the idempotency check; failed-mid-worker reports are
  reprocessed from scratch.
"""
from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.institution import Institution, Wave
from app.models.provenance import ReviewStatus, SourceDocument, SourceType
from app.models.run import Run
from app.models.taxonomy import Category, Term
from app.services.pipeline import (
    PIPELINE_VERSION,
    WorkerResult,
    _current_taxonomy_version,
    _run_pipeline_cpu,
    build_terms_payload,
    existing_report_for,
    persist_worker_result,
)
from app.services.reproducibility import config_hash, git_commit, manifest_hash
from app.services.verity_config import load_verity_config

log = logging.getLogger("verity.batch")


@dataclass
class BatchSummary:
    scored: int = 0
    needs_review: int = 0
    errors: int = 0
    skipped_idempotent: int = 0
    skipped_type_filter: int = 0
    skipped_source_review: int = 0
    total_candidates: int = 0
    timings_seconds: list[float] | None = None
    wall_clock_seconds: float = 0.0


def _select_candidates(
    db: Session, *, scope: str, only: list[str], fy: int | None,
    report_types_scored: list[str],
) -> tuple[list[SourceDocument], int, int]:
    """Return (candidates_matching_scope, skipped_type_filter, skipped_source_review).

    A SourceDocument is a candidate when:
    - its institution is in-scope (wave filter + optional slug filter),
    - its fiscal_year matches `fy` (or any year if fy is None),
    - its review_status is auto_ok,
    - its report_type is in config.report_types_scored.
    """
    q = db.query(SourceDocument).join(Institution, Institution.id == SourceDocument.institution_id)
    if scope == "financial":
        q = q.filter(Institution.wave == Wave.financial)
    elif scope == "other":
        q = q.filter(Institution.wave == Wave.other)
    # scope == "all" — no wave filter
    if only:
        q = q.filter(Institution.slug.in_(only))
    if fy is not None:
        q = q.filter(SourceDocument.fiscal_year == fy)

    all_matching = q.order_by(Institution.slug, SourceDocument.fiscal_year).all()

    cands: list[SourceDocument] = []
    skipped_type = 0
    skipped_review = 0
    skipped_superseded = 0
    types_lower = {t.lower() for t in report_types_scored}
    for sd in all_matching:
        if sd.review_status != ReviewStatus.auto_ok:
            skipped_review += 1
            continue
        if sd.superseded_by_id is not None:
            # Session 6: a colleague-supplied doc superseded this one for the
            # same (institution, FY). Keep the row for audit; don't rescore.
            skipped_superseded += 1
            continue
        if (sd.report_type.value if sd.report_type else "unknown") not in types_lower:
            skipped_type += 1
            continue
        cands.append(sd)
    # Preserve the two-value return API for existing callers.
    skipped_review += skipped_superseded
    return cands, skipped_type, skipped_review


def _auto_worker_count(configured: int) -> int:
    if configured and configured > 0:
        return configured
    cpu = os.cpu_count() or 2
    return max(1, cpu - 1)


def _progress(idx: int, total: int, result: WorkerResult, slug: str, fy: int) -> None:
    took = result.total_seconds or 0.0
    status = result.status
    extra = ""
    if status == "needs_review":
        extra = f" [{result.processing_review_reason or ''}]"[:80]
    elif status == "error":
        extra = f" [err: {result.error_message or ''}]"[:80]
    print(f"[{idx}/{total}] {slug} FY{fy}: {status} in {took:.1f}s"
          f"  pages={result.page_count} matches={result.matches_count}"
          f"  OCR={result.ocr_page_count}/{result.page_count}{extra}",
          flush=True)


def run_batch(
    db: Session, *, scope: str, only: list[str], fy: int | None, force: bool,
    worker_count_override: int | None = None,
) -> BatchSummary:
    cfg = load_verity_config()
    terms = db.query(Term).all()
    categories = db.query(Category).all()
    if not terms:
        raise RuntimeError(
            "No taxonomy terms in the DB. Load seed/taxonomy_starter.json first."
        )
    payload = build_terms_payload(terms, categories)
    tv = _current_taxonomy_version(db)

    candidates, skipped_type, skipped_review = _select_candidates(
        db, scope=scope, only=only, fy=fy,
        report_types_scored=cfg.report_types_scored,
    )
    summary = BatchSummary(
        total_candidates=len(candidates),
        skipped_type_filter=skipped_type,
        skipped_source_review=skipped_review,
    )

    # Idempotency pass: filter out anything already scored under current
    # (tv, pipeline_version) unless --force. --force always reprocesses
    # (producing additional rows, not overwriting — append-only).
    to_run: list[SourceDocument] = []
    for sd in candidates:
        if not force and existing_report_for(
            db, source_document_id=sd.id,
            taxonomy_version_id=tv.id, pipeline_version=PIPELINE_VERSION,
        ):
            summary.skipped_idempotent += 1
            continue
        to_run.append(sd)

    if not to_run:
        print(f"nothing to do: {len(candidates)} candidate(s), all up-to-date "
              f"under taxonomy={tv.hash[:8]} pipeline={PIPELINE_VERSION}"
              f"  (type-filter skipped {skipped_type}, source-review skipped {skipped_review})")
        return summary

    # Snapshot (institution_id, fiscal_year, file_path) up front since the
    # worker returns a WorkerResult referring to source_document_id only.
    sd_meta = {
        sd.id: (sd.institution_id, sd.fiscal_year, sd.file_path, sd.institution.slug)
        for sd in to_run
    }

    worker_n = _auto_worker_count(worker_count_override or cfg.worker_count)
    print(f"processing {len(to_run)} report(s) with {worker_n} worker(s)")
    print(f"  taxonomy={tv.hash[:8]} pipeline={PIPELINE_VERSION}")
    if skipped_type:
        print(f"  (skipped {skipped_type} source_documents with non-scored report_type)")
    if skipped_review:
        print(f"  (skipped {skipped_review} source_documents still in needs_review)")
    if summary.skipped_idempotent:
        print(f"  (skipped {summary.skipped_idempotent} already up-to-date)")

    # Open a Run row so this batch is traceable later. finished_at
    # populated after the loop; the row survives even if the batch crashes.
    run = Run(
        kind="process", git_commit=git_commit(),
        taxonomy_version=tv.hash, pipeline_version=PIPELINE_VERSION,
        config_hash=config_hash(), manifest_hash=manifest_hash(),
        started_at=datetime.now(UTC),
    )
    db.add(run)
    db.commit()

    t_wall = time.monotonic()
    timings: list[float] = []

    def _handle(result: WorkerResult, idx: int) -> None:
        iid, fy_, _path, slug = sd_meta[result.source_document_id]
        _progress(idx, len(to_run), result, slug, fy_)
        timings.append(result.total_seconds or 0.0)
        try:
            persist_worker_result(
                db, worker_result=result,
                institution_id=iid, fiscal_year=fy_, taxonomy_version=tv,
            )
        except Exception as exc:
            # Persistence errors shouldn't take the whole batch down.
            log.error("persist failed for sd_id=%s: %s", result.source_document_id, exc)
            summary.errors += 1
            return
        if result.status == "scored":
            summary.scored += 1
        elif result.status == "needs_review":
            summary.needs_review += 1
        else:
            summary.errors += 1

    if worker_n == 1:
        # Simpler single-process path — easier debugging + accurate timings.
        for idx, sd in enumerate(to_run, start=1):
            try:
                res = _run_pipeline_cpu(
                    source_document_id=sd.id, file_path=sd.file_path,
                    terms_payload=payload, cfg=cfg,
                )
            except Exception as exc:
                res = WorkerResult(
                    source_document_id=sd.id, file_path=sd.file_path,
                    status="error", error_message=str(exc),
                )
            _handle(res, idx)
    else:
        with ProcessPoolExecutor(max_workers=worker_n) as pool:
            futures = {
                pool.submit(
                    _run_pipeline_cpu,
                    source_document_id=sd.id, file_path=sd.file_path,
                    terms_payload=payload, cfg=cfg,
                ): sd for sd in to_run
            }
            for idx, fut in enumerate(as_completed(futures), start=1):
                sd = futures[fut]
                try:
                    res = fut.result()
                except Exception as exc:
                    res = WorkerResult(
                        source_document_id=sd.id, file_path=sd.file_path,
                        status="error", error_message=str(exc),
                    )
                _handle(res, idx)

    summary.wall_clock_seconds = time.monotonic() - t_wall
    summary.timings_seconds = timings
    run.finished_at = datetime.now(UTC)
    run.note = (f"scored={summary.scored} needs_review={summary.needs_review} "
                f"errors={summary.errors}")
    db.commit()
    return summary


def print_summary(summary: BatchSummary) -> None:
    print()
    print("=== batch summary ===")
    print(f"candidates matching scope       : {summary.total_candidates}")
    print(f"skipped (non-scored report_type): {summary.skipped_type_filter}")
    print(f"skipped (needs_review source)   : {summary.skipped_source_review}")
    print(f"skipped (already up-to-date)    : {summary.skipped_idempotent}")
    print(f"scored                          : {summary.scored}")
    print(f"needs_review (heavily scanned)  : {summary.needs_review}")
    print(f"errors                          : {summary.errors}")
    if summary.timings_seconds:
        ts = sorted(summary.timings_seconds)
        n = len(ts)
        med = ts[n // 2]
        p95 = ts[max(0, int(n * 0.95) - 1)]
        print(f"wall clock                      : {summary.wall_clock_seconds:.1f}s")
        print(f"per-report seconds (min/med/p95/max): "
              f"{ts[0]:.1f} / {med:.1f} / {p95:.1f} / {ts[-1]:.1f}")


__all__ = ["BatchSummary", "print_summary", "run_batch"]


_ = SourceType  # keep import referenced; needed to force enum registration
