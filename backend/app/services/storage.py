"""Storage layer: PDF read/write backed by Cloudflare R2.

In production PDFs live in R2; `SourceDocument.file_path` holds the R2 object
key (forward-slash, no absolute prefix — e.g.
`al-rajhi-bank/2025_integrated_e66e4adf.pdf`). The crawler calls `write_pdf()`,
the dashboard streams via `open_pdf_stream()`, the scoring pipeline reads bytes
via `read_pdf_bytes()`.

**R2 is required in production.** All four I/O functions raise `RuntimeError`
when the R2 client cannot be constructed (missing env vars) UNLESS the env var
`VERITY_LOCAL_STORAGE=1` is explicitly set, which enables the local-disk fallback
for developer environments without R2 credentials. Never set
`VERITY_LOCAL_STORAGE=1` in a deployed environment.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings


class R2Settings:
    """Read R2 config from env."""

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
        config=Config(
            signature_version="s3v4",
            connect_timeout=10,
            read_timeout=120,
            retries={"max_attempts": 2, "mode": "standard"},
        ),
    )


def r2_enabled() -> bool:
    return R2Settings().enabled


def _local_storage_enabled() -> bool:
    """True only when VERITY_LOCAL_STORAGE=1 is explicitly set.
    Intended for local development without R2 credentials."""
    return os.environ.get("VERITY_LOCAL_STORAGE", "") == "1"


def _require_r2(fn_name: str) -> None:
    """Raise if R2 is unavailable and the local-storage flag is not set."""
    raise RuntimeError(
        f"{fn_name}: R2 is not configured and VERITY_LOCAL_STORAGE=1 is not set. "
        "Configure R2 credentials (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, "
        "R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME), or set VERITY_LOCAL_STORAGE=1 "
        "for local development only."
    )


def _local_path(key: str) -> Path:
    """Dev fallback: resolve an R2 object key to a path under storage_dir."""
    return Path(settings.storage_dir) / key


def write_pdf(key: str, body: bytes) -> str:
    """Upload bytes to R2 at the given key.

    Returns the key for the caller to persist as `SourceDocument.file_path`.
    Raises `RuntimeError` if R2 is unavailable, unless `VERITY_LOCAL_STORAGE=1`.
    """
    client = _r2_client()
    if client is None:
        if not _local_storage_enabled():
            _require_r2("write_pdf")
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
    """Return the full PDF content for the given key.

    Raises `RuntimeError` if R2 is unavailable (unless `VERITY_LOCAL_STORAGE=1`).
    Raises `FileNotFoundError` if the object does not exist in R2.
    """
    client = _r2_client()
    if client is None:
        if not _local_storage_enabled():
            _require_r2("read_pdf_bytes")
        p = _local_path(key)
        if not p.exists():
            raise FileNotFoundError(f"local PDF missing: {p}")
        return p.read_bytes()
    try:
        obj = client.get_object(Bucket=R2Settings().bucket, Key=key)
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("NoSuchKey", "404"):
            raise FileNotFoundError(f"R2 object not found: {key}") from exc
        raise
    return obj["Body"].read()


def open_pdf_stream(key: str) -> BinaryIO:
    """Return a file-like object for streaming the PDF.

    For R2 this is the raw botocore StreamingBody; for local dev a file handle.
    Caller is responsible for closing (FastAPI StreamingResponse handles the
    HTTP side). Raises `RuntimeError` if R2 is unavailable, unless
    `VERITY_LOCAL_STORAGE=1`.
    """
    client = _r2_client()
    if client is None:
        if not _local_storage_enabled():
            _require_r2("open_pdf_stream")
        return _local_path(key).open("rb")
    try:
        obj = client.get_object(Bucket=R2Settings().bucket, Key=key)
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("NoSuchKey", "404"):
            raise FileNotFoundError(f"R2 object not found: {key}") from exc
        raise
    return obj["Body"]


def pdf_exists(key: str) -> bool:
    """True iff an object exists at the given key.

    Raises `RuntimeError` if R2 is unavailable, unless `VERITY_LOCAL_STORAGE=1`.
    """
    client = _r2_client()
    if client is None:
        if not _local_storage_enabled():
            _require_r2("pdf_exists")
        return _local_path(key).exists()
    try:
        client.head_object(Bucket=R2Settings().bucket, Key=key)
        return True
    except ClientError:
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
    return norm.lstrip("/")
