"""Generate docs/IR_REVIEW.md from data/ir_sources.json."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IR_SOURCES = REPO_ROOT / "data" / "ir_sources.json"
OUT = REPO_ROOT / "docs" / "IR_REVIEW.md"
ALAFCO_SLUG = "alafco-aviation-lease-and-finance-company"


def main() -> None:
    from app.database import SessionLocal
    from app.models import (  # noqa: F401 — register mappers
        institution as _i,
        provenance as _p,
        report as _r,
        score as _s,
        taxonomy as _t,
    )
    from app.models.institution import Institution

    db = SessionLocal()
    try:
        meta = {
            r.slug: {"wave": r.wave.value, "country": r.country, "name": r.name, "rank": r.rank}
            for r in db.query(Institution).all()
        }
    finally:
        db.close()

    institutions = json.loads(IR_SOURCES.read_text(encoding="utf-8"))

    lines: list[str] = []
    lines.append("# IR + exchange source review")
    lines.append("")
    lines.append("Current state: **Session 3b** (2026-10-01). Session 3 did WebFetch-based discovery; "
                 "Session 3b retried everything blocked at that layer with Playwright (Chromium + the "
                 "VerityResearchBot UA from CLAUDE.md), closed the deferred non-financial exchange "
                 "work, and resolved ALAFCO's path.")
    lines.append("")
    lines.append("## Statuses")
    lines.append("")
    lines.append("- **verified** — the URL was fetched (Session 3 via WebFetch or Session 3b via "
                 "Playwright) and the page's content / title / preserved final URL confirmed it was the "
                 "intended IR or exchange-company page.")
    lines.append("- **unreachable** — the URL was fetched and the site returned a definitive block "
                 "(403 / 404 / 500 / 523) or redirected to a dead end. For exchange URLs this includes "
                 "Tadawul (saudiexchange.sa) and Boursa Kuwait `/stock/<id>/profile`, which both 403 "
                 "even to Playwright + the honest VerityResearchBot UA — Akamai-style bot detection "
                 "that trips on the UA string. Per CLAUDE.md rule 3 we stop for those domains and "
                 "move on; they go to Tier 3/4.")
    lines.append("- **needs_human** — no verified fetch, no definitive block. Three rows remain here "
                 "after Session 3b because no live URL has been identified at all (Jarir Marketing; "
                 "Tamdeen Real Estate; Oman International Development and Investment IR page).")
    lines.append("")
    lines.append("## What changed from Session 3")
    lines.append("")
    lines.append("- Tadawul (24 slugs) and Boursa Kuwait numeric-id profile URLs (6 slugs) now "
                 "`exchange_status = unreachable` with Playwright evidence, not `needs_human`.")
    lines.append("- ADX / DFM / QSE / MSX / Bahrain Bourse per-company URLs verified via Playwright "
                 "— 27 total `exchange_status = verified` rows (up from 10).")
    lines.append("- SNB (`alahli.com`) was Session-3-unreachable due to a cert error — Playwright "
                 "returned 200 with title \"Investor Relations | Saudi National Bank\". Session 3's "
                 "cert error was Claude-tool-specific.")
    lines.append("- 19 of the 24 deferred `needs_human` IR rows upgraded to `verified`; 6 downgraded "
                 "to `unreachable` (403/500 or redirect-to-homepage).")
    lines.append("- ALAFCO: both sides `unreachable`, with a dedicated Wayback plan — 5 gap rows now live "
                 "in the `gaps` table (imported via `seed/import_alafco_gaps.py`) so Session 4's Wayback "
                 "helper picks them up directly from the DB. `data/alafco_gaps.json` is now a staging "
                 "artefact.")
    lines.append("")
    lines.append("## Pilot gate note for Session 4")
    lines.append("")
    lines.append("**Do not include ALAFCO in Session 4's 3-institution financial-wave pilot gate.** "
                 "ALAFCO is a Wayback-only path, not a live-crawl test; including it would make the "
                 "pilot's pass/fail signal ambiguous between \"live crawler works\" and \"Wayback "
                 "helper works\". Pick any 3 of the 22 other financial-wave institutions that have at "
                 "least one verified live source.")
    lines.append("")

    # ---- Table ordered by wave, then rank ----
    lines.append("## Per-institution table")
    lines.append("")
    lines.append("| # | slug | wave | country | ir | exchange | evidence sample |")
    lines.append("|---|---|---|---|---|---|---|")

    ordered = sorted(
        institutions,
        key=lambda r: (0 if meta[r["slug"]]["wave"] == "financial" else 1, meta[r["slug"]]["rank"] or 999),
    )
    for i, inst in enumerate(ordered, start=1):
        m = meta[inst["slug"]]
        pdfs = inst["evidence"]["ir"].get("sample_report_links") or []
        sample = pdfs[0] if pdfs else "—"
        if len(sample) > 90:
            sample = sample[:87] + "..."
        marker = " **(ALAFCO — Tier 3 path)**" if inst["slug"] == ALAFCO_SLUG else ""
        lines.append(
            f"| {i} | `{inst['slug']}`{marker} | {m['wave']} | {m['country']} | "
            f"{inst['ir_status']} | {inst['exchange_status']} | {sample} |"
        )

    # ---- Counts ----
    financial = [i for i in institutions if meta[i["slug"]]["wave"] == "financial"]
    other = [i for i in institutions if meta[i["slug"]]["wave"] == "other"]

    def status_count(rows, key):
        return Counter(row[key] for row in rows)

    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append("### By wave")
    lines.append("")
    lines.append("| wave | rows | ir verified | ir unreachable | ir needs_human | exch verified | exch unreachable | exch needs_human |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for name, rows in (("financial", financial), ("other", other), ("total", institutions)):
        ir_c = status_count(rows, "ir_status")
        ex_c = status_count(rows, "exchange_status")
        lines.append(
            f"| {name} | {len(rows)} | "
            f"{ir_c.get('verified',0)} | {ir_c.get('unreachable',0)} | {ir_c.get('needs_human',0)} | "
            f"{ex_c.get('verified',0)} | {ex_c.get('unreachable',0)} | {ex_c.get('needs_human',0)} |"
        )

    # ---- Combined coverage (ALAFCO reported separately) ----
    def bucket(inst):
        ir_ok = inst["ir_status"] == "verified"
        ex_ok = inst["exchange_status"] == "verified"
        if ir_ok and ex_ok: return "both"
        if ir_ok: return "ir_only"
        if ex_ok: return "exchange_only"
        return "neither"

    non_alafco = [i for i in institutions if i["slug"] != ALAFCO_SLUG]
    buckets = Counter(bucket(i) for i in non_alafco)

    lines.append("")
    lines.append("### Combined coverage (ALAFCO reported separately)")
    lines.append("")
    lines.append(f"Of the {len(non_alafco)} non-ALAFCO institutions:")
    lines.append("")
    lines.append("| combination | count |")
    lines.append("|---|---|")
    for name in ("both", "ir_only", "exchange_only", "neither"):
        lines.append(f"| {name} | {buckets.get(name, 0)} |")

    lines.append("")
    lines.append(f"**ALAFCO** (reported separately): both IR and exchange `unreachable`, but with a "
                 f"documented Tier-3 path — Wayback Machine has 36 captures of alafco.com/en/investors "
                 f"between 2021-03-05 and 2025-05-23. Delisted from Boursa Kuwait on 2025-03-05 before "
                 f"FY2025 closed. See `data/alafco_gaps.json` for one gap row per target year with "
                 f"`tier_tried = live, next_action = Tier 3 Wayback Machine` (and FY2025 marked as "
                 f"confirmed non-existent).")
    lines.append("")
    lines.append("### `neither` breakdown (the real Tier 3/4 backlog)")
    lines.append("")
    lines.append("| slug | wave | country | ir status | exchange status | why |")
    lines.append("|---|---|---|---|---|---|")
    for inst in sorted(institutions, key=lambda r: r["slug"]):
        if inst["slug"] == ALAFCO_SLUG:
            continue
        if bucket(inst) == "neither":
            m = meta[inst["slug"]]
            why = (inst.get("notes") or
                   inst["evidence"]["ir"].get("note") or
                   inst["evidence"]["exchange"].get("note") or "")
            why = why.replace("\n", " ")
            if len(why) > 110:
                why = why[:107] + "..."
            lines.append(
                f"| `{inst['slug']}` | {m['wave']} | {m['country']} | "
                f"{inst['ir_status']} | {inst['exchange_status']} | {why} |"
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")

    # Also print summary.
    print()
    print("Summary:")
    for name, rows in (("financial", financial), ("other", other), ("total", institutions)):
        ir_c = status_count(rows, "ir_status")
        ex_c = status_count(rows, "exchange_status")
        print(f"  {name:>10}: {len(rows):>3} rows | ir {dict(ir_c)} exch {dict(ex_c)}")
    print(f"  combined (ex-ALAFCO): {dict(buckets)}")


if __name__ == "__main__":
    main()
