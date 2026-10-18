"""Offline regressions for adaptive pacing, restart safety, and survey preservation."""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_ir_research_adaptive.py"
SPEC = importlib.util.spec_from_file_location("ir_adaptive_runner", SCRIPT)
adaptive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adaptive)
START = datetime(2026, 10, 11, 6, 20, tzinfo=timezone.utc)


class AdaptiveRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name)
        self.run = self.output / "adaptive"
        self.run.mkdir()
        self.manifest = {"started_at": "2026-10-11T06:12:00+00:00"}
        self.write("adaptive/manifest.json", self.manifest)
        (self.output / "universe.csv").write_text(
            "security_code\n1111\n2222\n3333\n", encoding="utf-8"
        )
        self.seeds = {
            code: {"security_code": code, "official_url": f"https://{code}.invalid/"}
            for code in ("1111", "2222", "3333")
        }
        self.write("seeds-current.json", list(self.seeds.values()))
        self.args = adaptive.parser().parse_args([
            "--output", str(self.output), "--manifest", str(self.run / "manifest.json"),
            "--universe", str(self.output / "universe.csv"),
        ])
        self.runner = self.new_runner()
        # The production log is covered separately; unit assertions stay quiet.
        self.runner.event = lambda *args, **kwargs: None

    def write(self, relative, value):
        path = self.output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")
        return relative

    def new_runner(self):
        return adaptive.Runner(self.args, self.run, self.manifest, self.seeds, list(self.seeds))

    def fixture(self, code="1111", attempt=1, signature="site_tls_503", actual_gets=1,
                reason="environment_transport_failure", retry_after=None, latest_attempt=False):
        stamp = (START + timedelta(minutes=attempt, seconds=1)).isoformat()
        status = {
            "site_tls_503": 503, "common_transport_503": 503,
            "http_404": 404, "http_429": 429,
        }.get(signature)
        snapshot = self.write(f"evidence/{code}-{attempt}.json", {
            "url": f"https://{code}.invalid/", "http_get_started_at": stamp,
            "retrieved_at": stamp, "http_get_attempted": actual_gets > 0,
            "http_status": status, "failure_signature": signature,
            "retry_after_seconds": retry_after,
        })
        fresh = {
            "attempted_at": stamp, "http_get_attempt_count": actual_gets,
            "fetches": [{"snapshot": snapshot}],
        }
        record = {"security_code": code, "company_name": "一時テスト会社",
                  "unconfirmed_reason": reason}
        if latest_attempt:
            record.update(latest_attempt=fresh, retained_prior_contact=True)
        else:
            record.update(fresh)
        self.write(f"records/{code}.json", record)
        return record

    def batch(self, attempt=1):
        return {
            "batch_id": f"fixture-{attempt}",
            "started_at": (START + timedelta(minutes=attempt)).isoformat(),
            "security_codes": ["1111"], "before_hashes": {"1111": "old-record"},
            "stdout_path": str(self.run / "stdout.log"),
        }

    def result(self, **changes):
        return {
            "status": "completed", "preflight_passed": True, "preflight_http_status": 200,
            "common_transport_503_count": 0, "http_429_count": 0,
            "http_get_attempt_count": 2, "final_global_rps": 1.0, **changes,
        }

    def test_plan_is_read_only_and_cannot_start_collector(self):
        self.fixture()
        before = {str(path): path.read_bytes() for path in self.output.rglob("*") if path.is_file()}
        with patch.object(adaptive.subprocess, "Popen", side_effect=AssertionError("process prohibited")), \
                patch.object(adaptive, "atomic_json", side_effect=AssertionError("write prohibited")), \
                redirect_stdout(io.StringIO()) as stream:
            status = adaptive.main([
                "--output", str(self.output), "--manifest", str(self.run / "manifest.json"),
                "--initial-stage", "1", "--initial-rps", "2", "--plan-only",
            ])
        self.assertEqual(0, status)
        plan = json.loads(stream.getvalue())
        self.assertEqual((0, 0, 2), (plan["network_requests"], plan["writes"], plan["first_batch_rps"]))
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.output.rglob("*") if path.is_file()})

    def test_only_latest_network_failures_enter_queue_and_exhausted_stay_unverified(self):
        self.fixture()
        self.fixture("2222", reason="robots_disallowed")
        self.fixture("3333")
        self.assertEqual((["1111"], ["3333"]), adaptive.pending_codes(
            self.output, list(self.seeds), {"3333": {"IR_channel_verified": False}}))

    def test_common_503_and_429_reduce_once_and_preserve_retry_after(self):
        for signature, return_code, delay in (("common_transport_503", 2, 300), ("http_429", 0, 5000)):
            with self.subTest(signature=signature):
                self.runner.state = adaptive.fresh_state(self.args, self.manifest)
                self.fixture(signature=signature, retry_after=delay if signature == "http_429" else None)
                before = (self.output / "records/1111.json").read_bytes()
                result = self.result(final_global_rps=0.5,
                                     common_transport_503_count=int(signature == "common_transport_503"),
                                     http_429_count=int(signature == "http_429"))
                self.assertIsNone(self.runner.finish_batch(self.batch(), result, return_code))
                state = self.runner.state
                self.assertEqual(0.5, state["current_global_rps"])
                self.assertEqual("waiting_for_recovery", state["status"])
                self.assertEqual(delay, state["cooldown"]["seconds"])
                self.assertEqual(2, state["actual_http_get_attempt_count"])
                self.assertEqual(before, (self.output / "records/1111.json").read_bytes())
                self.assertEqual(["1111"], adaptive.pending_codes(self.output, list(self.seeds), {})[0])

    def test_backoff_is_bounded_and_does_not_cut_off_recovery_waits(self):
        for expected in (300, 900, 1800, 3600, 3600, 3600):
            self.runner.schedule_cooldown("shared_transport_503")
            self.assertEqual(expected, self.runner.state["cooldown"]["seconds"])
            self.assertEqual("waiting_for_recovery", self.runner.state["status"])

    def test_site_tls_503_does_not_trigger_shared_circuit_cooldown(self):
        self.fixture(signature="site_tls_503")
        self.assertIsNone(self.runner.finish_batch(
            self.batch(), self.result(site_specific_503_count=1), 0))
        self.assertIsNone(self.runner.state["cooldown"])
        self.assertEqual(2, self.runner.state["current_global_rps"])
        self.assertEqual(1, self.runner.state["attempts_by_code"]["1111"]["healthy_same_failure_count"])

    def test_two_matching_healthy_failures_leave_records_unchanged_and_make_retry_finite(self):
        for signature in ("site_tls_503", "request_exception:ProxyError", "request_exception:ReadTimeout", "http_404"):
            with self.subTest(signature=signature):
                state = adaptive.fresh_state(self.args, self.manifest)
                self.fixture(signature=signature)
                adaptive.record_attempts(self.output, state, self.batch(), self.result())
                self.assertEqual({}, state["exhausted_codes"])
                self.fixture(attempt=2, signature=signature)
                before = (self.output / "records/1111.json").read_bytes()
                adaptive.record_attempts(self.output, state, self.batch(2), self.result())
                candidate = state["exhausted_codes"]["1111"]
                self.assertTrue(candidate["excluded_from_network_queue_only"])
                self.assertTrue(candidate["requires_followup"])
                self.assertFalse(candidate["IR_channel_verified"])
                self.assertIn("cause undetermined", candidate["reason"])
                self.assertEqual(([], ["1111"]), adaptive.pending_codes(self.output, list(self.seeds), state["exhausted_codes"]))
                self.assertEqual(before, (self.output / "records/1111.json").read_bytes())

    def test_unhealthy_preflight_or_changed_signature_cannot_exhaust_a_company(self):
        for changed_signature, result in (
            ("site_tls_503", self.result(preflight_passed=False)),
            ("site_tls_503", self.result(common_transport_503_count=1)),
            ("request_exception:ProxyError", self.result()),
        ):
            with self.subTest(changed_signature=changed_signature, result=result):
                state = adaptive.fresh_state(self.args, self.manifest)
                self.fixture()
                adaptive.record_attempts(self.output, state, self.batch(), self.result())
                self.fixture(attempt=2, signature=changed_signature)
                adaptive.record_attempts(self.output, state, self.batch(2), result)
                self.assertEqual({}, state["exhausted_codes"])

    def test_fresh_latest_attempt_is_counted_once_and_no_get_wrappers_are_not_counted(self):
        self.fixture(latest_attempt=True)
        state = self.runner.state
        for _ in range(2):
            adaptive.record_attempts(self.output, state, self.batch(), self.result())
        self.assertEqual(1, state["attempts_by_code"]["1111"]["attempt_count"])
        self.fixture(attempt=2, actual_gets=0)
        observed = adaptive.record_attempts(self.output, state, self.batch(2), self.result())
        self.assertEqual(0, observed["actual_company_attempts"])
        self.assertEqual(1, state["attempts_by_code"]["1111"]["attempt_count"])

    def test_nested_redirects_robots_and_local_circuit_do_not_duplicate_request_failures(self):
        stamp = (START + timedelta(minutes=1)).isoformat()
        actual = {"url": "https://1111.invalid/actual", "http_get_started_at": stamp,
                  "http_get_attempted": True, "http_status": 429,
                  "failure_signature": "http_429", "retry_after_seconds": 600}
        snapshot = self.write("evidence/nested.json", {
            "url": "https://1111.invalid/local", "retrieved_at": stamp,
            "http_get_attempted": False, "http_status": 503,
            "text": "Invalid argument|remote address:envoy://cloudflare_",
            "robots": actual, "redirects": [actual],
        })
        observed = adaptive.observed_failures(
            self.output, {"fetches": [{"snapshot": snapshot}]}, START)
        self.assertEqual((0, 1, 600), (observed["shared_503_count"], observed["http_429_count"], observed["retry_after_seconds"]))

    def test_unreachable_robots_local_stop_preserves_nested_failure_without_double_counting(self):
        self.assertIn("robots_unreachable_stopped", adaptive.LOCAL_STOPS)
        stamp = (START + timedelta(minutes=1, seconds=1)).isoformat()
        for signature, status in (("common_transport_503", 503), ("site_tls_503", 503),
                                  ("request_exception:ReadTimeout", None)):
            with self.subTest(signature=signature):
                actual = {"url": "https://1111.invalid/robots.txt", "http_get_started_at": stamp,
                          "retrieved_at": stamp, "http_get_attempted": True,
                          "http_status": status, "failure_signature": signature}
                snapshot = self.write("evidence/robots_unreachable.json", {
                    "requested_url": "https://1111.invalid/", "retrieved_at": stamp,
                    "http_get_attempted": False, "error": "robots_unreachable_stopped",
                    "robots": actual, "redirects": [actual],
                })
                observed = adaptive.observed_failures(self.output, {
                    "fetches": [{"snapshot": snapshot}, {"snapshot": snapshot}]
                }, START)
                self.assertEqual(int(signature == "common_transport_503"), observed["shared_503_count"])
                self.assertEqual(None if signature == "common_transport_503" else signature, observed["site_failure_signature"])
                self.assertEqual(0, observed["http_429_count"])

    def test_paused_cooldown_survives_restart_and_wait_chunks_are_interruptible(self):
        self.fixture()
        until = START + timedelta(seconds=900)
        self.runner.state.update(status="waiting_for_recovery", cooldown={
            "reason": "shared_transport_503", "seconds": 900, "until_utc": until.isoformat(),
        })
        self.runner.save()
        resumed = self.new_runner()
        resumed.event = lambda *args, **kwargs: None
        self.assertEqual(until.isoformat(), resumed.state["cooldown"]["until_utc"])
        clock = [START]
        waits = []

        def advance(seconds):
            self.assertLessEqual(seconds, 60)
            waits.append(seconds)
            clock[0] += timedelta(seconds=seconds)

        with patch.object(adaptive, "utc_now", side_effect=lambda: clock[0]), \
                patch.object(resumed.stop, "wait", side_effect=advance), \
                patch.object(adaptive.subprocess, "Popen", side_effect=AssertionError("process prohibited")):
            resumed.cooldown()
        self.assertEqual(900, sum(waits))
        self.assertIsNone(adaptive.read_json(self.run / "progress.json")["cooldown"])
        self.assertEqual(["1111"], adaptive.pending_codes(self.output, list(self.seeds), {})[0])

    def test_live_previous_collector_blocks_a_second_child(self):
        self.fixture()
        self.runner.state["active_batch"] = {**self.batch(), "collector_pid": 999999999}
        with patch.object(adaptive.os, "kill"), \
                patch.object(adaptive.subprocess, "Popen", side_effect=AssertionError("duplicate prohibited")):
            self.assertEqual(3, self.runner.execute())
        self.assertEqual("previous_collector_process_unresolved", self.runner.state["status"])

    def test_finished_child_reconciles_once_after_wrapper_restart(self):
        self.fixture()
        self.runner.state["active_batch"] = self.batch()
        self.runner.save()
        (self.run / "stdout.log").write_text(json.dumps({"collection_run": self.result()}) + "\n", encoding="utf-8")
        self.args.max_batches = 1
        for _ in range(2):
            resumed = self.new_runner()
            resumed.event = lambda *args, **kwargs: None
            with patch.object(adaptive.signal, "signal"), \
                    patch.object(adaptive.subprocess, "Popen", side_effect=AssertionError("process prohibited")):
                self.assertEqual(0, resumed.execute())
            self.assertEqual(1, resumed.state["completed_batch_count"])
            self.assertEqual(2, resumed.state["actual_http_get_attempt_count"])
            self.assertIsNone(resumed.state["active_batch"])

    def test_one_mock_child_receives_only_the_selected_seeds(self):
        self.fixture()
        case = self

        class FakeChild:
            pid = 999999999

            def __init__(self, command, **kwargs):
                seed_path = Path(command[command.index("--seeds") + 1])
                case.assertEqual([case.seeds["1111"]], adaptive.read_json(seed_path))
                case.assertIn("--only-seeded", command)
                case.assertEqual("1", command[command.index("--limit") + 1])
                kwargs["stdout"].write((json.dumps({"collection_run": case.result()}) + "\n").encode())

            def poll(self):
                return 0

            def wait(self, *args, **kwargs):
                return 0

        with patch.object(adaptive.subprocess, "Popen", side_effect=FakeChild) as calls:
            self.assertIsNone(self.runner.run_batch(["1111"]))
        self.assertEqual(1, calls.call_count)
        self.assertEqual(1, self.runner.state["completed_batch_count"])
        self.assertEqual(2, self.runner.state["actual_http_get_attempt_count"])
        self.assertIsNone(self.runner.state["active_batch"])

    def test_rate_floor_and_gradual_recovery_follow_healthy_batches(self):
        state = self.runner.state
        adaptive.next_rate(state, self.result(final_global_rps=0.5), True)
        adaptive.next_rate(state, self.result(final_global_rps=0.25), True)
        adaptive.next_rate(state, self.result(final_global_rps=0.25), True)
        self.assertEqual(0.25, state["current_global_rps"])
        adaptive.next_rate(state, self.result(final_global_rps=0.25), False)
        self.assertEqual(0.25, state["current_global_rps"])
        adaptive.next_rate(state, self.result(final_global_rps=0.25), False)
        self.assertEqual(0.75, state["current_global_rps"])

    def test_drained_queue_does_not_claim_ir_verification_or_start_child(self):
        with patch.object(adaptive.signal, "signal"), \
                patch.object(adaptive.subprocess, "Popen", side_effect=AssertionError("process prohibited")):
            self.assertEqual(0, self.runner.execute())
        self.assertEqual("network_phase_complete", self.runner.state["status"])
        self.assertFalse(self.runner.state["all_IR_channels_verified"])


if __name__ == "__main__":
    unittest.main()
