"""Finite ledger linkage/timing checks; forecasts remain unscored candidates."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ir_agent.models import json_text
from ir_agent.observation_assessments import digest
from ir_agent.observation_store import ObservationStore, SCHEMA as OBSERVATION_SCHEMA
from ir_agent.prediction_readiness import audit_prediction_readiness
from ir_agent.prediction_store import PredictionStore, SCHEMA
from test_observation_store import design, fixture
from test_prediction_store import candidate, CREATED, DESIGN_SAVED, SAVED, SENT, LATER

spec = importlib.util.spec_from_file_location("report_prediction_readiness", Path(__file__).resolve().parents[1] / "scripts/report_prediction_readiness.py")
script = importlib.util.module_from_spec(spec); spec.loader.exec_module(script)


class PredictionReadinessTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "ledger.sqlite3"
        self.db = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(self.db.close); self.db.executescript(OBSERVATION_SCHEMA + SCHEMA)
        self.observations = ObservationStore(self.db)
        self.predictions = PredictionStore(self.db)
        self.initial = self.observations.register(design(), DESIGN_SAVED)

    def audit(self, as_of=LATER):
        return audit_prediction_readiness(script.read_snapshot(self.path), as_of=as_of)

    def register_prediction(self):
        return self.predictions.register(candidate(self.initial), SAVED)

    def append_complete(self, record=None):
        value = deepcopy(self.initial["record"]) if record is None else deepcopy(record)
        value.update(dispatch=fixture()["dispatch"], replies=fixture()["replies"], verification=fixture()["verification"], response_check=fixture()["response_check"])
        return self.observations.append(value, 1, LATER)

    def test_population_left_join_retains_missing_prediction_unsent_and_unknown_tables(self):
        report = self.audit()
        self.assertEqual(report["observation_count"], 1)
        self.assertEqual(report["observations_without_prediction_count"], 1)
        self.assertEqual(report["observations"][0]["view"]["dispatch_status"], "not_sent_or_not_yet_recorded")
        self.assertEqual(report["observations"][0]["status"], "missing_prediction")
        unknown = audit_prediction_readiness({}, as_of=LATER)
        self.assertEqual(unknown["table_status"]["predictions"], "unknown")
        snapshot = script.read_snapshot(self.path); del snapshot["predictions"]
        self.assertEqual(audit_prediction_readiness(snapshot, as_of=LATER)["observations"][0]["prediction_coverage"], "unknown")

    def test_saved_forecast_binds_reference_and_matrix_but_remains_unverified(self):
        self.register_prediction(); self.append_complete()
        report = self.audit(); item = report["observations"][0]["predictions"][0]
        self.assertEqual(item["status"], "needs_evidence_binding_review")
        self.assertTrue(item["reference_verified"])
        self.assertEqual(item["prospective_timing"], "no_detected_violation")
        self.assertFalse(item["evidence_binding_verified"]); self.assertFalse(item["calibration_verified"])
        self.assertEqual(report["observations"][0]["view"]["signal"], "temporary_explanation")
        self.assertNotIn("score", report); self.assertNotIn("ready_for_scoring", json.dumps(report))

    def test_actual_dispatch_recorded_later_can_invalidate_prediction_timing(self):
        self.register_prediction()
        record = deepcopy(self.initial["record"])
        # Initial design had no dispatch. The later saved log reveals an actual
        # attempt before prediction persistence, although generation was earlier.
        record["dispatch"] = {"attempted_at": "2026-10-01T10:01:15+09:00", "recorded_at": SENT, "status": "sent"}
        self.observations.append(record, 1, SENT)
        earlier = self.audit(SAVED)["observations"][0]["predictions"][0]
        later = self.audit(SENT)["observations"][0]["predictions"][0]
        self.assertEqual(earlier["prospective_timing"], "no_detected_violation")
        self.assertEqual(later["status"], "invalid_prospective_timing")
        self.assertIn("actual_dispatch_predates_prediction_save", later["reason_codes"])

    def test_actual_receipt_and_future_prediction_visibility_are_separate(self):
        self.register_prediction()
        before = self.audit(CREATED)
        self.assertEqual(before["visible_prediction_count"], 0)
        record = deepcopy(self.initial["record"])
        record["dispatch"] = {"attempted_at": "2026-10-01T10:01:01+09:00", "recorded_at": SENT, "status": "sent"}
        reply = deepcopy(fixture()["replies"][0]); reply.update(received_at="2026-10-01T10:01:19+09:00", recorded_at=SENT)
        record["replies"] = [reply]
        self.observations.append(record, 1, SENT)
        item = self.audit(SENT)["observations"][0]["predictions"][0]
        self.assertIn("actual_receipt_predates_prediction_save", item["reason_codes"])

    def test_corrupt_saved_identity_snapshot_matrix_and_synthetic_are_reported(self):
        self.register_prediction(); snapshot = script.read_snapshot(self.path)
        changes = [lambda row: row["record"]["request"]["observation_ref"].update(snapshot_sha256="0"*64),
                   lambda row: row["record"]["observation_binding"].update(company_id="other"),
                   lambda row: row["record"]["request"].update(synthetic=True),
                   lambda row: row["record"]["request"]["likelihoods"]["unclear"].pop("temporary"),
                   lambda row: row.update(observation_version=99)]
        for index, change in enumerate(changes):
            damaged = deepcopy(snapshot); change(damaged["predictions"][0])
            with self.subTest(case=index):
                item = audit_prediction_readiness(damaged, as_of=LATER)["observations"][0]["predictions"][0]
                self.assertEqual(item["status"], "invalid_prediction_reference")
                self.assertFalse(item["reference_verified"])
        self.assertEqual(self.audit()["visible_prediction_count"], 1)

    def test_orphan_forecasts_do_not_create_or_remove_observations(self):
        self.register_prediction(); snapshot = script.read_snapshot(self.path)
        snapshot["predictions"][0]["observation_id"] = "missing-observation"
        result = audit_prediction_readiness(snapshot, as_of=LATER)
        self.assertEqual(result["observation_count"], 1)
        self.assertEqual(result["observations_without_prediction_count"], 1)
        self.assertEqual(len(result["orphan_predictions"]), 1)

    def test_existing_view_preserves_held_external_and_no_response_rules(self):
        self.register_prediction()
        value = deepcopy(self.initial["record"])
        value.update(dispatch=fixture()["dispatch"], response_check=fixture()["response_check"], verification=fixture()["verification"])
        value["external_changes"] = [{"id": "change", "occurred_at": "2026-10-03T10:00:00+09:00", "recorded_at": "2026-10-03T10:01:00+09:00", "description": "Synthetic unresolved change", "impact": "unresolved"}]
        self.observations.append(value, 1, LATER)
        view = self.audit()["observations"][0]["view"]
        self.assertEqual(view["signal"], "no_response_by_deadline")
        self.assertIn("external_change_blocks_state_inference", view["exclusion_reasons"])
        self.assertFalse(view["eligible_for_descriptive_table"])

    def test_signal_changed_after_known_state_is_leakage_candidate(self):
        self.register_prediction(); complete = self.append_complete()
        value = deepcopy(complete["record"]); reply = value["replies"][0]
        event = {"id": "corrected", "target_kind": "reply", "target_id": reply["id"], "target_snapshot_sha256": digest(reply),
                 "version": 1, "expected_previous_version": 0, "recorded_at": "2026-11-04T10:00:00+09:00",
                 "reviewer": "test-only", "rationale": "Synthetic independent-binding fixture for read-only audit", "basis": {},
                 "assessment": {"signal": "persistent_explanation", "information_status": "public_clarification"}}
        # Snapshot-only fixture: no claim the read-only audit independently
        # validates this asserted binding. Store rejects forged approvals.
        event.update(request=deepcopy(event), first_saved_at=event["recorded_at"], basis_verification={"status": "verified", "reason_codes": [], "source_snapshots": {}})
        value["assessments"] = [event]
        snapshot = script.read_snapshot(self.path)
        snapshot["observation_versions"].append({"observation_id": value["id"], "version": 3, "record": value,
            "design_sha256": complete["design_sha256"], "first_saved_at": event["recorded_at"]})
        report = audit_prediction_readiness(snapshot, as_of="2026-11-04T11:00:00+09:00")
        item = report["observations"][0]
        self.assertEqual(item["view"]["signal"], "persistent_explanation")
        self.assertEqual(item["predictions"][0]["signal_classification_leakage_candidates"][0]["assessment_id"], "corrected")
        self.assertFalse(item["predictions"][0]["evidence_binding_verified"])

    def test_input_boundaries_duplicates_and_read_only_script(self):
        self.register_prediction(); snapshot = script.read_snapshot(self.path); original = deepcopy(snapshot)
        for damaged in (None, [], {"predictions": None}, {"unknown": []}):
            with self.subTest(value=damaged), self.assertRaises(ValueError): audit_prediction_readiness(damaged, as_of=LATER)
        repeated = deepcopy(snapshot); repeated["observation_versions"] *= 2
        with self.assertRaisesRegex(ValueError, "Duplicate"): audit_prediction_readiness(repeated, as_of=LATER)
        audit_prediction_readiness(snapshot, as_of=LATER); self.assertEqual(snapshot, original)
        before = sha256(self.path.read_bytes()).hexdigest()
        script.read_snapshot(self.path)
        self.assertEqual(sha256(self.path.read_bytes()).hexdigest(), before)

    def test_script_rejects_duplicate_json_keys_and_nonfinite_constants(self):
        self.register_prediction()
        for content in ('{"request": {}, "request": {}}', '{"invalid": NaN}'):
            self.db.execute("UPDATE ir_predictions SET data=?", (content,))
            with self.subTest(content=content), self.assertRaises(ValueError): script.read_snapshot(self.path)


if __name__ == "__main__": unittest.main()
