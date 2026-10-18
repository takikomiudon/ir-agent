"""Read-only J-Quants V2 SDK integration and offline record normalization."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from urllib.parse import urlencode

from .common import (
    DataAdapterError,
    canonical_json,
    company_record,
    empty_bundle,
    non_ordinary_security_code,
    normalize_security_code,
    records,
    request_date,
    retrieval_timestamp,
    stable_source_id,
)

JQUANTS_API_BASE = "https://api.jquants.com/v2"


def _row_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    # pandas Date columns represent trading dates; midnight is not publication.
    if isinstance(value, str) and len(value) >= 10:
        suffix = value[10:]
        if not suffix or suffix.startswith("T") or suffix.startswith(" "):
            return request_date(value[:10])
    raise ValueError("J-Quants daily bar must contain a valid Date")


def normalize_jquants_daily(
    company_master: Any,
    daily_bars: Any,
    *,
    retrieved_at: str | datetime | None = None,
) -> dict:
    """Normalize observed V2 master/bars, with no fabricated publication time.

    Daily bars reference the exact imported master row in metadata. A bar with
    no master row fails instead of inventing a company name. The bundle marks
    price sources as not requiring qualitative research.
    """
    timestamp = retrieval_timestamp(retrieved_at)
    masters: dict[str, dict] = {}
    companies: dict[str, dict] = {}
    skipped: dict[str, dict] = {}

    def skip_non_ordinary(row: dict) -> bool:
        code = non_ordinary_security_code(row.get("Code"))
        if code is None:
            return False
        item = skipped.setdefault(code, {
            "security_code": code,
            "record_count": 0,
            "reason": "5桁末尾非0の別種証券は普通株モデルの対象外。",
        })
        item["record_count"] += 1
        return True

    for row in records(company_master):
        if skip_non_ordinary(row):
            continue
        code = normalize_security_code(row.get("Code"))
        name = row.get("CoName")
        company = company_record(code, name)
        if code in masters and masters[code] != row:
            raise ValueError("J-Quants returned conflicting company master rows")
        masters[code] = row
        companies[company["id"]] = company

    sources: dict[str, dict] = {}
    for row in records(daily_bars):
        if skip_non_ordinary(row):
            continue
        code = normalize_security_code(row.get("Code"))
        if code not in masters:
            raise ValueError("J-Quants daily bar has no matching company master row")
        trading_date = _row_date(row.get("Date"))
        company_id = f"jp:{code}"
        url = f"{JQUANTS_API_BASE}/equities/bars/daily?" + urlencode({"code": row["Code"], "date": trading_date})
        content = canonical_json(row)
        metadata = {
            "provider": "jquants",
            "dataset": "equities/bars/daily",
            "trading_date": trading_date,
            "company_master": masters[code],
            "publication_time_known": False,
        }
        source_id = stable_source_id("jquants", company_id=company_id, url=url, content=content, metadata=metadata)
        sources[source_id] = {
            "id": source_id,
            "company_id": company_id,
            "title": f"{companies[company_id]['name']} 株価日足 {trading_date}",
            "url": url,
            "source_type": "market_data",
            "published_at": None,
            "retrieved_at": timestamp,
            "content": content,
            "requires_research": False,
            "metadata": metadata,
        }
    bundle = empty_bundle()
    bundle["companies"] = sorted(companies.values(), key=lambda item: item["id"])
    bundle["sources"] = sorted(sources.values(), key=lambda item: (item["company_id"], item["metadata"]["trading_date"], item["id"]))
    if skipped:
        bundle["skipped_security_codes"] = sorted(skipped.values(), key=lambda item: item["security_code"])
    return bundle


def fetch_jquants_daily(date: str, api_key: str | None = None, client: Any = None) -> dict:
    """Fetch one date across all securities via two paginated V2 SDK methods.

    The SDK reads JQUANTS_API_KEY/configuration when api_key is omitted. No
    registration, write operations, or trading are performed. Inject a client
    with these methods to test without credentials or external API calls.
    """
    date = request_date(date)
    if client is None:
        try:
            import jquantsapi
        except ImportError:
            raise DataAdapterError("Install the optional data SDKs: pip install 'ir-agent[data]'") from None
        try:
            client = jquantsapi.ClientV2(api_key=api_key)
        except Exception:
            raise DataAdapterError("Unable to initialize J-Quants V2; check SDK configuration and credentials") from None
    try:
        master = client.get_eq_master(date=date)
        bars = client.get_eq_bars_daily(date_yyyymmdd=date)
    except Exception as error:
        raise DataAdapterError(f"J-Quants read failed ({type(error).__name__}); check plan, date, credentials, and rate limits") from None
    return normalize_jquants_daily(master, bars)
