#!/usr/bin/env python3
"""Finite, resumable GETs of IR links actually present in saved official pages.

--plan-only reads local evidence and prints JSON without GETs or writes. Collection
uses the existing Fetcher, never supplies form values or authentication, and never
promotes a contact classification. Run after the initial collector has stopped.
The GET budget includes preflight, robots, and redirects, across state resumes.
--parser-refresh is restricted to the preserved 2752/2784 audit: two known URLs,
0.25 RPS, at most 12 GETs, and a fixed state with one reservation per company.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import ipaddress
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urldefrag, urlsplit
from urllib.robotparser import RobotFileParser

sys.dont_write_bytecode = True  # A cold --plan-only invocation must not create caches.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import research_ir_universe as research

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "research/ir-contacts-universe-2026-10-11"
PREFLIGHT = "https://www.jpx.co.jp/listing/stocks/new/index.html"
PARSER_REFRESH_AUDIT = "parts/adaptive-parser-refresh-12.json"
PARSER_REFRESH_STATE = "parser-refresh-current-run.json"
PARSER_REFRESH_MODE = "parser_refresh_2752_2784"
PARSER_REFRESH_MAX_GETS = 12
PARSER_REFRESH_TARGETS = {
    "2752": "https://fujiogroup.com/ir/",
    "2784": "https://reg18.smp.ne.jp/regist/is?SMPFORM=likc-ldtgqi-721d81312ae1e403f8cbff64c037eb5c",
}
IDENTITY_DISCOVERY_CODES = {"2300", "3440", "3695"}
IDENTITY_REFERENCE_AUDIT = "parts/adaptive-audit-services-3839-batch10.json"
# These are the three actual links from this fixed, reviewed evidence set.
# They discover issuer identity only, and are not a general language-site crawler.
IDENTITY_REFERENCE_ROUTES = {
    "3853": {
        "company_name": "アステリア", "official_url": "https://www.asteria.com/",
        "parent_url": "https://www.asteria.com/jp/en/contact/entry_ir/",
        "parent_snapshot": "evidence/3853/20261011T090158323372Z/02.json",
        "public_issuer_quote": "Asteria Corporation.",
        "links": [("https://jp.asteria.com/", "Japanese", "official_japanese_language_discovery")],
    },
    "3901": {
        "company_name": "マークラインズ", "official_url": "https://www.marklines.com/",
        "parent_url": "https://www.marklines.com/",
        "parent_snapshot": "evidence/3901/20261011T090902743206Z/01.json",
        "public_issuer_quote": "MarkLines Co., Ltd.",
        "links": [("https://www.marklines.com/portal_top_ja.html", "JAPANESE", "official_japanese_language_discovery"),
                  ("https://www.marklines.com/en/corporate_profile/", "Company Overview", "official_company_info_discovery")],
    },
}
IR_PORTAL_REFERENCE = {
    "security_code": "4444", "company_name": "インフォネット",
    "official_url": "https://www.e-infonet.jp/", "parent_url": "https://www.e-infonet.jp/",
    "parent_snapshot": "evidence/4444/20261011T113512324447Z/01.json", "source_link_index": 44,
    "target_url": "https://www.infonet-group.co.jp/",
    "quote": "株主投資家情報はインフォネットグループ社のサイトに掲載しています。",
    "reviewer": "codex_audit_services", "audit_snapshot": "parts/adaptive-audit-services-4-overflow-02.json",
    # This single completed review is the authority for following its portal
    # reference. The old event-release address supplies no contact authority.
    "source_sha256": "772da44c872d975e597242824366734fd0e1263a49fb118445299c0602c45a0e",
    "record_sha256": "d11d8978bc7e57533834ec7ccc00a8d7c6f1fa4b9017f4cd900f3d37873baad3",
    "audit_sha256": "72015dc8a8eb4db30983a63ffbb0874012b69ba2e05fd6c980e8948462f2581c",
}
REVIEWED_IR_AUDIT = "parts/adaptive-audit-manufacturing-46-batch12.json"
# Two recorded financial-IR sections whose link labels omit the word Contact.
# Exact issuer/source/row binding is deliberate; query strings never supply scope.
REVIEWED_IR_ROUTES = {
    "4004": {
        "company_name": "レゾナック・ホールディングス", "official_url": "https://www.resonac.com/jp",
        "parent_url": "https://www.resonac.com/jp/inquiry",
        "parent_snapshot": "evidence/4004/20261011T093814339081Z/05.json", "source_link_index": 177,
        "target_url": "https://www.inquiry.resonac.com/inquiryJa?typeId=ir", "label": "問い合わせフォーム",
        "quote": "IR（機関投資家・アナリスト向け） 問い合わせフォーム",
        "section_quote": "製品以外のお問い合わせ 問い合わせ内容 Webからのお問い合わせ 関連リンク "
                         "IR（機関投資家・アナリスト向け） 問い合わせフォーム - 個人株主 問い合わせフォーム "
                         "株式手続きのご案内 持株会 問い合わせフォーム",
    },
    "4046": {
        "company_name": "大阪ソーダ", "official_url": "https://www.osaka-soda.co.jp/",
        "parent_url": "https://www.osaka-soda.co.jp/ja/contact.html",
        "parent_snapshot": "evidence/4046/20261011T095054916048Z/03.json", "source_link_index": 16,
        "target_url": "https://www.osaka-soda.co.jp/form/ja/agree_07.html", "label": "IR、その他",
        "quote": "IR、その他",
        "section_quote": "事業・製品（化学品事業部） 事業・製品（機能材事業部） 事業・製品（ヘルスケア事業部） "
                         "採用 研究開発・開発品 サステナビリティ IR、その他 お取引先様相談窓口",
    },
}
COMPLETED_IDENTITY_PROPOSAL = {
    "path": "parts/adaptive-followup-data-46-identity-coverage-plan.json",
    "sha256": "cb1ed309408a1fd3ca07ea7b9cb59686618dcc72afba287b47dea9aa37d7f50c",
    "audit_path": "parts/adaptive-audit-data-46-batch03.json",
    "audit_sha256": "ca5f279be2550ed8568b26bc926ed394b7f3c4186bdbe33c603539e99faf8481",
    "reviewer": "codex_audit_data_46_batch03",
}
# These operator/holding links discover identity, never a reception channel.
# The duplicate holding label at 4651 index102 is deliberately not a fallback.
COMPLETED_IDENTITY_ROUTES = {
    "462A": {
        "company_name": "ＦＵＮＤＩＮＮＯ", "official_url": "https://fundinno.com/", "seed_company_name": "（株）ＦＵＮＤＩＮＮＯ",
        "parent_snapshot": "evidence/462A/20261011T122843060528Z/01.json",
        "parent_url": "https://fundinno.com/", "parent_requested_url": "https://fundinno.com/",
        "target_url": "https://corp.fundinno.com/company/", "source_link_index": 41, "label": "運営会社",
        "quote": "運営会社", "ir_transition_quote": None,
        "kind": "official_operator_company_info_discovery",
    },
    "4651": {
        "company_name": "サニックスホールディングス", "official_url": "https://sanix.jp/", "seed_company_name": "サニックス",
        "parent_snapshot": "evidence/4651/20261011T123147281914Z/06.json",
        "parent_url": "https://sanix.jp/customeroffice/formlist",
        "parent_requested_url": "https://sanix.jp/customeroffice/formlist/",
        "target_url": "https://hd.sanix.jp/", "source_link_index": 99,
        "label": "株式会社サニックスホールディングス",
        "quote": "2025年4月1日、サニックスグループは、 ホールディングス体制に移行いたしました（事業ごとに分社）。",
        "ir_transition_quote": "IR情報、採用情報、 グループ全体に関することは",
        "kind": "official_holding_company_transition_discovery",
    },
}
# Only these frozen, reviewed anchors may bypass the generic contact classifier.
# 6412 is bound to its final closed audit and separate root authority.
FINITE_REVIEWED_AUTHORITIES = {
    "6383": {
        "path": "parts/adaptive-followup-ir-6383-route177.json",
        "sha256": "aefab2ac13008bbe33c04402337fbe3ff2b1873220d55e96a5978b5debe44347",
        "record_sha256": "f084b329b80b0006e91ca5ad6f0e4bd137c91fc25a498a7769475ea77f72ee3c",
        "reviewer": "ir_operations_64_batch17", "binding_reviewer": "ir_operations_6383_route177",
        "company_name": "ダイフク", "official_url": "https://www.daifuku.com/jp/",
        "purpose": "ir_contact_followup",
        "historical_stop_snapshot": "evidence/6383/20261011T173437506705Z/04.json",
    },
    "6412": {
        "path": "parts/adaptive-followup-manufacturing-6412-identity.json",
        "sha256": "93bf27db8576a9f5709e9d4958ee8ec6cade8fb881e57a7f419b0362e4d95df7",
        "record_sha256": "41846364a374589a5f587eba2953a19cc4c9332e2fc77e1353b95c86728cb194",
        "reviewer": "codex_audit_manufacturing", "binding_reviewer": "codex_audit_manufacturing",
        "company_name": "平和", "official_url": "https://www.heiwanet.co.jp/",
        "purpose": "issuer_identity_discovery",
        "audit_path": "parts/adaptive-audit-manufacturing-64-batch35.json",
        "audit_sha256": "8e51c4eebe2fa640eb2e1db2f05532bc6ca634323e37e00df9d3ff4de9843035",
        "original_proposal_sha256": "0de47bf2569171c6fd83144049db16a7ba0cb6b37e36c9e70abe9cdff6173c46",
    },
    "6633": {
        "path": "parts/adaptive-followup-services-6633-identity.json",
        "sha256": "8acd57bdeae7398809308aa8d94963a3a30183f7baeb2fdcc2cfb5adaf951bcb",
        "record_sha256": "5d4849b26ec3edae6c7ef1a7bac7a07643af7b66a6461188f4c1a3cf69f16dbb",
        "record_logical_sha256": "1d63b61b19e5d2738a00d887996f7dec1d222e11f34e2ddfe8f43f4a34c25ed3",
        "reviewer": "codex_audit_services",
        "binding_reviewer": "root_6633_named_current_issuer_discovery",
        "company_name": "ＣＧＳホールディングス",
        "seed_company_name": "Ｃ＆Ｇシステムズ",
        "official_url": "https://www.cgsys.co.jp/",
        "purpose": "issuer_identity_discovery",
        "audit_path": "parts/adaptive-audit-services-66-batch19.json",
        "audit_sha256": "2f5a6718f7da80dff40cbfd908d9e5deb771076dd696f95ad64bf7320065c1f1",
        "original_proposal_path": "/tmp/ir-followup-6633-proposal-20261011.json",
        "original_proposal_sha256": "1b336de9e709d2c48afcf5dff7e52420ff13507881458bf76537330e79c76bdc",
        "source_references": [
            "evidence/6633/20261011T183222056139Z/01.json",
            "evidence/6633/20261011T183222056139Z/02.json",
            "evidence/6633/01.json",
            "evidence/6633/20261011T045059691094Z/01.json",
            "attempts/6633/20261011T045047608008Z.json",
            "attempts/6633/20261011T183310173403Z.json"
        ]
    },
}
FINITE_REVIEWED_ROUTES = {
    "6383": [{
        "snapshot": "evidence/6383/20261011T173437506705Z/03.json", "index": 177,
        "parent_url": "https://www.daifuku.com/jp/contact/",
        "target_url": "https://inquiry.daifuku.com/others_jp",
        "quote": "製品以外のお問い合わせ 採用、IR、サステナビリティ、広報、日に新た館については、こちらからお問い合わせください。",
        "label": "製品以外のお問い合わせ 採用、IR、サステナビリティ、広報、日に新た館については、こちらからお問い合わせください。",
        "evidence_role": "official_ir_parent",
    }],
    "6412": [{
        "snapshot": "evidence/6412/20261011T174052096054Z/01.json", "index": 16,
        "parent_url": "https://www.heiwanet.co.jp/", "target_url": "https://www.heiwa-hd.co.jp/ja/",
        "quote": "2026年10月1日より株式会社平和は商号変更により株式会社平和ホールディングスとなり、持株会社体制へ移行しました。 株式会社平和ホールディングスのHPは こちら",
        "label": "こちら", "evidence_role": "issuer_migration_notice",
    }, {
        "snapshot": "evidence/6412/20261011T174052096054Z/03.json", "index": 18,
        "parent_url": "https://www.heiwanet.co.jp/company/faq/mail/",
        "parent_requested_url": "https://www.heiwanet.co.jp/faq/mail/",
        "target_url": "https://www.heiwa-hd.co.jp/ja/inquiry/contact//",
        "quote": "当社グループのIRや株主優待に関するお問い合わせ、ご質問については、 平和ホールディングスのFAQ・お問い合わせ よりご確認の程お願い致します。",
        "label": "平和ホールディングスのFAQ・お問い合わせ", "evidence_role": "ir_route_migration_notice",
    }],
    "6633": [
        {
            "snapshot": "evidence/6633/20261011T183222056139Z/01.json",
            "index": 41,
            "parent_url": "https://www.cgsys.co.jp/",
            "target_url": "https://www.cgshd.co.jp/",
            "quote": "CGSホールディングスのサイトへ",
            "label": "CGSホールディングスのサイトへ",
            "evidence_role": "actual_named_current_holding_site_identity_discovery_only"
        }
    ],
}
SITE_MOVE = re.compile(r"(?:WEB\s*サイト|ウェブサイト|ホームページ|(?:公式)?サイト).{0,45}(?:移転|移行)", re.I)
CODE = re.compile(r"[0-9]{3}[0-9A-Z]\Z")
OTHER = re.compile(r"採用|製品|商品|店舗|株主優待|営業|資料請求|お客様|お客さま|カタログ|広告|privacy|policy|recruit|career|customer|sales|よくある|FAQ", re.I)
SESSION_KEY = re.compile(r"sid|(?:php|j)?sess(?:ion)?(?:_?id)?|auth(?:_?token)?|access_?token|token|nonce|csrf", re.I)
BAD_PATH = re.compile(r"(?:^|[/;])(?:search|submit|send|confirm|delete|update|session)(?:[/;._-]|$)|CreateDocument|[;?]jsessionid=", re.I)
TRACKER = re.compile(r"googletagmanager|google-analytics|doubleclick|facebook\.com/tr|GTM-", re.I)
CONTACT_ROUTE = re.compile(r"contact|inquir|toiawase|otoiawase|inqform|(?:^|[/_.-])(?:forms?|formir|input)[0-9]*(?:$|[/_.-])", re.I)
OTHER_PATH = re.compile(r"/(?:privacy[^/]*|recruit(?:ment)?|career|search|faq|catalog[^/]*|customer|sales|adinfo|agency|trafficsafety|abuse|exemption|ticker|widget)(?:/|[._-]|$)", re.I)
IR_INTAKE = re.compile(r"(?<![A-Za-z0-9])(?:IR|ＩＲ|投資家)\s*(?:(?:情報)?\s*(?:に関する|についての|の)\s*)?(?:お問い合わせ|お問合せ|問合せ|問い合わせ|ご質問)", re.I)
IR_DISCOVERY_ROUTE = re.compile(r"(?:^|/)(?:ir|investors?)(?:/?$|/(?:faq|disclosure[-_]?policy|policy)(?:[/\.]|$))", re.I)
NO_CONTENT_GET = {"environment_circuit_breaker_open", "robots_disallowed", "robots_access_denied_stopped",
                  "robots_unreachable_stopped", "host_access_denied_stopped", "followup_get_limit_reached",
                  "unlinked_redirect_host", "unsafe_followup_url"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_url(value: object) -> str | None:
    """Public HTTP(S) only; no session URLs, executable actions, or tracking URLs."""
    if not isinstance(value, str) or re.search(r"[\s\x00-\x1f\x7f\\]", value):
        return None
    try:
        value = urldefrag(value)[0]
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in {"https", "http"} or parsed.username or parsed.password:
            return None
        if not host or "." not in host or host.endswith((".localhost", ".local", ".internal")):
            return None
        if parsed.port not in {None, 80, 443}:
            return None
        try:
            if not ipaddress.ip_address(host).is_global:
                return None
        except ValueError:
            if any(part.lower().startswith("0x") for part in host.split(".")) or host.replace(".", "").isdigit():
                return None
        if research.SKIP_URL.search(value) or TRACKER.search(value) or BAD_PATH.search(unquote(parsed.path)):
            return None
        if any(SESSION_KEY.fullmatch(key) for key, _ in parse_qsl(parsed.query, keep_blank_values=True)):
            return None
        return value
    except (ValueError, UnicodeError):
        return None


def host_key(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower().rstrip(".")
    return host.removeprefix("www.")


def origin_key(url: str) -> tuple[str, str, int]:
    parsed = urlsplit(url)
    return (parsed.scheme.lower(), (parsed.hostname or "").lower().rstrip("."),
            parsed.port or (443 if parsed.scheme == "https" else 80))


def url_key(url: str) -> str:
    parsed = urlsplit(url)
    return parsed._replace(netloc=parsed.netloc.lower(), fragment="").geturl()


def evidence_path(output: Path, relative: object) -> Path | None:
    if not isinstance(relative, str):
        return None
    path = (output / relative).resolve()
    # Allow the immutable older survey evidence, but no arbitrary filesystem paths.
    roots = [output / "evidence", *(p / "evidence" for p in output.parent.glob("ir-contacts*"))]
    return path if path.suffix == ".json" and any(path.is_relative_to(p.resolve()) for p in roots) else None


def proposal_rows(output: Path) -> dict[str, list[dict]]:
    rows: dict[str, list[dict]] = {}
    fields = ("followups", "followup_get_candidates", "additional_get_candidates", "recommended_urls", "todos", "todo", "followup_candidates")
    paths = sorted({p for pattern in ("adaptive-followup-*.json", "adaptive-audit-*.json", "adaptive-old-audit-*.json")
                    for p in (output / "parts").glob(pattern)})
    for path in paths:
        if path.stem.endswith("-plan"):
            continue
        data = read_json(path)
        containers = [data, *data.get("records", []), *data.get("companies", []),
                      *data.get("reviews", []), *data.get("inspections", []), *data.get("reviewed", [])]
        for container in containers:
            if not isinstance(container, dict):
                continue
            container_code = container.get("security_code")
            if isinstance(container_code, str) and CODE.fullmatch(container_code):
                sources = [item.get("snapshot") for field in ("evidence", "sources", "new_evidence", "added_evidence", "new_exact_evidence")
                           for item in container.get(field, []) if isinstance(item, dict)]
                sources += container.get("reviewed_snapshot_paths", [])
                rows.setdefault(container_code, []).extend(
                    {"associated_snapshot": source, "proposal_source": str(path.relative_to(output))}
                    for source in sources if isinstance(source, str))
                rows[container_code].extend(
                    {"binding_evidence": item, "proposal_source": str(path.relative_to(output))}
                    for field in ("evidence", "new_evidence") for item in container.get(field, [])
                    if isinstance(item, dict) and item.get("source_link_url"))
            for field in fields:
                for item in container.get(field, []):
                    if not isinstance(item, dict):
                        continue
                    code = item.get("security_code", container.get("security_code"))
                    if isinstance(code, str) and CODE.fullmatch(code):
                        normalized = dict(item)
                        if "url" not in normalized and "target_url" in normalized:
                            normalized["url"] = normalized["target_url"]
                        if "parent_url" not in normalized and "source_url" in normalized:
                            normalized["parent_url"] = normalized["source_url"]
                        rows.setdefault(code, []).append({**normalized, "proposal_source": str(path.relative_to(output))})
    return rows


def saved_pages(output: Path, record: dict, proposals: list[dict]) -> list[tuple[str, dict]]:
    references = [x.get("snapshot") for field in ("fetches", "evidence") for x in record.get(field, [])]
    references += [x.get("parent_snapshot") or x.get("source_snapshot") for x in proposals]
    references += [x.get("associated_snapshot") for x in proposals]
    # Older archived attempts still count as already fetched; do not repeat them.
    for relative in record.get("previous_attempts", []):
        path = (output / relative).resolve()
        if path.is_relative_to((output / "attempts").resolve()) and path.is_file():
            old = read_json(path)
            references += [x.get("snapshot") for field in ("fetches", "evidence") for x in old.get(field, [])]
    pages = []
    for reference in dict.fromkeys(x for x in references if isinstance(x, str)):
        path = evidence_path(output, reference)
        if path and path.is_file():
            page = read_json(path)
            if isinstance(page, dict) and page.get("security_code", record["security_code"]) == record["security_code"]:
                pages.append((reference, page))
    return pages


def responses(page: dict):
    yield page
    for redirect in page.get("redirects", []):
        yield from responses(redirect)
    if isinstance(page.get("robots"), dict):
        yield from responses(page["robots"])


def latest_robots(pages: list[tuple[str, dict]]) -> dict[tuple[str, str, int], dict]:
    """A transport failure is a current route gap, superseded by newer robots."""
    latest: dict[tuple[str, str, int], tuple[datetime, dict]] = {}
    for _, page in pages:
        candidates = [page["robots"]] if isinstance(page.get("robots"), dict) else []
        if any(safe_url(page.get(field)) and urlsplit(page[field]).path == "/robots.txt" for field in ("url", "requested_url")):
            candidates.append(page)
        for robot in candidates:
            redirects = robot.get("redirects", [])
            original = redirects[0].get("requested_url") if redirects else None
            original = original or robot.get("requested_url") or robot.get("url")
            if not safe_url(original):
                continue
            try:
                stamp = datetime.fromisoformat(robot.get("retrieved_at", ""))
                if stamp.tzinfo is None:
                    raise ValueError("naive robots timestamp")
            except (ValueError, TypeError):
                stamp = datetime.min.replace(tzinfo=timezone.utc)
            origin = origin_key(original)
            if origin not in latest or stamp >= latest[origin][0]:
                latest[origin] = (stamp, robot)
    return {origin: robot for origin, (_, robot) in latest.items()}



def saved_robots_literal_correction(output: Path, url: str, blocked: list[tuple[str, dict]],
                                    latest: dict | None, pages: list[tuple[str, dict]]) -> dict | None:
    """Revisit only a demonstrably incorrect saved literal-rule block.

    Both the latest policy and every historical stop must prove the same
    origin's first-match error. A changed/unknown policy alone is not enough.
    The old evidence is never rewritten; fresh dispatch still checks robots.
    """
    def qualifies(robot):
        if not isinstance(robot, dict) or robot.get("http_status") != 200 or robot.get("error") or robot.get("robots_failure_reason"):
            return False
        redirects = robot.get("redirects", [])
        original = (redirects[0].get("requested_url") if redirects else None) or robot.get("requested_url") or robot.get("url")
        if not safe_url(original) or urlsplit(original).path != "/robots.txt" or origin_key(original) != origin_key(url):
            return False
        try:
            if datetime.fromisoformat(robot.get("retrieved_at", "")).tzinfo is None:
                return False
        except (TypeError, ValueError):
            return False
        parser = RobotFileParser()
        parser.parse(robot.get("text", "").splitlines())
        return research.robots_specific_allow_correction(parser, research.USER_AGENT, url)

    if not blocked or not qualifies(latest):
        return None
    # An undated same-origin observation makes "latest" uncertain. Keep the
    # existing stop rather than use a guessed temporal ordering to clear it.
    for row in pages:
        robot = latest_robots([row]).get(origin_key(url))
        if robot is not None:
            try:
                if datetime.fromisoformat(robot.get("retrieved_at", "")).tzinfo is None:
                    return None
            except (TypeError, ValueError):
                return None
    for _, event in blocked:
        if event.get("http_get_attempted") is not False or not qualifies(event.get("robots")):
            return None
    references = [ref for ref, page in pages if page is latest or page.get("robots") is latest]
    if not references:
        return None
    refs = sorted({*references, *(ref for ref, _ in blocked)})
    hashes = {ref: file_sha256(evidence_path(output, ref)) for ref in refs}
    return {"basis": "saved_same_origin_more_specific_literal_allow_corrects_first_match",
            "source_snapshot_sha256": hashes, "latest_robots_source_snapshots": references,
            "latest_robots_retrieved_at": latest["retrieved_at"],
            "latest_robots_text_sha256": hashlib.sha256(latest.get("text", "").encode()).hexdigest(),
            "historical_stop_snapshots": sorted({ref for ref, _ in blocked}),
            "historical_events_preserved": True, "financial_ir_reception_verified": False}


def ir_parent(page: dict) -> bool:
    heading = " ".join([page.get("title", ""), *page.get("headings", [])[:1]])
    return not OTHER.search(heading) and bool(research.IR.search(heading) or research.IR_PATH.search(urlsplit(page.get("url", "")).path))


def link_priority(page: dict, link: dict, ir_bound: bool = False) -> int | None:
    label, url = link.get("label", ""), safe_url(link.get("url"))
    if not url or OTHER.search(label):
        return None
    path = urlsplit(url).path
    if OTHER_PATH.search(path):
        return None
    if research.IR_CONTACT.search(label):
        return 0
    if research.IR_PATH.search(path) and CONTACT_ROUTE.search(path):
        return 1
    if ir_parent(page) and (research.CONTACT.search(label) or CONTACT_ROUTE.search(path)):
        return 2
    if label == "embedded frame" and (ir_bound or ir_parent(page) and research.IR_CONTACT.search(
            " ".join([page.get("title", ""), *page.get("headings", [])[:1]]))):
        frames = [item for item in page.get("links", []) if item.get("label") == "embedded frame"
                  and safe_url(item.get("url")) and not OTHER_PATH.search(urlsplit(item["url"]).path)]
        if len(frames) == 1:
            return 2
    return None


def observed_identity(record: dict, page: dict) -> bool:
    name = research.identity_key(record.get("company_name", ""))
    text = page.get("text", "")
    return bool((len(name) >= 3 and name in research.identity_key(text)) or
                re.search(r"(?<![0-9A-Z])" + re.escape(record["security_code"]) + r"(?![0-9A-Z])", text))


def has_identity(record: dict, page: dict) -> bool:
    return record.get("identity_status") in {"previous_verified", "name_or_security_code_observed"} or observed_identity(record, page)


def quoted_link_bindings(record: dict, proposals: list[dict], pages: dict[str, dict]) -> dict[tuple[str, int], dict]:
    """Bind a generic label only by an exact IR intake quotation and real link."""
    evidence = [*record.get("evidence", []), *(p["binding_evidence"] for p in proposals if "binding_evidence" in p)]
    bindings = {}
    for item in evidence:
        page = pages.get(item.get("snapshot"))
        target, quote = safe_url(item.get("source_link_url")), item.get("quote", "")
        if not page or not target or not isinstance(quote, str) or quote not in page.get("text", ""):
            continue
        match = IR_INTAKE.search(quote)
        if not match or item.get("url") and url_key(item["url"]) != url_key(page["url"]):
            continue
        for index, link in enumerate(page.get("links", [])):
            label = link.get("label", "")
            start = quote.find(label, match.start()) if label else -1
            if (safe_url(link.get("url")) == target and start >= 0 and research.CONTACT.search(label)
                    and not OTHER.search(label)
                    and not re.search(r"採用|製品|商品|店舗|株主優待|営業", quote[match.end():start])):
                bindings[(item["snapshot"], index)] = {key: item[key] for key in ("snapshot", "url", "retrieved_at", "quote", "source_link_url") if key in item}
    return bindings


def matching_proposal(proposal: dict, reference: str, page: dict, link: dict) -> bool:
    quote = proposal.get("quote")
    return (str(proposal.get("method", "GET")).upper() == "GET" and safe_url(proposal.get("url")) == safe_url(link.get("url"))
            and (proposal.get("parent_snapshot") or proposal.get("source_snapshot")) == reference
            and url_key(proposal.get("parent_url", page["url"])) == url_key(page["url"])
            and (not quote or isinstance(quote, str) and (quote in page.get("text", "") or quote == link.get("label", ""))))


def identity_discovery_bindings(output: Path, record: dict, proposals: list[dict], pages: dict[str, dict],
                                proof_record_sha256: str | None = None) -> dict[tuple[str, int], dict]:
    """Only three reviewed migration routes; never establish a contact channel."""
    code, review = record["security_code"], record.get("manual_review", {})
    if (code not in IDENTITY_DISCOVERY_CODES or record.get("manual_review_required") is not False
            or not isinstance(review, dict) or not review.get("reviewer")):
        return {}
    try:
        reviewed_at = datetime.fromisoformat(review.get("reviewed_at", ""))
        if reviewed_at.tzinfo is None:
            return {}
    except (ValueError, TypeError):
        return {}
    expected_name = research.identity_key(record.get("company_name", ""))
    official = safe_url(record.get("official_url"))
    roles = {"2300": "official_site_move", "3440": "holding_company_transition_notice", "3695": "issuer_site_migration"}
    result = {}
    for item in record.get("evidence", []):
        reference, quote = item.get("snapshot"), item.get("quote", "")
        page = pages.get(reference)
        if (not page or not official or item.get("role", item.get("purpose")) != roles[code]
                or not isinstance(quote, str) or not quote or quote not in page.get("text", "")
                or host_key(page["url"]) != host_key(official)
                or item.get("url") != page["url"]):
            continue
        try:
            retrieved_at = datetime.fromisoformat(page.get("retrieved_at", ""))
            if retrieved_at.tzinfo is None or retrieved_at > reviewed_at or item.get("retrieved_at") != page.get("retrieved_at"):
                continue
        except (ValueError, TypeError):
            continue
        name_observed = len(expected_name) >= 3 and expected_name in research.identity_key(quote)
        if code in {"2300", "3695"} and (not name_observed or not SITE_MOVE.search(quote)):
            continue
        if code == "3695" and not ("持株会社" in quote and "社名" in quote and "本サイトは子会社" in quote):
            continue
        if code == "3440":
            legacy_name = research.identity_key(record.get("discovery", {}).get("seed_company_name", ""))
            if (len(legacy_name) < 3 or legacy_name not in research.identity_key(page.get("title", ""))
                    or not re.search(r"持株会社.*移行.*ホームページリニューアル", quote)):
                continue
        eligible = []
        for index, link in enumerate(page.get("links", [])):
            target = safe_url(link.get("url"))
            if not target:
                continue
            if code == "2300":
                public_links = {safe_url(x.get("url")) for x in page.get("links", []) if safe_url(x.get("url"))}
                if len(public_links) != 1 or target not in page.get("text", ""):
                    continue
            elif code == "3695":
                if research.identity_key(link.get("label", "")) != expected_name:
                    continue
            elif (host_key(target) != host_key(page["url"]) or not urlsplit(target).path.startswith("/news/")
                  or link.get("label") != quote or target != item.get("source_link_url")):
                continue
            matching = [p for p in proposals if matching_proposal(p, reference, page, link)]
            source_sha = file_sha256(evidence_path(output, reference))
            matching = [p for p in matching if not p.get("source_snapshot_sha256") or p["source_snapshot_sha256"] == source_sha]
            if matching:
                eligible.append((index, link, matching[0], source_sha))
        if len({link["url"] for _, link, _, _ in eligible}) != 1:
            continue
        for index, link, proposal, source_sha in eligible:
            proof = {"kind": "holding_company_transition_notice_discovery" if code == "3440" else "official_issuer_site_migration_discovery",
                "purpose": "issuer_identity_discovery", "current_jpx_company_name": record["company_name"],
                "current_issuer_name_observed_in_notice": name_observed, "identity_status": record.get("identity_status"),
                "IR_purpose_verified": False, "current_issuer_reception_verified": False,
                "manual_reviewer": review["reviewer"], "manual_reviewed_at": review["reviewed_at"],
                "quote": quote, "source_snapshot": reference, "source_snapshot_sha256": source_sha,
                "source_url": page["url"], "source_retrieved_at": page["retrieved_at"],
                "source_link_index": index, "source_link": copy.deepcopy(link),
                "source_record_sha256": proof_record_sha256 or file_sha256(output / "records" / (code + ".json")),
                "proposal_source": proposal["proposal_source"],
                "proposal_source_sha256": file_sha256(output / proposal["proposal_source"])}
            result[(reference, index)] = proof
    return result


def identity_reference_bindings(output: Path, record: dict, proposals: list[dict], pages: dict[str, dict],
                                proof_record_sha256: str | None = None) -> dict[tuple[str, int], dict]:
    """Bind only the three audited Japanese/company-info routes to frozen sources."""
    code = record["security_code"]
    route, review = IDENTITY_REFERENCE_ROUTES.get(code), record.get("manual_review", {})
    if (not route or record.get("manual_review_required") is not False or not isinstance(review, dict)
            or not review.get("reviewer") or record.get("company_name") != route["company_name"]
            or record.get("official_url") != route["official_url"]):
        return {}
    discovery = record.get("discovery", {})
    if (not isinstance(discovery, dict) or discovery.get("seed_company_name") != route["company_name"]
            or discovery.get("official_url") != route["official_url"]):
        return {}
    reference, audit_path = route["parent_snapshot"], output / IDENTITY_REFERENCE_AUDIT
    page = pages.get(reference)
    if (not page or page.get("url") != route["parent_url"]
            or host_key(page["url"]) != host_key(route["official_url"])
            or route["public_issuer_quote"] not in page.get("text", "") or not audit_path.is_file()):
        return {}
    try:
        reviewed_at = datetime.fromisoformat(review.get("reviewed_at", ""))
        retrieved_at = datetime.fromisoformat(page.get("retrieved_at", ""))
        if reviewed_at.tzinfo is None or retrieved_at.tzinfo is None or reviewed_at < retrieved_at:
            return {}
    except (ValueError, TypeError):
        return {}
    audit = read_json(audit_path)
    rows = [row for row in audit.get("reviewed", []) if isinstance(row, dict) and row.get("security_code") == code]
    if len(rows) != 1 or audit.get("reviewer") != review["reviewer"]:
        return {}
    row = rows[0]
    source_sha = file_sha256(evidence_path(output, reference))
    record_sha = proof_record_sha256 or file_sha256(output / "records" / (code + ".json"))
    if (row.get("company_name") != record["company_name"] or row.get("reviewed_at") != review["reviewed_at"]
            or row.get("record_sha256_after_review") != record_sha
            or row.get("original_evidence_sha256", {}).get(reference) != source_sha):
        return {}
    result = {}
    for index, link in enumerate(page.get("links", [])):
        for target, label, kind in route["links"]:
            if (link.get("url") != target or link.get("href") != target or link.get("label") != label
                    or label not in page.get("text", "")):
                continue
            matching = [p for p in proposals if p.get("proposal_source") == IDENTITY_REFERENCE_AUDIT
                        and p.get("quote") == label and matching_proposal(p, reference, page, link)]
            if not matching:
                continue
            result[(reference, index)] = {
                "kind": kind, "purpose": "issuer_identity_discovery",
                "current_jpx_company_name": record["company_name"], "seed_company_name": discovery["seed_company_name"],
                "official_seed_url": discovery["official_url"], "identity_status": record.get("identity_status"),
                "current_issuer_name_observed_in_source": observed_identity(record, page),
                "IR_purpose_verified": False, "current_issuer_reception_verified": False,
                "manual_reviewer": review["reviewer"], "manual_reviewed_at": review["reviewed_at"],
                "quote": label, "public_issuer_quote": route["public_issuer_quote"],
                "source_snapshot": reference, "source_snapshot_sha256": source_sha,
                "source_url": page["url"], "source_retrieved_at": page["retrieved_at"],
                "source_link_index": index, "source_link": copy.deepcopy(link), "source_record_sha256": record_sha,
                "proposal_source": IDENTITY_REFERENCE_AUDIT, "proposal_source_sha256": file_sha256(audit_path),
                "association_basis": "saved_reviewed_official_language_or_company_info_link; issuer identity and reception require new review",
            }
    return result


def ir_portal_reference_binding(output: Path, record: dict, proposals: list[dict], pages: dict[str, dict],
                                proof_record_sha256: str | None = None) -> dict[tuple[str, int], dict]:
    """One reviewed portal reference; neither issuer identity nor IR intake."""
    route, review = IR_PORTAL_REFERENCE, record.get("manual_review", {})
    discovery = record.get("discovery", {})
    if (record.get("security_code") != route["security_code"]
            or record.get("company_name") != route["company_name"]
            or record.get("official_url") != route["official_url"]
            or record.get("manual_review_required") is not False or not isinstance(review, dict)
            or review.get("reviewer") != route["reviewer"]
            or record.get("investigation_status") != "unconfirmed" or record.get("identity_status") != "unverified"
            or record.get("verification_level") != "none" or record.get("public_ir_emails") != []
            or not isinstance(discovery, dict) or discovery.get("seed_company_name") != route["company_name"]
            or discovery.get("official_url") != route["official_url"]):
        return {}
    reference, index = route["parent_snapshot"], route["source_link_index"]
    page, audit_path = pages.get(reference), output / route["audit_snapshot"]
    if (not page or page.get("url") != route["parent_url"] or not audit_path.is_file()
            or page.get("text", "").count(route["quote"]) != 1
            or file_sha256(evidence_path(output, reference)) != route["source_sha256"]
            or file_sha256(audit_path) != route["audit_sha256"]):
        return {}
    record_sha = proof_record_sha256 or file_sha256(output / "records" / (route["security_code"] + ".json"))
    if record_sha != route["record_sha256"]:
        return {}
    try:
        reviewed_at = datetime.fromisoformat(review.get("reviewed_at", ""))
        retrieved_at = datetime.fromisoformat(page.get("retrieved_at", ""))
        link = page["links"][index]
        if reviewed_at.tzinfo is None or retrieved_at.tzinfo is None or reviewed_at < retrieved_at:
            return {}
    except (ValueError, TypeError, KeyError, IndexError):
        return {}
    if (link.get("url") != route["target_url"] or link.get("href") != route["target_url"]
            or link.get("label") != route["quote"]):
        return {}
    audit = read_json(audit_path)
    rows = [row for row in audit.get("reviewed", []) if isinstance(row, dict)
            and row.get("security_code") == route["security_code"]]
    if (audit.get("status") != "completed" or audit.get("pending_validation") != []
            or audit.get("reviewer") != review["reviewer"] or len(rows) != 1
            or rows[0].get("company_name") != record["company_name"]
            or rows[0].get("reviewed_at") != review["reviewed_at"]
            or rows[0].get("record_sha256_after_review") != record_sha
            or rows[0].get("original_evidence_sha256", {}).get(reference) != route["source_sha256"]):
        return {}
    exact_evidence = [e for e in record.get("evidence", []) if isinstance(e, dict)
        and e.get("snapshot") == reference and e.get("url") == page["url"]
        and e.get("retrieved_at") == page["retrieved_at"] and e.get("quote") == route["quote"]
        and e.get("role") == "ir_issuer_transition_link" and e.get("source_link_url") == link["url"]]
    matching = [p for p in proposals if p.get("proposal_source") == route["audit_snapshot"]
        and p.get("quote") == route["quote"] and matching_proposal(p, reference, page, link)]
    if not exact_evidence or not matching:
        return {}
    return {(reference, index): {
        "kind": "official_ir_portal_reference_discovery", "purpose": "issuer_identity_discovery",
        "current_jpx_company_name": record["company_name"], "current_jpx_security_code": record["security_code"],
        "seed_company_name": discovery["seed_company_name"], "official_seed_url": discovery["official_url"],
        "identity_status": record["identity_status"], "current_issuer_identity_verified": False,
        "current_issuer_name_observed_in_source": False, "IR_purpose_verified": False,
        "current_issuer_reception_verified": False,
        "manual_reviewer": review["reviewer"], "manual_reviewed_at": review["reviewed_at"],
        "quote": route["quote"], "source_snapshot": reference,
        "source_snapshot_sha256": route["source_sha256"], "source_url": page["url"],
        "source_retrieved_at": page["retrieved_at"], "source_link_index": index, "source_link": copy.deepcopy(link),
        "source_record_sha256": record_sha, "proposal_source": route["audit_snapshot"],
        "proposal_source_sha256": route["audit_sha256"],
        "association_basis": "saved_reviewed_exact_shareholder_information_portal_reference; issuer identity and reception require new review",
    }}


def reviewed_ir_route_bindings(output: Path, record: dict, proposals: list[dict], pages: dict[str, dict],
                               proof_record_sha256: str | None = None) -> dict[tuple[str, int], dict]:
    """The two audited IR table/label routes, with no claim about input fields."""
    code = record["security_code"]
    route, review = REVIEWED_IR_ROUTES.get(code), record.get("manual_review", {})
    if (not route or record.get("manual_review_required") is not False or not isinstance(review, dict)
            or review.get("reviewer") != "codex_audit_manufacturing"
            or record.get("company_name") != route["company_name"]
            or record.get("official_url") != route["official_url"]
            or record.get("contact_url") != route["target_url"]):
        return {}
    discovery = record.get("discovery", {})
    if (not isinstance(discovery, dict) or discovery.get("seed_company_name") != route["company_name"]
            or discovery.get("official_url") != route["official_url"]):
        return {}
    reference, index = route["parent_snapshot"], route["source_link_index"]
    page, part_path = pages.get(reference), output / REVIEWED_IR_AUDIT
    if (not page or page.get("url") != route["parent_url"] or not part_path.is_file()
            or host_key(page["url"]) != host_key(route["official_url"])
            or page.get("text", "").count(route["quote"]) != 1
            or page.get("text", "").count(route["section_quote"]) != 1):
        return {}
    try:
        reviewed_at = datetime.fromisoformat(review.get("reviewed_at", ""))
        retrieved_at = datetime.fromisoformat(page.get("retrieved_at", ""))
        if reviewed_at.tzinfo is None or retrieved_at.tzinfo is None or reviewed_at < retrieved_at:
            return {}
        link = page["links"][index]
    except (ValueError, TypeError, IndexError, KeyError):
        return {}
    if (link.get("url") != route["target_url"] or link.get("label") != route["label"]
            or research.urljoin(page["url"], link.get("href", "")) != route["target_url"]):
        return {}
    part = read_json(part_path)
    rows = [r for r in part.get("reviewed", []) if isinstance(r, dict) and r.get("security_code") == code]
    record_sha = proof_record_sha256 or file_sha256(output / "records" / (code + ".json"))
    source_sha = file_sha256(evidence_path(output, reference))
    if (part.get("reviewer") != review["reviewer"] or len(rows) != 1
            or rows[0].get("saved") is not True or rows[0].get("company_name") != route["company_name"]
            or rows[0].get("reviewed_at") != review["reviewed_at"]
            or rows[0].get("record_sha256_after_review") != record_sha
            or rows[0].get("original_evidence_sha256", {}).get(reference) != source_sha):
        return {}
    exact_evidence = [e for e in record.get("evidence", []) if isinstance(e, dict)
        and e.get("snapshot") == reference and e.get("url") == page["url"]
        and e.get("retrieved_at") == page["retrieved_at"] and e.get("quote") == route["quote"]
        and e.get("source_link_url") == link["url"] and e.get("source_link_index") == index]
    matching = [p for p in proposals if p.get("proposal_source") == REVIEWED_IR_AUDIT
        and p.get("source_link_index") == index and p.get("source_sha256") == source_sha
        and p.get("record_sha256_after_review") == record_sha and p.get("reviewer") == review["reviewer"]
        and p.get("quote") == route["quote"] and p.get("ir_scope_verified") is True
        and p.get("source_link") == link and matching_proposal(p, reference, page, link)]
    if not exact_evidence or not matching:
        return {}
    return {(reference, index): {
        "kind": "reviewed_financial_ir_contact_section", "purpose": "ir_contact_followup",
        "current_jpx_company_name": record["company_name"], "official_seed_url": route["official_url"],
        "IR_purpose_verified": True, "actual_form_fields_verified": False,
        "current_issuer_reception_verified": False,
        "individual_access": record.get("individual_access"), "outreach_suitability": record.get("outreach_suitability"),
        "manual_reviewer": review["reviewer"], "manual_reviewed_at": review["reviewed_at"],
        "quote": route["quote"], "section_quote": route["section_quote"],
        "source_snapshot": reference, "source_snapshot_sha256": source_sha, "source_url": page["url"],
        "source_retrieved_at": page["retrieved_at"], "source_link_index": index, "source_link": copy.deepcopy(link),
        "source_record_sha256": record_sha, "proposal_source": REVIEWED_IR_AUDIT,
        "proposal_source_sha256": file_sha256(part_path),
    }}


def completed_identity_bindings(output: Path, record: dict, pages: dict[str, dict],
                                proof_record_sha256: str | None = None) -> dict[tuple[str, int], dict]:
    """Only the two immutable, completed operator/holding discovery proposals."""
    code = record["security_code"]
    route, review = COMPLETED_IDENTITY_ROUTES.get(code), record.get("manual_review", {})
    discovery = record.get("discovery", {})
    frozen = COMPLETED_IDENTITY_PROPOSAL
    if (not route or record.get("company_name") != route["company_name"]
            or record.get("official_url") != route["official_url"]
            or record.get("manual_review_required") is not False or not isinstance(review, dict)
            or review.get("reviewer") != frozen["reviewer"]
            or record.get("investigation_status") != "unconfirmed" or record.get("verification_level") != "none"
            or record.get("channels") != [] or record.get("public_ir_emails") != []
            or record.get("contact_url") is not None or record.get("individual_access") != "not_stated"
            or record.get("outreach_suitability") != "unconfirmed" or not isinstance(discovery, dict)
            or discovery.get("security_code") != code or discovery.get("official_url") != route["official_url"]
            or discovery.get("seed_company_name") != route["seed_company_name"]):
        return {}
    try:
        proposal_path, audit_path = output / frozen["path"], output / frozen["audit_path"]
        if (not proposal_path.is_file() or not audit_path.is_file()
                or file_sha256(proposal_path) != frozen["sha256"]
                or file_sha256(audit_path) != frozen["audit_sha256"]):
            return {}
        packet, audit = read_json(proposal_path), read_json(audit_path)
        proposed = packet.get("finite_discovery_proposals", [])
        if (len(proposed) != 2 or {p.get("security_code") for p in proposed} != set(COMPLETED_IDENTITY_ROUTES)
                or packet.get("completed_audit_part") != frozen["audit_path"]
                or packet.get("completed_audit_sha256") != frozen["audit_sha256"]
                or audit.get("status") != "closed" or audit.get("scope_closed") is not True
                or audit.get("reviewer") != frozen["reviewer"] or audit.get("pending_security_codes") != []):
            return {}
        proposal = next(p for p in proposed if p["security_code"] == code)
        reference, index = route["parent_snapshot"], route["source_link_index"]
        page, source_path = pages.get(reference), evidence_path(output, reference)
        record_sha = proof_record_sha256 or file_sha256(output / "records" / (code + ".json"))
        if (not page or not source_path or file_sha256(source_path) != proposal.get("parent_snapshot_sha256")
                or record_sha != proposal.get("source_record_sha256")
                or proposal.get("company_name") != route["company_name"]
                or proposal.get("official_seed_url") != route["official_url"]
                or proposal.get("source_record_path") != "records/" + code + ".json"
                or proposal.get("source_audit_part") != frozen["audit_path"]
                or proposal.get("source_audit_sha256") != frozen["audit_sha256"]
                or proposal.get("parent_snapshot") != reference or proposal.get("source_link_index") != index
                or proposal.get("parent_url") != route["parent_url"]
                or proposal.get("parent_requested_url") != route["parent_requested_url"]
                or proposal.get("url") != route["target_url"] or proposal.get("target_url") != route["target_url"]
                or proposal.get("quote") != route["quote"] or proposal.get("kind") != route["kind"]
                or proposal.get("ir_transition_quote") != route["ir_transition_quote"]
                or proposal.get("method") != "GET" or proposal.get("purpose") != "issuer_identity_discovery"
                or any(proposal.get(key) is not False for key in (
                    "current_issuer_identity_verified", "IR_purpose_verified", "current_issuer_reception_verified"))
                or page.get("security_code") != code or page.get("url") != route["parent_url"]
                or page.get("requested_url") != route["parent_requested_url"]
                or page.get("retrieved_at") != proposal.get("parent_retrieved_at")
                or page.get("http_status") != 200 or page.get("error") or page.get("http_get_attempted") is not True
                or route["quote"] not in page.get("text", "")
                or (route["ir_transition_quote"] and route["ir_transition_quote"] not in page.get("text", ""))):
            return {}
        link = page["links"][index]
        if (link != proposal.get("source_link") or link.get("url") != route["target_url"]
                or link.get("href") != route["target_url"] or link.get("label") != route["label"]
                or safe_url(link["url"]) != link["url"]):
            return {}
        reviewed_at = datetime.fromisoformat(review["reviewed_at"])
        retrieved_at = datetime.fromisoformat(page["retrieved_at"])
        completed_at = datetime.fromisoformat(audit["completed_at_utc"])
        if (any(t.tzinfo is None for t in (reviewed_at, retrieved_at, completed_at))
                or not retrieved_at <= reviewed_at <= completed_at):
            return {}
        rows = [row for row in audit.get("records", []) if row.get("security_code") == code]
        final_rows = [row for row in audit.get("reviewed", []) if row.get("security_code") == code]
        if (len(rows) != 1 or len(final_rows) != 1 or rows[0].get("state") != "reviewed"
                or rows[0].get("company_name") != record["company_name"] or rows[0].get("draft_record") != record
                or rows[0].get("reviewed_record_sha256") != record_sha
                or rows[0].get("original_source_sha256", {}).get(reference) != proposal["parent_snapshot_sha256"]
                or final_rows[0].get("record_sha256") != record_sha
                or audit.get("final_record_sha256", {}).get(code) != record_sha):
            return {}
        return {(reference, index): {
            "kind": route["kind"], "purpose": "issuer_identity_discovery",
            "current_jpx_security_code": code, "current_jpx_company_name": record["company_name"],
            "official_seed_url": route["official_url"], "seed_company_name": discovery["seed_company_name"],
            "identity_status": record.get("identity_status"), "current_issuer_identity_verified": False,
            "current_issuer_name_observed_in_source": False, "IR_purpose_verified": False,
            "current_issuer_reception_verified": False, "manual_reviewer": review["reviewer"],
            "manual_reviewed_at": review["reviewed_at"], "quote": route["quote"],
            "ir_transition_quote": route["ir_transition_quote"], "source_snapshot": reference,
            "source_snapshot_sha256": proposal["parent_snapshot_sha256"], "source_url": page["url"],
            "source_requested_url": page["requested_url"], "source_retrieved_at": page["retrieved_at"],
            "source_link_index": index, "source_link": copy.deepcopy(link), "source_record_sha256": record_sha,
            "proposal_source": frozen["path"], "proposal_source_sha256": frozen["sha256"],
            "completed_audit_source": frozen["audit_path"], "completed_audit_source_sha256": frozen["audit_sha256"],
            "association_basis": "saved_completed_review_exact_operator_or_holding_link; issuer identity and reception require new review",
        }}
    except (KeyError, IndexError, TypeError, ValueError, OSError):
        return {}


def finite_reviewed_dependencies_match(output: Path, code: str, guards: dict) -> bool:
    """Check only this issuer's frozen evidence/attempts, never arbitrary paths."""
    if code not in FINITE_REVIEWED_AUTHORITIES or not isinstance(guards, dict) or not guards:
        return False
    for reference, expected in guards.items():
        if (not isinstance(reference, str) or not isinstance(expected, str)
                or not re.fullmatch(r"[a-f0-9]{64}", expected)):
            return False
        path = (output / reference).resolve()
        allowed = [output / kind / code for kind in ("evidence", "attempts")]
        if (not reference.startswith((f"evidence/{code}/", f"attempts/{code}/"))
                or path.suffix != ".json" or not path.is_relative_to(output.resolve())
                or not any(path.is_relative_to(p.resolve()) for p in allowed)
                or not path.is_file() or file_sha256(path) != expected):
            return False
    return True


