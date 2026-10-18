"""Pure stable-period reinvestment/FCFF arithmetic; no forecast preparation.

Damodaran, *Ups and Downs: Valuing Cyclical and Commodity Companies* (2009),
PDF pp.17 and 21, uses stable reinvestment rate = g / ROC and a next-period
after-tax operating profit times (1 - g/ROC) in the valuation numerator. This
module only decomposes that numerator. The request/metadata contract, positive
author-example scope and unresolved adoption are project adaptations; see
docs/cyclical-reinvestment-spec.md. No financial default is supplied.

Request keys are exactly method, basis, nopat_next, growth, roc_new, assessment.
method is stable_growth_new_investment_roc. basis has company_id, currency,
amount_unit, scope, accounting_basis; currency is an uppercase 3-letter label,
amount_unit is units/thousands/millions/billions. No conversion is performed.

nopat_next has value, concept, timing, period, basis, data_kind, source_refs,
rationale. concept is aftertax_operating_income_before_financing and timing is
next_stable_period. growth/roc_new each have value, concept, unit, period,
basis, data_kind, source_refs, rationale. Their concepts are respectively
stable_operating_income_growth and aftertax_return_on_new_investment; unit is
annual_decimal_ratio. All three basis declarations match the request basis,
and their periods match each other. period = {kind, label, start, end}, with
kind full_fiscal_year and YYYY-MM-DD or null for each bound. Annual/stable/next
declarations and 52/53-week comparability remain unverified; dates are not
inferred and no day-count threshold certifies annual applicability.

Values are explicit finite decimal strings: positive NOPAT and ROC, and
nonnegative growth. Explicit zero growth extends only the algebraic domain;
the cited positive author examples do not establish its economic applicability.
ROC=0 remains undefined, including 0/0. Negative/zero NOPAT and negative
rates remain out of scope, not company exclusion rules. r>1 and negative
FCFF are retained; no cap, funding guarantee or valuation is added.

data_kind is reported_fact/issuer_guidance/author_estimate/explicit_assumption/
synthetic_example, a caller declaration only. source_refs is a list (possibly
empty) of {id, version, sha256, location, quote}; version/SHA may be null. SHA
declares original document bytes; no source or quote is resolved here.
assessment = {tax_and_nol_rationale, stable_growth_rationale,
new_investment_roc_rationale, comparability_rationale, source_refs}; the first
four are nonempty prose or null. No approval flags are accepted.

Only r=g/ROC_new, R=NOPAT_next*r, FCFF=NOPAT_next-R are calculated, under an
isolated Decimal context. No tax/NOL, (1+g), historical ROC, accounting-component
reinvestment, financing, DCF, price, IR, DB or probability step is performed.
The function returns a copied request, declared references and arithmetic, with
status intermediate_only / adoption unresolved / all verification unverified.
"""
from __future__ import annotations

from decimal import (
    Context, DecimalException, DivisionByZero, InvalidOperation, Overflow,
    ROUND_HALF_UP, Underflow, localcontext,
)
from hashlib import sha256
import json
import math
import re

from .models import day, integer, json_text
from .valuation import _number, _ratio


_BASIS = {"company_id", "currency", "amount_unit", "scope", "accounting_basis"}
_DESCRIPTOR = {"value", "concept", "period", "basis", "data_kind", "source_refs", "rationale"}
_ASSESSMENT = {"tax_and_nol_rationale", "stable_growth_rationale",
               "new_investment_roc_rationale", "comparability_rationale", "source_refs"}
_KINDS = {"reported_fact", "issuer_guidance", "author_estimate", "explicit_assumption", "synthetic_example"}
_NUMERIC = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


def _fields(value, keys, path):
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{path} must contain exactly {sorted(keys)!r}; unknown fields are rejected")


def _text(value, path):
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(path + " must be nonempty text without surrounding whitespace")


def _json_types(value, depth=0):
    if depth > 64:
        raise ValueError("Stable-reinvestment JSON exceeds the nesting resource limit")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("Stable-reinvestment JSON keys must be strings")
            _json_types(item, depth + 1)
    elif type(value) is list:
        for item in value:
            _json_types(item, depth + 1)
    elif type(value) not in (str, int, float, bool, type(None)):
        raise ValueError("Stable-reinvestment requests must contain only JSON values")
    elif type(value) is float and not math.isfinite(value):
        raise ValueError("Stable-reinvestment JSON numbers must be finite")


