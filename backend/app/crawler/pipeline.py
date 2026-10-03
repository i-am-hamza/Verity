"""Per-institution crawl pipeline.

Order of attempt per institution:
    1. If ir_status == "verified", crawl ir_url (plus allowed_hosts) looking
       for all target_years. For each year still missing after that, continue to:
    2. If exchange_status == "verified", crawl exchange_company_url the same way,
       logged as source="exchange".
    3. Years still missing after both become `Gap` rows.

Both passes use the same fetcher (so blocked hosts stay blocked within a
run), the same validation rules, the same manifest, and the same crawl-log.

Playwright fallback: a page whose static HTML has zero candidate links
is re-fetched with render=True. Exchange pages hit this more often than
IR pages (confirmed for the Saudi Exchange during Session 3b probing).
"""
from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.crawler.config import (
    IR_SOURCES_PATH,
    MAX_CRAWL_DEPTH,
    MAX_PAGES_PER_SOURCE,
)
from app.crawler.fetch import Fetcher, FetchResult, resolve
from app.crawler.manifest import save_pdf
from app.crawler.parse import find_annual_report_links_rich
from app.crawler.validate import validate_pdf
from app.models.institution import Institution
from app.models.provenance import (
    CrawlLog,
    Gap,
    GapReason,
    ReportType,
    ReviewStatus,
    SourceDocument,
    SourceType,
)

log = logging.getLogger("verity.crawler.pipeline")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_ir_sources() -> dict[str, dict]:
    rows = json.loads(IR_SOURCES_PATH.read_text(encoding="utf-8"))
    return {r["slug"]: r for r in rows}


# ---------------------------------------------------------------------------
# Per-institution attempt
# ---------------------------------------------------------------------------
@dataclass
class AttemptOutcome:
    """One (institution, year, source) outcome."""
    slug: str
    fiscal_year: int
    source: str  # "crawler" | "exchange"
    result: str  # "downloaded" | "deduped" | "needs_review" | "year_mismatch" | "blocked" | "robots_disallowed" | "missing" | "error"
    url: str | None = None
    sha256: str | None = None
    file_path: str | None = None
    note: str | None = None


@dataclass
class InstitutionRun:
    slug: str
    run_id: str
    outcomes: list[AttemptOutcome] = field(default_factory=list)

    def result_by_year(self, year: int) -> AttemptOutcome | None:
        for o in self.outcomes:
            if o.fiscal_year == year and o.result in (
                "downloaded", "deduped", "needs_review",
            ):
                return o
        return None


