"""Append-only observation classifications bound to saved reply/public evidence.

These are project recordkeeping rules. They do not estimate signal accuracy or
modify the original replies, external events, investment theses or policies.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

from .decision import _check_source_origins
from .models import (integer, json_text, object_value, source_origins, strings,
                     text, timestamp, validate_reply, validate_source)

_REQUEST = {"id", "target_kind", "target_id", "target_snapshot_sha256", "version",
            "expected_previous_version", "recorded_at", "reviewer", "rationale", "basis", "assessment"}
_SERVER = {"request", "first_saved_at", "basis_verification"}


def digest(value):
    return sha256(json_text(value).encode()).hexdigest()


def _hash(value, field):
    text(value, field)
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(field + " must be a lowercase SHA-256")


def _target(record, kind, target_id):
    items = record["replies"] if kind == "reply" else record["external_changes"]
    target = next((x for x in items if x["id"] == target_id), None)
    if target is None:
        raise ValueError("Assessment target is outside this observation")
    return target


def original_classification(target, kind):
    return ({"signal": target["signal"], "information_status": target["information_status"]}
            if kind == "reply" else {"impact": target["impact"]})


def _request(event):
    return {k: deepcopy(event[k]) for k in _REQUEST}


def validate_assessments(record):
    events = record.get("assessments", [])
    if not isinstance(events, list):
        raise ValueError("assessments must be a list")
    ids, chains = set(), {}
    for event in events:
        object_value(event, "observation assessment")
        if not _REQUEST <= set(event) or set(event) - _REQUEST - _SERVER:
            raise ValueError("Assessment requires its explicit target, version, reviewer, basis and classification")
        for field in ("id", "target_kind", "target_id", "reviewer", "rationale"):
            text(event[field], "assessment." + field)
        if event["id"] in ids:
            raise ValueError("Duplicate observation assessment ID")
        ids.add(event["id"])
        kind = event["target_kind"]
        if kind not in ("reply", "external_change"):
            raise ValueError("Invalid observation assessment target kind")
        target = _target(record, kind, event["target_id"])
        _hash(event["target_snapshot_sha256"], "target_snapshot_sha256")
        if event["target_snapshot_sha256"] != digest(target):
            raise ValueError("Assessment target snapshot hash differs from the immutable target")
        integer(event["version"], "assessment.version", minimum=1)
        integer(event["expected_previous_version"], "assessment.expected_previous_version")
        key = (kind, event["target_id"])
        previous = chains.get(key)
        expected = previous["version"] if previous else 0
        if event["expected_previous_version"] != expected or event["version"] != expected + 1:
            raise ValueError("Assessment target versions must form one consecutive CAS chain")
        when = timestamp(event["recorded_at"], "assessment.recorded_at")
        if when < timestamp(target["recorded_at"]) or (previous and when <= timestamp(previous["recorded_at"])):
            raise ValueError("Assessment record times must advance after their target and previous assessment")
        basis = object_value(event["basis"], "assessment.basis")
        if set(basis) - {"target_text_reference", "target_text_sha256", "basis_quote", "public_evidence_references"}:
            raise ValueError("Unknown observation assessment basis field")
        for field in ("target_text_reference", "basis_quote"):
            if field in basis:
                text(basis[field], "basis." + field)
        if "target_text_sha256" in basis:
            _hash(basis["target_text_sha256"], "target_text_sha256")
        refs = basis.get("public_evidence_references", [])
        if not isinstance(refs, list):
            raise ValueError("public_evidence_references must be a list")
        seen = set()
        for reference in refs:
            object_value(reference, "public evidence reference")
            if set(reference) != {"source_id", "source_sha256", "basis_quote"}:
                raise ValueError("Public evidence requires source_id, source_sha256 and basis_quote")
            text(reference["source_id"], "public source ID"); text(reference["basis_quote"], "public evidence quote")
            _hash(reference["source_sha256"], "public source SHA")
            if reference["source_id"] in seen:
                raise ValueError("Duplicate public evidence reference")
            seen.add(reference["source_id"])
        assessment = object_value(event["assessment"], "assessment.classification")
        if kind == "reply":
            if set(assessment) != {"signal", "information_status"}:
                raise ValueError("Reply assessment requires complete signal and information_status")
            text(assessment["signal"], "assessment.signal")
            if assessment["signal"] not in record["signals"] or assessment["signal"] == "no_response_by_deadline":
                raise ValueError("Reply assessment signal must be a precommitted response signal")
            if assessment["information_status"] not in ("public_clarification", "unclear", "potential_nonpublic"):
                raise ValueError("Invalid assessment information_status")
        else:
            if set(assessment) != {"impact"} or assessment["impact"] not in ("invalidates_question_time_inference", "unresolved", "reviewed_no_change"):
                raise ValueError("External assessment requires a complete valid impact")
        if set(event) & _SERVER:
            if not _SERVER <= set(event) or event["request"] != _request(event):
                raise ValueError("Stored assessment metadata differs from its immutable request")
            if timestamp(event["first_saved_at"]) < when:
                raise ValueError("Assessment cannot be saved before it was recorded")
            verification = object_value(event["basis_verification"], "basis_verification")
            if set(verification) != {"status", "reason_codes", "source_snapshots"}:
                raise ValueError("Invalid assessment binding metadata")
            if verification["status"] not in ("verified", "unverified"):
                raise ValueError("Invalid assessment binding status")
            strings(verification["reason_codes"], "binding reason codes")
            for source_id, source_hash in object_value(verification["source_snapshots"], "binding sources").items():
                text(source_id, "binding source ID"); _hash(source_hash, "binding source hash")
        chains[key] = event


def assessment_view(record, cutoff):
    """Copy classifications only; immutable times and population stay unchanged."""
    copied = deepcopy(record)
    latest = {}
    for event in record.get("assessments", []):
        if timestamp(event["recorded_at"]) > cutoff:
            continue
        if event.get("first_saved_at") is not None and timestamp(event["first_saved_at"]) > cutoff:
            continue
        latest[(event["target_kind"], event["target_id"])] = event
    views = []
    for (kind, target_id), event in latest.items():
        target = _target(copied, kind, target_id)
        original = original_classification(target, kind)
        bound = event.get("basis_verification", {}).get("status") == "verified"
        effective = deepcopy(event["assessment"])
        if not bound:
            stored = _SERVER <= set(event)
            effective = ({"signal": event["assessment"]["signal"] if stored else original["signal"],
                          "information_status": event["assessment"]["information_status"] if stored else "unclear"}
                         if kind == "reply" else {"impact": "unresolved"})
        target.update(effective)
        views.append({"target_kind": kind, "target_id": target_id, "assessment_id": event["id"],
                      "version": event["version"], "original_classification": original,
                      "effective_classification": effective,
                      "basis_verification": deepcopy(event.get("basis_verification", {"status": "unverified"})),
                      "recorded_at": event["recorded_at"], "first_saved_at": event.get("first_saved_at"),
                      "recorded_after_reply_deadline": timestamp(event["recorded_at"]) > timestamp(record["reply_deadline"]),
                      "recorded_after_verification": (timestamp(event["recorded_at"]) > timestamp(record["verification"]["recorded_at"])
                          if record.get("verification") is not None else None)})
    return copied, views


class _Saved:
    def __init__(self, connection):
        self.connection = connection
        self.tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    def get(self, table, record_id):
        if table not in self.tables:
            return None
        row = self.connection.execute("SELECT data FROM " + table + " WHERE id=?", (record_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def source(self, source_id):
        result = self.get("sources", source_id)
        if result is None:
            raise ValueError("Observation evidence source is not saved")
        return result


def _bind(saved, observation, target, event, saved_at):
    basis = event["basis"]; kind = event["target_kind"]
    reasons = []; target_bound = False; snapshots = {}
    if kind == "reply":
        reply = saved.get("replies", target["id"])
        question = saved.get("questions", observation["question_id"])
        if reply is None or question is None:
            reasons.append("saved_reply_or_question_unavailable")
        else:
            reply = validate_reply(reply)
            if (reply["id"] != target["id"] or reply["question_id"] != observation["question_id"]
                    or question.get("id") != observation["question_id"]
                    or question.get("company_id") != observation["company_id"]):
                raise ValueError("Assessment reply belongs to another question or company")
            if timestamp(reply["received_at"]) != timestamp(target["received_at"]):
                raise ValueError("Observation receipt time differs from its saved reply")
            raw_text = reply["raw_text"]
            target_bound = _text_binding(basis, target["id"], raw_text)
    else:
        target_bound = _text_binding(basis, target["id"], target["description"])
    if not target_bound:
        reasons.append("target_text_binding_missing")
    refs = basis.get("public_evidence_references", [])
    for reference in refs:
        root = saved.get("sources", reference["source_id"])
        if root is None:
            reasons.append("public_source_not_saved")
            continue
        if root.get("id") != reference["source_id"]:
            raise ValueError("Public evidence source identity differs from its saved key")
        if digest(root) != reference["source_sha256"]:
            raise ValueError("Public evidence snapshot SHA differs from its saved source")
        validate_source(root)
        if root["source_type"] != "public_disclosure" or reference["basis_quote"] not in root["content"]:
            raise ValueError("Public evidence must quote a saved public disclosure")
        pending = [root["id"]]; closure = {}
        while pending:
            source_id = pending.pop()
            if source_id in closure:
                continue
            source = saved.source(source_id); validate_source(source)
            if source["id"] != source_id:
                raise ValueError("Public evidence origin identity differs from its saved key")
            if not observation.get("synthetic", False) and source["metadata"].get("synthetic") is True:
                raise ValueError("Synthetic observation evidence cannot support a real observation")
            closure[source_id] = source
            pending.extend(source_origins(source))
        issue = _check_source_origins([root["id"]], closure, observation["company_id"], timestamp(event["recorded_at"]))
        if issue:
            raise ValueError("Observation public evidence is unavailable: " + issue)
        # A later classification correction cannot be hidden by an unchanged
        # original public-looking source snapshot.
        if "reply_information_reviews" in saved.tables:
            for source in closure.values():
                reply_id = source.get("metadata", {}).get("reply_id")
                if source["source_type"] == "ir_reply" and reply_id:
                    rows = [(json.loads(row[0]), timestamp(row[1])) for row in saved.connection.execute(
                        "SELECT data,first_saved_at FROM reply_information_reviews WHERE reply_id=? ORDER BY version", (reply_id,))]
                    # Event-time evidence and trusted save-time knowledge are
                    # separate gates. Backdating the claimed assessment cannot
                    # bypass a hold already visible when this request is saved.
                    for boundary in (timestamp(event["recorded_at"]), timestamp(saved_at)):
                        history = [review for review, first_saved in rows
                                   if first_saved <= boundary and timestamp(review["recorded_at"]) <= boundary]
                        if history and history[-1]["information_status"] != "public_clarification":
                            raise ValueError("Observation public evidence has a held information correction")
        snapshots.update({source_id: digest(source) for source_id, source in closure.items()})
    needs_public = (kind == "external_change" or event["assessment"].get("information_status") == "public_clarification")
    if needs_public and not refs:
        reasons.append("public_evidence_required")
    return {"status": "verified" if target_bound and not reasons else "unverified",
            "reason_codes": list(dict.fromkeys(reasons)), "source_snapshots": snapshots}


def _text_binding(basis, reference, raw_text):
    fields = {"target_text_reference", "target_text_sha256", "basis_quote"}
    if not fields <= set(basis):
        return False
    if basis["target_text_reference"] != reference:
        raise ValueError("Assessment text reference differs from its target")
    if sha256(raw_text.encode()).hexdigest() != basis["target_text_sha256"] or basis["basis_quote"] not in raw_text:
        raise ValueError("Assessment raw-text SHA or verbatim quote does not match")
    return True


def prepare_assessments(connection, record, previous, saved_at):
    """Bind new requests; reuse saved results on exact request retries."""
    result = deepcopy(record)
    old = {event["id"]: event for event in previous.get("assessments", [])}
    normalized = []; saved = _Saved(connection)
    for event in record.get("assessments", []):
        if event["id"] in old:
            existing = old[event["id"]]
            if set(event) & _SERVER:
                if event != existing:
                    raise ValueError("Saved observation assessments are immutable")
            elif event != existing["request"]:
                raise ValueError("Assessment ID reused for a different request")
            normalized.append(deepcopy(existing))
            continue
        if set(event) & _SERVER:
            raise ValueError("A caller cannot supply approval metadata for a new assessment")
        target = _target(previous, event["target_kind"], event["target_id"])
        verification = _bind(saved, previous, target, event, saved_at)
        current_record = deepcopy(previous); current_record["assessments"] = normalized
        effective, _ = assessment_view(current_record, timestamp(saved_at))
        current = original_classification(_target(effective, event["target_kind"], event["target_id"]), event["target_kind"])
        if verification["status"] != "verified":
            desired = event["assessment"]
            safe = ((event["target_kind"] == "reply" and desired["signal"] == current["signal"]
                     and desired["information_status"] in ("unclear", "potential_nonpublic"))
                    or (event["target_kind"] == "external_change" and desired["impact"] == "unresolved"))
            if not safe:
                raise ValueError("Independent saved evidence is required to reclassify or release an observation hold")
        bound = deepcopy(event)
        bound.update(request=deepcopy(event), first_saved_at=saved_at, basis_verification=verification)
        normalized.append(bound)
    if "assessments" in record:
        result["assessments"] = normalized
    return result
