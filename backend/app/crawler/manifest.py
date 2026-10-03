"""File storage + manifest writer.

The storage/manifest.jsonl file is the ground-truth audit log: one JSON
object per line, append-only, keyed by sha256. The DB (source_documents)
is the queryable view; the manifest is what survives if the DB is
dropped and rebuilt.

Idempotency: `save_pdf` is keyed by sha256. If the same sha256 is
already present on disk or in the manifest, no file is written and no
new manifest row is appended — the caller gets back the existing path
and a note that it was deduped.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.crawler.config import MANIFEST_PATH, REPORTS_DIR


def _ensure_dirs() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_existing_sha256() -> dict[str, str]:
    """Return sha256 -> file_path mapping based on the current manifest.

    Reads every line, keeps the LAST entry for a given sha256 (so an
    older row that pointed at a since-renamed file is overridden by the
    row that reflects the current layout).
    """
    _ensure_dirs()
    out: dict[str, str] = {}
    if not MANIFEST_PATH.exists():
        return out
    with MANIFEST_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            sha = row.get("sha256")
            path = row.get("file_path")
            if sha and path:
                out[sha] = path
    return out


def report_path(slug: str, fiscal_year: int, report_type: str, sha256: str) -> Path:
    short = sha256[:8]
    return REPORTS_DIR / slug / f"{fiscal_year}_{report_type}_{short}.pdf"


def save_pdf(
    *,
    slug: str,
    fiscal_year: int,
    report_type: str,
    sha256: str,
    body: bytes,
    manifest_row: dict,
) -> tuple[Path, bool]:
    """Write the PDF to disk and append a manifest line.

    Returns `(path, created)`. `created=False` means the sha256 was
    already present; nothing was written. The returned path is the
    existing file in that case.
    """
    _ensure_dirs()
    existing = load_existing_sha256()
    if sha256 in existing:
        return Path(existing[sha256]), False

    dest = report_path(slug, fiscal_year, report_type, sha256)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)

    row = {
        **manifest_row,
        "sha256": sha256,
        "file_path": str(dest),
        "written_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    with MANIFEST_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return dest, True
