"""Verity crawler package.

Hard rules from CLAUDE.md (data acquisition) are enforced here, not
elsewhere. Specifically:

- VERITY_CONTACT_EMAIL env var must be set; otherwise `make_user_agent()`
  refuses to build the UA string and the CLI refuses to run.
- robots.txt is fetched once per domain, cached, and obeyed.
- 2-second minimum delay per domain, honoured per-fetch.
- One in-flight request per domain, up to 4 domains in parallel.
- A detected block (403, 429 after 3 retries, challenge-page markers)
  stops that domain for the rest of the run and writes a gap row.
- Playwright is read-only — no form interaction, see tests/test_crawler_no_write_actions.py.
"""
from __future__ import annotations

__all__ = ["__version__", "register_all_mappers"]
__version__ = "0.1.0"


def register_all_mappers() -> None:
    """Import every ORM model module so SQLAlchemy can resolve string-named
    relationships (e.g. `relationship("Report", back_populates=...)`)
    before the first query runs.

    Call this from any CLI/script entry point BEFORE opening a Session.
    Keeps the import side-effects explicit instead of relying on
    `# noqa: F401` tricks that linters routinely delete.
    """
    from app.models import institution, provenance, report, score, taxonomy  # noqa: F401