def finite_reviewed_reference_set(record: dict, output: Path, guards: dict) -> bool:
    """Require the exact recursive source/attempt set, with visited deduplication."""
    references, visited = set(), set()

    def walk(value):
        if isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, dict):
            ref = value.get("snapshot")
            if ref is not None:
                if not isinstance(ref, str) or ref not in guards:
                    raise ValueError("unbound source reference")
                references.add(ref)
            for ref in value.get("previous_attempts", []):
                if not isinstance(ref, str) or ref not in guards or not ref.startswith("attempts/" + record["security_code"] + "/"):
                    raise ValueError("unbound archive reference")
                references.add(ref)
                if ref not in visited:
                    visited.add(ref)
                    archived = read_json(output / ref)
                    if archived.get("security_code") != record["security_code"]:
                        raise ValueError("archive belongs to another issuer")
                    walk(archived)
            for key, child in value.items():
                if key != "previous_attempts":
                    walk(child)

    try:
        walk(record)
        return references == set(guards)
    except (KeyError, TypeError, ValueError, OSError):
        return False



def finite_named_issuer_path(output: Path, reference: object, prefixes: tuple[str, ...]) -> Path | None:
    """6633 only: a logical path must also be the same physical dataset path."""
    try:
        if not isinstance(reference, str) or not reference.startswith(prefixes):
            return None
        path = (output / reference).resolve()
        if (path.suffix != ".json" or not path.is_file()
                or path.relative_to(output.resolve()).as_posix() != reference):
            return None
        return path
    except (ValueError, OSError, RuntimeError):
        return None


