"""Session 9 storage layer.

Backend-wide PDF read/write wrapper. In production (Session 9+), PDFs live
in Cloudflare R2 and `SourceDocument.file_path` holds the R2 object key
(no backslashes, no absolute paths, just something like
`al-rajhi-bank/2025_integrated_e66e4adf.pdf`). The crawler calls
`write_pdf()`, the dashboard streams via `open_pdf_stream()`, the scoring
pipeline reads bytes via `read_pdf_bytes()` and passes them to pymupdf.

Keeping this behind a thin wrapper has three benefits:
1. The backend's dependence on "there's a local disk somewhere" collapses
   to this one module — the FastAPI process is stateless.
2. Local development against a volume mount still works: if R2 env vars
   are missing, the wrapper falls through to a plain filesystem path
   relative to `settings.storage_dir`.
3. The S3 API lives in exactly one place; swapping to a different
   object store later is a config change, not a code refactor.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.config import Config

from app.config import settings


class R2Settings:
    """Read R2 config from env. Lazy so dev / tests without R2 just see
    `enabled=False` and get the local-disk path instead."""

    def __init__(self) -> None:
        self.account_id = os.environ.get("R2_ACCOUNT_ID", "")
        self.access_key_id = os.environ.get("R2_ACCESS_KEY_ID", "")
        self.secret_access_key = os.environ.get("R2_SECRET_ACCESS_KEY", "")
        self.bucket = os.environ.get("R2_BUCKET_NAME", "")

    @property
    def enabled(self) -> bool:
        return bool(
            self.account_id and self.access_key_id
            and self.secret_access_key and self.bucket
        )

    @property
    def endpoint_url(self) -> str:
        return f"https://{self.account_id}.r2.cloudflarestorage.com"


@lru_cache(maxsize=1)
def _r2_client():
    cfg = R2Settings()
    if not cfg.enabled:
        return None
    return boto3.client(
        "s3",
        endpoint_url=cfg.endpoint_url,
        aws_access_key_id=cfg.access_key_id,
        aws_secret_access_key=cfg.secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def r2_enabled() -> bool:
    return R2Settings().enabled


def _local_path(key: str) -> Path:
    """Dev fallback: resolve an R2 object key to a path under storage_dir."""
    return Path(settings.storage_dir) / key


def write_pdf(key: str, body: bytes) -> str:
    """Upload bytes to R2 (or write to disk in dev) at the given key.

    Returns the key, which is what the caller should persist as
    `SourceDocument.file_path`.
    """
    client = _r2_client()
    if client is None:
        p = _local_path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
        return key
    client.put_object(
        Bucket=R2Settings().bucket, Key=key, Body=body,
        ContentType="application/pdf",
    )
    return key


def read_pdf_bytes(key: str) -> bytes:
    """Return the full PDF content for the given key. Used by the scoring
    pipeline to hand bytes to pymupdf; one read per report, cached by
    nothing because the pipeline consumes the result immediately."""
    client = _r2_client()
    if client is None:
        p = _local_path(key)
        if not p.exists():
            raise FileNotFoundError(f"local PDF missing: {p}")
        return p.read_bytes()
    obj = client.get_object(Bucket=R2Settings().bucket, Key=key)
    return obj["Body"].read()


def open_pdf_stream(key: str) -> BinaryIO:
    """Return a file-like object for the dashboard's PDF endpoint. For R2
    this is the raw botocore StreamingBody; for local dev it's a file
    handle. Caller closes it (FastAPI StreamingResponse handles that for
    the HTTP side)."""
    client = _r2_client()
    if client is None:
        return _local_path(key).open("rb")
    obj = client.get_object(Bucket=R2Settings().bucket, Key=key)
    return obj["Body"]


def pdf_exists(key: str) -> bool:
    """True iff an object exists at the given key. Used by the provenance
    audit to confirm every SourceDocument's file is still reachable."""
    client = _r2_client()
    if client is None:
        return _local_path(key).exists()
    try:
        client.head_object(Bucket=R2Settings().bucket, Key=key)
        return True
    except Exception:
        return False


def file_path_to_r2_key(file_path: str) -> str:
    """Convert a legacy absolute (local-disk) file_path to an R2 object key.

    The convention in this project is:
        storage/reports/<slug>/<year>_<report_type>_<sha_prefix>.pdf

    So the key is everything after `storage/reports/`. Normalises
    backslashes to forward slashes for S3 compatibility.
    """
    norm = file_path.replace("\\", "/")
    marker = "storage/reports/"
    i = norm.rfind(marker)
    if i >= 0:
        return norm[i + len(marker):]
    # If a file_path is already a bare key (no absolute prefix), return as-is.
    return norm.lstrip("/")
