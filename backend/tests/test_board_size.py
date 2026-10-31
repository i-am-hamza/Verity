"""Tests for the board-size loader (scripts/extract_board_size.py).

Covers the pure-logic functions: flag computation (not_found,
out_of_range, big_change, STATED_LIST_MISMATCH, low_confidence,
needs_annotation) and the names-string parser.

The DB-touching paths (write_db, load_ages) are exercised end-to-end
by running the loader against the test DB via Alembic in CI.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent

# Load the script module from scripts/ (not a package).
_spec = importlib.util.spec_from_file_location(
    "extract_board_size",
    BACKEND / "scripts" / "extract_board_size.py",
)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("extract_board_size", _mod)
_spec.loader.exec_module(_mod)

Row = _mod.Row
compute_flags = _mod.compute_flags
_parse_names = _mod._parse_names


def _row(**kw) -> Row:
    """Build a Row with sensible defaults."""
    defaults = dict(
        slug="acme", fiscal_year=2023, board_size=9,
        basis="stated_number_and_list", confidence="high",
        pages="12", names="A; B; C",
        stated_number=9, list_count=9,
        flag="", note="", method="read",
    )
    defaults.update(kw)
    return Row(**defaults)


def test_parse_names_splits_on_semicolon() -> None:
    assert _parse_names("A; B; C") == ["A", "B", "C"]


def test_parse_names_strips_whitespace() -> None:
    assert _parse_names("  A ; B ") == ["A", "B"]


def test_parse_names_empty_returns_none() -> None:
    assert _parse_names("") is None
    assert _parse_names("   ") is None


def test_flags_clean_row_has_no_flags() -> None:
    annots = [_row()]
    result = compute_flags(annots)
    assert result[0][1] == []


def test_flags_not_found_sets_flag() -> None:
    annots = [_row(basis="not_found", board_size=None, confidence="low")]
    _, flags = compute_flags(annots)[0]
    assert "not_found" in flags


def test_flags_out_of_range_small() -> None:
    annots = [_row(board_size=2, list_count=2)]
    _, flags = compute_flags(annots)[0]
    assert "out_of_range" in flags


def test_flags_out_of_range_large() -> None:
    annots = [_row(board_size=21, list_count=21)]
    _, flags = compute_flags(annots)[0]
    assert "out_of_range" in flags


def test_flags_in_range_boundaries() -> None:
    for size in (3, 20):
        annots = [_row(board_size=size, list_count=size)]
        _, flags = compute_flags(annots)[0]
        assert "out_of_range" not in flags


def test_flags_big_change_more_than_three() -> None:
    annots = [
        _row(slug="acme", fiscal_year=2022, board_size=9, list_count=9),
        _row(slug="acme", fiscal_year=2023, board_size=13, list_count=13),
    ]
    flagged = compute_flags(annots)
    # Pick the 2023 row.
    row23 = next(fs for r, fs in flagged if r.fiscal_year == 2023)
    assert "big_change" in row23


def test_flags_change_of_three_is_not_flagged() -> None:
    annots = [
        _row(slug="acme", fiscal_year=2022, board_size=9, list_count=9),
        _row(slug="acme", fiscal_year=2023, board_size=12, list_count=12),
    ]
    flagged = compute_flags(annots)
    row23 = next(fs for r, fs in flagged if r.fiscal_year == 2023)
    assert "big_change" not in row23


def test_flags_stated_list_mismatch() -> None:
    annots = [_row(flag="STATED_LIST_MISMATCH stated=10 list=9")]
    _, flags = compute_flags(annots)[0]
    assert "stated_list_mismatch" in flags


def test_flags_low_confidence() -> None:
    annots = [_row(confidence="low")]
    _, flags = compute_flags(annots)[0]
    assert "low_confidence" in flags


def test_flags_needs_annotation() -> None:
    annots = [_row(flag="needs_annotation", basis="not_found", board_size=None)]
    _, flags = compute_flags(annots)[0]
    assert "needs_annotation" in flags
    assert "not_found" in flags


def test_flags_order_independent() -> None:
    """compute_flags must sort rows per-company by fiscal_year even when
    the input list is shuffled."""
    annots = [
        _row(slug="acme", fiscal_year=2023, board_size=13, list_count=13),
        _row(slug="acme", fiscal_year=2022, board_size=9, list_count=9),
    ]
    flagged = compute_flags(annots)
    row23 = next(fs for r, fs in flagged if r.fiscal_year == 2023)
    assert "big_change" in row23
