"""Shared, dependency-free normalization helpers for read-only data adapters."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import re
import unicodedata
from collections.abc import Mapping
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any


class DataAdapterError(RuntimeError):
    """An adapter failed without exposing request credentials in its message."""


def non_ordinary_security_code(value: Any) -> str | None:
    """Identify five-character nonzero suffixes without hiding malformed input."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    code = unicodedata.normalize("NFKC", str(value)).strip().upper()
    if re.fullmatch(r"(?=.*[0-9])[0-9A-Z]{5}", code) and not code.endswith("0"):
        return code
    return None


def normalize_security_code(value: str | int) -> str:
    """Keep alphanumeric tickers; remove only the ordinary-share fifth zero.

    Five-character codes with a nonzero suffix are outside this baseline's
    ordinary-share model. Rejecting them avoids merging distinct securities.
    """
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("security code must be a string or integer")
    code = unicodedata.normalize("NFKC", str(value)).strip().upper()
    if len(code) == 5 and code.endswith("0"):
        code = code[:-1]
    if not re.fullmatch(r"(?=.*[0-9])[0-9A-Z]{4}", code) or code == "0000":
        raise ValueError("expected a four-character ordinary-share security code")
    return code


def retrieval_timestamp(value: str | datetime | None = None) -> str:
    """Return an offset-aware timestamp, never assuming a caller's timezone."""
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("retrieved_at must be an offset-aware ISO timestamp") from None
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("retrieved_at must be an offset-aware ISO timestamp")
    return value.isoformat()


def request_date(value: str) -> str:
    """Validate the YYYY-MM-DD API date before any network access."""
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("date must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise ValueError("date must be a valid calendar date") from None


def json_value(value: Any) -> Any:
    """Preserve source precision and missingness as strict JSON-compatible data."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if not math.isfinite(value):
            raise ValueError("source data contains an infinite number")
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("source data contains a non-finite decimal")
        return str(value)
    # pandas NaT can also satisfy isinstance(value, datetime).
    if type(value).__module__.startswith("pandas.") and type(value).__name__ in {"NAType", "NaTType"}:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {field.name: json_value(getattr(value, field.name)) for field in dataclasses.fields(value)}
    # pandas and numpy are optional SDK dependencies, not baseline dependencies.
    scalar = getattr(value, "item", None)
    if callable(scalar):
        converted = scalar()
        if converted is not value:
            return json_value(converted)
    export = getattr(value, "to_dict", None)
    if callable(export):
        return json_value(export())
    raise ValueError(f"unsupported source value type: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(json_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def stable_source_id(provider: str, *, company_id: str, url: str, content: str, metadata: dict) -> str:
    """Hash source identity and content, deliberately excluding retrieval time."""
    identity = {"company_id": company_id, "url": url, "content": content, "metadata": metadata}
    return f"{provider}:" + hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest()


def records(value: Any) -> list[dict]:
    """Accept SDK DataFrames or plain records without importing pandas."""
    if isinstance(value, (list, tuple)):
        rows = value
    elif callable(getattr(value, "to_dict", None)):
        rows = value.to_dict(orient="records")
    else:
        raise ValueError("expected a DataFrame or a list of source records")
    if not isinstance(rows, (list, tuple)) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("expected a list of source record mappings")
    return [json_value(row) for row in rows]


def company_record(code: str, name: str) -> dict:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("source record must contain a company name")
    return {
        "id": f"jp:{code}",
        "name": name.strip(),
        "security_code": code,
        "status": "active",
        "screening_reason": "データ取り込み済み。投資対象のスクリーニングは未実施。",
    }


def empty_bundle() -> dict:
    return {"schema_version": 1, "companies": [], "sources": []}
