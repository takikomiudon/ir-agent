"""Ex-ante design preservation, point-in-time snapshots and atomic append CAS."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import unittest

from ir_agent.observation_store import ObservationStore, SCHEMA
from ir_agent.observations import summarize_observations


def fixture():
    return json.loads((Path(__file__).resolve().parents[1] / "examples/ir-observations.json").read_text())["records"][0]


def design(synthetic=False):
    record = fixture(); record["synthetic"] = synthetic
    for key in ("dispatch", "response_check", "verification"): record.pop(key)
    record["replies"] = []
    return record


REGISTERED = "2026-10-01T10:01:00+09:00"
SENT = "2026-10-01T10:02:00+09:00"
RECEIVED = "2026-10-02T10:01:00+09:00"
VERIFIED = "2026-11-02T16:00:00+09:00"


class ObservationStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.addCleanup(self.db.close); self.db.executescript(SCHEMA)
        self.store = ObservationStore(self.db)

    def sent(self):
        record = design(); self.store.register(record, REGISTERED)
        record["dispatch"] = fixture()["dispatch"]
        self.store.append(record, 1, SENT)
        return record

    def test_initial_design_retry_is_immutable_and_keeps_first_saved_time(self):
        record = design(); result = self.store.register(record, REGISTERED)
        retried = self.store.register(record, SENT)
        self.assertTrue(result["added"]); self.assertFalse(retried["added"])
        self.assertEqual(result["first_saved_at"], retried["first_saved_at"])
        self.assertEqual(result["version"], 1)
        changed = deepcopy(record); changed["hypothesis"]["statement"] = "Changed after seeing outcome"
        with self.assertRaisesRegex(ValueError, "immutable"): self.store.register(changed, SENT)

    def test_real_initial_registration_cannot_backfill_sent_or_verified_records(self):
        record = fixture(); record["synthetic"] = False
        with self.assertRaisesRegex(ValueError, "before dispatch"): self.store.register(record, VERIFIED)
        self.assertEqual(self.store.records_as_of(VERIFIED), [])
        record = design(); record["dispatch"] = fixture()["dispatch"]
        with self.assertRaises(ValueError): self.store.register(record, RECEIVED)
        record = fixture()
        self.assertEqual(self.store.register(record, VERIFIED)["version"], 1)

    def test_synthetic_example_is_not_allowed_to_record_future_events(self):
        with self.assertRaisesRegex(ValueError, "future"): self.store.register(fixture(), REGISTERED)

    def test_missingness_or_state_change_verdict_cannot_be_backfilled_as_live_design(self):
        for status in ("not_identifiable", "state_changed", "definition_mismatch"):
            record = design()
            record["verification"] = {"status": status, "recorded_at": "2026-11-20T12:00:00+09:00", "reason": "An outcome was already adjudicated", "evidence": []}
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "adjudicated"):
                self.store.register(record, "2026-11-20T13:00:00+09:00")

    def test_design_identity_deadline_premise_prior_and_synthetic_flag_are_fixed(self):
        self.store.register(design(), REGISTERED)
        changes = [lambda r: r.update(company_id="other"), lambda r: r.update(cohort_id="other"),
                   lambda r: r.update(reply_deadline="2026-10-09T17:00:00+09:00"),
                   lambda r: r["signals"].update(unclear="New meaning"),
                   lambda r: r["premise_evidence"][0].update(quote="Different premise"),
                   lambda r: r.update(synthetic=True), lambda r: r.update(policy_ref={"id": "p", "version": 1})]
        for change in changes:
            record = design(); change(record)
            with self.subTest(change=changes.index(change)), self.assertRaises(ValueError): self.store.append(record, 1, SENT)
        self.assertEqual(len(self.store.history(design()["id"])), 1)

    def test_snapshot_visibility_requires_actual_first_save_not_asserted_design_date(self):
        record = design(); self.store.register(record, SENT)
        self.assertEqual(self.store.records_as_of(REGISTERED), [])
        self.assertEqual(len(self.store.records_as_of(SENT)), 1)
        self.assertEqual(summarize_observations(self.store.records_as_of(REGISTERED), as_of=REGISTERED)["record_count"], 0)

    def test_append_snapshots_are_prefix_only_cas_and_transport_retry_is_idempotent(self):
        record = self.sent(); record["replies"] = fixture()["replies"]
        saved = self.store.append(record, 2, RECEIVED)
        retried = self.store.append(record, 2, VERIFIED)
        self.assertEqual(saved["version"], 3); self.assertEqual(retried["version"], 3)
        self.assertEqual(saved["first_saved_at"], retried["first_saved_at"])
        old = deepcopy(record); old["replies"] = []
        with self.assertRaisesRegex(ValueError, "prefix-only"): self.store.append(old, 3, VERIFIED)
        changed = deepcopy(record); changed["replies"][0]["signal"] = "persistent_explanation"
        with self.assertRaisesRegex(ValueError, "prefix-only"): self.store.append(changed, 3, VERIFIED)
        changed = deepcopy(record); changed["verification"] = fixture()["verification"]
        with self.assertRaisesRegex(ValueError, "Stale"): self.store.append(changed, 1, VERIFIED)
        self.assertEqual(len(self.store.history(record["id"])), 3)

    def test_verified_outcome_is_not_visible_before_version_first_save(self):
        record = self.sent(); record["replies"] = fixture()["replies"]
        self.store.append(record, 2, RECEIVED)
        record["verification"] = fixture()["verification"]
        self.store.append(record, 3, "2026-11-03T12:00:00+09:00")
        earlier = self.store.records_as_of(VERIFIED)
        self.assertNotIn("verification", earlier[0])
        later = self.store.records_as_of("2026-11-03T12:00:00+09:00")
        self.assertEqual(summarize_observations(later, as_of="2026-11-03T12:00:00+09:00")["eligible_count"], 1)

    def test_response_check_and_verification_updates_preserve_old_snapshots(self):
        record = self.sent(); record["response_check"] = fixture()["response_check"]
        self.store.append(record, 2, "2026-10-08T17:01:00+09:00")
        earlier = deepcopy(record)
        record["response_check"].update(checked_through="2026-10-09T17:00:00+09:00", recorded_at="2026-10-09T17:01:00+09:00")
        self.store.append(record, 3, "2026-10-09T17:01:00+09:00")
        self.assertEqual(self.store.history(record["id"])[2]["record"], earlier)
        record["verification"] = fixture()["verification"]
        self.store.append(record, 4, VERIFIED)
        record["verification"].update(state="persistent", recorded_at="2026-11-03T17:00:00+09:00", reason="New public evidence revises original supplied label")
        self.store.append(record, 5, "2026-11-03T17:00:00+09:00")
        self.assertEqual(self.store.history(record["id"])[4]["record"]["verification"]["state"], "temporary")
        self.assertEqual(self.store.history(record["id"])[5]["record"]["verification"]["state"], "persistent")

    def test_time_regression_new_backdated_event_and_dispatch_before_design_are_rejected(self):
        record = self.sent()
        with self.assertRaises(ValueError): self.store.append(record, 2, REGISTERED)
        record["replies"] = fixture()["replies"]
        record["replies"][0]["received_at"] = SENT
        record["replies"][0]["recorded_at"] = REGISTERED
        with self.assertRaises(ValueError): self.store.append(record, 2, RECEIVED)
        other = design(); other["id"] += "other"; other["question_id"] += "other"
        self.store.register(other, "2026-10-01T10:03:00+09:00")
        other["dispatch"] = fixture()["dispatch"]
        other["dispatch"]["recorded_at"] = "2026-10-01T10:04:00+09:00"
        with self.assertRaisesRegex(ValueError, "predate initial"): self.store.append(other, 1, "2026-10-01T10:04:00+09:00")

    def test_nested_transaction_rolls_back_without_committing_parent_work(self):
        self.db.execute("BEGIN IMMEDIATE")
        self.store.register(design(), REGISTERED)
        self.assertTrue(self.db.in_transaction)
        self.db.execute("ROLLBACK")
        self.assertEqual(self.store.records_as_of(VERIFIED), [])

    def test_conflicting_company_question_or_cohort_rolls_back_fully(self):
        self.store.register(design(), REGISTERED)
        changed = design(); changed["id"] = "different-id"
        with self.assertRaises(ValueError): self.store.register(changed, SENT)
        changed["question_id"] += "different"
        changed["signals"]["unclear"] = "Different cohort definition"
        with self.assertRaises(ValueError): self.store.register(changed, SENT)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM ir_observations").fetchone()[0], 1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM ir_observation_versions").fetchone()[0], 1)

    def test_unknown_status_can_be_resolved_but_dispatch_attempt_cannot_be_rewritten(self):
        record = design(); self.store.register(record, REGISTERED)
        record["dispatch"] = deepcopy(fixture()["dispatch"]); record["dispatch"]["status"] = "unknown"
        self.store.append(record, 1, SENT)
        record["dispatch"].update(status="sent", recorded_at="2026-10-01T10:03:00+09:00")
        self.store.append(record, 2, "2026-10-01T10:03:00+09:00")
        record["dispatch"].update(attempted_at="2026-10-01T10:02:30+09:00", recorded_at="2026-10-01T10:04:00+09:00")
        with self.assertRaisesRegex(ValueError, "immutable"): self.store.append(record, 3, "2026-10-01T10:04:00+09:00")


if __name__ == "__main__": unittest.main()
