"""Pure intermediate arithmetic for cycle-average operating margins.

Damodaran, *Ups and Downs: Valuing Cyclical and Commodity Companies* (2009),
PDF pp.14–16, describes averaging a scaled profit measure and applying it to
recent revenues. His Toyota Table 2 is consistent with equal annual-margin
weights. The fixed method, metadata, validation and unresolved adoption result
below are project adaptations, not a universal weighting rule from the author.
See docs/cyclical-normalization-spec.md for quotes, arithmetic and source gaps.

Request fields are exact, all required, and no method or missing number defaults:

* method: ``arithmetic_equal_annual_periods`` only.
* basis: {company_id, currency, amount_unit, scope, accounting_basis,
  profit_concept}. Currency is an uppercase three-letter label, not an exchange
  rate. amount_unit is units/thousands/millions/billions; no unit conversion is
  performed. profit_concept is pretax_operating_income. Each observation and
  application basis must match this declaration exactly. Source meaning is not
  verified by matching these labels.
* annual_observations: nonempty list of {id, basis, period, revenue,
  operating_income, data_kind, source_refs, selection_rationale}.
* application_revenue: {basis, period, revenue, data_kind, source_refs,
  selection_rationale}; this may refer to a period also in the annual history.
* assessment: {cycle_driver, full_cycle_rationale, comparability_rationale,
  application_rationale, source_refs, excluded_observations}. The first four
  values are nonempty prose or null, never approval flags. Excluded rows are
  {label, reason, source_refs}; no missing historical row is synthesized.

period = {kind, label, start, end}. kind must explicitly be full_fiscal_year;
start and end are each YYYY-MM-DD or null. Complete reversed ranges and known
history overlaps, duplicate IDs and duplicate period labels are rejected.
Unknown dates remain unknown. Date counts, 52/53-week conventions, and labels
do not prove that any declaration is annual or comparable. Explicit quarter or
YTD kinds are unsupported; a falsely annual-labelled source is not detected by
this arithmetic-only API and remains a semantic-review issue.

Numeric inputs are explicit finite decimal strings: revenue > 0 and signed OI.
data_kind is reported_fact / issuer_guidance / author_estimate /
synthetic_example. It records a claim, not source verification. source_refs may
be empty; each entry is {id, version, sha256, location, quote}. version and
sha256 may be null. SHA refers to the declared original document bytes, not an
automatically resolved source snapshot; no quote or content is retrieved here.

The function preserves the request and returns ratios and a same-unit applied
OI candidate under a private Decimal context. Repeating divisions may round at
the reported working precision; there is no display-percent intermediate or
money quantization. All results stay intermediate_only / adoption unresolved.
No ROC, reinvestment, financing, DCF, price, IR, probability or DB is connected.
"""
from __future__ import annotations

from decimal import (
    Context, Decimal, DecimalException, DivisionByZero, InvalidOperation,
    Overflow, ROUND_HALF_UP, Underflow, localcontext,
)
from hashlib import sha256
import json
import math
import re

from .models import day, integer, json_text
from .valuation import _number, _ratio


_METHOD = "arithmetic_equal_annual_periods"
_BASIS = {"company_id", "currency", "amount_unit", "scope", "accounting_basis", "profit_concept"}
_PERIOD = {"kind", "label", "start", "end"}
_SOURCE = {"id", "version", "sha256", "location", "quote"}
_OBSERVATION = {"id", "basis", "period", "revenue", "operating_income", "data_kind", "source_refs", "selection_rationale"}
_APPLICATION = _OBSERVATION - {"id", "operating_income"}
_ASSESSMENT = {"cycle_driver", "full_cycle_rationale", "comparability_rationale",
               "application_rationale", "source_refs", "excluded_observations"}
_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")
_DATA_KINDS = {"reported_fact", "issuer_guidance", "author_estimate", "synthetic_example"}


def _fields(value, keys, path):
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{path} must contain exactly {sorted(keys)!r}; unknown fields are rejected")
    return value


def _text(value, path):
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(path + " must be nonempty text without surrounding whitespace")


def _json_types(value, depth=0):
    if depth > 64:
        raise ValueError("Cycle-margin JSON exceeds the nesting resource limit")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("Cycle-margin JSON object keys must be strings")
            _json_types(item, depth + 1)
    elif type(value) is list:
        for item in value:
            _json_types(item, depth + 1)
    elif type(value) not in (str, int, float, bool, type(None)):
        raise ValueError("Cycle-margin requests must contain only JSON values")
    elif type(value) is float and not math.isfinite(value):
        raise ValueError("Cycle-margin JSON numbers must be finite")


def _copy_request(request):
    _json_types(request)
    try:
        encoded = json_text(request)
        if len(encoded.encode("utf-8")) > 2 * 1024 * 1024:
            raise ValueError("Cycle-margin JSON exceeds the 2 MiB resource limit")
    except (TypeError, OverflowError, UnicodeError) as error:
        raise ValueError("Cycle-margin request must be finite UTF-8 JSON") from error
    return json.loads(encoded), sha256(encoded.encode("utf-8")).hexdigest()


