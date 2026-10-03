"""Reader for config/verity.toml.

Kept intentionally small: parses the TOML on first read, caches it, and
exposes a typed VerityConfig. Anything read from here must be defaultable
(missing key -> documented default) so that dev environments without a
custom config file still work.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# config/ lives at the repo root, alongside backend/.
_DEFAULT_PATH = Path(__file__).resolve().parents[3] / "config" / "verity.toml"


_DEFAULT_FS_MARKERS = [
    "independent auditor's report",
    "independent auditors' report",
    "report of the independent auditor",
    "consolidated statement of financial position",
    "consolidated statement of comprehensive income",
    "consolidated statement of cash flows",
    "consolidated statement of changes in equity",
    "statement of financial position",
    "notes to the consolidated financial statements",
    "notes to the financial statements",
]


@dataclass(frozen=True)
class VerityConfig:
    years: list[int] = field(default_factory=lambda: [2021, 2022, 2023, 2024, 2025])
    report_types_scored: list[str] = field(default_factory=lambda: ["annual", "integrated"])
    matching_mode: str = "longest"
    exclude_toc_pages: bool = True
    exclude_repeated_lines: bool = True
    # Declared here now (Patch A). Session 5 lands the implementation:
    # everything from the independent auditor's report onward is dropped
    # before scoring, so density measures narrative disclosure only.
    exclude_financial_statement_pages: bool = True
    header_footer_repeat_ratio: float = 0.30
    arabic_page_token_ratio: float = 0.50
    ocr_max_page_ratio: float = 0.40
    log_all_mode_diff: bool = True
    financial_statement_boundary_markers: list[str] = field(
        default_factory=lambda: list(_DEFAULT_FS_MARKERS)
    )
    worker_count: int = 0  # 0 = auto (CPU count - 1)
    iqr_multiplier: float = 3.0
    iqr_min_cohort: int = 5
    low_latin_word_count_threshold: int = 5000
    high_ocr_ratio_threshold: float = 0.30
    high_arabic_ratio_threshold: float = 0.50
    evidence_sample_per_pillar: int = 50
    evidence_sample_seed: int = 42
    wave_order: list[str] = field(default_factory=lambda: ["financial", "other"])


_cache: VerityConfig | None = None


def load_verity_config(path: Path | None = None) -> VerityConfig:
    """Read and cache config/verity.toml. Pass an explicit path to bypass the cache
    (e.g. tests that want a purpose-built config)."""
    global _cache
    if path is None:
        if _cache is not None:
            return _cache
        path = _DEFAULT_PATH

    if not path.exists():
        cfg = VerityConfig()
    else:
        with path.open("rb") as fh:
            raw = tomllib.load(fh)
        pipe = raw.get("pipeline", {})
        proc = raw.get("processing", {})
        defaults = VerityConfig()
        cfg = VerityConfig(
            years=list(raw.get("schedule", {}).get("years", defaults.years)),
            report_types_scored=list(
                raw.get("reports", {}).get(
                    "report_types_scored", defaults.report_types_scored
                )
            ),
            matching_mode=str(pipe.get("matching_mode", defaults.matching_mode)),
            exclude_toc_pages=bool(pipe.get("exclude_toc_pages", defaults.exclude_toc_pages)),
            exclude_repeated_lines=bool(
                pipe.get("exclude_repeated_lines", defaults.exclude_repeated_lines)
            ),
            exclude_financial_statement_pages=bool(
                pipe.get(
                    "exclude_financial_statement_pages",
                    defaults.exclude_financial_statement_pages,
                )
            ),
            header_footer_repeat_ratio=float(
                pipe.get("header_footer_repeat_ratio", defaults.header_footer_repeat_ratio)
            ),
            arabic_page_token_ratio=float(
                pipe.get("arabic_page_token_ratio", defaults.arabic_page_token_ratio)
            ),
            ocr_max_page_ratio=float(
                pipe.get("ocr_max_page_ratio", defaults.ocr_max_page_ratio)
            ),
            log_all_mode_diff=bool(
                pipe.get("log_all_mode_diff", defaults.log_all_mode_diff)
            ),
            financial_statement_boundary_markers=list(
                pipe.get(
                    "financial_statement_boundary_markers",
                    defaults.financial_statement_boundary_markers,
                )
            ),
            worker_count=int(proc.get("worker_count", defaults.worker_count)),
            iqr_multiplier=float(proc.get("iqr_multiplier", defaults.iqr_multiplier)),
            iqr_min_cohort=int(proc.get("iqr_min_cohort", defaults.iqr_min_cohort)),
            low_latin_word_count_threshold=int(
                proc.get("low_latin_word_count_threshold",
                         defaults.low_latin_word_count_threshold)
            ),
            high_ocr_ratio_threshold=float(
                proc.get("high_ocr_ratio_threshold", defaults.high_ocr_ratio_threshold)
            ),
            high_arabic_ratio_threshold=float(
                proc.get("high_arabic_ratio_threshold", defaults.high_arabic_ratio_threshold)
            ),
            evidence_sample_per_pillar=int(
                proc.get("evidence_sample_per_pillar", defaults.evidence_sample_per_pillar)
            ),
            evidence_sample_seed=int(
                proc.get("evidence_sample_seed", defaults.evidence_sample_seed)
            ),
            wave_order=list(raw.get("waves", {}).get("order", defaults.wave_order)),
        )

    if path == _DEFAULT_PATH:
        _cache = cfg
    return cfg


def reset_cache() -> None:
    """Test hook — forget the cached config so tests can hand-craft one."""
    global _cache
    _cache = None
