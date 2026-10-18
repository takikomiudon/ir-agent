"""Deterministic, JPY-denominated scenario valuation.

The formulas below are independently implemented. The design follows the
separation of software-computed numbers from model-written explanations in
FinRobot, and the explicit valuation assumptions in Anthropic's thesis tracker:

https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/README.md
https://github.com/anthropics/financial-services-plugins/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/vertical-plugins/equity-research/skills/thesis-tracker/SKILL.md

No provider data, default discount rate, or model-generated number is supplied.

``dividend_discount`` independently implements Damodaran, *Valuing Financial
Service Firms* (April 2009), PDF pp.14–15, especially the two-stage equity-per-
share equation on p.15 (forecast and stable-period costs of equity may differ):
https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf
Preserved source/quotes: research/valuation-model-routing-2026-10-15/sources.json.
As p.14 states, "We value equity by discounting cash flows to equity investors
at the cost of equity." DDM uses expected payouts, not automatically all cash
available for distribution. Applicability, regulatory capital, future payout
sustainability, dilution and consistent per-share forecasts remain external
assumptions; the calculator does not establish them or estimate missing values.

``dcf_explicit_terminal`` follows Damodaran, *Valuing Young, Start-up and Growth
Companies* (May 2009), PDF pp.39–40: year-n terminal value uses the explicitly
prepared FCFF_(n+1), then is discounted n periods. This implementation keeps the
existing single discount rate for both forecast and stable periods; the author's
year-specific rate example is outside this limited project contract. No tax,
reinvestment or (1+g) is applied to the explicit terminal flow. Source and scope:
docs/explicit-terminal-fcff-spec.md. Legacy ``dcf`` retains its last-FCF growth
calculation and does not consume previously ignored terminal fields.

``dcf_explicit_terminal_equity_bridge`` additionally keeps cash, non-operating
assets, debt and minority interests separate in the equity bridge. Damodaran,
*Ups and Downs: Valuing Cyclical and Commodity Companies* (September 2009),
PDF pp.17–18 and 24–25, displays this bridge for Toyota. Source, quotations and
displayed-input discrepancies are preserved in
research/ir-toyota-author-valuation-readiness-2026-10-15/readiness.json.
The nonnegative-input restriction is a project scope, not a certification of
book/market values, ownership claims, absence of double counting or forecasts.

``graham_number`` independently implements sqrt(22.5 * EPS * BVPS) as described
by the maxgfr/crible maintainers at commit
00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7, not Graham's complete eligibility
rules or a validated investment strategy. Preserved formula and input scope:
research/ir-case-studies-2026-10-15/1975/graham-number-input-spec-review-2026-10-16/specification.json.
The annual displayed-input arithmetic is independently preserved in
research/ir-case-studies-2026-10-15/1975/graham-number-annual-arithmetic-2026-10-16/README.md.
The fixed 22.5 is the cited formula coefficient, not a default input or risk
threshold. Annual actual earnings, ordinary-share equity/denominator alignment,
and applicability require external review. No price, forecast, growth, treasury
share adjustment or input period is inferred by this two-input calculator.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import (
    Context, Decimal, DecimalException, DivisionByZero, InvalidOperation,
    Overflow, ROUND_HALF_UP, Underflow, localcontext,
)
from typing import Any


_ONE = Decimal("1")
_HUNDRED = Decimal("100")
_OUTPUT_QUANTUM = Decimal("0.01")
_EXPLICIT_DCF_METHODS = ("dcf_explicit_terminal", "dcf_explicit_terminal_equity_bridge")
# Computational budget for this new square-root method only; not a financial
# admissibility rule. Bound representation size before allocating its context.
_GRAHAM_MAX_INPUT_PLACES = 10000
# Price, probabilities and mixed-method forecast horizons also contribute to
# _precision. Cap their combined context before allocating it, only when this
# new method is present; legacy-only valuations retain their existing contract.
_GRAHAM_MAX_CONTEXT_PRECISION = 100000


@dataclass(frozen=True)
class _Scenario:
    name: str
    probability: Decimal | None
    method: str
    inputs: dict[str, Any]


def _number(value: Any, path: str) -> Decimal:
    """Parse a finite decimal without importing binary float rounding errors."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError(f"{path} must be a finite number or numeric string")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (DecimalException, ValueError) as exc:
        raise ValueError(f"{path} must be a finite number or numeric string") from exc
    if not result.is_finite():
        raise ValueError(f"{path} must be finite")
    return result