def _decimal(value, path, *, positive=False):
    if type(value) is not str or len(value) > 2048 or _DECIMAL.fullmatch(value) is None:
        raise ValueError(path + " must be an explicit finite decimal string; missing values are not zero")
    number = _number(value, path)
    if len(number.as_tuple().digits) > 256 or abs(number.as_tuple().exponent) > 1000:
        raise ValueError(path + " exceeds the supported decimal resource range")
    if positive and number <= 0:
        raise ValueError(path + " must be greater than zero")
    return number


def _basis(value, path):
    _fields(value, _BASIS, path)
    for key in _BASIS:
        _text(value[key], path + "." + key)
    if re.fullmatch(r"[A-Z]{3}", value["currency"]) is None:
        raise ValueError(path + ".currency must be an explicit uppercase three-letter currency label")
    if value["amount_unit"] not in {"units", "thousands", "millions", "billions"}:
        raise ValueError(path + ".amount_unit is unsupported; no implicit conversion is performed")
    if value["profit_concept"] != "pretax_operating_income":
        raise ValueError(path + ".profit_concept must be pretax_operating_income")


def _period(value, path, incomplete):
    _fields(value, _PERIOD, path)
    _text(value["kind"], path + ".kind")
    if value["kind"] != "full_fiscal_year":
        raise ValueError(path + ".kind must explicitly be full_fiscal_year; quarter/YTD periods are unsupported")
    _text(value["label"], path + ".label")
    dates = []
    for key in ("start", "end"):
        raw = value[key]
        if raw is None:
            incomplete.append(path + "." + key)
            dates.append(None)
        else:
            dates.append(day(raw, path + "." + key))
    start, end = dates
    if start is not None and end is not None and start > end:
        raise ValueError(path + " ends before it starts")
    return start, end


def _sources(value, path):
    if type(value) is not list:
        raise ValueError(path + " must be a list")
    identities = set()
    for index, source in enumerate(value):
        label = f"{path}[{index}]"
        _fields(source, _SOURCE, label)
        for key in ("id", "location", "quote"):
            _text(source[key], label + "." + key)
        if source["version"] is not None:
            integer(source["version"], label + ".version", minimum=1)
        digest = source["sha256"]
        if digest is not None and (type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None):
            raise ValueError(label + ".sha256 must be a lowercase SHA-256 or null")
        identity = (source["id"], source["version"], source["location"], source["quote"])
        if identity in identities:
            raise ValueError(path + " contains a duplicate source reference")
        identities.add(identity)


def _row(value, basis, path, incomplete, *, observation):
    _fields(value, _OBSERVATION if observation else _APPLICATION, path)
    if observation:
        _text(value["id"], path + ".id")
    _basis(value["basis"], path + ".basis")
    if value["basis"] != basis:
        raise ValueError(path + ".basis must match the request basis; mixed company/currency/unit/scope/accounting/concept is unsupported")
    dates = _period(value["period"], path + ".period", incomplete)
    _text(value["data_kind"], path + ".data_kind")
    if value["data_kind"] not in _DATA_KINDS:
        raise ValueError(path + ".data_kind is unsupported")
    _sources(value["source_refs"], path + ".source_refs")
    _text(value["selection_rationale"], path + ".selection_rationale")
    revenue = _decimal(value["revenue"], path + ".revenue", positive=True)
    income = _decimal(value["operating_income"], path + ".operating_income") if observation else None
    return revenue, income, dates


def _known_overlap(left, right):
    """Reject provable overlap only; partial unknown bounds remain unresolved."""
    left_start, left_end = left
    right_start, right_end = right
    for start, end, other in ((left_start, left_end, right), (right_start, right_end, left)):
        if start is not None and end is not None:
            if any(point is not None and start <= point <= end for point in other):
                return True
    return bool({point for point in left if point is not None}
                & {point for point in right if point is not None})


def _precision(rows, application_revenue):
    numbers = [application_revenue] + [number for revenue, income, _ in rows for number in (revenue, income)]
    digits = max(len(number.as_tuple().digits) for number in numbers)
    ratio_scales = [income.adjusted() - revenue.adjusted() for revenue, income, _ in rows if income != 0]
    span = max(ratio_scales, default=0) - min(ratio_scales, default=0)
    # Include scale/cancellation, multiplication and summation guard digits.
    # These are numeric resource/precision choices, not a financial threshold.
    return max(80, span + 3 * digits + len(str(len(rows))) + 40)


