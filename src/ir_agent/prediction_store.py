"""Immutable candidate forecasts bound to a saved IR observation design.

Install SCHEMA on the existing ObservationStore connection before constructing
PredictionStore. The trusted caller supplies ``now`` outside the request JSON.
Only registration/readback is implemented: no scoring, fitting, calibration,
dispatch, evidence retrieval or investment decision is performed.

The author-supported pre-observation scoring principle and this project's
additional persistence rules are distinguished in
docs/probability-prediction-contract.md and docs/probability-prediction-storage.md.
Manifest hashes prove content agreement, not the truth of a training history.
"""
from __future__ import annotations

from contextlib import contextmanager
from decimal import Context, Decimal, DecimalException, DivisionByZero, InvalidOperation, Overflow, localcontext
from hashlib import sha256
import json
import math
import re
import sqlite3

from .models import integer, json_text, timestamp
from .observation_store import ObservationStore, _design_hash
from .observations import validate_observation


SCHEMA = """
CREATE TABLE IF NOT EXISTS ir_prediction_models (
    model_id TEXT NOT NULL, model_version INTEGER NOT NULL CHECK(model_version>=1),
    commitment_sha256 TEXT NOT NULL, data TEXT NOT NULL, first_saved_at TEXT NOT NULL,
    PRIMARY KEY(model_id,model_version)
);
CREATE TABLE IF NOT EXISTS ir_predictions (
    id TEXT PRIMARY KEY, observation_id TEXT NOT NULL, observation_version INTEGER NOT NULL,
    model_id TEXT NOT NULL, model_version INTEGER NOT NULL, request_sha256 TEXT NOT NULL,
    data TEXT NOT NULL, first_saved_at TEXT NOT NULL,
    FOREIGN KEY(observation_id,observation_version)
        REFERENCES ir_observation_versions(observation_id,version),
    FOREIGN KEY(model_id,model_version) REFERENCES ir_prediction_models(model_id,model_version)
);
"""

_REQUEST = {"id", "observation_ref", "model_ref", "training_ref", "created_at",
            "likelihoods", "provenance", "synthetic"}
