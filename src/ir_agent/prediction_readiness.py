"""Read-only candidate forecast/observation linkage audit; never a scorer.

The observation ledger is the population. Content hashes and timing checks do
not establish independently bound labels, training provenance or calibration.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from .models import integer, object_value, text, timestamp
from .observation_store import _design_hash
from .observations import summarize_observations, validate_observation
from .prediction_store import _binding, _digest, _likelihoods, _validate_request


def _rows(snapshot, section, fields):
    if section not in snapshot:
        return None
    rows = snapshot[section]
    if not isinstance(rows, list):
        raise ValueError(section + " must be a list")
    for row in rows:
        object_value(row, section + " row")
        if set(row) != fields:
            raise ValueError(section + " row has missing or unknown fields")
        timestamp(row["first_saved_at"], section + ".first_saved_at")
        object_value(row["record"], section + ".record")
    return rows


def _visible_events(history, cutoff):
    events = []
    for row in history:
        record = row["record"]
        dispatch = record.get("dispatch")
        if dispatch and timestamp(dispatch["recorded_at"]) <= cutoff:
            events.append(("dispatch", timestamp(dispatch["attempted_at"])))
        for reply in record["replies"]:
            if timestamp(reply["recorded_at"]) <= cutoff:
                events.append(("receipt", timestamp(reply["received_at"])))
        verification = record.get("verification")
        if (verification and verification["status"] != "pending"
                and timestamp(verification["recorded_at"]) <= cutoff):
            events.append(("outcome_adjudication", timestamp(verification["recorded_at"])))
    return events


def _signal_leakage(history, cutoff):
    """Record candidates, not a claim that reviewers saw the outcome."""
    state_times = []
    for row in history:
        verification = row["record"].get("verification")
        if verification and verification["status"] == "verified" and timestamp(verification["recorded_at"]) <= cutoff:
            state_times.append(timestamp(verification["recorded_at"]))
    if not state_times:
        return []
    known = min(state_times); candidates = {}
    for row in history:
        record = row["record"]
        for event in record.get("assessments", []):
            if (event["target_kind"] != "reply" or timestamp(event["recorded_at"]) > cutoff
                    or (event.get("first_saved_at") and timestamp(event["first_saved_at"]) > cutoff)):
                continue
            target = next(reply for reply in record["replies"] if reply["id"] == event["target_id"])
            earlier = [item for item in record.get("assessments", [])
                       if item["target_kind"] == "reply" and item["target_id"] == event["target_id"]
                       and item["version"] < event["version"]]
            previous = earlier[-1]["assessment"]["signal"] if earlier else target["signal"]
            if event["assessment"]["signal"] != previous and timestamp(event["recorded_at"]) >= known:
                candidates[event["id"]] = {"assessment_id": event["id"], "target_id": event["target_id"],
                    "version": event["version"], "recorded_at": event["recorded_at"],
                    "state_known_at": known.isoformat(), "reason": "signal_reclassified_after_state_known"}
    return list(candidates.values())


def _audit_prediction(row, history, current, models, cutoff):
    reasons = []; timing = []; value = row["record"]
    result = {"id": row["id"], "first_saved_at": row["first_saved_at"], "status": "invalid_prediction_reference",
              "reference_verified": False, "prospective_timing": "unverified", "reason_codes": reasons,
              "evidence_binding_verified": False, "training_provenance_verified": False, "calibration_verified": False}
    try:
        request = object_value(value.get("request"), "saved prediction request")
        created = _validate_request(request)
        saved = timestamp(row["first_saved_at"])
        if type(value.get("schema_version")) is not int or value["schema_version"] != 1 or value.get("status") != "candidate_prediction_only":
            reasons.append("unsupported_saved_prediction_schema")
        if created > saved or created > cutoff:
            reasons.append("prediction_created_after_save_or_cutoff")
        reference = request["observation_ref"]
        target = next((item for item in history if item["version"] == reference["version"]), None)
        if target is None:
            reasons.append("referenced_observation_version_unavailable")
            return result
        record = validate_observation(target["record"])
        if (request["id"] != row["id"] or value.get("id") != row["id"]
                or reference["id"] != row["observation_id"] or reference["version"] != row["observation_version"]):
            reasons.append("prediction_identity_or_reference_mismatch")
        if reference["snapshot_sha256"] != _digest(record):
            reasons.append("observation_snapshot_mismatch")
        if reference["design_sha256"] != target["design_sha256"] or _design_hash(record) != target["design_sha256"]:
            reasons.append("observation_design_mismatch")
        expected_binding = _binding(record, target["version"])
        if value.get("observation_binding") != expected_binding:
            reasons.append("observation_company_or_definition_binding_mismatch")
        if current is not None and _binding(current["record"], target["version"]) != expected_binding:
            reasons.append("current_observation_design_or_identity_changed")
        if request["synthetic"] != record.get("synthetic", False):
            reasons.append("synthetic_status_mismatch")
        _likelihoods(request["likelihoods"], record["signals"], record["hypothesis"]["states"])
        if row["request_sha256"] != _digest(request):
            reasons.append("prediction_request_snapshot_mismatch")
        model = request["model_ref"]
        commitment = {"model_ref": model, "training_ref": request["training_ref"], "synthetic": request["synthetic"]}
        if row["model_id"] != model["id"] or row["model_version"] != model["version"]:
            reasons.append("model_identity_mismatch")
        if value.get("model_commitment_sha256") != _digest(commitment):
            reasons.append("model_commitment_mismatch")
        if models is None:
            result["model_table_status"] = "unknown"
        else:
            matched = [item for item in models if item["model_id"] == model["id"] and item["model_version"] == model["version"]]
            if not matched or timestamp(matched[0]["first_saved_at"]) > saved:
                reasons.append("saved_model_commitment_unavailable")
            elif matched[0]["record"] != commitment or matched[0]["commitment_sha256"] != _digest(commitment):
                reasons.append("saved_model_commitment_mismatch")
            result["model_table_status"] = "known"
        if timestamp(target["first_saved_at"]) > created or timestamp(record["design_recorded_at"]) > created:
            timing.append("observation_design_saved_after_prediction_creation")
        if value.get("observation_first_saved_at") != target["first_saved_at"]:
            reasons.append("observation_saved_time_binding_mismatch")
        if timestamp(record["reply_deadline"]) < saved or timestamp(record["verification_deadline"]) < saved:
            timing.append("prediction_saved_after_observation_deadline")
        for kind, occurred in _visible_events(history, cutoff):
            if occurred < saved:
                timing.append("actual_" + kind + "_predates_prediction_save")
        result["prospective_timing"] = "invalid" if timing else "no_detected_violation"
        reasons.extend(timing)
        result["reference_verified"] = not reasons or (bool(timing) and set(reasons) == set(timing))
        result["status"] = ("invalid_prospective_timing" if timing and result["reference_verified"]
                            else "invalid_prediction_reference" if reasons else "needs_evidence_binding_review")
        result["synthetic"] = request["synthetic"]
        result["observation_ref"] = deepcopy(reference)
    except (ValueError, KeyError) as error:
        # Malformed persisted content is reported, rather than dropped from the
        # observed population or silently repaired. No caller state is changed.
        reasons.append("invalid_saved_prediction")
        result["validation_error"] = str(error)
    result["reason_codes"] = list(dict.fromkeys(reasons))
    return result


def audit_prediction_readiness(snapshot: dict, *, as_of: str) -> dict:
    """Audit a consistent SQLite-shaped snapshot; absent tables remain unknown."""
    object_value(snapshot, "prediction readiness snapshot")
    if set(snapshot) - {"observation_versions", "predictions", "models"}:
        raise ValueError("Unknown prediction readiness snapshot section")
    cutoff = timestamp(as_of, "as_of")
    observations = _rows(snapshot, "observation_versions", {"observation_id", "version", "design_sha256", "record", "first_saved_at"})
    predictions = _rows(snapshot, "predictions", {"id", "observation_id", "observation_version", "model_id", "model_version", "request_sha256", "record", "first_saved_at"})
    models = _rows(snapshot, "models", {"model_id", "model_version", "commitment_sha256", "record", "first_saved_at"})
    keys = set(); histories = {}
    for row in observations or []:
        text(row["observation_id"], "observation ID"); integer(row["version"], "observation version", minimum=1)
        key = (row["observation_id"], row["version"])
        if key in keys: raise ValueError("Duplicate observation version")
        keys.add(key)
        if timestamp(row["first_saved_at"]) <= cutoff:
            record = validate_observation(row["record"])
            if record["id"] != row["observation_id"] or _design_hash(record) != row["design_sha256"]:
                raise ValueError("Saved observation identity/design mismatch")
            histories.setdefault(row["observation_id"], []).append(row)
    for history in histories.values(): history.sort(key=lambda item: item["version"])
    prediction_ids = set(); visible_predictions = []
    for row in predictions or []:
        text(row["id"], "prediction ID"); text(row["observation_id"], "prediction observation ID")
        integer(row["observation_version"], "prediction observation version", minimum=1)
        text(row["model_id"], "model ID"); integer(row["model_version"], "model version", minimum=1)
        if row["id"] in prediction_ids: raise ValueError("Duplicate prediction ID")
        prediction_ids.add(row["id"])
        if timestamp(row["first_saved_at"]) <= cutoff:
            created = row["record"].get("request", {}).get("created_at") if isinstance(row["record"].get("request"), dict) else None
            if created is not None and timestamp(created, "prediction.created_at") > cutoff: continue
            visible_predictions.append(row)
    model_keys = set()
    for row in models or []:
        text(row["model_id"], "model ID"); integer(row["model_version"], "model version", minimum=1)
        key = (row["model_id"], row["model_version"])
        if key in model_keys: raise ValueError("Duplicate model commitment")
        model_keys.add(key)
    views = summarize_observations([history[-1]["record"] for history in histories.values()], as_of=as_of)["observations"]
    by_id = {view["id"]: view for view in views}; reports = []; orphans = []
    for observation_id, history in sorted(histories.items()):
        current = history[-1]; view = by_id[observation_id]
        attached = [_audit_prediction(row, history, current, models, cutoff) for row in visible_predictions if row["observation_id"] == observation_id]
        leakages = _signal_leakage(history, cutoff)
        for item in attached:
            item["signal_classification_leakage_candidates"] = deepcopy(leakages)
            item["observation_exclusion_reasons"] = deepcopy(view["exclusion_reasons"])
        reports.append({"observation_id": observation_id, "company_id": current["record"]["company_id"],
            "synthetic": current["record"].get("synthetic", False),
            "current_snapshot": {"version": current["version"], "snapshot_sha256": _digest(current["record"]),
                                 "design_sha256": current["design_sha256"], "first_saved_at": current["first_saved_at"]},
            "view": view, "predictions": attached,
            "prediction_coverage": "unknown" if predictions is None else "present" if attached else "missing",
            "status": "needs_evidence_binding_review" if attached else "predictions_unknown" if predictions is None else "missing_prediction"})
    for row in visible_predictions:
        if row["observation_id"] not in histories:
            orphans.append(_audit_prediction(row, [], None, models, cutoff))
    return {"status": "prediction_readiness_only", "as_of": cutoff.isoformat(),
        "table_status": {key: "unknown" if value is None else "known" for key, value in
                         (("observation_versions", observations), ("predictions", predictions), ("models", models))},
        "observation_count": len(reports), "visible_prediction_count": len(visible_predictions),
        "orphan_prediction_count": len(orphans),
        "observations_without_prediction_count": sum(item["prediction_coverage"] == "missing" for item in reports),
        "prediction_status_counts": dict(Counter(item["status"] for report in reports for item in report["predictions"])),
        "observation_dispatch_counts": dict(Counter(item["view"]["dispatch_status"] for item in reports)),
        "observation_response_counts": dict(Counter(item["view"]["response_status"] for item in reports)),
        "observation_verification_counts": dict(Counter(item["view"]["verification_status"] for item in reports)),
        "orphan_predictions": orphans, "observations": reports,
        "evidence_binding_verified": False, "training_provenance_verified": False, "calibration_verified": False,
        "limitations": ["No forecast is scored or declared ready for scoring; all original observations remain the population.",
            "Content/time agreement is not independently verified reply/state evidence, training history or calibration.",
            "Signal changes after a known state are leakage candidates; no automatic adoption or repair is performed.",
            "Equal timestamps do not prove execution order; no_detected_violation is not verified prospectiveness."]}
