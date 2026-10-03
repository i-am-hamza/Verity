"""Block-page detection on fixture strings — no network."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.crawler.fetch import BLOCK_MARKERS, Fetcher


def test_cloudflare_just_a_moment_detected():
    body = b"<title>Just a moment...</title><body>cf-browser-verification</body>"
    assert Fetcher.is_block_body(body)


def test_akamai_access_denied_detected():
    body = (
        b"<html><body>Access Denied\n"
        b"You don't have permission to access ... on this server.\n"
        b"Reference #18.ea779452.65bdd79</body></html>"
    )
    assert Fetcher.is_block_body(body)


def test_f5_asm_rejected_url_detected():
    body = b"The requested URL was rejected. Please consult with your administrator."
    assert Fetcher.is_block_body(body)


def test_normal_annual_report_html_not_flagged():
    body = (
        b"<html><body><h1>Investor Relations</h1>"
        b"<a href=\"ar2024.pdf\">Annual Report 2024</a></body></html>"
    )
    assert not Fetcher.is_block_body(body)


def test_all_markers_are_lowercase_already():
    # Markers are compared against a lower-cased sample; must be lower.
    for m in BLOCK_MARKERS:
        assert m == m.lower(), f"marker {m!r} is not lowercased"
