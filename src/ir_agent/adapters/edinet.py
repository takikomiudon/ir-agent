"""EDINET index normalization and optional edinet-tools package parsing."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .common import (
    DataAdapterError,
    canonical_json,
    company_record,
    empty_bundle,
    json_value,
    non_ordinary_security_code,
    normalize_security_code,
    request_date,
    retrieval_timestamp,
    stable_source_id,
)

EDINET_API_BASE = "https://api.edinet-fsa.go.jp/api/v2"
JST = timezone(timedelta(hours=9))


def _submission_timestamp(value: Any) -> str | None:
    """Interpret documented submission time in JST; date-only stays unknown."""
    if value in (None, ""):
        return None
    if isinstance(value, str):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return None
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("EDINET submitDateTime is malformed") from None
    if not isinstance(value, datetime):
        raise ValueError("EDINET submitDateTime must be a datetime or ISO string")
    if value.tzinfo is None:
        value = value.replace(tzinfo=JST)
    return value.isoformat()


def _document_id(document: Mapping) -> str:
    value = document.get("docID")
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z0-9]+", value):
        raise ValueError("EDINET document must contain a valid docID")
    return value


def _report_data(report: Any) -> dict:
    if isinstance(report, Mapping):
        return json_value(report)
    export = getattr(report, "to_dict", None)
    if not callable(export):
        raise ValueError("EDINET parser must return a mapping or report with to_dict()")
    data = dict(export())
    # SDK to_dict() omits narrative/raw maps; keep these for source inspection.
    for field in ("raw_fields", "unmapped_fields", "text_blocks"):
        if hasattr(report, field):
            data[field] = getattr(report, field)
    return json_value(data)


def normalize_edinet_document(
    document: Mapping,
    *,
    retrieved_at: str | datetime | None = None,
    parsed_report: Any = None,
) -> dict:
    """Normalize a listed filer's index row, optionally retaining parsed facts.

    No security code means no inferred stock attribution: the returned bundle
    is empty. In particular, attributing a large shareholder's filing to its
    target stock requires a separately checked issuer/target mapping.
    """
    if not isinstance(document, Mapping):
        raise ValueError("EDINET document metadata must be a mapping")
    timestamp = retrieval_timestamp(retrieved_at)
    document = json_value(document)
    doc_id = _document_id(document)
    if document.get("secCode") in (None, ""):
        bundle = empty_bundle()
        bundle["skipped_documents"] = [{"doc_id": doc_id, "reason": "提出者の株式証券コードがなく、投資対象会社を未確認。"}]
        return bundle
    unsupported_code = non_ordinary_security_code(document["secCode"])
    if unsupported_code is not None:
        bundle = empty_bundle()
        bundle["skipped_security_codes"] = [{
            "security_code": unsupported_code,
            "record_count": 1,
            "reason": "5桁末尾非0の別種証券は普通株モデルの対象外。",
        }]
        return bundle
    code = normalize_security_code(document["secCode"])
    company = company_record(code, document.get("filerName"))
    url = f"{EDINET_API_BASE}/documents/{doc_id}?type=1"
    payload = {"document_metadata": document}
    if parsed_report is not None:
        payload["parsed_report"] = _report_data(parsed_report)
    content = canonical_json(payload)
    metadata = {
        "provider": "edinet",
        "dataset": "documents",
        "doc_id": doc_id,
        "edinet_code": document.get("edinetCode"),
        "doc_type_code": document.get("docTypeCode"),
        "period_start": document.get("periodStart"),
        "period_end": document.get("periodEnd"),
        "index_only": parsed_report is None,
        "company_attribution": "filer",
    }
    source_id = stable_source_id("edinet", company_id=company["id"], url=url, content=content, metadata=metadata)
    source = {
        "id": source_id,
        "company_id": company["id"],
        "title": document.get("docDescription") or f"EDINET {doc_id}",
        "url": url,
        "source_type": "public_disclosure",
        "published_at": _submission_timestamp(document.get("submitDateTime")),
        "retrieved_at": timestamp,
        "content": content,
        "requires_research": True,
        "metadata": metadata,
    }
    return {"schema_version": 1, "companies": [company], "sources": [source]}


def fetch_edinet_documents(date: str, api_key: str | None = None, client: Any = None) -> dict:
    """Read one day's index with the SDK's explicit-key low-level function.

    client can be edinet_tools.api or a mock exposing fetch_documents_list().
    Omitting the key uses the SDK's EDINET_API_KEY/configuration resolution.
    This function does not download or parse every filing automatically.
    """
    date = request_date(date)
    if client is None:
        try:
            from edinet_tools import api as client
        except ImportError:
            raise DataAdapterError("Install the optional data SDKs: pip install 'ir-agent[data]'") from None
    try:
        response = client.fetch_documents_list(date, type=2, api_key=api_key)
    except Exception as error:
        raise DataAdapterError(f"EDINET index read failed ({type(error).__name__}); check credentials, date, and rate limits") from None
    if not isinstance(response, Mapping):
        raise DataAdapterError("EDINET index did not return a metadata/results mapping")
    response_metadata = response.get("metadata") or {}
    if not isinstance(response_metadata, Mapping):
        raise DataAdapterError("EDINET index returned malformed response metadata")
    status = response.get("StatusCode", response_metadata.get("status"))
    if status is not None and str(status) != "200":
        raise DataAdapterError("EDINET index returned an error status; this is not an empty filing day")
    rows = response.get("results")
    if not isinstance(rows, list):
        raise DataAdapterError("EDINET index is missing its results list")
    timestamp = retrieval_timestamp()
    companies: dict[str, dict] = {}
    sources: dict[str, dict] = {}
    skipped_codes: dict[str, dict] = {}
    skipped_documents = []
    for row in rows:
        bundle = normalize_edinet_document(row, retrieved_at=timestamp)
        companies.update({item["id"]: item for item in bundle["companies"]})
        sources.update({item["id"]: item for item in bundle["sources"]})
        skipped_documents.extend(bundle.get("skipped_documents", []))
        for item in bundle.get("skipped_security_codes", []):
            code = item["security_code"]
            if code not in skipped_codes:
                skipped_codes[code] = dict(item)
            else:
                skipped_codes[code]["record_count"] += item["record_count"]
    result = {
        "schema_version": 1,
        "companies": sorted(companies.values(), key=lambda item: item["id"]),
        "sources": sorted(sources.values(), key=lambda item: (item["company_id"], item["id"])),
    }
    if skipped_codes:
        result["skipped_security_codes"] = sorted(skipped_codes.values(), key=lambda item: item["security_code"])
    if skipped_documents:
        result["skipped_documents"] = skipped_documents
    return result


def parse_edinet_package(
    package: bytes | str | Path,
    document_metadata: Mapping,
    *,
    source: str = "instance",
    parser: Any = None,
    retrieved_at: str | datetime | None = None,
) -> dict:
    """Parse a saved type-1 ZIP with no API key, retaining facts and narratives.

    Choose instance or inline XBRL explicitly. Unsupported native formats fail;
    the adapter never substitutes a different extraction method silently.
    """
    if source not in {"instance", "xbrl"}:
        raise ValueError("source must be 'instance' or 'xbrl'")
    if not isinstance(document_metadata, Mapping):
        raise ValueError("EDINET document metadata must be a mapping")
    doc_id = _document_id(document_metadata)
    doc_type = document_metadata.get("docTypeCode")
    if not isinstance(doc_type, str) or not re.fullmatch(r"\d{3}", doc_type):
        raise ValueError("EDINET parsing requires a three-digit docTypeCode")
    raw = package if isinstance(package, bytes) else Path(package).read_bytes()
    if not raw.startswith(b"PK"):
        raise ValueError("expected an EDINET type-1 ZIP package")
    if parser is None:
        try:
            import edinet_tools as parser
        except ImportError:
            raise DataAdapterError("Install the optional data SDKs: pip install 'ir-agent[data]'") from None
    try:
        report = parser.parse_xbrl(raw, doc_type, source=source, doc_id=doc_id)
    except Exception as error:
        raise DataAdapterError(f"EDINET package parsing failed ({type(error).__name__}); inspect the original package and extraction format") from None
    return normalize_edinet_document(document_metadata, retrieved_at=retrieved_at, parsed_report=report)
