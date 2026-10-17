"""
export_review_xlsx.py  --  Build docs/exports/financials_review.xlsx

One row per remaining flagged company-year (excluding rows whose ONLY flag
is FS_BOUNDARY_NOT_FOUND — those are the "truly no FS in PDF" cases).

Columns:
  slug, fiscal_year, flags, flag_types,
  then for each extracted field: _value, _page, _label, _confidence
  then computed ratios: leverage, roa, roe, net_profit_margin
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

# ---- config -----------------------------------------------------------------

CSV_IN   = REPO_ROOT / "docs" / "exports" / "financials_extracted.csv"
XLSX_OUT = REPO_ROOT / "docs" / "exports" / "financials_review.xlsx"

_FS_ONLY_RE = re.compile(r"^FS_BOUNDARY_NOT_FOUND[^;]*$")

_EV_FIELDS = [
    "total_assets",
    "total_liabilities",
    "total_equity",
    "equity_attributable",
    "revenue",
    "gross_income_bank",
    "net_profit",
    "net_profit_attributable",
    "eps_numerator",
    "basic_eps",
    "shares_outstanding",
    "shares_eps_note",
    # Debt components
    "st_borrowings",
    "lt_borrowings",
    "sukuk_bonds_notes",
    "lease_liabilities_nb",
    "due_to_banks_fi",
    "sukuk_issued_bank",
    "subordinated_debt_bank",
    "total_borrowings",
]

_RATIO_FIELDS = [
    "total_debt", "total_debt_status",
    "leverage", "leverage_alt",
    "roa", "roe", "net_profit_margin", "net_margin_alt",
    "equity_ordinary",
    "eps_in_fils_baisa",
]

_FLAG_PREFIXES = [
    "BS_MISMATCH",
    "NP_ATTR_GT_TOTAL",
    "EPS_MISMATCH",
    "ROE_NPA_FALLBACK",
    "LEVERAGE_NEGATIVE_EQUITY",
    "FS_BOUNDARY_NOT_FOUND",
    "OCR_HEAVY",
]


def _flag_types(flags_str: str) -> str:
    """Return comma-separated list of flag type codes."""
    if not flags_str:
        return ""
    types = []
    for f in flags_str.split(";"):
        f = f.strip()
        for p in _FLAG_PREFIXES:
            if f.startswith(p):
                if p not in types:
                    types.append(p)
                break
    return ", ".join(types)


def _is_true_no_fs(flags_str: str) -> bool:
    """True when the only flag is FS_BOUNDARY_NOT_FOUND (no FS in the PDF)."""
    if not flags_str:
        return False
    parts = [p.strip() for p in flags_str.split(";") if p.strip()]
    return all(p.startswith("FS_BOUNDARY_NOT_FOUND") for p in parts)


_ILLEGAL_XML_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f�￾￿]")


def _xl(val: object) -> object:
    if isinstance(val, str):
        return _ILLEGAL_XML_RE.sub("", val)
    return val


def main() -> int:
    with open(CSV_IN, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        all_rows = list(reader)

    # Filter: flagged and not pure FS_BOUNDARY_NOT_FOUND
    flagged = [
        r for r in all_rows
        if r.get("flags") and not _is_true_no_fs(r["flags"])
    ]
    print(f"Total rows in CSV     : {len(all_rows)}")
    print(f"Flagged (non-no-FS)   : {len(flagged)}")

    if not flagged:
        print("Nothing to export.")
        return 0

    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "review"

    # ---- build header --------------------------------------------------------
    cols: list[str] = []
    cols += ["slug", "fiscal_year", "is_bank", "currency", "unit", "flag_types", "flags"]
    for f in _EV_FIELDS:
        cols += [f"{f}_value", f"{f}_page", f"{f}_label", f"{f}_confidence"]
    cols += _RATIO_FIELDS

    # Colour-coded header by flag type
    HEADER_COLOURS = {
        "id":       "1F4E79",
        "ev":       "2E4057",
        "ratio":    "264653",
    }
    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(bold=True, color="FFFFFF")

    for col_i, col_name in enumerate(cols, start=1):
        cell = ws.cell(row=1, column=col_i, value=col_name)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # ---- colour scale for flag_types column ----------------------------------
    FLAG_FILL = {
        "BS_MISMATCH":              PatternFill("solid", fgColor="FFD700"),
        "NP_ATTR_GT_TOTAL":         PatternFill("solid", fgColor="FFA500"),
        "EPS_MISMATCH":             PatternFill("solid", fgColor="FF6B6B"),
        "ROE_NPA_FALLBACK":         PatternFill("solid", fgColor="C8E6C9"),
        "LEVERAGE_NEGATIVE_EQUITY": PatternFill("solid", fgColor="FF9999"),
        "FS_BOUNDARY_NOT_FOUND":    PatternFill("solid", fgColor="E0E0E0"),
        "OCR_HEAVY":                PatternFill("solid", fgColor="B0BEC5"),
    }
    ft_col_idx = cols.index("flag_types") + 1

    # ---- write rows ----------------------------------------------------------
    def _num(raw: str) -> object:
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            return raw

    for row_i, r in enumerate(sorted(flagged, key=lambda x: (x["slug"], x["fiscal_year"])), start=2):
        ft = _flag_types(r.get("flags", ""))
        row_vals: dict[str, object] = {
            "slug":        r["slug"],
            "fiscal_year": _num(r["fiscal_year"]),
            "is_bank":     r.get("is_bank"),
            "currency":    r.get("currency"),
            "unit":        r.get("unit"),
            "flag_types":  ft,
            "flags":       r.get("flags"),
        }
        for f in _EV_FIELDS:
            row_vals[f"{f}_value"]      = _num(r.get(f"{f}_value", ""))
            row_vals[f"{f}_page"]       = _num(r.get(f"{f}_page", ""))
            row_vals[f"{f}_label"]      = r.get(f"{f}_label")
            row_vals[f"{f}_confidence"] = r.get(f"{f}_confidence")
        for rf in _RATIO_FIELDS:
            row_vals[rf] = _num(r.get(rf, ""))

        for col_i, col_name in enumerate(cols, start=1):
            ws.cell(row=row_i, column=col_i, value=_xl(row_vals.get(col_name)))

        # Colour the flag_types cell
        ft_cell = ws.cell(row=row_i, column=ft_col_idx)
        for flag_key, fill in FLAG_FILL.items():
            if flag_key in ft:
                ft_cell.fill = fill
                break

    # ---- column widths -------------------------------------------------------
    for col_i, col_name in enumerate(cols, start=1):
        if "_label" in col_name:
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_i)].width = 40
        elif col_name in ("slug", "flags"):
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_i)].width = 55
        elif col_name == "flag_types":
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_i)].width = 35
        else:
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_i)].width = max(12, len(col_name) + 2)

    # ---- freeze header row ---------------------------------------------------
    ws.freeze_panes = "A2"

    wb.save(XLSX_OUT)
    print(f"XLSX -> {XLSX_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
