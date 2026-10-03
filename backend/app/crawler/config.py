"""Runtime config for the crawler.

The contact email is read exactly once at import time. If it is unset,
`get_contact_email()` raises immediately — that's the CLAUDE.md rule 5
guarantee: no network request ever leaves this package without a
descriptive, contactable UA.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
STORAGE_DIR = REPO_ROOT / "backend" / "storage"
REPORTS_DIR = STORAGE_DIR / "reports"
MANIFEST_PATH = STORAGE_DIR / "manifest.jsonl"
MANUAL_INBOX_DIR = STORAGE_DIR / "manual_inbox"

IR_SOURCES_PATH = REPO_ROOT / "data" / "ir_sources.json"
APPROVED_DOWNLOADS_PATH = REPO_ROOT / "data" / "approved_downloads.json"

DOCS_DIR = REPO_ROOT / "docs"
GAP_REPORT_PATH = DOCS_DIR / "GAP_REPORT.md"
WAYBACK_CANDIDATES_PATH = DOCS_DIR / "WAYBACK_CANDIDATES.md"
EMAIL_DRAFTS_DIR = DOCS_DIR / "ir_email_drafts"

PER_DOMAIN_DELAY_SECONDS = 2.0
MAX_RETRIES = 3
MAX_PARALLEL_DOMAINS = 4
MAX_CRAWL_DEPTH = 3
MAX_PAGES_PER_SOURCE = 25
MIN_PDF_BYTES = 100 * 1024  # 100 KB
MIN_ANNUAL_REPORT_PAGES = 30


def get_contact_email() -> str:
    """Return VERITY_CONTACT_EMAIL or raise. Called once per CLI run."""
    email = os.environ.get("VERITY_CONTACT_EMAIL", "").strip()
    if not email:
        raise RuntimeError(
            "VERITY_CONTACT_EMAIL is not set. Per CLAUDE.md rule 5 the crawler "
            "refuses to make any network request without a contact email in its "
            "User-Agent. Set the env var and re-run."
        )
    return email


def make_user_agent() -> str:
    return f"VerityResearchBot/1.0 (academic research; contact: {get_contact_email()})"