def _copy_request(request):
    _json_types(request)
    try:
        encoded = json_text(request)
        raw = encoded.encode("utf-8")
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Stable-reinvestment JSON exceeds the 2 MiB resource limit")
    except (TypeError, OverflowError, UnicodeError) as error:
        raise ValueError("Stable-reinvestment request must be finite UTF-8 JSON") from error
    return json.loads(encoded), sha256(raw).hexdigest()


def _decimal(value, path):
    if type(value) is not str or len(value) > 2048 or _NUMERIC.fullmatch(value) is None:
        raise ValueError(path + " must be an explicit finite decimal string; missing values are not zero")
    number = _number(value, path)
    if len(number.as_tuple().digits) > 256 or abs(number.as_tuple().exponent) > 1000:
        raise ValueError(path + " exceeds the supported decimal resource range")
    return number


def _basis(value, path):
    _fields(value, _BASIS, path)
    for key in _BASIS:
        _text(value[key], path + "." + key)
    if re.fullmatch(r"[A-Z]{3}", value["currency"]) is None:
        raise ValueError(path + ".currency must be an uppercase three-letter currency label")
    if value["amount_unit"] not in {"units", "thousands", "millions", "billions"}:
        raise ValueError(path + ".amount_unit is unsupported; no unit conversion is performed")


def _sources(value, path):
    if type(value) is not list:
        raise ValueError(path + " must be a list")
    identities = set()
    for index, source in enumerate(value):
        label = f"{path}[{index}]"
        _fields(source, {"id", "version", "sha256", "location", "quote"}, label)
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


def _period(value, path, incomplete):
    _fields(value, {"kind", "label", "start", "end"}, path)
    _text(value["kind"], path + ".kind")
    if value["kind"] != "full_fiscal_year":
        raise ValueError(path + ".kind must declare full_fiscal_year; quarter/YTD periods are unsupported")
    _text(value["label"], path + ".label")
    dates = []
    for key in ("start", "end"):
        if value[key] is None:
            incomplete.append(path + "." + key)
            dates.append(None)
        else:
            dates.append(day(value[key], path + "." + key))
    if all(date is not None for date in dates) and dates[0] > dates[1]:
        raise ValueError(path + " ends before it starts")


def _descriptor(value, basis, path, concept, incomplete, *, nopat=False):
    _fields(value, _DESCRIPTOR | ({"timing"} if nopat else {"unit"}), path)
    _text(value["concept"], path + ".concept")
    if value["concept"] != concept:
        raise ValueError(path + ".concept must be " + concept + "; no profit/rate conversion is performed")
    qualifier = "timing" if nopat else "unit"
    expected = "next_stable_period" if nopat else "annual_decimal_ratio"
    _text(value[qualifier], path + "." + qualifier)
    if value[qualifier] != expected:
        raise ValueError(path + "." + qualifier + " must explicitly be " + expected)
    _basis(value["basis"], path + ".basis")
    if value["basis"] != basis:
        raise ValueError(path + ".basis must exactly match the request company/currency/unit/scope/accounting basis")
    _period(value["period"], path + ".period", incomplete)
    _text(value["data_kind"], path + ".data_kind")
    if value["data_kind"] not in _KINDS:
        raise ValueError(path + ".data_kind is unsupported")
    _sources(value["source_refs"], path + ".source_refs")
    _text(value["rationale"], path + ".rationale")
    return _decimal(value["value"], path + ".value")


