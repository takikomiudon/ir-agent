"""Read committed lease-attempt events into capacity inputs without writing.

Lease ownership elapsed time is not analyst activity, model usage or complete
company research. Historical jobs without measured starts remain unmeasured.
This adapter does not construct Store, initialize schema or append expiry events.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import sqlite3

from .models import integer, json_text, parse_json, text, timestamp


_KINDS = {"lease_started", "lease_renewed", "completed", "lease_expired"}


def _digest(value):
    return sha256(json_text(value).encode("utf-8")).hexdigest()


def _hash(value, label):
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(label + " must be a lowercase SHA-256")


def _object(value, label):
    if not isinstance(value, dict):
        raise ValueError(label + " must be an object")
    return value


def _time(value, label):
    return timestamp(value, label)


def _event_view(row, cutoff):
    if _time(row["first_saved_at"], "event row save time") > cutoff:
        return None
    value = _object(parse_json(row["data"]), "attempt event")
    observed = _time(value.get("observed_at"), "event.observed_at")
    saved = _time(value.get("first_saved_at"), "event.first_saved_at")
    if observed > cutoff or saved > cutoff:
        return None
    for key, column in (("id", "event_id"), ("attempt_id", "attempt_id"),
                        ("sequence", "sequence"), ("kind", "kind")):
        if value.get(key) != row[column]:
            raise ValueError("event_column_mismatch:" + key)
    integer(value.get("sequence"), "event.sequence", minimum=1)
    text(value.get("id"), "event.id")
    if not isinstance(value.get("kind"), str) or value["kind"] not in _KINDS:
        raise ValueError("unknown_event_kind")
    if saved != _time(row["first_saved_at"], "event row save time"):
        raise ValueError("event_save_time_mismatch")
    if type(value.get("normal_interval")) is not bool or not isinstance(value.get("clock_issues"), list):
        raise ValueError("invalid_event_clock_metadata")
    if any(not isinstance(item, str) for item in value["clock_issues"]):
        raise ValueError("invalid_event_clock_issues")
    _object(value.get("payload"), "event.payload")
    _time(value.get("effective_at"), "event.effective_at")
    return value


def _stage(header, job):
    packet = _object(parse_json(job["packet"]), "saved packet")
    _hash(header.get("packet_sha256"), "packet_sha256")
    if _digest(packet) != header["packet_sha256"]:
        raise ValueError("packet_hash_mismatch")
    kind = packet.get("kind")
    if kind is None and "thesis" in packet:
        kind = "research"
    stage = packet.get("stage")
    kind = kind if isinstance(kind, str) and kind.strip() else None
    stage = stage if isinstance(stage, str) and stage.strip() else None
    for key, expected in (("job_kind", kind), ("stage", stage)):
        if key in header and header[key] != expected:
            raise ValueError("header_packet_mismatch:" + key)
    unknown = [key for key, value in (("job_kind", kind), ("stage", stage)) if value is None]
    return "lease:" + (kind or "unknown") + ":" + (stage or "unknown"), unknown


def _project(header_row, event_rows, jobs, all_headers, cutoff):
    audit = {"attempt_id": header_row["attempt_id"], "job_id": header_row["job_id"],
             "generation": header_row["generation"], "projection_status": "excluded",
             "exclusion_reasons": [], "warnings": [], "used_events": [], "clock_issues": []}
    try:
        header = _object(parse_json(header_row["data"]), "attempt header")
        start = _time(header.get("started_at"), "header.started_at")
        saved = _time(header.get("first_saved_at"), "header.first_saved_at")
        if start > cutoff or saved > cutoff:
            return None, None
        audit.update(company_id=header.get("company_id"), worker_id=header.get("worker_id"),
                     worker_session_id=header.get("worker_session_id"), synthetic=header.get("synthetic"),
                     measurement_scope=header.get("measurement_scope"), started_at=header.get("started_at"),
                     first_saved_at=header.get("first_saved_at"), packet_sha256=header.get("packet_sha256"),
                     previous_measured_attempt=header.get("previous_measured_attempt"))
        for key, column in (("id", "attempt_id"), ("job_id", "job_id"), ("generation", "generation")):
            if header.get(key) != header_row[column]:
                raise ValueError("header_column_mismatch:" + key)
        integer(header.get("generation"), "header.generation", minimum=1)
        for key in ("id", "job_id", "company_id", "worker_id"):
            text(header.get(key), "header." + key)
        if header.get("measurement_scope") != "lease_ownership":
            raise ValueError("unknown_measurement_scope")
        if saved != _time(header_row["first_saved_at"], "header row save time"):
            raise ValueError("header_save_time_mismatch")
        if type(header.get("synthetic")) is not bool:
            raise ValueError("synthetic_status_unknown")
        session = header.get("worker_session_id")
        if session is not None:
            text(session, "worker_session_id")
        audit.update(worker_id=header["worker_id"], worker_session_id=session,
                     synthetic=header["synthetic"], started_at=header["started_at"],
                     first_saved_at=header["first_saved_at"], previous_measured_attempt=header.get("previous_measured_attempt"))
        if header["job_id"] not in jobs:
            raise ValueError("job_not_found")
        job = jobs[header["job_id"]]
        if job["company_id"] != header["company_id"]:
            raise ValueError("job_company_mismatch")
        integer(job["attempts"], "jobs.attempts")
        if header["generation"] > job["attempts"]:
            raise ValueError("generation_exceeds_job_counter")
        previous = header.get("previous_measured_attempt")
        if previous is not None:
            _object(previous, "previous_measured_attempt")
            if set(previous) != {"id", "generation"}:
                raise ValueError("invalid_previous_measured_attempt")
            integer(previous["generation"], "previous generation", minimum=1)
            row = all_headers.get(previous["id"])
            if (row is None or row["job_id"] != header["job_id"] or row["generation"] != previous["generation"]
                    or previous["generation"] >= header["generation"]):
                raise ValueError("invalid_previous_measured_attempt")
        stage, unknown = _stage(header, job)
        audit.update(stage=stage, unknown_stage_components=unknown)
        if unknown:
            audit["warnings"].append("stage_components_unknown")
        visible = []
        for row in event_rows:
            event = _event_view(row, cutoff)
            if event is not None:
                visible.append(event)
        if not visible or visible[0]["kind"] != "lease_started":
            raise ValueError("missing_visible_start_event")
        lease = terminal = None
        last_observed, last_saved = start, saved
        for index, event in enumerate(visible, 1):
            audit["used_events"].append({"id": event["id"], "sequence": event["sequence"],
                                          "kind": event["kind"], "observed_at": event["observed_at"],
                                          "first_saved_at": event["first_saved_at"], "sha256": _digest(event)})
            if event["sequence"] != index:
                raise ValueError("visible_events_are_not_a_contiguous_prefix")
            if terminal is not None:
                raise ValueError("event_after_lease_terminal")
            observed = _time(event["observed_at"], "observed_at")
            event_saved = _time(event["first_saved_at"], "first_saved_at")
            effective = _time(event["effective_at"], "effective_at")
            issues = list(event["clock_issues"])
            if not event["normal_interval"]:
                issues.append("normal_interval_false")
            if observed < last_observed or event_saved < last_saved or event_saved < observed or effective < start:
                issues.append("clock_order_invalid")
            if effective > observed:
                issues.append("effective_time_after_observation")
            audit["clock_issues"] += [issue for issue in issues if issue not in audit["clock_issues"]]
            payload = event["payload"]
            lease_until = _time(payload.get("lease_until"), "payload.lease_until")
            kind = event["kind"]
            if kind == "lease_started":
                if index != 1 or observed != start or effective != start or lease_until <= start:
                    raise ValueError("invalid_start_event")
                lease = lease_until
            elif kind == "lease_renewed":
                if (_time(payload.get("previous_lease_until"), "previous_lease_until") != lease
                        or observed >= lease or lease_until <= observed or effective != observed):
                    raise ValueError("invalid_renewal_chain")
                lease = lease_until
            else:
                if lease_until != lease:
                    raise ValueError("terminal_lease_mismatch")
                if kind == "completed":
                    _hash(payload.get("result_sha256"), "result_sha256")
                    completed = _time(payload.get("completed_at"), "completed_at")
                    if effective != completed or completed >= lease:
                        raise ValueError("invalid_completion_time")
                    if job["attempts"] == header["generation"] and job["status"] == "completed":
                        if (job["result"] is None or _digest(parse_json(job["result"])) != payload["result_sha256"]
                                or _time(job["completed_at"], "job.completed_at") != completed):
                            raise ValueError("terminal_result_or_completion_mismatch")
                        audit["terminal_result_verification"] = {"status": "matched_current_job_snapshot"}
                    else:
                        audit["terminal_result_verification"] = {
                            "status": "not_resolved",
                            "reason": "current_job_generation_or_status_no_longer_retains_this_completion"}
                    terminal = ("completed", effective, event)
                else:
                    if effective != lease or observed < lease:
                        raise ValueError("invalid_expiry_time")
                    terminal = ("failed", lease, event)
            last_observed, last_saved = observed, event_saved
        audit.update(latest_lease_until=lease.isoformat(), planned_lease_exceeded_as_of=cutoff >= lease,
                     termination_reason=terminal[2]["kind"] if terminal else None,
                     terminal_observed_at=terminal[2]["observed_at"] if terminal else None)
        if start > saved:
            audit["clock_issues"].append("header_started_after_save")
        if audit["clock_issues"]:
            raise ValueError("clock_anomaly")
        measurement = {"id": header["id"], "attempt_id": header["id"], "company_id": header["company_id"],
                       "worker_id": header["worker_id"], "stage": stage,
                       "started_at": header["started_at"], "ended_at": terminal[1].isoformat() if terminal else None,
                       "status": terminal[0] if terminal else "in_progress", "synthetic": header["synthetic"],
                       "active_seconds": None, "tokens": None, "cost": None}
        audit["projection_status"] = "included"
        if terminal is None and cutoff >= lease:
            audit["warnings"].append("planned_lease_exceeded_without_saved_terminal")
        return measurement, audit
    except (ValueError, TypeError, KeyError, OverflowError) as error:
        audit["exclusion_reasons"].append(str(error))
        return None, audit


def build_attempt_measurements(db_path, *, as_of: str, window: dict, operator_capacity: dict | None = None) -> dict:
    """Project one record per visible normal lease attempt in a read-only snapshot.

    A missing/partial ledger returns measurements=None; an existing empty ledger
    returns []. The explicit window must end by as_of. All visible attempts are
    passed through; capacity owns clipping and outside-window counts. Unknown
    synthetic status and anomalous clocks are excluded with audit reasons.
    """
    cutoff = _time(as_of, "as_of")
    if not isinstance(window, dict) or set(window) != {"started_at", "ended_at"}:
        raise ValueError("window must explicitly contain started_at and ended_at")
    start, end = _time(window["started_at"], "window start"), _time(window["ended_at"], "window end")
    if not start < end <= cutoff:
        raise ValueError("window must have positive duration and end no later than as_of")
    if operator_capacity is not None and not isinstance(operator_capacity, dict):
        raise ValueError("operator_capacity must be an explicit object")
    path = Path(db_path).resolve()
    try:
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, isolation_level=None)
    except sqlite3.Error as error:
        raise ValueError("Cannot open existing database read-only") from error
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        jobs = {row["id"]: dict(row) for row in connection.execute("SELECT id,company_id,status,attempts,result,completed_at,packet FROM jobs ORDER BY id")} if "jobs" in tables else {}
        present = {name: name in tables for name in ("jobs", "job_attempts", "job_attempt_events")}
        ledger_available = all(present.values())
        headers = [dict(row) for row in connection.execute("SELECT attempt_id,job_id,generation,data,first_saved_at FROM job_attempts ORDER BY job_id,generation")] if present["job_attempts"] else []
        events = [dict(row) for row in connection.execute("SELECT event_id,attempt_id,sequence,kind,data,first_saved_at FROM job_attempt_events ORDER BY attempt_id,sequence")] if present["job_attempt_events"] else []
        events_by_attempt = {}
        for row in events:
            events_by_attempt.setdefault(row["attempt_id"], []).append(row)
        all_headers = {row["attempt_id"]: row for row in headers}
        measurements, audits, not_visible = [], [], 0
        for row in headers:
            try:
                if _time(row["first_saved_at"], "header row save time") > cutoff:
                    not_visible += 1
                    continue
            except ValueError as error:
                audits.append({"attempt_id": row["attempt_id"], "job_id": row["job_id"],
                               "projection_status": "excluded", "exclusion_reasons": [str(error)]})
                continue
            if not ledger_available:
                continue
            measurement, audit = _project(row, events_by_attempt.get(row["attempt_id"], []), jobs, all_headers, cutoff)
            if audit is None:
                not_visible += 1
            else:
                audits.append(audit)
            if measurement is not None:
                measurements.append(measurement)
        measured_job_ids = {row["job_id"] for row in headers}
        unmeasured = [{"job_id": row["id"], "company_id": row["company_id"],
                       "current_snapshot_status": row["status"], "current_snapshot_completed_at": row["completed_at"],
                       "current_attempts_counter": row["attempts"], "reason": "no_saved_attempt_header"}
                      for row in jobs.values() if row["id"] not in measured_job_ids]
        request = {"schema_version": 1, "window": deepcopy(window), "measurements": measurements if ledger_available else None}
        if operator_capacity is not None:
            request["operator_capacity"] = deepcopy(operator_capacity)
        orphans = []
        if ledger_available:
            for row in events:
                if row["attempt_id"] in all_headers:
                    continue
                try:
                    event = _event_view(row, cutoff)
                    if event is None:
                        continue
                    reason = "event_without_attempt_header"
                except (ValueError, TypeError) as error:
                    reason = str(error)
                orphans.append({"event_id": row["event_id"], "attempt_id": row["attempt_id"], "reason": reason})
        input_fingerprint = {"headers": headers, "events": events, "jobs": list(jobs.values())}
        audit = {
            "as_of": cutoff.isoformat(), "measurement_scope": "lease_ownership",
            "table_status": {name: "present" if available else "absent" for name, available in present.items()},
            "ledger_status": "available" if ledger_available else "unavailable_or_partial_schema",
            "snapshot": {"database_path": str(path), "read_only": True,
                         "query_only": bool(connection.execute("PRAGMA query_only").fetchone()[0]),
                         "sqlite_data_version": connection.execute("PRAGMA data_version").fetchone()[0],
                         "committed_snapshot_sha256": _digest(input_fingerprint), "write_count": connection.total_changes},
            "counts": {"stored_header_rows_current_snapshot": len(headers) if present["job_attempts"] else None,
                       "not_yet_visible_headers": not_visible if ledger_available else None,
                       "projected_attempts": len(measurements) if ledger_available else None,
                       "excluded_attempts": sum(a["projection_status"] == "excluded" for a in audits) if ledger_available else None,
                       "unmeasured_jobs_current_snapshot": len(unmeasured) if present["jobs"] else None,
                       "orphan_events": len(orphans) if ledger_available else None},
            "exclusion_counts": dict(Counter(reason for item in audits for reason in item["exclusion_reasons"])),
            "attempts": audits, "orphan_events": orphans,
            "unmeasured_jobs": unmeasured if present["jobs"] else None,
            "limitations": [
                "Elapsed intervals measure lease ownership, not active analysis, process termination, model usage or complete company research. Active seconds, tokens and cost remain null.",
                "Only saved and observed events visible at as_of are projected. Passing a planned lease deadline does not append an expiry or supply a terminal event.",
                "Job status/counters and unmeasured-job inventory describe the current committed DB snapshot, not reconstructed job states at historical as_of.",
                "first_saved_at is the recording operation time, not proof of the exact outer-transaction commit time. Data version/fingerprint identify this read; they do not reconstruct past concurrent visibility.",
                "No company-count limit, worker-scaling estimate, operator budget, likelihood, model execution or financial analysis is supplied.",
            ],
        }
        return {"schema_version": 1, "projection_version": 1, "capacity_request": request, "audit": audit}
    except sqlite3.Error as error:
        raise ValueError("Existing attempt schema cannot be read consistently: " + str(error)) from error
    finally:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        connection.close()
