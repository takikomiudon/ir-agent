"""Memory-only contracts for trusted save receipts and historical imports."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import sqlite3
import unittest

from ir_agent.availability import RecordAvailability, SCHEMA
from ir_agent.models import json_text


EARLY = "2026-10-09T16:00:00+09:00"
BEFORE = "2026-10-09T17:30:00+09:00"
SAVED = "2026-10-09T18:00:00+09:00"
LATER = "2026-10-09T19:00:00+09:00"


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA)
        self.db.execute("CREATE TABLE base_records(id TEXT PRIMARY KEY, data TEXT)")
        self.addCleanup(self.db.close)
        self.records = RecordAvailability(self.db)
        self.source = {"id": "s1", "company_id": "demo", "content": "Fictional original text",
                       "retrieved_at": EARLY, "published_at": EARLY}

    def insert(self, snapshot=None, *, kind="source", version=None, now=SAVED, legacy=False):
        value = self.source if snapshot is None else snapshot
        record_id = value["company_id"] if kind == "thesis" else value["id"]
        with self.db:
            self.db.execute("BEGIN")
            call = self.records.observe_existing if legacy else self.records.record_first_save
            return call(kind, record_id, value, version=version, now=now)

    def at(self, *, snapshot=None, as_of=BEFORE, knowledge_at=BEFORE, now=LATER):
        return self.records.at("source", "s1", self.source if snapshot is None else snapshot,
                               as_of=as_of, knowledge_at=knowledge_at, now=now)

    def test_insert_preserves_original_json_and_canonical_digest(self):
        original = deepcopy(self.source)
        receipt = self.insert()
        self.assertEqual(self.source, original)
        self.assertEqual(receipt["snapshot_sha256"], sha256(json_text(original).encode()).hexdigest())
        self.assertEqual(receipt["first_saved_at"], "2026-10-09T09:00:00.000000+00:00")
        self.assertEqual(receipt["first_saved_at"], receipt["presence_observed_at"])
        self.assertEqual(receipt["basis"], "trusted_insert")
        self.assertEqual(receipt["version"], 0)
        # Equivalent object key order is the same canonical snapshot.
        reordered = dict(reversed(list(self.source.items())))
        self.assertEqual(self.insert(reordered, now=LATER), receipt)
        self.assertEqual(self.insert(now=LATER, legacy=True), receipt)
        receipt["first_saved_at"] = "changed detached result"
        self.assertNotEqual(self.records.get("source", "s1")["first_saved_at"], receipt["first_saved_at"])

    def test_identity_and_snapshot_reuse_are_rejected_without_overwriting(self):
        first = self.insert()
        changed = {**self.source, "content": "Changed original"}
        with self.assertRaisesRegex(ValueError, "different snapshot"):
            self.insert(changed, now=LATER)
        self.assertEqual(self.records.get("source", "s1"), first)
        with self.db:
            self.db.execute("BEGIN")
            with self.assertRaisesRegex(ValueError, "identity"):
                self.records.record_first_save("source", "other", self.source, now=SAVED)
        with self.assertRaisesRegex(ValueError, "different snapshot"):
            self.at(snapshot=changed)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM record_availability").fetchone()[0], 1)

    def test_legacy_presence_keeps_first_save_unknown_after_retry(self):
        first = self.insert(legacy=True)
        self.assertIsNone(first["first_saved_at"])
        self.assertEqual(first["basis"], "legacy_presence")
        old = self.at()
        self.assertEqual(old["status"], "unknown")
        self.assertIsNone(old["available"])
        self.assertIn("legacy_history_unknown", old["reason_codes"])
        current = self.at(as_of=SAVED, knowledge_at=SAVED)
        self.assertEqual(current["status"], "available")
        self.assertFalse(current["first_save_known"])
        self.assertEqual(current["known_by_at"], first["presence_observed_at"])
        self.assertEqual(self.insert(now=LATER), first)
        self.assertEqual(self.insert(now=LATER, legacy=True), first)

    def test_missing_receipt_is_unknown_and_read_does_not_create_one(self):
        result = self.at()
        self.assertEqual(result["status"], "unknown")
        self.assertIsNone(result["receipt"])
        self.assertFalse(result["first_save_known"])
        self.assertIn("availability_receipt_missing", result["reason_codes"])
        self.assertIsNone(self.records.get("source", "s1"))
        self.assertFalse(self.db.in_transaction)

    def test_event_and_knowledge_axes_are_independent_and_exact_at_boundary(self):
        self.insert()
        old = self.at()
        self.assertEqual(old["status"], "unavailable")
        self.assertIn("first_saved_after_knowledge_at", old["reason_codes"])
        retrospective = self.at(knowledge_at=SAVED)
        self.assertEqual(retrospective["status"], "available")
        self.assertEqual(retrospective["effective_fields"]["retrieved_at"], "2026-10-09T07:00:00+00:00")
        self.assertEqual(self.at(as_of=SAVED, knowledge_at=SAVED)["status"], "available")
        before_event = self.at(as_of="2026-10-09T15:59:59.999999+09:00", knowledge_at=LATER)
        self.assertEqual(before_event["status"], "unavailable")
        self.assertIn("effective_time_after_as_of", before_event["reason_codes"])

    def test_snapshot_types_reserved_server_fields_and_identity_versions(self):
        cases = [
            {**self.source, "first_saved_at": EARLY},
            {**self.source, "presence_observed_at": EARLY},
            {**self.source, "record_availability": {}},
            {**self.source, "bad": float("nan")},
            {**self.source, "bad": float("inf")},
            {**self.source, "bad": {1: "non-string key"}},
            {**self.source, "bad": (1, 2)},
            {**self.source, "retrieved_at": "2026-10-09T10:00:00"},
            {**self.source, "content": "\ud800"},
        ]
        for value in cases:
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                self.insert(value)
        for kind, version in (([], None), ({}, None), ("unknown", None),
                              ("source", True), ("source", 1), ("source", 0.0),
                              ("thesis", None), ("thesis", True), ("thesis", 0),
                              ("thesis", 2**63)):
            with self.subTest(kind=kind, version=version), self.assertRaises(ValueError):
                self.records.get(kind, "s1", version=version)
        self.assertIsNone(self.records.get("source", "s1", version=0))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM record_availability").fetchone()[0], 0)

    def test_all_entity_types_and_versioned_thesis_are_separate(self):
        snapshots = [
            ("thesis", {"company_id": "demo", "version": 1, "recorded_at": EARLY}, 1),
            ("thesis", {"company_id": "demo", "version": 2, "recorded_at": BEFORE}, 2),
            ("reply", {"id": "s1", "received_at": EARLY, "raw_text": "Fictional reply"}, None),
            ("question", {"id": "s1", "created_at": EARLY, "question": "Fictional question"}, None),
        ]
        self.insert()
        for kind, snapshot, version in snapshots:
            receipt = self.insert(snapshot, kind=kind, version=version)
            record_id = "demo" if kind == "thesis" else "s1"
            result = self.records.at(kind, record_id, snapshot, version=version,
                                     as_of=SAVED, knowledge_at=SAVED, now=SAVED)
            self.assertEqual(result["status"], "available")
            self.assertEqual(result["receipt"], receipt)
        with self.assertRaisesRegex(ValueError, "version"):
            self.insert(snapshots[0][1], kind="thesis", version=2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM record_availability").fetchone()[0], 5)

    def test_future_effective_times_cutoffs_and_naive_runtime_are_rejected(self):
        with self.db:
            self.db.execute("BEGIN")
            with self.assertRaisesRegex(ValueError, "future"):
                self.records.record_first_save("source", "s1", {**self.source, "retrieved_at": LATER}, now=SAVED)
            for call in (self.records.record_first_save, self.records.observe_existing):
                with self.assertRaisesRegex(ValueError, "timezone"):
                    call("source", "s1", self.source, now=datetime(2026, 10, 9, 10))
        for as_of, knowledge in ((LATER, SAVED), (SAVED, LATER)):
            with self.assertRaisesRegex(ValueError, "cutoffs"):
                self.at(as_of=as_of, knowledge_at=knowledge, now=SAVED)
        with self.assertRaisesRegex(ValueError, "publication"):
            self.insert({**self.source, "published_at": BEFORE})
        self.assertIsNone(self.records.get("source", "s1"))

    def test_clock_rollback_does_not_mint_or_modify_receipts(self):
        original = self.insert()
        for snapshot in (self.source, {**self.source, "id": "s2"}):
            with self.assertRaisesRegex(ValueError, "clock"):
                self.insert(snapshot, now=BEFORE)
        self.assertEqual(self.records.get("source", "s1"), original)
        self.assertIsNone(self.records.get("source", "s2"))
        held = self.at(now=BEFORE)
        self.assertEqual(held["status"], "unknown")
        self.assertIn("availability_clock_anomaly", held["reason_codes"])

    def test_open_transaction_required_and_outer_rollback_includes_base_and_receipt(self):
        with self.assertRaisesRegex(ValueError, "transaction"):
            self.records.record_first_save("source", "s1", self.source, now=SAVED)
        with self.assertRaisesRegex(RuntimeError, "later failure"):
            with self.db:
                self.db.execute("INSERT INTO base_records VALUES (?,?)", ("s1", json_text(self.source)))
                self.records.record_first_save("source", "s1", self.source, now=SAVED)
                self.assertTrue(self.db.in_transaction)
                raise RuntimeError("later failure")
        self.assertIsNone(self.records.get("source", "s1"))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM base_records").fetchone()[0], 0)

    def test_savepoint_rollback_and_conflict_keep_outer_transaction(self):
        with self.db:
            self.db.execute("INSERT INTO base_records VALUES ('outer','retained')")
            self.db.execute("SAVEPOINT classification")
            self.records.record_first_save("source", "s1", self.source, now=SAVED)
            self.db.execute("ROLLBACK TO SAVEPOINT classification")
            self.db.execute("RELEASE SAVEPOINT classification")
            self.assertIsNone(self.records.get("source", "s1"))
            self.assertTrue(self.db.in_transaction)
            first = self.records.record_first_save("source", "s1", self.source, now=SAVED)
            with self.assertRaisesRegex(ValueError, "different snapshot"):
                self.records.record_first_save("source", "s1", {**self.source, "content": "tampered"}, now=SAVED)
            self.assertTrue(self.db.in_transaction)
            self.assertEqual(self.records.get("source", "s1"), first)
        self.assertEqual(self.db.execute("SELECT data FROM base_records WHERE id='outer'").fetchone()[0], "retained")

    def test_date_offset_equivalence_and_stored_invalid_clock_are_not_silently_success(self):
        now = datetime(2026, 10, 9, 9, tzinfo=timezone.utc)
        receipt = self.insert(now=now)
        self.assertEqual(receipt["first_saved_at"], "2026-10-09T09:00:00.000000+00:00")
        # Direct DB corruption is outside the trusted write API, but the view
        # must not count an unreadable timestamp as successful availability.
        with self.db:
            self.db.execute("UPDATE record_availability SET first_saved_at='bad',presence_observed_at='bad'")
        held = self.at(as_of=SAVED, knowledge_at=SAVED)
        self.assertEqual(held["status"], "unknown")
        self.assertIn("availability_receipt_invalid", held["reason_codes"])

    def test_two_connections_share_cas_identity_without_replacing_receipt(self):
        # SQLite serializes writers; distinct connections must still use the
        # stored primary-key receipt rather than a per-object identity cache.
        uri = "file:availability-cas-test?mode=memory&cache=shared"
        first_db = sqlite3.connect(uri, uri=True)
        self.addCleanup(first_db.close)
        first_db.executescript(SCHEMA)
        second_db = sqlite3.connect(uri, uri=True)
        self.addCleanup(second_db.close)
        first_store, second_store = RecordAvailability(first_db), RecordAvailability(second_db)
        with first_db:
            first_db.execute("BEGIN")
            original = first_store.record_first_save("source", "s1", self.source, now=SAVED)
        with second_db:
            second_db.execute("BEGIN")
            self.assertEqual(second_store.record_first_save("source", "s1", self.source, now=LATER), original)
        with self.assertRaisesRegex(ValueError, "different snapshot"), second_db:
            second_db.execute("BEGIN")
            second_store.record_first_save("source", "s1", {**self.source, "content": "other worker"}, now=LATER)
        self.assertEqual(first_store.get("source", "s1"), original)

    def test_legacy_future_effective_time_does_not_prevent_presence_observation(self):
        future = {**self.source, "retrieved_at": LATER}
        receipt = self.insert(future, legacy=True)
        self.assertEqual(receipt["basis"], "legacy_presence")
        self.assertIsNone(receipt["first_saved_at"])
        held = self.at(snapshot=future, as_of=SAVED, knowledge_at=SAVED, now=SAVED)
        self.assertEqual(held["status"], "unavailable")
        self.assertIn("effective_time_after_as_of", held["reason_codes"])
        # First save stays unknown even after the declared future time passes.
        after = self.at(snapshot=future, as_of=LATER, knowledge_at=LATER, now=LATER)
        self.assertEqual(after["status"], "available")
        self.assertFalse(after["first_save_known"])

    def test_legacy_invalid_effective_time_is_unknown_without_rewriting_raw(self):
        for invalid in ("bad", None, 123, "2026-10-09T18:00:00"):
            snapshot = {**self.source, "id": "invalid-" + repr(invalid), "retrieved_at": invalid}
            original = deepcopy(snapshot)
            receipt = self.insert(snapshot, legacy=True)
            self.assertEqual(snapshot, original)
            self.assertIsNone(receipt["first_saved_at"])
            result = self.records.at("source", snapshot["id"], snapshot,
                                     as_of=SAVED, knowledge_at=SAVED, now=SAVED)
            self.assertEqual(result["status"], "unknown")
            self.assertIn("invalid_effective_time", result["reason_codes"])
            self.assertEqual(self.insert(snapshot, legacy=True, now=BEFORE), receipt)

    def test_legacy_clock_rollback_keeps_existing_and_does_not_mint_earlier_new_proof(self):
        first = self.insert(now=LATER)
        # A reopen retains a matching existing receipt without requiring its
        # timestamp to be valid under today's clock. PIT remains held.
        self.assertEqual(self.insert(legacy=True, now=SAVED), first)
        self.assertIn("availability_clock_anomaly", self.at(now=SAVED)["reason_codes"])
        second = {**self.source, "id": "s2"}
        skipped = self.insert(second, legacy=True, now=SAVED)
        self.assertEqual(skipped["status"], "unknown")
        self.assertIn("availability_clock_anomaly", skipped["reason_codes"])
        self.assertIsNone(self.records.get("source", "s2"))
        # A later honest observation can establish only its own known-by bound.
        observed = self.insert(second, legacy=True, now=LATER)
        self.assertEqual(observed["presence_observed_at"], first["presence_observed_at"])
        self.assertIsNone(observed["first_saved_at"])

    def test_legacy_server_named_raw_fields_cannot_become_save_proof(self):
        old = {**self.source, "first_saved_at": EARLY, "presence_observed_at": EARLY}
        receipt = self.insert(old, legacy=True)
        self.assertIsNone(receipt["first_saved_at"])
        self.assertNotEqual(receipt["presence_observed_at"], EARLY)
        result = self.at(snapshot=old)
        self.assertEqual(result["status"], "unknown")
        self.assertIn("legacy_history_unknown", result["reason_codes"])


if __name__ == "__main__":
    unittest.main()
