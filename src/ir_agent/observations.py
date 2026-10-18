"""Validate a precommitted IR observation and describe visible observations.

This independently implemented record design follows docs/ir-outcome-observation.md.
Descriptive counts are not fitted likelihoods, calibrated precision, or a trading
policy. No smoothing, minimum sample size, or default probability is supplied.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
from urllib.parse import urlsplit

from .models import day, integer, json_text, object_value, text, timestamp
from .valuation import _number
from .observation_assessments import assessment_view, validate_assessments


_REQUIRED = {"id", "company_id", "question_id", "question", "thesis_version", "cohort_id", "design_version",
             "question_created_at", "design_recorded_at", "hypothesis", "signals", "reply_deadline",
             "verification_deadline", "premise_evidence", "policy_ref", "replies", "external_changes"}
_OPTIONAL = {"dispatch", "response_check", "verification", "synthetic", "prior", "prior_provenance", "assessments"}


def _fields(value, required, optional, path):
    value = object_value(value, path)
    if not required <= set(value) or set(value) - required - optional:
        raise ValueError(f"{path} requires {sorted(required)!r}; unknown fields are not accepted")
    return value


def _sequence(value, path):
    if not isinstance(value, list):
        raise ValueError(f"{path} must be a list")
    return value


def _definitions(value, path):
    value = object_value(value, path)
    if not value:
        raise ValueError(f"{path} must not be empty")
    for name, definition in value.items():
        text(name, path + " name")
        text(definition, f"{path}.{name}")
        if name != name.strip():
            raise ValueError(f"{path} names must not have surrounding whitespace")
    return value


def _evidence(value, company_id, path):
    value = _fields(value, {"id", "company_id", "published_at", "retrieved_at", "quote", "url"}, set(), path)
    for key in ("id", "quote", "url"):
        text(value[key], f"{path}.{key}")
    parsed = urlsplit(value["url"])
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        raise ValueError(f"{path}.url must identify a public document")
    if value["company_id"] != company_id:
        raise ValueError(f"{path} belongs to another company")
    published = timestamp(value["published_at"], path + ".published_at")
    retrieved = timestamp(value["retrieved_at"], path + ".retrieved_at")
    if retrieved < published:
        raise ValueError(f"{path} cannot be retrieved before publication")
    return published, retrieved


def validate_observation(record: dict) -> dict:
    """Validate the complete history, including events beyond a later query cutoff.

    Returns a copy. Evidence fields are explicit document references, not proof
    that this function retrieved a document or independently verified its quote.
    """
    value = deepcopy(_fields(record, _REQUIRED, _OPTIONAL, "observation"))
    for key in ("id", "company_id", "question_id", "question", "cohort_id"):
        text(value[key], key)
    for key in ("thesis_version", "design_version"):
        integer(value[key], key, minimum=1)
    if type(value.get("synthetic", False)) is not bool:
        raise ValueError("synthetic must be boolean")
    question = timestamp(value["question_created_at"], "question_created_at")
    frozen = timestamp(value["design_recorded_at"], "design_recorded_at")
    reply_deadline = timestamp(value["reply_deadline"], "reply_deadline")
    verification_deadline = timestamp(value["verification_deadline"], "verification_deadline")
    if not question <= frozen <= reply_deadline or verification_deadline < frozen:
        raise ValueError("Question, design freeze and deadlines have an invalid time order")
    hypothesis = _fields(value["hypothesis"], {"statement", "states", "state_timing", "target_period"}, set(), "hypothesis")
    text(hypothesis["statement"], "hypothesis.statement")
    states = _definitions(hypothesis["states"], "hypothesis.states")
    text(hypothesis["state_timing"], "hypothesis.state_timing")
    if hypothesis["state_timing"] not in {"at_question", "future_outcome"}:
        raise ValueError("state_timing must distinguish question-time state from future outcome")
    period = _fields(hypothesis["target_period"], {"start", "end"}, set(), "hypothesis.target_period")
    if day(period["end"]) < day(period["start"]):
        raise ValueError("Target period ends before it starts")
    signals = _definitions(value["signals"], "signals")
    if not {"unclear", "declined", "no_response_by_deadline"} <= set(signals):
        raise ValueError("signals must include unclear, declined and no_response_by_deadline")
    policy = value["policy_ref"]
    if policy is not None:
        _fields(policy, {"id", "version"}, set(), "policy_ref")
        text(policy["id"], "policy_ref.id"); integer(policy["version"], "policy_ref.version", minimum=1)
    premises = _sequence(value["premise_evidence"], "premise_evidence")
    if not premises:
        raise ValueError("A pre-question public premise reference is required")
    premise_ids = set()
    for evidence in premises:
        published, retrieved = _evidence(evidence, value["company_id"], "premise_evidence")
        if retrieved > question or published > question:
            raise ValueError("Premise evidence was not available before the question")
        if evidence["id"] in premise_ids:
            raise ValueError("Duplicate premise evidence ID")
        premise_ids.add(evidence["id"])
    prior = value.get("prior")
    if prior is not None:
        prior = object_value(prior, "prior")
        if set(prior) != set(states):
            raise ValueError("prior must cover exactly the defined states")
        probabilities = [_number(p, "prior probability") for p in prior.values()]
        precision = max(80, sum(len(p.as_tuple().digits) + abs(p.as_tuple().exponent) for p in probabilities) + 10)
        if precision > 100000:
            raise ValueError("Prior exceeds the supported Decimal range")
        with localcontext(Context(prec=precision)):
            if any(p < 0 or p > 1 for p in probabilities) or sum(probabilities, Decimal(0)) != 1:
                raise ValueError("prior must be a complete probability distribution summing exactly to 1")
        source = _fields(value.get("prior_provenance"), {"kind", "reference", "rationale"}, set(), "prior_provenance")
        text(source["kind"], "prior_provenance.kind")
        if source["kind"] not in {"external_evidence", "user_assumption", "synthetic_example"}:
            raise ValueError("prior provenance must distinguish evidence from assumptions")
        if source["kind"] == "synthetic_example" and not value.get("synthetic"):
            raise ValueError("Synthetic prior requires synthetic=true")
        text(source["reference"], "prior reference"); text(source["rationale"], "prior rationale")
    elif value.get("prior_provenance") is not None:
        raise ValueError("prior_provenance cannot describe an absent prior")
    dispatch = value.get("dispatch")
    attempted = None
    if dispatch is not None:
        _fields(dispatch, {"attempted_at", "recorded_at", "status"}, set(), "dispatch")
        attempted = timestamp(dispatch["attempted_at"], "dispatch.attempted_at")
        text(dispatch["status"], "dispatch.status")
        if dispatch["status"] not in {"sent", "failed", "unknown"}:
            raise ValueError("Invalid dispatch status")
        if not frozen <= attempted <= reply_deadline or attempted > timestamp(dispatch["recorded_at"]):
            raise ValueError("Dispatch cannot precede design freeze or its record precede the attempt")
    check = value.get("response_check")
    if check is not None:
        _fields(check, {"checked_through", "recorded_at"}, set(), "response_check")
        if attempted is None or dispatch["status"] != "sent":
            raise ValueError("A response check requires a recorded sent question")
        if not attempted <= timestamp(check["checked_through"]) <= timestamp(check["recorded_at"]):
            raise ValueError("Invalid response-check chronology")
    reply_ids = set()
    for reply in _sequence(value["replies"], "replies"):
        _fields(reply, {"id", "received_at", "recorded_at", "signal", "information_status"}, set(), "reply")
        text(reply["id"], "reply.id")
        if reply["id"] in reply_ids:
            raise ValueError("Duplicate reply ID")
        reply_ids.add(reply["id"])
        if attempted is None or dispatch["status"] == "failed":
            raise ValueError("A reply requires a dispatched question without a known delivery failure")
        if not attempted <= timestamp(reply["received_at"]) <= timestamp(reply["recorded_at"]):
            raise ValueError("Reply cannot precede dispatch or its record precede receipt")
        text(reply["signal"], "reply.signal")
        if reply["signal"] not in signals or reply["signal"] == "no_response_by_deadline":
            raise ValueError("Reply signal must be a defined response, not a no-response label")
        text(reply["information_status"], "reply.information_status")
        if reply["information_status"] not in {"public_clarification", "unclear", "potential_nonpublic"}:
            raise ValueError("Invalid reply information_status")
    for change in _sequence(value["external_changes"], "external_changes"):
        _fields(change, {"id", "occurred_at", "recorded_at", "description", "impact"}, set(), "external change")
        text(change["id"], "external change ID"); text(change["description"], "external change description")
        if not question <= timestamp(change["occurred_at"]) <= timestamp(change["recorded_at"]):
            raise ValueError("Invalid external-change chronology")
        text(change["impact"], "external_change.impact")
        if change["impact"] not in {"invalidates_question_time_inference", "unresolved", "reviewed_no_change"}:
            raise ValueError("External change requires an explicit impact review")
    changes = value["external_changes"]
    if len({c["id"] for c in changes}) != len(changes):
        raise ValueError("Duplicate external-change ID")
    verification = value.get("verification")
    if verification is not None:
        _fields(verification, {"status", "recorded_at", "reason", "evidence"}, {"state"}, "verification")
        status = verification["status"]
        text(status, "verification.status")
        if status not in {"verified", "pending", "not_identifiable", "state_changed", "definition_mismatch"}:
            raise ValueError("Invalid verification status")
        when = timestamp(verification["recorded_at"])
        text(verification["reason"], "verification.reason")
        if when < frozen:
            raise ValueError("Verification cannot predate design freeze")
        if status == "not_identifiable" and when < verification_deadline:
            raise ValueError("not_identifiable requires reaching the precommitted verification deadline")
        evidence = _sequence(verification["evidence"], "verification.evidence")
        if status == "verified":
            text(verification.get("state"), "verification.state")
            if verification.get("state") not in states or not evidence:
                raise ValueError("Verified state requires a defined state and later public evidence")
        elif verification.get("state") is not None:
            raise ValueError("An unresolved verification cannot assert a state")
        evidence_ids = set()
        for item in evidence:
            published, retrieved = _evidence(item, value["company_id"], "verification.evidence")
            if not question <= published <= retrieved <= when:
                raise ValueError("Verification needs subsequent publication retrieved before its verdict")
            if item["id"] in evidence_ids:
                raise ValueError("Duplicate verification evidence ID")
            evidence_ids.add(item["id"])
    validate_assessments(value)
    return value


def _visible(event, cutoff):
    return event is not None and timestamp(event["recorded_at"]) <= cutoff


def _view(record, cutoff):
    result = {"id": record["id"], "company_id": record["company_id"], "question_id": record["question_id"],
              "cohort_id": record["cohort_id"], "design_version": record["design_version"],
              "policy_ref": record["policy_ref"], "synthetic": record.get("synthetic", False),
              "active": timestamp(record["design_recorded_at"]) <= cutoff,
              "signal": None, "state": None, "eligible_for_descriptive_table": False,
              "exclusion_reasons": [], "late_reply_count": 0, "verification_status": "not_recorded"}
    if not result["active"]:
        result.update(dispatch_status="not_yet_recorded", response_status="not_yet_recorded",
                      exclusion_reasons=["design_not_yet_recorded"])
        return result
    record, corrections = assessment_view(record, cutoff)
    if corrections:
        result["assessment_views"] = corrections
    dispatch = record.get("dispatch")
    if not _visible(dispatch, cutoff):
        result.update(dispatch_status="not_sent_or_not_yet_recorded", response_status="not_applicable")
        result["exclusion_reasons"].append("not_sent_or_not_yet_recorded")
    else:
        result["dispatch_status"] = dispatch["status"]
        if dispatch["status"] != "sent":
            result["response_status"] = "delivery_failed" if dispatch["status"] == "failed" else "delivery_unknown"
            result["exclusion_reasons"].append(result["response_status"])
        else:
            replies = sorted((r for r in record["replies"] if _visible(r, cutoff)),
                             key=lambda r: (timestamp(r["received_at"]), r["id"]))
            deadline = timestamp(record["reply_deadline"])
            on_time = [r for r in replies if timestamp(r["received_at"]) <= deadline]
            result["late_reply_count"] = sum(timestamp(r["received_at"]) > deadline for r in replies)
            if on_time:
                first_time = timestamp(on_time[0]["received_at"])
                first = [r for r in on_time if timestamp(r["received_at"]) == first_time]
                if len({r["signal"] for r in first}) > 1:
                    result["response_status"] = "conflicting_first_replies"
                    result["exclusion_reasons"].append("conflicting_first_replies")
                else:
                    result.update(response_status="on_time_reply", signal=first[0]["signal"])
                    if any(r["information_status"] != "public_clarification" for r in first):
                        result["exclusion_reasons"].append("reply_information_held_for_review")
            elif cutoff < deadline:
                result["response_status"] = "awaiting_reply_deadline"
                result["exclusion_reasons"].append("reply_deadline_not_reached")
            else:
                check = record.get("response_check")
                if _visible(check, cutoff) and timestamp(check["checked_through"]) >= deadline:
                    result.update(response_status="no_response_by_deadline", signal="no_response_by_deadline")
                else:
                    result["response_status"] = "response_not_verified"
                    result["exclusion_reasons"].append("response_log_not_verified_through_deadline")
    verification = record.get("verification")
    if _visible(verification, cutoff):
        result["verification_status"] = verification["status"]
        if verification["status"] == "verified":
            result["state"] = verification["state"]
        else:
            result["exclusion_reasons"].append("verification_" + verification["status"])
    else:
        result["verification_status"] = "awaiting_verification_deadline" if cutoff < timestamp(record["verification_deadline"]) else "verification_missing_after_deadline"
        result["exclusion_reasons"].append(result["verification_status"])
    changes = [c for c in record["external_changes"] if _visible(c, cutoff)]
    result["visible_external_changes"] = len(changes)
    if any(c["impact"] in {"invalidates_question_time_inference", "unresolved"} for c in changes):
        result["exclusion_reasons"].append("external_change_blocks_state_inference")
    result["eligible_for_descriptive_table"] = bool(result["signal"] is not None and result["state"] is not None and not result["exclusion_reasons"])
    return result


def summarize_observations(records: list[dict], *, as_of: str) -> dict:
    """Describe all records, excluding future events from cutoff-time evidence.

    All input observations are retained as views. Counts and ratios are split by
    a compatible cohort/design, never exported as calibrated IR likelihoods.
    """
    cutoff = timestamp(as_of, "as_of")
    records = [validate_observation(r) for r in _sequence(records, "records")]
    if len({r["id"] for r in records}) != len(records):
        raise ValueError("Duplicate observation ID")
    if len({(r["company_id"], r["question_id"]) for r in records}) != len(records):
        raise ValueError("A company/question pair must have one observation, not duplicate outcomes")
    reply_ids = [reply["id"] for record in records for reply in record["replies"]]
    if len(set(reply_ids)) != len(reply_ids):
        raise ValueError("A reply ID cannot be reused across observations")
    cohorts = {}
    views = []
    for record in records:
        key = (record["cohort_id"], record["design_version"])
        definition = {"state_timing": record["hypothesis"]["state_timing"], "states": record["hypothesis"]["states"],
                      "target_period": record["hypothesis"]["target_period"], "signals": record["signals"],
                      "synthetic": record.get("synthetic", False)}
        signature = sha256(json_text(definition).encode()).hexdigest()
        if key in cohorts and cohorts[key]["definition_sha256"] != signature:
            raise ValueError("A cohort/design version cannot mix different state, signal, target-period definitions or synthetic status")
        if key not in cohorts:
            cohorts[key] = {"cohort_id": key[0], "design_version": key[1], "definition": definition,
                            "definition_sha256": signature, "record_count": 0, "active_count": 0,
                            "eligible_count": 0, "excluded_count": 0, "exclusion_counts": Counter(),
                            "company_counts": Counter(), "policy_counts": Counter(),
                            "state_signal_counts": {s: {signal: 0 for signal in definition["signals"]} for s in definition["states"]}}
        group = cohorts[key]; group["record_count"] += 1
        view = _view(record, cutoff); views.append(view)
        if not view["active"]:
            continue
        group["active_count"] += 1
        group["company_counts"][record["company_id"]] += 1
        policy = record["policy_ref"]
        group["policy_counts"]["unknown" if policy is None else json_text(policy)] += 1
        if view["eligible_for_descriptive_table"]:
            group["eligible_count"] += 1
            group["state_signal_counts"][view["state"]][view["signal"]] += 1
        else:
            group["excluded_count"] += 1
            group["exclusion_counts"].update(view["exclusion_reasons"])
    groups = []
    for key in sorted(cohorts):
        group = cohorts[key]
        group["descriptive_signal_ratios_given_verified_state"] = {}
        for state, counts in group["state_signal_counts"].items():
            denominator = sum(counts.values())
            with localcontext(Context(prec=80, rounding=ROUND_HALF_UP)):
                ratios = {signal: {"numerator": n, "denominator": denominator,
                                   "ratio": format(Decimal(n) / denominator, "f") if denominator else None}
                          for signal, n in counts.items()}
            group["descriptive_signal_ratios_given_verified_state"][state] = ratios
        group["within_company_repetition_present"] = any(n > 1 for n in group["company_counts"].values())
        for name in ("exclusion_counts", "company_counts", "policy_counts"):
            group[name] = dict(sorted(group[name].items()))
        groups.append(group)
    active = [v for v in views if v["active"]]
    return {"status": "observations_only", "calibration_status": "needs_calibration", "as_of": cutoff.isoformat(),
            "record_count": len(records), "active_count": len(active), "not_yet_recorded_count": len(records)-len(active),
            "eligible_count": sum(v["eligible_for_descriptive_table"] for v in active),
            "dispatch_counts": dict(sorted(Counter(v["dispatch_status"] for v in active).items())),
            "response_counts": dict(sorted(Counter(v["response_status"] for v in active).items())),
            "verification_counts": dict(sorted(Counter(v["verification_status"] for v in active).items())),
            "records_with_late_replies": sum(v["late_reply_count"] > 0 for v in active),
            "unknown_policy_count": sum(v["policy_ref"] is None for v in active),
            "excluded_active_count": sum(not v["eligible_for_descriptive_table"] for v in active),
            "cohorts": groups, "observations": views,
            "signal_rule": "Use the earliest received on-time reply visible at as_of; conflicting simultaneous first replies are excluded. Late replies do not replace a verified deadline no-response signal.",
            "limitations": ["Ratios describe only the sent, signal-observed, supplied verified-label subset; selection and missing-label bias remain.",
                            "Repeated observations within a company are not independent evidence.",
                            "Public-document references and state labels are supplied assertions, not independently checked by this API.",
                            "No likelihood estimation, smoothing, performance threshold, investment ranking or sending is performed."]}