def _required_number(values: dict[str, Any], key: str, path: str) -> Decimal:
    if key not in values:
        raise ValueError(f"{path}.{key} is required")
    return _number(values[key], f"{path}.{key}")


def _aggregation(valuation: dict) -> str:
    mode = valuation.get("aggregation", "weighted")
    if not isinstance(mode, str) or mode not in {"weighted", "unweighted"}:
        raise ValueError("valuation.aggregation must be 'weighted' or 'unweighted'")
    return mode


def _prepare(valuation: Any) -> list[_Scenario]:
    if not isinstance(valuation, dict):
        raise ValueError("valuation must be an object")
    aggregation = _aggregation(valuation)
    raw_scenarios = valuation.get("scenarios")
    if not isinstance(raw_scenarios, list) or not raw_scenarios:
        raise ValueError("valuation.scenarios must be a non-empty list")

    names: set[str] = set()
    scenarios = []
    for index, raw in enumerate(raw_scenarios):
        path = f"valuation.scenarios[{index}]"
        if not isinstance(raw, dict):
            raise ValueError(f"{path} must be an object")
        name = raw.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{path}.name must be a non-empty string")
        name = name.strip()
        if name in names:
            raise ValueError(f"scenario name {name!r} must be unique")
        names.add(name)

        if aggregation == "unweighted":
            if raw.get("probability") is not None:
                raise ValueError(f"{path}.probability must be absent or null in unweighted mode; do not mix configured and unknown probabilities")
            probability = None
        else:
            probability = _required_number(raw, "probability", path)
            if not Decimal("0") <= probability <= _ONE:
                raise ValueError(f"{path}.probability must be between 0 and 1")

        method = raw.get("method")
        if method not in ("eps_multiple", "graham_number", "dcf", "dividend_discount", *_EXPLICIT_DCF_METHODS):
            raise ValueError(f"{path}.method must be 'eps_multiple', 'graham_number', 'dcf', 'dividend_discount', 'dcf_explicit_terminal' or 'dcf_explicit_terminal_equity_bridge'")
        raw_inputs = raw.get("inputs")
        input_path = f"{path}.inputs"
        if not isinstance(raw_inputs, dict):
            raise ValueError(f"{input_path} must be an object")

        if method == "eps_multiple":
            inputs: dict[str, Any] = {
                key: _required_number(raw_inputs, key, input_path)
                for key in ("eps_jpy", "pe")
            }
            for key, value in inputs.items():
                if value <= 0:
                    raise ValueError(f"{input_path}.{key} must be greater than zero")
        elif method == "graham_number":
            required_keys = {"eps_jpy", "book_value_per_share_jpy"}
            if set(raw_inputs) != required_keys:
                raise ValueError(f"{input_path} must contain exactly the two graham_number inputs: eps_jpy and book_value_per_share_jpy")
            inputs = {key: _required_number(raw_inputs, key, input_path)
                      for key in ("eps_jpy", "book_value_per_share_jpy")}
            for key, value in inputs.items():
                if value <= 0:
                    raise ValueError(f"{input_path}.{key} must be greater than zero")
                if (len(value.as_tuple().digits) > _GRAHAM_MAX_INPUT_PLACES
                        or abs(value.as_tuple().exponent) > _GRAHAM_MAX_INPUT_PLACES
                        or abs(value.adjusted()) > _GRAHAM_MAX_INPUT_PLACES):
                    raise ValueError(f"{input_path}.{key} exceeds the supported graham_number Decimal computation budget")
        elif method == "dividend_discount":
            required_keys = {
                "dividends_per_share_jpy", "cost_of_equity", "terminal_cost_of_equity",
                "terminal_dividend_per_share_jpy", "terminal_growth_rate",
            }
            if set(raw_inputs) != required_keys:
                raise ValueError(f"{input_path} must contain exactly the five dividend_discount inputs; do not mix firm cash flows, WACC, cash, debt or shares")
            inputs = {
                key: _required_number(raw_inputs, key, input_path)
                for key in required_keys - {"dividends_per_share_jpy"}
            }
            raw_dividends = raw_inputs["dividends_per_share_jpy"]
            if not isinstance(raw_dividends, list) or not raw_dividends:
                raise ValueError(f"{input_path}.dividends_per_share_jpy must be a non-empty list")
            inputs["dividends_per_share_jpy"] = [
                _number(value, f"{input_path}.dividends_per_share_jpy[{period}]")
                for period, value in enumerate(raw_dividends)
            ]
            for key in ("cost_of_equity", "terminal_cost_of_equity"):
                if inputs[key] <= 0:
                    raise ValueError(f"{input_path}.{key} must be greater than zero")
            growth = inputs["terminal_growth_rate"]
            if growth <= -_ONE or growth >= inputs["terminal_cost_of_equity"]:
                raise ValueError(f"{input_path}.terminal_growth_rate must be greater than -1 and less than terminal_cost_of_equity")
            if inputs["terminal_dividend_per_share_jpy"] < 0 or any(value < 0 for value in inputs["dividends_per_share_jpy"]):
                raise ValueError(f"{input_path} dividends per share must be non-negative")
        else:
            if method in _EXPLICIT_DCF_METHODS:
                required_keys = {"discount_rate", "terminal_growth_rate", "cash_jpy", "debt_jpy",
                                 "shares_outstanding", "fcf_jpy", "terminal_fcff_jpy"}
                if method == "dcf_explicit_terminal_equity_bridge":
                    required_keys |= {"non_operating_assets_jpy", "minority_interests_jpy"}
                if set(raw_inputs) != required_keys:
                    count = "nine" if method == "dcf_explicit_terminal_equity_bridge" else "seven"
                    raise ValueError(f"{input_path} must contain exactly the {count} {method} inputs")
            inputs = {
                key: _required_number(raw_inputs, key, input_path)
                for key in (
                    "discount_rate", "terminal_growth_rate", "cash_jpy",
                    "debt_jpy", "shares_outstanding",
                )
            }
            raw_fcf = raw_inputs.get("fcf_jpy")
            if not isinstance(raw_fcf, list) or not raw_fcf:
                raise ValueError(f"{input_path}.fcf_jpy must be a non-empty list")
            inputs["fcf_jpy"] = [
                _number(value, f"{input_path}.fcf_jpy[{period}]")
                for period, value in enumerate(raw_fcf)
            ]
            if method in _EXPLICIT_DCF_METHODS:
                inputs["terminal_fcff_jpy"] = _required_number(raw_inputs, "terminal_fcff_jpy", input_path)
            if method == "dcf_explicit_terminal_equity_bridge":
                for key in ("non_operating_assets_jpy", "minority_interests_jpy"):
                    inputs[key] = _required_number(raw_inputs, key, input_path)
            rate = inputs["discount_rate"]
            growth = inputs["terminal_growth_rate"]
            if rate <= 0:
                raise ValueError(f"{input_path}.discount_rate must be greater than zero")
            if growth <= -_ONE or growth >= rate:
                raise ValueError(
                    f"{input_path}.terminal_growth_rate must be greater than -1 "
                    "and less than discount_rate"
                )
            adjustment_keys = ("cash_jpy", "debt_jpy")
            if method == "dcf_explicit_terminal_equity_bridge":
                adjustment_keys += ("non_operating_assets_jpy", "minority_interests_jpy")
            for key in adjustment_keys:
                if inputs[key] < 0:
                    raise ValueError(f"{input_path}.{key} must be non-negative")
            if inputs["shares_outstanding"] <= 0:
                raise ValueError(f"{input_path}.shares_outstanding must be greater than zero")
        scenarios.append(_Scenario(name, probability, method, inputs))
    return scenarios