def finite_named_issuer_dependencies_match(output: Path, guards: dict, dependencies: dict) -> bool:
    """Do not follow issuer-directory aliases or authority aliases for 6633."""
    frozen = FINITE_REVIEWED_AUTHORITIES.get("6633", {})
    expected = {frozen.get("path"): frozen.get("sha256"),
                frozen.get("audit_path"): frozen.get("audit_sha256")}
    if not isinstance(guards, dict) or dependencies != expected:
        return False
    if set(guards) != set(frozen.get("source_references", [])):
        return False
    for reference, digest in {**guards, **dependencies}.items():
        prefixes = ("parts/",) if reference in dependencies else ("evidence/6633/", "attempts/6633/")
        path = finite_named_issuer_path(output, reference, prefixes)
        if not path or not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            return False
        if file_sha256(path) != digest:
            return False
        if reference in guards:
            try:
                if read_json(path).get("security_code") != "6633":
                    return False
            except (ValueError, AttributeError, OSError):
                return False
    return True


def finite_named_issuer_reference_set(record: dict, output: Path, guards: dict) -> bool:
    """6633's exact recursive snapshot/source_snapshot/archive graph."""
    references, visited = set(), set()

    def walk(value):
        if isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, dict):
            for key in ("snapshot", "source_snapshot"):
                ref = value.get(key)
                if ref is not None:
                    if not isinstance(ref, str) or ref not in guards or not ref.startswith("evidence/6633/"):
                        raise ValueError("unbound named-issuer source")
                    references.add(ref)
            archives = value.get("previous_attempts", [])
            if not isinstance(archives, list):
                raise ValueError("invalid named-issuer archive list")
            for ref in archives:
                if not isinstance(ref, str) or ref not in guards or not ref.startswith("attempts/6633/"):
                    raise ValueError("unbound named-issuer archive")
                references.add(ref)
                if ref not in visited:
                    visited.add(ref)
                    archived = read_json(output / ref)
                    if archived.get("security_code") != "6633":
                        raise ValueError("archive belongs to another issuer")
                    walk(archived)
            for key, child in value.items():
                if key != "previous_attempts":
                    walk(child)

    try:
        walk(record)
        return references == set(guards)
    except (KeyError, TypeError, ValueError, AttributeError, OSError):
        return False


