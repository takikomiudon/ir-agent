"""Pure, traceable conversion of saved J-Quants V2 daily bars to quotes.

V2 field definitions: https://jpx-jquants.com/ja/spec/eq-bars-daily
The upstream adapter preserves the raw bar and does not know an observation
time. Midnight below is explicitly a date's lower bound, never a closing or
publication time. Consumers requiring exact observation times must hold it.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, time
import json

from .adapters.common import canonical_json, normalize_security_code, stable_source_id
from .models import JST, day, object_value, timestamp, validate_source
from .valuation import _number


def _trading_date(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("J-Quants Date must contain a trading date")
    trading_date = day(value[:10], "J-Quants Date").isoformat()
    if len(value) > 10:
        # The adapter also accepts SDK/pandas datetime values for this column.
        # Their time component is not a quote observation or publication time.
        if value[10] not in {"T", " "}:
            raise ValueError("J-Quants Date must contain a valid date or datetime")
        try:
            datetime.fromisoformat(value)
        except ValueError as error:
            raise ValueError("J-Quants Date must contain a valid date or datetime") from error
    return trading_date


def _unique_object(items: list[tuple]) -> dict:
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("J-Quants source content has duplicate JSON keys")
        result[key] = value
    return result


def normalize_jquants_quote(source: dict, *, price_field: str = "C") -> dict:
    """Bind an unadjusted close to a separately identified derived snapshot.

    Input is an existing ``normalize_jquants_daily`` source, not an API row.
    Raw C is the actual JPY close; AdjC is a different split-adjusted series and
    is never substituted when C is absent. Missing/zero closes and explicitly
    zero trading volume cannot supply a usable quote. This does not establish
    a currently tradable market, a last execution time, or a live price.

    The result contains ``quote``, both original and derived ``sources``, and
    ``limitations``. Neither input nor its ID/content/metadata is modified.
    Date precision is explicit so an exact-time consumer can return unresolved.
    """
    if price_field != "C":
        raise ValueError("Only raw J-Quants C is supported; adjusted prices must not replace actual prices")
    original = deepcopy(object_value(source, "J-Quants source"))
    validated = validate_source(original)
    metadata = validated["metadata"]
    if validated["source_type"] != "market_data" or metadata.get("provider") != "jquants" or metadata.get("dataset") != "equities/bars/daily":
        raise ValueError("Expected a normalized J-Quants V2 daily-bar market-data source")
    try:
        raw = object_value(json.loads(validated["content"], object_pairs_hook=_unique_object), "J-Quants raw bar")
    except json.JSONDecodeError as error:
        raise ValueError("J-Quants source content must contain the raw JSON bar") from error
    code = normalize_security_code(raw.get("Code"))
    if validated["company_id"] != f"jp:{code}":
        raise ValueError("J-Quants raw Code differs from the saved source company")
    master = object_value(metadata.get("company_master"), "J-Quants company master")
    if normalize_security_code(master.get("Code")) != code:
        raise ValueError("J-Quants company master differs from the saved raw bar")
    for record in (metadata, raw, master):
        for key in ("currency", "Currency"):
            if key in record and record[key] != "JPY":
                raise ValueError("J-Quants domestic-stock quotes must be denominated in JPY")
    trading_date = _trading_date(raw.get("Date"))
    if metadata.get("trading_date") != trading_date:
        raise ValueError("J-Quants raw Date differs from saved trading_date metadata")
    retrieved = timestamp(validated["retrieved_at"])
    if day(trading_date) > retrieved.astimezone(JST).date():
        raise ValueError("J-Quants trading date cannot be later than source retrieval in JST")
    price = _number(raw.get(price_field), "J-Quants C")
    if price <= 0:
        raise ValueError("J-Quants C must be positive; missing or zero is not a usable actual price")
    if raw.get("Vo") is not None and _number(raw["Vo"], "J-Quants Vo") <= 0:
        raise ValueError("J-Quants daily bar has no positive trading volume")
    observed_at = datetime.combine(day(trading_date), time.min, JST).isoformat()
    content = {
        "company_id": validated["company_id"], "currency": "JPY",
        "price_jpy": str(price), "observed_at": observed_at,
        "observation_precision": "day", "observation_basis": "date_lower_bound",
        "original_source_id": validated["id"], "original_trading_date": trading_date,
        "original_price_field": price_field, "raw_record": raw,
    }
    derived_metadata = {
        "provider": "jquants", "dataset": "equities/bars/daily/decision-quote",
        "normalization_version": 1, "original_source_id": validated["id"],
        "original_trading_date": trading_date, "original_price_field": price_field,
        "observation_precision": "day", "observation_basis": "date_lower_bound",
        "publication_time_known": False, "currency": "JPY",
    }
    if "synthetic" in metadata:
        derived_metadata["synthetic"] = deepcopy(metadata["synthetic"])
    encoded = canonical_json(content)
    derived_id = stable_source_id("jquants-quote", company_id=validated["company_id"],
                                 url=validated["url"], content=encoded, metadata=derived_metadata)
    derived = {
        "id": derived_id, "company_id": validated["company_id"],
        "title": f"{validated['title']} — derived daily quote (date lower bound)",
        "url": validated["url"], "source_type": "market_data", "published_at": None,
        "retrieved_at": validated["retrieved_at"], "content": encoded,
        "requires_research": False, "metadata": derived_metadata,
    }
    quote = {
        "company_id": validated["company_id"], "source_id": derived_id,
        "price_jpy": str(price), "currency": "JPY", "observed_at": observed_at,
        "retrieved_at": validated["retrieved_at"], "price_path": ["content", "price_jpy"],
        "observed_at_path": ["content", "observed_at"],
        "observation_precision": "day", "observation_basis": "date_lower_bound",
        "trading_date": trading_date,
    }
    return {
        "quote": quote, "sources": [original, derived],
        "limitations": [
            "Exact observation time is unknown; observed_at is the JST trading-date lower bound, not the execution or closing time.",
            "Freshness measured from the date lower bound is conservative; this is not a live quote or proof of current tradability.",
        ],
    }
