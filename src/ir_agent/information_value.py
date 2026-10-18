"""Finite-state Bayesian value of information, independently implemented.

EVPI and EVSI are standard decision-analysis definitions, rather than a new
question-priority score. The IR adaptation is to model a reply as an imperfect
signal with explicitly supplied P(reply | state), not as revelation of truth.
All utilities/payoffs and question cost must share one cardinal, additive unit;
this calculator neither estimates those inputs nor chooses an investment.

EVSI definition: Baio, Heath and Manolopoulou, author-hosted "EVSI with the
Moment Matching method", https://gianluca.statistica.it/research/voi/ .
This module uses exact finite sums, not that chapter's moment-matching algorithm.
EVPI is the corresponding perfect-information bound over the supplied states.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import (Context, Decimal, DecimalException, DivisionByZero,
                     InvalidOperation, Overflow, ROUND_HALF_UP, Underflow,
                     localcontext)

from .valuation import _number


_ZERO = Decimal(0)
_ONE = Decimal(1)
_KEYS = {"unit", "states", "actions", "prior", "payoffs", "question_cost",
         "likelihoods", "provenance", "synthetic"}


def _object(value, path):
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    return value


def _names(value, path):
    if not isinstance(value, list) or not value:
        raise ValueError(f"{path} must be a nonempty list")
    if any(not isinstance(x, str) or not x.strip() or x != x.strip() for x in value):
        raise ValueError(f"{path} must contain nonempty names without surrounding whitespace")
    if len(set(value)) != len(value):
        raise ValueError(f"{path} contains duplicate names")
    return value


def _vector(value, names, path, probability=False):
    value = _object(value, path)
    if set(value) != set(names):
        raise ValueError(f"{path} must contain exactly {names!r}")
    result = {name: _number(value[name], f"{path}.{name}") for name in names}
    if probability and any(x < 0 or x > 1 for x in result.values()):
        raise ValueError(f"{path} probabilities must be between 0 and 1")
    return result


def _serialize(number):
    return "0" if number == 0 else format(number, "f")


def _best(values):
    maximum = max(values.values())
    return maximum, [action for action, value in values.items() if value == maximum]


def _provenance(config, required):
    sources = _object(config.get("provenance"), "provenance")
    if set(sources) != set(required):
        raise ValueError(f"provenance must contain exactly {required!r}")
    for name, source in sources.items():
        source = _object(source, f"provenance.{name}")
        if set(source) != {"kind", "reference", "rationale"}:
            raise ValueError(f"provenance.{name} requires kind, reference and rationale")
        if source["kind"] not in ("external_evidence", "user_assumption", "synthetic_example"):
            raise ValueError(f"provenance.{name}.kind must distinguish evidence from assumptions")
        for field in ("reference", "rationale"):
            if not isinstance(source[field], str) or not source[field].strip():
                raise ValueError(f"provenance.{name}.{field} must be nonempty")
        if source["kind"] == "synthetic_example" and config.get("synthetic") is not True:
            raise ValueError("Synthetic inputs require synthetic=true")
    if "synthetic" in config and type(config["synthetic"]) is not bool:
        raise ValueError("synthetic must be a boolean")
    return deepcopy(sources)


def _calculate(config):
    config = _object(config, "information-value input")
    if set(config) - _KEYS:
        raise ValueError("Unknown information-value input field")
    unit = config.get("unit")
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("unit must name a shared additive payoff and cost unit")
    states = _names(config.get("states"), "states")
    actions = _names(config.get("actions"), "actions")
    prior = _vector(config.get("prior"), states, "prior", probability=True)
    raw_payoffs = _object(config.get("payoffs"), "payoffs")
    if set(raw_payoffs) != set(actions):
        raise ValueError("payoffs must contain exactly the declared actions")
    payoffs = {action: _vector(raw_payoffs[action], states, f"payoffs.{action}") for action in actions}
    cost = _number(config.get("question_cost"), "question_cost")
    if cost < 0:
        raise ValueError("question_cost must be nonnegative")
    raw_likelihoods = config.get("likelihoods")
    likelihoods = None
    required_sources = ["prior", "payoffs", "question_cost"]
    if raw_likelihoods is not None:
        raw_likelihoods = _object(raw_likelihoods, "likelihoods")
        signals = _names(list(raw_likelihoods), "likelihoods signal names")
        likelihoods = {signal: _vector(raw_likelihoods[signal], states,
                                      f"likelihoods.{signal}", probability=True)
                       for signal in signals}
        required_sources.append("likelihoods")
    provenance = _provenance(config, required_sources)
    numbers = [cost, *prior.values(), *(x for row in payoffs.values() for x in row.values()),
               *(x for row in (likelihoods or {}).values() for x in row.values())]
    # Finite products/sums are exact at this precision; only posterior division
    # can repeat. EVSI is calculated from unnormalised joint values, so it does
    # not depend on rounding a posterior (or the caller's Decimal context).
    if any(abs(x.as_tuple().exponent) > 10000 or len(x.as_tuple().digits) > 10000 for x in numbers):
        raise ValueError("Inputs exceed supported Decimal digit/exponent range (10000)")
    precision = max(80, 4 * sum(len(x.as_tuple().digits) + abs(x.as_tuple().exponent) for x in numbers) + 40)
    with localcontext(Context(prec=precision, rounding=ROUND_HALF_UP, Emin=-999999, Emax=999999,
                              flags=[], traps=[InvalidOperation, DivisionByZero, Overflow, Underflow])):
        if sum(prior.values(), _ZERO) != _ONE:
            raise ValueError("prior probabilities must sum exactly to 1")
        if likelihoods is not None:
            for state in states:
                if sum((row[state] for row in likelihoods.values()), _ZERO) != _ONE:
                    raise ValueError(f"P(signal | {state}) must sum exactly to 1 over all signals")
        expected = {action: sum((prior[s] * payoffs[action][s] for s in states), _ZERO)
                    for action in actions}
        baseline_value, baseline_actions = _best(expected)
        perfect_value = sum((prior[s] * max(payoffs[a][s] for a in actions) for s in states), _ZERO)
        evpi = perfect_value - baseline_value
        result = {
            "status": "needs_calibration" if likelihoods is None else "calculated",
            "unit": unit, "synthetic": config.get("synthetic", False),
            "method": "finite_state_bayesian_evpi_evsi",
            "method_sources": [{"reference": "Baio, Heath and Manolopoulou: EVSI with the Moment Matching method",
                                "url": "https://gianluca.statistica.it/research/voi/",
                                "adopted": "EVSI definition as expected maximised posterior utility minus optimal prior utility",
                                "adaptation": "Independent finite-state exact summation; no moment-matching algorithm adopted"}],
            "adaptation": "IR replies are imperfect signals; likelihoods are supplied, never inferred.",
            "interpretation": "Conditional model comparison, not an instruction to contact a company or trade.",
            "assumptions": ["Actions remain available after observing a signal.",
                            "Payoffs and question cost share the stated additive utility unit.",
                            "Information does not itself change state probabilities or state payoffs.",
                            "The supplied state space and payoff matrix define the decision model."],
            "provenance": provenance,
            "baseline": {"action_expected_values": {a: _serialize(x) for a, x in expected.items()},
                         "best_actions": baseline_actions, "expected_value": _serialize(baseline_value)},
            "perfect_information": {"expected_value": _serialize(perfect_value), "evpi": _serialize(evpi),
                                    "role": "Upper bound on gross information value, not an IR forecast."},
            "question_cost": _serialize(cost),
            "sample_information": None,
        }
        if likelihoods is None:
            result["reason_codes"] = ["likelihoods_not_calibrated"]
            return result
        signals_result = {}
        sample_value = _ZERO
        for signal, likelihood in likelihoods.items():
            joint = {s: prior[s] * likelihood[s] for s in states}
            probability = sum(joint.values(), _ZERO)
            if probability == 0:
                signals_result[signal] = {"probability": "0", "possible": False,
                                          "posterior": None, "best_actions": [], "expected_value": None}
                continue
            joint_values = {a: sum((joint[s] * payoffs[a][s] for s in states), _ZERO) for a in actions}
            joint_best, best_actions = _best(joint_values)
            sample_value += joint_best
            signals_result[signal] = {"probability": _serialize(probability), "possible": True,
                                      "posterior": {s: _serialize(joint[s] / probability) for s in states},
                                      "best_actions": best_actions, "expected_value": _serialize(joint_best / probability)}
        evsi = sample_value - baseline_value
        net = evsi - cost
        # These bounds follow from the finite matrix; failure is an arithmetic
        # or implementation error, never something to hide with a clamp.
        if not _ZERO <= evsi <= evpi:
            raise ValueError("Calculated information value violates 0 <= EVSI <= EVPI")
        result["sample_information"] = {"signals": signals_result, "expected_value": _serialize(sample_value),
                                        "evsi": _serialize(evsi), "net_evsi": _serialize(net),
                                        "worth_cost": net > 0,
                                        "cost_comparison": "positive" if net > 0 else "break_even" if net == 0 else "negative"}
        return result


def calculate_information_value(config: dict) -> dict:
    """Return JSON-safe decimal strings; do not infer missing calibration.

    ``likelihoods[signal][state]`` means P(signal | state), not a posterior.
    Every declared state, including zero-prior states, needs a complete column.
    Omitted/null likelihoods produce EVPI only and ``needs_calibration``.
    Inputs may use decimal strings to preserve decimal precision through JSON.
    """
    try:
        return _calculate(config)
    except DecimalException as error:
        raise ValueError("Information-value inputs exceed supported Decimal computation range") from error
