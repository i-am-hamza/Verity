"""Unit tests for the completeness guard helper in batch_runner.

No DB, no workers needed — pure set arithmetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.batch_runner import _missing_sd_ids


def test_no_missing():
    assert _missing_sd_ids({1, 2, 3}, {1, 2, 3}) == set()


def test_one_missing():
    assert _missing_sd_ids({1, 2, 3}, {1, 2}) == {3}


def test_all_missing():
    assert _missing_sd_ids({5, 6}, set()) == {5, 6}


def test_empty_batch():
    assert _missing_sd_ids(set(), set()) == set()


def test_extra_found_ignored():
    # found may contain IDs outside the processed set (old pipeline versions); ignore them
    assert _missing_sd_ids({1, 2}, {1, 2, 99}) == set()
