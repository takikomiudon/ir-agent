#!/usr/bin/env python3
"""One-shot public IR directory research; never submits forms or sends mail.

Discovery seeds are not contact evidence. Each company has a bounded, resumable
GET investigation; the original 49-company research remains immutable.
Requires requests from the repository's optional data environment.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import os
import re
import tempfile
import threading
import time
import unicodedata
import sys
from collections import Counter
from datetime import datetime, timezone
from email.message import Message
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urldefrag, urljoin, urlparse, urlsplit, urlunparse
from urllib.robotparser import RobotFileParser

import requests
from protego import Protego

USER_AGENT = "ir-agent-public-research/0.1"
IR = re.compile(r"(?<![A-Za-z0-9])IR(?![A-Za-z0-9])|ＩＲ|投資家|investor|investor relations", re.I)
CONTACT = re.compile(r"お問い合わせ|お問合せ|お問い合せ|問合せ|問い合わせ|contact|inquir|ご質問", re.I)
IR_CONTACT = re.compile(
    r"(?:(?<![A-Za-z0-9])IR(?![A-Za-z0-9])|ＩＲ|投資家|investor)[^。\n]{0,55}(?:お問い合わせ|問合せ|問い合わせ|contact|inquir)|"
    r"(?:お問い合わせ|問合せ|問い合わせ|contact|inquir)[^。\n]{0,55}(?:(?<![A-Za-z0-9])IR(?![A-Za-z0-9])|ＩＲ|投資家|investor)", re.I)
EMAIL = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SKIP_URL = re.compile(r"\.(?:pdf|zip|xlsx?|csv|docx?|pptx?|png|jpe?g|gif|svg|css|js|mp4)(?:$|\?)", re.I)
IR_PATH = re.compile(r"(?:^|[/_.-])(?:ir|investors?|shareholders?)(?:$|[/_.-])", re.I)
CONTACT_PATH = re.compile(r"contact|inquir|toiawase|otoiawase|query|form", re.I)
NO_REPLY = re.compile(r"個別.{0,35}(?:回答しない|回答.{0,8}行っておりません|回答.{0,8}いたしません|対応.{0,8}行っておりません)")
RESTRICTION = re.compile(r"(?:機関投資家|アナリスト).{0,55}(?:限定|専用|のみ|対象)|(?:個人投資家|個人).{0,40}(?:受け付けておりません|受付.{0,8}行っておりません)")
CONDITIONS = re.compile(r"沈黙期間|サイレント|quiet period|フェア.{0,2}ディスクロ|非公開|未公表|未公開|重要事実|転載|二次利用|転用|機関投資家|アナリスト|個別.{0,30}(?:回答|対応)|会社名|所属|個人投資家|株価", re.I)
PRIVACY_START = re.compile(r"個人情報保護方針|プライバシーポリシー|個人情報.{0,8}(?:取扱|取り扱|保護)", re.I)
IR_DEFLECTION = re.compile(r"(?:なお、)?IR(?:情報)?について[^。]{0,120}(?:IRページ|IRサイト)[^。]{0,80}(?:。|$)", re.I)
TRANSPORT_FAILURE = re.compile(r"Invalid argument\|remote address:envoy://cloudflare_(?:https|http)_tunnel/|upstream connect error")
SAFE_RESPONSE_HEADERS = {
    "retry-after", "ratelimit", "ratelimit-limit", "ratelimit-remaining", "ratelimit-reset", "ratelimit-policy",
    "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset", "x-ratelimit-used",
    "server", "date", "via", "request-id", "x-request-id", "x-correlation-id", "cf-ray", "x-amzn-trace-id", "traceparent",
}
REQUEST_METADATA_FIELDS = (
    "requested_url", "url", "http_status", "redirect_target", "redirect_error", "retrieved_at", "http_get_attempted",
    "http_get_started_at", "http_response_received_at", "http_get_completed_at", "http_get_elapsed_seconds",
    "host_wait_seconds", "global_wait_seconds", "wait_seconds", "global_rps_at_dispatch",
    "response_headers", "retry_after_seconds", "failure_signature", "error",
    "raw_file", "raw_sha256", "raw_storage_status", "raw_storage_error",
    "raw_body_completed_at", "raw_entity_semantics", "raw_file_path_basis",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def retry_after_seconds(value: str | None, received_at: str) -> float | None:
    if not value:
        return None
    try:
        seconds = float(value)
        return max(0.0, seconds) if math.isfinite(seconds) else None
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                return None
            return max(0.0, (parsed - datetime.fromisoformat(received_at)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def request_metadata(result: dict) -> dict:
    return {key: result[key] for key in REQUEST_METADATA_FIELDS if key in result}


def transport_failure_observed(page: dict) -> bool:
    """Include robots/redirect transport observations, not just company content."""
    if TRANSPORT_FAILURE.search(page.get("text", "")) or page.get("error") in (
        "ProxyError", "ReadTimeout", "ConnectionError", "ConnectTimeout", "SSLError",
        "ChunkedEncodingError", "Timeout", "RequestException", "environment_circuit_breaker_open",
    ) or page.get("failure_signature") in (
        "common_transport_503", "site_tls_503", "site_connection_termination_503",
    ):
        return True
    robots = page.get("robots")
    if isinstance(robots, dict) and transport_failure_observed(robots):
        return True
    return any(transport_failure_observed(hop) for hop in page.get("redirects", []) if isinstance(hop, dict))



def _literal_robots_decision(parser: RobotFileParser, useragent: str, url: str) -> tuple[bool, bool]:
    """Preserve stdlib group/URI selection; order only simple literal rules.

    The second result proves a FIRST-match block was overridden by a strictly
    longer Allow. Ties allow fresh reads but do not clear saved denial events.
    Pattern groups retain the legacy result as an upper bound; callers also
    apply the separate deny-only Protego guard below.
    """
    legacy = parser.can_fetch(useragent, url)
    if parser.disallow_all or parser.allow_all or not parser.mtime():
        return legacy, False
    entry = next((e for e in parser.entries if e.applies_to(useragent)), parser.default_entry)
    if entry is None or any("*" in unquote(r.path) or "$" in unquote(r.path) for r in entry.rulelines):
        return legacy, False
    # These are the same transformations used by RobotFileParser.can_fetch.
    parsed = urlparse(unquote(url))
    path = quote(urlunparse(("", "", parsed.path, parsed.params, parsed.query, parsed.fragment))) or "/"
    matching = [r for r in entry.rulelines if r.applies_to(path)]
    if not matching:
        return legacy, False
    best = max(matching, key=lambda r: (len(r.path), r.allowance))
    disallow_length = max((len(r.path) for r in matching if not r.allowance), default=-1)
    correction = not legacy and best.allowance and len(best.path) > disallow_length
    return bool(best.allowance), bool(correction)


class _RawRobotsParser(RobotFileParser):
    def parse(self, lines):
        raw_lines = list(lines)
        first_parse = not getattr(self, "_ir_parse_seen", False)
        self._ir_parse_seen = True
        self._ir_raw_robots_text = None
        super().parse(raw_lines)
        # stdlib parse() appends rather than replacing all prior groups.
        # Reparsed mutable objects no longer have a single proven raw policy.
        if first_parse:
            self._ir_raw_robots_text = "\n".join(raw_lines)


def parse_robots(raw_text: str) -> RobotFileParser:
    """Keep exact directive text for the pattern library; never reconstruct it
    by unquoting stdlib paths (which loses escaped literal '*' and '$').
    """
    if not isinstance(raw_text, str):
        raise ValueError("robots raw text must be a string")
    parser = _RawRobotsParser()
    parser.parse(raw_text.splitlines())
    parser._ir_raw_robots_text = raw_text
    return parser


def _pattern_robots_guard(parser: RobotFileParser, useragent: str, url: str) -> bool:
    entry = next((e for e in parser.entries if e.applies_to(useragent)), parser.default_entry)
    if entry is None or not any("*" in unquote(r.path) or "$" in unquote(r.path)
                                for r in entry.rulelines):
        return True
    raw = getattr(parser, "_ir_raw_robots_text", None)
    if not isinstance(raw, str):
        return False  # stdlib's encoded rules do not establish original patterns.
    # Use stdlib itself to bind original directives to the selected legacy
    # group's rules. Do not reimplement RFC matching or choose Protego's
    # different user-agent/group-merging policy. Ambiguous raw bindings stop.
    directives = {}
    for line in raw.splitlines():
        line = line.split("#", 1)[0].strip()
        single = RobotFileParser()
        single.parse(["User-agent: *", line])
        if single.default_entry and len(single.default_entry.rulelines) == 1:
            rule = single.default_entry.rulelines[0]
            directives.setdefault((rule.path, rule.allowance), set()).add(line)
    selected = []
    for rule in entry.rulelines:
        candidates = directives.get((rule.path, rule.allowance), set())
        if len(candidates) != 1:
            return False
        selected.append(next(iter(candidates)))
    try:
        return Protego.parse("User-agent: *\n" + "\n".join(selected)).can_fetch(url, useragent)
    except (TypeError, ValueError):
        return False


def robots_can_fetch(parser: RobotFileParser, useragent: str, url: str) -> bool:
    allowed = _literal_robots_decision(parser, useragent, url)[0]
    return allowed and _pattern_robots_guard(parser, useragent, url)


def robots_specific_allow_correction(parser: RobotFileParser, useragent: str, url: str) -> bool:
    """A saved first-match block has an explicit, strictly longer literal Allow."""
    return _literal_robots_decision(parser, useragent, url)[1]


def identity_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"株式会社|有限会社|\(株\)|ホールディングス|holdings", "", value)
    return re.sub(r"[^\wぁ-んァ-ン一-龥]", "", value)


def http_url(value: str) -> str | None:
    value = urldefrag(value.strip())[0]
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        return None
    if SKIP_URL.search(value) or parsed.hostname in ("localhost", "127.0.0.1"):
        return None
    return value


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[dict] = []
        self.base_hrefs: list[str] = []
        self.forms: list[dict] = []
        self.headings: list[str] = []
        self.title_parts: list[str] = []
        self.suppressed: list[str] = []
        self.anchor: dict | None = None
        self.form: dict | None = None
        self.heading: list[str] | None = None
        self.in_title = False
        self.control: dict | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style", "svg", "noscript"):
            self.suppressed.append(tag)
        if self.suppressed:
            return
        if tag == "title":
            self.in_title = True
        if tag in ("h1", "h2", "h3"):
            self.heading = []
        if tag == "base" and "href" in attrs:
            self.base_hrefs.append(attrs["href"] or "")
        if tag == "a" and attrs.get("href"):
            self.anchor = {"href": attrs["href"], "label": attrs.get("title") or ""}
        if tag == "img" and attrs.get("alt"):
            if self.anchor is not None:
                self.anchor["label"] += " " + attrs["alt"]
        if tag == "iframe" and attrs.get("src"):
            self.links.append({"href": attrs["src"], "attribute": "src", "label": "embedded frame"})
        if tag == "form":
            self.form = {"action": attrs.get("action"), "method": attrs.get("method", "get"), "controls": [], "parts": []}
            self.forms.append(self.form)
        if self.form is not None and tag in ("input", "textarea", "select") and attrs.get("type", "").lower() != "hidden":
            self.control = {"tag": tag, **{k: attrs[k] for k in ("type", "name", "required", "placeholder", "aria-label", "id") if k in attrs}}
            self.form["controls"].append(self.control)

    def handle_endtag(self, tag):
        if self.suppressed:
            if tag == self.suppressed[-1]:
                self.suppressed.pop()
            return
        if tag == "title":
            self.in_title = False
        if tag in ("h1", "h2", "h3") and self.heading is not None:
            self.headings.append(clean(" ".join(self.heading)))
            self.heading = None
        if tag == "a" and self.anchor is not None:
            self.links.append(self.anchor)
            self.anchor = None
        if tag == "form":
            self.form = None
        if tag in ("input", "textarea", "select"):
            self.control = None

    def handle_data(self, data):
        if self.suppressed or not data.strip():
            return
        self.parts.append(data)
        if self.in_title:
            self.title_parts.append(data)
        if self.heading is not None:
            self.heading.append(data)
        if self.anchor is not None:
            self.anchor["label"] += " " + data
        if self.form is not None:
            self.form["parts"].append(data)

    def extract(self, url):
        # HTML uses the first base with href, even if it is unusable. Never
        # replace it with a later base or guess HTTP links from an opaque base.
        base_url, base_href, base_error = url, None, None
        if self.base_hrefs:
            base_href = self.base_hrefs[0]
            try:
                candidate = urljoin(url, base_href.strip())
                parsed = urlsplit(candidate)
                parsed.port  # Validate a declared port as well as the hostname.
                if parsed.scheme not in ("http", "https"):
                    base_url, base_error = None, "unsupported_base_scheme"
                elif not parsed.hostname or parsed.username or parsed.password:
                    base_url, base_error = None, "invalid_base_url"
                else:
                    base_url = candidate
            except ValueError:
                base_url, base_error = None, "invalid_base_url"
        links, unresolved_links = [], []
        for item in self.links:
            attribute = item.get("attribute", "href")
            captured = {attribute: item["href"], "label": clean(item["label"])}
            try:
                if base_url is not None:
                    resolved = urljoin(base_url, item["href"])
                else:
                    parsed = urlsplit(item["href"])
                    if parsed.scheme == "mailto" or (parsed.scheme in ("http", "https") and parsed.hostname):
                        resolved = item["href"]
                    else:
                        unresolved_links.append({**captured, "resolution_error": "base_url_unresolved"})
                        continue
                links.append({"url": resolved, **captured})
            except ValueError:
                unresolved_links.append({**captured, "resolution_error": "invalid_link_url"})
        forms = []
        for item in self.forms:
            item = dict(item)
            item["text"] = clean(" ".join(item.pop("parts")))
            forms.append(item)
        return {
            "text": clean(" ".join(self.parts)), "title": clean(" ".join(self.title_parts)),
            "headings": self.headings,
            "base_href": base_href, "base_hrefs": list(self.base_hrefs), "base_url": base_url,
            "base_resolution_error": base_error, "links": links, "unresolved_links": unresolved_links,
            "forms": forms,
        }


class Fetcher:
    """No retries; host serialization, robots checks, and bounded public GETs."""
    def __init__(self, delay=1.0, timeout=14, global_rps=1.0, raw_directory=None):
        if not math.isfinite(global_rps) or not 0 < global_rps <= 4:
            raise ValueError("global_rps must be finite, greater than zero, and at most 4")
        self.delay, self.timeout = delay, timeout
        self.guard = threading.Lock()
        self.dispatch_lock = threading.Lock()
        self.log_lock = threading.Lock()
        self.configured_global_rps = self.global_rps = float(global_rps)
        self.minimum_global_rps = min(self.global_rps, 0.25)
        self.next_dispatch = 0.0
        self.rate_adjustments: list[dict] = []
        self.generic_503_origins: set[str] = set()
        self.http_status_counts: Counter = Counter()
        self.failure_counts: Counter = Counter()
        self.locks: dict[str, threading.Lock] = {}
        self.next_allowed: dict[str, float] = {}
        self.robots: dict[str, tuple[RobotFileParser | None, dict]] = {}
        self.denied: set[str] = set()
        self.delays: dict[str, float] = {}
        self.environment_failure_hosts: set[str] = set()
        self.environment_failed = threading.Event()
        self.http_get_attempt_count = 0
        self.thread_state = threading.local()
        self.raw_directory = Path(raw_directory) if raw_directory is not None else None

    def _save_raw_entity(self, raw: bytes, result: dict) -> None:
        """Publish a complete entity without replacing any existing SHA file."""
        result.update(raw_body_completed_at=now(),
                      raw_entity_semantics="Complete requests.iter_content response entity; may be content-decoded, not wire or gzip transfer bytes. Completion is the local observation of iteration ending.",
                      raw_storage_status="failed")
        temporary = None
        try:
            self.raw_directory.mkdir(parents=True, exist_ok=True)
            target = self.raw_directory / result["sha256"]
            # The temporary is never exposed under the completed entity's name.
            with tempfile.NamedTemporaryFile(dir=self.raw_directory, prefix=".raw-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, target)  # Atomic creation; never overwrites.
                status = "saved"
            except FileExistsError:
                if target.is_symlink() or target.read_bytes() != raw:
                    raise FileExistsError("Existing raw SHA target does not match the received entity")
                status = "reused"
            result.update(raw_file=str(target), raw_sha256=result["sha256"],
                          raw_file_path_basis="Collector working directory if the configured path is relative",
                          raw_storage_status=status)
        except (OSError, ValueError) as error:
            # Storage failure is evidence loss, not a network failure or retry.
            result["raw_storage_error"] = type(error).__name__
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    # A leftover non-SHA temporary is not a complete artifact.
                    result["raw_storage_cleanup_error"] = "OSError"

    def thread_get_attempt_count(self) -> int:
        return getattr(self.thread_state, "http_get_attempt_count", 0)

    def wait_for_delay(self, seconds: float) -> bool:
        return self.environment_failed.wait(seconds)

    def stats(self) -> dict:
        with self.guard:
            return {
                "configured_global_rps": self.configured_global_rps, "final_global_rps": self.global_rps,
                "minimum_global_rps": self.minimum_global_rps, "http_get_attempt_count": self.http_get_attempt_count,
                "http_status_counts": dict(self.http_status_counts),
                "common_transport_503_count": self.failure_counts["common_transport_503"],
                "site_specific_503_count": self.failure_counts["site_tls_503"] + self.failure_counts["site_connection_termination_503"],
                "http_429_count": self.failure_counts["http_429"],
                "rate_adjustments": list(self.rate_adjustments),
            }

    def _observe_response(self, result: dict, origin: str) -> None:
        status, text = result.get("http_status"), result.get("text", "")
        if status == 503:
            if "Invalid argument|remote address:envoy://cloudflare_" in text:
                signature = "common_transport_503"
            elif re.search(r"TLS_error:|WRONG_VERSION_NUMBER|CERTIFICATE_VERIFY_FAILED", text, re.I):
                signature = "site_tls_503"
            elif "connection termination" in text.lower():
                signature = "site_connection_termination_503"
            else:
                signature = "http_503"
        elif result.get("error"):
            signature = "request_exception:" + result["error"]
        elif status is not None and status >= 400:
            signature = "http_" + str(status)
        else:
            signature = None
        result["failure_signature"] = signature
        adjustment = None
        with self.guard:
            if status is not None:
                self.http_status_counts[str(status)] += 1
            if signature:
                self.failure_counts[signature] += 1
            common = signature == "common_transport_503"
            if common:
                self.environment_failure_hosts.add(origin)
                if len(self.environment_failure_hosts) >= 3:
                    self.environment_failed.set()
            generic = signature == "http_503" and origin not in self.generic_503_origins
            if generic:
                self.generic_503_origins.add(origin)
            if common or generic:
                previous = self.global_rps
                self.global_rps = max(self.minimum_global_rps, previous * (0.5 if common else 0.8))
                self.next_dispatch = max(self.next_dispatch, time.monotonic() + 1 / self.global_rps)
                if self.global_rps < previous:
                    adjustment = {"event": "global_rate_reduced", "observed_at": now(), "origin": origin,
                                  "failure_signature": signature, "previous_rps": previous,
                                  "global_rps": self.global_rps, "minimum_rps": self.minimum_global_rps}
                    self.rate_adjustments.append(adjustment)
        if adjustment:
            with self.log_lock:
                print(json.dumps(adjustment, ensure_ascii=False), flush=True)

    def _dispatch_get(self, url: str, origin: str, result: dict):
        waiting_since = time.monotonic()
        # All GETs share this monotonic admission gate, including preflight,
        # robots and redirects. Wait for the current slot here; never distribute
        # future slots to workers. Network waits retain only the origin lock.
        with self.dispatch_lock:
            while True:
                with self.guard:
                    if self.environment_failed.is_set():
                        result["error"] = "environment_circuit_breaker_open"
                        result["global_wait_seconds"] = max(0.0, time.monotonic() - waiting_since)
                        result["wait_seconds"] = result["host_wait_seconds"] + result["global_wait_seconds"]
                        return None
                    tick = time.monotonic()
                    remaining = self.next_dispatch - tick
                    if remaining <= 0:
                        self.next_dispatch = tick + 1 / self.global_rps
                        self.next_allowed[origin] = tick + self.delays.get(origin, self.delay)
                        self.http_get_attempt_count += 1
                        self.thread_state.http_get_attempt_count = self.thread_get_attempt_count() + 1
                        result.update(http_get_attempted=True, global_rps_at_dispatch=self.global_rps,
                                      global_wait_seconds=max(0.0, tick - waiting_since),
                                      http_get_started_at=now(), _started_monotonic=tick)
                        result["wait_seconds"] = result["host_wait_seconds"] + result["global_wait_seconds"]
                        break
                if self.wait_for_delay(remaining):
                    continue  # Recheck the circuit, and any slower updated rate.
        # Release the global gate immediately before GET; its timestamp above
        # is the call-admission time, not a packet-transmission measurement.
        # Inherit proxy and CA configuration. No authentication or form data.
        response = requests.get(url, timeout=(8, self.timeout), headers={"User-Agent": USER_AGENT}, stream=True, allow_redirects=False)
        result["http_response_received_at"] = now()
        return response

    def raw_get(self, url):
        origin = "{}://{}".format(urlsplit(url).scheme, urlsplit(url).netloc)
        with self.guard:
            lock = self.locks.setdefault(origin, threading.Lock())
        result = {"requested_url": url, "retrieved_at": now(), "publication_time": None,
                  "submitted": False, "http_get_attempted": False,
                  "http_get_started_at": None, "http_response_received_at": None, "http_get_completed_at": None,
                  "host_wait_seconds": 0.0, "global_wait_seconds": 0.0, "wait_seconds": 0.0,
                  "extraction_method": "HTTP GET; visible HTML text, links, non-hidden form controls"}
        if self.raw_directory is not None:
            result["raw_storage_status"] = "not_saved_incomplete_entity"
        if self.environment_failed.is_set():
            result["error"] = "environment_circuit_breaker_open"
            return result
        waiting_since = time.monotonic()
        with lock:
            result["host_wait_seconds"] = max(0.0, time.monotonic() - waiting_since)
            result["wait_seconds"] = result["host_wait_seconds"]
            if origin in self.denied:
                result["error"] = "host_access_denied_stopped"
                return result
            wait_for = self.next_allowed.get(origin, 0) - time.monotonic()
            if wait_for > 0 and self.wait_for_delay(wait_for):
                result["host_wait_seconds"] = max(0.0, time.monotonic() - waiting_since)
                result["wait_seconds"] = result["host_wait_seconds"]
                result["error"] = "environment_circuit_breaker_open"
                return result
            result["host_wait_seconds"] = max(0.0, time.monotonic() - waiting_since)
            result["wait_seconds"] = result["host_wait_seconds"]
            try:
                response = self._dispatch_get(url, origin, result)
                if response is None:
                    return result
                with response:
                    result.update(url=response.url, http_status=response.status_code,
                                  response_headers={str(k).lower(): clean(str(v))[:1024] for k, v in response.headers.items() if str(k).lower() in SAFE_RESPONSE_HEADERS})
                    result["retry_after_seconds"] = retry_after_seconds(result["response_headers"].get("retry-after"), result["http_response_received_at"])
                    if response.status_code in (401, 403, 429):
                        self.denied.add(origin)
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > 3 * 1024 * 1024:
                            raise ValueError("public page exceeds three MiB")
                        chunks.append(chunk)
                    raw = b"".join(chunks)
                    result.update(url=response.url, http_status=response.status_code, byte_count=size,
                                  sha256=hashlib.sha256(raw).hexdigest(), content_type=response.headers.get("Content-Type", ""))
                    if self.raw_directory is not None:
                        self._save_raw_entity(raw, result)
                    if response.status_code in (301, 302, 303, 307, 308) and response.headers.get("Location"):
                        try:
                            result["redirect_target"] = http_url(urljoin(url, response.headers["Location"]))
                        except ValueError:
                            # Preserve the response body despite an invalid target.
                            result["redirect_target"] = None
                            result["redirect_error"] = "invalid_redirect_target"
                    # An explicit HTTP charset takes precedence over HTML meta.
                    # Requests' implicit Latin-1 default is not an HTTP declaration.
                    header = Message()
                    header["Content-Type"] = result["content_type"]
                    http_charset = header.get_content_charset()
                    meta = re.search(rb"<meta\b[^>]*charset\s*=\s*[\"']?\s*([a-zA-Z0-9_-]+)", raw[:30000], re.I)
                    html_meta_charset = meta.group(1).decode("ascii") if meta else None
                    if http_charset:
                        encoding, encoding_source = http_charset, "http_charset"
                    elif html_meta_charset:
                        encoding, encoding_source = html_meta_charset, "html_meta_charset"
                    elif response.encoding and response.encoding.lower() != "iso-8859-1":
                        encoding, encoding_source = response.encoding, "requests_encoding"
                    else:
                        encoding, encoding_source = "utf-8", "utf8_fallback"
                    if encoding.lower() in ("shift_jis", "shift-jis", "sjis"):
                        encoding = "cp932"
                    result.update(encoding=encoding, encoding_source=encoding_source,
                                  http_charset=http_charset, html_meta_charset=html_meta_charset)
                    decoded = raw.decode(encoding, errors="replace")
                    if "html" in result["content_type"].lower() or decoded.lstrip().startswith("<"):
                        parser = Page()
                        parser.feed(decoded)
                        result.update(parser.extract(response.url))
                    else:
                        result.update(text=decoded[:200000], title="", headings=[], links=[], forms=[])
            except (requests.RequestException, ValueError, LookupError) as error:
                result["error"] = type(error).__name__
            finally:
                if result["http_get_attempted"]:
                    result["http_get_completed_at"] = now()
                    result["http_get_elapsed_seconds"] = max(0.0, time.monotonic() - result.pop("_started_monotonic"))
                    self._observe_response(result, origin)
        return result

    def capture_one(self, url):
        origin = "{}://{}".format(urlsplit(url).scheme, urlsplit(url).netloc)
        # A host's robots capture is itself public evidence and cached for this run.
        # Unreachable robots are not permission to make another GET to the site.
        with self.guard:
            cached = self.robots.get(origin)
        if cached is None:
            robots_url = origin + "/robots.txt"
            evidence = self.raw_get(robots_url)
            redirects, visited = [], {robots_url}
            redirect_failure = None
            while not evidence.get("error") and 300 <= (evidence.get("http_status") or 0) < 400:
                target = evidence.get("redirect_target")
                if not target:
                    redirect_failure = "redirect_unresolved"
                    break
                if target in visited:
                    redirect_failure = "redirect_loop"
                    break
                if len(redirects) >= 5:
                    redirect_failure = "redirect_limit"
                    break
                redirects.append(request_metadata(evidence))
                visited.add(target)
                evidence = self.raw_get(target)
            if redirects:
                evidence["redirects"] = redirects
            if redirect_failure:
                # A derived stopping reason; keep the final HTTP result intact.
                evidence["robots_failure_reason"] = redirect_failure
            parser = None
            if not evidence.get("error") and evidence.get("http_status") == 200 and evidence.get("text"):
                parser = parse_robots(evidence["text"])
                delay = parser.crawl_delay(USER_AGENT)
                if delay:
                    with self.guard:
                        self.delays[origin] = max(self.delay, delay)
                        self.next_allowed[origin] = max(self.next_allowed.get(origin, 0), time.monotonic() + delay)
            with self.guard:
                cached = self.robots.setdefault(origin, (parser, evidence))
        parser, robots_evidence = cached
        stopped = {"requested_url": url, "retrieved_at": now(), "submitted": False,
                   "http_get_attempted": False, "robots": robots_evidence}
        status = robots_evidence.get("http_status")
        if status in (401, 403, 429):
            return {**stopped, "error": "robots_access_denied_stopped"}
        reason = robots_evidence.get("robots_failure_reason")
        if not reason and robots_evidence.get("error"):
            reason = "request_or_response_error"
        if not reason and status is None:
            reason = "missing_http_status"
        if not reason and status >= 500:
            reason = "http_5xx"
        if not reason and 300 <= status < 400:
            reason = "redirect_unresolved"
        if reason:
            return {**stopped, "error": "robots_unreachable_stopped", "robots_failure_reason": reason}
        if parser and not robots_can_fetch(parser, USER_AGENT, url):
            return {**stopped, "error": "robots_disallowed"}
        result = self.raw_get(url)
        result["robots"] = robots_evidence
        return result

    def capture(self, url):
        original, redirects, visited = url, [], set()
        for _ in range(8):
            if url in visited:
                return {"requested_url": original, "retrieved_at": now(), "submitted": False, "error": "redirect_loop", "redirects": redirects}
            visited.add(url)
            result = self.capture_one(url)
            target = result.get("redirect_target")
            if not target:
                result["requested_url"] = original
                if redirects:
                    result["redirects"] = redirects
                return result
            redirects.append(request_metadata(result))
            url = target
        return {"requested_url": original, "retrieved_at": now(), "submitted": False, "error": "redirect_limit", "redirects": redirects}


def excerpt(text: str, pattern: re.Pattern, radius=180) -> str | None:
    match = pattern.search(text)
    return text[max(0, match.start() - 60): min(len(text), match.end() + radius)] if match else None


def form_has_fields(form: dict) -> bool:
    controls = [x for x in form.get("controls", []) if x.get("type", "text").lower() not in ("hidden", "submit", "button", "search", "checkbox", "radio", "reset") and x.get("tag") != "select"]
    email_indices = {
        i for i, x in enumerate(controls)
        if x.get("type") == "email" or (
            x.get("tag") == "input" and (
                re.search(r"email|e_mail|mailaddress|mail_address|メール", json.dumps(x, ensure_ascii=False), re.I)
                # Saved IR forms also use text input names mail and mail2.
                or re.fullmatch(r"mail[0-9]*", str(x.get("name", "")), re.I)
            )
        )
    }
    question_indices = {i for i, x in enumerate(controls) if x.get("tag") == "textarea" or re.search(r"message|question|inquiry_content|お問い合わせ内容|ご質問", json.dumps(x, ensure_ascii=False), re.I)}
    return any(email != question for email in email_indices for question in question_indices)


def analyze_page(page: dict, explicit_ir_route=False) -> dict:
    """A generic navigation label is insufficient to validate a contact."""
    if not (200 <= page.get("http_status", 0) < 300) or not page.get("text") or page.get("error"):
        return {"level": "none", "channels": [], "emails": [], "quotes": []}
    text, url = page["text"], page.get("url", page["requested_url"])
    # Global h2/h3 navigation is not a description of the actual form.
    headers = " ".join([page.get("title", ""), *page.get("headings", [])[:1]])
    dedicated = bool(IR_CONTACT.search(headers))
    ir_text = IR_CONTACT.search(text)
    emails, quotes = [], []
    for match in EMAIL.finditer(text):
        email = match.group(0).strip(".")
        nearby = text[max(0, match.start() - 200):match.end() + 100]
        local = email.split("@")[0]
        if re.search(r"example|sample|^x{3,}|^your[._-]|^test$|yutai|yuutai|優待", email, re.I) or re.search(r"(?:入力例|記入例|例[:：]).{0,25}" + re.escape(email), nearby):
            continue
        if re.search(r"(?:^|[._-])ir(?:$|[._-])|investor", local, re.I) and IR.search(nearby):
            emails.append(email)
            quotes.append(nearby)
        elif dedicated and IR_CONTACT.search(nearby) and not re.search(r"個人情報.{0,30}(?:管理|相談)|privacy|製品|採用|広報に", nearby, re.I):
            emails.append(email)
            quotes.append(nearby)
    for link in page.get("links", []):
        if link["url"].startswith("mailto:") and IR_CONTACT.search(link.get("label", "")):
            address = link["url"][7:].split("?")[0]
            if EMAIL.fullmatch(address):
                emails.append(address)
                # A machine-readable link quote is independently validated by the audit tool.
                if link["label"] in text:
                    quotes.append(link["label"])
    email_set = sorted(set(emails))
    forms = []
    for form in page.get("forms", []):
        # A privacy notice describing shareholder data is not an IR category.
        scope_text = PRIVACY_START.split(form.get("text", ""), maxsplit=1)[0]
        scope_text = IR_DEFLECTION.sub("", scope_text)
        in_form = IR.search(scope_text)
        if form_has_fields(form) and (dedicated or in_form or explicit_ir_route):
            forms.append(form)
            candidate_quote = (excerpt(scope_text, IR_CONTACT) or excerpt(scope_text, IR)) if in_form else (excerpt(text, IR_CONTACT) or excerpt(text, IR))
            if candidate_quote:
                quotes.append(candidate_quote)
    channels = (["email"] if email_set else []) + (["form"] if forms else [])
    if channels:
        level = "form_fields_verified" if forms else "ir_email_verified"
        if not quotes:
            level = "official_form_link_only"
    elif dedicated and ("フォーム" in text or "form" in text.lower()) and CONTACT_PATH.search(urlsplit(url).path):
        level = "official_form_link_only"
        candidate_quote = excerpt(text, IR_CONTACT) or excerpt(text, IR)
        if candidate_quote:
            quotes.append(candidate_quote)
        channels = ["form"]
    else:
        level = "none"
        for link in page.get("links", []):
            if IR_CONTACT.search(link.get("label", "")) and re.search(r"フォーム|\bform\b", link.get("label", ""), re.I):
                level, channels = "official_form_link_only", ["form"]
                if link["label"] in text:
                    quotes.append(link["label"])
                break
    return {"level": level, "channels": channels, "emails": email_set, "quotes": list(dict.fromkeys(quotes)), "forms": forms}


def candidate_links(page: dict, seed_host: str, came_from_ir=False):
    candidates = []
    for item in page.get("links", []):
        url = http_url(item["url"])
        if not url:
            continue
        label, parsed = item.get("label", ""), urlsplit(url)
        same = parsed.hostname == seed_host or parsed.hostname.endswith("." + seed_host.removeprefix("www.")) or parsed.hostname.removeprefix("www.") == seed_host.removeprefix("www.")
        is_ir_contact = bool(IR_CONTACT.search(label))
        is_ir_path = bool(IR_PATH.search(parsed.path))
        is_contact = bool(CONTACT.search(label) or CONTACT_PATH.search(parsed.path))
        embedded = label == "embedded frame" and came_from_ir
        if not same and not (is_ir_contact or embedded or (came_from_ir and is_contact)):
            continue
        # Follow only discovered public links. Do not guess addresses or submit endpoints.
        if is_ir_contact:
            rank = 100
        elif came_from_ir and is_contact:
            rank = 85
        elif is_ir_path and is_contact:
            rank = 80
        elif embedded:
            rank = 75
        elif IR.search(label) or is_ir_path:
            rank = 65
        elif same and is_contact:
            rank = 50
        elif same and re.search(r"サイトマップ|sitemap", label + parsed.path, re.I):
            rank = 25
        else:
            continue
        candidates.append((rank, url, is_ir_contact or embedded, label, page.get("url", page["requested_url"])))
    return candidates


def initial_investigation_record(company: dict, seed: dict | None) -> dict:
    return {**company, "investigation_status": "unconfirmed", "verification_level": "none",
              "official_url": seed.get("official_url") if seed else None,
              "contact_url": None, "channels": [], "public_ir_emails": [],
              "individual_access": "not_stated", "outreach_suitability": "unconfirmed",
              "attempted_at": now(), "completed_at": None, "manual_review_required": True,
              "evidence": [], "fetches": [], "conditions": [], "limitations": [],
              "discovery": seed, "identity_status": "unverified", "identity_matches": [],
              "successful_official_page_count": 0}


def investigation(company: dict, seed: dict | None, output: Path, fetcher: Fetcher,
                  max_pages: int, record: dict | None = None) -> dict:
    # The caller keeps this object so an exception cannot discard references
    # to snapshots that were already saved. Standalone callers use the same schema.
    if record is None:
        record = initial_investigation_record(company, seed)
    code = company["security_code"]
    if seed is None or not http_url(seed.get("official_url", "")):
        record["limitations"].append("公式サイトURLの発見未完了。公式ページ取得・窓口確認とも未実施。")
        record["completed_at"] = now()
        return record
    original_url = http_url(seed["official_url"])
    capture_attempt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    seed_host = urlsplit(original_url).hostname
    queue = [(120, original_url, False, "discovery seed", seed.get("discovery_url"))]
    visited, observations, best, parents = set(), [], None, {}
    for _ in range(max_pages):
        if getattr(fetcher, "environment_failed", None) and fetcher.environment_failed.is_set():
            record["collection_stop_reason"] = "environment_circuit_breaker_open"
            break
        queue.sort(key=lambda x: -x[0])
        item = next((x for x in queue if x[1] not in visited), None)
        if item is None:
            break
        queue.remove(item)
        _, url, explicit_route, label, parent_url = item
        visited.add(url)
        page = fetcher.capture(url)
        relative = f"evidence/{code}/{capture_attempt}/{len(visited):02d}.json"
        page.update(security_code=code, source_type="official_public_contact_page", discovery_parent_url=parent_url,
                    discovery_link_label=label, official_identity_basis=seed.get("discovery_type"))
        write_json(output / relative, page)
        record["fetches"].append({"url": url, "final_url": page.get("url"), "snapshot": relative,
                                  "retrieved_at": page["retrieved_at"], "http_status": page.get("http_status"), "error": page.get("error")})
        observations.append((page, relative, explicit_route))
        status = page.get("http_status")
        if isinstance(status, int) and 200 <= status < 300 and page.get("text"):
            record["successful_official_page_count"] += 1
        normalized_text = identity_key(page.get("text", ""))
        expected_name = identity_key(company["company_name"])
        code_observed = bool(re.search(r"(?:証券コード|銘柄コード|security code|stock code)[\s:：]*" + re.escape(code) + r"(?![0-9A-Z])", page.get("text", ""), re.I))
        if (len(expected_name) >= 2 and expected_name in normalized_text) or code_observed:
            record["identity_status"] = "name_or_security_code_observed"
            record["identity_matches"].append({"snapshot": relative, "normalized_name": expected_name, "security_code_observed": code_observed})
        parents[url] = (parent_url, label)
        if page.get("http_status") in (401, 403, 429) or page.get("error"):
            record["limitations"].append(f"{url}: {page.get('error') or ('HTTP ' + str(page.get('http_status')))}")
            if len(visited) == 1:
                break
            continue
        result = analyze_page(page, explicit_route)
        scores = {"form_fields_verified": 3, "ir_email_verified": 3, "official_form_link_only": 1, "none": 0}
        if scores[result["level"]] > (scores[best[0]["level"]] if best else 0):
            best = (result, page, relative)
        came_from_ir = explicit_route or bool(IR_PATH.search(urlsplit(page.get("url", url)).path))
        for candidate in candidate_links(page, seed_host, came_from_ir):
            if candidate[1] not in visited:
                queue.append(candidate)
        if best and scores[best[0]["level"]] == 3:
            # Retain publicly linked disclosure/contact conditions when already present.
            if not any(x[0] >= 90 and x[1] not in visited for x in queue):
                break
    if best:
        result, page, snapshot = best
        record.update(verification_level=result["level"], contact_url=page.get("url", page["requested_url"]),
                      channels=result["channels"], public_ir_emails=result["emails"],
                      investigation_status="provisional" if result["level"] == "official_form_link_only" else "confirmed",
                      outreach_suitability="candidate")
        for quote in result["quotes"]:
            record["evidence"].append({"snapshot": snapshot, "url": page.get("url", page["requested_url"]),
                                       "retrieved_at": page["retrieved_at"], "quote": quote, "role": "contact_channel"})
        for candidate_page, candidate_snapshot, explicit in observations:
            # Conditions come from IR/contact pages, not unrelated navigation or products.
            if candidate_page is not page and not explicit and not IR_PATH.search(urlsplit(candidate_page.get("url", "")).path):
                continue
            text = candidate_page.get("text", "")
            matches = []
            for match in CONDITIONS.finditer(text):
                quote = text[max(0, match.start() - 80):min(len(text), match.end() + 180)]
                if quote not in matches:
                    matches.append(quote)
                if len(matches) >= 14:
                    break
            for quote in matches:
                record["conditions"].append(quote)
                record["evidence"].append({"snapshot": candidate_snapshot, "url": candidate_page.get("url", candidate_page["requested_url"]),
                                           "retrieved_at": candidate_page["retrieved_at"], "quote": quote, "role": "conditions"})
            if NO_REPLY.search(text):
                record["outreach_suitability"] = "no_individual_reply"
            elif RESTRICTION.search(text) and record["outreach_suitability"] != "no_individual_reply":
                record["outreach_suitability"] = "restricted"
        record["limitations"].append("自動抽出。個人の利用条件・会社名必須・返信条件は人の点検が必要。送信・回答実績は未確認。")
        if record["identity_status"] == "unverified":
            record["investigation_status"] = "provisional"
            record["limitations"].append("取得本文で現JPX会社名・銘柄コードを照合できない。発見用URL一覧の会社同一性を人の点検が必要。")
    else:
        has_success = any(200 <= p.get("http_status", 0) < 300 and p.get("text") for p, _, _ in observations)
        record["limitations"].append(
            "取得できた公開ページではIR用途とメール/質問フォームの結びつきを実証できなかった。窓口不存在の判定ではない。"
            if has_success else "公式本文を未取得。IR受付の確認は未完了で、窓口不存在の判定ではない。")
    success_count = sum(200 <= p.get("http_status", 0) < 300 and bool(p.get("text")) for p, _, _ in observations)
    record["successful_official_page_count"] = success_count
    failure = any(transport_failure_observed(p) for p, _, _ in observations)
    if not success_count and failure:
        record["unconfirmed_reason"] = "environment_transport_failure"
        record["limitations"].insert(0, "クラウドの通信経路で接続失敗。公式本文を未取得。企業側の受付拒否・窓口不存在の判定ではない。")
    elif record["investigation_status"] == "unconfirmed":
        record["unconfirmed_reason"] = "official_channel_not_demonstrated" if success_count else "access_or_parse_failure"
    record["completed_at"] = now()
    return record


def previous_records(previous: Path, output: Path, universe: dict[str, dict]) -> None:
    previous_data = json.loads((previous / "companies.json").read_text(encoding="utf-8"))
    prefix = "../" + previous.name + "/"
    for old in previous_data["companies"]:
        code = old["security_code"]
        if code not in universe or (output / "records" / f"{code}.json").exists():
            continue
        old_level = old["verification_level"]
        levels = {"page_and_fields_verified": "form_fields_verified", "page_and_email_verified": "ir_email_verified", "official_link_only": "official_form_link_only"}
        level = levels.get(old_level, "none")
        evidence = [{**x, "snapshot": prefix + x["snapshot"], "role": "previous_contact_or_conditions"} for x in old["evidence"]]
        record = {**universe[code], "official_url": old.get("ir_url"), "contact_url": old["contact_url"],
                  "investigation_status": "provisional" if level == "official_form_link_only" else "confirmed",
                  "verification_level": level, "channels": old["channels"], "public_ir_emails": old["public_ir_emails"],
                  "individual_access": old["individual_access"], "outreach_suitability": old["outreach_suitability"],
                  "attempted_at": old["verified_at"], "completed_at": old["verified_at"],
                  "manual_review_required": False, "manual_review": {"reviewer": "previous_codex_research", "reviewed_at": old["verified_at"], "notes": "前回のCodexによる調査分類を引継ぎ。確認水準は昇格しない。"},
                  "evidence": evidence, "fetches": [], "conditions": old["conditions"], "limitations": old["limitations"],
                  "previous_record": prefix + "companies.json", "original_verification_level": old_level}
        record["identity_status"] = "previous_verified"
        write_json(output / "records" / f"{code}.json", record)


def retain_prior_contact(old: dict, new: dict) -> dict:
    """Keep dated contact evidence when a new attempt demonstrates less.

    The latest attempt stays inspectable in full; an access failure does not
    establish that the previously verified contact no longer exists.
    """
    strength = {"none": 0, "official_form_link_only": 1, "form_fields_verified": 3, "ir_email_verified": 3}
    old_strength = strength.get(old.get("verification_level"), 0)
    weakened = strength.get(new.get("verification_level"), 0) < old_strength or (
        old.get("investigation_status") == "confirmed" and new.get("investigation_status") != "confirmed")
    if old_strength and old.get("contact_url") and old.get("evidence") and weakened:
        return {**old, "previous_attempts": new["previous_attempts"], "retained_prior_contact": True,
                "needs_contact_recheck": True, "latest_attempt": new,
                "last_attempted_at": new.get("attempted_at"), "last_attempt_completed_at": new.get("completed_at")}
    return new


def reclassify_saved(output: Path, universe: dict[str, dict]) -> None:
    """Reevaluate already saved observations without additional HTTP requests."""
    scores = {"form_fields_verified": 3, "ir_email_verified": 3, "official_form_link_only": 1, "none": 0}
    for code in universe:
        path = output / "records" / f"{code}.json"
        if not path.exists():
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("previous_record") or record.get("manual_review_required") is False:
            continue
        observations, best = [], None
        for fetch in record.get("fetches", []):
            page = json.loads((output / fetch["snapshot"]).read_text(encoding="utf-8"))
            explicit = bool(IR_CONTACT.search(page.get("discovery_link_label", "")))
            result = analyze_page(page, explicit)
            observations.append((page, fetch["snapshot"], explicit))
            if scores[result["level"]] > (scores[best[0]["level"]] if best else 0):
                best = result, page, fetch["snapshot"]
        record.update(investigation_status="unconfirmed", verification_level="none", contact_url=None,
                      channels=[], public_ir_emails=[], evidence=[], conditions=[], outreach_suitability="unconfirmed",
                      classification_version=2)
        record["limitations"] = [x for x in record.get("limitations", []) if not x.startswith(("自動抽出", "取得できた公開ページ", "取得本文で現JPX"))]
        if best:
            result, page, snapshot = best
            record.update(investigation_status="provisional" if result["level"] == "official_form_link_only" else "confirmed",
                          verification_level=result["level"], contact_url=page.get("url", page["requested_url"]),
                          channels=result["channels"], public_ir_emails=result["emails"], outreach_suitability="candidate")
            for quote in result["quotes"]:
                record["evidence"].append({"snapshot": snapshot, "url": page.get("url", page["requested_url"]), "retrieved_at": page["retrieved_at"], "quote": quote, "role": "contact_channel"})
            for condition_page, condition_snapshot, explicit in observations:
                if condition_page is not page and not explicit and not IR_PATH.search(urlsplit(condition_page.get("url", "")).path):
                    continue
                text = condition_page.get("text", "")
                for match in list(CONDITIONS.finditer(text))[:14]:
                    quote = text[max(0, match.start() - 80):min(len(text), match.end() + 180)]
                    if quote in record["conditions"]:
                        continue
                    record["conditions"].append(quote)
                    record["evidence"].append({"snapshot": condition_snapshot, "url": condition_page.get("url", condition_page["requested_url"]), "retrieved_at": condition_page["retrieved_at"], "quote": quote, "role": "conditions"})
                if NO_REPLY.search(text):
                    record["outreach_suitability"] = "no_individual_reply"
                elif RESTRICTION.search(text) and record["outreach_suitability"] != "no_individual_reply":
                    record["outreach_suitability"] = "restricted"
            if record.get("identity_status") == "unverified":
                record["investigation_status"] = "provisional"
                record["limitations"].append("現会社の同一性は未確認。発見用URLと現会社名の人による照合が必要。")
            record["limitations"].append("自動抽出。個人条件・会社名必須・返信条件を人が点検する必要がある。送信・回答実績は未確認。")
        has_success = any(200 <= p.get("http_status", 0) < 300 and p.get("text") for p, _, _ in observations)
        network_failure = any(transport_failure_observed(p) for p, _, _ in observations)
        if not has_success and network_failure:
            record["unconfirmed_reason"] = "environment_transport_failure"
            record["limitations"].insert(0, "クラウドの通信経路で接続失敗。企業公式本文を取得できていない。IR窓口不存在・企業側の受付拒否の判定ではない。")
        elif record["investigation_status"] == "unconfirmed":
            record["unconfirmed_reason"] = "official_channel_not_demonstrated" if has_success else "access_or_parse_failure"
            record["limitations"].append(
                "取得できた公開ページではIR用メール/質問フォームの明示を実証できなかった。窓口不存在の判定ではない。"
                if has_success else "公式本文を未取得。IR受付の確認は未完了で、窓口不存在の判定ではない。")
        record["successful_official_page_count"] = sum(200 <= p.get("http_status", 0) < 300 and bool(p.get("text")) for p, _, _ in observations)
        write_json(path, record)


def compile_directory(output: Path, universe: dict[str, dict]) -> dict:
    records = []
    for company in universe.values():
        path = output / "records" / (company["security_code"] + ".json")
        if path.exists():
            records.append(json.loads(path.read_text(encoding="utf-8")))
        else:
            records.append({**company, "investigation_status": "pending", "verification_level": "none", "outreach_suitability": "unconfirmed"})
    counts = Counter(x["investigation_status"] for x in records)
    local_stops = {"robots_disallowed", "robots_access_denied_stopped", "robots_unreachable_stopped", "host_access_denied_stopped", "environment_circuit_breaker_open"}
    attempted_now = sum(any(f.get("http_status") is not None or (f.get("error") and f["error"] not in local_stops) for f in x.get("fetches", [])) for x in records)
    summary = {"universe_count": len(universe), "terminal_records": len(universe) - counts["pending"],
               "by_investigation_status": dict(counts), "by_verification_level": dict(Counter(x["verification_level"] for x in records)),
               "official_get_company_count": attempted_now,
               "official_get_attempt_company_count_current_run": attempted_now,
               "reused_previous_company_count": sum(bool(x.get("previous_record")) for x in records),
               "codex_reviewed_company_count": sum(x.get("manual_review_required") is False for x in records),
               "by_outreach_suitability": dict(Counter(x["outreach_suitability"] for x in records)),
               "companies_with_successful_public_page_this_run": sum(x.get("successful_official_page_count", 0) > 0 or any(f.get("http_status") is not None and 200 <= f["http_status"] < 300 for f in x.get("fetches", [])) for x in records),
               "unconfirmed_reasons": dict(Counter(x.get("unconfirmed_reason", "unspecified") for x in records if x["investigation_status"] == "unconfirmed")),
               "email_or_form_sent_count": 0, "financial_screening_completed": False}
    envelope = {"format": "ir_universe_contact_directory", "format_version": 1, "generated_at": now(),
                "listing_data_as_of": "2026-09-30", "scope": "JPX Prime/Standard/Growth domestic ordinary stocks; not all Japanese exchanges",
                "summary": summary, "companies": records}
    if (output / "listing-deltas.json").exists():
        envelope["listing_changes_applied_through"] = "2026-10-11"
    write_json(output / "companies.json", envelope)
    write_json(output / "coverage.json", summary)
    fields = ["security_code", "company_name", "market", "jpx_sector", "investigation_status", "verification_level", "outreach_suitability", "individual_access", "official_url", "contact_url", "channels", "public_ir_emails", "manual_review_required", "unconfirmed_reason", "completed_at", "conditions", "limitations"]
    with (output / "companies.csv").open("w", newline="", encoding="utf-8-sig") as target:
        writer = csv.DictWriter(target, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = {key: record.get(key, "") for key in fields}
            for key, value in row.items():
                if isinstance(value, list):
                    row[key] = " | ".join(value)
            writer.writerow(row)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--universe", type=Path, required=True)
    parser.add_argument("--seeds", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--global-rps", type=float, default=1.0, help="Smooth all GET dispatches across origins; finite 0 < RPS <= 4")
    parser.add_argument("--max-pages", type=int, default=7)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--only-seeded", action="store_true", help="Leave undiscovered companies pending for a subsequent discovery batch")
    parser.add_argument("--listing-deltas", type=Path)
    parser.add_argument("--compile-only", action="store_true")
    parser.add_argument("--reclassify", action="store_true", help="Use existing evidence only; no networking")
    parser.add_argument("--resume-network-errors", action="store_true", help="Retry only environment failures once, retaining previous observations")
    parser.add_argument("--resume-unconfirmed", action="store_true", help="Retry saved unconfirmed/provisional contacts while retaining better prior evidence")
    parser.add_argument("--only-codes", nargs="+", help="Investigate only these codes, including explicitly selected existing records")
    args = parser.parse_args()
    if not 1 <= args.workers <= 40 or not 1 <= args.max_pages <= 15:
        parser.error("workers must be 1..40 and max-pages must be 1..15")
    if not math.isfinite(args.global_rps) or not 0 < args.global_rps <= 4:
        parser.error("global-rps must be finite, greater than zero, and at most 4")
    if args.limit is not None and args.limit < 1:
        parser.error("limit must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    with args.universe.open(encoding="utf-8-sig") as source:
        input_rows = list(csv.DictReader(source))
    if input_rows and "コード" in input_rows[0]:
        excluded = [x for x in input_rows if x["市場・商品区分"] in ("プライム（内国株式）", "スタンダード（内国株式）", "グロース（内国株式）") and not re.fullmatch(r"[0-9]{3}[0-9A-Z]", x["コード"])]
        write_json(args.output / "excluded-share-classes.json", excluded)
        input_rows = [{"security_code": x["コード"], "company_name": x["銘柄名"], "market": x["市場・商品区分"], "jpx_sector": x["33業種区分"]} for x in input_rows if x["市場・商品区分"] in ("プライム（内国株式）", "スタンダード（内国株式）", "グロース（内国株式）") and re.fullmatch(r"[0-9]{3}[0-9A-Z]", x["コード"])]
    universe = {x["security_code"]: x for x in input_rows}
    if len(universe) != len(input_rows):
        raise ValueError("duplicate security code in universe")
    if args.listing_deltas:
        for delta in json.loads(args.listing_deltas.read_text(encoding="utf-8")):
            if delta["effective_date"] > "2026-10-11":
                continue
            code = delta["security_code"]
            if delta["change"] == "delisted":
                universe.pop(code, None)
            elif delta["change"] == "new_listing":
                universe[code] = {key: delta.get(key) or "未確認" for key in ("security_code", "company_name", "market", "jpx_sector")}
                universe[code]["market"] += "（内国株式）" if "（" not in universe[code]["market"] else ""
    if args.only_codes:
        unknown = sorted(set(args.only_codes) - set(universe))
        if unknown:
            parser.error("only-codes includes codes outside the current universe: " + ", ".join(unknown))
    with (args.output / "universe.csv").open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["security_code", "company_name", "market", "jpx_sector"])
        writer.writeheader()
        writer.writerows(universe.values())
    seeds = {x["security_code"]: x for x in json.loads(args.seeds.read_text(encoding="utf-8"))}
    if args.previous:
        previous_records(args.previous, args.output, universe)
    if args.reclassify:
        reclassify_saved(args.output, universe)
    collection_run = None
    if not args.compile_only and not args.reclassify:
        pending, archived_attempts = [], {}
        for company in universe.values():
            if args.only_codes and company["security_code"] not in args.only_codes:
                continue
            path = args.output / "records" / f"{company['security_code']}.json"
            if not path.exists():
                pending.append(company)
            elif args.resume_network_errors or args.resume_unconfirmed or args.only_codes:
                old = json.loads(path.read_text(encoding="utf-8"))
                if args.only_codes or (args.resume_network_errors and old.get("unconfirmed_reason") == "environment_transport_failure") or (
                        args.resume_unconfirmed and old.get("investigation_status") in ("unconfirmed", "provisional")):
                    pending.append(company)
                    archived_attempts[company["security_code"]] = old
        if args.only_seeded:
            pending = [x for x in pending if x["security_code"] in seeds]
        if args.limit:
            pending = pending[:args.limit]
        fetcher = Fetcher(global_rps=args.global_rps, raw_directory=args.output / "raw")
        started_at = now()
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        run_path = args.output / "collection-runs" / (run_id + ".json")
        progress_path = args.output / "collection-runs" / (run_id + "-progress.json")
        saved_codes, actual_get_codes = [], []
        submitted_count = cancelled_count = preflight_get_count = 0
        preflight_http_status, preflight_passed = None, not pending

        def run_snapshot(status):
            stats = fetcher.stats()
            saved_set = set(saved_codes)
            not_saved = [x["security_code"] for x in pending if x["security_code"] not in saved_set]
            return {
                "started_at": started_at, "observed_at": now(), "status": status,
                "stop_reason": "environment_circuit_breaker_open" if fetcher.environment_failed.is_set() else None,
                "workers": args.workers, "max_pages": args.max_pages, **stats,
                "preflight_passed": preflight_passed, "preflight_http_status": preflight_http_status,
                "selected_company_count": len(pending), "submitted_company_count": submitted_count,
                "completed_in_this_run": len(saved_codes), "cancelled_future_count": cancelled_count,
                "companies_with_actual_get_count": len(actual_get_codes),
                "preflight_http_get_attempt_count": preflight_get_count,
                "company_http_get_attempt_count": stats["http_get_attempt_count"] - preflight_get_count,
                "get_count_scope": "requests.get attempts, including robots and redirects; total also includes preflight",
                "saved_security_codes": list(saved_codes), "not_saved_security_codes": not_saved,
                "not_saved_company_count": len(not_saved),
                "progress_path": str(progress_path.relative_to(args.output)),
                "run_path": str(run_path.relative_to(args.output)),
            }

        def write_progress(status="running"):
            write_json(progress_path, run_snapshot(status))

        write_progress("preflight" if pending else "running")
        if pending:
            health = fetcher.raw_get("https://www.jpx.co.jp/listing/stocks/new/index.html")
            health_path = args.output / "network-healthchecks" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
            write_json(health_path, health)
            preflight_get_count = fetcher.http_get_attempt_count
            preflight_http_status = health.get("http_status")
            preflight_passed = bool(200 <= health.get("http_status", 0) < 300 and "新規上場" in health.get("text", ""))
            if not preflight_passed:
                collection_run = {**run_snapshot("environment_preflight_failed"), "completed_at": now(),
                                  "stop_reason": "environment_preflight_failed", "preflight_snapshot": str(health_path.relative_to(args.output))}
                write_json(run_path, collection_run)
                write_json(progress_path, collection_run)
                print(json.dumps({"error": "environment_preflight_failed", "snapshot": str(health_path), "http_status": health.get("http_status"), "pending_count": len(pending), "companies_retried": 0,
                                  "http_get_attempt_count": fetcher.http_get_attempt_count,
                                  "company_http_get_attempt_count": 0, "collection_run": collection_run}, ensure_ascii=False), flush=True)
                return 2
        preflight_get_count = fetcher.http_get_attempt_count
        write_progress()

        def collect(company):
            if fetcher.environment_failed.is_set():
                return None
            before = fetcher.thread_get_attempt_count()
            seed = seeds.get(company["security_code"])
            record = initial_investigation_record(company, seed)
            try:
                record = investigation(company, seed, args.output, fetcher, args.max_pages, record=record)
            except Exception as error:
                partial = record
                record = initial_investigation_record(company, seed)
                # Preserve only observed acquisition/identity facts in the active
                # fallback. A tentative contact classification is not a completed
                # result; retain its full context separately for manual review.
                for field in ("attempted_at", "fetches", "identity_status", "identity_matches",
                              "successful_official_page_count"):
                    record[field] = partial[field]
                record.update(completed_at=now(), unconfirmed_reason="investigation_exception",
                              exception_partial_record=partial)
                record["limitations"] = [*partial["limitations"], "investigation_error:" + type(error).__name__,
                    "解析例外のため調査未確認。例外前の保存資料は保持し、未保存の応答や窓口不存在を推測しない。"]
            attempts = fetcher.thread_get_attempt_count() - before
            if fetcher.environment_failed.is_set() and not attempts:
                # A running worker that stopped before any GET is still pending.
                return None
            record["http_get_attempt_count"] = attempts
            return record

        remaining = iter(pending)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {}
            while True:
                # Keep only a worker-sized batch queued, so an outage cannot turn
                # thousands of unstarted companies into local terminal records.
                while len(futures) < args.workers and not fetcher.environment_failed.is_set():
                    company = next(remaining, None)
                    if company is None:
                        break
                    futures[pool.submit(collect, company)] = company
                    submitted_count += 1
                if fetcher.environment_failed.is_set():
                    for future in list(futures):
                        if future.cancel():
                            cancelled_count += 1
                            del futures[future]
                if not futures:
                    break
                done, _ = concurrent.futures.wait(futures, timeout=1, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    company = futures.pop(future)
                    record = future.result()
                    if record is None:
                        continue
                    code = company["security_code"]
                    old = archived_attempts.get(code)
                    attempt_get_count = record["http_get_attempt_count"]
                    if old is not None:
                        # Archive only when an executed result is ready to replace
                        # the old record. Its original snapshots remain untouched.
                        attempt = args.output / "attempts" / code / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
                        write_json(attempt, old)
                        record["previous_attempts"] = [*old.get("previous_attempts", []), str(attempt.relative_to(args.output))]
                        record = retain_prior_contact(old, record)
                    write_json(args.output / "records" / f"{code}.json", record)
                    saved_codes.append(code)
                    if attempt_get_count:
                        actual_get_codes.append(code)
                    if len(saved_codes) % 50 == 0:
                        summary = compile_directory(args.output, universe)
                        with fetcher.log_lock:
                            print(json.dumps({"completed_in_this_run": len(saved_codes), **summary, "collection_run": run_snapshot("running")}, ensure_ascii=False), flush=True)
                write_progress("environment_stopped" if fetcher.environment_failed.is_set() else "running")
        collection_run = {**run_snapshot("environment_stopped" if fetcher.environment_failed.is_set() else "completed"), "completed_at": now()}
        write_json(run_path, collection_run)
        write_json(progress_path, collection_run)
    summary = compile_directory(args.output, universe)
    if collection_run is not None:
        summary = {**summary, "collection_run": collection_run}
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 2 if collection_run and collection_run["status"] == "environment_stopped" else 0


if __name__ == "__main__":
    sys.exit(main())
