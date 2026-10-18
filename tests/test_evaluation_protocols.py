"""Synthetic protocol commitments only; no actual labels or trading rules."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from ir_agent.evaluation_protocols import COHORT_FIELDS, RULE_FIELDS, EvaluationProtocols, SCHEMA
from ir_agent.models import json_text


RECORDED = "2026-10-01T09:00:00+09:00"
SAVED = "2026-10-15T01:00:00+00:00"
LATER = "2026-10-15T01:05:00+00:00"


def draft(protocol_id="synthetic-protocol", version=1):
    return {
        "id": protocol_id, "version": version, "recorded_at": RECORDED,
        "recorded_by": "synthetic-test-recorder", "evaluation_task": None,
        "cohort": dict.fromkeys(sorted(COHORT_FIELDS)), "model_refs": [],
        "rules": dict.fromkeys(sorted(RULE_FIELDS)), "source_refs": [],
    }


def declared(protocol_id="synthetic-protocol", version=1):
    value = draft(protocol_id, version)
    value["evaluation_task"] = "Synthetic conditional-signal task declaration, not an adopted procedure."
    value["cohort"] = {
        "id": "synthetic-unresolved-cohort", "design_version": 1,
        "definition_sha256": "a" * 64, "state_timing": "at_question",
        "target_period": {"start": "2026-10-01", "end": "2026-10-31"},
        "question_type": "synthetic test only",
        "states": {"test_state": "Synthetic category definition."},
        "signals": {"test_signal": "Synthetic reply category definition."},
        "synthetic": True,
    }
    value["model_refs"] = [{
        "id": "synthetic-unresolved-model", "version": 1,
        "commitment_sha256": "b" * 64,
        "training_information_cutoff": "2026-10-01T00:00:00+00:00",
    }]
    value["source_refs"] = [{
        "source_id": "synthetic-unresolved-source", "content_sha256": "c" * 64,
        "quote_ids": ["synthetic-unresolved-quote"],
        "purpose": "Synthetic assertion of a reference; no quote or adoption is verified.",
    }]
    value["rules"] = {key: "Synthetic procedure text only; never execute or approve this fixture."
                      for key in RULE_FIELDS}
    return value


class EvaluationProtocolTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.addCleanup(self.db.close)
        self.db.executescript(SCHEMA)
        self.registry = EvaluationProtocols(self.db)

    def count(self):
        return self.db.execute("SELECT COUNT(*) FROM ir_evaluation_protocol_versions").fetchone()[0]

    def test_draft_preserves_nulls_hash_and_trusted_save_without_invented_rules(self):
        request = draft()
        before = deepcopy(request)
        result = self.registry.register(request, 0, now=SAVED)
        self.assertEqual(request, before)
        self.assertEqual(result["request"], before)
        self.assertEqual(result["status"], "protocol_commitment_only")
        self.assertTrue(result["draft"])
        self.assertTrue(result["added"])
        self.assertEqual(result["first_saved_at"], "2026-10-15T01:00:00.000000+00:00")
        self.assertEqual(result["request_sha256"], sha256(json_text(before).encode()).hexdigest())
        self.assertEqual(set(result["unset_fields"]),
                         {"evaluation_task", "model_refs", "source_refs"}
                         | {"cohort." + field for field in COHORT_FIELDS}
                         | {"rules." + field for field in RULE_FIELDS})
        self.assertTrue(all(value is None for value in result["request"]["rules"].values()))
        json.dumps(result, allow_nan=False)

    def test_whole_cohort_null_and_partial_reference_drafts_are_explicit(self):
        request = draft()
        request["cohort"] = None
        request["model_refs"] = [{"id": "synthetic-model", "version": 1,
                                  "commitment_sha256": None, "training_information_cutoff": None}]
        request["source_refs"] = [{"source_id": "synthetic-source", "content_sha256": None,
                                   "quote_ids": [], "purpose": "Synthetic pending reference."}]
        result = self.registry.register(request, 0, now=SAVED)
        for field in ("cohort", "model_refs[0].commitment_sha256",
                      "model_refs[0].training_information_cutoff",
                      "source_refs[0].content_sha256", "source_refs[0].quote_ids"):
            self.assertIn(field, result["unset_fields"])

    def test_fully_declared_fields_do_not_verify_references_or_unlock_evaluation(self):
        result = self.registry.register(declared(), 0, now=SAVED)
        self.assertFalse(result["draft"])
        self.assertEqual(result["unset_fields"], [])
        self.assertEqual(result["status"], "protocol_commitment_only")
        for key in ("cohort_reference", "model_references", "source_references", "source_quotes",
                    "author_principle_adoption", "rule_correctness", "prospectiveness",
                    "blindness", "independence"):
            self.assertEqual(result["verification"][key], "unverified")
        self.assertEqual(result["verification"]["execution"], "not_performed")
        self.assertEqual(result["verification"]["score_eligibility"], "not_assessed")
        self.assertNotIn("state", result)
        self.assertNotIn("score", result)
        tables = self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        self.assertEqual(tables, [("ir_evaluation_protocol_versions",)])

    def test_late_registration_and_old_claimed_time_are_not_prospective_evidence(self):
        request = declared()
        request["recorded_at"] = "2020-01-01T00:00:00Z"
        # The registry does not inspect an actual case's reply/outcome history.
        # An old claim saved now must remain unverified, even with all fields set.
        result = self.registry.register(request, 0, now=SAVED)
        self.assertEqual(result["request"]["recorded_at"], "2020-01-01T00:00:00Z")
        self.assertEqual(result["first_saved_at"], "2026-10-15T01:00:00.000000+00:00")
        self.assertEqual(result["verification"]["prospectiveness"], "unverified")
        self.assertTrue(any("existing replies" in item for item in result["limitations"]))

    def test_exact_retry_preserves_first_save_and_request_after_later_versions(self):
        first_request = draft()
        first = self.registry.register(first_request, 0, now=SAVED)
        second_request = draft(version=2)
        second_request["rules"]["state"] = "Synthetic revised text; not executed."
        second = self.registry.register(second_request, 1, now=LATER)
        retry = self.registry.register(deepcopy(first_request), 0, now=LATER)
        self.assertEqual(retry, first | {"added": False})
        self.assertEqual(self.registry.show(first_request["id"], 1), retry)
        self.assertEqual(self.registry.show(first_request["id"]), second | {"added": False})
        self.assertEqual(self.count(), 2)

    def test_same_version_different_content_is_immutable_even_if_only_prose_changes(self):
        self.registry.register(draft(), 0, now=SAVED)
        mutations = [lambda r: r.update(recorded_by="other recorder"),
                     lambda r: r.update(recorded_at="2026-10-02T00:00:00Z"),
                     lambda r: r["rules"].update(state="Different synthetic instructions."),
                     lambda r: r["cohort"].update(synthetic=True)]
        for mutate in mutations:
            request = draft()
            mutate(request)
            with self.subTest(mutation=mutations.index(mutate)), self.assertRaisesRegex(ValueError, "immutable"):
                self.registry.register(request, 0, now=LATER)
        self.assertEqual(self.count(), 1)

    def test_expected_previous_version_and_contiguous_sequence_cas(self):
        with self.assertRaisesRegex(ValueError, "Stale"):
            self.registry.register(draft(version=2), 1, now=SAVED)
        with self.assertRaisesRegex(ValueError, "version - 1"):
            self.registry.register(draft(), 1, now=SAVED)
        self.registry.register(draft(), 0, now=SAVED)
        with self.assertRaisesRegex(ValueError, "Stale"):
            self.registry.register(draft(version=3), 2, now=LATER)
        for expected in (True, -1, "0", 0.0):
            with self.subTest(expected=expected), self.assertRaises(ValueError):
                self.registry.register(draft(), expected, now=LATER)
        self.assertEqual(self.count(), 1)

    def test_later_version_can_record_changes_without_mutating_previous_version(self):
        first = self.registry.register(declared(), 0, now=SAVED)
        changed = declared(version=2)
        changed["cohort"]["states"] = {"new_test_state": "Synthetic replacement category."}
        changed["source_refs"] = []
        self.registry.register(changed, 1, now=LATER)
        self.assertEqual(self.registry.show(first["id"], 1), first | {"added": False})
        self.assertEqual([row["version"] for row in self.registry.history(first["id"])], [1, 2])

    def test_json_key_order_is_not_new_content_but_caller_mutation_cannot_edit_saved_data(self):
        request = declared()
        first = self.registry.register(request, 0, now=SAVED)
        reversed_request = dict(reversed(list(request.items())))
        reversed_request["rules"] = dict(reversed(list(request["rules"].items())))
        self.assertEqual(self.registry.register(reversed_request, 0, now=LATER), first | {"added": False})
        request["rules"]["state"] = "Caller changed its own object."
        first["request"]["cohort"]["states"]["test_state"] = "Caller changed the returned object."
        self.assertEqual(self.registry.show(request["id"])["request"], declared())

    def test_unknown_fields_and_approval_assertions_are_rejected_at_every_structure(self):
        mutations = [lambda r: r.update(approved=True),
                     lambda r: r.update(prospective=True),
                     lambda r: r["cohort"].update(independent=True),
                     lambda r: r["rules"].update(blind=True),
                     lambda r: r["model_refs"][0].update(verified=True),
                     lambda r: r["source_refs"][0].update(adopted=True),
                     lambda r: r["cohort"]["target_period"].update(now=SAVED),
                     lambda r: r["rules"].update(state=True)]
        for mutate in mutations:
            request = declared()
            mutate(request)
            with self.subTest(mutation=mutations.index(mutate)), self.assertRaises(ValueError):
                self.registry.register(request, 0, now=SAVED)
        self.assertEqual(self.count(), 0)

    def test_caller_cannot_inject_trusted_clock_or_missing_keys(self):
        for field in ("now", "first_saved_at", "trusted_now", "request_sha256", "status"):
            request = draft()
            request[field] = SAVED
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.registry.register(request, 0, now=SAVED)
        for field in draft():
            request = draft()
            del request[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                self.registry.register(request, 0, now=SAVED)
        request = draft()
        del request["rules"]["no_response"]
        with self.assertRaises(ValueError):
            self.registry.register(request, 0, now=SAVED)
        self.assertEqual(self.count(), 0)

    def test_aware_clock_normalization_future_recorded_time_and_invalid_clock(self):
        aware = datetime(2026, 10, 15, 1, tzinfo=timezone.utc)
        first = self.registry.register(draft(), 0, now=aware)
        self.assertEqual(first["first_saved_at"], "2026-10-15T01:00:00.000000+00:00")
        future = draft("synthetic-future")
        future["recorded_at"] = "2026-10-15T01:00:01+00:00"
        with self.assertRaisesRegex(ValueError, "future"):
            self.registry.register(future, 0, now=SAVED)
        for now in ("2026-10-15T01:00:00", datetime(2026, 10, 15, 1), None, True):
            with self.subTest(now=now), self.assertRaises(ValueError):
                self.registry.register(draft("synthetic-clock"), 0, now=now)
        request = draft("synthetic-naive-record")
        request["recorded_at"] = "2026-10-01T01:00:00"
        with self.assertRaises(ValueError):
            self.registry.register(request, 0, now=SAVED)
        self.assertEqual(self.count(), 1)

    def test_clock_reversal_cannot_create_an_earlier_first_save(self):
        self.registry.register(draft(), 0, now=SAVED)
        early = "2026-10-15T00:59:59+00:00"
        for request, previous in ((draft(), 0), (draft(version=2), 1), (draft("synthetic-second"), 0)):
            with self.subTest(request=request["id"], version=request["version"]), self.assertRaises(ValueError):
                self.registry.register(request, previous, now=early)
        self.assertEqual(self.count(), 1)

    def test_declared_training_cutoff_and_target_period_are_not_availability_guarantees(self):
        request = declared()
        request["model_refs"][0]["training_information_cutoff"] = "2030-01-01T00:00:00Z"
        request["cohort"]["target_period"] = {"start": "2030-01-01", "end": "2030-12-31"}
        result = self.registry.register(request, 0, now=SAVED)
        self.assertEqual(result["verification"]["model_references"], "unverified")
        self.assertEqual(result["verification"]["prospectiveness"], "unverified")

    def test_definition_reference_format_is_checked_without_inventing_missing_semantics(self):
        mutations = [lambda r: r["cohort"].update(state_timing="unknown timing"),
                     lambda r: r["cohort"].update(state_timing=[]),
                     lambda r: r["cohort"].update(state_timing={}),
                     lambda r: r["cohort"].update(states={}),
                     lambda r: r["cohort"].update(signals={"test": True}),
                     lambda r: r["cohort"].update(synthetic="true"),
                     lambda r: r["cohort"].update(synthetic=1),
                     lambda r: r["cohort"].update(design_version=True),
                     lambda r: r["cohort"].update(definition_sha256="not a hash"),
                     lambda r: r["cohort"].update(target_period={"start": "2026-10-31", "end": "2026-10-01"}),
                     lambda r: r["cohort"].update(target_period={"start": "2026-10-01", "end": None}),
                     lambda r: r["model_refs"][0].update(training_information_cutoff="2026-10-01"),
                     lambda r: r["source_refs"][0].update(content_sha256="A" * 64),
                     lambda r: r["source_refs"][0].update(quote_ids=[True]),
                     lambda r: r["source_refs"][0].update(purpose=" "),
                     lambda r: r.update(evaluation_task=False)]
        for mutate in mutations:
            request = declared()
            mutate(request)
            with self.subTest(mutation=mutations.index(mutate)), self.assertRaises(ValueError):
                self.registry.register(request, 0, now=SAVED)
        self.assertEqual(self.count(), 0)

    def test_duplicate_model_source_and_quote_references_are_rejected(self):
        for kind in ("model_refs", "source_refs", "quote_ids"):
            request = declared()
            if kind == "quote_ids":
                request["source_refs"][0]["quote_ids"] *= 2
            else:
                request[kind] *= 2
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "duplicate"):
                self.registry.register(request, 0, now=SAVED)
        self.assertEqual(self.count(), 0)

    def test_strict_json_rejects_nonfinite_nonjson_and_nonstring_keys(self):
        for value in (float("nan"), float("inf"), Decimal("1"), ("tuple",), {1: "key"}):
            request = draft()
            request["evaluation_task"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.registry.register(request, 0, now=SAVED)
        circular = draft()
        circular["rules"]["state"] = circular
        with self.assertRaisesRegex(ValueError, "nesting"):
            self.registry.register(circular, 0, now=SAVED)
        self.assertEqual(self.count(), 0)

    def test_read_methods_are_nonwriting_and_unknown_versions_are_explicit(self):
        first = self.registry.register(draft(), 0, now=SAVED)
        changes = self.db.total_changes
        self.assertEqual(self.registry.show(first["id"]), first | {"added": False})
        self.assertEqual(self.registry.history(first["id"]), [first | {"added": False}])
        for protocol_id, version in (("unknown", None), (first["id"], 2), (first["id"], True), ("", 1)):
            with self.subTest(protocol_id=protocol_id, version=version), self.assertRaises(ValueError):
                self.registry.show(protocol_id, version)
        self.assertEqual(self.db.total_changes, changes)

    def test_outer_transaction_rollback_preserves_no_partial_protocol(self):
        self.db.execute("BEGIN IMMEDIATE")
        self.registry.register(draft(), 0, now=SAVED)
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.count(), 1)
        self.db.execute("ROLLBACK")
        self.assertEqual(self.count(), 0)
        first = self.registry.register(draft(), 0, now=LATER)
        self.assertEqual(first["first_saved_at"], "2026-10-15T01:05:00.000000+00:00")

    def test_trigger_failure_rolls_back_only_module_savepoint_and_keeps_outer_work(self):
        self.db.execute("CREATE TABLE synthetic_outer_work (value TEXT)")
        self.db.execute("CREATE TRIGGER reject_protocol AFTER INSERT ON ir_evaluation_protocol_versions "
                        "BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
        self.db.execute("BEGIN IMMEDIATE")
        self.db.execute("INSERT INTO synthetic_outer_work VALUES ('keep outer transaction')")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "synthetic failure"):
            self.registry.register(draft(), 0, now=SAVED)
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.db.execute("SELECT value FROM synthetic_outer_work").fetchone()[0],
                         "keep outer transaction")
        self.db.execute("COMMIT")

    def test_standalone_failure_leaves_connection_usable_and_prior_version_immutable(self):
        first = self.registry.register(draft(), 0, now=SAVED)
        self.db.execute("CREATE TRIGGER reject_protocol BEFORE INSERT ON ir_evaluation_protocol_versions "
                        "WHEN NEW.version=2 BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.registry.register(draft(version=2), 1, now=LATER)
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.registry.history(first["id"]), [first | {"added": False}])
        self.db.execute("DROP TRIGGER reject_protocol")
        self.assertTrue(self.registry.register(draft(version=2), 1, now=LATER)["added"])

    def test_two_connections_same_request_converge_on_one_immutable_version(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-protocols.sqlite"
            with sqlite3.connect(path) as setup:
                setup.executescript(SCHEMA)
            barrier = threading.Barrier(2)
            outputs, errors = [], []

            def register():
                connection = sqlite3.connect(path, isolation_level=None, timeout=5)
                try:
                    barrier.wait(timeout=5)
                    outputs.append(EvaluationProtocols(connection).register(draft(), 0, now=SAVED))
                except BaseException as error:
                    errors.append(error)
                finally:
                    connection.close()

            threads = [threading.Thread(target=register) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(errors, [])
            self.assertEqual(sorted(result["added"] for result in outputs), [False, True])
            self.assertEqual(outputs[0] | {"added": False}, outputs[1] | {"added": False})
            with sqlite3.connect(path) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM ir_evaluation_protocol_versions").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