class Pipeline:
    def __init__(self, db: Session, fetcher: Fetcher | None = None):
        self.db = db
        self.fetcher = fetcher or Fetcher()
        self.ir_sources = load_ir_sources()
        self.user_agent = self.fetcher.user_agent

    # ------------------------------------------------------------------ public
    def crawl_institution(
        self,
        slug: str,
        target_years: list[int],
        *,
        run_id: str,
        dry_run: bool = False,
    ) -> InstitutionRun:
        inst_row = self.db.query(Institution).filter(Institution.slug == slug).one_or_none()
        if inst_row is None:
            raise RuntimeError(f"institution {slug!r} not loaded in DB")

        source_info = self.ir_sources.get(slug)
        if source_info is None:
            raise RuntimeError(f"{slug} not in data/ir_sources.json")

        run = InstitutionRun(slug=slug, run_id=run_id)
        missing = set(target_years)

        # 1. IR source first.
        if source_info["ir_status"] == "verified" and source_info["ir_url"]:
            attempted = self._attempt_source(
                inst=inst_row,
                run=run,
                root_url=source_info["ir_url"],
                allowed_hosts=source_info.get("allowed_hosts") or [],
                source_type=SourceType.crawler,
                target_years=missing,
                dry_run=dry_run,
            )
            for year, outcome in attempted.items():
                if outcome.result in ("downloaded", "deduped", "needs_review"):
                    missing.discard(year)

        # 2. Exchange source for anything still missing.
        if missing and source_info["exchange_status"] == "verified" and source_info["exchange_company_url"]:
            attempted = self._attempt_source(
                inst=inst_row,
                run=run,
                root_url=source_info["exchange_company_url"],
                allowed_hosts=source_info.get("allowed_hosts") or [],
                source_type=SourceType.exchange,
                target_years=missing,
                dry_run=dry_run,
            )
            for year, outcome in attempted.items():
                if outcome.result in ("downloaded", "deduped", "needs_review"):
                    missing.discard(year)

        # 3. Everything still missing becomes a gap row.
        for year in sorted(missing):
            if dry_run:
                run.outcomes.append(AttemptOutcome(
                    slug=slug, fiscal_year=year, source="",
                    result="missing", note="(dry run — gap not persisted)",
                ))
                continue
            self._write_gap(inst_row, year, run)
            run.outcomes.append(AttemptOutcome(
                slug=slug, fiscal_year=year, source="",
                result="missing", note="all stages exhausted or unverified",
            ))

        # 5. Housekeeping: any Gap row that is now covered by a SourceDocument
        # for this institution should be deleted. This matters for reruns —
        # the first run wrote a gap for FY2021, the rerun with a better trigger
        # fills FY2021, and without this cleanup the stale "no PDF found" row
        # would still read as a live gap in the gap_report.
        if not dry_run:
            self._clear_gaps_now_covered(inst_row.id)

        return run

    def _fetch_pdf_candidates(
        self,
        *,
        inst: Institution,
        run: InstitutionRun,
        source_type: SourceType,
        cands: list,
        wanted: set[int],
        found_for_year: dict,
        pages_fetched: int,
        dry_run: bool,
        already_tried: set[str],
    ) -> int:
        """Fetch each PDF candidate once, update `wanted` / `found_for_year`
        in place, and return the updated `pages_fetched` count.

        `already_tried` is the set of URLs the caller has already fetched in
        a prior pass; those are skipped here. This lets a Playwright-based
        second pass fetch only NEW URLs rather than re-trying static ones.
        """
        pdf_candidates = [
            c for c in cands
            if c.is_pdf and c.kind in ("annual", "integrated") and c.url not in already_tried
        ]
        for c in pdf_candidates:
            if c.year is not None and c.year not in wanted:
                continue
            if c.year is None and not wanted:
                continue
            pdf = self.fetcher.get(c.url)
            pages_fetched += 1
            self._log(inst.id, run.run_id, c.url, "fetch_pdf", pdf.outcome,
                      source=source_type)
            if pdf.outcome != "ok":
                continue
            outcome = self._process_pdf(
                inst=inst, run=run, source_type=source_type,
                url=c.url, fetched=pdf, suspected_year=c.year,
                dry_run=dry_run,
            )
            if outcome and outcome.result in ("downloaded", "deduped", "needs_review"):
                found_for_year[outcome.fiscal_year] = outcome
                wanted.discard(outcome.fiscal_year)
                if not wanted:
                    return pages_fetched
            if pages_fetched >= MAX_PAGES_PER_SOURCE:
                return pages_fetched
        return pages_fetched

    def _clear_gaps_now_covered(self, institution_id: int) -> None:
        """Delete Gap rows for (institution_id, fiscal_year) pairs that now
        have a SourceDocument. Called at the end of each institution's crawl.
        """
        covered_years = {
            d.fiscal_year for d in
            self.db.query(SourceDocument)
            .filter(SourceDocument.institution_id == institution_id).all()
        }
        if not covered_years:
            return
        stale = (
            self.db.query(Gap)
            .filter(Gap.institution_id == institution_id,
                    Gap.fiscal_year.in_(covered_years))
            .all()
        )
        for g in stale:
            self.db.delete(g)
        if stale:
            self.db.commit()
            log.info("cleared %d stale gap row(s) for institution_id=%d",
                     len(stale), institution_id)

    # ---------------------------------------------------------- source attempt
    def _attempt_source(
        self,
        *,
        inst: Institution,
        run: InstitutionRun,
        root_url: str,
        allowed_hosts: list[str],
        source_type: SourceType,
        target_years: Iterable[int],
        dry_run: bool,
    ) -> dict[int, AttemptOutcome]:
        """Crawl one source (IR or exchange) up to the depth / page caps.

        Returns a dict year -> AttemptOutcome. Years not touched are not in
        the dict.
        """
        wanted = set(target_years)
        found_for_year: dict[int, AttemptOutcome] = {}

        root_host = urlparse(root_url).netloc
        allow_hosts = {root_host, *(h.lower() for h in allowed_hosts)}

        visited: set[str] = set()
        # Breadth-first with depth cap.
        frontier: list[tuple[str, int]] = [(root_url, 0)]
        pages_fetched = 0

        while frontier and pages_fetched < MAX_PAGES_PER_SOURCE and wanted:
            url, depth = frontier.pop(0)
            if url in visited:
                continue
            visited.add(url)

            host = urlparse(url).netloc
            if host != root_host and not any(
                host.endswith(a) or a.endswith(host) for a in allow_hosts
            ):
                self._log(inst.id, run.run_id, url, "skip", "off_domain",
                          source=source_type)
                continue

            # Fetch the page.
            fetched = self.fetcher.get(url)
            pages_fetched += 1
            self._log(inst.id, run.run_id, url, "fetch", fetched.outcome,
                      source=source_type)

            if fetched.outcome == "blocked":
                # Record one blocked gap per year still wanted.
                for y in sorted(wanted):
                    out = AttemptOutcome(
                        slug=inst.slug, fiscal_year=y,
                        source=source_type.value, result="blocked",
                        url=url, note=fetched.detail or "blocked",
                    )
                    run.outcomes.append(out)
                    if not dry_run:
                        self._write_gap(inst, y, run, reason=GapReason.blocked,
                                        detail=f"{url}: {fetched.detail}")
                return found_for_year

            if fetched.outcome == "robots_disallowed":
                for y in sorted(wanted):
                    out = AttemptOutcome(
                        slug=inst.slug, fiscal_year=y,
                        source=source_type.value, result="robots_disallowed",
                        url=url, note="robots.txt",
                    )
                    run.outcomes.append(out)
                    if not dry_run:
                        self._write_gap(inst, y, run, reason=GapReason.robots_disallowed,
                                        detail=url)
                return found_for_year

            # Playwright fallback #1: root-level fetch failed with a non-block
            # error (SSL handshake, cert, timeout, connection refused). Many
            # MENA bank IR sites have TLS configurations Python's requests
            # library rejects but a real browser handles — e.g. alahli.com,
            # dubaiinvestments.com in the previous financial-wave run.
            # Only trigger on the ROOT URL (depth == 0): a per-link error
            # is just a bad link, not worth another browser launch.
            if (fetched.outcome == "error" and depth == 0
                    and not fetched.rendered):
                rendered = self.fetcher.get(url, render=True)
                self._log(inst.id, run.run_id, url, "render", rendered.outcome,
                          source=source_type)
                pages_fetched += 1
                if rendered.outcome == "ok":
                    fetched = rendered
                # else: Playwright also failed; fall through to the usual skip.

            if fetched.outcome != "ok":
                continue

            # If this is a PDF, hand off to the per-PDF path.
            ct = (fetched.content_type or "").lower()
            if ct.startswith("application/pdf") or (
                fetched.body[:4] == b"%PDF" and "pdf" in url.lower()
            ):
                outcome = self._process_pdf(
                    inst=inst, run=run, source_type=source_type,
                    url=url, fetched=fetched, suspected_year=None,
                    dry_run=dry_run,
                )
                if outcome and outcome.result in ("downloaded", "deduped", "needs_review"):
                    found_for_year[outcome.fiscal_year] = outcome
                    wanted.discard(outcome.fiscal_year)
                continue

            # HTML page: parse for candidate links.
            soup = BeautifulSoup(fetched.body, "html.parser")
            cands = find_annual_report_links_rich(soup, fetched.final_url or url)

            # Pass 1: fetch PDF candidates from the STATIC HTML first — before
            # any Playwright render. Rationale: a render on sites with WAF
            # may trip bot-detection and block the whole host, which cascades
            # onto PDF URLs on that same host. Securing static-visible PDFs
            # first means a later host-block doesn't lose what was already
            # reachable. (bank-muscat regressed in the previous corrected-
            # trigger run for exactly this reason.)
            pages_fetched = self._fetch_pdf_candidates(
                inst=inst, run=run, source_type=source_type, cands=cands,
                wanted=wanted, found_for_year=found_for_year,
                pages_fetched=pages_fetched, dry_run=dry_run,
                already_tried=set(),
            )
            if not wanted or pages_fetched >= MAX_PAGES_PER_SOURCE:
                return found_for_year

            # Pass 2: if any target years are still uncovered, trigger a
            # Playwright render to see below-the-fold / JS-populated PDF
            # links. Per-target-year coverage (not "any PDF found") is what
            # catches Al Rajhi's below-fold 2021/22/23 PDFs when the top of
            # the IR page already surfaced 2024/25.
            covered_years = {
                c.year for c in cands
                if c.is_pdf and c.kind in ("annual", "integrated") and c.year is not None
            }
            uncovered_wanted = wanted - covered_years
            if uncovered_wanted and not fetched.rendered:
                already_tried_urls = {c.url for c in cands if c.is_pdf}
                rendered = self.fetcher.get(url, render=True)
                self._log(inst.id, run.run_id, url, "render", rendered.outcome,
                          source=source_type)
                pages_fetched += 1
                if rendered.outcome == "ok":
                    rendered_cands = find_annual_report_links_rich(
                        BeautifulSoup(rendered.body, "html.parser"),
                        rendered.final_url or url,
                    )
                    cands = rendered_cands  # for the subpage-enqueue step below
                    pages_fetched = self._fetch_pdf_candidates(
                        inst=inst, run=run, source_type=source_type,
                        cands=rendered_cands, wanted=wanted,
                        found_for_year=found_for_year,
                        pages_fetched=pages_fetched, dry_run=dry_run,
                        already_tried=already_tried_urls,
                    )
                    if not wanted or pages_fetched >= MAX_PAGES_PER_SOURCE:
                        return found_for_year

            # Depth-limited enqueue of non-PDF annual-report-ish subpages.
            if depth < MAX_CRAWL_DEPTH:
                for c in cands:
                    if c.is_pdf:
                        continue
                    if c.kind not in ("annual", "integrated"):
                        continue
                    sub = resolve(fetched.final_url or url, c.url)
                    sub_host = urlparse(sub).netloc
                    if sub_host != root_host and not any(
                        sub_host.endswith(a) or a.endswith(sub_host) for a in allow_hosts
                    ):
                        continue
                    if sub not in visited:
                        frontier.append((sub, depth + 1))

        return found_for_year

    # ----------------------------------------------------------- PDF handling
    def _process_pdf(
        self,
        *,
        inst: Institution,
        run: InstitutionRun,
        source_type: SourceType,
        url: str,
        fetched: FetchResult,
        suspected_year: int | None,
        dry_run: bool,
    ) -> AttemptOutcome | None:
        source_filename = url.rsplit("/", 1)[-1]
        validation = validate_pdf(fetched.body,
                                  source_filename=source_filename,
                                  expected_year=suspected_year)

        year = suspected_year or validation.inferred_year
        if not year:
            # No year to attach it to → log and move on; not persisted.
            self._log(inst.id, run.run_id, url, "unattributed_pdf",
                      "needs_year", source=source_type)
            return None

        if not validation.ok:
            out = AttemptOutcome(
                slug=inst.slug, fiscal_year=year, source=source_type.value,
                result="error", url=url, sha256=validation.sha256,
                note=validation.reason,
            )
            run.outcomes.append(out)
            return out

        # Year mismatch: keep the file (if we still can), flag needs_review,
        # and write a gap row for traceability.
        year_mismatch = (suspected_year is not None and validation.inferred_year is not None
                        and suspected_year != validation.inferred_year)

        # If existing sha256, dedupe.
        existing = (
            self.db.query(SourceDocument)
            .filter(SourceDocument.sha256 == validation.sha256)
            .one_or_none()
        )
        is_dedupe = existing is not None

        if dry_run:
            out = AttemptOutcome(
                slug=inst.slug, fiscal_year=year, source=source_type.value,
                result="downloaded" if validation.review_status == "auto_ok" else "needs_review",
                url=url, sha256=validation.sha256,
                note="(dry run — not persisted)",
            )
            run.outcomes.append(out)
            return out

        # Save file (dedupe-aware).
        manifest_row = {
            "source": source_type.value,
            "institution_slug": inst.slug,
            "fiscal_year": year,
            "source_url": url,
            "final_url": fetched.final_url,
            "http_status": fetched.status,
            "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "bytes": validation.byte_count,
            "content_type": fetched.content_type,
            "report_type": validation.report_type,
            "page_count": validation.page_count,
            "includes_financial_statements": validation.includes_financial_statements,
            "review_status": validation.review_status,
            "run_id": run.run_id,
        }

        if is_dedupe:
            assert existing is not None  # narrowed by is_dedupe
            path = existing.file_path
            # Still log the attempt in crawl_log so the alt-source "we also
            # found this file via X" is visible later.
            self._log(inst.id, run.run_id, url, "dedupe",
                      f"existing sha256 {validation.sha256[:8]}", source=source_type)
        else:
            dest, _created = save_pdf(
                slug=inst.slug, fiscal_year=year,
                report_type=validation.report_type, sha256=validation.sha256,
                body=fetched.body, manifest_row=manifest_row,
            )
            path = str(dest)

            # Insert new source_documents row.
            review = ReviewStatus(validation.review_status)
            if year_mismatch:
                review = ReviewStatus.needs_review
            try:
                rt = ReportType(validation.report_type)
            except ValueError:
                rt = ReportType.unknown
            doc = SourceDocument(
                institution_id=inst.id,
                fiscal_year=year,
                report_type=rt,
                source=source_type,
                source_url=url,
                final_url=fetched.final_url,
                http_status=fetched.status,
                retrieved_at=datetime.now(UTC),
                sha256=validation.sha256,
                bytes=validation.byte_count,
                content_type=fetched.content_type,
                page_count=validation.page_count,
                includes_financial_statements=validation.includes_financial_statements,
                file_path=path,
                review_status=review,
                review_note=(validation.reason or "") +
                           (f" | expected FY{suspected_year}, PDF says FY{validation.inferred_year}"
                            if year_mismatch else ""),
            )
            self.db.add(doc)
            self.db.commit()

        if year_mismatch:
            assert suspected_year is not None  # narrowed by year_mismatch guard
            self._write_gap(inst, suspected_year, run,
                            reason=GapReason.year_mismatch,
                            detail=f"link said FY{suspected_year}, PDF reads FY{validation.inferred_year}; file kept at {path}")

        if is_dedupe:
            result_label = "deduped"
        elif validation.review_status == "needs_review" or year_mismatch:
            result_label = "needs_review"
        else:
            result_label = "downloaded"

        out = AttemptOutcome(
            slug=inst.slug, fiscal_year=year, source=source_type.value,
            result=result_label, url=url, sha256=validation.sha256, file_path=path,
            note=validation.reason or ("deduped against earlier sha256" if is_dedupe else None),
        )
        run.outcomes.append(out)
        return out

    # -------------------------------------------------------- bookkeeping ops
    def _log(self, institution_id: int, run_id: str, url: str, action: str,
             outcome: str, *, source: SourceType) -> None:
        self.db.add(CrawlLog(
            run_id=run_id,
            institution_id=institution_id,
            url=url,
            action=f"{source.value}:{action}",
            outcome=outcome,
        ))
        self.db.commit()

    def _write_gap(
        self,
        inst: Institution,
        year: int,
        run: InstitutionRun,
        *,
        reason: GapReason = GapReason.not_found,
        detail: str | None = None,
    ) -> None:
        # Upsert on (institution_id, fiscal_year).
        existing = (
            self.db.query(Gap)
            .filter(Gap.institution_id == inst.id, Gap.fiscal_year == year)
            .one_or_none()
        )
        next_action = "Tier 3 Wayback Machine" if reason != GapReason.robots_disallowed else "Tier 4 email (robots.txt disallows automated fetch)"
        fields = {
            "institution_id": inst.id,
            "fiscal_year": year,
            "reason": reason,
            "detail": detail or f"run {run.run_id}: no verified source produced FY{year}",
            "tier_tried": "live",
            "next_action": next_action,
        }
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
        else:
            self.db.add(Gap(**fields))
        self.db.commit()


# ---------------------------------------------------------------------------
# High-level entry point used by the CLI
# ---------------------------------------------------------------------------
def new_run_id() -> str:
    return uuid.uuid4().hex[:12]
