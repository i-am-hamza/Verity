"""HTTP + Playwright fetch layer.

- `Fetcher.get(url)` returns a FetchResult. Plain HTTP via `requests`.
  Falls back to Playwright on explicit request (`Fetcher.get(url, render=True)`),
  used when the static HTML has no report links.
- robots.txt is fetched once per host, cached, obeyed. A disallowed path
  returns outcome="robots_disallowed" without hitting the real URL.
- Politeness: 2 seconds (or robots.txt Crawl-delay, whichever is longer)
  between consecutive requests to the same host. One in-flight request
  per host is implicit — the fetcher is single-threaded.
- Retries: three attempts with exponential backoff on 5xx and timeouts
  only. 4xx is NOT retried (it's a definitive answer). 429 is retried up
  to the retry cap; after that it's treated as a block.
- Block detection: 403, repeated 429, or any of a known set of
  challenge-page markers in the response body. On detection, the host is
  marked blocked for the rest of this Fetcher's lifetime, and the caller
  gets outcome="blocked" without further requests to that host.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from playwright.sync_api import sync_playwright

from app.crawler.config import MAX_RETRIES, PER_DOMAIN_DELAY_SECONDS, make_user_agent

log = logging.getLogger("verity.crawler.fetch")

# Lowercased markers that strongly indicate an interstitial / block page.
BLOCK_MARKERS: tuple[str, ...] = (
    "captcha",
    "just a moment",
    "access denied",
    "verify you are human",
    "attention required",      # Cloudflare
    "cf-browser-verification",
    "cf_chl",                   # Cloudflare challenge token
    "akamai",                   # Akamai edge messages
    "incapsula",
    "please enable javascript and cookies",
    "the requested url was rejected",  # F5 ASM
)


@dataclass
class FetchResult:
    url: str
    final_url: str | None = None
    status: int | None = None
    body: bytes = b""
    content_type: str | None = None
    outcome: str = "ok"
    # "ok" | "blocked" | "robots_disallowed" | "error" | "not_found" (404)
    detail: str | None = None
    rendered: bool = False


@dataclass
class Fetcher:
    """One Fetcher per crawl run. State (robots cache, blocked hosts,
    last-hit timestamps) is run-scoped — a new run starts fresh."""
    user_agent: str = field(default_factory=make_user_agent)
    session: requests.Session = field(default_factory=requests.Session)
    _robots: dict[str, RobotFileParser | None] = field(default_factory=dict)
    _crawl_delay: dict[str, float] = field(default_factory=dict)
    _last_hit: dict[str, float] = field(default_factory=dict)
    _blocked: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
            "Accept-Language": "en;q=0.9, ar;q=0.3",
        })

    # ------------------------------------------------------------------ robots
    def _get_robots(self, host: str, scheme: str) -> RobotFileParser | None:
        if host in self._robots:
            return self._robots[host]
        rp = RobotFileParser()
        robots_url = f"{scheme}://{host}/robots.txt"
        rp.set_url(robots_url)
        try:
            # Use our own GET so robots.txt also travels under the honest UA.
            resp = self.session.get(robots_url, timeout=15)
            if resp.status_code >= 400:
                self._robots[host] = None
                return None
            rp.parse(resp.text.splitlines())
            self._robots[host] = rp
            # Record crawl delay if specified.
            cd = rp.crawl_delay(self.user_agent) or rp.crawl_delay("*")
            if cd:
                self._crawl_delay[host] = max(float(cd), PER_DOMAIN_DELAY_SECONDS)
        except (requests.RequestException, UnicodeDecodeError) as exc:
            # Absence of robots.txt (or malformed one) is "no restrictions" per
            # the standard. We log and treat as no-rules.
            log.warning("robots.txt fetch failed for %s: %s", host, exc)
            self._robots[host] = None
        return self._robots[host]

    def _robots_allow(self, url: str) -> bool:
        p = urlparse(url)
        if p.path.endswith("/robots.txt"):
            return True  # don't recurse
        rp = self._get_robots(p.netloc, p.scheme)
        if rp is None:
            return True
        return rp.can_fetch(self.user_agent, url)

    # -------------------------------------------------------- politeness delay
    def _wait(self, host: str) -> None:
        min_delay = self._crawl_delay.get(host, PER_DOMAIN_DELAY_SECONDS)
        last = self._last_hit.get(host, 0.0)
        now = time.time()
        gap = min_delay - (now - last)
        if gap > 0:
            time.sleep(gap)
        self._last_hit[host] = time.time()

    # ------------------------------------------------------- block / challenge
    @staticmethod
    def is_block_body(body: bytes) -> bool:
        """True if the body looks like a bot-check / challenge / block page."""
        if not body:
            return False
        # Only inspect a reasonable prefix — challenge pages are small.
        sample = body[:8192].lower()
        try:
            text = sample.decode("utf-8", errors="ignore")
        except Exception:
            return False
        return any(m in text for m in BLOCK_MARKERS)

    def _block_host(self, host: str, reason: str) -> None:
        log.info("blocking host %s for the rest of this run: %s", host, reason)
        self._blocked.add(host)

    def is_blocked(self, host: str) -> bool:
        return host in self._blocked

    # ------------------------------------------------------------------- HTTP
    def get(self, url: str, *, render: bool = False) -> FetchResult:
        host = urlparse(url).netloc
        if host in self._blocked:
            return FetchResult(url=url, outcome="blocked", detail="host blocked earlier this run")
        if not self._robots_allow(url):
            return FetchResult(url=url, outcome="robots_disallowed",
                               detail="robots.txt disallows this path for our UA")

        if render:
            return self._get_playwright(url)
        return self._get_requests(url)

    def _get_requests(self, url: str) -> FetchResult:
        host = urlparse(url).netloc
        last_error: str | None = None
        for attempt in range(MAX_RETRIES):
            self._wait(host)
            try:
                resp = self.session.get(url, timeout=30, allow_redirects=True)
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5 * (2 ** attempt))
                    continue
                return FetchResult(url=url, outcome="error", detail=last_error)

            status = resp.status_code
            # 429: back off, retry; after MAX_RETRIES treat as block.
            if status == 429:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(10 * (2 ** attempt))
                    continue
                self._block_host(host, "repeated HTTP 429")
                return FetchResult(url=url, final_url=resp.url, status=status, body=resp.content,
                                   outcome="blocked", detail="repeated 429")

            # 403: definitive block, do not retry.
            if status == 403:
                self._block_host(host, "HTTP 403")
                return FetchResult(url=url, final_url=resp.url, status=status, body=resp.content,
                                   outcome="blocked", detail="HTTP 403")

            # 5xx: retry on backoff.
            if 500 <= status < 600:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5 * (2 ** attempt))
                    continue
                return FetchResult(url=url, final_url=resp.url, status=status, body=resp.content,
                                   outcome="error", detail=f"HTTP {status}")

            if status == 404:
                return FetchResult(url=url, final_url=resp.url, status=status, body=resp.content,
                                   content_type=resp.headers.get("content-type"),
                                   outcome="not_found")

            # 2xx/3xx with body: check for a challenge page before accepting.
            if self.is_block_body(resp.content):
                self._block_host(host, "challenge-page markers in body")
                return FetchResult(url=url, final_url=resp.url, status=status, body=resp.content,
                                   outcome="blocked", detail="challenge-page markers in body")

            return FetchResult(
                url=url, final_url=resp.url, status=status, body=resp.content,
                content_type=resp.headers.get("content-type"), outcome="ok",
            )
        # Should not reach here.
        return FetchResult(url=url, outcome="error", detail=last_error or "exhausted retries")

    # -------------------------------------------------------------- Playwright
    def _get_playwright(self, url: str) -> FetchResult:
        host = urlparse(url).netloc
        self._wait(host)
        html = ""
        status: int | None = None
        final_url: str | None = None
        try:
            with self._playwright_browser() as ctx:
                page = ctx.new_page()
                resp = page.goto(url, wait_until="domcontentloaded", timeout=25000)
                final_url = page.url
                status = resp.status if resp else None
                # Playwright is READ-only (CLAUDE.md). Give the SPA time to populate.
                page.wait_for_timeout(4000)
                html = page.content()
        except Exception as exc:
            return FetchResult(url=url, outcome="error", detail=f"playwright {type(exc).__name__}: {exc}",
                               rendered=True)

        body = html.encode("utf-8", errors="replace")
        if status is not None and status == 403:
            self._block_host(host, "HTTP 403 (Playwright)")
            return FetchResult(url=url, final_url=final_url, status=status, body=body,
                               outcome="blocked", detail="HTTP 403 (Playwright)", rendered=True)
        if self.is_block_body(body):
            self._block_host(host, "challenge markers in Playwright body")
            return FetchResult(url=url, final_url=final_url, status=status, body=body,
                               outcome="blocked", detail="challenge markers", rendered=True)

        return FetchResult(
            url=url, final_url=final_url, status=status, body=body,
            content_type="text/html", outcome="ok", rendered=True,
        )

    @contextmanager
    def _playwright_browser(self) -> Iterator:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1366, "height": 900},
                locale="en-US",
            )
            try:
                yield ctx
            finally:
                browser.close()


def resolve(base: str, href: str) -> str:
    """Absolute URL from an href that may be relative."""
    return urljoin(base, href.strip())


def same_registered_host(a: str, b: str) -> bool:
    """Loose host comparison: match on last two labels (foo.bar.example.com
    and bar.example.com both end in example.com → match)."""
    def tail(host: str) -> str:
        parts = host.lower().split(".")
        return ".".join(parts[-2:]) if len(parts) >= 2 else host.lower()

    return tail(urlparse(a).netloc) == tail(urlparse(b).netloc)