def finite_named_current_issuer_binding(output: Path, record: dict, pages: dict[str, dict],
                                        proof_record_sha256: str | None = None) -> dict[tuple[str, int], dict]:
    """One root-reviewed named site href; no migration or IR intake inference."""
    code = "6633"
    frozen = FINITE_REVIEWED_AUTHORITIES.get(code)
    if not frozen or record.get("security_code") != code:
        return {}
    try:
        route = FINITE_REVIEWED_ROUTES[code][0]
        review = record["manual_review"]
        record_path = finite_named_issuer_path(output, "records/6633.json", ("records/",))
        authority_path = finite_named_issuer_path(output, frozen["path"], ("parts/",))
        audit_path = finite_named_issuer_path(output, frozen["audit_path"], ("parts/",))
        if not record_path or not authority_path or not audit_path:
            return {}
        record_sha = proof_record_sha256 or file_sha256(record_path)
        logical = hashlib.sha256(json.dumps(record, ensure_ascii=False, sort_keys=True,
                                          separators=(",", ":")).encode()).hexdigest()
        if (record_sha != frozen["record_sha256"] or logical != frozen["record_logical_sha256"]
                or file_sha256(authority_path) != frozen["sha256"]
                or file_sha256(audit_path) != frozen["audit_sha256"]
                or record.get("company_name") != frozen["company_name"]
                or record.get("official_url") != frozen["official_url"]
                or record.get("discovery", {}).get("security_code") != code
                or record["discovery"].get("seed_company_name") != frozen["seed_company_name"]
                or record["discovery"].get("official_url") != frozen["official_url"]
                or record.get("investigation_status") != "unconfirmed" or record.get("verification_level") != "none"
                or record.get("unconfirmed_reason") != "issuer_unverified"
                or record.get("individual_access") != "not_stated" or record.get("outreach_suitability") != "unconfirmed"
                or record.get("channels") != [] or record.get("public_ir_emails") != [] or record.get("contact_url") is not None
                or record.get("manual_review_required") is not False or review.get("reviewer") != frozen["reviewer"]
                or record.get("identity_status") != "name_or_security_code_observed"):
            return {}
        packet, audit = read_json(authority_path), read_json(audit_path)
        dependencies = {frozen["path"]: frozen["sha256"], frozen["audit_path"]: frozen["audit_sha256"]}
        guards = packet["recursive_source_and_archive_sha256"]
        bindings = packet["finite_discovery_proposals"]
        if (packet.get("approved_by") != "/root" or packet.get("reviewer") != frozen["binding_reviewer"]
                or packet.get("status") != "authorized_finite_identity_discovery" or packet.get("security_code") != code
                or packet.get("source_proposal_path") != frozen["original_proposal_path"]
                or packet.get("source_proposal_sha256") != frozen["original_proposal_sha256"]
                or packet.get("closed_audit_part") != frozen["audit_path"]
                or packet.get("closed_audit_part_sha256") != frozen["audit_sha256"]
                or packet.get("source_record_path") != "records/6633.json"
                or packet.get("source_record_sha256") != record_sha or packet.get("source_record_logical_sha256") != logical
                or type(packet.get("maximum_candidate_count")) is not int or packet["maximum_candidate_count"] != 1
                or packet.get("secondary_ir_route_candidate_present") is not False or len(bindings) != 1
                or packet.get("root_actual_primary_meaning_review_completed") is not True
                or packet.get("source_record_initial_identity_status_and_matches_are_immutable_history") is not True
                or not finite_named_issuer_dependencies_match(output, guards, dependencies)
                or not finite_named_issuer_reference_set(record, output, guards)):
            return {}
        selected = [r for r in audit["selected"] if r.get("security_code") == code]
        rows = [r for r in audit["reviewed"] if r.get("security_code") == code]
        if (audit.get("status") != "completed" or audit.get("pending_validation") != []
                or audit.get("pending_company_count") != 0 or audit.get("validator_error_count") != 0
                or audit.get("conflict_count") != 0 or audit.get("reviewed_company_count") != 10
                or len(audit["selected"]) != 10 or len(audit["reviewed"]) != 10 or len(selected) != 1 or len(rows) != 1):
            return {}
        original, row = selected[0], rows[0]
        row_sha = hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                          separators=(",", ":")).encode()).hexdigest()
        if (row != packet["source_audit_company_row_exact"] or row_sha != packet["source_audit_company_row_sha256"]
                or row.get("record_sha256_after_review") != record_sha or row.get("reviewed_at") != review["reviewed_at"]
                or original.get("record_sha256") != packet["original_record_sha256"]
                or {**original["original_source_snapshot_sha256"], **original["original_historical_source_snapshot_sha256"],
                    **original["original_attempt_archive_sha256"]} != guards
                or any(record.get(key) != value for key, value in original["immutable_record_fields"].items())
                or record["evidence"][:len(original["original_evidence"])] != original["original_evidence"]
                or record["conditions"][:len(original["original_conditions"])] != original["original_conditions"]
                or record["limitations"][:len(original["original_limitations"])] != original["original_limitations"]):
            return {}
        binding = bindings[0]
        reference, index = route["snapshot"], route["index"]
        page = pages.get(reference)
        if (not page or page.get("security_code") != code or page.get("url") != route["parent_url"]
                or page.get("requested_url") != route["parent_url"] or page.get("http_status") != 200
                or page.get("error") or page.get("http_get_attempted") is not True
                or page.get("text", "").count(route["quote"]) != 1
                or type(binding.get("source_link_index")) is not int or binding["source_link_index"] != index):
            return {}
        link = page["links"][index]
        flags = ("IR_channel_verified", "IR_purpose_verified", "current_issuer_reception_verified",
                 "current_issuer_identity_verified", "financial_ir_reception_verified", "actual_form_fields_verified",
                 "old_form_or_conditions_inherited", "legal_migration_or_split_or_date_inferred", "raw_url_normalized")
        expected = {
            "security_code": code, "company_name": frozen["company_name"], "seed_company_name": frozen["seed_company_name"],
            "official_seed_url": frozen["official_url"], "purpose": "issuer_identity_discovery",
            "kind": "reviewed_named_current_issuer_site_discovery", "method": "GET",
            "url": route["target_url"], "target_url": route["target_url"], "parent_url": route["parent_url"],
            "parent_requested_url": route["parent_url"], "source_url": route["parent_url"],
            "parent_snapshot": reference, "source_snapshot": reference, "parent_snapshot_sha256": guards[reference],
            "source_sha256": guards[reference], "retrieved_at": page["retrieved_at"], "parent_retrieved_at": page["retrieved_at"],
            "source_link": link, "source_link_url": route["target_url"], "raw_href": route["target_url"],
            "quote": route["quote"], "quote_field_path": "text", "field_path": "links.41",
            "raw_href_field_path": "links.41.href", "resolved_url_field_path": "links.41.url",
            "source_record_path": "records/6633.json", "source_record_sha256": record_sha,
            "source_record_candidate_path": "manual_followup_candidates.0", "source_record_evidence_path": "evidence.1",
            "reviewer": frozen["reviewer"], "reviewed_at": review["reviewed_at"],
            "source_audit_part": frozen["audit_path"], "source_audit_part_sha256": frozen["audit_sha256"],
            "parent_http_status": 200, "parent_error": None, "parent_http_get_attempted": True,
        }
        if (any(binding.get(key) != value for key, value in expected.items())
                or any(binding.get(key) is not False for key in flags)
                or link != {"url": route["target_url"], "href": route["target_url"], "label": route["label"]}
                or safe_url(link["url"]) != link["url"]):
            return {}
        evidence, candidate = record["evidence"][1], record["manual_followup_candidates"][0]
        if (evidence.get("snapshot") != reference or evidence.get("url") != page["url"]
                or evidence.get("retrieved_at") != page["retrieved_at"] or evidence.get("quote") != route["quote"]
                or evidence.get("role") != route["evidence_role"] or type(evidence.get("source_link_index")) is not int
                or evidence["source_link_index"] != index or evidence.get("source_link_url") != link["url"]
                or candidate.get("purpose") != "issuer_identity_discovery" or candidate.get("method") != "GET"
                or type(candidate.get("source_link_index")) is not int or candidate["source_link_index"] != index
                or candidate.get("source_snapshot") != reference or candidate.get("parent_snapshot") != reference
                or candidate.get("source_link") != link or candidate.get("url") != link["url"]
                or any(candidate.get(key) is not False for key in flags[:3])):
            return {}
        retrieved, reviewed, closed, authorized = map(datetime.fromisoformat, (
            page["retrieved_at"], review["reviewed_at"], audit["completed_at"], packet["authority_recorded_at_utc"]))
        times = {key: page[key] for key in ("http_get_started_at", "http_response_received_at", "http_get_completed_at")}
        started, received, finished = map(datetime.fromisoformat, times.values())
        if (any(t.tzinfo is None for t in (retrieved, reviewed, closed, authorized, started, received, finished))
                or not retrieved <= reviewed <= closed <= authorized or not started <= received <= finished <= reviewed
                or binding.get("parent_actual_http_times") != times):
            return {}
        return {(reference, index): {
            "kind": "reviewed_named_current_issuer_site_discovery", "purpose": "issuer_identity_discovery",
            "current_jpx_security_code": code, "current_jpx_company_name": frozen["company_name"],
            "official_seed_url": frozen["official_url"], "current_issuer_identity_verified": False,
            "IR_channel_verified": False, "IR_purpose_verified": False, "current_issuer_reception_verified": False,
            "actual_form_fields_verified": False, "manual_reviewer": frozen["binding_reviewer"],
            "manual_reviewed_at": packet["authority_recorded_at_utc"], "quote": route["quote"],
            "source_snapshot": reference, "source_snapshot_sha256": guards[reference],
            "source_url": page["url"], "source_retrieved_at": page["retrieved_at"],
            "source_link_index": index, "source_link": copy.deepcopy(link), "source_record_sha256": record_sha,
            "proposal_source": frozen["path"], "proposal_source_sha256": frozen["sha256"],
            "finite_saved_source_guards": guards, "finite_authority_guards": dependencies,
            "association_basis": "reviewed_named_current_JPX_root_anchor; issuer identity and IR reception require separate review",
        }}
    except (KeyError, IndexError, TypeError, ValueError, AttributeError, OSError, RuntimeError):
        return {}


