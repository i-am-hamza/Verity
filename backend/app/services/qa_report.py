"""Writes docs/PROCESSING_QA.md: one row per processed Report plus
IQR-based outlier flags per fiscal-year cohort.

Also updates Report.processing_review_status for any report that scores
as an outlier, so a downstream reader can filter them out without
re-reading this markdown file. Outlier is a review signal, not a score
correction — the composite in the Report row stays as-is.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from statistics import median

from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.models.report import Report
from app.services.verity_config import load_verity_config


def _quartiles(xs: list[float]) -> tuple[float, float, float]:
    """Return (q1, median, q3) using the "exclusive" rule. For small
    samples returns best-effort values. Caller must guard against empty.
    """
    s = sorted(xs)
    n = len(s)
    lo = s[: n // 2]
    hi = s[(n + 1) // 2:]
    q1 = median(lo) if lo else s[0]
    q2 = median(s)
    q3 = median(hi) if hi else s[-1]
    return q1, q2, q3


def write_processing_qa(db: Session, out_path: Path | None = None) -> Path:
    cfg = load_verity_config()
    out = out_path or (Path(__file__).resolve().parents[3] / "docs" / "PROCESSING_QA.md")

    reports = (
        db.query(Report)
        .join(Institution, Institution.id == Report.institution_id)
        .order_by(Institution.slug, Report.fiscal_year)
        .all()
    )
    if not reports:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("# Processing QA\n\n_(no reports yet)_\n", encoding="utf-8")
        return out

    # Threshold flags: independent of cohort, per CLAUDE.md / spec.
    # Each returns a reason string or None.
    def _threshold_reason(r: Report) -> str | None:
        reasons: list[str] = []
        if r.latin_word_count < cfg.low_latin_word_count_threshold:
            reasons.append(
                f"very low Latin word count ({r.latin_word_count} "
                f"< {cfg.low_latin_word_count_threshold})"
            )
        if r.ocr_page_ratio is not None and r.ocr_page_ratio > cfg.high_ocr_ratio_threshold:
            reasons.append(
                f"high OCR ratio ({r.ocr_page_ratio:.0%} "
                f"> {cfg.high_ocr_ratio_threshold:.0%})"
            )
        ar_frac = r.pages_mostly_arabic / r.page_count if r.page_count else 0.0
        if ar_frac > cfg.high_arabic_ratio_threshold:
            reasons.append(
                f"high Arabic ratio ({ar_frac:.0%} of pages > "
                f"{cfg.high_arabic_ratio_threshold:.0%})"
            )
        return "; ".join(reasons) if reasons else None

    threshold_flagged: dict[int, str] = {}
    for r in reports:
        reason = _threshold_reason(r)
        if reason:
            threshold_flagged[r.id] = reason

    # Group by fiscal year for IQR cohort.
    cohorts: dict[int, list[Report]] = {}
    for r in reports:
        cohorts.setdefault(r.fiscal_year, []).append(r)

    flagged: list[tuple[int, str]] = []  # (report_id, reason)
    bounds: dict[int, tuple[float, float, bool]] = {}  # fy -> (lo, hi, low_conf)
    for fy, cohort in cohorts.items():
        scored_vals = [r.composite_score for r in cohort
                       if r.composite_score is not None]
        if len(scored_vals) < 2:
            bounds[fy] = (float("-inf"), float("inf"), True)
            continue
        q1, _med, q3 = _quartiles(scored_vals)
        iqr = q3 - q1
        lo = q1 - cfg.iqr_multiplier * iqr
        hi = q3 + cfg.iqr_multiplier * iqr
        low_conf = len(scored_vals) < cfg.iqr_min_cohort
        bounds[fy] = (lo, hi, low_conf)
        for r in cohort:
            if r.composite_score is None:
                continue
            if r.composite_score < lo or r.composite_score > hi:
                tag = " (low-confidence — cohort < min)" if low_conf else ""
                flagged.append((r.id, f"composite {r.composite_score:.3f} outside "
                                     f"[{lo:.3f}, {hi:.3f}] for FY{fy}{tag}"))

    # Persist flags on the report rows. Threshold flags and IQR flags both
    # set processing_review_status = needs_review; the reason string is
    # whichever applies (threshold wins if both — more actionable).
    changed = 0
    flag_map = dict(flagged)
    for r in reports:
        if r.processing_review_status != "auto_ok":
            continue
        reason = threshold_flagged.get(r.id) or flag_map.get(r.id)
        if reason:
            r.processing_review_status = "needs_review"
            r.processing_review_reason = reason
            changed += 1
    if changed:
        db.commit()

    # ---- write markdown ---------------------------------------------------
    lines: list[str] = []
    lines.append("# Processing QA")
    lines.append("")
    lines.append(f"Generated {datetime.now(UTC).isoformat(timespec='seconds')}.")
    lines.append("")
    threshold_flag_count = len(threshold_flagged)
    lines.append(
        f"Reports processed: **{len(reports)}** "
        f"(threshold-flagged: **{threshold_flag_count}**, "
        f"IQR-flagged: **{len(flagged)}**)."
    )
    lines.append("")
    lines.append("IQR cohort = fiscal year. A composite more than "
                 f"{cfg.iqr_multiplier:g}xIQR from Q1/Q3 of its cohort is flagged "
                 f"as a processing outlier (Report.processing_review_status "
                 f"= needs_review). Cohorts with fewer than {cfg.iqr_min_cohort} "
                 "scored reports are labelled low-confidence.")
    lines.append("")

    # Cohort bounds table
    lines.append("## Cohort IQR bounds")
    lines.append("")
    lines.append("| FY | n | median | Q1 | Q3 | lower | upper | note |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for fy in sorted(cohorts.keys()):
        xs = [r.composite_score for r in cohorts[fy] if r.composite_score is not None]
        if not xs:
            lines.append(f"| {fy} | 0 | — | — | — | — | — | no scored reports |")
            continue
        q1, med, q3 = _quartiles(xs) if len(xs) >= 2 else (xs[0], xs[0], xs[0])
        lo, hi, low_conf = bounds[fy]
        note = "low-confidence (small cohort)" if low_conf else ""
        lines.append(
            f"| {fy} | {len(xs)} | {med:.3f} | {q1:.3f} | {q3:.3f} | "
            f"{(lo if lo != float('-inf') else 0):.3f} | "
            f"{(hi if hi != float('inf') else 0):.3f} | {note} |"
        )
    lines.append("")

    # Per-report table
    lines.append("## Per-report audit")
    lines.append("")
    lines.append("| slug | FY | status | pages | Latin words | OCR frac | Ar pages | "
                 "ToC pages | repeat lines | FS start | matches | all-mode extra "
                 "| composite | flag |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")

    for r in reports:
        slug = r.institution.slug if r.institution else "?"
        toc = ",".join(str(x) for x in (r.excluded_contents_pages or [])) or "—"
        fs = str(r.financial_statements_start_page) if r.financial_statements_start_page else "—"
        comp = f"{r.composite_score:.3f}" if r.composite_score is not None else "—"
        ocrf = f"{r.ocr_page_ratio:.2f}" if r.ocr_page_ratio is not None else "—"
        amx = str(r.all_mode_extra_matches) if r.all_mode_extra_matches is not None else "—"
        flags: list[str] = []
        if r.id in threshold_flagged:
            flags.append("threshold")
        if r.id in flag_map:
            flags.append("IQR-outlier")
        if not flags and r.processing_review_status == "needs_review":
            flags.append("needs_review")
        flag = ",".join(flags)
        lines.append(
            f"| `{slug}` | {r.fiscal_year} | {r.status.value} | {r.page_count} | "
            f"{r.latin_word_count} | {ocrf} | {r.pages_mostly_arabic} | {toc} | "
            f"{r.repeated_lines_removed} | {fs} | {r.matches_count} | {amx} | "
            f"{comp} | {flag} |"
        )

    lines.append("")
    reports_by_id = {rr.id: rr for rr in reports}
    lines.append("## Threshold flags")
    lines.append("")
    if not threshold_flagged:
        lines.append("_(none)_")
    else:
        for rid, reason in sorted(threshold_flagged.items()):
            rr = reports_by_id.get(rid)
            if rr is not None:
                lines.append(f"- `{rr.institution.slug}` FY{rr.fiscal_year}: {reason}")

    lines.append("")
    lines.append("## IQR outliers")
    lines.append("")
    if not flagged:
        lines.append("_(none)_")
    else:
        for report_id, reason in flagged:
            rr = reports_by_id.get(report_id)
            if rr is not None:
                lines.append(f"- `{rr.institution.slug}` FY{rr.fiscal_year}: {reason}")

    # Also surface processing_review_reasons that came from the pipeline
    # (heavily scanned, FS detector miss, etc.) — distinct from IQR outliers.
    non_iqr_reviews = [r for r in reports
                       if r.processing_review_status == "needs_review"
                       and r.id not in flag_map]
    if non_iqr_reviews:
        lines.append("")
        lines.append("## Pipeline-flagged needs_review (non-IQR)")
        lines.append("")
        for r in non_iqr_reviews:
            lines.append(f"- `{r.institution.slug}` FY{r.fiscal_year}: "
                         f"{r.processing_review_reason}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


__all__ = ["write_processing_qa"]
