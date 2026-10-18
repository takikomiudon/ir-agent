"""Apply an explicitly sourced policy to a thesis and precommitted IR branches.

Principles: the preserved Anthropic thesis-tracker and earnings-preview skills.
The executable gates are this project's adaptation, not an upstream strategy.
No numerical investment limits, probabilities, prices or evidence are inferred.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Context, Decimal, DecimalException, DivisionByZero, InvalidOperation, Overflow, ROUND_HALF_UP, Underflow, localcontext

from .models import JST, available, day, integer, object_value, source_origins, strings, text, timestamp, validate_question, validate_source, validate_thesis
from .valuation import _number, _prepare, calculate_valuation

_OPTIONAL_PARAMETERS = {"allow_date_precision"}
_PARAMETERS = {
    "minimum_upside_pct", "maximum_downside_pct", "entry_cost_pct", "exit_cost_pct",
    "max_quote_age_seconds", "target_scenario",
}


def validate_decision_policy(value: dict) -> dict:
    policy = deepcopy(object_value(value, "decision policy"))
    text(policy.get("id"), "policy.id")
    integer(policy.get("version"), "policy.version", minimum=1)
    timestamp(policy.get("recorded_at"), "policy.recorded_at")
    parameters = object_value(policy.get("parameters"), "policy.parameters")
    sources = object_value(policy.get("parameter_sources", {}), "policy.parameter_sources")
    if set(parameters) - (_PARAMETERS | _OPTIONAL_PARAMETERS) or set(sources) - (_PARAMETERS | _OPTIONAL_PARAMETERS):
        raise ValueError("Unknown decision parameter or source; do not silently ignore a misspelled limit")
    for key, source in sources.items():
        object_value(source, f"policy.parameter_sources.{key}")
    for key, value in parameters.items():
        if value is None:
            continue
        if key == "allow_date_precision":
            if type(value) is not bool:
                raise ValueError("policy.allow_date_precision must be boolean")
        elif key == "target_scenario":
            text(value, "policy.target_scenario")
        elif key == "max_quote_age_seconds":
            integer(value, "policy.max_quote_age_seconds", minimum=1)
        else:
            number = _number(value, f"policy.{key}")
            if number < 0 or (key == "maximum_downside_pct" and number > 100):
                raise ValueError(f"Invalid policy.{key}")
            if key in {"entry_cost_pct", "exit_cost_pct"} and number >= 100:
                raise ValueError(f"policy.{key} must be below 100")
        source = object_value(sources.get(key), f"policy.parameter_sources.{key}")
        if source.get("kind") not in ("user", "external_policy", "synthetic_example"):
            raise ValueError(f"policy.{key} requires a user or external policy source")
        for name in ("reference", "rationale"):
            text(source.get(name), f"policy.parameter_sources.{key}.{name}")
    return policy


def check_quote_timing(quote: dict, max_quote_age_seconds: int, *, as_of: str) -> dict:
    """Apply only the existing policy age/availability gate, with exact us.

    This does not verify price/source binding, precision, company or a complete
    decision. Callers retain their existing checks and ordering for those.
    """
    object_value(quote, "quote timing snapshot")
    integer(max_quote_age_seconds, "max_quote_age_seconds", minimum=1)
    boundary = timestamp(as_of, "quote timing as_of")
    observed = timestamp(quote.get("observed_at"), "quote.observed_at")
    retrieved = timestamp(quote.get("retrieved_at"), "quote.retrieved_at")
    if observed > retrieved:
        raise ValueError("A quote cannot be retrieved before its observation")
    elapsed = boundary - observed
    age = (elapsed.days * 86400 + elapsed.seconds) * 1000000 + elapsed.microseconds
    status, reasons = "fresh", []
    if observed > boundary or retrieved > boundary:
        status, reasons = "unavailable", ["market_quote_not_available"]
    elif age > max_quote_age_seconds * 1000000:
        status, reasons = "stale", ["market_quote_stale"]
    return {"checked_at": boundary.isoformat(), "status": status, "reason_codes": reasons,
            "age_microseconds": age, "max_quote_age_seconds": max_quote_age_seconds}


def _check_decision_quote_source(quote: dict, source_map: dict, company_id: str, as_of) -> str | None:
    """Check saved quote identity/origin before policy-specific timing gates.

    Callers supply validated snapshots. Missing evidence returns a reason;
    inconsistent identity or deterministic normalization raises. Persistence
    calls this even when a policy/position gate would stop pure calculation.
    """
    required_quote = {"company_id", "source_id", "price_jpy", "currency", "observed_at", "retrieved_at"}
    if any(quote.get(k) is None for k in required_quote):
        return "missing_market_quote"
    text(quote["source_id"], "quote.source_id")
    if quote["company_id"] != company_id or quote["currency"] != "JPY":
        raise ValueError("Quote must refer to the same company in JPY")
    observed = timestamp(quote["observed_at"], "quote.observed_at")
    retrieved = timestamp(quote["retrieved_at"], "quote.retrieved_at")
    if observed > retrieved:
        raise ValueError("A quote cannot be retrieved before its observation")
    market_source = source_map.get(quote["source_id"])
    if market_source is None:
        return "missing_market_source_snapshot"
    if market_source["company_id"] != company_id or market_source["source_type"] != "market_data":
        raise ValueError("Quote must be backed by a market-data source for the same company")
    if timestamp(market_source["retrieved_at"]) != retrieved:
        raise ValueError("Quote retrieval time must equal its saved source retrieval time")
    lineage_issue = _check_source_origins([market_source["id"]], source_map, company_id, as_of)
    if lineage_issue:
        return lineage_issue
    metadata = market_source["metadata"]
    if metadata.get("provider") == "jquants" and metadata.get("dataset") == "equities/bars/daily/decision-quote":
        from .quotes import normalize_jquants_quote
        original = source_map.get(metadata.get("original_source_id"))
        if original is None:
            return "missing_original_quote_source"
        expected_source = validate_source(normalize_jquants_quote(original)["sources"][1])
        if market_source != expected_source:
            raise ValueError("Derived quote differs from deterministic normalization of its original source")
    return None


def _check_decision_quote_fields(quote: dict, market_source: dict, *, validate_present_fields=False) -> str | None:
    """Check source fields; persistence may also check a partial supplied quote.

    The default retains pure decision's missing-path early-return ordering.
    """
    missing_paths = not quote.get("price_path") or not quote.get("observed_at_path")
    if missing_paths and not validate_present_fields:
        return "quote_not_bound_to_source_fields"
    if quote.get("price_path") and (not validate_present_fields or quote.get("price_jpy") is not None):
        if _number(_source_field(market_source, quote["price_path"]), "source price") != _number(quote["price_jpy"], "quote.price_jpy"):
            raise ValueError("Quote price differs from the cited source field")
    if quote.get("observed_at_path") and (not validate_present_fields or quote.get("observed_at") is not None):
        if timestamp(_source_field(market_source, quote["observed_at_path"]), "source observation") != timestamp(quote["observed_at"], "quote.observed_at"):
            raise ValueError("Quote observation differs from the cited source field")
    return "quote_not_bound_to_source_fields" if missing_paths else None


def _evaluate_decision(request: dict) -> dict:
    request = object_value(request, "decision request")
    thesis = validate_thesis(request.get("thesis"))
    policy = validate_decision_policy(request.get("policy"))
    as_of = timestamp(request.get("as_of"), "decision.as_of")
    if timestamp(thesis["recorded_at"]) > as_of or timestamp(policy["recorded_at"]) > as_of:
        raise ValueError("Thesis and policy must be available at decision.as_of")
    context = object_value(request.get("context", {}), "decision.context")
    result = {
        "company_id": thesis["company_id"], "thesis_version": thesis["version"],
        "as_of": as_of.isoformat(), "policy_id": policy["id"], "policy_version": policy["version"],
        "policy_snapshot": policy, "status": "unresolved", "proposed_action": "unresolved",
        "reason_codes": [], "evidence_ids": context.get("evidence_ids", []),
    }
    if any(x.get("kind") == "synthetic_example" for x in policy.get("parameter_sources", {}).values()):
        if request.get("synthetic") is not True:
            raise ValueError("A synthetic example policy cannot be used for a non-synthetic decision")
    missing = sorted(k for k in _PARAMETERS if policy["parameters"].get(k) is None)
    if missing:
        result.update(reason_codes=["policy_not_configured"], missing_parameters=missing)
        return result
    if type(context.get("held")) is not bool:
        result["reason_codes"] = ["position_not_verified"]
        return result
    if context.get("thesis_status") not in ("intact", "invalidated", "uncertain"):
        result["reason_codes"] = ["thesis_status_not_reviewed"]
        return result
    if context.get("information_status") not in ("public_disclosure", "public_clarification"):
        result["reason_codes"] = ["information_held_for_review"]
        return result
    evidence = strings(context.get("evidence_ids", []), "context.evidence_ids")
    if not evidence:
        result["reason_codes"] = ["missing_decision_evidence"]
        return result
    if not set(evidence) <= set(thesis["evidence_ids"]):
        raise ValueError("Decision evidence must belong to the selected thesis snapshot")
    if context["thesis_status"] == "uncertain":
        result["reason_codes"] = ["thesis_uncertain"]
        return result
    if day(thesis["next_review_date"]) <= as_of.astimezone(JST).date():
        result["reason_codes"] = ["thesis_review_due"]
        return result
    raw_sources = request.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        result["reason_codes"] = ["missing_source_snapshots"]
        return result
    source_map = {}
    for item in raw_sources:
        source = validate_source(item)
        if source["id"] in source_map:
            raise ValueError("Duplicate source IDs in decision snapshots")
        source_map[source["id"]] = source
    for source_id in thesis["evidence_ids"]:
        source = source_map.get(source_id)
        if source is None:
            result["reason_codes"] = ["missing_thesis_source_snapshot"]
            return result
        if source["company_id"] != thesis["company_id"]:
            raise ValueError("Thesis evidence snapshot belongs to a different company")
        if not available(source, timestamp(thesis["recorded_at"])):
            result["reason_codes"] = ["evidence_not_available_at_thesis_recording"]
            return result
        if source["source_type"] == "ir_reply" and source["metadata"].get("information_status") != "public_clarification":
            result["reason_codes"] = ["source_information_held_for_review"]
            return result
    lineage_issue = _check_source_origins(thesis["evidence_ids"], source_map, thesis["company_id"], timestamp(thesis["recorded_at"]))
    if lineage_issue:
        result["reason_codes"] = [lineage_issue]
        return result
    quote = object_value(request.get("quote", {}), "decision.quote")
    quote_issue = _check_decision_quote_source(quote, source_map, thesis["company_id"], as_of)
    if quote_issue:
        result["reason_codes"] = [quote_issue]
        return result
    market_source = source_map[quote["source_id"]]
    observed = timestamp(quote["observed_at"], "quote.observed_at")
    retrieved = timestamp(quote["retrieved_at"], "quote.retrieved_at")
    metadata = market_source["metadata"]
    precisions = (quote.get("observation_precision"), metadata.get("observation_precision"))
    if any(value not in (None, "instant", "second", "day") for value in precisions):
        raise ValueError("Unknown or malformed quote observation precision")
    if "day" in precisions:
        if policy["parameters"].get("allow_date_precision") is not True:
            result["reason_codes"] = ["observation_precision_not_accepted"]
            return result
    if retrieved > as_of or not available(market_source, as_of):
        result["reason_codes"] = ["market_quote_not_available"]
        return result
    quote_issue = _check_decision_quote_fields(quote, market_source)
    if quote_issue:
        result["reason_codes"] = [quote_issue]
        return result
    p = policy["parameters"]
    quote_check = check_quote_timing(quote, p["max_quote_age_seconds"], as_of=as_of.isoformat())
    if quote_check["reason_codes"]:
        result["reason_codes"] = quote_check["reason_codes"]
        return result
    valuation = calculate_valuation(thesis["valuation"], quote["price_jpy"], include_unrounded=True)
    exact = valuation.pop("unrounded")
    target = next((x for x in exact["scenarios"] if x["name"] == p["target_scenario"]), None)
    if target is None:
        raise ValueError("policy.target_scenario must name a supplied valuation scenario")
    price = _number(quote["price_jpy"], "quote.price_jpy")
    expected_value = exact["expected_value_jpy"]
    numbers = [price, *(_number(p[k], k) for k in ("entry_cost_pct", "exit_cost_pct", "minimum_upside_pct", "maximum_downside_pct")),
               *(_number(x["fair_value_jpy"], "scenario price") for x in exact["scenarios"])]
    if expected_value is not None:
        numbers.append(_number(expected_value, "expected value"))
    precision = max(80, sum(len(x.as_tuple().digits) + abs(x.as_tuple().exponent) for x in numbers) + 40)
    with localcontext(Context(prec=precision, rounding=ROUND_HALF_UP, Emin=-999999, Emax=999999,
                              flags=[], traps=[InvalidOperation, DivisionByZero, Overflow, Underflow])):
        # Existing holdings do not incur a new purchase fee merely by being held.
        entry = price if context["held"] else price * (1 + _number(p["entry_cost_pct"], "entry cost") / 100)
        proceeds_factor = 1 - _number(p["exit_cost_pct"], "exit cost") / 100
        expected = _number(expected_value, "expected value") * proceeds_factor if expected_value is not None else None
        worst = min(_number(x["fair_value_jpy"], "scenario price") for x in exact["scenarios"]) * proceeds_factor
        target_net = _number(target["fair_value_jpy"], "target value")
        upside = (expected / entry - 1) * 100 if expected is not None else None
        downside = max(Decimal(0), (1 - worst / entry) * 100)
        entry_upside_pass = (expected * 100 >= entry * (100 + _number(p["minimum_upside_pct"], "minimum upside"))
                             if expected is not None else None)
        downside_pass = worst * 100 >= entry * (100 - _number(p["maximum_downside_pct"], "maximum downside"))
        target_reached = price * proceeds_factor >= target_net
        result["metrics"] = {
            "net_expected_upside_pct": format(upside, "f") if upside is not None else None,
            "scenario_downside_pct": format(downside, "f"),
            "target_price_jpy_before_exit_cost": format(target_net / proceeds_factor, "f"),
            "entry_price_ceiling_jpy": format(expected / ((1 + _number(p["entry_cost_pct"], "entry cost") / 100) *
                                                         (1 + _number(p["minimum_upside_pct"], "minimum upside") / 100)), "f")
                                        if expected is not None else None,
            "entry_upside_pass": entry_upside_pass, "scenario_downside_pass": downside_pass,
        }
    result.update(status="reviewed", valuation=valuation, quote=deepcopy(quote))
    if context["thesis_status"] == "invalidated":
        result.update(proposed_action="exit_review" if context["held"] else "watch", reason_codes=["thesis_invalidated"])
    elif context["held"] and target_reached:
        result.update(proposed_action="exit_review", reason_codes=["valuation_target_reached"])
    elif context["held"] and not downside_pass:
        result.update(proposed_action="exit_review", reason_codes=["scenario_risk_limit_exceeded"])
    elif context["held"]:
        result.update(proposed_action="hold_review", reason_codes=["thesis_intact_below_target"])
    elif expected is None:
        result.update(status="unresolved", proposed_action="unresolved", reason_codes=["scenario_probabilities_not_configured"])
    elif entry_upside_pass and downside_pass:
        result.update(proposed_action="buy_review", reason_codes=["entry_conditions_met"])
    else:
        result.update(proposed_action="watch", reason_codes=[code for code, ok in
                      (("insufficient_expected_upside", entry_upside_pass), ("scenario_risk_limit_exceeded", downside_pass)) if not ok])
    return result


def evaluate_decision(request: dict) -> dict:
    try:
        return _evaluate_decision(request)
    except DecimalException as error:
        raise ValueError("Decision inputs exceed the supported Decimal computation range") from error


def _check_source_origins(roots, source_map, company_id, boundary):
    visited, active = set(), set()
    pending = [(source_id, False) for source_id in roots]
    while pending:
        source_id, exiting = pending.pop()
        if exiting:
            active.remove(source_id)
            visited.add(source_id)
            continue
        if source_id in active:
            raise ValueError("Cyclic source provenance is not valid evidence")
        if source_id in visited:
            continue
        source = source_map.get(source_id)
        if source is None:
            return "missing_origin_source_snapshot"
        if source["company_id"] != company_id:
            raise ValueError("Source provenance belongs to another company")
        if not available(source, boundary):
            return "source_origin_not_available"
        classification = source["metadata"].get("information_status")
        if ((source["source_type"] == "ir_reply" and classification != "public_clarification")
                or classification not in (None, "public_disclosure", "public_clarification")):
            return "source_information_held_for_review"
        active.add(source_id)
        pending.append((source_id, True))
        pending.extend((parent, False) for parent in source_origins(source))
    return None


def _source_field(source: dict, path: list):
    if not isinstance(path, list) or not path:
        raise ValueError("Quote source paths must be nonempty lists of field names or indices")
    current = source
    for component in path:
        if isinstance(current, str):
            try:
                from .models import parse_json
                current = parse_json(current, parse_float=Decimal)
            except (ValueError, TypeError) as error:
                raise ValueError("Quote source path does not resolve to a structured field") from error
        if isinstance(current, dict) and isinstance(component, str) and component in current:
            current = current[component]
        elif isinstance(current, list) and type(component) is int and 0 <= component < len(current):
            current = current[component]
        else:
            raise ValueError("Quote source path does not resolve to a saved field")
    return current


def _flatten(value: dict) -> dict:
    # Traverse only canonical financial inputs used by the valuation calculator.
    # Extra metadata or dotted JSON keys must never shadow a real model input.
    scenarios = _prepare(value)
    if any("." in scenario.name for scenario in scenarios):
        raise ValueError("IR parameter paths require scenario names without dots")
    canonical = {"scenarios": {s.name: {"probability": s.probability, "method": s.method, "inputs": s.inputs}
                               for s in scenarios}}
    result = {}
    def visit(item, path):
        if isinstance(item, dict):
            for key, child in item.items():
                visit(child, f"{path}.{key}" if path else key)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                visit(child, f"{path}.{index}")
        else:
            if path in result:
                raise ValueError("Ambiguous financial parameter path")
            result[path] = item
    visit(canonical, "")
    return result


def _same(left, right):
    try:
        return _number(left, "value") == _number(right, "value")
    except ValueError:
        return left == right


def evaluate_ir_plan(request: dict) -> dict:
    request = deepcopy(object_value(request, "IR plan"))
    object_value(request.get("context", {}), "plan.context")
    thesis = validate_thesis(request.get("thesis"))
    question = validate_question(request.get("question"))
    policy = validate_decision_policy(request.get("policy"))
    as_of = timestamp(request.get("as_of"), "plan.as_of")
    if question["company_id"] != thesis["company_id"] or question["thesis_version"] != thesis["version"]:
        raise ValueError("Question must use the same company and current thesis version")
    created = timestamp(question["created_at"])
    if not timestamp(thesis["recorded_at"]) <= created <= as_of:
        raise ValueError("Question must be created after its thesis and before plan.as_of")
    if timestamp(policy["recorded_at"]) > created:
        raise ValueError("Freeze the decision policy before the question")
    if not set(question["evidence_ids"]) <= set(thesis["evidence_ids"]):
        raise ValueError("Question evidence must belong to its thesis snapshot")
    before = _flatten(thesis["valuation"])
    paths = strings(question.get("parameter_paths", []), "question.parameter_paths")
    if any(path not in before for path in paths):
        raise ValueError("Question parameter_paths must identify existing valuation inputs")
    outcomes = []
    incomplete = []
    public_review = None
    if "public_information_review" in question:
        from .public_information_review import check_public_information_review
        public_review = check_public_information_review(question, request.get("sources"),
                                                       as_of=as_of.isoformat())
        if public_review["reason_codes"]:
            incomplete.append("public_information_review_binding")
    for branch in question["branches"]:
        if branch["action"] == "unresolved":
            outcomes.append({"branch_id": branch["id"], "proposed_action": "unresolved", "status": "unresolved",
                             "reason_codes": ["ambiguous_or_no_response"], "parameter_changes": []})
            continue
        updated = deepcopy(thesis)
        updated["valuation"] = branch.get("valuation", thesis["valuation"])
        after = _flatten(updated["valuation"])
        changes = sorted(k for k in before.keys() | after.keys() if k not in before or k not in after or not _same(before[k], after[k]))
        unauthorized = [k for k in changes if k not in paths]
        if unauthorized:
            outcome = {"status": "unresolved", "proposed_action": "unresolved", "reason_codes": ["unmapped_parameter_change"],
                       "unmapped_parameters": unauthorized}
        else:
            context = dict(request.get("context", {}))
            context["thesis_status"] = branch.get("thesis_status")
            context["information_status"] = "public_clarification"
            context["evidence_ids"] = question["evidence_ids"]
            outcome = evaluate_decision({**request, "thesis": updated, "context": context})
        outcome.update(branch_id=branch["id"], precommitted_action=branch["action"], parameter_changes=changes)
        if outcome["status"] != "reviewed":
            incomplete.append(branch["id"])
        outcomes.append(outcome)
    actions = {x["proposed_action"] for x in outcomes if x["status"] == "reviewed"}
    if question.get("public_answer_status") != "not_found":
        incomplete.append("public_information_review")
    result = {"question_id": question["id"], "company_id": thesis["company_id"], "as_of": as_of.isoformat(),
            "question_value": "needs_review" if incomplete else "decision_distinguishing" if len(actions) > 1 else "no_decision_change",
            "incomplete_reviews": incomplete, "outcomes": outcomes,
            "interpretation": "Conditional analysis before receipt; no branch has been observed or applied."}
    if public_review is not None:
        result["public_information_review_check"] = public_review
    return result