def finite_reviewed_bindings(output: Path, record: dict, pages: dict[str, dict],
                             proof_record_sha256: str | None = None) -> dict[tuple[str, int], dict]:
    """One financial-IR anchor and two holding discoveries, all source bound."""
    code = record["security_code"]
    if code == "6633":
        return finite_named_current_issuer_binding(output, record, pages, proof_record_sha256)
    frozen, review = FINITE_REVIEWED_AUTHORITIES.get(code), record.get("manual_review", {})
    if (not frozen or not frozen["sha256"] or record.get("company_name") != frozen["company_name"]
            or record.get("official_url") != frozen["official_url"]
            or record.get("manual_review_required") is not False or not isinstance(review, dict)
            or review.get("reviewer") != frozen["reviewer"]
            or record.get("individual_access") != "not_stated" or record.get("outreach_suitability") != "unconfirmed"
            or record.get("discovery", {}).get("security_code") != code
            or record.get("discovery", {}).get("seed_company_name") != frozen["company_name"]
            or record.get("discovery", {}).get("official_url") != frozen["official_url"]):
        return {}
    try:
        record_sha = proof_record_sha256 or file_sha256(output / "records" / (code + ".json"))
        authority_path = (output / frozen["path"]).resolve()
        if (record_sha != frozen["record_sha256"] or not authority_path.is_relative_to(output.resolve())
                or not authority_path.is_file()
                or file_sha256(authority_path) != frozen["sha256"]):
            return {}
        packet = read_json(authority_path)
        dependencies = {frozen["path"]: frozen["sha256"]}
        if code == "6383":
            anchor = packet["actual_indexed_official_financial_IR_anchor"]
            identity = packet["current_JPX_issuer_and_financial_IR_identity"]
            guards = {**packet["verification"]["source_snapshot_sha256"], **packet["verification"]["previous_attempt_sha256"]}
            bindings = [anchor]
            authorized_at = packet["authority_recorded_at_utc"]
            if (packet.get("approved_by") != "/root" or packet.get("binding_reviewed_by") != frozen["binding_reviewer"]
                    or packet["record_transition"].get("new_record_sha256") != record_sha
                    or packet["verification"].get("pending") != [] or packet["verification"].get("update_races") != []
                    or packet["verification"].get("validation_errors") != 0
                    or record.get("investigation_status") != "provisional"
                    or record.get("verification_level") != "official_form_link_only"
                    or record.get("contact_url") != FINITE_REVIEWED_ROUTES[code][0]["target_url"]
                    or identity.get("JPX_issuer", {}).get("security_code") != code
                    or identity.get("JPX_issuer", {}).get("company_name") != frozen["company_name"]
                    or identity.get("IR_NAV_footer_used_as_contact_purpose") is not False
                    or anchor.get("attribute_kind") != "anchor href"
                    or anchor.get("source_anchor_attribute_is_form_POST_action") is not False
                    or anchor.get("source_captured_link_is_embedded_iframe_src") is not False):
                return {}
            if not finite_reviewed_dependencies_match(output, code, guards):
                return {}
            if frozen["historical_stop_snapshot"] not in guards:
                return {}
            old_stop = read_json(output / frozen["historical_stop_snapshot"])
            if (old_stop.get("error") != "robots_disallowed"
                    or old_stop.get("http_get_attempted") is not False
                    or old_stop.get("requested_url") != FINITE_REVIEWED_ROUTES[code][0]["target_url"]):
                return {}
            for name in ("homepage_proof", "issuer_IR_page_proof"):
                proof = identity[name]
                if proof.get("snapshot") not in guards:
                    return {}
                page = read_json(output / proof["snapshot"])
                if (guards.get(proof["snapshot"]) != proof["snapshot_sha256"]
                        or page.get("security_code") != code or page.get("http_status") != 200 or page.get("error")
                        or page.get("url") != proof["url"] or page.get("retrieved_at") != proof["retrieved_at"]
                        or (name == "homepage_proof" and proof["quote"] not in page.get("text", ""))
                        or (name == "issuer_IR_page_proof" and
                            (proof["title_quote"] != "IR情報 | ダイフク" or proof["title_quote"] != page.get("title")
                             or proof["financial_IR_quote"] != "最新のIR資料 決算関連資料 一括ダウンロード（ZIP） 統合報告書 ダイフクレポート2026"
                             or proof["financial_IR_quote"] not in page.get("text", "")))):
                    return {}
        else:
            if not frozen["audit_sha256"]:
                return {}
            guards = packet["recursive_source_and_archive_sha256"]
            bindings = packet["finite_discovery_proposals"]
            authorized_at = packet["authorized_at_utc"]
            audit_path = (output / frozen["audit_path"]).resolve()
            if (not audit_path.is_relative_to(output.resolve()) or not audit_path.is_file()
                    or file_sha256(audit_path) != frozen["audit_sha256"]
                    or packet.get("approved_by") != "/root" or packet.get("security_code") != code
                    or packet.get("completed_audit_part") != frozen["audit_path"]
                    or packet.get("completed_audit_sha256") != frozen["audit_sha256"]
                    or packet.get("source_record_sha256") != record_sha
                    or any(packet.get(key) is not False for key in (
                        "current_issuer_identity_verified", "financial_ir_reception_verified", "actual_form_fields_verified"))
                    or packet.get("original_proposal_sha256") != frozen["original_proposal_sha256"]
                    or hashlib.sha256((json.dumps(packet["original_proposal_exact"], ensure_ascii=False, indent=2) + "\n").encode()).hexdigest() != frozen["original_proposal_sha256"]
                    or packet["original_proposal_exact"].get("secondary_binding_decision_deferred") is not True
                    or len(bindings) != 2
                    or record.get("investigation_status") != "unconfirmed" or record.get("verification_level") != "none"
                    or record.get("identity_status") != "issuer_unverified" or record.get("identity_matches") != []
                    or record.get("channels") != [] or record.get("public_ir_emails") != [] or record.get("contact_url") is not None):
                return {}
            original_routes = [packet["original_proposal_exact"][key] for key in ("primary_discovery", "secondary_ir_route_candidate")]
            if bindings != [{**original, "purpose": "issuer_identity_discovery"} for original in original_routes]:
                return {}
            audit = read_json(audit_path)
            rows = [r for r in audit.get("reviewed", []) if r.get("security_code") == code]
            if (audit.get("status") != "completed_finite_batch" or audit.get("validation_pending_security_codes") != []
                    or audit.get("error_count") != 0 or audit.get("race_count") != 0 or audit.get("pending_count") != 0
                    or audit.get("saved_count") != audit.get("selected_company_count")
                    or len(rows) != 1 or rows[0].get("saved") is not True
                    or rows[0].get("record_sha256_after_review") != record_sha
                    or rows[0].get("reviewed_at") != review["reviewed_at"]
                    or {**rows[0].get("original_evidence_sha256", {}), **rows[0].get("original_attempt_sha256", {})} != guards):
                return {}
            closed_at = datetime.fromisoformat(audit["closed_at_utc"])
            if (closed_at.tzinfo is None or not datetime.fromisoformat(review["reviewed_at"]) <= closed_at <= datetime.fromisoformat(authorized_at)):
                return {}
            dependencies[frozen["audit_path"]] = frozen["audit_sha256"]
        if (not finite_reviewed_dependencies_match(output, code, guards)
                or not finite_reviewed_reference_set(record, output, guards)):
            return {}
        reviewed_at, authority_time = datetime.fromisoformat(review["reviewed_at"]), datetime.fromisoformat(authorized_at)
        if any(t.tzinfo is None for t in (reviewed_at, authority_time)) or reviewed_at > authority_time:
            return {}
        result = {}
        for route, binding in zip(FINITE_REVIEWED_ROUTES[code], bindings):
            reference, index = route["snapshot"], route["index"]
            page = pages.get(reference)
            bound_index = binding.get("source_link_index")
            if (not page or type(bound_index) is not int or bound_index != index
                    or page.get("security_code") != code or page.get("url") != route["parent_url"]
                    or page.get("requested_url") != route.get("parent_requested_url", route["parent_url"])
                    or page.get("http_status") != 200 or page.get("error")
                    or page.get("http_get_attempted") is not True or page.get("text", "").count(route["quote"]) != 1
                    or binding.get("snapshot", binding.get("source_snapshot")) != reference):
                return {}
            retrieved_at = datetime.fromisoformat(page["retrieved_at"])
            link = page["links"][index]
            if (retrieved_at.tzinfo is None or retrieved_at > reviewed_at
                    or link.get("url") != route["target_url"] or link.get("href") != route["target_url"]
                    or link.get("label") != route["label"] or safe_url(link["url"]) != link["url"]
                    or not any(type(e.get("source_link_index")) is int and e["source_link_index"] == index
                        and e.get("snapshot") == reference and e.get("role") == route["evidence_role"]
                        and e.get("url") == page["url"] and e.get("retrieved_at") == page["retrieved_at"]
                        and e.get("quote") == route["quote"] and e.get("source_link_url") == link["url"]
                        for e in record.get("evidence", []) if isinstance(e, dict))):
                return {}
            if code == "6383":
                if (binding.get("actual_source_link") != link or binding.get("snapshot_sha256") != guards[reference]
                        or binding.get("exact_primary_receipt_quote") != route["quote"]
                        or binding.get("retrieved_at") != page["retrieved_at"] or page.get("forms") != []):
                    return {}
            elif (binding.get("source_link") != link or binding.get("source_sha256") != guards[reference]
                    or binding.get("purpose") != "issuer_identity_discovery" or binding.get("method") != "GET"
                    or binding.get("security_code") != code or binding.get("company_name") != frozen["company_name"]
                    or binding.get("seed_company_name") != frozen["company_name"] or binding.get("official_seed_url") != frozen["official_url"]
                    or binding.get("url") != route["target_url"] or binding.get("target_url") != route["target_url"]
                    or binding.get("quote") != route["quote"] or binding.get("raw_href") != link["href"]
                    or binding.get("retrieved_at") != page["retrieved_at"]
                    or binding.get("source_record_sha256") != record_sha or binding.get("reviewer") != frozen["reviewer"]
                    or binding.get("reviewed_at") != review["reviewed_at"]
                    or any(binding.get(key) is not False for key in (
                        "current_issuer_identity_verified", "financial_ir_reception_verified", "actual_form_fields_verified", "old_form_or_conditions_inherited"))):
                return {}
            result[(reference, index)] = {
                "kind": "reviewed_mixed_financial_ir_anchor" if code == "6383" else "reviewed_holding_issuer_migration_discovery",
                "purpose": frozen["purpose"], "current_jpx_security_code": code,
                "current_jpx_company_name": record["company_name"], "official_seed_url": frozen["official_url"],
                "current_issuer_identity_verified": False, "IR_purpose_verified": code == "6383",
                "current_issuer_reception_verified": False, "actual_form_fields_verified": False,
                "manual_reviewer": frozen["binding_reviewer"], "manual_reviewed_at": authorized_at,
                "quote": route["quote"], "source_snapshot": reference, "source_snapshot_sha256": guards[reference],
                "source_url": page["url"], "source_retrieved_at": page["retrieved_at"],
                "source_link_index": index, "source_link": copy.deepcopy(link), "source_record_sha256": record_sha,
                "proposal_source": frozen["path"], "proposal_source_sha256": frozen["sha256"],
                "finite_saved_source_guards": guards, "finite_authority_guards": dependencies,
                "association_basis": "frozen_reviewed_actual_anchor; new issuer identity/reception/fields require review",
            }
        return result
    except (KeyError, IndexError, TypeError, ValueError, OSError):
        return {}


