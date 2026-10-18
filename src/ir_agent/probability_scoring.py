"""Score one explicit categorical forecast; no fitting or observation validation.

Gneiting & Raftery (2007), JASA 102(477), pp.359–378, Example 1 and
Example 3 on p.363: https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf
The author's rewards are negated here to obtain losses (lower is better).
Preserved original, quotations and adoption limits are in
research/probabilistic-evaluation-2026-10-15/.

References are caller declarations, not proof that a forecast was saved before
an eligible observation. Properness is an expected-score property; this pure
calculation does not establish calibration, independence or investment value.
"""

from __future__ import annotations

from decimal import (
    Context, Decimal, DecimalException, DivisionByZero, InvalidOperation,
    Overflow, ROUND_HALF_EVEN, localcontext,
)
import re
from typing import Any


_MAX_CATEGORIES = 1000
_MAX_NUMBER_CHARS = 2048
_MAX_COEFFICIENT_DIGITS = 256
_MAX_ABS_EXPONENT = 1000
_MAX_PRECISION = 4096
_LOG_PRECISION = 80
_NUMERIC = re.compile(r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")
_KEYS = {
    "categories", "probabilities", "observed_category", "prediction_ref",
    "observation_ref", "definition_ref",
}


def _context(precision: int) -> Context:
    # Construct a complete context instead of inheriting caller rounding,
    # exponent bounds, traps or flags. ln is rounded to this private precision.
    return Context(prec=precision, rounding=ROUND_HALF_EVEN,
                   Emin=-999999, Emax=999999, capitals=1, clamp=0,
                   flags=[], traps=[InvalidOperation, DivisionByZero, Overflow])


def _label(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{path} must be a non-empty string without surrounding whitespace")
    return value


def _probability(value: Any, path: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError(f"{path} must be a finite decimal number or numeric string")
    try:
        text = str(value)
        if len(text) > _MAX_NUMBER_CHARS or not _NUMERIC.fullmatch(text):
            raise ValueError(f"{path} must be a bounded decimal numeric token")
        number = Decimal(text)
    except (DecimalException, OverflowError, ValueError) as exc:
        raise ValueError(f"{path} must be a bounded finite decimal numeric token") from exc
    if not number.is_finite():
        raise ValueError(f"{path} must be finite")
    parts = number.as_tuple()
    if len(parts.digits) > _MAX_COEFFICIENT_DIGITS or abs(parts.exponent) > _MAX_ABS_EXPONENT:
        raise ValueError(f"{path} exceeds decimal resource limits")
    if not Decimal(0) <= number <= Decimal(1):
        raise ValueError(f"{path} must be between 0 and 1")
    return number


def _decimal_string(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def score_categorical_forecast(request: dict) -> dict:
    """Return strict-JSON-safe losses for one fully specified prediction.

    Exact request keys: categories, probabilities, observed_category and three
    non-empty string references: prediction_ref, observation_ref, definition_ref.
    Probability keys must match the unique categories exactly and sum exactly
    to one as decimals; no tolerance, normalization, missing-value filling or
    clipping is applied. Decimal strings are recommended; floats use str(float).

    The Brier loss is the full categorical squared-error sum, including both
    components in a binary forecast. Log loss uses natural logarithms in an
    isolated 80-significant-digit context. A zero observed probability yields
    positive_infinity with value=None, never a finite sentinel or JSON Infinity.
    Resource bounds reject excessive inputs rather than rounding their values.
    """
    with localcontext(_context(_LOG_PRECISION)):
        return _score(request)


def _score(request: Any) -> dict:
    if not isinstance(request, dict) or set(request) != _KEYS:
        raise ValueError("request must contain exactly categories, probabilities, observed_category, prediction_ref, observation_ref, definition_ref")
    categories = request["categories"]
    if not isinstance(categories, list) or not 1 <= len(categories) <= _MAX_CATEGORIES:
        raise ValueError(f"categories must be a non-empty list with at most {_MAX_CATEGORIES} entries")
    labels = [_label(label, f"categories[{i}]") for i, label in enumerate(categories)]
    if len(set(labels)) != len(labels):
        raise ValueError("categories must be unique")
    probabilities = request["probabilities"]
    if not isinstance(probabilities, dict) or set(probabilities) != set(labels):
        raise ValueError("probabilities must be an object with exactly the category keys")
    observed = _label(request["observed_category"], "observed_category")
    if observed not in labels:
        raise ValueError("observed_category must be one of the categories")
    references = {key: _label(request[key], key) for key in
                  ("prediction_ref", "observation_ref", "definition_ref")}
    values = {label: _probability(probabilities[label], f"probabilities[{label!r}]")
              for label in labels}
    scale = max(max(0, -value.as_tuple().exponent) for value in values.values())
    # Each squared error has at most 2*scale fractional places and at most one
    # integer digit. The count guard is conservative and ensures exact sums.
    exact_precision = max(_LOG_PRECISION, 2 * scale + len(str(len(labels))) + 4)
    if exact_precision > _MAX_PRECISION:
        raise ValueError("required decimal precision exceeds the resource limit")
    with localcontext(_context(exact_precision)):
        if sum(values.values(), Decimal(0)) != Decimal(1):
            raise ValueError("probabilities must sum exactly to 1")
        brier = sum(((value - (Decimal(1) if label == observed else Decimal(0))) ** 2
                     for label, value in values.items()), Decimal(0))
    observed_probability = values[observed]
    if observed_probability == 0:
        log = {"status": "positive_infinity", "value": None, "unit": "nats"}
    else:
        # Decimal.ln is correctly rounded (ROUND_HALF_EVEN), not an exact
        # algebraic result except at p=1. No binary floating point is involved.
        with localcontext(_context(_LOG_PRECISION)):
            log = {"status": "finite", "value": _decimal_string(-observed_probability.ln()),
                   "unit": "nats"}
    return {
        "schema_version": 1,
        "status": "calculation_only",
        **references,
        "categories": list(labels),
        "probabilities": {label: _decimal_string(value) for label, value in values.items()},
        "observed_category": observed,
        "brier_loss": {"status": "finite", "value": _decimal_string(brier),
                       "convention": "multiclass_sum_squared_error"},
        "log_loss": log,
        "arithmetic": {"brier": "exact_decimal", "logarithm": "decimal_ln",
                       "log_precision_digits": _LOG_PRECISION, "log_rounding": "ROUND_HALF_EVEN"},
        "verification": {"references_resolved": False, "prior_prediction_verified": False,
                         "observation_eligibility_verified": False, "calibration_verified": False},
        "limitations": [
            "References are supplied declarations; this function does not access storage or verify timing, category meaning, state labels or observation eligibility.",
            "A single score does not establish calibration, independent samples, population accuracy, IR information value or investment performance.",
            "No probability estimation, default probabilities, score threshold or investment decision is supplied.",
        ],
    }
