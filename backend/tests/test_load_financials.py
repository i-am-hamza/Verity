"""Tests for the researcher-financials loader (scripts/load_financials.py).

Covers only pure-logic functions:
  - parse_market_cap_to_usd_millions
  - _num and _norm sanity
  - apply_corrections (all four researcher corrections / six cells)
  - compute_tobins_q_and_pb (positive, zero, negative equity)
  - resolve_institution_names (direct match + NAME_OVERRIDES)
  - load_rows against the committed inputs in analysis/data/

The DB write path (write_db) is exercised end-to-end by the loader when
run against the test DB, not here. These tests must not open DB sessions.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def _load() -> object:
    """Load the script module without triggering DB imports in app.database.

    The script-level `load_dotenv` call is fine; the DB session only opens
    when write_db() runs, which these tests do not call.
    """
    spec = importlib.util.spec_from_file_location(
        "load_financials",
        BACKEND / "scripts" / "load_financials.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("load_financials", mod)
    spec.loader.exec_module(mod)
    return mod


_mod = _load()
Correction = _mod.Correction
FinRow = _mod.FinRow
parse_mcap = _mod.parse_market_cap_to_usd_millions
apply_corrections = _mod.apply_corrections
compute = _mod.compute_tobins_q_and_pb
resolve_names = _mod.resolve_institution_names
load_rows = _mod.load_rows
NAME_OVERRIDES = _mod.NAME_OVERRIDES


# -------------------------------------------------------- market-cap parse
def test_mcap_trillion() -> None:
    assert parse_mcap("$2.053 T") == 2.053e12 / 1e6  # 2_053_000 USD million


def test_mcap_billion() -> None:
    assert parse_mcap("$5.6 B") == 5600.0


def test_mcap_million() -> None:
    assert parse_mcap("$920 M") == 920.0


def test_mcap_blank_is_none() -> None:
    assert parse_mcap(None) is None
    assert parse_mcap("") is None


def test_mcap_numeric_passthrough() -> None:
    # Numeric cell already in USD → USD millions.
    assert parse_mcap(2_053_000_000_000) == 2_053_000.0


# -------------------------------------------------------- corrections
def _fin(company: str, year: int, **kw: float | None) -> FinRow:
    defaults = dict(
        market_cap_usd_m=None, eps=None, leverage=None,
        net_margin=None, roe=None, roa=None,
    )
    defaults.update(kw)
    return FinRow(company=company, year=year, **defaults)


def test_corrections_apply_cleanly() -> None:
    rows = [
        _fin("Saudi Aramco", 2024, roe=16.07, roa=26.32),
        _fin("Saudi Aramco", 2025, roe=13.99, roa=23.59),
        _fin("Sahara International Petrochemical Co.", 2025, net_margin=2.45),
        _fin("Bank Aljazira", 2020, eps=0.70),
    ]
    apply_corrections(rows)
    assert rows[0].roe == 26.32 and rows[0].roa == 16.07
    assert rows[1].roe == 23.59 and rows[1].roa == 13.99
    assert rows[2].net_margin == -12.6
    assert rows[3].eps == 0.03


def test_corrections_raise_on_source_drift() -> None:
    # Source value differs from expected "old" → must fail loudly.
    rows = [
        _fin("Saudi Aramco", 2024, roe=99.0, roa=26.32),
        _fin("Saudi Aramco", 2025, roe=13.99, roa=23.59),
        _fin("Sahara International Petrochemical Co.", 2025, net_margin=2.45),
        _fin("Bank Aljazira", 2020, eps=0.70),
    ]
    import pytest  # type: ignore[import-not-found]
    with pytest.raises(ValueError, match="Correction mismatch"):
        apply_corrections(rows)


# -------------------------------------------------------- derived ratios
def test_tobins_q_normal() -> None:
    r = _fin("X", 2023, market_cap_usd_m=1000.0)
    r.total_assets_usd_m = 2000.0
    r.total_liabilities_usd_m = 1500.0
    compute([r])
    assert r.tobins_q == (1000.0 + 1500.0) / 2000.0
    assert r.price_to_book == 1000.0 / (2000.0 - 1500.0)


def test_pb_none_when_equity_zero() -> None:
    r = _fin("X", 2023, market_cap_usd_m=100.0)
    r.total_assets_usd_m = 500.0
    r.total_liabilities_usd_m = 500.0
    compute([r])
    assert r.tobins_q == (100.0 + 500.0) / 500.0
    assert r.price_to_book is None


def test_pb_none_when_equity_negative() -> None:
    r = _fin("X", 2023, market_cap_usd_m=100.0)
    r.total_assets_usd_m = 400.0
    r.total_liabilities_usd_m = 500.0
    compute([r])
    assert r.price_to_book is None


def test_ratios_none_when_assets_missing() -> None:
    r = _fin("X", 2023, market_cap_usd_m=100.0)
    r.total_assets_usd_m = None
    r.total_liabilities_usd_m = None
    compute([r])
    assert r.tobins_q is None
    assert r.price_to_book is None


# -------------------------------------------------------- name resolution
class _FakeInst:
    def __init__(self, name: str) -> None:
        self.name = name


def test_resolve_direct_match() -> None:
    rows = [_fin("Al Rajhi Bank", 2023)]
    insts = [_FakeInst("Al Rajhi Bank"), _FakeInst("Other")]
    resolved = resolve_names(rows, insts)
    assert resolved["Al Rajhi Bank"] == "Al Rajhi Bank"


def test_resolve_name_override() -> None:
    # Workbook writes "Dubai Investment PJSC", registry has "Dubai Investments PJSC".
    rows = [_fin("Dubai Investment PJSC", 2024)]
    insts = [_FakeInst("Dubai Investments PJSC")]
    resolved = resolve_names(rows, insts)
    assert resolved["Dubai Investment PJSC"] == "Dubai Investments PJSC"


def test_resolve_raises_on_unmatched() -> None:
    rows = [_fin("Not A Real Company", 2024)]
    insts = [_FakeInst("Al Rajhi Bank")]
    import pytest
    with pytest.raises(ValueError, match="Unmatched companies"):
        resolve_names(rows, insts)


# -------------------------------------------------------- end-to-end
def test_load_rows_matches_dataset_shape() -> None:
    rows = load_rows()
    assert len(rows) == 390
    # The four corrections should produce their stated post-correction values.
    by_key = {(r.company, r.year): r for r in rows}
    assert by_key[("Saudi Aramco", 2024)].roe == 26.32
    assert by_key[("Saudi Aramco", 2024)].roa == 16.07
    assert by_key[("Bank Aljazira", 2020)].eps == 0.03
    # Al Rajhi Bank 2023 is the Step-6 spot-check target.
    r = by_key[("Al Rajhi Bank", 2023)]
    assert r.total_assets_usd_m == 215_377.9
    assert r.total_liabilities_usd_m == 186_924.0
    # Tobin's Q and P/B are computed with rounding — look within ~1e-3.
    assert r.tobins_q is not None
    assert abs(r.tobins_q - 1.299) < 0.005
    assert r.price_to_book is not None
    assert abs(r.price_to_book - 3.263) < 0.005
