"""Verity command-line entry point.

Usage:
    python -m app.cli crawl --wave financial|other|all \
                            --years 2021 2022 2023 2024 2025 \
                            [--only slug ...] [--dry-run]
    python -m app.cli gaps wayback
    python -m app.cli gaps email-drafts
    python -m app.cli ingest-approved
    python -m app.cli ingest-manual

All subcommands require VERITY_CONTACT_EMAIL to be set (CLAUDE.md
rule 5). The crawl subcommand gates between waves: it stops after the
financial wave completes so the human can review before 'other' runs.
"""
from __future__ import annotations

import argparse
import contextlib
import logging
import sys

from app.crawler.config import make_user_agent


def _force_utf8_stdout() -> None:
    """Windows cp1252 can't encode arrows / em-dash / warning glyphs the
    crawler prints. Reconfigure at process start so every print survives.
    Falls back silently on terminals / IO objects without reconfigure()."""
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if callable(reconf):
            with contextlib.suppress(Exception):
                reconf(encoding="utf-8")


def _setup_logging(verbose: bool) -> None:
    _force_utf8_stdout()
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # Reduce noise from third-party libs.
    for noisy in ("urllib3", "requests", "playwright", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def _print_run_table(outcomes: list, years: list[int]) -> None:
    """Pretty print per-institution run table to stdout."""
    # Reconfigure stdout to UTF-8 so Arabic/em-dash/warning glyphs survive
    # Windows cp1252. getattr-fallback is for terminals / test IO that
    # don't expose reconfigure.
    reconf = getattr(sys.stdout, "reconfigure", None)
    if callable(reconf):
        reconf(encoding="utf-8")
    by_inst: dict[str, dict[int, str]] = {}
    for o in outcomes:
        row = by_inst.setdefault(o.slug, {})
        label = o.result
        if o.result in ("downloaded", "deduped", "needs_review"):
            label = f"{o.result}[{o.source or '?'}]"
        row[o.fiscal_year] = label

    print()
    header = "institution".ljust(50) + "".join(f" | FY{y}".ljust(22) for y in years)
    print(header)
    print("-" * len(header))
    for slug, cells in sorted(by_inst.items()):
        line = slug.ljust(50)
        for y in years:
            label = cells.get(y, "—")
            line += f" | {label[:20]:<20}"
        print(line)
    print()


def _cmd_crawl(args: argparse.Namespace) -> int:
    # Confirm the UA is well-formed before touching the DB or the network.
    try:
        _ua = make_user_agent()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"User-Agent: {_ua}")

    from app.crawler import register_all_mappers
    from app.crawler.gap_report import write_gap_report
    from app.crawler.pipeline import Pipeline, new_run_id
    from app.database import SessionLocal
    register_all_mappers()
    from app.models.institution import Institution, Wave

    years = args.years
    waves = {
        "financial": [Wave.financial],
        "other": [Wave.other],
        "all": [Wave.financial, Wave.other],
    }[args.wave]

    db = SessionLocal()
    try:
        q = db.query(Institution).filter(Institution.wave.in_(waves)).order_by(
            Institution.wave.desc(), Institution.rank.asc()
        )
        if args.only:
            q = q.filter(Institution.slug.in_(args.only))
        institutions = q.all()
        if not institutions:
            print("No institutions match the filter.", file=sys.stderr)
            return 1

        print(f"Crawling {len(institutions)} institution(s): "
              + ", ".join(i.slug for i in institutions))

        pipe = Pipeline(db)
        run_id = new_run_id()
        print(f"run_id: {run_id}  dry_run={args.dry_run}")
        all_outcomes: list = []
        for inst in institutions:
            print(f"\n→ {inst.slug}")
            try:
                run = pipe.crawl_institution(
                    inst.slug, years, run_id=run_id, dry_run=args.dry_run,
                )
            except Exception as exc:
                print(f"  ERROR crawling {inst.slug}: {exc}")
                continue
            for o in run.outcomes:
                src = f"[{o.source}]" if o.source else ""
                print(f"  FY{o.fiscal_year} {o.result} {src} {o.url or ''}  {o.note or ''}")
            all_outcomes.extend(run.outcomes)

        _print_run_table(all_outcomes, years)

        if not args.dry_run:
            only_slugs = args.only or None
            report_path = write_gap_report(db, target_years=years, only_slugs=only_slugs)
            print(f"Gap report: {report_path}")

        print(
            "\nSTOP. Review the outcomes before launching the next wave.\n"
            "The crawler does NOT auto-advance between waves (financial → other) — "
            "you re-invoke it manually, which keeps review-and-authorise explicit."
        )
    finally:
        db.close()
    return 0


def _cmd_gaps_wayback(args: argparse.Namespace) -> int:
    try:
        _ua = make_user_agent()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    from app.crawler import register_all_mappers
    from app.crawler.wayback import run_wayback
    from app.database import SessionLocal
    register_all_mappers()

    db = SessionLocal()
    try:
        path = run_wayback(db)
    finally:
        db.close()
    print(f"Wrote: {path}")
    print("REMINDER: nothing was downloaded. Copy approved rows into "
          "data/approved_downloads.json and run `python -m app.cli ingest-approved`.")
    return 0


