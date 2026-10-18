"""One-day J-Quants V2 financial-summary SDK snapshots, without valuation.

The SDK-returned rows are preserved as JSON-compatible data. They are neither
original HTTP JSON lexemes nor issuer PDF/full-text disclosures. Financial
units, periods, forecast authorship and accounting scopes are not interpreted.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from .common import (
    DataAdapterError, canonical_json, empty_bundle, non_ordinary_security_code,
    normalize_security_code, records, request_date, retrieval_timestamp,
    stable_source_id,
)
from .jquants import JQUANTS_API_BASE, _row_date


def _company_scope(company_ids: Iterable[str]) -> set[str]:
    if isinstance(company_ids, (str, bytes, Mapping)):
        raise ValueError("company_ids must explicitly list existing canonical jp:CODE IDs")
    try:
        values = list(company_ids)
    except TypeError:
        raise ValueError("company_ids must explicitly list existing canonical jp:CODE IDs") from None
    if not values:
        raise ValueError("J-Quants financial summaries require a nonempty existing company scope")
    for identifier in values:
        if not isinstance(identifier, str) or not identifier.startswith("jp:"):
            raise ValueError("company_ids must contain canonical jp:CODE IDs")
        if identifier != "jp:" + normalize_security_code(identifier[3:]):
            raise ValueError("company_ids must contain canonical jp:CODE IDs")
    return set(values)


def _disclosure_date(value: Any) -> str:
    try:
        result = _row_date(value)
        if isinstance(value, str) and len(value) > 10:
            datetime.fromisoformat(value)
        return result
    except (ValueError, TypeError):
        raise ValueError("J-Quants financial summary requires a valid DiscDate") from None


def normalize_jquants_financial_summary(
    rows: Any,
    *,
    company_ids: Iterable[str],
    retrieved_at: str | datetime | None = None,
) -> dict:
    """Keep only an explicit existing-company scope; never create companies.

    Code and DiscDate identify each row's company and disclosure-day reference.
    All other returned fields, including missing, forecast and nonconsolidated
    values, remain in the row without unit or financial-meaning conversion.
    Equal rows deduplicate; changed rows produce distinct immutable source IDs.
    """
    scope = _company_scope(company_ids)
    received = retrieval_timestamp(retrieved_at)
    sources: dict[str, dict] = {}
    skipped: dict[str, dict] = {}
    for row in records(rows):
        other_security = non_ordinary_security_code(row.get("Code"))
        code = other_security or normalize_security_code(row.get("Code"))
        company_id = f"jp:{code}"
        if other_security or company_id not in scope:
            item = skipped.setdefault(code, {
                "security_code": code, "record_count": 0,
                "reason_code": "non_ordinary_security_code" if other_security else "outside_explicit_company_scope",
                "reason": "5桁末尾非0の別種証券は対象外。" if other_security else "明示された既存company scopeの対象外。",
            })
            item["record_count"] += 1
            continue
        disclosure_date = _disclosure_date(row.get("DiscDate"))
        # This is a dataset reference, not evidence of a per-company HTTP call.
        url = f"{JQUANTS_API_BASE}/fins/summary?" + urlencode({"date": disclosure_date})
        content = canonical_json(row)
        metadata = {
            "provider": "jquants_financials", "dataset": "fins/summary",
            "adapter_version": 1, "document_kind": "SDK_financial_summary_row",
            "disclosure_date": disclosure_date, "publication_time_known": False,
            "SDK_row_not_original_HTTP_JSON": True,
            "issuer_PDF_or_full_text": False,
            "raw_HTTP_or_wire_capture_verified": False,
            "SDK_numeric_lexemes_or_original_precision_verified": False,
            "financial_units_or_meaning_interpreted": False,
            "meaning_review_required": True, "financial_inputs_verified": False,
            "forecast_values_automatically_adopted": False,
            "retrieval_basis": "local SDK result receipt; not HTTP body completion or publication time",
        }
        if row.get("synthetic") is True:
            metadata["synthetic"] = True
        source_id = stable_source_id("jquants-financials", company_id=company_id,
                                     url=url, content=content, metadata=metadata)
        sources[source_id] = {
            "id": source_id, "company_id": company_id,
            "title": f"{company_id} J-Quants財務情報サマリ {disclosure_date}",
            "url": url, "source_type": "public_disclosure",
            "published_at": None, "retrieved_at": received,
            "content": content, "requires_research": True, "metadata": metadata,
        }
    bundle = empty_bundle()
    bundle["sources"] = sorted(sources.values(), key=lambda item: (
        item["company_id"], item["metadata"]["disclosure_date"], item["id"]))
    if skipped:
        bundle["skipped_security_codes"] = sorted(skipped.values(), key=lambda item: item["security_code"])
    return bundle


def fetch_jquants_financial_summary(
    date: str,
    *,
    company_ids: Iterable[str],
    api_key: str | None = None,
    client: Any = None,
) -> dict:
    """Call get_fin_summary_cursor once for one disclosure day, without cursor.

    The SDK may paginate internally. Returned cursors are discarded; this is
    not premium incremental retrieval. An empty scope fails before client
    initialization. Injection supports credential-free, offline verification.
    """
    date = request_date(date)
    scope = _company_scope(company_ids)
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
        response = client.get_fin_summary_cursor(date_yyyymmdd=date)
        received = retrieval_timestamp()
    except Exception:
        raise DataAdapterError("J-Quants financial-summary read failed; check plan, date, credentials, and rate limits") from None
    if not isinstance(response, tuple) or len(response) != 2:
        raise DataAdapterError("J-Quants financial-summary SDK returned an invalid result contract")
    rows, _ = response  # No cursor persistence, inspection or follow-up request.
    bundle = normalize_jquants_financial_summary(rows, company_ids=scope, retrieved_at=received)
    if any(source["metadata"]["disclosure_date"] != date for source in bundle["sources"]):
        raise DataAdapterError("J-Quants financial-summary DiscDate differs from the requested disclosure day")
    return bundle
