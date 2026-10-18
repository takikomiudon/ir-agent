"""Record-only, immutable commitments to an IR evaluation procedure.

Install ``SCHEMA`` on the supplied SQLite connection separately. This module
does not resolve observation/cohort, model, source, quote or author references,
build reviewer packets, execute rules, choose state/signal labels, or call a
scorer or investment policy. The protocol registry and its API are project
adaptations described in docs/evaluation-protocol-design.md; a proper scoring
rule does not establish that an IR label or blind review procedure is valid.

``register(request, expected_previous_version, *, now)`` accepts exactly:

* id, version: protocol identity and explicit consecutive version, starting at 1.
* recorded_at, recorded_by: an aware claimed recording time and recorder label.
  The runtime supplies aware ``now`` outside the JSON. Only recorded_at <= now
  is checked. Neither a historical recorded_at nor this registration proves
  that the protocol preceded any prediction, dispatch, reply or outcome.
* evaluation_task: nullable prose identifying the evaluation question. It must
  distinguish conditional signal forecasting from posterior, EVSI or PnL tasks
  in the eventual procedure; this module does not interpret that prose.
* cohort: null, or the fixed keys in COHORT_FIELDS. Scalar fields may be null;
  states/signals are null or nonempty name-to-definition maps. target_period
  is null or a complete {start, end} date range. synthetic is true/false/null.
  These are claimed existing definitions, not resolved or verified bindings.
* model_refs: a list of {id, version, commitment_sha256,
  training_information_cutoff}. The latter two may be null. Cutoff format is
  checked, not actual training or historical information availability.
* rules: exactly RULE_FIELDS, each null or nonempty procedural prose. Text may
  describe selections, comparisons, exclusions or missingness; it is not code,
  an approval assertion, a verified rule or an automatic adoption instruction.
* source_refs: a list of {source_id, content_sha256, quote_ids, purpose}. Hash
  may be null, quote_ids may be empty. Hashes and quote IDs remain declarations:
  no source retrieval, quote check or author-principle adoption occurs here.

All keys must be present, including nulls and empty reference lists in a draft.
Unknown keys, approval/blind/independence booleans, and caller-supplied trusted
clock fields are rejected by the fixed structure. Nulls and empty reference
lists are reported as unset; no missing rule, probability or number is filled.
``draft`` reports only these syntactic gaps, never substantive readiness.

An exact ID/version/request retry uses its original expected_previous_version
and returns the original record even after later versions exist. New content
requires latest+1 and CAS against latest. Existing versions are never updated.
The trusted first-save clock must not reverse within this registry; this is
not a guarantee against a silent database restore or a compromised clock.
An outer transaction is preserved with a savepoint; otherwise an immediate
transaction is committed by this module. No other tables are read or written.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import re
import sqlite3

from .models import day, integer, json_text, timestamp


SCHEMA = """
CREATE TABLE IF NOT EXISTS ir_evaluation_protocol_versions (
    protocol_id TEXT NOT NULL,
    version INTEGER NOT NULL CHECK(version>=1),
    request_sha256 TEXT NOT NULL,
    data TEXT NOT NULL,
    first_saved_at TEXT NOT NULL,
    PRIMARY KEY(protocol_id,version)
);
"""

COHORT_FIELDS = frozenset({
    "id", "design_version", "definition_sha256", "state_timing", "target_period",
    "question_type", "states", "signals", "synthetic",
})
RULE_FIELDS = frozenset({
    "inclusion", "state", "signal", "information_separation", "no_response",
    "external_change", "correction", "group_time", "prediction_selection",
    "population_output",
})
_REQUEST_FIELDS = {
    "id", "version", "recorded_at", "recorded_by", "evaluation_task", "cohort",
    "model_refs", "rules", "source_refs",
}
_LIMITATIONS = (
    "Record-only commitment: rules are neither executed nor checked for correctness; no state, signal, score, model fitting or investment decision is produced.",
    "Cohort/model/source existence, definition agreement, source hashes, quote IDs and author-principle adoption are unverified declarations, not resolved evidence.",
    "A trusted first-save time and a claimed recorded_at do not establish prospective registration; existing replies, outcomes, exposure, training availability, blind review and independence are not inspected.",
    "draft and unset_fields describe missing syntax only; filling every field does not establish evaluation readiness or score eligibility.",
)


def _fields(value, expected, path):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError(f"{path} must contain exactly {sorted(expected)!r}; unknown fields are rejected")
    return value


def _text(value, path):
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(path + " must be nonempty text without surrounding whitespace")


def _hash(value, path):
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(path + " must be a lowercase SHA-256")


def _json_types(value, depth=0):
    if depth > 64:
        raise ValueError("Protocol JSON exceeds the nesting resource limit")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("Protocol JSON object keys must be strings")
            _json_types(item, depth + 1)
    elif type(value) is list:
        for item in value:
            _json_types(item, depth + 1)
    elif type(value) not in (str, int, float, bool, type(None)):
        raise ValueError("Protocol must contain only JSON values")
    elif type(value) is float and not math.isfinite(value):
        raise ValueError("Protocol JSON numbers must be finite")


def _encode(value):
    _json_types(value)
    try:
        encoded = json_text(value)
        if len(encoded.encode("utf-8")) > 2 * 1024 * 1024:
            raise ValueError("Protocol JSON exceeds the 2 MiB resource limit")
        return encoded
    except (TypeError, OverflowError, UnicodeError) as error:
        raise ValueError("Protocol must be finite UTF-8 JSON") from error


def _runtime_time(now):
    if isinstance(now, datetime):
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("trusted now must include a timezone offset")
        try:
            return now.astimezone(timezone.utc)
        except OverflowError as error:
            raise ValueError("trusted now is outside the supported UTC datetime range") from error
    return timestamp(now, "trusted now")


def _definitions(value, path):
    if type(value) is not dict or not value:
        raise ValueError(path + " must be a nonempty name-to-definition object or null")
    for name, definition in value.items():
        _text(name, path + " name")
        _text(definition, path + "." + name)


def _list(value, path):
    if type(value) is not list:
        raise ValueError(path + " must be a list")
    return value


def _validate(request):
    _fields(request, _REQUEST_FIELDS, "protocol")
    _text(request["id"], "id")
    integer(request["version"], "version", minimum=1)
    _text(request["recorded_by"], "recorded_by")
    recorded = timestamp(request["recorded_at"], "recorded_at")
    unset = []

    def nullable(value, path, validator):
        if value is None:
            unset.append(path)
        else:
            validator(value, path)

    nullable(request["evaluation_task"], "evaluation_task", _text)
    cohort = request["cohort"]
    if cohort is None:
        unset.append("cohort")
    else:
        _fields(cohort, COHORT_FIELDS, "cohort")
        for key in ("id", "question_type"):
            nullable(cohort[key], "cohort." + key, _text)
        nullable(cohort["design_version"], "cohort.design_version",
                 lambda v, p: integer(v, p, minimum=1))
        nullable(cohort["definition_sha256"], "cohort.definition_sha256", _hash)
        if cohort["state_timing"] is None:
            unset.append("cohort.state_timing")
        elif (type(cohort["state_timing"]) is not str
              or cohort["state_timing"] not in {"at_question", "future_outcome"}):
            raise ValueError("cohort.state_timing must be at_question, future_outcome or null")
        for key in ("states", "signals"):
            nullable(cohort[key], "cohort." + key, _definitions)
        period = cohort["target_period"]
        if period is None:
            unset.append("cohort.target_period")
        else:
            _fields(period, {"start", "end"}, "cohort.target_period")
            if day(period["end"], "cohort.target_period.end") < day(period["start"], "cohort.target_period.start"):
                raise ValueError("cohort.target_period ends before it starts")
        if cohort["synthetic"] is None:
            unset.append("cohort.synthetic")
        elif type(cohort["synthetic"]) is not bool:
            raise ValueError("cohort.synthetic must be boolean or null")

    models = _list(request["model_refs"], "model_refs")
    if not models:
        unset.append("model_refs")
    identities = set()
    for index, model in enumerate(models):
        path = f"model_refs[{index}]"
        _fields(model, {"id", "version", "commitment_sha256", "training_information_cutoff"}, path)
        _text(model["id"], path + ".id")
        integer(model["version"], path + ".version", minimum=1)
        identity = (model["id"], model["version"])
        if identity in identities:
            raise ValueError("model_refs contains a duplicate model ID/version")
        identities.add(identity)
        nullable(model["commitment_sha256"], path + ".commitment_sha256", _hash)
        nullable(model["training_information_cutoff"], path + ".training_information_cutoff", timestamp)

    rules = _fields(request["rules"], RULE_FIELDS, "rules")
    for key in sorted(RULE_FIELDS):
        nullable(rules[key], "rules." + key, _text)

    sources = _list(request["source_refs"], "source_refs")
    if not sources:
        unset.append("source_refs")
    identities = set()
    for index, source in enumerate(sources):
        path = f"source_refs[{index}]"
        _fields(source, {"source_id", "content_sha256", "quote_ids", "purpose"}, path)
        _text(source["source_id"], path + ".source_id")
        if source["source_id"] in identities:
            raise ValueError("source_refs contains a duplicate source ID")
        identities.add(source["source_id"])
        nullable(source["content_sha256"], path + ".content_sha256", _hash)
        _text(source["purpose"], path + ".purpose")
        quotes = _list(source["quote_ids"], path + ".quote_ids")
        if not quotes:
            unset.append(path + ".quote_ids")
        for quote in quotes:
            _text(quote, path + ".quote_ids entry")
        if len(set(quotes)) != len(quotes):
            raise ValueError(path + ".quote_ids contains duplicates")
    return recorded, sorted(unset)


class EvaluationProtocols:
    """Store unverified procedural commitments, with immutable version CAS."""

    def __init__(self, sqlite_connection: sqlite3.Connection):
        self.connection = sqlite_connection

    @contextmanager
    def _atomic(self):
        nested = self.connection.in_transaction
        self.connection.execute("SAVEPOINT ir_evaluation_protocol_mutation" if nested else "BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            if nested:
                self.connection.execute("ROLLBACK TO SAVEPOINT ir_evaluation_protocol_mutation")
                self.connection.execute("RELEASE SAVEPOINT ir_evaluation_protocol_mutation")
            else:
                self.connection.execute("ROLLBACK")
            raise
        else:
            self.connection.execute("RELEASE SAVEPOINT ir_evaluation_protocol_mutation" if nested else "COMMIT")

    def _row(self, protocol_id, version):
        return self.connection.execute(
            "SELECT data,request_sha256,first_saved_at FROM ir_evaluation_protocol_versions "
            "WHERE protocol_id=? AND version=?", (protocol_id, version)).fetchone()

    @staticmethod
    def _envelope(row, *, added=False):
        return {**json.loads(row[0]), "request_sha256": row[1],
                "first_saved_at": row[2], "added": added}

    def history(self, protocol_id: str) -> list[dict]:
        _text(protocol_id, "protocol ID")
        rows = self.connection.execute(
            "SELECT data,request_sha256,first_saved_at FROM ir_evaluation_protocol_versions "
            "WHERE protocol_id=? ORDER BY version", (protocol_id,)).fetchall()
        if not rows:
            raise ValueError("Unknown evaluation protocol ID")
        return [self._envelope(row) for row in rows]

    def show(self, protocol_id: str, version: int | None = None) -> dict:
        _text(protocol_id, "protocol ID")
        if version is None:
            return self.history(protocol_id)[-1]
        integer(version, "version", minimum=1)
        row = self._row(protocol_id, version)
        if row is None:
            raise ValueError("Unknown evaluation protocol ID/version")
        return self._envelope(row)

    def register(self, request: dict, expected_previous_version: int, *, now: str | datetime) -> dict:
        """Save a declaration only; late registration is not made prospective.

        ``now`` belongs to the trusted runtime, not the user JSON. All external
        reference and procedural validity claims remain unverified, including
        when these fields are syntactically filled or recorded_at is old.
        """
        encoded = _encode(request)
        value = json.loads(encoded)
        recorded, unset = _validate(value)
        integer(expected_previous_version, "expected_previous_version", minimum=0)
        if expected_previous_version != value["version"] - 1:
            raise ValueError("expected_previous_version must equal request.version - 1")
        current = _runtime_time(now)
        if recorded > current:
            raise ValueError("recorded_at cannot be in the future relative to trusted now")
        saved = current.isoformat(timespec="microseconds")
        digest = sha256(encoded.encode("utf-8")).hexdigest()
        with self._atomic():
            existing = self._row(value["id"], value["version"])
            if existing is not None:
                if existing[1] != digest or _encode(json.loads(existing[0])["request"]) != encoded:
                    raise ValueError("Protocol ID/version is immutable and already has different content")
                if current < timestamp(existing[2]):
                    raise ValueError("A retry cannot predate its first saved record")
                return self._envelope(existing)

            latest = self.connection.execute(
                "SELECT MAX(version) FROM ir_evaluation_protocol_versions WHERE protocol_id=?",
                (value["id"],)).fetchone()[0] or 0
            if latest != expected_previous_version:
                raise ValueError("Stale evaluation protocol version; use latest+1 with expected latest")
            high_water = self.connection.execute(
                "SELECT MAX(first_saved_at) FROM ir_evaluation_protocol_versions").fetchone()[0]
            if high_water is not None and current < timestamp(high_water):
                raise ValueError("Trusted protocol save clock cannot reverse")

            result = {
                "schema_version": 1, "id": value["id"], "version": value["version"],
                "status": "protocol_commitment_only", "request": value,
                "draft": bool(unset), "unset_fields": unset,
                "verification": {
                    "cohort_reference": "unverified", "model_references": "unverified",
                    "source_references": "unverified", "source_quotes": "unverified",
                    "author_principle_adoption": "unverified", "rule_correctness": "unverified",
                    "prospectiveness": "unverified", "blindness": "unverified",
                    "independence": "unverified", "execution": "not_performed",
                    "score_eligibility": "not_assessed",
                },
                "limitations": list(_LIMITATIONS),
            }
            self.connection.execute(
                "INSERT INTO ir_evaluation_protocol_versions "
                "(protocol_id,version,request_sha256,data,first_saved_at) VALUES (?,?,?,?,?)",
                (value["id"], value["version"], digest, _encode(result), saved))
            return self._envelope(self._row(value["id"], value["version"]), added=True)