_NUMERIC = re.compile(r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


def _fields(value, keys, path):
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{path} must contain exactly {sorted(keys)!r}")
    return value


def _text(value, path):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(path + " must be nonempty text without surrounding whitespace")
    return value


def _hash(value, path):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(path + " must be a lowercase SHA-256")
    return value


def _json_types(value, depth=0):
    if depth > 64:
        raise ValueError("Prediction JSON exceeds the nesting resource limit")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _json_types(item, depth + 1)
    elif type(value) is list:
        for item in value:
            _json_types(item, depth + 1)
    elif type(value) not in (str, int, float, bool, type(None)):
        raise ValueError("Prediction and manifests must contain only JSON values")
    elif type(value) is float and not math.isfinite(value):
        raise ValueError("JSON numbers must be finite")


def _encode(value):
    _json_types(value)
    try:
        encoded = json_text(value)
        if len(encoded.encode("utf-8")) > 2 * 1024 * 1024:
            raise ValueError("Prediction JSON exceeds the 2 MiB resource limit")
        return encoded
    except (TypeError, OverflowError, UnicodeError) as error:
        raise ValueError("Prediction must be finite UTF-8 JSON") from error


def _digest(value):
    return sha256(_encode(value).encode("utf-8")).hexdigest()


def _manifest(reference, path):
    value = reference["manifest"]
    if not isinstance(value, dict) or not value:
        raise ValueError(path + ".manifest must be a nonempty JSON object")
    expected = _hash(reference["manifest_sha256"], path + ".manifest_sha256")
    actual = _digest(value)
    if expected != actual:
        raise ValueError(path + " manifest SHA-256 does not match its inline content")


def _validate_request(value):
    _fields(value, _REQUEST, "prediction")
    _text(value["id"], "prediction.id")
    reference = _fields(value["observation_ref"], {"id", "version", "snapshot_sha256", "design_sha256"}, "observation_ref")
    _text(reference["id"], "observation_ref.id")
    integer(reference["version"], "observation_ref.version", minimum=1)
    for key in ("snapshot_sha256", "design_sha256"):
        _hash(reference[key], "observation_ref." + key)
    model = _fields(value["model_ref"], {"id", "version", "trained_at", "manifest", "manifest_sha256"}, "model_ref")
    _text(model["id"], "model_ref.id")
    integer(model["version"], "model_ref.version", minimum=1)
    _manifest(model, "model_ref")
    training = _fields(value["training_ref"], {"information_cutoff", "manifest", "manifest_sha256"}, "training_ref")
    _manifest(training, "training_ref")
    trained = timestamp(model["trained_at"], "model_ref.trained_at")
    cutoff = timestamp(training["information_cutoff"], "training_ref.information_cutoff")
    created = timestamp(value["created_at"], "created_at")
    if not cutoff <= trained <= created:
        raise ValueError("Information cutoff must be <= trained_at <= created_at")
    if type(value["synthetic"]) is not bool:
        raise ValueError("synthetic must be boolean")
    provenance = _fields(value["provenance"], {"kind", "reference", "rationale"}, "provenance")
    kind = _text(provenance["kind"], "provenance.kind")
    if kind not in {"external_evidence", "user_assumption", "synthetic_example"}:
        raise ValueError("Unknown provenance.kind")
    if kind == "synthetic_example" and not value["synthetic"]:
        raise ValueError("Synthetic provenance cannot be promoted to live")
    for key in ("reference", "rationale"):
        _text(provenance[key], "provenance." + key)
    return created


def _likelihoods(value, signals, states):
    if len(signals) > 1000 or len(states) > 1000 or len(signals) * len(states) > 100000:
        raise ValueError("Observation matrix exceeds the probability resource limit")
    if not isinstance(value, dict) or set(value) != set(signals):
        raise ValueError("likelihoods must cover exactly the observation signals")
    numbers = {}
    private = Context(prec=80, Emin=-999999, Emax=999999, flags=[],
                      traps=[InvalidOperation, DivisionByZero, Overflow])
    with localcontext(private):
        for signal, row in value.items():
            if not isinstance(row, dict) or set(row) != set(states):
                raise ValueError("Each signal must cover exactly the observation states")
            numbers[signal] = {}
            for state, raw in row.items():
                if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
                    raise ValueError("Each likelihood must be a finite decimal token")
                token = str(raw)
                if len(token) > 2048 or not _NUMERIC.fullmatch(token):
                    raise ValueError("Each likelihood must be a bounded decimal token")
                try:
                    number = Decimal(token)
                except DecimalException as error:
                    raise ValueError("Likelihood must be a bounded finite decimal") from error
                if (not number.is_finite() or len(number.as_tuple().digits) > 256
                        or abs(number.as_tuple().exponent) > 1000):
                    raise ValueError("Likelihood exceeds the supported decimal range")
                if not Decimal(0) <= number <= Decimal(1):
                    raise ValueError("Each likelihood must be between 0 and 1")
                numbers[signal][state] = number
        scale = max(max(0, -n.as_tuple().exponent) for row in numbers.values() for n in row.values())
        private.prec = max(80, scale + len(str(len(signals))) + 4)
        with localcontext(private):
            for state in states:
                if sum((row[state] for row in numbers.values()), Decimal(0)) != Decimal(1):
                    raise ValueError("Each state must sum exactly to 1 over all signals")


def _binding(record, version):
    definition = {"state_timing": record["hypothesis"]["state_timing"],
                  "states": record["hypothesis"]["states"], "target_period": record["hypothesis"]["target_period"],
                  "signals": record["signals"], "synthetic": record.get("synthetic", False)}
    return {"company_id": record["company_id"], "question_id": record["question_id"],
            "cohort_id": record["cohort_id"], "design_version": record["design_version"],
            "observation_version": version, "definition": definition,
            "definition_sha256": _digest(definition)}


class PredictionStore:
    def __init__(self, sqlite_connection: sqlite3.Connection):
        self.connection = sqlite_connection
        self.observations = ObservationStore(sqlite_connection)

    @contextmanager
    def _atomic(self):
        nested = self.connection.in_transaction
        self.connection.execute("SAVEPOINT ir_prediction_mutation" if nested else "BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            if nested:
                self.connection.execute("ROLLBACK TO SAVEPOINT ir_prediction_mutation")
                self.connection.execute("RELEASE SAVEPOINT ir_prediction_mutation")
            else:
                self.connection.execute("ROLLBACK")
            raise
        else:
            self.connection.execute("RELEASE SAVEPOINT ir_prediction_mutation" if nested else "COMMIT")

    def _row(self, prediction_id):
        return self.connection.execute("SELECT data,request_sha256,first_saved_at FROM ir_predictions WHERE id=?", (prediction_id,)).fetchone()

    @staticmethod
    def _envelope(row, added=False):
        return {**json.loads(row[0]), "request_sha256": row[1], "first_saved_at": row[2], "added": added}

    def show(self, prediction_id: str) -> dict:
        _text(prediction_id, "prediction ID")
        row = self._row(prediction_id)
        if row is None:
            raise ValueError("Unknown prediction ID")
        return self._envelope(row)

    def list_as_of(self, as_of: str) -> list[dict]:
        cutoff = timestamp(as_of, "as_of").isoformat(timespec="microseconds")
        rows = self.connection.execute("SELECT data,request_sha256,first_saved_at FROM ir_predictions WHERE first_saved_at<=? ORDER BY first_saved_at,id", (cutoff,)).fetchall()
        return [self._envelope(row) for row in rows]

    def register(self, request: dict, now: str) -> dict:
        encoded = _encode(request)
        value = json.loads(encoded)
        _fields(value, _REQUEST, "prediction")
        _text(value["id"], "prediction.id")
        saved = timestamp(now, "trusted now").isoformat(timespec="microseconds")
        current = timestamp(saved)
        with self._atomic():
            existing = self._row(value["id"])
            if existing is not None:
                if _encode(json.loads(existing[0])["request"]) != encoded:
                    raise ValueError("Prediction ID is immutable and already has different content")
                if current < timestamp(existing[2]):
                    raise ValueError("A retry cannot predate its first saved record")
                return self._envelope(existing)
            created = _validate_request(value)
            if created > current:
                raise ValueError("Prediction cannot be created in the future")
            reference = value["observation_ref"]
            history = self.observations.history(reference["id"])
            if reference["version"] != history[-1]["version"]:
                raise ValueError("Prediction must reference the current observation version, not an old or unknown version")
            observed = history[-1]
            record = validate_observation(observed["record"])
            if reference["snapshot_sha256"] != _digest(record):
                raise ValueError("Observation snapshot SHA-256 does not match the referenced observation/company")
            if reference["design_sha256"] != observed["design_sha256"] or _design_hash(record) != observed["design_sha256"]:
                raise ValueError("Observation design SHA-256 mismatch")
            if timestamp(observed["first_saved_at"]) > created or timestamp(record["design_recorded_at"]) > created:
                raise ValueError("Observation design must be saved before prediction creation")
            if value["synthetic"] != record.get("synthetic", False):
                raise ValueError("Prediction synthetic status must match its observation; no promotion to live")
            live = not value["synthetic"]
            if live:
                status = (record.get("verification") or {}).get("status")
                if record.get("dispatch") is not None or record["replies"] or status not in {None, "pending"}:
                    raise ValueError("Register a live prediction before any dispatch attempt, reply or outcome adjudication")
                if record.get("external_changes") or record.get("assessments"):
                    raise ValueError("Live prediction requires an unobserved design without outcome changes/assessments")
                if current > timestamp(record["reply_deadline"]) or current > timestamp(record["verification_deadline"]):
                    raise ValueError("Live prediction must be registered before its observation deadlines")
            _likelihoods(value["likelihoods"], record["signals"], record["hypothesis"]["states"])
            model = value["model_ref"]
            commitment = {"model_ref": model, "training_ref": value["training_ref"], "synthetic": value["synthetic"]}
            commitment_json, commitment_hash = _encode(commitment), _digest(commitment)
            previous_model = self.connection.execute("SELECT commitment_sha256,data,first_saved_at FROM ir_prediction_models WHERE model_id=? AND model_version=?", (model["id"], model["version"])).fetchone()
            if previous_model is not None:
                if previous_model[0] != commitment_hash or previous_model[1] != commitment_json:
                    raise ValueError("Model ID/version has an immutable model/training commitment; use a new version")
                if current < timestamp(previous_model[2]):
                    raise ValueError("Prediction cannot predate the saved model commitment")
                model_saved = previous_model[2]
            else:
                model_saved = saved
                self.connection.execute("INSERT INTO ir_prediction_models VALUES (?,?,?,?,?)", (model["id"], model["version"], commitment_hash, commitment_json, saved))
            result = {
                "schema_version": 1, "id": value["id"], "status": "candidate_prediction_only",
                "request": value, "observation_binding": _binding(record, reference["version"]),
                "observation_first_saved_at": observed["first_saved_at"],
                "model_commitment_sha256": commitment_hash, "model_first_saved_at": model_saved,
                "verification": {"observation_reference_verified": True, "manifest_hashes_verified": True,
                                 "live_registration_timing_checked": live,
                                 "training_provenance_verified": False, "calibration_verified": False},
                "limitations": [
                    "Inline manifests and their hashes are immutable content commitments, not independently resolved training evidence or verified historical availability.",
                    "The supplied cutoff/training/creation times are checked for order; model training, leakage freedom and likelihood calibration are not verified.",
                    "Registration only: no signal/state selection, scoring, model fitting, aggregate evaluation, EVSI adoption or investment decision is performed.",
                    "Subsequent observation events may require timing and eligibility review; registration alone does not establish score eligibility.",
                ],
            }
            self.connection.execute("INSERT INTO ir_predictions VALUES (?,?,?,?,?,?,?,?)", (value["id"], reference["id"], reference["version"], model["id"], model["version"], sha256(encoded.encode()).hexdigest(), _encode(result), saved))
            return self._envelope(self._row(value["id"]), added=True)