def _precision(scenarios: list[_Scenario], current_price: Decimal | None) -> int:
    """Use guard digits and input-dependent precision, isolated from caller state."""
    numbers = [] if current_price is None else [current_price]
    horizon = 1
    for scenario in scenarios:
        if scenario.probability is not None:
            numbers.append(scenario.probability)
        for value in scenario.inputs.values():
            if isinstance(value, list):
                horizon = max(horizon, len(value))
                numbers.extend(value)
            else:
                numbers.append(value)
    integer_places = max(max(1, value.adjusted() + 1) for value in numbers)
    fractional_places = max(max(0, -value.as_tuple().exponent) for value in numbers)
    digits = max(len(value.as_tuple().digits) for value in numbers)
    return max(80, (integer_places + digits) * (horizon + 2) + fractional_places + 20)


def _money_or_percent(value: Decimal) -> str:
    rounded = value.quantize(_OUTPUT_QUANTUM, rounding=ROUND_HALF_UP)
    if rounded == 0:
        rounded = abs(rounded)
    return format(rounded, "f")


def _ratio(value: Decimal) -> str:
    if value == 0:
        return "0"
    result = format(value, "f")
    return result.rstrip("0").rstrip(".") if "." in result else result


def _fair_value(scenario: _Scenario) -> tuple[Decimal, dict[str, str | int]]:
    inputs = scenario.inputs
    if scenario.method == "eps_multiple":
        return inputs["eps_jpy"] * inputs["pe"], {}

    if scenario.method == "graham_number":
        return (Decimal("22.5") * inputs["eps_jpy"]
                * inputs["book_value_per_share_jpy"]).sqrt(), {}

    if scenario.method == "dividend_discount":
        # Damodaran (2009), PDF p.15: explicit year-end DPS are discounted at
        # forecast-period k_e. TV_n uses *next year's* explicit DPS divided by
        # stable-period k_e minus stable growth, then is discounted n years at
        # forecast k_e. Neither cost nor next-period DPS is inferred.
        factor = _ONE
        present_dividends = Decimal("0")
        for dividend in inputs["dividends_per_share_jpy"]:
            factor *= _ONE + inputs["cost_of_equity"]
            present_dividends += dividend / factor
        terminal_value = inputs["terminal_dividend_per_share_jpy"] / (
            inputs["terminal_cost_of_equity"] - inputs["terminal_growth_rate"]
        )
        present_terminal = terminal_value / factor
        return present_dividends + present_terminal, {
            "present_value_of_forecast_dividends_jpy": _money_or_percent(present_dividends),
            "terminal_value_per_share_jpy": _money_or_percent(terminal_value),
            "present_value_of_terminal_value_jpy": _money_or_percent(present_terminal),
        }

    # FCF is unlevered, company-wide JPY received at each forecast year's end.
    # Terminal value uses the following year's FCF and the Gordon growth formula.
    factor = _ONE
    present_value = Decimal("0")
    rate = inputs["discount_rate"]
    growth = inputs["terminal_growth_rate"]
    for fcf in inputs["fcf_jpy"]:
        factor *= _ONE + rate
        present_value += fcf / factor
    if scenario.method in _EXPLICIT_DCF_METHODS:
        # This amount is already next-period, after-tax/reinvestment FCFF.
        # Keep the forecast array and n unchanged; no additional growth factor.
        terminal_value = inputs["terminal_fcff_jpy"] / (rate - growth)
    else:
        # Preserve legacy DCF semantics, even if raw input has a terminal field.
        terminal_value = inputs["fcf_jpy"][-1] * (_ONE + growth) / (rate - growth)
    enterprise_value = present_value + terminal_value / factor
    equity_value = enterprise_value + inputs["cash_jpy"] - inputs["debt_jpy"]
    if scenario.method == "dcf_explicit_terminal_equity_bridge":
        equity_value += inputs["non_operating_assets_jpy"] - inputs["minority_interests_jpy"]
    if equity_value < 0:
        raise ValueError(
            f"DCF scenario {scenario.name!r} has negative equity value; "
            "it cannot be converted to a non-negative stock price"
        )
    details = {
        "enterprise_value_jpy": _money_or_percent(enterprise_value),
        "equity_value_jpy": _money_or_percent(equity_value),
    }
    if scenario.method in _EXPLICIT_DCF_METHODS:
        details.update(
            terminal_fcff_jpy=_ratio(inputs["terminal_fcff_jpy"]),
            forecast_periods=len(inputs["fcf_jpy"]),
            terminal_value_jpy=_money_or_percent(terminal_value),
            present_value_of_terminal_value_jpy=_money_or_percent(terminal_value / factor),
            present_value_of_forecast_fcf_jpy=_money_or_percent(present_value),
        )
    if scenario.method == "dcf_explicit_terminal_equity_bridge":
        details.update({key: _money_or_percent(inputs[key]) for key in (
            "cash_jpy", "non_operating_assets_jpy", "debt_jpy", "minority_interests_jpy",
        )})
        details["equity_bridge_formula"] = (
            "enterprise_value_jpy + cash_jpy + non_operating_assets_jpy"
            " - debt_jpy - minority_interests_jpy"
        )
    return equity_value / inputs["shares_outstanding"], details