def calculate_cyclical_margin(request: dict) -> dict:
    """Calculate equal declared-annual OI/S mean × explicit same-basis revenue."""
    value, request_hash = _copy_request(request)
    _fields(value, {"method", "basis", "annual_observations", "application_revenue", "assessment"}, "cycle-margin request")
    _text(value["method"], "method")
    if value["method"] != _METHOD:
        raise ValueError("method must explicitly be arithmetic_equal_annual_periods; weighted methods are unsupported")
    _basis(value["basis"], "basis")
    annual = value["annual_observations"]
    if type(annual) is not list or not annual:
        raise ValueError("annual_observations must be a nonempty list; no historical row is inferred")
    incomplete, rows = [], []
    identifiers, labels = set(), set()
    for index, observation in enumerate(annual):
        path = f"annual_observations[{index}]"
        prepared = _row(observation, value["basis"], path, incomplete, observation=True)
        if observation["id"] in identifiers:
            raise ValueError("Duplicate annual observation ID")
        if observation["period"]["label"] in labels:
            raise ValueError("Duplicate annual period label")
        identifiers.add(observation["id"])
        labels.add(observation["period"]["label"])
        for _, _, earlier_dates in rows:
            if _known_overlap(earlier_dates, prepared[2]):
                raise ValueError("Annual history has duplicate or overlapping known periods")
        rows.append(prepared)
    application, _, _ = _row(value["application_revenue"], value["basis"], "application_revenue", incomplete, observation=False)
    assessment = _fields(value["assessment"], _ASSESSMENT, "assessment")
    missing_assessments = []
    for key in ("cycle_driver", "full_cycle_rationale", "comparability_rationale", "application_rationale"):
        if assessment[key] is None:
            missing_assessments.append("assessment." + key)
        else:
            _text(assessment[key], "assessment." + key)
    _sources(assessment["source_refs"], "assessment.source_refs")
    excluded = assessment["excluded_observations"]
    if type(excluded) is not list:
        raise ValueError("assessment.excluded_observations must be a list")
    for index, exclusion in enumerate(excluded):
        path = f"assessment.excluded_observations[{index}]"
        _fields(exclusion, {"label", "reason", "source_refs"}, path)
        _text(exclusion["label"], path + ".label")
        _text(exclusion["reason"], path + ".reason")
        _sources(exclusion["source_refs"], path + ".source_refs")
        if exclusion["label"] in labels:
            raise ValueError("An included annual period cannot also be declared excluded")

    precision = _precision(rows, application)
    context = Context(prec=precision, rounding=ROUND_HALF_UP, Emin=-999999, Emax=999999,
                      flags=[], traps=[InvalidOperation, DivisionByZero, Overflow, Underflow])
    try:
        with localcontext(context):
            margins = [income / revenue for revenue, income, _ in rows]
            mean = sum(margins, Decimal("0")) / Decimal(len(margins))
            applied_income = mean * application
            annual_results = [{"id": observation["id"], "operating_margin_ratio": _ratio(margin)}
                              for observation, margin in zip(annual, margins)]
            arithmetic = {"annual_margins": annual_results, "period_count": len(rows),
                          "mean_operating_margin_ratio": _ratio(mean),
                          "applied_operating_income": _ratio(applied_income),
                          "basis": value["basis"]}
    except DecimalException as error:
        raise ValueError("Cycle-margin arithmetic exceeds the supported decimal range") from error

    return {
        "status": "intermediate_only", "adoption": "unresolved", "request": value,
        "request_sha256": request_hash, "arithmetic": arithmetic,
        "calculation": {
            "working_precision_digits": precision, "rounding": "ROUND_HALF_UP",
            "division_may_round": True, "display_quantization": None,
            "formula": {"per_period": "operating_income / revenue",
                        "mean": "sum(annual_operating_margin_ratio) / period_count",
                        "application": "mean_operating_margin_ratio * application_revenue"},
            "author_reference": {"author": "Aswath Damodaran", "year": 2009,
                "title": "Ups and Downs: Valuing Cyclical and Commodity Companies",
                "source_id": "damodaran.cyclical-commodity.2009",
                "pdf_sha256": "16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40",
                "pdf_pages": [14, 15, 16],
                "support": "Average scaled profit margins and apply to recent revenues; Toyota's annual example is consistent with equal margin weights."},
            "project_adaptation": "Strict metadata/period checks, explicit equal declared-annual weights, isolated Decimal arithmetic and unresolved adoption are local API rules; the author did not prescribe a universal period weighting or automatic full-cycle test.",
        },
        "verification": {"source_references": "unverified", "declared_basis_semantics": "unverified",
                         "declared_annual_periods": "unverified", "fiscal_year_duration_comparability": "unverified",
                         "full_cycle_coverage": "unverified", "history_selection_and_exclusions": "unverified",
                         "application_revenue_suitability": "unverified"},
        "period_dates_incomplete": incomplete, "assessment_fields_unset": missing_assessments,
        "limitations": [
            "Matching caller metadata and carrying source/quote references do not verify the documents, annual declarations, period comparability, full-cycle coverage or applicability today; 52/53-week and changed fiscal years need separate review.",
            "Unknown bounds and unlisted/missing years are not inferred or filled; known overlaps are rejected, but unknown dates cannot prove a complete or nonoverlapping history.",
            "Signed income is retained; no loss row is removed or clamped, no displayed margin is substituted, and no sales/period weighting, annualization or currency/unit conversion is performed.",
            "The applied amount is an arithmetic candidate, not reported profit or an adopted normalized forecast; no return on capital, reinvestment, financing, valuation, price, IR action or forecast probability is calculated.",
        ],
    }