def finite_own_archive_matches(output: Path, proof: dict, lineage: dict) -> bool:
    """Recheck this run's original archive immediately before a finite GET."""
    if "finite_saved_source_guards" not in proof:
        return True  # Older identity/generic routes keep their existing contract.
    try:
        code, original_sha = proof["current_jpx_security_code"], proof["source_record_sha256"]
        if code not in FINITE_REVIEWED_AUTHORITIES or lineage.get("source_record_sha256") != original_sha:
            return False
        if code == "6633" and not finite_named_issuer_path(output, "records/6633.json", ("records/",)):
            return False
        archive = lineage.get("original_record_archive")
        if archive is None:
            return lineage.get("expected_record_sha256") == original_sha
        if not isinstance(archive, str) or not archive.startswith("attempts/" + code + "/"):
            return False
        path = (output / archive).resolve()
        if code == "6633" and finite_named_issuer_path(output, archive, ("attempts/6633/",)) != path:
            return False
        return (path.suffix == ".json" and path.is_relative_to(output.resolve())
                and path.is_relative_to((output / "attempts" / code).resolve())
                and path.is_file() and file_sha256(path) == original_sha)
    except (KeyError, TypeError, AttributeError, OSError):
        return False


def completed_identity_audit_matches(output: Path, proof: dict) -> bool:
    """Recheck the additional immutable audit after preflight, before dispatch."""
    if "finite_saved_source_guards" in proof:
        code = proof.get("current_jpx_security_code")
        frozen = FINITE_REVIEWED_AUTHORITIES.get(code, {})
        dependencies = {frozen.get("path"): frozen.get("sha256")}
        if frozen.get("audit_path"):
            dependencies[frozen["audit_path"]] = frozen["audit_sha256"]
        try:
            if code == "6633" and not finite_named_issuer_dependencies_match(output, proof["finite_saved_source_guards"], dependencies):
                return False
            return (proof.get("finite_authority_guards") == dependencies
                    and finite_reviewed_dependencies_match(output, code, proof["finite_saved_source_guards"])
                    and all((output / ref).resolve().is_relative_to(output.resolve())
                            and (output / ref).is_file() and file_sha256(output / ref) == sha
                            for ref, sha in dependencies.items()))
        except (TypeError, ValueError, OSError):
            return False
    if "completed_audit_source" not in proof:
        return True  # The older finite routes have their existing source guards.
    frozen = COMPLETED_IDENTITY_PROPOSAL
    try:
        return (proof.get("completed_audit_source") == frozen["audit_path"]
                and proof.get("completed_audit_source_sha256") == frozen["audit_sha256"]
                and file_sha256(output / frozen["audit_path"]) == frozen["audit_sha256"])
    except OSError:
        return False


def company_candidates(output: Path, record: dict, proposals: list[dict], max_links: int = 3,
                       proof_record_sha256: str | None = None) -> tuple[list[dict], Counter]:
    rejected = Counter()
    if record.get("investigation_status") not in {"unconfirmed", "provisional"}:
        return [], rejected
    official = safe_url(record.get("official_url"))
    if not official:
        return [], Counter({"missing_safe_official_url": 1})
    if record["security_code"] == "6633":
        # Reject changed authority/bounds before reading unrelated saved pages.
        try:
            named = FINITE_REVIEWED_ROUTES["6633"][0]["snapshot"]
            named_path = finite_named_issuer_path(output, named, ("evidence/6633/",))
            if not named_path or not finite_named_current_issuer_binding(
                    output, record, {named: read_json(named_path)}, proof_record_sha256):
                return [], Counter({"finite_named_issuer_authority_unbound": 1})
        except (KeyError, TypeError, ValueError, OSError, RuntimeError):
            return [], Counter({"finite_named_issuer_authority_unbound": 1})
    pages = saved_pages(output, record, proposals)
    seen, denied, disallowed, robots = set(), set(), {}, {}
    robot_observations = latest_robots(pages)
    unreachable = set()
    for origin, robot in robot_observations.items():
        status = robot.get("http_status")
        if robot.get("error") or not isinstance(status, int) or status >= 500 or 300 <= status < 400:
            unreachable.add(origin)
        elif status == 200:
            parser = RobotFileParser()
            parser.parse(robot.get("text", "").splitlines())
            robots[origin] = parser
    for fetch in record.get("fetches", []):
        if fetch.get("error") not in NO_CONTENT_GET and fetch.get("failure_signature") != "common_transport_503":
            for field in ("url", "final_url"):
                if safe_url(fetch.get(field)):
                    seen.add(url_key(fetch[field]))
    for reference, page in pages:
        for response in responses(page):
            url = response.get("url") or response.get("requested_url")
            if not safe_url(url):
                continue
            if response.get("http_status") in (401, 403, 429):
                denied.add(host_key(url))
            if response.get("error") == "robots_disallowed":
                disallowed.setdefault(url_key(url), []).append((reference, response))
            if (response.get("error") not in NO_CONTENT_GET and response.get("failure_signature") != "common_transport_503"
                    and not research.TRANSPORT_FAILURE.search(response.get("text", ""))
                    and response.get("http_get_attempted") is not False
                    and (response.get("http_status") is not None or response.get("error"))):
                for field in ("requested_url", "url"):
                    if safe_url(response.get(field)):
                        seen.add(url_key(response[field]))
    successful = {reference: page for reference, page in pages
                  if page.get("http_status") == 200 and not page.get("error") and safe_url(page.get("url"))
                  and not research.TRANSPORT_FAILURE.search(page.get("text", ""))}
    trusted = {reference for reference, page in successful.items()
               if host_key(page["url"]) == host_key(official) and has_identity(record, page)}
    # An observed issuer name/code plus its saved official redirect can establish
    # the new company host. A proposed arbitrary external host cannot do so.
    for reference, page in successful.items():
        if (safe_url(page.get("requested_url")) and host_key(page["requested_url"]) == host_key(official)
                and observed_identity(record, page)
                and any(r.get("http_status") in (301, 302, 303, 307, 308)
                        and safe_url(r.get("requested_url") or r.get("url"))
                        and host_key(r.get("requested_url") or r.get("url")) == host_key(official)
                        for r in page.get("redirects", []))):
            trusted.add(reference)
    bindings = quoted_link_bindings(record, proposals, successful)
    reviewed_ir_bindings = reviewed_ir_route_bindings(output, record, proposals, successful, proof_record_sha256)
    finite_bindings = finite_reviewed_bindings(output, record, successful, proof_record_sha256)
    reviewed_ir_bindings.update({key: proof for key, proof in finite_bindings.items() if proof["purpose"] == "ir_contact_followup"})
    identity_bindings = identity_discovery_bindings(output, record, proposals, successful, proof_record_sha256)
    identity_bindings.update(identity_reference_bindings(output, record, proposals, successful, proof_record_sha256))
    identity_bindings.update(ir_portal_reference_binding(output, record, proposals, successful, proof_record_sha256))
    identity_bindings.update(completed_identity_bindings(output, record, successful, proof_record_sha256))
    identity_bindings.update({key: proof for key, proof in finite_bindings.items() if proof["purpose"] == "issuer_identity_discovery"})
    completed_route = COMPLETED_IDENTITY_ROUTES.get(record["security_code"])
    if completed_route and host_key(official) == host_key(completed_route["official_url"]):
        # Their legacy/service pages authorize just the two frozen discoveries.
        # A missing/changed proof cannot fall through to generic IR-looking links.
        trusted.clear()
    finite_route = FINITE_REVIEWED_AUTHORITIES.get(record["security_code"])
    frozen_references = {route["snapshot"] for route in FINITE_REVIEWED_ROUTES.get(record["security_code"], [])}
    finite_only = record["security_code"] == "6633" or bool(finite_route and (
        host_key(official) == host_key(finite_route["official_url"])
        or (output / finite_route["path"]).is_file()
        or any(item.get("snapshot") in frozen_references for field in ("fetches", "evidence")
               for item in record.get(field, []) if isinstance(item, dict))))
    if finite_only:
        # Failed/missing authority never falls back to generic IR-looking links.
        trusted.clear()
    ir_scope: dict[str, list[dict]] = {}
    # Preserve the exact IR ancestor when its target is a generic contact page.
    changed = True
    while changed:
        changed = False
        linked, intake = {}, {}
        for reference in sorted(trusted):
            page = successful[reference]
            for index, link in enumerate(page.get("links", [])):
                binding = bindings.get((reference, index)) or reviewed_ir_bindings.get((reference, index))
                priority = 1 if binding else link_priority(page, link, reference in ir_scope)
                if priority is None or not safe_url(link.get("url")) or OTHER_PATH.search(urlsplit(link["url"]).path):
                    continue
                header_scope = bool(research.IR_CONTACT.search(" ".join([page.get("title", ""), *page.get("headings", [])[:1]])))
                if priority == 2 and host_key(link["url"]) != host_key(page["url"]) and not (header_scope or reference in ir_scope):
                    continue
                key = url_key(link["url"])
                linked[key] = reference
                if priority <= 1 or link.get("label") == "embedded frame" and (header_scope or reference in ir_scope):
                    edge = {"parent_snapshot": reference, "parent_url": page["url"],
                            "source_link_index": index, "discovery_link_label": link.get("label", ""),
                            "target_url": link["url"]}
                    if binding:
                        edge["binding_evidence"] = binding
                    intake[key] = [*ir_scope.get(reference, []), edge]
        for reference, page in successful.items():
            keys = [url_key(page[field]) for field in ("requested_url", "url") if safe_url(page.get(field))]
            if reference not in trusted and any(key in linked for key in keys):
                trusted.add(reference)
                changed = True
            if reference not in ir_scope:
                for key in keys:
                    if key in intake:
                        ir_scope[reference] = intake[key]
                        changed = True
                        break
    candidates = {}
    for reference in sorted(trusted | {reference for reference, _ in identity_bindings}
                            | {reference for reference, _ in finite_bindings}):
        page = successful[reference]
        post_actions = {url_key(research.urljoin(page["url"], form["action"])) for form in page.get("forms", [])
                        if form.get("action") and str(form.get("method", "get")).lower() == "post"}
        for index, link in enumerate(page.get("links", [])):
            binding = bindings.get((reference, index)) or reviewed_ir_bindings.get((reference, index))
            reviewed_ir_binding = reviewed_ir_bindings.get((reference, index))
            identity_binding = identity_bindings.get((reference, index))
            if finite_only and (reference, index) not in finite_bindings:
                continue
            if reference not in trusted and not identity_binding and (reference, index) not in finite_bindings:
                continue  # The unverified legacy site permits only its bound notice.
            priority = 4 if identity_binding else 1 if binding else link_priority(page, link, reference in ir_scope)
            matching = [p for p in proposals if matching_proposal(p, reference, page, link)]
            # Explicitly proposed IR landing/FAQ/policy pages are discovery
            # work, with no inference that a contact is already demonstrated.
            if priority is None and matching and safe_url(link.get("url")) and IR_DISCOVERY_ROUTE.search(urlsplit(link["url"]).path):
                if research.IR.search(link.get("label", "")) or ir_parent(page):
                    priority = 3
            if priority is None:
                continue
            url = safe_url(link.get("url"))
            if not url or priority != 3 and OTHER_PATH.search(urlsplit(url).path):
                continue
            if (priority == 2 and host_key(url) != host_key(page["url"]) and
                    reference not in ir_scope and not research.IR_CONTACT.search(" ".join([page.get("title", ""), *page.get("headings", [])[:1]]))):
                rejected["external_generic_contact_without_ir_association"] += 1
                continue
            key = url_key(url)
            if key in seen:
                rejected["already_fetched"] += 1
                continue
            if key in post_actions:
                rejected["post_action"] += 1
                continue
            origin = origin_key(url)
            if origin in unreachable:
                rejected["saved_robots_unreachable_current_route_unconfirmed"] += 1
                continue
            correction = saved_robots_literal_correction(output, url, disallowed.get(key, []),
                                                        robot_observations.get(origin), pages) if key in disallowed else None
            if finite_only and record["security_code"] == "6383" and not correction:
                rejected["finite_route_requires_saved_literal_allow_correction"] += 1
                continue
            if (host_key(url) in denied or key in disallowed and not correction
                    or origin in robots and not research.robots_can_fetch(robots[origin], research.USER_AGENT, url)):
                rejected["saved_access_denial"] += 1
                continue
            candidate = {"security_code": record["security_code"], "company_name": record.get("company_name"), "url": url,
                         "parent_url": page["url"], "parent_snapshot": reference,
                         "parent_snapshot_sha256": hashlib.sha256(evidence_path(output, reference).read_bytes()).hexdigest(),
                         "parent_retrieved_at": page.get("retrieved_at"), "discovery_link_label": link.get("label", ""),
                         "source_link_index": index, "priority": priority,
                         "explicit_ir_link": priority <= 1,
                         "purpose": "issuer_identity_discovery" if identity_binding else "ir_contact_followup",
                         "association_basis": identity_binding.get("association_basis", "saved_reviewed_formal_site_transition; current issuer identity and reception require new review") if identity_binding else "official_ir_discovery_link_not_verified_contact" if priority == 3 else "exact_link_in_saved_official_parent; requires human contact review",
                         "official_url": official}
            if correction:
                candidate["robots_literal_allow_correction"] = correction
            if identity_binding:
                candidate["identity_discovery_proof"] = identity_binding
            if reviewed_ir_binding:
                candidate["reviewed_ir_route_proof"] = reviewed_ir_binding
                candidate["association_basis"] = "saved_reviewed_explicit_financial_ir_section; input fields and reception require human review"
            if reference in ir_scope:
                candidate["ir_scope_evidence"] = ir_scope[reference]
            if binding:
                candidate["binding_evidence"] = binding
            if matching:
                candidate["manual_proposal_source"] = matching[0]["proposal_source"]
            if key not in candidates or priority < candidates[key]["priority"]:
                candidates[key] = candidate
    chosen = sorted(candidates.values(), key=lambda item: (item["priority"], item["url"]))
    rejected["per_company_limit"] += max(0, len(chosen) - max_links)
    return chosen[:max_links], rejected


