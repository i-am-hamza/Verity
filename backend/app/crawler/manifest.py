"""File storage + manifest writer.

The storage/manifest.jsonl file is the ground-truth audit log: one JSON
object per line, append-only, keyed by sha256. The DB (source_documents)
is the queryable view; the manifest is what survives if the DB is
dropped and rebuilt.

Session 9 change: PDF bytes themselves live in Cloudflare R2, not on
the local disk. The manifest.jsonl stays append-only on disk (it's the
offline-replayable audit log). The `file_path` column stored on
SourceDocument and in each manifest row is the R2 object key — a
forward-slash path relative to the bucket root, e.g.
"al-rajhi-bank/2025_integrated_e66e4adf.pdf". Historical manifest rows
that still carry an absolute Windows path are left alone (append-only);
the storage module's `file_path_to_r2_key` resolves both forms.

Idempotency: `save_pdf` is keyed by sha256. If the same sha256 is
already present in the manifest, no R2 upload is performed and no
new manifest row is appended — the caller gets back the existing key
and `created=False`.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime

from app.crawler.config import MANIFEST_PATH, REPORTS_DIR
from app.services.storage import file_path_to_r2_key, write_pdf


def _ensure_dirs() -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    # REPORTS_DIR still exists for the dev / tests filesystem fallback
    # inside app.services.storage; harmless to pre-create.
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_existing_sha256() -> dict[str, str]:
    """Return sha256 -> R2 object key mapping based on the manifest.

    Reads every line, keeps the LAST entry for a given sha256. Any
    legacy absolute-path row is normalised to an R2 key via
    `file_path_to_r2_key` so callers can treat the return value
    uniformly.
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
                out[sha] = file_path_to_r2_key(path)
    return out


def report_key(slug: str, fiscal_year: int, report_type: str, sha256: str) -> str:
    """The R2 object key for a given report. Mirrors the old on-disk
    layout <slug>/<year>_<report_type>_<sha_prefix>.pdf but as a
    forward-slash key with no absolute prefix.
    """
    short = sha256[:8]
    return f"{slug}/{fiscal_year}_{report_type}_{short}.pdf"


def save_pdf(
    *,
    slug: str,
    fiscal_year: int,
    report_type: str,
    sha256: str,
    body: bytes,
    manifest_row: dict,
) -> tuple[str, bool]:
    """Write the PDF to R2 (or the dev-mode local fallback) and append a
    manifest line.

    Returns `(key, created)`. `created=False` means the sha256 was
    already present; nothing was uploaded. The returned key is the
    existing object in that case. Callers should persist the key as
    `SourceDocument.file_path`.
    """
    _ensure_dirs()
    existing = load_existing_sha256()
    if sha256 in existing:
        return existing[sha256], False

    key = report_key(slug, fiscal_year, report_type, sha256)
    write_pdf(key, body)

    row = {
        **manifest_row,
        "sha256": sha256,
        "file_path": key,
        "written_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    with MANIFEST_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return key, True
