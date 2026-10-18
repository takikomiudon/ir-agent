"""Trusted-runtime receipts for immutable saved records, separate from raw JSON.

Install SCHEMA on the owning connection. Mutations require the caller's open
transaction and never commit it. ``now`` is a trusted runtime argument, not a
field accepted from request JSON; this library cannot independently certify
its clock or prove that the caller actually performed a new base INSERT.

These are project persistence rules, not financial or statistical thresholds.
Origin closure, company/public-information checks and PIT record selection
remain the caller's responsibility. See docs/historical-availability-design.md.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import math

from .models import integer, json_text, object_value, text, timestamp


SCHEMA = """
CREATE TABLE IF NOT EXISTS record_availability (
    entity_type TEXT NOT NULL CHECK(entity_type IN ('source','thesis','reply','question')),
    entity_id TEXT NOT NULL,
    version INTEGER NOT NULL CHECK(typeof(version)='integer'),
    snapshot_sha256 TEXT NOT NULL CHECK(length(snapshot_sha256)=64),
    first_saved_at TEXT,
    presence_observed_at TEXT NOT NULL,
    basis TEXT NOT NULL CHECK(basis IN ('trusted_insert','legacy_presence')),
    PRIMARY KEY(entity_type,entity_id,version),
    CHECK((entity_type='thesis' AND version>=1) OR (entity_type!='thesis' AND version=0)),
    CHECK((basis='trusted_insert' AND first_saved_at IS NOT NULL
            AND first_saved_at=presence_observed_at)
        OR (basis='legacy_presence' AND first_saved_at IS NULL))
);
CREATE INDEX IF NOT EXISTS record_availability_presence
    ON record_availability(presence_observed_at);