def build_plan(output: Path, max_links: int = 3, only_codes: list[str] | None = None) -> dict:
    proposals = proposal_rows(output)
    tasks, rejected = [], Counter()
    for path in sorted((output / "records").glob("*.json")):
        if not CODE.fullmatch(path.stem) or (only_codes and path.stem not in only_codes):
            continue
        record = read_json(path)
        if record.get("security_code") != path.stem:
            raise ValueError("record filename/code mismatch: " + str(path))
        selected, exclusions = company_candidates(output, record, proposals.get(path.stem, []), max_links)
        tasks.extend(selected)
        rejected.update(exclusions)
    return {"format": "ir_followup_plan", "output": str(output), "plan_only": True,
            "http_get_attempt_count": 0, "writes": 0, "selected_company_count": len({t["security_code"] for t in tasks}),
            "selected_url_count": len(tasks), "max_links_per_company": max_links,
            "rejected_counts": dict(rejected), "selected": tasks}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_parser_refresh_plan(output: Path) -> dict:
    """The sole already-fetched exception: two previously observed 200 URLs."""
    audit_path = output / PARSER_REFRESH_AUDIT
    audit = read_json(audit_path)
    audit_sha = file_sha256(audit_path)
    rows = audit.get("refreshes", [])
    if len(rows) != 2 or {row.get("security_code") for row in rows} != set(PARSER_REFRESH_TARGETS):
        raise ValueError("parser refresh must contain exactly 2752 and 2784")
    hashes = audit.get("source_snapshots_to_preserve", {})
    for reference, expected in hashes.items():
        path = evidence_path(output, reference)
        if not path or not path.is_file() or file_sha256(path) != expected:
            raise ValueError("parser refresh immutable source mismatch: " + str(reference))
    state_path = output / PARSER_REFRESH_STATE
    state = read_json(state_path) if state_path.is_file() else {}
    if state and (state.get("mode") != PARSER_REFRESH_MODE or state.get("audit_sha256") != audit_sha):
        raise ValueError("parser refresh state/audit mismatch")
    claims = state.get("refresh_claims", {})
    tasks = []
    for row in sorted(rows, key=lambda item: item["security_code"]):
        code = row["security_code"]
        record_path = output / "records" / (code + ".json")
        record = read_json(record_path)
        target = safe_url(row.get("target_url"))
        parent_ref, target_ref = row.get("parent_snapshot"), row.get("target_snapshot")
        parent_path, target_path = evidence_path(output, parent_ref), evidence_path(output, target_ref)
        if (target != PARSER_REFRESH_TARGETS[code] or not parent_path or not target_path
                or parent_ref not in hashes or target_ref not in hashes or record.get("security_code") != code):
            raise ValueError("parser refresh target/source mismatch: " + code)
        parent, old_target = read_json(parent_path), read_json(target_path)
        original_link = row.get("parent_link", {})
        link_url = safe_url(original_link.get("url"))
        official = safe_url(record.get("official_url"))
        if (not official or safe_url(parent.get("url")) != safe_url(row.get("parent_url"))
                or host_key(parent["url"]) != host_key(official)
                or not has_identity(record, parent) or original_link not in parent.get("links", [])
                or not link_url or parent.get("http_status") != 200 or parent.get("error")
                or old_target.get("http_status") != 200 or old_target.get("error")
                or safe_url(old_target.get("url")) != target
                or safe_url(old_target.get("requested_url")) != link_url):
            raise ValueError("parser refresh needs observed official parent/link/200 target: " + code)
        current = link_url
        for redirect in old_target.get("redirects", []):
            if (redirect.get("http_status") not in (301, 302, 303, 307, 308)
                    or safe_url(redirect.get("requested_url") or redirect.get("url")) != current
                    or not safe_url(redirect.get("redirect_target"))):
                raise ValueError("parser refresh redirect chain mismatch: " + code)
            current = safe_url(redirect["redirect_target"])
        if current != target or (host_key(target) != host_key(official) and code == "2752"
                                 and not observed_identity(record, old_target)):
            raise ValueError("parser refresh canonical identity mismatch: " + code)
        for item in row.get("identity_and_ir_scope_evidence", []):
            reference = item.get("snapshot")
            path = evidence_path(output, reference)
            if not path or reference not in hashes:
                raise ValueError("parser refresh scope evidence not preserved: " + code)
            page = read_json(path)
            field = "title" if item.get("quote_source") == "title" else "text"
            if not item.get("quote") or item["quote"] not in page.get(field, ""):
                raise ValueError("parser refresh scope quote mismatch: " + code)
        expected_record = audit.get("original_record_hashes_at_preparation", {}).get(code)
        key = code + " " + url_key(target)
        if key not in claims and file_sha256(record_path) != expected_record:
            raise ValueError("parser refresh original record changed: " + code)
        proof = {"audit_snapshot": PARSER_REFRESH_AUDIT, "audit_sha256": audit_sha,
                 "source_record_sha256": expected_record, "previous_target_snapshot": target_ref,
                 "previous_target_snapshot_sha256": hashes[target_ref],
                 "parent_snapshot_sha256": hashes[parent_ref],
                 "parser_script_sha256": file_sha256(Path(research.__file__))}
        tasks.append({"security_code": code, "company_name": record.get("company_name"), "url": target,
            "parent_url": parent["url"], "parent_snapshot": parent_ref,
            "parent_snapshot_sha256": hashes[parent_ref], "parent_retrieved_at": parent.get("retrieved_at"),
            "discovery_link_label": original_link.get("label", ""), "official_url": official,
            "explicit_ir_link": False, "priority": 0, "one_attempt_parser_refresh": True,
            "association_basis": "known_successful_exact_url_parser_refresh; requires new human contact review",
            "parser_refresh_proof": proof})
    return {"format": "ir_followup_plan", "mode": PARSER_REFRESH_MODE, "audit_sha256": audit_sha,
            "output": str(output), "plan_only": True, "http_get_attempt_count": 0, "writes": 0,
            "selected_company_count": 2, "selected_url_count": 2, "max_links_per_company": 1,
            "global_rps": 0.25, "max_gets": PARSER_REFRESH_MAX_GETS,
            "state": str(state_path), "claimed_once_count": len(claims), "selected": tasks}


class BoundedFetcher(research.Fetcher):
    """Keep the existing transport/robots behavior, with a hard GET dispatch cap."""
    def __init__(self, max_gets: int, global_rps: float, raw_directory=None):
        super().__init__(global_rps=global_rps, raw_directory=raw_directory)
        self.max_gets = max_gets
        self.limit_reached = False
        self.allowed_hosts = {host_key(PREFLIGHT)}
        self.before_dispatch = None

    def _dispatch_get(self, url, origin, result):
        if not safe_url(url):
            result["error"] = "unsafe_followup_url"
            return None
        if host_key(url) not in self.allowed_hosts:
            result["error"] = "unlinked_redirect_host"
            return None
        if self.http_get_attempt_count >= self.max_gets:
            self.limit_reached = True
            result["error"] = "followup_get_limit_reached"
            return None
        if self.before_dispatch and not self.before_dispatch(url, result):
            return None
        return super()._dispatch_get(url, origin, result)

    def _observe_response(self, result, origin):
        super()._observe_response(result, origin)
        if result.get("failure_signature") == "common_transport_503":
            # One shared-path failure suffices here; do not probe more companies.
            self.environment_failed.set()


def task_key(task: dict) -> str:
    return task["security_code"] + " " + url_key(task["url"])


def frozen_route_contract(task: dict) -> tuple[str, str, str, str] | None:
    if task.get("purpose") == "issuer_identity_discovery":
        return ("identity_discovery_proof", "identity_record_lineage",
                "identity_source_changed_stopped", "identity_resume_proof_missing_stopped")
    if "reviewed_ir_route_proof" in task:
        return ("reviewed_ir_route_proof", "reviewed_ir_record_lineage",
                "reviewed_ir_source_changed_stopped", "reviewed_ir_resume_proof_missing_stopped")
    return None


def tracked_route_lineages(state: dict, code: str) -> list[tuple[dict, str]]:
    """Track every own append for an issuer with a finite reviewed task."""
    return [(state[field][code], error) for field, error in (
        ("identity_record_lineage", "identity_source_changed_stopped"),
        ("reviewed_ir_record_lineage", "reviewed_ir_source_changed_stopped"))
        if code in state.get(field, {})]


def verified_frozen_resume_task(output: Path, saved: dict, lineage: dict | None) -> dict:
    """Rebuild the finite reviewed route from its original record and proof."""
    contract = frozen_route_contract(saved)
    if contract is None:
        raise ValueError("identity_resume_proof_missing_stopped")
    proof_field, _, changed_error, missing_error = contract
    code, proof = saved["security_code"], saved.get(proof_field)
    if not isinstance(proof, dict):
        raise ValueError(missing_error)
    try:
        original_sha = proof["source_record_sha256"]
        record_path = output / "records" / (code + ".json")
        current_sha = file_sha256(record_path)
        if lineage is None:
            if current_sha != original_sha:
                # Old states cannot infer that a changed record was our own write.
                raise ValueError(missing_error)
            original = read_json(record_path)
        else:
            if (not isinstance(lineage, dict) or lineage.get("source_record_sha256") != original_sha
                    or current_sha != lineage.get("expected_record_sha256")):
                raise ValueError(changed_error)
            archive = lineage.get("original_record_archive")
            if archive is None:
                if current_sha != original_sha:
                    raise ValueError(missing_error)
                original = read_json(record_path)
            else:
                if not isinstance(archive, str):
                    raise ValueError(missing_error)
                original_path = (output / archive).resolve()
                if code == "6633" and finite_named_issuer_path(output, archive, ("attempts/6633/",)) != original_path:
                    raise ValueError(changed_error)
                if (not original_path.is_relative_to((output / "attempts" / code).resolve())
                        or original_path.suffix != ".json" or not original_path.is_file()
                        or file_sha256(original_path) != original_sha):
                    raise ValueError(changed_error)
                original = read_json(original_path)
        source_path = evidence_path(output, proof["source_snapshot"])
        part = proof["proposal_source"]
        if not isinstance(part, str):
            raise ValueError(changed_error)
        part_path = (output / part).resolve()
        if (not source_path or not source_path.is_file() or part_path.suffix != ".json"
                or not part_path.is_relative_to((output / "parts").resolve()) or not part_path.is_file()
                or file_sha256(source_path) != proof["source_snapshot_sha256"]
                or file_sha256(part_path) != proof["proposal_source_sha256"]
                or original.get("security_code") != code):
            raise ValueError(changed_error)
        tasks, _ = company_candidates(output, original, proposal_rows(output).get(code, []),
                                      proof_record_sha256=original_sha)
        matches = [task for task in tasks if task_key(task) == task_key(saved)
                   and frozen_route_contract(task) == contract]
        if len(matches) != 1 or matches[0] != saved:
            raise ValueError(changed_error)
        return matches[0]
    except (KeyError, TypeError, OSError):
        raise ValueError(changed_error) from None


def verified_identity_resume_task(output: Path, saved: dict, lineage: dict | None) -> dict:
    """Compatibility entry point for the original identity-only proof."""
    return verified_frozen_resume_task(output, saved, lineage)


def successful_saved_body_count(output: Path, record: dict, new_snapshot: str, new_page: dict) -> int:
    """Count current fetch snapshots, never archived attempts or nested robots."""
    count, seen = 0, set()
    for fetch in record.get("fetches", []):
        reference = fetch.get("snapshot")
        path = evidence_path(output, reference)
        if path is None or path in seen:
            continue
        seen.add(path)
        if reference == new_snapshot:
            page = new_page  # Collection has already atomically saved this snapshot.
        elif path.is_file():
            page = read_json(path)
        else:
            continue
        if not isinstance(page, dict):
            continue
        status, text = page.get("http_status"), page.get("text")
        if (not isinstance(status, int) or not 200 <= status < 300 or page.get("error")
                or page.get("http_get_attempted") is False or not isinstance(text, str) or not text.strip()
                or page.get("failure_signature") == "common_transport_503" or research.TRANSPORT_FAILURE.search(text)
                or any(safe_url(page.get(field)) and urlsplit(page[field]).path == "/robots.txt"
                       for field in ("requested_url", "url"))):
            continue
        count += 1
    return count


