"""Session 7 hardening: a `runs` table so every batch execution is
reproducible after the fact.

One row per `python -m app.cli process` (or `reproduce`) invocation —
captures the git commit of the running code, the taxonomy and pipeline
versions in force, a hash of the config file, a hash of the manifest at
start, and timestamps. The reproduce CLI uses this row (plus the stored
Report / CategoryScore / MatchEvidence rows) to assert that running the
pipeline today under the same versions produces byte-identical scoring
output.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    kind: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # One of: "process", "reproduce", "reproduce-ok", "reproduce-mismatch".
    git_commit: Mapped[str] = mapped_column(String, nullable=False)
    # 40-char SHA or the literal string "uncommitted" when the repo is a
    # fresh working copy with no commits yet.
    taxonomy_version: Mapped[str] = mapped_column(String, nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String, nullable=False)
    config_hash: Mapped[str] = mapped_column(String, nullable=False)
    # SHA-256 of config/verity.toml at run start.
    manifest_hash: Mapped[str] = mapped_column(String, nullable=False)
    # SHA-256 of storage/manifest.jsonl at run start; proves which files
    # were in the corpus when scoring happened.
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