"""

_COLUMNS = ("entity_type", "entity_id", "version", "snapshot_sha256",
            "first_saved_at", "presence_observed_at", "basis")
_TYPES = {"source", "thesis", "reply", "question"}
_RESERVED = {"first_saved_at", "presence_observed_at", "record_availability"}
_LIMITATIONS = [
    "Clock provenance is trusted runtime input, not independently certified.",
    "Receipt confirms presence of this snapshot; origin closure, company, public status and mutable-state history are separate checks.",
    "Legacy presence is a known-by bound, not a reconstructed first-save time.",
]


def _time(value, label):
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(label + " must include a timezone offset")
        value = value.isoformat()
    return timestamp(value, label)


def _key(entity_type, entity_id, version):
    if not isinstance(entity_type, str) or entity_type not in _TYPES:
        raise ValueError("Unknown availability entity_type")
    text(entity_id, "availability.entity_id")
    if entity_type == "thesis":
        integer(version, "availability.version", minimum=1)
        if version > 2**63 - 1:
            raise ValueError("Availability version exceeds SQLite's integer range")
    else:
        if version is not None:
            integer(version, "availability.version")
            if version != 0:
                raise ValueError("Unversioned availability records use version=0")
        version = 0
    return entity_type, entity_id, version


def _json_types(value, depth=0):
    if depth > 64:
        raise ValueError("Availability snapshot exceeds the JSON nesting limit")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("Availability snapshot JSON keys must be strings")
            _json_types(item, depth + 1)
    elif type(value) is list:
        for item in value:
            _json_types(item, depth + 1)
    elif type(value) not in (str, int, float, bool, type(None)):
        raise ValueError("Availability snapshot must contain only JSON values")
    elif type(value) is float and not math.isfinite(value):
        raise ValueError("Availability snapshot numbers must be finite")


def _snapshot_binding(key, snapshot):
    object_value(snapshot, "availability.snapshot")
    _json_types(snapshot)
    entity_type, entity_id, version = key
    identity = snapshot.get("company_id") if entity_type == "thesis" else snapshot.get("id")
    if identity != entity_id:
        raise ValueError("Availability snapshot identity differs from its saved key")
    if entity_type == "thesis":
        integer(snapshot.get("version"), "snapshot.version", minimum=1)
        if snapshot["version"] != version:
            raise ValueError("Availability thesis version differs from its saved key")
    try:
        return sha256(json_text(snapshot).encode("utf-8")).hexdigest()
    except (TypeError, OverflowError, UnicodeError) as error:
        raise ValueError("Availability snapshot must be finite UTF-8 JSON") from error


def _effective_fields(entity_type, snapshot):
    fields = ("retrieved_at", "published_at") if entity_type == "source" else {
        "thesis": ("recorded_at",), "reply": ("received_at",), "question": ("created_at",)
    }[entity_type]
    effective = {}
    for field in fields:
        if field == "published_at" and snapshot.get(field) is None:
            continue
        effective[field] = _time(snapshot.get(field), "snapshot." + field)
    if (entity_type == "source" and "published_at" in effective
            and effective["published_at"] > effective["retrieved_at"]):
        raise ValueError("Source cannot be retrieved before its publication")
    return effective


class RecordAvailability:
    def __init__(self, sqlite_connection):
        self.connection = sqlite_connection

    def get(self, entity_type, entity_id, *, version=None):
        """Return a detached receipt or None; no JSON metadata is inferred."""
        key = _key(entity_type, entity_id, version)
        row = self.connection.execute(
            "SELECT " + ",".join(_COLUMNS)
            + " FROM record_availability WHERE entity_type=? AND entity_id=? AND version=?", key
        ).fetchone()
        return dict(zip(_COLUMNS, row)) if row is not None else None

    def _record(self, entity_type, entity_id, snapshot, *, version, now, basis):
        if not self.connection.in_transaction:
            raise ValueError("Availability write requires the base INSERT's open transaction")
        key = _key(entity_type, entity_id, version)
        digest = _snapshot_binding(key, snapshot)
        existing = self.get(entity_type, entity_id, version=key[2])
        if existing is not None and existing["snapshot_sha256"] != digest:
            raise ValueError("Availability identity reused for a different snapshot")
        # Reopening a database must not reinterpret a saved row's declared
        # timestamps or require a forward clock just to retain its receipt.
        if basis == "legacy_presence" and existing is not None:
            return existing
        current = _time(now, "trusted runtime now")
        if basis == "trusted_insert":
            if _RESERVED & set(snapshot):
                raise ValueError("Snapshot cannot declare server availability fields")
            effective = _effective_fields(entity_type, snapshot)
            if any(value > current for value in effective.values()):
                raise ValueError("Snapshot effective time is in the future of trusted runtime now")
        # A rollback of the runtime clock must not mint an earlier receipt,
        # including one for a different record. Nothing is rewritten on retry.
        latest = self.connection.execute(
            "SELECT MAX(presence_observed_at) FROM record_availability").fetchone()[0]
        clock_issue = None
        if latest is not None:
            try:
                if _time(latest, "saved presence_observed_at") > current:
                    clock_issue = "availability_clock_anomaly"
            except (TypeError, ValueError, OverflowError):
                clock_issue = "availability_receipt_invalid"
        if clock_issue is not None:
            if basis == "legacy_presence":
                # No retrograde presence proof is minted. Existing data stays
                # readable, and later PIT reads see a missing receipt/unknown.
                return {"entity_type": key[0], "entity_id": key[1], "version": key[2],
                        "snapshot_sha256": digest, "status": "unknown",
                        "reason_codes": [clock_issue], "receipt": None}
            raise ValueError("Trusted runtime clock precedes or cannot verify saved availability history")
        saved_at = current.isoformat(timespec="microseconds")
        self.connection.execute(
            "INSERT INTO record_availability VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(entity_type,entity_id,version) DO NOTHING",
            (*key, digest, saved_at if basis == "trusted_insert" else None, saved_at, basis),
        )
        receipt = self.get(entity_type, entity_id, version=key[2])
        if receipt["snapshot_sha256"] != digest:
            raise ValueError("Availability identity reused for a different snapshot")
        # An existing legacy-presence receipt remains unknown-first-save even
        # when a later duplicate takes the new-record code path.
        return receipt

    def record_first_save(self, entity_type, entity_id, snapshot, *, version=None, now):
        """Call only after a real new INSERT, within that same transaction."""
        return self._record(entity_type, entity_id, snapshot, version=version, now=now,
                            basis="trusted_insert")

    def observe_existing(self, entity_type, entity_id, snapshot, *, version=None, now):
        """Observe raw legacy presence, not its declared event-time validity.

        Existing matching receipts are retained unchanged. A clock anomaly
        returns an unknown diagnostic without a new receipt; it must not block
        current raw reads merely because historical availability is unknown.
        """
        return self._record(entity_type, entity_id, snapshot, version=version, now=now,
                            basis="legacy_presence")

    def at(self, entity_type, entity_id, snapshot, *, version=None, as_of, knowledge_at, now):
        """Assess one snapshot on two explicit axes; does not select or mutate.

        No mode is guessed: the integration layer enforces equal cutoffs for
        strict PIT and labels explicit retrospective views separately.
        """
        key = _key(entity_type, entity_id, version)
        digest = _snapshot_binding(key, snapshot)
        event_cutoff = _time(as_of, "as_of")
        knowledge_cutoff = _time(knowledge_at, "knowledge_at")
        current = _time(now, "trusted runtime now")
        if event_cutoff > current or knowledge_cutoff > current:
            raise ValueError("Availability cutoffs cannot exceed trusted runtime now")
        receipt = self.get(entity_type, entity_id, version=key[2])
        reasons = []
        unknown = False
        try:
            effective = _effective_fields(entity_type, snapshot)
        except (TypeError, ValueError, OverflowError):
            effective = {}
            reasons.append("invalid_effective_time")
            unknown = True
        if any(value > event_cutoff for value in effective.values()):
            reasons.append("effective_time_after_as_of")
        known_by = None
        first_save_known = False
        if receipt is None:
            reasons.append("availability_receipt_missing")
            unknown = True
        else:
            if receipt["snapshot_sha256"] != digest:
                raise ValueError("Availability identity reused for a different snapshot")
            try:
                observed = _time(receipt["presence_observed_at"], "saved presence_observed_at")
                if receipt["basis"] == "trusted_insert":
                    first = _time(receipt["first_saved_at"], "saved first_saved_at")
                    if first != observed:
                        raise ValueError("Invalid trusted availability receipt")
                    first_save_known = True
                elif receipt["basis"] != "legacy_presence" or receipt["first_saved_at"] is not None:
                    raise ValueError("Invalid legacy availability receipt")
                known_by = observed.isoformat(timespec="microseconds")
                if observed > current:
                    reasons.append("availability_clock_anomaly")
                    unknown = True
                elif observed > knowledge_cutoff:
                    if first_save_known:
                        reasons.append("first_saved_after_knowledge_at")
                    else:
                        reasons.append("legacy_history_unknown")
                        unknown = True
                if first_save_known and any(value > observed for value in effective.values()):
                    reasons.append("availability_record_chronology_invalid")
                    unknown = True
            except (TypeError, ValueError, OverflowError):
                reasons.append("availability_receipt_invalid")
                unknown = True
                first_save_known = False
                known_by = None
        # Definite effective-time exclusion is still exclusion if another
        # independent check is unknown; all reasons remain visible.
        excluded = ("effective_time_after_as_of" in reasons
                    or "first_saved_after_knowledge_at" in reasons)
        status = "unavailable" if excluded else "unknown" if unknown else "available"
        return {"entity_type": key[0], "entity_id": key[1], "version": key[2],
                "snapshot_sha256": digest, "as_of": event_cutoff.isoformat(),
                "knowledge_at": knowledge_cutoff.isoformat(), "status": status,
                "available": True if status == "available" else False if status == "unavailable" else None,
                "reason_codes": reasons,
                "effective_fields": {field: value.isoformat() for field, value in effective.items()},
                "receipt": receipt, "known_by_at": known_by,
                "first_save_known": first_save_known, "limitations": list(_LIMITATIONS)}
