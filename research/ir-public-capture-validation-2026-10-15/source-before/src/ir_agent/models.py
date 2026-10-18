"""Versioned JSON input contracts. Dates and source availability are explicit."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .valuation import calculate_valuation

JST = ZoneInfo("Asia/Tokyo")
ACTIONS = {"watch", "buy_review", "hold_review", "exit_review", "unresolved"}
COMPANY_STATUSES = {"active", "watch", "excluded", "special_model"}
SOURCE_TYPES = {"public_disclosure", "market_data", "ir_reply"}


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def parse_json(value: str, *, parse_float=float):
    """Read unambiguous finite JSON; callers may retain exact decimal tokens."""
    def reject_constant(value: str) -> None:
        raise ValueError(f"Non-finite JSON number: {value}")

    def unique_object(items: list[tuple]) -> dict:
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(value, parse_constant=reject_constant,
                      object_pairs_hook=unique_object, parse_float=parse_float)


def load_json(path: str | Path) -> dict:
    result = parse_json(Path(path).read_text(encoding="utf-8"))
    return object_value(result, "JSON document")


def object_value(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def strings(value: object, label: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(f"{label} must be a{' nonempty' if nonempty else ''} list")
    for item in value:
        text(item, label)
    if len(set(value)) != len(value):
        raise ValueError(f"{label} contains duplicates")
    return value


def integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def timestamp(value: object, label: str = "timestamp") -> datetime:
    parsed = datetime.fromisoformat(text(value, label).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone offset")
    try:
        return parsed.astimezone(timezone.utc)
    except OverflowError as error:
        raise ValueError(f"{label} is outside the supported UTC datetime range") from error


def day(value: object, label: str = "date") -> date:
    raw = text(value, label)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        raise ValueError(f"{label} must be YYYY-MM-DD")
    return date.fromisoformat(raw)


def cutoff(value: str) -> datetime:
    """A date means the end of that JST calendar day; a timestamp is exact."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return datetime.combine(day(value), time.max, JST).astimezone(timezone.utc)
    return timestamp(value, "as_of")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def available(source: dict, as_of: datetime) -> bool:
    if timestamp(source["retrieved_at"]) > as_of:
        return False
    return source.get("published_at") is None or timestamp(source["published_at"]) <= as_of


def source_origins(source: dict) -> list[str]:
    """Return all declared parent IDs without mutating the saved source.

    The legacy singular field and the plural field can coexist. Duplicate IDs
    inside the array are invalid; overlap between singular and plural is one
    dependency. This project data contract adds no financial inference.
    """
    source = object_value(source, "source provenance")
    metadata = object_value(source.get("metadata", {}), "source.metadata")
    parents = []
    if "original_source_id" in metadata:
        parents.append(text(metadata["original_source_id"], "metadata.original_source_id"))
    if "original_source_ids" in metadata:
        declared = strings(metadata["original_source_ids"], "metadata.original_source_ids")
        parents.extend(parent for parent in declared if parent not in parents)
    return parents


def validate_company(value: dict) -> dict:
    result = deepcopy(object_value(value, "company"))
    for key in ("id", "name"):
        text(result.get(key), f"company.{key}")
    code = result.get("security_code")
    if code is not None and (not isinstance(code, str) or not re.fullmatch(r"[0-9A-Z]{4}", code)):
        raise ValueError("company.security_code must be a four-character string")
    text(result.get("status", "watch"), "company.status")
    if result.get("status", "watch") not in COMPANY_STATUSES:
        raise ValueError("Invalid company status")
    result.setdefault("status", "watch")
    result.setdefault("held", False)
    if not isinstance(result["held"], bool):
        raise ValueError("company.held must be boolean")
    if result["status"] in {"excluded", "special_model"}:
        text(result.get("screening_reason"), "company.screening_reason")
    return result


