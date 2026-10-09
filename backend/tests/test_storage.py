"""Tests for app.services.storage — R2 guard and local fallback."""
from __future__ import annotations

import pytest

import app.services.storage as storage


def test_write_pdf_raises_without_r2_and_no_local_flag(monkeypatch):
    """write_pdf raises RuntimeError when R2 is unavailable and the local-storage
    flag is not set."""
    monkeypatch.delenv("VERITY_LOCAL_STORAGE", raising=False)
    monkeypatch.setattr(storage, "_r2_client", lambda: None)
    with pytest.raises(RuntimeError, match="R2"):
        storage.write_pdf("slug/2024_annual_abc12345.pdf", b"%PDF-1.4")


def test_read_pdf_bytes_raises_without_r2_and_no_local_flag(monkeypatch):
    """read_pdf_bytes raises RuntimeError when R2 is unavailable and the
    local-storage flag is not set."""
    monkeypatch.delenv("VERITY_LOCAL_STORAGE", raising=False)
    monkeypatch.setattr(storage, "_r2_client", lambda: None)
    with pytest.raises(RuntimeError, match="R2"):
        storage.read_pdf_bytes("slug/2024_annual_abc12345.pdf")


def test_local_fallback_works_when_flag_set(monkeypatch, tmp_path):
    """With VERITY_LOCAL_STORAGE=1 and no R2, write_pdf and read_pdf_bytes
    use the local disk under storage_dir."""
    monkeypatch.setenv("VERITY_LOCAL_STORAGE", "1")
    monkeypatch.setattr(storage, "_r2_client", lambda: None)
    monkeypatch.setattr(storage.settings, "storage_dir", tmp_path)

    key = "slug/2024_annual_abc12345.pdf"
    body = b"%PDF-1.4 local-storage test"
    storage.write_pdf(key, body)
    assert storage.read_pdf_bytes(key) == body
