"""Playwright-based URL verifier.

Reads a list of URLs (one per line) from stdin or a positional file, visits
each with a Chromium browser labelled as VerityResearchBot (contact email
from VERITY_CONTACT_EMAIL), and emits a JSONL stream with one object per
URL:

    {"url": "...", "final_url": "...", "status": <int|null>, "title": "...",
     "body_signature": "...", "error": null, "fetched_at": "..."}

Politeness: at least 2 seconds between consecutive requests to the same
host (CLAUDE.md data-acquisition rule 5). One in-flight request per domain
is implicit — the script is single-threaded.

Verification tolerance: a status of 200/301/302/304 counts as "reachable";
anything else goes into error. A page-level 403/404 is reported as the
HTTP status, same as a WebFetch 403, so the caller can distinguish
network-level success from site-level block.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

CONTACT = os.environ.get("VERITY_CONTACT_EMAIL")
if not CONTACT:
    print("VERITY_CONTACT_EMAIL not set — refusing to run per CLAUDE.md rule 5", file=sys.stderr)
    sys.exit(2)

USER_AGENT = f"VerityResearchBot/0.1 (academic PhD research; contact: {CONTACT})"
PER_DOMAIN_DELAY_SECONDS = 2.0
DEFAULT_TIMEOUT_MS = 20000
_last_hit: dict[str, float] = {}


def _politeness_wait(url: str) -> None:
    host = urlparse(url).hostname or ""
    last = _last_hit.get(host, 0.0)
    now = time.time()
    wait = PER_DOMAIN_DELAY_SECONDS - (now - last)
    if wait > 0:
        time.sleep(wait)
    _last_hit[host] = time.time()


def _signature(text: str, max_chars: int = 4000) -> str:
    """Short signature of the page body: strip whitespace, trim.

    4 KB is a compromise — long enough to catch company names that live
    below the fold / ticker scroll on SPA sites (ADX, DFM, QSE), still
    short enough that the output JSON stays scannable.
    """
    s = re.sub(r"\s+", " ", text or "").strip()
    return s[:max_chars]


def probe(url: str, timeout_ms: int, wait_selector: str | None) -> dict:
    out: dict = {
        "url": url,
        "final_url": None,
        "status": None,
        "title": None,
        "body_signature": "",
        "error": None,
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    try:
        _politeness_wait(url)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1366, "height": 900},
                locale="en-US",
                ignore_https_errors=False,
            )
            page = ctx.new_page()
            response = page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            out["final_url"] = page.url
            out["status"] = response.status if response else None
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=timeout_ms // 2)
                except PlaywrightTimeout:
                    pass
            # Give the SPA/portlet a longer settle window — ADX/DFM/QSE
            # load company-specific content via XHR after the shell appears.
            page.wait_for_timeout(5000)
            out["title"] = page.title()
            out["body_signature"] = _signature(page.inner_text("body"))
            browser.close()
    except PlaywrightTimeout as exc:
        out["error"] = f"timeout: {exc}"
    except Exception as exc:  # noqa: BLE001 — want full taxonomy of browser errors
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("urls_file", nargs="?", help="Path with one URL per line; omit to read from stdin")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_MS)
    parser.add_argument("--wait-selector", default=None, help="Optional CSS selector to wait for")
    args = parser.parse_args()

    # Force UTF-8 stdout so Arabic page content doesn't crash cp1252 on Windows.
    sys.stdout.reconfigure(encoding="utf-8")

    source = Path(args.urls_file).open(encoding="utf-8") if args.urls_file else sys.stdin
    urls = [line.strip() for line in source if line.strip() and not line.strip().startswith("#")]

    for url in urls:
        print(json.dumps(probe(url, args.timeout, args.wait_selector), ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
