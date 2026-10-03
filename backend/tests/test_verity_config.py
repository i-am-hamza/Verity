"""verity.toml reader smoke tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.verity_config import VerityConfig, load_verity_config, reset_cache


def test_repo_config_is_readable_and_matches_expectations():
    reset_cache()
    cfg = load_verity_config()
    assert cfg.years == [2020, 2021, 2022, 2023, 2024, 2025]
    assert cfg.report_types_scored == ["annual", "integrated"]
    assert cfg.matching_mode == "longest"
    assert cfg.exclude_toc_pages is True
    assert cfg.exclude_repeated_lines is True
    assert cfg.exclude_financial_statement_pages is True  # Patch A
    assert cfg.wave_order == ["financial", "other"]


def test_missing_file_falls_back_to_defaults(tmp_path):
    cfg = load_verity_config(tmp_path / "does-not-exist.toml")
    assert cfg == VerityConfig()


def test_custom_toml_overrides_defaults(tmp_path):
    path = tmp_path / "custom.toml"
    path.write_text(
        """
[schedule]
years = [2020]

[pipeline]
matching_mode = "all"
exclude_toc_pages = false
exclude_repeated_lines = false

[reports]
report_types_scored = ["annual"]

[waves]
order = ["other", "financial"]
""",
        encoding="utf-8",
    )
    cfg = load_verity_config(path)
    assert cfg.years == [2020]
    assert cfg.matching_mode == "all"
    assert cfg.exclude_toc_pages is False
    assert cfg.exclude_repeated_lines is False
    assert cfg.report_types_scored == ["annual"]
    assert cfg.wave_order == ["other", "financial"]
