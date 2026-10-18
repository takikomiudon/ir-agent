"""Immutable, ex-ante candidate registration; no likelihood fitting or scoring."""
from copy import deepcopy
from decimal import Decimal, Inexact, InvalidOperation, ROUND_DOWN, Rounded, localcontext
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ir_agent.models import json_text
from ir_agent.observation_store import ObservationStore, SCHEMA as OBSERVATION_SCHEMA
from ir_agent.prediction_store import PredictionStore, SCHEMA
from test_observation_store import design, fixture


DESIGN_SAVED = "2026-10-01T10:01:00+09:00"
CREATED = "2026-10-01T10:01:10+09:00"
SAVED = "2026-10-01T10:01:20+09:00"
SENT = "2026-10-01T10:02:00+09:00"
LATER = "2026-11-03T18:00:00+09:00"


def digest(value):
    return sha256(json_text(value).encode()).hexdigest()


def candidate(envelope, prediction_id="candidate-1"):
    record = envelope["record"]
    model_manifest = {"code_reference": "synthetic:explicit-test-function:v1", "settings": {"test_only": True}}
    training_manifest = {"kind": "user_declared_test_assumption", "evidence": [],
                         "rationale": "Arithmetic fixture only; no learned or calibrated model."}
    signals, states = list(record["signals"]), list(record["hypothesis"]["states"])
    # Test-only explicit degenerate distributions, never a project default.
    return {"id": prediction_id,
            "observation_ref": {"id": envelope["id"], "version": envelope["version"],
                                "snapshot_sha256": digest(record), "design_sha256": envelope["design_sha256"]},
            "model_ref": {"id": "synthetic-test-model", "version": 1,
                          "trained_at": "2026-10-01T09:50:00+09:00",
                          "manifest": model_manifest, "manifest_sha256": digest(model_manifest)},
            "training_ref": {"information_cutoff": "2026-10-01T09:00:00+09:00",
                             "manifest": training_manifest, "manifest_sha256": digest(training_manifest)},
            "created_at": CREATED,
            "likelihoods": {signal: {state: "1" if i == j else "0" for j, state in enumerate(states)}
                            for i, signal in enumerate(signals)},
            "provenance": {"kind": "synthetic_example" if record["synthetic"] else "user_assumption",
                           "reference": "synthetic:test-only", "rationale": "Unit-test values, not an actual forecast."},
            "synthetic": record["synthetic"]}


class PredictionStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.addCleanup(self.db.close)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript(OBSERVATION_SCHEMA + SCHEMA)
        self.observations = ObservationStore(self.db)
        self.store = PredictionStore(self.db)
        self.envelope = self.observations.register(design(), DESIGN_SAVED)
        self.request = candidate(self.envelope)

    def count(self, table="ir_predictions"):
        return self.db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]

    def sent_record(self):
        record = deepcopy(self.envelope["record"])
        record["dispatch"] = fixture()["dispatch"]
        return self.observations.append(record, 1, SENT)

    def test_registration_derives_identity_definition_and_keeps_declarations_unverified(self):
        original = deepcopy(self.request)
        result = self.store.register(self.request, SAVED)
        self.assertTrue(result["added"])
        self.assertEqual(result["status"], "candidate_prediction_only")
        self.assertEqual(result["first_saved_at"], "2026-10-01T01:01:20.000000+00:00")
        self.assertEqual(result["request_sha256"], digest(original))
        self.assertEqual(result["request"], original)
        binding = result["observation_binding"]
        record = self.envelope["record"]
        for key in ("company_id", "question_id", "cohort_id", "design_version"):
            self.assertEqual(binding[key], record[key])
        self.assertEqual(binding["definition"]["states"], record["hypothesis"]["states"])
        self.assertEqual(binding["definition"]["signals"], record["signals"])
        self.assertEqual(binding["definition_sha256"], digest(binding["definition"]))
        self.assertTrue(result["verification"]["manifest_hashes_verified"])
        self.assertFalse(result["verification"]["training_provenance_verified"])
        self.assertFalse(result["verification"]["calibration_verified"])
        self.assertEqual(self.request, original)
        self.assertEqual(self.observations.history(record["id"]), [self.envelope | {"added": False}])
        json.dumps(result, allow_nan=False)

    def test_identical_retry_returns_first_record_even_after_observation_results(self):
        first = self.store.register(self.request, SAVED)
        sent = self.sent_record()
        record = sent["record"]
        record["replies"] = fixture()["replies"]
        self.observations.append(record, 2, "2026-10-02T10:01:00+09:00")
        retry = self.store.register(deepcopy(self.request), LATER)
        self.assertEqual(retry, first | {"added": False})
        self.assertEqual(self.store.show(self.request["id"]), retry)
        self.assertEqual(self.count(), 1)
        changed = deepcopy(self.request)
        changed["likelihoods"]["unclear"]["temporary"] = "1"
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.store.register(changed, LATER)
        with self.assertRaisesRegex(ValueError, "predate"):
            self.store.register(self.request, CREATED)

    def test_read_visibility_uses_actual_first_save_and_offset_normalization(self):
        self.store.register(self.request, SAVED)
        self.assertEqual(self.store.list_as_of(CREATED), [])
        self.assertEqual(self.store.list_as_of("2026-10-01T01:01:19Z"), [])
        self.assertEqual(len(self.store.list_as_of("2026-10-01T01:01:20Z")), 1)
        self.assertEqual(len(self.store.list_as_of(LATER)), 1)
        with self.assertRaises(ValueError):
            self.store.show("unknown")

    def test_time_order_future_and_design_save_before_prediction_are_required(self):
        mutations = [
            lambda r: r.update(created_at="2026-10-01T10:01:21+09:00"),
            lambda r: r.update(created_at="2026-10-01T10:00:59+09:00"),
            lambda r: r["model_ref"].update(trained_at="2026-10-01T10:01:11+09:00"),
            lambda r: r["training_ref"].update(information_cutoff="2026-10-01T09:50:01+09:00"),
            lambda r: r.update(created_at="2026-10-01T10:01:10"),
        ]
        for mutate in mutations:
            current = deepcopy(self.request)
            mutate(current)
            with self.subTest(mutate=mutations.index(mutate)), self.assertRaises(ValueError):
                self.store.register(current, SAVED)
        with self.assertRaises(ValueError):
            self.store.register(self.request, "2026-10-01T10:01:05+09:00")
        expired = deepcopy(self.request)
        expired["created_at"] = "2026-10-09T18:00:00+09:00"
        with self.assertRaisesRegex(ValueError, "deadlines"):
            self.store.register(expired, "2026-10-09T18:01:00+09:00")
        self.assertEqual(self.count(), 0)

    def test_old_unknown_other_company_and_hash_mismatch_references_are_rejected(self):
        other = design()
        other.update(id="observation-other", company_id="other-company", question_id="other-question")
        for evidence in other["premise_evidence"]:
            evidence["company_id"] = "other-company"
        self.observations.register(other, DESIGN_SAVED)
        mutations = [lambda r: r["observation_ref"].update(id="unknown"),
                     lambda r: r["observation_ref"].update(id="observation-other"),
                     lambda r: r["observation_ref"].update(snapshot_sha256="0"*64),
                     lambda r: r["observation_ref"].update(design_sha256="0"*64),
                     lambda r: r["observation_ref"].update(version=999)]
        for mutate in mutations:
            current = deepcopy(self.request)
            mutate(current)
            with self.subTest(mutate=mutations.index(mutate)), self.assertRaises(ValueError):
                self.store.register(current, SAVED)
        self.sent_record()
        with self.assertRaisesRegex(ValueError, "current observation"):
            self.store.register(self.request, SENT)

    def test_live_registration_rejects_any_dispatch_reply_or_adjudication(self):
        sent = self.sent_record()
        current = candidate(sent)
        current["created_at"] = SENT
        with self.assertRaisesRegex(ValueError, "before any dispatch"):
            self.store.register(current, SENT)
        for status in ["not_identifiable", "state_changed", "definition_mismatch"]:
            with self.subTest(status=status):
                # Independent unsent observations may have explicit verdicts.
                record = design()
                record.update(id="adjudicated-"+status, question_id="adjudicated-"+status)
                env = self.observations.register(record, DESIGN_SAVED)
                record["verification"] = {"status": status, "recorded_at": "2026-11-20T12:00:00+09:00", "reason": "Verdict already known", "evidence": []}
                env = self.observations.append(record, 1, "2026-11-20T12:00:00+09:00")
                current = candidate(env, "prediction-"+status)
                current["created_at"] = "2026-11-20T12:00:00+09:00"
                with self.assertRaisesRegex(ValueError, "before any dispatch"):
                    self.store.register(current, "2026-11-20T12:01:00+09:00")

    def test_model_version_cannot_rebind_manifest_training_or_synthetic_status(self):
        self.store.register(self.request, SAVED)
        other = design()
        other.update(id="second-observation", question_id="second-question")
        env = self.observations.register(other, DESIGN_SAVED)
        second = candidate(env, "second-prediction")
        result = self.store.register(second, SAVED)
        self.assertEqual(result["model_first_saved_at"], self.store.show(self.request["id"])["model_first_saved_at"])
        self.assertEqual(self.count("ir_prediction_models"), 1)
        mutations = [lambda r: r["model_ref"]["manifest"].update(code_reference="different-model"),
                     lambda r: r["training_ref"]["manifest"].update(evidence=["different-training"]),
                     lambda r: r["model_ref"].update(trained_at="2026-10-01T09:51:00+09:00"),
                     lambda r: r["training_ref"].update(information_cutoff="2026-10-01T08:59:00+09:00")]
        for i, mutate in enumerate(mutations):
            current = deepcopy(second)
            current["id"] = "rebind-"+str(i)
            mutate(current)
            for key in ("model_ref", "training_ref"):
                current[key]["manifest_sha256"] = digest(current[key]["manifest"])
            with self.subTest(i=i), self.assertRaisesRegex(ValueError, "immutable model/training"):
                self.store.register(current, SAVED)
        current["model_ref"]["version"] = 2
        self.assertTrue(self.store.register(current, SAVED)["added"])
        self.assertEqual(self.count("ir_prediction_models"), 2)

    def test_manifest_integrity_exact_json_and_provenance_do_not_claim_training_truth(self):
        for key in ("model_ref", "training_ref"):
            current = deepcopy(self.request)
            current[key]["manifest"]["tampered"] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "manifest SHA"):
                self.store.register(current, SAVED)
        current = deepcopy(self.request)
        current["provenance"]["kind"] = "external_evidence"
        current["training_ref"]["manifest"]["claimed_verified"] = True
        current["training_ref"]["manifest_sha256"] = digest(current["training_ref"]["manifest"])
        result = self.store.register(current, SAVED)
        self.assertFalse(result["verification"]["training_provenance_verified"])
        self.assertFalse(result["verification"]["calibration_verified"])

    def test_likelihood_full_matrix_exact_column_sums_and_types_are_required(self):
        mutations = [lambda r: r.update(likelihoods=None), lambda r: r["likelihoods"].pop("declined"),
                     lambda r: r["likelihoods"]["unclear"].pop("mixed"),
                     lambda r: r["likelihoods"]["unclear"].update(other="0"),
                     lambda r: r["likelihoods"]["unclear"].update(temporary="1e-100"),
                     lambda r: r["likelihoods"]["unclear"].update(temporary=True),
                     lambda r: r["likelihoods"]["unclear"].update(temporary="NaN"),
                     lambda r: r["likelihoods"]["unclear"].update(temporary="-0.1"),
                     lambda r: r["likelihoods"]["unclear"].update(temporary="1.01"),
                     lambda r: r["likelihoods"]["unclear"].update(temporary="1e999999999999999999999999999")]
        for i, mutate in enumerate(mutations):
            current = deepcopy(self.request)
            mutate(current)
            with self.subTest(i=i), self.assertRaises(ValueError):
                self.store.register(current, SAVED)
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.count("ir_prediction_models"), 0)

    def test_unknown_fields_enum_types_and_caller_verification_are_rejected(self):
        mutations = [lambda r: r.update(company_id="other-company"), lambda r: r.update(cohort_id="other"),
                     lambda r: r.update(first_saved_at=SAVED), lambda r: r.update(calibration_verified=True),
                     lambda r: r.update(synthetic="false"), lambda r: r["provenance"].update(kind=[]),
                     lambda r: r["provenance"].update(kind="calibrated"),
                     lambda r: r["model_ref"].update(version=True),
                     lambda r: r["observation_ref"].update(version=False),
                     lambda r: r["training_ref"].update(verified=True)]
        for i, mutate in enumerate(mutations):
            current = deepcopy(self.request)
            mutate(current)
            with self.subTest(i=i), self.assertRaises(ValueError):
                self.store.register(current, SAVED)
        for raw in [None, [], {}, self.request | {"manifest": {1: "not-a-JSON-object"}}]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.store.register(raw, SAVED)

    def test_synthetic_match_and_model_commitment_never_promote_to_live(self):
        current = deepcopy(self.request)
        current["synthetic"] = True
        with self.assertRaisesRegex(ValueError, "match its observation"):
            self.store.register(current, SAVED)
        current = deepcopy(self.request)
        current["provenance"]["kind"] = "synthetic_example"
        with self.assertRaisesRegex(ValueError, "promoted to live"):
            self.store.register(current, SAVED)
        record = design(True)
        record.update(id="synthetic-design", question_id="synthetic-question", cohort_id="synthetic-only-cohort")
        synthetic = candidate(self.observations.register(record, DESIGN_SAVED), "synthetic-prediction")
        self.store.register(synthetic, SAVED)
        with self.assertRaisesRegex(ValueError, "immutable model/training"):
            self.store.register(self.request, SAVED)

    def test_unknown_and_failed_dispatches_are_attempts_and_pending_verdict_is_allowed(self):
        for status in ("unknown", "failed"):
            record = design()
            record.update(id="dispatch-" + status, question_id="dispatch-" + status)
            self.observations.register(record, DESIGN_SAVED)
            record["dispatch"] = deepcopy(fixture()["dispatch"])
            record["dispatch"]["status"] = status
            env = self.observations.append(record, 1, SENT)
            current = candidate(env, "prediction-" + status)
            current["created_at"] = SENT
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "before any dispatch"):
                self.store.register(current, SENT)
        record = deepcopy(self.envelope["record"])
        record["verification"] = {"status": "pending", "recorded_at": CREATED,
                                  "reason": "State is not yet known", "evidence": []}
        env = self.observations.append(record, 1, CREATED)
        current = candidate(env)
        self.assertTrue(self.store.register(current, SAVED)["added"])

    def test_nested_transactions_and_failed_insert_roll_back_model_and_prediction(self):
        self.db.execute("BEGIN IMMEDIATE")
        self.store.register(self.request, SAVED)
        self.assertTrue(self.db.in_transaction)
        self.db.execute("ROLLBACK")
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.count("ir_prediction_models"), 0)
        self.db.execute("CREATE TRIGGER reject_prediction BEFORE INSERT ON ir_predictions BEGIN SELECT RAISE(ABORT,'test insertion failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.register(self.request, SAVED)
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.count("ir_prediction_models"), 0)
        self.db.execute("CREATE TABLE parent_work (value TEXT)")
        self.db.execute("BEGIN IMMEDIATE")
        self.db.execute("INSERT INTO parent_work VALUES ('retain parent work')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.register(self.request, SAVED)
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.db.execute("SELECT value FROM parent_work").fetchone()[0], "retain parent work")
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.count("ir_prediction_models"), 0)
        self.db.execute("ROLLBACK")

    def test_private_decimal_validation_preserves_preexisting_flags(self):
        with localcontext() as context:
            context.traps[InvalidOperation] = False
            Decimal("bad-number")
            context.prec = 2
            context.rounding = ROUND_DOWN
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            before = context.copy()
            result = self.store.register(self.request, SAVED)
            self.assertEqual(context.flags, before.flags)
            self.assertEqual(context.prec, before.prec)
            self.assertEqual(context.rounding, before.rounding)
        self.assertEqual(result["status"], "candidate_prediction_only")

    def test_file_reopen_preserves_payload_manifests_and_first_save(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "predictions.sqlite3"
            connection = sqlite3.connect(path, isolation_level=None)
            try:
                connection.executescript(OBSERVATION_SCHEMA + SCHEMA)
                env = ObservationStore(connection).register(design(), DESIGN_SAVED)
                original = PredictionStore(connection).register(candidate(env), SAVED)
            finally:
                connection.close()
            connection = sqlite3.connect(path, isolation_level=None)
            try:
                self.assertEqual(PredictionStore(connection).show(original["id"]), original | {"added": False})
            finally:
                connection.close()

    def test_unfilled_template_is_not_a_prediction_and_cannot_fill_probabilities(self):
        path = Path(__file__).parents[1] / "examples/probability-prediction.template.json"
        value = json.loads(path.read_text())
        self.assertTrue(value["synthetic"])
        self.assertIsNone(value["likelihoods"])
        with self.assertRaises(ValueError):
            self.store.register(value, SAVED)
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.count("ir_prediction_models"), 0)


if __name__ == "__main__":
    unittest.main()
