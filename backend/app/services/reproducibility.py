"""Reproducibility helpers used by the batch runner and the `reproduce`
CLI. Everything is pure functions over paths and content hashes, so it's
cheap to call at both the start of a batch (to open a Run row) and
during an assertion-driven reproduce pass.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from app.config import settings

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = REPO_ROOT / "config" / "verity.toml"
MANIFEST_PATH = Path(settings.storage_dir).parent / "manifest.jsonl"


def git_commit() -> str:
    """Return the current HEAD sha, or the literal string "uncommitted" if
    the repo is a fresh working tree with no commits yet. Session 7 note:
    the project isn't under version control at submission time; recording
    "uncommitted" is honest and keeps the reproducibility story auditable
    rather than silently stamping an empty string.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True
        )
    except FileNotFoundError:
        return "no-git"
    if out.returncode != 0:
        return "uncommitted"
    return out.stdout.strip() or "uncommitted"


def _hash_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def config_hash() -> str:
    return _hash_file(CONFIG_PATH)


def manifest_hash() -> str:
    return _hash_file(MANIFEST_PATH)
