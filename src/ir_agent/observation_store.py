"""Immutable observation snapshots with fixed ex-ante design and append CAS.

Install SCHEMA on the supplied connection before constructing ObservationStore.
Methods preserve an outer transaction using a savepoint; standalone mutations
take an immediate write transaction. ``now`` is supplied by the trusted caller,
never read from the observation JSON.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
import sqlite3

from .models import integer, json_text, text, timestamp
from .observations import summarize_observations, validate_observation
from .observation_assessments import prepare_assessments


SCHEMA = """
CREATE TABLE IF NOT EXISTS ir_observations (
    id TEXT PRIMARY KEY, company_id TEXT NOT NULL, question_id TEXT NOT NULL,
    design_sha256 TEXT NOT NULL, first_saved_at TEXT NOT NULL,
    UNIQUE(company_id,question_id)
);
CREATE TABLE IF NOT EXISTS ir_observation_versions (
    observation_id TEXT NOT NULL REFERENCES ir_observations(id),
    version INTEGER NOT NULL CHECK(version>=1), design_sha256 TEXT NOT NULL,
    data TEXT NOT NULL, first_saved_at TEXT NOT NULL,
    PRIMARY KEY(observation_id,version)
);
"""

_MUTABLE = {"dispatch", "response_check", "verification", "replies", "external_changes", "assessments"}


def _saved_time(value):
    return timestamp(value, "trusted now").isoformat(timespec="microseconds")


def _design_hash(record):
    return sha256(json_text({k: v for k, v in record.items() if k not in _MUTABLE}).encode()).hexdigest()


def _not_future(record, now):
    fields = [("question_created_at", record["question_created_at"]), ("design_recorded_at", record["design_recorded_at"])]
    for evidence in record["premise_evidence"]:
        fields.extend((key, evidence[key]) for key in ("published_at", "retrieved_at"))
    for field, event_keys in (("dispatch", ("attempted_at", "recorded_at")),
                              ("response_check", ("checked_through", "recorded_at")),
                              ("verification", ("recorded_at",))):
        event = record.get(field)
        if event is not None:
            fields.extend((field + "." + key, event[key]) for key in event_keys)
    for reply in record["replies"]:
        fields.extend(("reply." + key, reply[key]) for key in ("received_at", "recorded_at"))
    for change in record["external_changes"]:
        fields.extend(("external_change." + key, change[key]) for key in ("occurred_at", "recorded_at"))
    for assessment in record.get("assessments", []):
        fields.append(("assessment.recorded_at", assessment["recorded_at"]))
        if assessment.get("first_saved_at") is not None:
            fields.append(("assessment.first_saved_at", assessment["first_saved_at"]))
    if record.get("verification") is not None:
        for evidence in record["verification"]["evidence"]:
            fields.extend(("verification.evidence." + key, evidence[key]) for key in ("published_at", "retrieved_at"))
    for field, value in fields:
        if timestamp(value) > now:
            raise ValueError(field + " cannot be recorded in the future")


class ObservationStore:
    def __init__(self, sqlite_connection: sqlite3.Connection):
        self.connection = sqlite_connection

    @contextmanager
    def _atomic(self):
        nested = self.connection.in_transaction
        self.connection.execute("SAVEPOINT ir_observation_mutation" if nested else "BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            if nested:
                self.connection.execute("ROLLBACK TO SAVEPOINT ir_observation_mutation")
                self.connection.execute("RELEASE SAVEPOINT ir_observation_mutation")
            else:
                self.connection.execute("ROLLBACK")
            raise
        else:
            self.connection.execute("RELEASE SAVEPOINT ir_observation_mutation" if nested else "COMMIT")

    def _versions(self, observation_id):
        return self.connection.execute(
            "SELECT observation_id,version,design_sha256,data,first_saved_at FROM ir_observation_versions WHERE observation_id=? ORDER BY version",
            (observation_id,)).fetchall()

    @staticmethod
    def _envelope(row, added=False):
        return {"id": row[0], "version": row[1], "design_sha256": row[2], "record": json.loads(row[3]),
                "first_saved_at": row[4], "added": added}

    def history(self, observation_id: str) -> list[dict]:
        text(observation_id, "observation ID")
        rows = self._versions(observation_id)
        if not rows:
            raise ValueError("Unknown observation ID")
        return [self._envelope(row) for row in rows]

    def records_as_of(self, as_of: str) -> list[dict]:
        boundary = _saved_time(as_of)
        rows = self.connection.execute(
            "SELECT v.data FROM ir_observation_versions v JOIN "
            "(SELECT observation_id,MAX(version) AS version FROM ir_observation_versions WHERE first_saved_at<=? GROUP BY observation_id) latest "
            "ON latest.observation_id=v.observation_id AND latest.version=v.version ORDER BY v.observation_id", (boundary,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def _population_check(self, record, now):
        # Structural identity/cohort checks use every current record, including
        # those recorded after an injected historical test clock. The analytical
        # API records_as_of is the separate visibility boundary.
        rows = self.connection.execute(
            "SELECT v.data FROM ir_observation_versions v JOIN "
            "(SELECT observation_id,MAX(version) AS version FROM ir_observation_versions GROUP BY observation_id) latest "
            "ON latest.observation_id=v.observation_id AND latest.version=v.version WHERE v.observation_id<>?", (record["id"],)).fetchall()
        summarize_observations([json.loads(row[0]) for row in rows] + [record], as_of=now)

    def register(self, record: dict, now: str) -> dict:
        value = validate_observation(record)
        saved = _saved_time(now); current = timestamp(saved)
        _not_future(value, current)
        if value.get("assessments"):
            raise ValueError("Register targets first, then append their observation assessments")
        encoded = json_text(value)
        with self._atomic():
            existing = self._versions(value["id"])
            if existing:
                if existing[0][3] != encoded:
                    raise ValueError("An observation ID is already registered with an immutable initial design/snapshot")
                if current < timestamp(existing[0][4]):
                    raise ValueError("A retry cannot predate its first saved record")
                return self._envelope(existing[0])
            if not value.get("synthetic", False):
                dispatch = value.get("dispatch")
                if dispatch is not None and timestamp(dispatch["attempted_at"]) < current:
                    raise ValueError("Register a real observation design before dispatch; past sent records are not ex-ante designs")
                verification_status = (value.get("verification") or {}).get("status")
                if value["replies"] or verification_status not in {None, "pending"}:
                    raise ValueError("A real design cannot be initially registered after a reply or adjudicated outcome")
            self._population_check(value, saved)
            digest = _design_hash(value)
            try:
                self.connection.execute("INSERT INTO ir_observations VALUES (?,?,?,?,?)",
                                        (value["id"], value["company_id"], value["question_id"], digest, saved))
                self.connection.execute("INSERT INTO ir_observation_versions VALUES (?,?,?,?,?)", (value["id"], 1, digest, encoded, saved))
            except sqlite3.IntegrityError as error:
                raise ValueError("Observation or company/question identity is already registered") from error
            return self._envelope(self._versions(value["id"])[0], added=True)

    def append(self, record: dict, expected_version: int, now: str) -> dict:
        integer(expected_version, "expected_version", minimum=1)
        value = validate_observation(record)
        saved = _saved_time(now); current = timestamp(saved)
        _not_future(value, current)
        encoded = json_text(value)
        with self._atomic():
            versions = self._versions(value["id"])
            if not versions:
                raise ValueError("Register the observation design before appending outcomes")
            latest = versions[-1]
            if current < timestamp(latest[4]):
                raise ValueError("Observation save times must be monotone")
            old = json.loads(latest[3])
            value = validate_observation(prepare_assessments(self.connection, value, old, saved))
            encoded = json_text(value)
            if encoded == latest[3]:
                if expected_version not in {latest[1], latest[1]-1}:
                    raise ValueError("Stale observation version")
                return self._envelope(latest)
            if latest[1] != expected_version:
                raise ValueError("Stale observation version; review the latest immutable snapshot")
            if _design_hash(value) != latest[2]:
                raise ValueError("Observation design, hypotheses, signal rules, deadlines, identity and priors are immutable")
            previous_save = timestamp(latest[4])
            for field in ("replies", "external_changes", "assessments"):
                before, after = old.get(field, []), value.get(field, [])
                if after[:len(before)] != before:
                    raise ValueError(field + " history must be prefix-only; saved events cannot be edited or removed")
                for event in after[len(before):]:
                    if timestamp(event["recorded_at"]) < previous_save:
                        raise ValueError("New events cannot be backdated before the previous snapshot")
            for field in ("dispatch", "response_check", "verification"):
                before, after = old.get(field), value.get(field)
                if before == after:
                    continue
                if after is None:
                    raise ValueError("Saved " + field + " cannot be removed")
                when = timestamp(after["recorded_at"])
                if when < previous_save or (before is not None and when <= timestamp(before["recorded_at"])):
                    raise ValueError("Changed " + field + " needs a new monotone record time")
                if field == "dispatch":
                    if not value.get("synthetic", False) and timestamp(after["attempted_at"]) < timestamp(versions[0][4]):
                        raise ValueError("Real dispatch cannot predate initial design registration")
                    if before is not None and (after["attempted_at"] != before["attempted_at"] or before["status"] != "unknown"):
                        raise ValueError("Dispatch attempt is immutable; only unknown delivery status may be resolved")
                elif field == "response_check" and before is not None:
                    if timestamp(after["checked_through"]) < timestamp(before["checked_through"]):
                        raise ValueError("Response-check coverage cannot move backwards")
            self._population_check(value, saved)
            version = latest[1] + 1
            self.connection.execute("INSERT INTO ir_observation_versions VALUES (?,?,?,?,?)", (value["id"], version, latest[2], encoded, saved))
            return self._envelope(self._versions(value["id"])[-1], added=True)