def validate_source(value: dict) -> dict:
    result = deepcopy(object_value(value, "source"))
    for key in ("id", "company_id", "title", "url", "content"):
        text(result.get(key), f"source.{key}")
    if not re.match(r"^https?://", result["url"]):
        raise ValueError("source.url must be an HTTP(S) reference URL")
    text(result.get("source_type"), "source.source_type")
    if result.get("source_type") not in SOURCE_TYPES:
        raise ValueError("Invalid source_type")
    fetched = timestamp(result.get("retrieved_at"), "source.retrieved_at")
    if result.get("published_at") is not None:
        if timestamp(result["published_at"], "source.published_at") > fetched:
            raise ValueError("A source cannot be retrieved before its publication")
    result.setdefault("requires_research", result["source_type"] == "public_disclosure")
    if not isinstance(result["requires_research"], bool):
        raise ValueError("source.requires_research must be boolean")
    object_value(result.setdefault("metadata", {}), "source.metadata")
    return result


def validate_thesis(value: dict) -> dict:
    result = deepcopy(object_value(value, "thesis"))
    for key in ("company_id", "statement"):
        text(result.get(key), f"thesis.{key}")
    integer(result.get("version"), "thesis.version", minimum=1)
    timestamp(result.get("recorded_at"), "thesis.recorded_at")
    day(result.get("next_review_date"), "thesis.next_review_date")
    for key in ("pillars", "invalidation_conditions", "evidence_ids"):
        strings(result.get(key), f"thesis.{key}", nonempty=True)
    object_value(result.get("valuation"), "thesis.valuation")
    calculate_valuation(result["valuation"], result.get("current_price_jpy"))
    return result


def validate_question(value: dict) -> dict:
    result = deepcopy(object_value(value, "question"))
    for key in ("id", "company_id", "topic", "question", "target_parameter"):
        text(result.get(key), f"question.{key}")
    integer(result.get("thesis_version"), "question.thesis_version", minimum=1)
    timestamp(result.get("created_at"), "question.created_at")
    strings(result.get("evidence_ids"), "question.evidence_ids", nonempty=True)
    branches = result.get("branches")
    if not isinstance(branches, list) or len(branches) < 2:
        raise ValueError("question.branches needs at least two answer branches")
    seen = set()
    unresolved = False
    for branch in branches:
        object_value(branch, "answer branch")
        for key in ("id", "condition", "interpretation"):
            text(branch.get(key), f"branch.{key}")
        if branch["id"] in seen:
            raise ValueError("Duplicate answer branch id")
        seen.add(branch["id"])
        text(branch.get("action"), "branch.action")
        if branch.get("action") not in ACTIONS:
            raise ValueError("Invalid branch action")
        if branch["action"] == "unresolved":
            unresolved = True
            if "valuation" in branch:
                raise ValueError("An unresolved branch must preserve the existing valuation")
        if "valuation" in branch:
            calculate_valuation(branch["valuation"], "1")
    if not unresolved:
        raise ValueError("Include an unresolved answer branch")
    priority = integer(result.setdefault("priority", 50), "question.priority")
    if priority > 100:
        raise ValueError("question.priority must be <= 100")
    return result


def validate_reply(value: dict) -> dict:
    result = deepcopy(object_value(value, "reply"))
    for key in ("id", "question_id", "raw_text"):
        text(result.get(key), f"reply.{key}")
    timestamp(result.get("received_at"), "reply.received_at")
    status = result.setdefault("information_status", "unclear")
    text(status, "reply.information_status")
    if status not in {"public_clarification", "unclear", "potential_nonpublic"}:
        raise ValueError("Invalid reply.information_status")
    return result


def validate_result(value: dict) -> dict:
    result = deepcopy(object_value(value, "research result"))
    text(result.get("summary"), "result.summary")
    strings(result.get("evidence_ids"), "result.evidence_ids", nonempty=True)
    strings(result.get("counterarguments"), "result.counterarguments", nonempty=True)
    text(result.get("proposed_action"), "result.proposed_action")
    if result.get("proposed_action") not in ACTIONS:
        raise ValueError("Invalid result.proposed_action")
    result["thesis_update"] = validate_thesis(result.get("thesis_update"))
    return result