def _cmd_gaps_email_drafts(args: argparse.Namespace) -> int:
    from app.crawler import register_all_mappers
    from app.crawler.email_drafts import write_email_drafts
    from app.database import SessionLocal
    register_all_mappers()

    db = SessionLocal()
    try:
        paths = write_email_drafts(db)
    finally:
        db.close()
    print(f"Wrote {len(paths)} draft(s). Nothing is sent — review manually and send yourself.")
    for p in paths:
        print(f"  {p}")
    return 0


def _cmd_ingest_approved(args: argparse.Namespace) -> int:
    try:
        _ua = make_user_agent()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    from app.crawler import register_all_mappers
    from app.crawler.ingest import ingest_approved
    from app.database import SessionLocal
    register_all_mappers()

    db = SessionLocal()
    try:
        results = ingest_approved(db)
    finally:
        db.close()
    for r in results:
        print(f"  {r}")
    return 0


def _cmd_process(args: argparse.Namespace) -> int:
    from app.crawler import register_all_mappers
    from app.database import SessionLocal
    from app.services.batch_runner import print_summary, run_batch
    register_all_mappers()

    db = SessionLocal()
    try:
        summary = run_batch(
            db, scope=args.scope, only=args.only or [],
            fy=args.fy, force=args.force,
            worker_count_override=args.workers,
        )
    finally:
        db.close()
    print_summary(summary)
    return 0 if summary.errors == 0 else 1


def _cmd_reproduce(args: argparse.Namespace) -> int:
    """Session 7 reproducibility check. Picks `--sample N` already-scored
    reports (default 3) under the current taxonomy/pipeline, re-runs the
    CPU-side of the pipeline against the stored PDF, and asserts that the
    recomputed match counts per (term, page) are byte-identical to what's
    stored in MatchEvidence. Exit code non-zero on any mismatch."""
    import random
    from collections import Counter
    from datetime import UTC, datetime

    from app.crawler import register_all_mappers
    from app.database import SessionLocal
    from app.models.institution import Institution
    from app.models.report import Report
    from app.models.run import Run
    from app.models.score import MatchEvidence
    from app.models.taxonomy import Category, Term
    from app.services.pipeline import (
        PIPELINE_VERSION,
        _current_taxonomy_version,
        _run_pipeline_cpu,
        build_terms_payload,
    )
    from app.services.reproducibility import config_hash, git_commit, manifest_hash
    from app.services.verity_config import load_verity_config
    register_all_mappers()

    db = SessionLocal()
    sample = max(1, args.sample)
    try:
        tv = _current_taxonomy_version(db)
        terms = db.query(Term).all()
        cats = db.query(Category).all()
        payload = build_terms_payload(terms, cats)
        cfg = load_verity_config()

        scored = (
            db.query(Report, Institution)
            .join(Institution, Institution.id == Report.institution_id)
            .filter(
                Report.taxonomy_version == tv.hash,
                Report.pipeline_version == PIPELINE_VERSION,
                Report.status == "scored",
            )
            .all()
        )
        if len(scored) < sample:
            print(f"only {len(scored)} scored reports available under the current "
                  f"taxonomy/pipeline — asked for {sample}")
            return 2
        rng = random.Random(42)
        picks = rng.sample(scored, sample)

        run = Run(
            kind="reproduce", git_commit=git_commit(),
            taxonomy_version=tv.hash, pipeline_version=PIPELINE_VERSION,
            config_hash=config_hash(), manifest_hash=manifest_hash(),
            started_at=datetime.now(UTC),
            note=f"sample={sample}",
        )
        db.add(run)
        db.commit()
        print(f"reproduce run_id={run.id}  taxonomy={tv.hash[:12]}  "
              f"pipeline={PIPELINE_VERSION}  git={run.git_commit[:12]}")
        print(f"config_hash={run.config_hash[:12]}  manifest_hash={run.manifest_hash[:12]}")
        print()

        mismatches = 0
        for rpt, inst in picks:
            stored = Counter(
                (me.term_id, me.page_number)
                for me in db.query(MatchEvidence)
                .filter(MatchEvidence.report_id == rpt.id,
                        MatchEvidence.taxonomy_version_id == tv.id)
                .all()
            )
            wr = _run_pipeline_cpu(
                source_document_id=rpt.source_document_id or 0,
                file_path=rpt.file_path, terms_payload=payload, cfg=cfg,
            )
            recomputed = Counter((m.term_id, m.page_number) for m in wr.matches)

            ok = stored == recomputed
            print(f"{'OK ' if ok else 'FAIL'}  {inst.slug} FY{rpt.fiscal_year} "
                  f"stored={sum(stored.values())}  recomputed={sum(recomputed.values())}")
            if not ok:
                mismatches += 1
                only_stored = stored - recomputed
                only_recomp = recomputed - stored
                for k, n in list(only_stored.items())[:5]:
                    print(f"      stored-only  (term_id={k[0]} page={k[1]}) x{n}")
                for k, n in list(only_recomp.items())[:5]:
                    print(f"      recomp-only  (term_id={k[0]} page={k[1]}) x{n}")

        run.finished_at = datetime.now(UTC)
        run.kind = "reproduce-ok" if mismatches == 0 else "reproduce-mismatch"
        run.note = f"{run.note} mismatches={mismatches}"
        db.commit()

        print()
        if mismatches == 0:
            print(f"reproducibility OK: {sample}/{sample} reports identical")
            return 0
        print(f"FAIL: {mismatches}/{sample} reports differ from stored output")
        return 1
    finally:
        db.close()


