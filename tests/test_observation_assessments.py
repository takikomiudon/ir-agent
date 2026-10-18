"""Finite corrections preserve originals, population, cutoff visibility and CAS."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

from ir_agent.models import json_text, validate_source
from ir_agent.observation_assessments import digest
from ir_agent.observation_store import ObservationStore, SCHEMA
from ir_agent.observations import summarize_observations

FIRST = "2026-11-02T16:00:00+09:00"
CORRECTED = "2026-11-03T16:00:00+09:00"
LATER = "2026-11-04T16:00:00+09:00"


def fixture():
    return json.loads((Path(__file__).resolve().parents[1] / "examples/ir-observations.json").read_text())["records"][0]


class ObservationAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.addCleanup(self.db.close); self.db.executescript(SCHEMA)
        self.store = ObservationStore(self.db)
        self.record = fixture()

    def saved_basis(self):
        self.db.executescript("CREATE TABLE sources(id TEXT PRIMARY KEY,data TEXT); CREATE TABLE replies(id TEXT PRIMARY KEY,data TEXT); CREATE TABLE questions(id TEXT PRIMARY KEY,data TEXT);")
        self.raw_text = "Synthetic reply. The cost is recurring. This repeats an existing public explanation."
        self.raw_reply = {"id": self.record["replies"][0]["id"], "question_id": self.record["question_id"],
                          "received_at": self.record["replies"][0]["received_at"], "raw_text": self.raw_text,
                          "information_status": "public_clarification"}
        self.public = validate_source({"id": "public-proof", "company_id": self.record["company_id"],
                                      "title": "Synthetic public proof", "url": "https://example.invalid/proof",
                                      "source_type": "public_disclosure", "published_at": "2026-10-02T08:00:00+09:00",
                                      "retrieved_at": "2026-10-02T09:00:00+09:00",
                                      "content": "The cost is recurring. The merger did not change the target accounting period.", "metadata": {}})
        self.db.execute("INSERT INTO sources VALUES (?,?)", (self.public["id"], json_text(self.public)))
        self.db.execute("INSERT INTO replies VALUES (?,?)", (self.raw_reply["id"], json_text(self.raw_reply)))
        self.db.execute("INSERT INTO questions VALUES (?,?)", (self.record["question_id"], json_text({"id": self.record["question_id"], "company_id": self.record["company_id"]})))

    def event(self, *, kind="reply", version=1, when=CORRECTED, assessment=None, bound=True):
        target = self.record["replies"][0] if kind == "reply" else self.record["external_changes"][0]
        if assessment is None:
            assessment = {"signal": "persistent_explanation", "information_status": "public_clarification"} if kind == "reply" else {"impact": "reviewed_no_change"}
        basis = {}
        if bound:
            body = self.raw_text if kind == "reply" else target["description"]
            basis = {"target_text_reference": target["id"], "target_text_sha256": sha256(body.encode()).hexdigest(),
                     "basis_quote": "cost is recurring" if kind == "reply" else target["description"],
                     "public_evidence_references": [{"source_id": self.public["id"], "source_sha256": digest(self.public), "basis_quote": "The cost is recurring."}]}
        return {"id": "correction-" + str(version), "target_kind": kind, "target_id": target["id"],
                "target_snapshot_sha256": digest(target), "version": version, "expected_previous_version": version-1,
                "recorded_at": when, "reviewer": "synthetic-test-reviewer", "rationale": "Correct the recorded interpretation using saved evidence.",
                "basis": basis, "assessment": assessment}

    def summary(self, as_of=LATER):
        return summarize_observations(self.store.records_as_of(as_of), as_of=as_of)

    def register_real_held_record(self):
        # Test a live-mode boundary with invented records, not a real IR case.
        self.record["synthetic"] = False
        self.record["replies"][0]["information_status"] = "unclear"
        design = deepcopy(self.record)
        for key in ("dispatch", "response_check", "verification"): design.pop(key)
        design["replies"] = []
        self.store.register(design, "2026-10-01T10:01:00+09:00")
        self.store.append(self.record, 1, FIRST)

    def test_real_observation_rejects_synthetic_root_and_second_origin(self):
        self.saved_basis(); self.register_real_held_record()
        first = deepcopy(self.public); first["id"] = "first-parent"
        second = deepcopy(self.public); second.update(id="second-parent", metadata={"synthetic": True})
        for source in (first, second):
            self.db.execute("INSERT INTO sources VALUES (?,?)", (source["id"], json_text(source)))
        before = self.store.history(self.record["id"])
        for metadata in ({"synthetic": True}, {"original_source_ids": [first["id"], second["id"]]}):
            self.public["metadata"] = metadata
            self.db.execute("UPDATE sources SET data=? WHERE id=?", (json_text(self.public), self.public["id"]))
            request = deepcopy(self.record); request["assessments"] = [self.event()]
            with self.subTest(metadata=metadata), self.assertRaisesRegex(ValueError, "Synthetic"):
                self.store.append(request, 2, CORRECTED)
            self.assertEqual(self.summary()["eligible_count"], 0)
            self.assertEqual(self.store.history(self.record["id"]), before)

    def test_trusted_save_time_checks_known_hold_but_retry_reuses_old_binding(self):
        self.saved_basis(); self.register_real_held_record()
        parent = deepcopy(self.public); parent.update(id="reply-parent", source_type="ir_reply",
            metadata={"reply_id": "upstream-reply", "information_status": "public_clarification"})
        self.db.execute("INSERT INTO sources VALUES (?,?)", (parent["id"], json_text(parent)))
        self.public["metadata"] = {"original_source_id": parent["id"]}
        self.db.execute("UPDATE sources SET data=? WHERE id=?", (json_text(self.public), self.public["id"]))
        self.db.execute("CREATE TABLE reply_information_reviews(reply_id TEXT,version INTEGER,data TEXT,first_saved_at TEXT,PRIMARY KEY(reply_id,version))")
        hold_time = "2026-11-03T17:00:00+09:00"
        review = {"reply_id": "upstream-reply", "version": 1, "recorded_at": hold_time,
                  "information_status": "potential_nonpublic", "first_saved_at": hold_time}
        self.db.execute("INSERT INTO reply_information_reviews VALUES (?,?,?,?)", (review["reply_id"], 1, json_text(review), hold_time))
        request = deepcopy(self.record); request["assessments"] = [self.event()]
        before = self.store.history(self.record["id"])
        with self.assertRaisesRegex(ValueError, "held information correction"):
            self.store.append(request, 2, LATER)
        self.assertEqual(self.summary()["eligible_count"], 0)
        self.assertEqual(self.store.history(self.record["id"]), before)
        # With an injected earlier trusted clock the later hold is not yet
        # visible. A subsequent transport retry preserves that saved result.
        earlier = self.store.append(request, 2, CORRECTED)
        retried = self.store.append(request, 2, LATER)
        self.assertEqual(retried["version"], earlier["version"])
        self.assertEqual(retried["record"], earlier["record"])
        self.assertEqual(retried["first_saved_at"], earlier["first_saved_at"])
        self.assertEqual(self.summary(FIRST)["eligible_count"], 0)

    def test_bound_signal_correction_preserves_originals_and_population_and_retries(self):
        self.saved_basis(); original = self.store.register(self.record, FIRST)
        request = deepcopy(self.record); request["assessments"] = [self.event()]; before = deepcopy(request)
        corrected = self.store.append(request, 1, CORRECTED)
        self.assertEqual(corrected["record"]["assessments"][0]["basis_verification"]["status"], "verified")
        self.assertEqual(corrected["design_sha256"], original["design_sha256"])
        self.assertEqual(corrected["record"]["replies"], self.record["replies"])
        self.assertEqual(self.store.history(self.record["id"])[0]["record"], self.record)
        summary = self.summary(); view = summary["observations"][0]
        self.assertEqual(summary["record_count"], 1); self.assertEqual(summary["eligible_count"], 1)
        self.assertEqual(view["signal"], "persistent_explanation")
        self.assertEqual(view["assessment_views"][0]["original_classification"]["signal"], "temporary_explanation")
        retried = self.store.append(request, 1, LATER)
        self.assertEqual(retried["version"], 2); self.assertEqual(retried["first_saved_at"], corrected["first_saved_at"])
        self.assertEqual(request, before)
        self.assertEqual(json.loads(self.db.execute("SELECT data FROM replies").fetchone()[0]), self.raw_reply)

    def test_standalone_database_allows_only_unbound_safety_hold_then_rejects_upgrade(self):
        self.store.register(self.record, FIRST)
        value = deepcopy(self.record)
        value["assessments"] = [self.event(bound=False, assessment={"signal": "temporary_explanation", "information_status": "unclear"})]
        held = self.store.append(value, 1, CORRECTED)
        self.assertEqual(self.summary()["eligible_count"], 0)
        self.assertEqual(held["record"]["assessments"][0]["basis_verification"]["status"], "unverified")
        second = self.event(version=2, when=LATER, bound=False)
        value["assessments"].append(second)
        with self.assertRaisesRegex(ValueError, "Independent saved evidence"):
            self.store.append(value, 2, LATER)
        self.assertEqual(len(self.store.history(self.record["id"])), 2)

    def test_publicity_withdrawal_and_reaffirmation_do_not_rewrite_past_views(self):
        self.saved_basis(); self.store.register(self.record, FIRST)
        value = deepcopy(self.record)
        value["assessments"] = [self.event(bound=False, assessment={"signal": "temporary_explanation", "information_status": "potential_nonpublic"})]
        self.store.append(value, 1, CORRECTED)
        self.assertEqual(self.summary(FIRST)["eligible_count"], 1)
        self.assertEqual(self.summary(CORRECTED)["eligible_count"], 0)
        value["assessments"].append(self.event(version=2, when=LATER))
        self.store.append(value, 2, LATER)
        self.assertEqual(self.summary(LATER)["eligible_count"], 1)
        self.assertEqual(self.summary(CORRECTED)["eligible_count"], 0)

    def test_unbound_hold_after_signal_correction_preserves_current_signal(self):
        self.saved_basis(); self.store.register(self.record, FIRST)
        value = deepcopy(self.record); value["assessments"] = [self.event()]
        self.store.append(value, 1, CORRECTED)
        value["assessments"].append(self.event(version=2, when=LATER, bound=False,
            assessment={"signal": "persistent_explanation", "information_status": "unclear"}))
        self.store.append(value, 2, LATER)
        view = self.summary()["observations"][0]
        self.assertEqual(view["assessment_views"][0]["effective_classification"],
                         {"signal": "persistent_explanation", "information_status": "unclear"})
        self.assertEqual(self.summary()["eligible_count"], 0)

    def test_declared_record_time_cannot_make_correction_visible_before_actual_save(self):
        self.saved_basis(); self.store.register(self.record, FIRST)
        value = deepcopy(self.record); value["assessments"] = [self.event()]
        self.store.append(value, 1, LATER)
        self.assertEqual(self.summary(CORRECTED)["observations"][0]["signal"], "temporary_explanation")
        self.assertEqual(self.summary(LATER)["observations"][0]["signal"], "persistent_explanation")

    def test_raw_sha_quote_identity_and_target_hash_mismatches_do_not_write(self):
        self.saved_basis(); self.store.register(self.record, FIRST)
        changes = [lambda e: e.update(target_snapshot_sha256="0"*64),
                   lambda e: e["basis"].update(target_text_sha256="0"*64),
                   lambda e: e["basis"].update(basis_quote="not present in received text"),
                   lambda e: e["basis"]["public_evidence_references"][0].update(source_sha256="0"*64),
                   lambda e: e["basis"]["public_evidence_references"][0].update(basis_quote="not a public quote"),
                   lambda e: e.update(target_id="another-reply"),
                   lambda e: e["assessment"].update(signal=[])]
        for index, change in enumerate(changes):
            event = self.event(); change(event); value = deepcopy(self.record); value["assessments"] = [event]
            with self.subTest(case=index), self.assertRaises(ValueError): self.store.append(value, 1, CORRECTED)
        self.assertEqual(len(self.store.history(self.record["id"])), 1)

    def test_second_source_parent_future_other_company_and_nonpublic_are_not_hidden(self):
        self.saved_basis(); self.store.register(self.record, FIRST)
        first = deepcopy(self.public); first["id"] = "first-parent"
        self.db.execute("INSERT INTO sources VALUES (?,?)", (first["id"], json_text(first)))
        for damage in ("future", "other-company", "nonpublic"):
            second = deepcopy(self.public); second["id"] = "second-parent"
            if damage == "future": second["retrieved_at"] = "2026-12-01T00:00:00+09:00"
            elif damage == "other-company": second["company_id"] = "other"
            else: second.update(source_type="ir_reply", metadata={"information_status": "potential_nonpublic"})
            self.public["metadata"] = {"original_source_ids": [first["id"], second["id"]]}
            self.db.execute("INSERT OR REPLACE INTO sources VALUES (?,?)", (second["id"], json_text(second)))
            self.db.execute("UPDATE sources SET data=? WHERE id=?", (json_text(self.public), self.public["id"]))
            value = deepcopy(self.record); value["assessments"] = [self.event()]
            with self.subTest(damage=damage), self.assertRaises(ValueError): self.store.append(value, 1, CORRECTED)
        self.assertEqual(len(self.store.history(self.record["id"])), 1)

    def test_saved_reply_question_and_company_are_independently_matched(self):
        self.saved_basis(); self.store.register(self.record, FIRST)
        for field, wrong in (("id", "other-reply"), ("question_id", "other-question")):
            damaged = deepcopy(self.raw_reply); damaged[field] = wrong
            self.db.execute("UPDATE replies SET data=?", (json_text(damaged),))
            value = deepcopy(self.record); value["assessments"] = [self.event()]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "another question or company"):
                self.store.append(value, 1, CORRECTED)
        self.db.execute("UPDATE replies SET data=?", (json_text(self.raw_reply),))
        self.db.execute("UPDATE questions SET data=?", (json_text({"id": self.record["question_id"], "company_id": "other-company"}),))
        with self.assertRaisesRegex(ValueError, "another question or company"):
            self.store.append(value, 1, CORRECTED)
        self.assertEqual(len(self.store.history(self.record["id"])), 1)

    def test_external_resolution_does_not_override_other_unresolved_changes(self):
        self.record["external_changes"] = [{"id": "merger", "occurred_at": "2026-10-03T00:00:00+09:00", "recorded_at": "2026-10-03T01:00:00+09:00", "description": "A synthetic merger occurred", "impact": "unresolved"},
                                          {"id": "other-change", "occurred_at": "2026-10-04T00:00:00+09:00", "recorded_at": "2026-10-04T01:00:00+09:00", "description": "Another synthetic change", "impact": "unresolved"}]
        self.saved_basis(); self.store.register(self.record, FIRST)
        value = deepcopy(self.record); value["assessments"] = [self.event(kind="external_change")]
        self.store.append(value, 1, CORRECTED)
        view = self.summary()["observations"][0]
        self.assertIn("external_change_blocks_state_inference", view["exclusion_reasons"])
        self.assertFalse(view["eligible_for_descriptive_table"])
        self.assertEqual(self.store.history(self.record["id"])[1]["record"]["external_changes"], self.record["external_changes"])

    def test_resolved_external_impact_does_not_invent_verified_state(self):
        self.record["external_changes"] = [{"id": "merger", "occurred_at": "2026-10-03T00:00:00+09:00",
            "recorded_at": "2026-10-03T01:00:00+09:00", "description": "A synthetic merger occurred", "impact": "unresolved"}]
        self.record["verification"]["status"] = "state_changed"
        self.record["verification"].pop("state")
        self.saved_basis(); self.store.register(self.record, FIRST)
        value = deepcopy(self.record); value["assessments"] = [self.event(kind="external_change")]
        self.store.append(value, 1, CORRECTED)
        view = self.summary()["observations"][0]
        self.assertNotIn("external_change_blocks_state_inference", view["exclusion_reasons"])
        self.assertIn("verification_state_changed", view["exclusion_reasons"])
        self.assertFalse(view["eligible_for_descriptive_table"]); self.assertIsNone(view["state"])

    def test_late_reply_stays_late_and_no_response_signal_is_not_replaced(self):
        self.record["replies"][0].update(received_at="2026-10-10T10:00:00+09:00", recorded_at="2026-10-10T10:01:00+09:00")
        self.saved_basis(); self.store.register(self.record, FIRST)
        value = deepcopy(self.record); value["assessments"] = [self.event()]
        self.store.append(value, 1, CORRECTED)
        result = self.summary()
        self.assertEqual(result["response_counts"], {"no_response_by_deadline": 1})
        self.assertEqual(result["records_with_late_replies"], 1)
        self.assertEqual(result["observations"][0]["signal"], "no_response_by_deadline")

    def test_forged_approval_future_stale_cas_and_same_append_target_are_rejected(self):
        self.saved_basis(); self.store.register(self.record, FIRST)
        event = self.event(); forged = deepcopy(event)
        forged.update(request=deepcopy(event), first_saved_at=CORRECTED, basis_verification={"status": "verified", "reason_codes": [], "source_snapshots": {}})
        value = deepcopy(self.record); value["assessments"] = [forged]
        with self.assertRaisesRegex(ValueError, "caller"): self.store.append(value, 1, CORRECTED)
        value["assessments"] = [self.event(when=LATER)]
        with self.assertRaisesRegex(ValueError, "future"): self.store.append(value, 1, CORRECTED)
        value["assessments"] = [event]
        with self.assertRaisesRegex(ValueError, "Stale"): self.store.append(value, 2, CORRECTED)
        new_target = deepcopy(value["replies"][0]); new_target["id"] = "new-target"
        new_target["recorded_at"] = CORRECTED
        value["replies"].append(new_target)
        value["assessments"][0].update(target_id=new_target["id"], target_snapshot_sha256=digest(new_target))
        with self.assertRaisesRegex(ValueError, "outside this observation"):
            self.store.append(value, 1, CORRECTED)
        self.assertEqual(len(self.store.history(self.record["id"])), 1)

    def test_target_version_gaps_and_saved_prefix_edits_are_rejected(self):
        self.saved_basis(); self.store.register(self.record, FIRST)
        value = deepcopy(self.record); value["assessments"] = [self.event(version=2)]
        with self.assertRaisesRegex(ValueError, "CAS chain"):
            self.store.append(value, 1, CORRECTED)
        value["assessments"] = [self.event()]
        stored = self.store.append(value, 1, CORRECTED)["record"]
        changed = deepcopy(stored); changed["assessments"][0]["rationale"] = "Changed old reason"
        with self.assertRaises(ValueError): self.store.append(changed, 2, LATER)
        deleted = deepcopy(stored); deleted["assessments"] = []
        with self.assertRaisesRegex(ValueError, "prefix-only"): self.store.append(deleted, 2, LATER)
        self.assertEqual(len(self.store.history(self.record["id"])), 2)

    def test_failure_after_insert_and_outer_rollback_keep_ledger_atomic(self):
        self.saved_basis(); self.store.register(self.record, FIRST)
        value = deepcopy(self.record); value["assessments"] = [self.event()]
        original = self.store._versions
        def fail_after_insert(observation_id):
            rows = original(observation_id)
            if len(rows) > 1: raise ValueError("injected post-insert failure")
            return rows
        with patch.object(self.store, "_versions", side_effect=fail_after_insert):
            with self.assertRaisesRegex(ValueError, "post-insert"): self.store.append(value, 1, CORRECTED)
        self.assertEqual(len(self.store.history(self.record["id"])), 1)
        self.db.execute("BEGIN IMMEDIATE")
        self.store.append(value, 1, CORRECTED)
        self.assertTrue(self.db.in_transaction); self.db.execute("ROLLBACK")
        self.assertEqual(len(self.store.history(self.record["id"])), 1)


if __name__ == "__main__": unittest.main()
