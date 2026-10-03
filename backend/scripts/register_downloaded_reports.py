"""
register_downloaded_reports.py

Feeds crawler output into the running API: for every PDF the crawler
downloaded, POSTs it to /reports so it enters the normal ingestion
pipeline (extraction -> matching -> scoring). Institutions must already
exist (POST /institutions) before running this -- the id map below is
what connects a crawler slug to a real institution_id.

Usage (from backend/, with the API running separately):
    python scripts/register_downloaded_reports.py \
        --summary storage/reports/crawl_summary.json \
        --institution-map scripts/institution_id_map.json \
        --api http://localhost:8000

institution_id_map.json is just: {"al-rajhi-bank": 3, "emirates-nbd": 7, ...}
-- one entry per slug in institutions_config.json, filled in after you've
created each institution via POST /institutions and noted the id it returned.
"""
import argparse
import json
from pathlib import Path

import requests


def main(summary_path: str, id_map_path: str, api_base: str):
    summary = json.loads(Path(summary_path).read_text())
    id_map = json.loads(Path(id_map_path).read_text())

    for entry in summary:
        slug = entry.get("slug")
        institution_id = id_map.get(slug)
        if institution_id is None:
            print(f"SKIP {entry['institution']}: no institution_id in map for slug '{slug}'")
            continue

        for d in entry["downloaded"]:
            with open(d["path"], "rb") as f:
                resp = requests.post(
                    f"{api_base}/reports",
                    data={"institution_id": institution_id, "fiscal_year": d["year"], "language": "en"},
                    files={"file": f},
                )
            if resp.ok:
                print(f"OK   {entry['institution']} {d['year']} -> report_id {resp.json()['id']}")
            else:
                print(f"FAIL {entry['institution']} {d['year']}: {resp.status_code} {resp.text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="storage/reports/crawl_summary.json")
    parser.add_argument("--institution-map", required=True)
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()
    main(args.summary, args.institution_map, args.api)
