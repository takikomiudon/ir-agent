"""Read-only projection of saved lease intervals, never analyst work estimates."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ir_agent.attempt_measurements import build_attempt_measurements
from ir_agent.capacity import report_research_capacity
from ir_agent.job_attempts import JobAttempts, SCHEMA
from ir_agent.models import json_text


BASE = datetime(2026, 10, 15, tzinfo=timezone.utc)


def at(seconds):
    return (BASE + timedelta(seconds=seconds)).isoformat()


JOBS = """CREATE TABLE jobs (
 id TEXT PRIMARY KEY, company_id TEXT, status TEXT, packet TEXT,
 lease_owner TEXT, lease_until TEXT, attempts INTEGER, result TEXT, completed_at TEXT
);"""


class AttemptMeasurementTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "jobs.sqlite3"
        self.db = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(self.db.close)
        self.db.executescript(JOBS + SCHEMA)
        self.journal = JobAttempts(self.db)

    def start(self, job="job-1", *, started=0, until=60, synthetic=False, packet=None, worker="worker-1"):
        packet = {"kind": "research", "stage": "thesis_review"} if packet is None else packet
        self.db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)",
                        (job, "jp:130A", "leased", json_text(packet), worker, at(until), 1, None, None))
        return self.journal.start(job, 1, synthetic=synthetic, now=at(started))

    def complete(self, job="job-1", *, completed=30, observed=None, generation=1, sequence=1):
        self.db.execute("UPDATE jobs SET status='completed',result=?,completed_at=? WHERE id=?",
                        (json_text({"test_only": True}), at(completed), job))
        return self.journal.complete(job, generation, expected_sequence=sequence,
                                     now=at(completed if observed is None else observed))

    def report(self, as_of=300, start=0, end=None, **kwargs):
        return build_attempt_measurements(self.path, as_of=at(as_of),
                                          window={"started_at": at(start), "ended_at": at(as_of if end is None else end)}, **kwargs)

    def update_event(self, event, **changes):
        value = dict(event)
        value.update(changes)
        self.db.execute("UPDATE job_attempt_events SET data=?,first_saved_at=?,sequence=? WHERE event_id=?",
                        (json_text(value), value["first_saved_at"], value["sequence"], value["id"]))

    def test_completed_measurement_round_trips_to_capacity_with_missing_usage(self):
        first = self.start()
        self.complete()
        before = self.path.read_bytes()
        result = self.report()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertTrue(result["audit"]["snapshot"]["query_only"])
        self.assertTrue(result["audit"]["snapshot"]["read_only"])
        self.assertEqual(result["audit"]["snapshot"]["write_count"], 0)
        rows = result["capacity_request"]["measurements"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["attempt_id"], first["attempt"]["id"])
        self.assertEqual(rows[0]["stage"], "lease:research:thesis_review")
        self.assertEqual(rows[0]["status"], "completed")
        self.assertEqual(result["audit"]["attempts"][0]["terminal_result_verification"]["status"], "matched_current_job_snapshot")
        for key in ("active_seconds", "tokens", "cost"):
            self.assertIsNone(rows[0][key])
        capacity = report_research_capacity(result["capacity_request"])
        observed = capacity["cohorts"]["observed"]
        self.assertEqual(observed["completed_attempts"], 1)
        self.assertEqual(observed["stages"][rows[0]["stage"]]["elapsed_seconds_whole_attempt_samples"]["total"], "30")
        self.assertIsNone(observed["usage"]["active_seconds"]["worker_total"])
        self.assertIsNone(observed["usage"]["tokens"]["value"])

    def test_renewals_stay_one_attempt_and_do_not_reset_elapsed_start(self):
        self.start()
        self.db.execute("UPDATE jobs SET lease_until=? WHERE id='job-1'", (at(120),))
        self.journal.renew("job-1", 1, expected_sequence=1, lease_until=at(120), now=at(20))
        self.complete(completed=90, sequence=2)
        result = self.report()
        rows = result["capacity_request"]["measurements"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["started_at"], at(0))
        self.assertEqual(rows[0]["ended_at"], at(90))
        self.assertEqual([e["kind"] for e in result["audit"]["attempts"][0]["used_events"]],
                         ["lease_started", "lease_renewed", "completed"])

    def test_unobserved_expiry_does_not_create_terminal_and_late_detection_uses_lease_end(self):
        self.start()
        self.journal.expire("job-1", 1, expected_sequence=1, now=at(90))
        count = self.db.execute("SELECT COUNT(*) FROM job_attempt_events").fetchone()[0]
        before = self.report(as_of=70)
        row = before["capacity_request"]["measurements"][0]
        self.assertEqual(row["status"], "in_progress")
        self.assertIsNone(row["ended_at"])
        self.assertIn("planned_lease_exceeded_without_saved_terminal", before["audit"]["attempts"][0]["warnings"])
        later = self.report(as_of=100)
        row = later["capacity_request"]["measurements"][0]
        self.assertEqual((row["status"], row["ended_at"]), ("failed", at(60)))
        audit = later["audit"]["attempts"][0]
        self.assertEqual(audit["termination_reason"], "lease_expired")
        self.assertEqual(audit["terminal_observed_at"], at(90))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM job_attempt_events").fetchone()[0], count)

    def test_actual_saved_and_observed_boundaries_both_control_visibility(self):
        self.start()
        terminal = self.complete()["event"]
        self.update_event(terminal, first_saved_at=at(100))
        before = self.report(as_of=50)
        self.assertEqual(before["capacity_request"]["measurements"][0]["status"], "in_progress")
        self.assertEqual(self.report(as_of=100)["capacity_request"]["measurements"][0]["status"], "completed")
        self.update_event(terminal, observed_at=at(100))
        self.assertEqual(self.report(as_of=50)["capacity_request"]["measurements"][0]["status"], "in_progress")
        # Once visible, inconsistent save-before-observation is a clock anomaly.
        final = self.report(as_of=100)
        self.assertEqual(final["capacity_request"]["measurements"], [])
        self.assertIn("clock_anomaly", final["audit"]["attempts"][0]["exclusion_reasons"])

    def test_header_first_save_is_not_replaced_by_earlier_start(self):
        initial = self.start()
        header = initial["attempt"]
        header["first_saved_at"] = at(100)
        self.db.execute("UPDATE job_attempts SET data=?,first_saved_at=?", (json_text(header), at(100)))
        self.update_event(initial["event"], first_saved_at=at(100))
        before = self.report(as_of=50)
        self.assertEqual(before["capacity_request"]["measurements"], [])
        self.assertEqual(before["audit"]["counts"]["not_yet_visible_headers"], 1)
        self.assertEqual(len(self.report(as_of=100)["capacity_request"]["measurements"]), 1)

    def test_clock_anomaly_and_unknown_synthetic_are_excluded_with_reasons(self):
        self.start(synthetic=None)
        self.start("clock-job", started=0, until=60)
        self.complete("clock-job", completed=-1, observed=-1)
        result = self.report()
        self.assertEqual(result["capacity_request"]["measurements"], [])
        audits = {row["job_id"]: row for row in result["audit"]["attempts"]}
        self.assertIn("synthetic_status_unknown", audits["job-1"]["exclusion_reasons"])
        self.assertIn("clock_anomaly", audits["clock-job"]["exclusion_reasons"])
        self.assertTrue(audits["clock-job"]["clock_issues"])
        self.assertEqual(audits["job-1"]["worker_id"], "worker-1")
        self.assertEqual(audits["job-1"]["measurement_scope"], "lease_ownership")

    def test_synthetic_attempt_remains_separate_and_operator_budget_is_only_explicit(self):
        self.start(synthetic=True)
        self.complete()
        plain = self.report()
        self.assertNotIn("operator_capacity", plain["capacity_request"])
        capacity = {"worker_seconds": "100", "synthetic": True}
        result = self.report(operator_capacity=capacity)
        self.assertEqual(result["capacity_request"]["operator_capacity"], capacity)
        computed = report_research_capacity(result["capacity_request"])
        self.assertEqual(computed["cohorts"]["synthetic"]["completed_attempts"], 1)
        self.assertEqual(computed["cohorts"]["observed"]["completed_attempts"], 0)
        self.assertIsNone(computed["cohorts"]["synthetic"]["budget_comparison"]["worker_seconds"])

    def test_two_generations_keep_failure_and_completion_separate_with_previous_reference(self):
        first = self.start()
        self.journal.expire("job-1", 1, expected_sequence=1, now=at(80))
        self.db.execute("UPDATE jobs SET attempts=2,lease_until=? WHERE id='job-1'", (at(150),))
        second = self.journal.start("job-1", 2, synthetic=False, now=at(90))
        self.complete(completed=120, generation=2)
        result = self.report()
        self.assertEqual([row["status"] for row in result["capacity_request"]["measurements"]], ["failed", "completed"])
        self.assertEqual(result["audit"]["attempts"][1]["previous_measured_attempt"], {"id": first["attempt"]["id"], "generation": 1})
        self.assertNotEqual(first["attempt"]["id"], second["attempt"]["id"])

    def test_hash_verified_legacy_kind_and_missing_stage_stay_explicit(self):
        self.start(packet={"thesis": {"version": 1}})
        self.start("unknown-stage-job", packet={})
        result = self.report()
        rows = {row["stage"] for row in result["capacity_request"]["measurements"]}
        self.assertEqual(rows, {"lease:research:unknown", "lease:unknown:unknown"})
        self.assertTrue(all("stage_components_unknown" in row["warnings"] for row in result["audit"]["attempts"]))

    def test_corrupt_packet_generation_and_sequence_are_audited_instead_of_dropped(self):
        self.start("packet-job")
        self.db.execute("UPDATE jobs SET packet='not JSON' WHERE id='packet-job'")
        self.start("generation-job")
        self.db.execute("UPDATE jobs SET attempts=0 WHERE id='generation-job'")
        self.start("sequence-job")
        terminal = self.complete("sequence-job")["event"]
        self.update_event(terminal, sequence=3)
        result = self.report()
        self.assertEqual(result["capacity_request"]["measurements"], [])
        self.assertEqual(result["audit"]["counts"]["excluded_attempts"], 3)
        reasons = result["audit"]["exclusion_counts"]
        self.assertIn("generation_exceeds_job_counter", reasons)
        self.assertIn("visible_events_are_not_a_contiguous_prefix", reasons)

    def test_legacy_completed_jobs_are_unmeasured_and_absent_ledger_is_not_known_zero(self):
        for i in range(3):
            self.db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)",
                            (f"old-job-{i}", "jp:130A", "completed", "{}", None, None, 1, "{}", at(20)))
        empty = self.report()
        self.assertEqual(empty["capacity_request"]["measurements"], [])
        self.assertEqual(empty["audit"]["counts"]["projected_attempts"], 0)
        self.assertEqual(empty["audit"]["counts"]["unmeasured_jobs_current_snapshot"], 3)
        self.assertTrue(all("started_at" not in row for row in empty["audit"]["unmeasured_jobs"]))
        self.db.execute("DROP TABLE job_attempt_events")
        self.db.execute("DROP TABLE job_attempts")
        unavailable = self.report()
        self.assertIsNone(unavailable["capacity_request"]["measurements"])
        self.assertIsNone(unavailable["audit"]["counts"]["projected_attempts"])
        self.assertEqual(unavailable["audit"]["table_status"]["job_attempts"], "absent")

    def test_consistent_read_only_snapshot_excludes_uncommitted_claim(self):
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("BEGIN IMMEDIATE")
        self.start()
        result = self.report()
        self.assertEqual(result["capacity_request"]["measurements"], [])
        self.assertTrue(self.db.in_transaction)
        self.db.execute("COMMIT")
        self.assertEqual(len(self.report()["capacity_request"]["measurements"]), 1)

    def test_deadline_completion_and_changed_saved_result_are_rejected(self):
        self.start("deadline-job")
        event = self.complete("deadline-job")["event"]
        event["payload"]["completed_at"] = at(60)
        self.update_event(event, effective_at=at(60), observed_at=at(60), first_saved_at=at(60))
        self.db.execute("UPDATE jobs SET completed_at=? WHERE id='deadline-job'", (at(60),))
        self.start("changed-result-job")
        self.complete("changed-result-job")
        self.db.execute("UPDATE jobs SET result=? WHERE id='changed-result-job'", (json_text({"changed": True}),))
        result = self.report()
        self.assertEqual(result["capacity_request"]["measurements"], [])
        self.assertIn("invalid_completion_time", result["audit"]["exclusion_counts"])
        self.assertIn("terminal_result_or_completion_mismatch", result["audit"]["exclusion_counts"])

    def test_completion_without_current_generation_result_is_explicitly_unresolved(self):
        self.start()
        self.complete()
        self.db.execute("UPDATE jobs SET attempts=2,status='pending',result=NULL,completed_at=NULL WHERE id='job-1'")
        result = self.report()
        self.assertEqual(result["capacity_request"]["measurements"][0]["status"], "completed")
        self.assertEqual(result["audit"]["attempts"][0]["terminal_result_verification"], {
            "status": "not_resolved", "reason": "current_job_generation_or_status_no_longer_retains_this_completion"})

    def test_missing_file_is_not_created_and_window_cannot_extrapolate_beyond_as_of(self):
        missing = Path(self.directory.name) / "missing.sqlite3"
        with self.assertRaises(ValueError):
            build_attempt_measurements(missing, as_of=at(60), window={"started_at": at(0), "ended_at": at(60)})
        self.assertFalse(missing.exists())
        for window in [{"started_at": at(0)}, {"started_at": at(60), "ended_at": at(60)},
                       {"started_at": at(0), "ended_at": at(61)}]:
            with self.subTest(window=window), self.assertRaises(ValueError):
                build_attempt_measurements(self.path, as_of=at(60), window=window)

    def test_script_outputs_request_and_audit_and_refuses_database_as_output(self):
        self.start()
        path = Path(__file__).parents[1] / "scripts/report_job_attempts.py"
        spec = importlib.util.spec_from_file_location("report_job_attempts_under_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        args = ["--db", str(self.path), "--as-of", at(120), "--window-start", at(0), "--window-end", at(120)]
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(module.main(args), 0)
        self.assertEqual(json.loads(stdout.getvalue())["capacity_request"]["measurements"][0]["status"], "in_progress")
        before = sha256(self.path.read_bytes()).hexdigest()
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(module.main(args + ["--output", str(self.path)]), 1)
        self.assertIn("must not overwrite", stderr.getvalue())
        self.assertEqual(sha256(self.path.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()
