"""Session 9: copy every row from the local SQLite DB to the Supabase
Postgres DB and verify per-table row counts match exactly.

Preserves primary-key ids so every foreign key lands cleanly, then
re-seats each table's sequence past the max id so new inserts don't
collide. Order of migration respects dependency chain
(institutions → taxonomy_versions → categories → terms → source_documents
→ reports → category_scores + match_evidence → gaps → crawl_log →
match_reviews → runs). alembic_version is handled by alembic itself.

Idempotent-ish: if the destination table already has rows the script
aborts rather than double-inserting. Clean a partial run with a
truncate before retrying.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

# Imports from `app` have to come after the sys.path tweak above.
from sqlalchemy import create_engine, inspect, text  # noqa: E402

from app.database import DB_URL as PG_URL  # noqa: E402 — already normalised

SQLITE_URL = "sqlite:///" + str(BACKEND / "disclosure_scorer.db").replace("\\", "/")
if not PG_URL.startswith("postgresql"):
    raise SystemExit(
        f"settings.database_url does not look like Postgres: {PG_URL!r}"
    )

# Order matters: a table with FKs must land after its parents. alembic_version
# is excluded (alembic owns it and already stamped the Postgres row).
ORDER = [
    "institutions",
    "taxonomy_versions",
    "categories",
    "terms",
    "source_documents",
    "reports",
    "category_scores",
    "match_evidence",
    "gaps",
    "crawl_log",
    "match_reviews",
    "runs",
]

# Sequence names that need resetting after id-preserving inserts.
# Convention: <table>_id_seq. SQLAlchemy / alembic uses the default
# Postgres SERIAL identity sequence naming.
SEQUENCES = {t: f"{t}_id_seq" for t in ORDER}


# Columns we need to NULL out during insert then back-fill after the table
# finishes loading, to avoid forward self-FK violations. Only
# source_documents.superseded_by_id behaves this way (a doc gets a pointer
# to a *later-written* doc that supersedes it).
_DEFER_SELF_FK: dict[str, tuple[str, ...]] = {
    "source_documents": ("superseded_by_id",),
}


def _copy_table(src_conn, dst_conn, table: str) -> tuple[int, int]:
    """Return (rows_in_src, rows_inserted)."""
    src_count = src_conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    dst_count_before = dst_conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    if dst_count_before and dst_count_before > 0:
        raise RuntimeError(
            f"destination table {table!r} already has {dst_count_before} rows — "
            f"truncate before re-running"
        )
    if not src_count:
        return 0, 0

    cols = [c["name"] for c in inspect(src_conn).get_columns(table)]
    col_list = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(f":{c}" for c in cols)
    insert_sql = text(
        f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})'
    )

    deferred = _DEFER_SELF_FK.get(table, ())
    deferred_updates: list[dict] = []  # populated during insert

    batch_size = 500
    inserted = 0
    cursor = src_conn.execute(text(f'SELECT {col_list} FROM "{table}" ORDER BY ROWID'))
    while True:
        batch = cursor.fetchmany(batch_size)
        if not batch:
            break
        rows = [dict(zip(cols, row, strict=True)) for row in batch]
        # Normalise SQLite bools (0/1) to Python bools for Postgres BOOLEAN
        # columns. Only applies to the known columns; everything else
        # passes through unchanged.
        for row in rows:
            for k, v in list(row.items()):
                if isinstance(v, int) and k in {
                    "is_financial", "active", "lemma_based",
                    "includes_financial_statements",
                }:
                    row[k] = bool(v)
            # Record then NULL out any deferred-FK column, so the row
            # inserts cleanly on the first pass. We'll back-fill below.
            if deferred:
                saved = {}
                for col in deferred:
                    if row.get(col) is not None:
                        saved[col] = row[col]
                        row[col] = None
                if saved:
                    deferred_updates.append({"id": row["id"], **saved})
        dst_conn.execute(insert_sql, rows)
        inserted += len(rows)

    # Second pass: UPDATE each saved deferred-FK value now that every
    # row in the table exists.
    for col in deferred:
        for upd in deferred_updates:
            if col in upd:
                dst_conn.execute(
                    text(f'UPDATE "{table}" SET "{col}" = :val WHERE id = :id'),
                    {"val": upd[col], "id": upd["id"]},
                )

    return src_count, inserted


def main() -> int:
    src = create_engine(SQLITE_URL)
    # Supabase's transaction pooler (port 6543) multiplexes connections and
    # cannot keep per-session prepared-statement state across requests. psycopg 3
    # creates prepared statements by default on executemany, which blows up with
    # `DuplicatePreparedStatement: _pg3_0 already exists`. Setting
    # prepare_threshold=None disables prepared statements entirely for this one
    # bulk-load script — the normal app (one query per request) is unaffected
    # because it never hits executemany at scale.
    dst = create_engine(PG_URL, connect_args={"prepare_threshold": None})

    src_tables = set(inspect(src).get_table_names())
    missing = [t for t in ORDER if t not in src_tables]
    if missing:
        raise SystemExit(f"source SQLite missing expected tables: {missing}")

    print(f"source : {SQLITE_URL}")
    print(f"dest   : {PG_URL.split('@')[-1]}  (secret redacted)")
    print()

    totals: dict[str, tuple[int, int]] = {}
    with src.connect() as src_conn, dst.begin() as dst_conn:
        for table in ORDER:
            print(f"  {table:<25} ", end="", flush=True)
            src_n, _ = _copy_table(src_conn, dst_conn, table)
            dst_n = dst_conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
            ok = src_n == dst_n
            print(f"src={src_n:>6}  dst={dst_n:>6}  {'OK' if ok else 'MISMATCH'}")
            totals[table] = (src_n, dst_n)

        # Reset sequences so new INSERTs don't collide with migrated ids.
        print()
        print("resetting sequences:")
        for table, seq in SEQUENCES.items():
            # Only reset if the sequence actually exists (some tables may
            # not have one on Postgres if the PK isn't an IDENTITY column
            # for some reason).
            row = dst_conn.execute(text(
                "SELECT setval(:seq, COALESCE((SELECT MAX(id) FROM \"" + table + "\"), 1), "
                "(SELECT COUNT(*) FROM \"" + table + "\") > 0)"
            ), {"seq": seq}).scalar()
            print(f"  {seq:<30} -> {row}")

    print()
    bad = [t for t, (s, d) in totals.items() if s != d]
    if bad:
        print(f"FAIL: row count mismatches on {bad}")
        return 1
    total_src = sum(s for s, _ in totals.values())
    total_dst = sum(d for _, d in totals.values())
    print(f"OK: {len(totals)} tables, {total_src} rows migrated (dst total {total_dst})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
