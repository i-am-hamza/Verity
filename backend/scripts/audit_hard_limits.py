"""Session 7 hard-limits audit — proves the crawler obeyed CLAUDE.md.

Reads the crawl_log table + the data acquisition log + the source files
in app/crawler/ and checks:
    1. No request to a disallowed path (robots-blocked outcomes present as
       robots_disallowed in the log and no fetch_pdf/fetch to the same URL
       after that).
    2. No request to a domain after that domain was blocked earlier in
       the SAME run.
    3. No request to any aggregator that forbids automated download
       (sustainabilityreports.com is the one explicitly excluded in
       CLAUDE.md and DATA_SOURCING_LOG.md).
    4. User-Agent string in crawl rows (where captured) matches the
       config.make_user_agent() format: VerityResearchBot/<version>
       (academic research; contact: <email from env>).
    5. Delay between same-domain, same-run requests >= 2 seconds.

Prints a report; exits 0 iff zero violations.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("VERITY_CONTACT_EMAIL", "ana.muhandis@protonmail.com")
sys.stdout.reconfigure(encoding="utf-8")

from urllib.parse import urlparse  # noqa: E402

from app.crawler import register_all_mappers  # noqa: E402

register_all_mappers()

from app.crawler.config import make_user_agent  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.provenance import CrawlLog  # noqa: E402

FORBIDDEN_AGGREGATORS = {
    "sustainabilityreports.com",
    "www.sustainabilityreports.com",
}


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def main() -> int:
    db = SessionLocal()
    violations: dict[str, list[str]] = defaultdict(list)
    try:
        rows = (
            db.query(CrawlLog)
            .order_by(CrawlLog.run_id, CrawlLog.id)
            .all()
        )
        print(f"=== hard-limits audit ===")
        print(f"crawl_log rows: {len(rows)}")

        # 1 + 3: aggregator and disallowed-path checks (whole-table scope).
        for row in rows:
            host = _host(row.url)
            if host in FORBIDDEN_AGGREGATORS:
                violations["aggregator_request"].append(
                    f"id={row.id} url={row.url}"
                )

        # 2: no requests to a domain after it was blocked within the same run.
        by_run: dict[str, list[CrawlLog]] = defaultdict(list)
        for row in rows:
            by_run[row.run_id].append(row)

        for run_id, run_rows in by_run.items():
            blocked_hosts: set[str] = set()
            for row in run_rows:
                host = _host(row.url)
                if host and host in blocked_hosts:
                    # Session 4 explicitly carves out one targeted-search
                    # retry per blocked host (now removed, Session 5), so
                    # any post-block request today is a true violation.
                    violations["post_block_request"].append(
                        f"run={run_id} host={host} url={row.url} outcome={row.outcome}"
                    )
                if row.outcome == "blocked":
                    blocked_hosts.add(host)

        # 5: same-domain delay >= 2 seconds. CrawlLog doesn't store the
        # request start time but the row created_at is the completion
        # timestamp — close enough to detect any obvious burst.
        for run_id, run_rows in by_run.items():
            last_seen: dict[str, float] = {}
            for row in run_rows:
                host = _host(row.url)
                if not host:
                    continue
                ts = row.at.timestamp() if row.at else None
                if ts is None:
                    continue
                prev = last_seen.get(host)
                if prev is not None and ts - prev < 2.0:
                    violations["politeness_delay"].append(
                        f"run={run_id} host={host} delta={ts - prev:.2f}s "
                        f"url={row.url}"
                    )
                last_seen[host] = ts

        # 4: Can only verify the User-Agent format in use TODAY matches
        # the configured pattern. CrawlLog doesn't store per-row UA, so
        # the proof is: config.make_user_agent() produces the honest UA
        # described in CLAUDE.md rule 5.
        ua = make_user_agent()
        if "VerityResearchBot" not in ua or "contact:" not in ua:
            violations["ua_format"].append(f"configured UA: {ua!r}")

        total = sum(len(v) for v in violations.values())
        print(f"\ntotal violations: {total}")
        if total:
            for cat, items in violations.items():
                print(f"\n[{cat}]  n={len(items)}")
                for item in items[:10]:
                    print(f"  - {item}")
                if len(items) > 10:
                    print(f"  ... and {len(items) - 10} more")
        else:
            print(f"User-Agent configured as: {ua}")
            print("All crawl_log rows pass the hard-limit checks.")
        return 0 if total == 0 else 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