def calculate_valuation(
    valuation: dict[str, Any], current_price_jpy: str | int | float, *, include_unrounded: bool = False
) -> dict[str, Any]:
    """Return scenario prices and probability-weighted value as JSON-safe strings.

    ``probability`` is a ratio and must sum exactly to one. ``eps_multiple`` uses
    positive EPS in JPY per share and a positive P/E multiple. ``dcf`` requires
    explicit end-of-year, unlevered FCF forecasts in company-wide JPY, cash and
    debt in JPY, shares outstanding, discount rate, and terminal growth rate.
    Rates are ratios: ``0.10`` means 10%. No default assumptions are inferred.

    ``graham_number`` accepts exactly positive finite ``eps_jpy`` and
    ``book_value_per_share_jpy``, both in JPY per share, and computes their
    product times the fixed 22.5 coefficient before taking Decimal.sqrt().
    It does not check annual/ordinary-share basis or estimate missing inputs.
    Each input is limited to 10,000 coefficient digits and absolute decimal
    exponent/adjusted exponent for bounded computation, not investment screening.
    When any scenario uses this method, total context precision (including
    price, probabilities, other inputs and forecast horizons) is limited to
    100,000 digits before Context creation. Legacy-only valuations are unchanged.

    ``dcf_explicit_terminal`` accepts exactly those six DCF fields plus required
    ``terminal_fcff_jpy``: explicit company-wide JPY FCFF for year n+1. Its year-n
    terminal value is terminal_fcff_jpy / (discount_rate - terminal_growth_rate)
    and is discounted n years at the same rate as the forecasts. No tax,
    reinvestment or growth is reapplied to that amount. Both forecast and terminal
    flows may be negative or zero; the existing nonnegative-equity constraint
    still applies. Forecasts remain nonempty (n>=1). The explicit-terminal methods
    add the terminal/forecast PV decomposition to scenario output. No source, period,
    stable-growth or forecast-adoption verification is supplied by arithmetic.

    ``dcf_explicit_terminal_equity_bridge`` requires exactly those seven inputs
    plus ``non_operating_assets_jpy`` and ``minority_interests_jpy``, including
    explicit zero values. Each of cash, non-operating assets, debt and minority
    interests is a nonnegative company-wide JPY amount at the valuation time.
    Equity is PV of operating cash flows + cash + non-operating assets - debt -
    minority interests, divided by the supplied shares. The new method alone
    adds those four adjustment amounts as two-decimal strings and a fixed
    ``equity_bridge_formula`` string to the existing explicit-terminal details.
    Intermediates remain unrounded. Book/market basis, other claims, ownership,
    double counting and forecast applicability require separate sourced review.
    Legacy DCF ignores these fields; old explicit-terminal stays exact-seven.

    Omitted ``aggregation`` or explicit ``weighted`` retains that probability-
    weighted contract. Explicit ``aggregation: unweighted`` instead requires
    every probability to be absent or null, and calculates only the supplied
    scenario values/range and downside. Expected values remain null; no average,
    equal weights or implicit probability-one scenario is created. This is the
    project's retention of unset probabilities, not an additional investment
    rule: Anthropic earnings-preview requests bull/base/bear operating scenarios
    but supplies no fixed probabilities for them.

    ``dividend_discount`` follows Damodaran (2009), PDF p.15: a non-empty array
    of explicit nonnegative year-end JPY DPS is discounted at ``cost_of_equity``.
    The year-n terminal value is the explicitly supplied n+1 DPS divided by
    ``terminal_cost_of_equity - terminal_growth_rate``; that value is discounted
    n years at the forecast-period cost. Both equity costs must be positive;
    stable growth must be greater than -1 and below the terminal equity cost.
    Its inputs accept exactly those five fields; company-wide FCF, WACC, cash,
    debt and share counts are not interchangeable with the per-share payouts.
    Dividends can differ from distributable earnings; payout sustainability and
    dilution require external, sourced assumptions. No FCFE model is inferred.
    All-zero payouts give zero modeled value, while current_price stays positive.

    Negative forecast FCF is allowed. Negative DCF equity value is an error;
    zero equity value is valid. ``worst_case_downside_pct`` is the non-negative
    loss magnitude against the lowest-valued supplied scenario, not a loss
    guarantee or a statistical bound beyond those supplied scenarios.

    ``include_unrounded=True`` additionally exposes computed values without
    display quantization for policy-boundary comparisons; defaults stay unchanged.

    Calculation uses a private high-precision Decimal context. Intermediate
    monetary amounts are not quantized; prices and percentages are rounded
    HALF_UP to two decimal places only for serialization. Invalid inputs or
    results outside Decimal's computation range raise ``ValueError``.
    """
    if type(include_unrounded) is not bool:
        raise ValueError("include_unrounded must be boolean")
    current_price = _number(current_price_jpy, "current_price_jpy")
    if current_price <= 0:
        raise ValueError("current_price_jpy must be greater than zero")
    scenarios = _prepare(valuation)
    unweighted = _aggregation(valuation) == "unweighted"

    try:
        precision = _precision(scenarios, current_price)
        if (any(scenario.method == "graham_number" for scenario in scenarios)
                and precision > _GRAHAM_MAX_CONTEXT_PRECISION):
            raise ValueError("valuation exceeds the supported graham_number Decimal context computation budget")
        context = Context(
            prec=precision, rounding=ROUND_HALF_UP,
            Emin=-999999, Emax=999999, flags=[],
            traps=[InvalidOperation, DivisionByZero, Overflow, Underflow],
        )
        with localcontext(context):
            if not unweighted and sum((scenario.probability for scenario in scenarios), Decimal("0")) != _ONE:
                raise ValueError("scenario probabilities must sum exactly to 1")

            result_scenarios = []
            expected_value = Decimal("0")
            fair_values = []
            for scenario in scenarios:
                fair_value, details = _fair_value(scenario)
                if not fair_value.is_finite():
                    raise ValueError(f"scenario {scenario.name!r} has a non-finite fair value")
                fair_values.append(fair_value)
                if not unweighted:
                    expected_value += scenario.probability * fair_value
                result_scenarios.append({
                    "name": scenario.name,
                    "probability": None if scenario.probability is None else _ratio(scenario.probability),
                    "method": scenario.method,
                    "fair_value_jpy": _money_or_percent(fair_value),
                    "upside_pct": _money_or_percent((fair_value / current_price - _ONE) * _HUNDRED),
                    **details,
                })

            downside = max(Decimal("0"), (_ONE - min(fair_values) / current_price) * _HUNDRED)
            result = {
                "scenarios": result_scenarios,
                "expected_value_jpy": None if unweighted else _money_or_percent(expected_value),
                "expected_upside_pct": None if unweighted else _money_or_percent((expected_value / current_price - _ONE) * _HUNDRED),
                "worst_case_downside_pct": _money_or_percent(downside),
            }
            if unweighted:
                result.update(aggregation="unweighted", status="scenario_values_only",
                              valuation_range_jpy={"min": _money_or_percent(min(fair_values)),
                                                   "max": _money_or_percent(max(fair_values))})
            if include_unrounded:
                result["unrounded"] = {
                    "expected_value_jpy": None if unweighted else format(expected_value, "f"),
                    "scenarios": [{"name": s.name, "fair_value_jpy": format(v, "f")}
                                  for s, v in zip(scenarios, fair_values)],
                }
                if unweighted:
                    result["unrounded"]["valuation_range_jpy"] = {"min": format(min(fair_values), "f"),
                                                                  "max": format(max(fair_values), "f")}
            return result
    except DecimalException as exc:
        raise ValueError("valuation exceeds the supported Decimal computation range") from exc


