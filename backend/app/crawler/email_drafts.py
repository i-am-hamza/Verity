"""Tier 4: draft an email per institution with outstanding gaps.

Writes `docs/ir_email_drafts/<slug>.txt`. **Nothing is sent** — this
module has no SMTP code and no network calls. CLAUDE.md rule 9.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.crawler.config import EMAIL_DRAFTS_DIR, get_contact_email
from app.models.institution import Institution
from app.models.provenance import Gap

_TEMPLATE = """\
Subject: Academic request — annual report PDFs ({years})

Dear Investor Relations team at {institution_name},

I am a PhD researcher building a public, academic text-based analysis of
Environmental, Social and Governance disclosures in annual reports from
Middle East listed companies. Your firm is one of 65 institutions in the
study, selected from publicly available market-capitalisation data.

I have been able to retrieve some of your annual reports from your
public investor-relations page{{,}} but the following fiscal year{plural} {verb} not
publicly reachable at this time:

{year_list}

If you are able to point me at a public URL for each PDF, or attach them
to a reply, I would be very grateful. The reports will be used only for
the academic study described above; no commercial use, no redistribution.

With thanks,
Verity (academic PhD research)
Contact: {contact_email}

---
This is a one-off, polite request. The project otherwise relies entirely
on public pages, obeys robots.txt, identifies itself with a descriptive
User-Agent, and never submits forms or credentials.
"""


def _format_years(years: list[int]) -> tuple[str, str, str]:
    years_s = sorted(set(years))
    if len(years_s) == 1:
        year_list = f"- Fiscal year {years_s[0]}"
        plural, verb = "", "is"
    else:
        year_list = "\n".join(f"- Fiscal year {y}" for y in years_s)
        plural, verb = "s", "are"
    return year_list, plural, verb


def write_email_drafts(db: Session) -> list[Path]:
    EMAIL_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    contact = get_contact_email()

    gaps_by_inst: dict[int, list[int]] = {}
    for g in db.query(Gap).all():
        gaps_by_inst.setdefault(g.institution_id, []).append(g.fiscal_year)

    paths: list[Path] = []
    for inst_id, years in gaps_by_inst.items():
        inst = db.get(Institution, inst_id)
        if inst is None:
            continue
        year_list, plural, verb = _format_years(years)
        content = _TEMPLATE.format(
            institution_name=inst.name,
            years=", ".join(str(y) for y in sorted(set(years))),
            year_list=year_list, plural=plural, verb=verb,
            contact_email=contact,
        )
        header = (
            f"# DRAFT ONLY — generated {datetime.now(UTC).isoformat(timespec='seconds')}\n"
            f"# This file is NOT sent by any Verity code. Review and send manually.\n\n"
        )
        path = EMAIL_DRAFTS_DIR / f"{inst.slug}.txt"
        path.write_text(header + content, encoding="utf-8")
        paths.append(path)
    return paths
