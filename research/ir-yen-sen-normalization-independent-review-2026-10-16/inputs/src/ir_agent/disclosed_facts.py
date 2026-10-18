"""Preserve cited disclosure tokens and explicit units as structured data.

This is project data shaping, not a financial author's indicator formula or an
automatic forecast. Exact text and arithmetic checks do not establish the
meaning of a period, table column, entity, ratio, or valuation parameter.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from decimal import Context, Decimal, DecimalException, DivisionByZero, InvalidOperation, Overflow, ROUND_HALF_UP, Underflow, localcontext
import hashlib
import re

from .adapters.common import canonical_json, stable_source_id
from .models import available, object_value, parse_json, text, timestamp, validate_source

_KINDS = {"reported_fact", "issuer_guidance", "external_estimate", "general_explanation"}
_REQUIRED = {"id", "concept", "kind", "raw_value", "raw_unit_label", "unit", "raw_period_label",
             "period", "basis_quote", "definition", "scope"}
_OPTIONAL = {"location", "company_id", "source_id", "raw_value_format"}
_NUMERIC = re.compile(r"[+\-△▲]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?\Z")
_TOKEN_NEIGHBOR = r"0-9A-Za-z_.,+\-△▲"
_YEN_SEN = re.compile(r"(?P<sign>[+\-△▲]?)(?P<yen>[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)"
                      r"[ \t\u3000]*円[ \t\u3000]*(?P<sen>[0-9]{1,2})[ \t\u3000]*銭\Z")
_DISPLAY_SIGNS = "−－﹣＋﹢‐‑‒–—―"
_MISSING_MARKERS = {"-", "－", "—", "–", "―"}
_UNIT_MULTIPLIERS = {
    ("JPY", "JPY"): "1", ("円", "JPY"): "1",
    ("千円", "JPY"): "1000", ("百万円", "JPY"): "1000000",
    ("億円", "JPY"): "100000000",
    ("JPY-per-share", "JPY-per-share"): "1", ("JPY/share", "JPY-per-share"): "1",
    ("円/株", "JPY-per-share"): "1", ("円／株", "JPY-per-share"): "1",
    ("円", "JPY-per-share"): "1",
    ("%", "ratio"): "0.01", ("％", "ratio"): "0.01", ("percent", "ratio"): "0.01",
    ("ratio", "ratio"): "1",
    ("shares", "shares"): "1", ("株", "shares"): "1",
    ("千株", "shares"): "1000", ("万株", "shares"): "10000",
    ("百万株", "shares"): "1000000",
}


def _json_descriptor(value, label):
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{label} must be a nonempty descriptor object")
    # Strictly JSON-compatible descriptors are assertions to preserve, not dates
    # or periods to infer. E.g. a fiscal-year-end month need not imply start/end.
    canonical_json(value)
    return deepcopy(value)


def _token_in_quote(token: str, quote: str) -> bool:
    # Avoid confirming 8 from 18/8.0/8e3, or a dash from an ISO date. This does
    # not identify the correct table column; that remains a semantic review.
    pattern = rf"(?<![{_TOKEN_NEIGHBOR}]){re.escape(token)}(?![{_TOKEN_NEIGHBOR}])"
    return re.search(pattern, quote) is not None


def _normalize_token(raw_value, quote, multiplier):
    if raw_value is None:
        return None, "missing_value", False
    if not isinstance(raw_value, str):
        raise ValueError("fact.raw_value must preserve a string token or null")
    if not raw_value.strip():
        return None, "empty_value", False
    if not _token_in_quote(raw_value, quote):
        raise ValueError("fact.raw_value token is absent from its quote or is only part of a larger numeric token")
    if raw_value in _MISSING_MARKERS:
        return None, "unconfirmed_dash", False
    if not _NUMERIC.fullmatch(raw_value):
        raise ValueError("fact.raw_value must be a strict numeric token with ordinary three-digit comma grouping")
    normalized = raw_value.replace(",", "")
    if normalized.startswith(("△", "▲")):
        normalized = "-" + normalized[1:]
    number = Decimal(normalized)
    context = Context(prec=max(80, len(number.as_tuple().digits) + 20), rounding=ROUND_HALF_UP,
                      Emin=-999999, Emax=999999, flags=[],
                      traps=[InvalidOperation, DivisionByZero, Overflow, Underflow])
    try:
        with localcontext(context):
            value = number * Decimal(multiplier)
            return "0" if value == 0 else format(value, "f"), "numeric_token_normalized", True
    except DecimalException as error:
        raise ValueError("Disclosed value exceeds the supported normalization range") from error


def _display_in_quote(display: str, quote: str) -> bool:
    # Preserve legacy token boundaries and reject slicing a positive display
    # out of Unicode signed/digit-prefixed or duplicated-unit displays.
    def neighbor(char):
        return char.isdecimal() or char in _DISPLAY_SIGNS + "円銭" or re.fullmatch(rf"[{_TOKEN_NEIGHBOR}]", char)

    return any((match.start() == 0 or not neighbor(quote[match.start() - 1]))
               and (match.end() == len(quote) or not neighbor(quote[match.end()]))
               for match in re.finditer(re.escape(display), quote))


def _normalize_yen_sen(raw_value, quote, unit):
    normalization = {"status": "missing_value", "raw_numeric_token_verified": False,
                     "raw_display_verified": False, "format": "jpy_yen_sen", "canonical_unit": unit,
                     "exact_quote_and_label_presence_verified": True, "components": None,
                     "component_span_basis": "Half-open Unicode character offsets within raw_value"}
    if raw_value is None:
        return None, normalization
    if not isinstance(raw_value, str):
        raise ValueError("fact.raw_value must preserve a string display or null")
    if not raw_value.strip(" \t\u3000"):
        normalization["status"] = "empty_value"
        return None, normalization
    if not _display_in_quote(raw_value, quote):
        raise ValueError("fact.raw_value display is absent from its quote or is only part of a larger token")
    if raw_value in _MISSING_MARKERS:
        normalization["status"] = "unconfirmed_dash"
        return None, normalization
    match = _YEN_SEN.fullmatch(raw_value)
    if match is None:
        raise ValueError("fact.raw_value must be a strict single-line yen/sen display")
    yen = match["yen"].replace(",", "")
    sign = "-1" if match["sign"] in ("-", "△", "▲") else "1"
    context = Context(prec=max(80, len(yen) + 20), rounding=ROUND_HALF_UP,
                      Emin=-999999, Emax=999999, flags=[],
                      traps=[InvalidOperation, DivisionByZero, Overflow, Underflow])
    try:
        with localcontext(context):
            value = (Decimal(yen) + Decimal(match["sen"]) * Decimal("0.01")) * Decimal(sign)
            rendered = "0" if value == 0 else format(value, "f")
    except DecimalException as error:
        raise ValueError("Disclosed value exceeds the supported normalization range") from error
    normalization.update(status="composite_display_normalized", raw_display_verified=True,
                         components={
                             "sign": {"raw_token": match["sign"], "multiplier": sign,
                                      "raw_value_span": list(match.span("sign"))},
                             "yen": {"raw_token": match["yen"], "raw_unit": "円", "unit_multiplier_to_JPY": "1",
                                     "raw_value_span": list(match.span("yen"))},
                             "sen": {"raw_token": match["sen"], "raw_unit": "銭", "unit_multiplier_to_JPY": "0.01",
                                     "raw_value_span": list(match.span("sen"))},
                         })
    return rendered, normalization


def normalize_disclosed_facts(request: dict, *, now: datetime | str) -> dict:
    """Return an immutable original and a separately identified cited extraction.

    Original availability must precede the attributed review and trusted ``now``.
    The derived source first becomes retrieved at ``now``. That time is excluded
    from its identity/content/metadata so repeat import may retain first retrieval.

    Supported canonical units are JPY, JPY-per-share, ratio and shares. Raw-label
    mappings are explicit, including percent→ratio. A capital ratio normalized
    from 8% is not thereby a cost-of-equity estimate or a validated DDM input.
    No future DPS, growth, probability, target price or thesis is generated.
    """
    request = deepcopy(object_value(request, "disclosed facts request"))
    if set(request) - {"source", "review", "facts", "company_id"}:
        raise ValueError("Unknown disclosed facts request field")
    if isinstance(now, datetime):
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be an offset-aware trusted time")
        current = timestamp(now.isoformat(), "now")
    else:
        current = timestamp(now, "now")
    original = deepcopy(object_value(request.get("source"), "source snapshot"))
    checked = validate_source(original)
    if checked["source_type"] != "public_disclosure":
        raise ValueError("Disclosed facts require a saved public-disclosure source")
    if request.get("company_id") not in (None, checked["company_id"]):
        raise ValueError("Request and source must belong to the same company")
    if not available(checked, current):
        raise ValueError("Source snapshot is from the future or unavailable at now")
    review = deepcopy(object_value(request.get("review"), "fact extraction review"))
    if set(review) != {"author", "recorded_at", "rationale"}:
        raise ValueError("Review must explicitly contain author, recorded_at and rationale")
    text(review["author"], "review.author")
    text(review["rationale"], "review.rationale")
    reviewed = timestamp(review["recorded_at"], "review.recorded_at")
    if reviewed > current or not available(checked, reviewed):
        raise ValueError("Review must not be future-dated or precede source availability")
    facts = request.get("facts")
    if not isinstance(facts, list) or not facts:
        raise ValueError("facts must be a nonempty list")
    normalized, identifiers = [], set()
    normalization_version = 1
    for item in facts:
        fact = deepcopy(object_value(item, "disclosed fact"))
        if not _REQUIRED <= set(fact) or set(fact) - _REQUIRED - _OPTIONAL:
            raise ValueError("Disclosed fact has missing or unknown fields")
        identifier = text(fact["id"], "fact.id")
        if identifier in identifiers:
            raise ValueError("Duplicate disclosed fact ID")
        identifiers.add(identifier)
        text(fact["concept"], "fact.concept")
        if not isinstance(fact["kind"], str) or fact["kind"] not in _KINDS:
            raise ValueError("fact.kind must be reported_fact, issuer_guidance, external_estimate or general_explanation")
        if fact.get("company_id") not in (None, checked["company_id"]):
            raise ValueError("Fact and source must belong to the same company")
        if fact.get("source_id") not in (None, checked["id"]):
            raise ValueError("Fact must cite the supplied original source")
        quote = text(fact["basis_quote"], "fact.basis_quote")
        if quote not in checked["content"]:
            raise ValueError("fact.basis_quote is absent from the saved original content")
        raw_unit = text(fact["raw_unit_label"], "fact.raw_unit_label")
        raw_period = text(fact["raw_period_label"], "fact.raw_period_label")
        if raw_unit not in quote or raw_period not in quote:
            raise ValueError("Raw unit and period labels must both appear verbatim in the same basis quote")
        unit = text(fact["unit"], "fact.unit")
        composite = "raw_value_format" in fact
        if composite:
            if not isinstance(fact["raw_value_format"], str) or fact["raw_value_format"] != "jpy_yen_sen":
                raise ValueError("Unsupported fact.raw_value_format")
            if raw_unit != "円" or unit not in ("JPY", "JPY-per-share"):
                raise ValueError("Unsupported explicit yen/sen raw-unit/canonical-unit mapping")
            normalization_version = 2
        multiplier = _UNIT_MULTIPLIERS.get((raw_unit, unit))
        if multiplier is None:
            raise ValueError("Unsupported explicit raw-unit/canonical-unit mapping")
        _json_descriptor(fact["period"], "fact.period")
        text(fact["definition"], "fact.definition")
        scope = fact["scope"]
        if isinstance(scope, str):
            text(scope, "fact.scope")
        else:
            _json_descriptor(scope, "fact.scope")
            if scope.get("company_id") not in (None, checked["company_id"]):
                raise ValueError("Fact scope and source must belong to the same company")
        if "location" in fact:
            location = _json_descriptor(fact["location"], "fact.location")
            if "pdf_page" in location:
                page = location["pdf_page"]
                pages = checked["content"].split("\f")
                if type(page) is not int or page < 1 or page > len(pages) or quote not in pages[page-1]:
                    raise ValueError("Fact quote does not appear on the declared saved PDF page")
        if composite:
            value, normalization = _normalize_yen_sen(fact["raw_value"], quote, unit)
        else:
            value, status, token_verified = _normalize_token(fact["raw_value"], quote, multiplier)
            normalization = {"status": status, "raw_numeric_token_verified": token_verified,
                             "explicit_unit_multiplier": multiplier, "canonical_unit": unit,
                             "exact_quote_and_label_presence_verified": True}
        normalized.append({
            **fact, "value": value, "original_source_id": checked["id"],
            "normalization": normalization,
            "financial_inputs_verified": False, "meaning_review_required": True,
        })
    original_content_hash = hashlib.sha256(original["content"].encode("utf-8")).hexdigest()
    original_snapshot_hash = hashlib.sha256(canonical_json(original).encode("utf-8")).hexdigest()
    declarations = {
        "financial_inputs_verified": False, "meaning_review_required": True,
        "scope_period_definition_and_table_column_are_reviewer_assertions": True,
        "forecast_values_automatically_adopted": False,
    }
    content = canonical_json({"original_source_id": checked["id"], "original_source_content_sha256": original_content_hash,
                              "review": review, "facts": normalized, "declarations": declarations})
    metadata = {
        "provider": "project_disclosed_fact_normalization", "normalization_version": normalization_version,
        "document_kind": "cited_fact_extraction_requiring_meaning_review",
        "original_source_id": checked["id"], "original_source_content_sha256": original_content_hash,
        "original_source_snapshot_sha256": original_snapshot_hash, "review": review, **declarations,
    }
    if "synthetic" in checked["metadata"]:
        metadata["synthetic"] = deepcopy(checked["metadata"]["synthetic"])
    derived_id = stable_source_id("disclosed-facts", company_id=checked["company_id"], url=checked["url"], content=content, metadata=metadata)
    derived = {
        "id": derived_id, "company_id": checked["company_id"],
        "title": checked["title"] + " — cited fact extraction (meaning review required)",
        "url": checked["url"], "source_type": "public_disclosure", "published_at": None,
        "retrieved_at": current.isoformat(), "content": content, "requires_research": True, "metadata": metadata,
    }
    validate_source(derived)
    return {
        "schema_version": 1, "companies": [], "sources": [original, derived], "theses": [],
        "review": review,
        "limitations": [
            "Only exact quote/token/label presence and explicit unit arithmetic are checked; definition, period, table column and entity meaning remain reviewer assertions",
            "Converting a disclosed regulatory capital ratio of 8% to ratio 0.08 does not identify it as cost of equity, a discount rate, or a verified financial-model input",
            "Reported facts, issuer guidance and general explanations remain distinct; one forecast period does not create future DPS, growth, probabilities or price targets",
            "Dash, absent and empty values remain null; the absence of a raw token is not evidence of zero",
            "Derived source is first retrieved at the supplied trusted now, not backdated to original disclosure retrieval",
        ],
    }


def reproduce_disclosed_fact_source(source: dict, sources: dict[str, dict]) -> dict:
    """Re-run only the known extraction contract against its supplied original.

    The original input snapshot can gain validation defaults on ingestion. Its
    old whole-snapshot hash is therefore a separate check from the mandatory
    original content hash and deterministic token/quote/unit reproduction.
    This check never establishes the financial meaning of a fact or forecast.
    """
    source = validate_source(source)
    metadata = source['metadata']
    result = {'source_id': source['id'], 'applicable': False, 'status': 'not_applicable',
              'reason_codes': [], 'financial_inputs_verified': False, 'meaning_review_required': True}
    if metadata.get('provider') != 'project_disclosed_fact_normalization':
        return result
    result.update(applicable=True, status='needs_review',
                  original_content_sha256_status='not_checked',
                  original_snapshot_sha256_status='not_reverified', fact_kinds=[])
    if type(metadata.get('normalization_version')) is not int or metadata['normalization_version'] not in (1, 2):
        result['reason_codes'] = ['unsupported_normalization_version']
        return result
    issues = []
    try:
        content = object_value(parse_json(source['content']), 'normalized content')
        if set(content) != {'original_source_id', 'original_source_content_sha256', 'review', 'facts', 'declarations'}:
            raise ValueError('Known normalized content has missing or unknown fields')
        saved_facts = content['facts']
        if metadata['normalization_version'] == 2 and not (
                isinstance(saved_facts, list) and any(isinstance(fact, dict)
                and fact.get('raw_value_format') == 'jpy_yen_sen' for fact in saved_facts)):
            result['reason_codes'] = ['unsupported_normalization_version']
            return result
        if metadata['normalization_version'] == 1 and isinstance(saved_facts, list) and any(
                isinstance(fact, dict) and 'raw_value_format' in fact for fact in saved_facts):
            raise ValueError('Normalization version 1 cannot contain formatted displays')
        original_id = text(metadata.get('original_source_id'), 'normalized original_source_id')
        result['original_source_id'] = original_id
        if content['original_source_id'] != original_id:
            issues.append('normalized_original_source_mismatch')
        original = sources.get(original_id)
        if original is None:
            result['reason_codes'] = [*issues, 'missing_origin_source_snapshot']
            return result
        original = deepcopy(object_value(original, 'original source snapshot'))
        checked_original = validate_source(original)
        original_hash = hashlib.sha256(checked_original['content'].encode()).hexdigest()
        if (metadata.get('original_source_content_sha256') != original_hash
                or content['original_source_content_sha256'] != original_hash):
            issues.append('original_content_hash_mismatch')
            result['original_content_sha256_status'] = 'mismatch'
        else:
            result['original_content_sha256_status'] = 'matched'
        # Only invert known validation defaults. Do not guess removed metadata,
        # old collection times, or other historical input fields to fit a hash.
        candidates = [(original, 'matched_supplied_snapshot')]
        if checked_original != original:
            candidates.append((checked_original, 'matched_validated_snapshot'))
        for candidate, _ in list(candidates):
            if candidate.get('requires_research') is True:
                without_default = deepcopy(candidate); without_default.pop('requires_research')
                candidates.append((without_default, 'matched_without_validation_defaults'))
        for candidate, _ in list(candidates):
            if candidate.get('metadata') == {}:
                without_default = deepcopy(candidate); without_default.pop('metadata')
                candidates.append((without_default, 'matched_without_validation_defaults'))
        replay_original = original
        declared_snapshot_hash = metadata.get('original_source_snapshot_sha256')
        for candidate, match_status in candidates:
            if hashlib.sha256(canonical_json(candidate).encode()).hexdigest() == declared_snapshot_hash:
                result['original_snapshot_sha256_status'] = match_status
                replay_original = candidate
                break
        if not isinstance(declared_snapshot_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', declared_snapshot_hash):
            issues.append('invalid_original_snapshot_hash')
        if not isinstance(saved_facts, list) or not saved_facts:
            raise ValueError('Known normalized facts must be a nonempty list')
        declarations = []
        for saved in saved_facts:
            saved = object_value(saved, 'normalized fact')
            declarations.append({key: deepcopy(value) for key, value in saved.items() if key in _REQUIRED | _OPTIONAL})
            result['fact_kinds'].append({'id': saved.get('id'), 'kind': saved.get('kind')})
        reproduced = normalize_disclosed_facts({'source': replay_original, 'company_id': source['company_id'],
                                               'review': content['review'], 'facts': declarations},
                                              now=source['retrieved_at'])['sources'][1]
        if canonical_json(content) != reproduced['content']:
            issues.append('normalized_content_not_reproduced')
        # Snapshot commitment is evaluated separately above. All remaining
        # declarations produced by this version must still be reproducible.
        for key, expected in reproduced['metadata'].items():
            if key != 'original_source_snapshot_sha256' and canonical_json(metadata.get(key)) != canonical_json(expected):
                issues.append('normalized_metadata_not_reproduced')
                break
        for key in ('company_id', 'title', 'url', 'source_type', 'published_at', 'requires_research'):
            if source.get(key) != reproduced.get(key):
                issues.append('normalized_source_fields_not_reproduced')
                break
        if (result['original_snapshot_sha256_status'] != 'not_reverified'
                and source['id'] != reproduced['id']):
            issues.append('normalized_identity_not_reproduced')
    except (ValueError, TypeError, KeyError) as error:
        issues.append('normalized_source_not_reproducible')
        result['detail'] = str(error)
    result['reason_codes'] = list(dict.fromkeys(issues))
    if not issues:
        result['status'] = 'reproduced'
    return result