def calculate_stable_reinvestment(request: dict) -> dict:
    """Decompose explicit next-stable-period NOPAT; never prepare its forecast."""
    value, digest = _copy_request(request)
    _fields(value, {"method", "basis", "nopat_next", "growth", "roc_new", "assessment"}, "stable reinvestment request")
    _text(value["method"], "method")
    if value["method"] != "stable_growth_new_investment_roc":
        raise ValueError("method must explicitly be stable_growth_new_investment_roc")
    _basis(value["basis"], "basis")
    incomplete = []
    nopat = _descriptor(value["nopat_next"], value["basis"], "nopat_next",
                        "aftertax_operating_income_before_financing", incomplete, nopat=True)
    growth = _descriptor(value["growth"], value["basis"], "growth", "stable_operating_income_growth", incomplete)
    roc = _descriptor(value["roc_new"], value["basis"], "roc_new", "aftertax_return_on_new_investment", incomplete)
    if value["growth"]["period"] != value["nopat_next"]["period"] or value["roc_new"]["period"] != value["nopat_next"]["period"]:
        raise ValueError("NOPAT_next, growth and ROC_new must declare exactly the same next stable annual period")
    if roc == 0:
        raise ValueError("ROC_new=0 is an undefined denominator; no substitute is supplied")
    if roc < 0 or nopat <= 0:
        raise ValueError("Nonpositive NOPAT or negative ROC_new is outside the initial positive author-example scope")
    if growth < 0:
        raise ValueError("Negative growth is outside the initial positive author-example scope")
    assessment = value["assessment"]
    _fields(assessment, _ASSESSMENT, "assessment")
    unset = []
    for key in sorted(_ASSESSMENT - {"source_refs"}):
        if assessment[key] is None:
            unset.append("assessment." + key)
        else:
            _text(assessment[key], "assessment." + key)
    _sources(assessment["source_refs"], "assessment.source_refs")

    digits = sum(len(number.as_tuple().digits) for number in (nopat, growth, roc))
    precision = max(80, digits + abs(growth.adjusted() - roc.adjusted()) + 40)
    context = Context(prec=precision, rounding=ROUND_HALF_UP, Emin=-999999, Emax=999999,
                      flags=[], traps=[InvalidOperation, DivisionByZero, Overflow, Underflow])
    try:
        with localcontext(context):
            rate = growth / roc
            reinvestment = nopat * rate
            fcff = nopat - reinvestment
            arithmetic = {"reinvestment_rate": _ratio(rate), "reinvestment_amount": _ratio(reinvestment),
                          "fcff": _ratio(fcff), "basis": dict(value["basis"])}
    except DecimalException as error:
        raise ValueError("Stable-reinvestment arithmetic exceeds the supported decimal range") from error
    result = {
        "status": "intermediate_only", "adoption": "unresolved", "request": value,
        "request_sha256": digest, "arithmetic": arithmetic,
        "calculation": {
            "working_precision_digits": precision, "rounding": "ROUND_HALF_UP",
            "division_may_round": True, "display_quantization": None,
            "formula": {"reinvestment_rate": "growth / roc_new",
                        "reinvestment_amount": "nopat_next * reinvestment_rate",
                        "fcff": "nopat_next - reinvestment_amount"},
            "author_reference": {"author": "Aswath Damodaran", "year": 2009,
                "title": "Ups and Downs: Valuing Cyclical and Commodity Companies",
                "source_id": "damodaran.cyclical-commodity.2009",
                "pdf_sha256": "16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40",
                "pdf_pages": [17, 21],
                "support": "Stable reinvestment rate g/ROC and the next-period after-tax operating-income valuation numerator; this function decomposes that numerator only."},
            "project_adaptation": "Strict next-stable-period metadata, positive author-example scope, isolated Decimal arithmetic and unresolved adoption are local API rules, not a universal author policy or verified forecast.",
        },
        "verification": {"source_references": "unverified", "declared_basis_semantics": "unverified",
                         "next_annual_period_and_comparability": "unverified", "tax_and_nol_treatment": "unverified",
                         "stable_growth_applicability": "unverified", "new_investment_roc_applicability": "unverified",
                         "funding_and_survival": "unverified"},
        "period_dates_incomplete": incomplete, "assessment_fields_unset": unset,
        "limitations": [
            "Input labels, period equality and source/quote references are caller declarations, not independently verified documents, tax treatment, annual/52/53-week comparability, next-period timing or economic applicability.",
            "NOPAT_next is supplied as after-tax operating income before financing; no tax/NOL calculation, (1+g) multiplication, historical ROC selection, WACC substitution or pretax-profit conversion is performed.",
            "Only the positive author-example scope is implemented; zero growth has a defined algebraic value with nonzero ROC but is unsupported here, distinct from the ROC=0 denominator error.",
            "Reinvestment rates above one and negative FCFF are retained without clamping; capital funding, growth sustainability and survival remain unverified.",
            "No capex/D&A/working-capital parts, financing cash flows, DCF, terminal value, stock price, IR action or probability is generated, and intermediate arithmetic does not adopt a normalized forecast.",
        ],
    }
    if growth == 0:
        result["calculation"]["project_adaptation"] = (
            "Explicit zero growth with positive NOPAT and positive ROC extends only the algebraic domain of g/ROC; "
            "the cited positive author examples do not establish zero-growth economic applicability. "
            "Strict metadata, isolated Decimal arithmetic and unresolved adoption remain local API rules."
        )
        result["limitations"][2] = (
            "Explicit zero growth gives reinvestment rate and modeled reinvestment amount zero, and FCFF equal to "
            "the supplied next-period NOPAT. This does not establish zero gross capex or maintenance spending, "
            "a normalized forecast, or economic applicability; ROC=0 remains an undefined denominator."
        )
    return result