def _cmd_write_qa(args: argparse.Namespace) -> int:
    from app.crawler import register_all_mappers
    from app.database import SessionLocal
    from app.services.qa_report import write_processing_qa
    register_all_mappers()

    db = SessionLocal()
    try:
        path = write_processing_qa(db)
    finally:
        db.close()
    print(f"wrote {path}")
    return 0


def _cmd_export_evidence_sample(args: argparse.Namespace) -> int:
    from app.crawler import register_all_mappers
    from app.database import SessionLocal
    from app.services.evidence_sample import export_evidence_sample
    register_all_mappers()

    db = SessionLocal()
    try:
        result = export_evidence_sample(db)
    finally:
        db.close()
    print(f"wrote {result.path}")
    for pillar, avail in sorted(result.per_pillar_available.items()):
        sampled = result.per_pillar_sampled.get(pillar, 0)
        if sampled < avail:
            print(f"  {pillar}: sampled {sampled} of {avail} available")
        else:
            print(f"  {pillar}: exported all {avail} match(es) (fewer than target)")
    return 0


def _cmd_ingest_manual(args: argparse.Namespace) -> int:
    from app.crawler import register_all_mappers
    from app.crawler.ingest import ingest_manual
    from app.database import SessionLocal
    register_all_mappers()

    db = SessionLocal()
    try:
        results = ingest_manual(db)
    finally:
        db.close()
    for r in results:
        print(f"  {r}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verity")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_crawl = sub.add_parser("crawl", help="run the live crawler")
    p_crawl.add_argument("--wave", choices=("financial", "other", "all"), required=True)
    p_crawl.add_argument("--years", type=int, nargs="+", required=True)
    p_crawl.add_argument("--only", nargs="+", default=[],
                         help="restrict to specific slug(s)")
    p_crawl.add_argument("--dry-run", action="store_true",
                         help="plan the crawl without persisting rows or files")
    p_crawl.set_defaults(func=_cmd_crawl)

    p_gaps = sub.add_parser("gaps", help="Tier 3/4 helpers")
    gaps_sub = p_gaps.add_subparsers(dest="gaps_cmd", required=True)
    p_wayback = gaps_sub.add_parser("wayback", help="list Wayback captures (no download)")
    p_wayback.set_defaults(func=_cmd_gaps_wayback)
    p_email = gaps_sub.add_parser("email-drafts", help="write per-institution email drafts")
    p_email.set_defaults(func=_cmd_gaps_email_drafts)

    p_ing_a = sub.add_parser("ingest-approved",
                             help="download URLs from data/approved_downloads.json")
    p_ing_a.set_defaults(func=_cmd_ingest_approved)

    p_ing_m = sub.add_parser("ingest-manual",
                             help="ingest PDFs from storage/manual_inbox/<slug>/")
    p_ing_m.set_defaults(func=_cmd_ingest_manual)

    p_proc = sub.add_parser("process",
                            help="run the scoring pipeline over auto_ok source_documents")
    p_proc.add_argument("--scope", choices=("financial", "other", "all"), required=True)
    p_proc.add_argument("--only", nargs="+", default=[],
                        help="restrict to specific slug(s)")
    p_proc.add_argument("--fy", type=int, default=None,
                        help="restrict to a single fiscal year")
    p_proc.add_argument("--force", action="store_true",
                        help="reprocess even if a Report already exists under current"
                             " (taxonomy_version, pipeline_version) — appends new rows")
    p_proc.add_argument("--workers", type=int, default=None,
                        help="override worker count (default from config, auto = cpu-1)")
    p_proc.set_defaults(func=_cmd_process)

    p_qa = sub.add_parser("write-qa", help="write docs/PROCESSING_QA.md")
    p_qa.set_defaults(func=_cmd_write_qa)

    p_repro = sub.add_parser(
        "reproduce",
        help="re-score N random already-scored reports and assert identical output",
    )
    p_repro.add_argument("--sample", type=int, default=3)
    p_repro.set_defaults(func=_cmd_reproduce)

    p_evi = sub.add_parser("export-evidence-sample",
                           help="write exports/evidence_sample.csv (seeded random sample)")
    p_evi.set_defaults(func=_cmd_export_evidence_sample)

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