def append_observation(output: Path, task: dict, page: dict, snapshot: str, get_count: int) -> str:
    path = output / "records" / (task["security_code"] + ".json")
    old = read_json(path)  # Re-read after GET; keep any intervening human review.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    archive = output / "attempts" / task["security_code"] / (stamp + "-followup.json")
    research.write_json(archive, old)
    updated = copy.deepcopy(old)
    updated["previous_attempts"] = [*old.get("previous_attempts", []), str(archive.relative_to(output))]
    updated.setdefault("fetches", []).append({**research.request_metadata(page), "url": task["url"],
        "final_url": page.get("url"), "snapshot": snapshot,
        "discovery_parent_url": task["parent_url"], "discovery_parent_snapshot": task["parent_snapshot"],
        "discovery_link_label": task["discovery_link_label"], "explicit_ir_link": task["explicit_ir_link"],
        **{key: task[key] for key in ("ir_scope_evidence", "binding_evidence", "parser_refresh_proof", "identity_discovery_proof", "reviewed_ir_route_proof", "purpose") if key in task}})
    updated["successful_official_page_count"] = successful_saved_body_count(output, updated, snapshot, page)
    updated["followup_completed_at"] = research.now()
    updated["followup_http_get_attempt_count"] = old.get("followup_http_get_attempt_count", 0) + get_count
    if page.get("http_status") == 200 and not page.get("error") or task.get("purpose") == "issuer_identity_discovery":
        if old.get("manual_review_required") is False and old.get("manual_review"):
            previous = updated.get("previous_manual_review", [])
            updated["previous_manual_review"] = [*(previous if isinstance(previous, list) else [previous]), updated.pop("manual_review")]
        updated["manual_review_required"] = True
        updated.setdefault("followup_review_pending", []).append({"snapshot": snapshot, "url": page.get("url"),
            "parent_url": task["parent_url"], "parent_snapshot": task["parent_snapshot"],
            "discovery_link_label": task["discovery_link_label"], "explicit_ir_link": task["explicit_ir_link"],
            **{key: task[key] for key in ("purpose", "identity_discovery_proof", "reviewed_ir_route_proof") if key in task}})
    # Classification, original quotations, conditions and identity stay intact.
    research.write_json(path, updated)
    # Match write_json's exact bytes; a later writer cannot silently extend the
    # proof for a second identity-discovery URL within this same collection.
    return hashlib.sha256((json.dumps(updated, ensure_ascii=False, indent=2) + "\n").encode("utf-8")).hexdigest()


def collect(output: Path, state_path: Path, plan: dict, max_gets: int, global_rps: float, fetcher=None) -> int:
    refresh = plan.get("mode") == PARSER_REFRESH_MODE
    if refresh and (state_path != output / PARSER_REFRESH_STATE or global_rps != 0.25
                    or max_gets > PARSER_REFRESH_MAX_GETS):
        raise ValueError("parser refresh needs its fixed state, 0.25 RPS and at most 12 GETs")
    if state_path.exists():
        state = read_json(state_path)
        if state.get("format") != "ir_followup_collection" or state.get("output") != str(output):
            raise ValueError("state belongs to another survey or format")
        if state.get("mode") != plan.get("mode") or refresh and state.get("audit_sha256") != plan.get("audit_sha256"):
            raise ValueError("state belongs to another collection mode or audit")
        if not re.fullmatch(r"[0-9]{8}T[0-9]{12}Z", str(state.get("run_id", ""))):
            raise ValueError("invalid saved run identifier")
        if any(not CODE.fullmatch(str(task.get("security_code", ""))) or not safe_url(task.get("url"))
               for task in state.get("selected", [])):
            raise ValueError("unsafe saved followup task")
    else:
        state = {"format": "ir_followup_collection", "output": str(output), "started_at": research.now(),
                 "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"),
                 "selected": plan["selected"], "done": [], "todo": plan["selected"], "pages": [], "attempts": [],
                 "preflight": [], "http_get_attempt_count": 0, "http_429_count": 0, "common_transport_503_count": 0}
        state["identity_record_lineage"] = {task["security_code"]: {
            "source_record_sha256": task["identity_discovery_proof"]["source_record_sha256"],
            "expected_record_sha256": task["identity_discovery_proof"]["source_record_sha256"],
            "original_record_archive": None}
            for task in plan["selected"] if task.get("purpose") == "issuer_identity_discovery"}
        state["reviewed_ir_record_lineage"] = {task["security_code"]: {
            "source_record_sha256": task["reviewed_ir_route_proof"]["source_record_sha256"],
            "expected_record_sha256": task["reviewed_ir_route_proof"]["source_record_sha256"],
            "original_record_archive": None}
            for task in plan["selected"] if "reviewed_ir_route_proof" in task}
        if refresh:
            state.update(mode=PARSER_REFRESH_MODE, audit_sha256=plan["audit_sha256"],
                         refresh_claims={}, reserved_get_count=0)
    baseline = {key: state.get(key, 0) for key in ("http_get_attempt_count", "http_429_count", "common_transport_503_count")}
    remaining = max_gets - (state.get("reserved_get_count", 0) if refresh else baseline["http_get_attempt_count"])
    if fetcher is None:
        fetcher = BoundedFetcher(max(0, remaining), global_rps, raw_directory=output / "raw")
    done = set(state["done"])
    if refresh:
        done.update(state["refresh_claims"])

        def reserve_dispatch(url, result):
            if state["reserved_get_count"] >= max_gets:
                fetcher.limit_reached = True
                result["error"] = "followup_get_limit_reached"
                return False
            state["reserved_get_count"] += 1
            # Reserve before dispatch so a restart cannot exceed the hard cap.
            research.write_json(state_path, state)
            return True

        fetcher.before_dispatch = reserve_dispatch
    state.update(max_gets=max_gets, global_rps=global_rps, finished_at=None)

    def save(status):
        state.update(status=status, observed_at=research.now(), done=sorted(done),
                     todo=[task for task in state["selected"] if task_key(task) not in done])
        stats = fetcher.stats()
        for key, original in baseline.items():
            state[key] = original + stats.get(key, 0)
        if status != "running":
            state["finished_at"] = research.now()
        research.write_json(state_path, state)

    pending = [task for task in state["selected"] if task_key(task) not in done]
    if not pending:
        save("completed")
        return 0
    if remaining <= 0:
        save("get_budget_exhausted")
        return 0
    # Own appends change review eligibility. Recover only finite reviewed routes
    # whose original archive, source proof and last own write still match.
    # An old or changed state keeps pending tasks visible and stops before GETs.
    permitted = {task_key(task): task for task in plan["selected"]}
    for saved in pending:
        contract = frozen_route_contract(saved)
        if contract is None:
            continue
        proof_field, lineage_field, _, missing_error = contract
        route_lineage = state.setdefault(lineage_field, {})
        code = saved["security_code"]
        try:
            task = verified_frozen_resume_task(output, saved, route_lineage.get(code))
        except (ValueError, AttributeError) as error:
            reason = str(error) if isinstance(error, ValueError) else missing_error
            state["attempts"].append({"key": task_key(saved), "stopped": reason})
            save(reason)
            return 2
        permitted[task_key(task)] = task
        route_lineage.setdefault(code, {"source_record_sha256": task[proof_field]["source_record_sha256"],
            "expected_record_sha256": task[proof_field]["source_record_sha256"],
            "original_record_archive": None})
    save("running")
    health = fetcher.raw_get(PREFLIGHT)
    health_path = output / "followup-runs" / state["run_id"] / ("preflight-" + str(len(state["preflight"]) + 1) + ".json")
    research.write_json(health_path, health)
    passed = health.get("http_status") == 200 and "新規上場" in health.get("text", "") and not health.get("error")
    state["preflight"].append({"snapshot": str(health_path.relative_to(output)), "passed": passed,
                               **research.request_metadata(health)})
    if not passed:
        save("environment_preflight_failed")
        return 2
    # General IR tasks use the latest plan; finite reviewed routes additionally
    # require the revalidated proof above. State never authorizes a bare URL.
    for saved in pending:
        key = task_key(saved)
        task = permitted.get(key)
        if task is None:
            contract = frozen_route_contract(saved)
            if contract:
                save(contract[3])
                return 2
            done.add(key)
            state["attempts"].append({"key": key, "skipped": "already_saved_or_no_longer_eligible"})
            save("running")
            continue
        if fetcher.environment_failed.is_set() or fetcher.limit_reached:
            break
        if fetcher.http_get_attempt_count >= remaining:
            fetcher.limit_reached = True
            break
        fetcher.allowed_hosts = {host_key(PREFLIGHT), host_key(task["official_url"]), host_key(task["url"])}
        tracked = tracked_route_lineages(state, task["security_code"])
        record_path = output / "records" / (task["security_code"] + ".json")
        for own_lineage, own_changed_error in tracked:
            if file_sha256(record_path) != own_lineage["expected_record_sha256"]:
                save(own_changed_error)
                return 2
        contract = frozen_route_contract(task)
        if contract:
            proof_field, lineage_field, changed_error, _ = contract
            proof = task[proof_field]
            expected_record_sha = state[lineage_field][task["security_code"]]["expected_record_sha256"]
            if (saved.get(proof_field) != proof
                    or file_sha256(output / "records" / (task["security_code"] + ".json")) != expected_record_sha
                    or ("finite_saved_source_guards" in proof and not completed_identity_audit_matches(output, proof))
                    or file_sha256(evidence_path(output, proof["source_snapshot"])) != proof["source_snapshot_sha256"]
                    or file_sha256(output / proof["proposal_source"]) != proof["proposal_source_sha256"]
                    or not finite_own_archive_matches(output, proof, state[lineage_field][task["security_code"]])
                    or not completed_identity_audit_matches(output, proof)):
                save(changed_error)
                return 2
        if refresh:
            proof = task["parser_refresh_proof"]
            if (file_sha256(output / "records" / (task["security_code"] + ".json")) != proof["source_record_sha256"]
                    or file_sha256(output / proof["audit_snapshot"]) != proof["audit_sha256"]
                    or file_sha256(evidence_path(output, task["parent_snapshot"])) != proof["parent_snapshot_sha256"]
                    or file_sha256(evidence_path(output, proof["previous_target_snapshot"])) != proof["previous_target_snapshot_sha256"]
                    or file_sha256(Path(research.__file__)) != proof["parser_script_sha256"]):
                save("source_changed_stopped")
                return 2
            state["refresh_claims"][key] = {"claimed_at": research.now(), "status": "claimed_once",
                                            "source_record_sha256": proof["source_record_sha256"]}
            done.add(key)
            # A claimed refresh is never attempted again, even after interruption.
            save("running")
        before = fetcher.http_get_attempt_count
        try:
            page = fetcher.capture(task["url"])
        except BaseException:
            if refresh:
                save("refresh_interrupted")
            raise
        delta = fetcher.http_get_attempt_count - before
        page.update(source_type="official_seed_identity_discovery_page" if task.get("purpose") == "issuer_identity_discovery" else "official_public_contact_page", security_code=task["security_code"],
                    discovery_parent_url=task["parent_url"], discovery_parent_snapshot=task["parent_snapshot"],
                    discovery_link_label=task["discovery_link_label"], explicit_ir_link=task["explicit_ir_link"],
                    official_identity_basis=task["association_basis"], submitted=False)
        page.update({key: task[key] for key in ("ir_scope_evidence", "binding_evidence", "parser_refresh_proof", "identity_discovery_proof", "reviewed_ir_route_proof", "purpose") if key in task})
        snapshot_path = output / "evidence" / task["security_code"] / state["run_id"] / (f"followup-{len(state['pages']) + 1:04}.json")
        snapshot = str(snapshot_path.relative_to(output))
        research.write_json(snapshot_path, page)
        state["pages"].append({"security_code": task["security_code"], "snapshot": snapshot,
                                "url": task["url"], "http_status": page.get("http_status")})
        state["attempts"].append({"key": key, "http_get_attempt_count": delta, "snapshot": snapshot,
                                   **research.request_metadata(page)})
        if refresh:
            state["refresh_claims"][key].update(status="observed", snapshot=snapshot)
        if delta or page.get("error") not in {"environment_circuit_breaker_open", "followup_get_limit_reached"}:
            updated_sha = append_observation(output, task, page, snapshot, delta)
            if tracked:
                updated = read_json(record_path)
                archive = updated.get("previous_attempts", [None])[-1]
                archive_path = (output / archive).resolve() if isinstance(archive, str) else None
                for own_lineage, own_changed_error in tracked:
                    if (file_sha256(record_path) != updated_sha or archive_path is None
                            or not archive_path.is_relative_to((output / "attempts" / task["security_code"]).resolve())
                            or not archive_path.is_file() or file_sha256(archive_path) != own_lineage["expected_record_sha256"]):
                        save(own_changed_error)
                        return 2
                    if own_lineage["original_record_archive"] is None:
                        own_lineage["original_record_archive"] = archive
                    own_lineage["expected_record_sha256"] = updated_sha
        if not fetcher.environment_failed.is_set() and not fetcher.limit_reached:
            done.add(key)
        save("running")
        if fetcher.environment_failed.is_set() or fetcher.limit_reached:
            break
    stopped = fetcher.environment_failed.is_set()
    save("environment_stopped" if stopped else "get_budget_exhausted" if fetcher.limit_reached else "completed")
    return 2 if stopped else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--state", type=Path, help="Resume this finite queue; defaults to output/followup-current-run.json")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--parser-refresh", action="store_true", help="Only the two preserved 2752/2784 parser-refresh URLs; fixed state, one attempt each")
    parser.add_argument("--global-rps", type=float)
    parser.add_argument("--max-gets", type=int, help="Total GET dispatch cap including preflight/robots/redirects and prior state")
    parser.add_argument("--max-links-per-company", type=int, default=3)
    parser.add_argument("--only-codes", nargs="+")
    args = parser.parse_args(argv)
    if args.global_rps is None:
        args.global_rps = 0.25 if args.parser_refresh else 1.0
    if args.max_gets is None:
        args.max_gets = PARSER_REFRESH_MAX_GETS if args.parser_refresh else 1000
    if args.parser_refresh and (args.state is not None or args.only_codes is not None
                               or args.global_rps != 0.25 or args.max_gets > PARSER_REFRESH_MAX_GETS):
        parser.error("parser-refresh uses a fixed state and both fixed targets, 0.25 RPS, max-gets <= 12")
    if not math.isfinite(args.global_rps) or not 0 < args.global_rps <= 4:
        parser.error("global-rps must be finite and 0 < RPS <= 4")
    if args.max_gets < 1 or not 1 <= args.max_links_per_company <= 3:
        parser.error("max-gets must be positive; max-links-per-company must be 1..3")
    if args.only_codes and any(not CODE.fullmatch(code) for code in args.only_codes):
        parser.error("only-codes must contain four-character security codes")
    output = args.output.resolve()
    state_path = (output / PARSER_REFRESH_STATE if args.parser_refresh else args.state or output / "followup-current-run.json").resolve()
    plan = build_parser_refresh_plan(output) if args.parser_refresh else build_plan(output, args.max_links_per_company, args.only_codes)
    if args.plan_only:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.with_suffix(state_path.suffix + ".lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("another followup collector owns this state")
        result = collect(output, state_path, plan, args.max_gets, args.global_rps)
    state = read_json(state_path)
    print(json.dumps({"state": str(state_path), "status": state["status"], "done": len(state["done"]),
                      "todo": len(state["todo"]), "http_get_attempt_count": state["http_get_attempt_count"]}, ensure_ascii=False))
    return result


if __name__ == "__main__":
    sys.exit(main())
