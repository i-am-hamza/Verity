"""Session 9: upload every PDF in storage/reports/ to R2 at the matching
object key, then re-download and sha256-verify before accepting the file
as migrated. Any mismatch stops that file, is reported, and the migration
continues with the remaining files. Non-matching files are listed at the
end for manual review.

Order is sha256-of-local-bytes, then upload, then sha256-of-downloaded-
bytes. The last compare is the one that matters: it proves R2 is holding
exactly the same bytes you had on disk, no in-flight corruption.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

# .env is loaded by Pydantic Settings for the FastAPI process; scripts
# don't trigger that path on their own, so load it explicitly here so
# R2_* env vars are present before the storage module reads them.
from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

from app.services.storage import R2Settings, _r2_client, r2_enabled  # noqa: E402

REPORTS_DIR = BACKEND / "storage" / "reports"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if not r2_enabled():
        print("R2 env vars not set (R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / "
              "R2_SECRET_ACCESS_KEY / R2_BUCKET_NAME). Nothing to do.")
        return 2
    client = _r2_client()
    bucket = R2Settings().bucket

    files = sorted(REPORTS_DIR.rglob("*.pdf"))
    print(f"files to upload: {len(files)}  bucket: {bucket}")

    uploaded = 0
    mismatches: list[tuple[str, str, str]] = []
    errors: list[tuple[str, str]] = []

    for i, path in enumerate(files, 1):
        key = str(path.relative_to(REPORTS_DIR)).replace("\\", "/")
        body = path.read_bytes()
        local_sha = _sha256(body)
        try:
            client.put_object(
                Bucket=bucket, Key=key, Body=body,
                ContentType="application/pdf",
            )
            obj = client.get_object(Bucket=bucket, Key=key)
            remote_sha = _sha256(obj["Body"].read())
        except Exception as exc:
            errors.append((key, f"{type(exc).__name__}: {exc}"))
            print(f"  [{i:3d}/{len(files)}] {key:<80} ERROR {exc}")
            continue
        if local_sha != remote_sha:
            mismatches.append((key, local_sha, remote_sha))
            print(f"  [{i:3d}/{len(files)}] {key:<80} MISMATCH "
                  f"local={local_sha[:12]} remote={remote_sha[:12]}")
            continue
        uploaded += 1
        if i % 10 == 0 or i == len(files):
            print(f"  [{i:3d}/{len(files)}] {key:<80} OK sha={remote_sha[:12]}")

    print()
    print(f"uploaded + verified: {uploaded}/{len(files)}")
    print(f"mismatches         : {len(mismatches)}")
    print(f"errors             : {len(errors)}")
    if mismatches:
        print()
        print("MISMATCHES:")
        for k, local_sha, remote_sha in mismatches:
            print(f"  {k}  local={local_sha[:12]} remote={remote_sha[:12]}")
    if errors:
        print()
        print("ERRORS:")
        for k, e in errors:
            print(f"  {k}  {e}")
    return 0 if (len(mismatches) == 0 and len(errors) == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