def calculate_reference_value(
    valuation: dict[str, Any], *, include_unrounded: bool = False
) -> dict[str, Any]:
    """Calculate scenario references without a market price or price ratios.

    Uses the same input validation, six method kernels, precision policy and
    output rounding as ``calculate_valuation``. Only a supplied weighted model
    produces an expected reference; unweighted scenarios retain unknown
    probabilities. No price, probability, forecast or financial adoption is
    inferred. ``include_unrounded`` retains finite-context calculation values,
    not an exact irrational result or a certified policy boundary.
    """
    if type(include_unrounded) is not bool:
        raise ValueError("include_unrounded must be boolean")
    # Invalid numeric text can set Decimal flags while it is parsed. Isolate
    # validation here without changing the legacy priced entrypoint's behavior.
    with localcontext():
        scenarios = _prepare(valuation)
    unweighted = _aggregation(valuation) == "unweighted"

    try:
        precision = _precision(scenarios, None)
        if (any(scenario.method == "graham_number" for scenario in scenarios)
                and precision > _GRAHAM_MAX_CONTEXT_PRECISION):
            raise ValueError("valuation exceeds the supported graham_number Decimal context computation budget")
        context = Context(
            prec=precision, rounding=ROUND_HALF_UP,
            Emin=-999999, Emax=999999, flags=[],
            traps=[InvalidOperation, DivisionByZero, Overflow, Underflow],
        )
        with localcontext(context):
            if not unweighted and sum((scenario.probability for scenario in scenarios), Decimal("0")) != _ONE:
                raise ValueError("scenario probabilities must sum exactly to 1")

            references = []
            result_scenarios = []
            expected = Decimal("0")
            for scenario in scenarios:
                reference, _details = _fair_value(scenario)
                if not reference.is_finite():
                    raise ValueError(f"scenario {scenario.name!r} has a non-finite fair value")
                references.append(reference)
                if not unweighted:
                    expected += scenario.probability * reference
                result_scenarios.append({
                    "name": scenario.name,
                    "probability": None if scenario.probability is None else _ratio(scenario.probability),
                    "method": scenario.method,
                    "reference_value_jpy": _money_or_percent(reference),
                })

            result = {
                "status": "reference_values_only",
                "aggregation": "unweighted" if unweighted else "weighted",
                "scenarios": result_scenarios,
                "expected_reference_value_jpy": None if unweighted else _money_or_percent(expected),
                "financial_inputs_verified": False,
                "meaning_review_required": True,
            }
            if unweighted:
                result["reference_range_jpy"] = {
                    "min": _money_or_percent(min(references)),
                    "max": _money_or_percent(max(references)),
                }
            if include_unrounded:
                result["unrounded"] = {
                    "expected_reference_value_jpy": None if unweighted else format(expected, "f"),
                    "scenarios": [{"name": scenario.name, "reference_value_jpy": format(value, "f")}
                                  for scenario, value in zip(scenarios, references)],
                }
                if unweighted:
                    result["unrounded"]["reference_range_jpy"] = {
                        "min": format(min(references), "f"),
                        "max": format(max(references), "f"),
                    }
            return result
    except DecimalException as exc:
        raise ValueError("valuation exceeds the supported Decimal computation range") from exc
