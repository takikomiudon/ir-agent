"""Keep historical execution evidence separate from later survey progress."""
import importlib.util
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "report_ir_universe.py"
SPEC = importlib.util.spec_from_file_location("adaptive_report", SCRIPT)
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)

START = "2026-10-11T06:12:00+00:00"
RUN = "adaptive-runs/goal"
OLD_RUN = "runs/old-retry"


class AdaptiveReportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / RUN).mkdir(parents=True)
        (self.root / OLD_RUN).mkdir(parents=True)
        self.old = {
            "started_at": "2026-10-11T04:46:00+00:00",
            "collection_status": "stopped_by_environment_circuit",
            "company_content_get_attempt_count": 255,
            "company_successful_public_body_count": 244,
            "universe_company_content_get_attempt_count_across_baseline_and_retry": 3645,
            "after_universe_statuses": {"confirmed": 220, "provisional": 71, "unconfirmed": 3395},
        }
        self.write("retry-current-run.json", {"run_directory": OLD_RUN, "manifest": OLD_RUN + "/manifest.json"})
        self.write(OLD_RUN + "/manifest.json", {"run_directory": OLD_RUN, "started_at": self.old["started_at"],
                                                "selected_security_codes": ["2222", "3333"]})
        self.write(OLD_RUN + "/summary.json", self.old)
        self.write("adaptive-current-run.json", {"run_directory": RUN, "manifest": RUN + "/manifest.json"})
        self.baseline = {"by_investigation_status": {"confirmed": 1, "provisional": 1, "unconfirmed": 2},
                         "blocked_network_count": 2, "additional_contact_followup_count": 1}
        self.write(RUN + "/manifest.json", {
            "started_at": START, "run_directory": RUN, "universe_count": 4,
            "baseline_summary": self.baseline, "network_pending_codes": ["2222", "3333"],
            "followup_codes": ["444A"], "configuration": {"initial_global_rps": 1.0},
        })

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def records(self):
        rows = []
        for code, status, stamp, http_status, error, body_count in [
            ("1111", "confirmed", "2026-10-11T06:00:00+00:00", 200, None, 1),
            ("2222", "confirmed", "2026-10-11T15:13:00+09:00", 200, None, 1),
            ("3333", "unconfirmed", "2026-10-11T06:14:00+00:00", 403, None, 0),
            ("444A", "provisional", "2026-10-11T06:15:00+00:00", None, "environment_circuit_breaker_open", 0),
        ]:
            snapshot = f"evidence/{code}.json"
            self.write(snapshot, {"url": f"https://{code}.invalid/", "retrieved_at": stamp,
                                  "http_status": http_status, "error": error, "submitted": False})
            rows.append({
                "security_code": code, "company_name": "会社" + code,
                "market": "プライム（内国株式）", "jpx_sector": "サービス業",
                "investigation_status": status, "verification_level": "form_fields_verified" if status == "confirmed" else "none",
                "outreach_suitability": "candidate" if status == "confirmed" else "unconfirmed",
                "individual_access": "not_stated", "manual_review_required": False,
                "attempted_at": stamp, "completed_at": stamp, "successful_official_page_count": body_count,
                "contact_url": f"https://{code}.invalid/", "channels": ["form"], "public_ir_emails": [],
                "conditions": [], "limitations": [], "evidence": [],
                "fetches": [{"snapshot": snapshot, "http_status": http_status, "error": error}],
            })
        return rows

    def collection(self, name, attempts, **changes):
        value = {
            "started_at": "2026-10-11T06:13:00+00:00", "http_get_attempt_count": attempts,
            "preflight_http_get_attempt_count": 1, "company_http_get_attempt_count": attempts - 1,
            "http_429_count": 0, "common_transport_503_count": 0, "site_specific_503_count": 0,
            "configured_global_rps": 1.0, "final_global_rps": 1.0, "minimum_global_rps": 0.25,
            "rate_adjustments": [], "status": "completed",
        }
        value.update(changes)
        self.write("collection-runs/" + name, value)

    def test_old_summary_bytes_and_counts_remain_frozen_after_later_gets(self):
        path = self.root / OLD_RUN / "summary.json"
        before = path.read_bytes()
        records = self.records()
        self.assertEqual(self.old, report.retry_overview(self.root, records))
        self.assertEqual(before, path.read_bytes())
        records[1]["successful_official_page_count"] = 5
        self.assertEqual(self.old, report.retry_overview(self.root, records))
        self.assertEqual(before, path.read_bytes())

    def test_missing_historical_summary_is_not_reconstructed_from_current_records(self):
        path = self.root / OLD_RUN / "summary.json"
        path.unlink()
        self.assertIsNone(report.retry_overview(self.root, self.records()))
        self.assertFalse(path.exists())

    def test_latest_company_counts_are_distinct_from_all_gets_and_controller_totals(self):
        self.collection("before-goal.json", 999, started_at="2026-10-11T06:00:00+00:00")
        self.collection("pilot-progress.json", 3)
        self.collection("pilot.json", 10, http_429_count=1,
                        final_global_rps=0.5,
                        rate_adjustments=[{"previous_rps": 1, "global_rps": 0.5}])
        self.collection("child-progress.json", 4, status="running", common_transport_503_count=2)
        self.write(RUN + "/progress.json", {
            "schema_version": 1, "status": "cooldown", "pending_network_company_count": 1,
            "exhausted_network_company_count": 1, "exhausted_codes_requiring_followup": ["3333"],
            "completed_batch_count": 1, "actual_http_get_attempt_count": 4, "current_global_rps": 0.5,
            "cooldown": {"reason": "common_transport_503", "seconds": 60},
        })
        events = [
            {"at_utc": "2026-10-11T06:13:00+00:00", "event": "batch_started", "global_rps": 1},
            {"at_utc": "2026-10-11T06:14:00+00:00", "event": "cooldown_scheduled", "global_rps": 0.5,
             "cooldown": {"reason": "common_transport_503", "seconds": 60}},
            {"at_utc": "2026-10-11T06:14:30+00:00", "event": "heartbeat", "global_rps": 0.5},
        ]
        (self.root / RUN / "events.jsonl").write_text("\n".join(json.dumps(x) for x in events) + "\n")
        observed = report.adaptive_overview(self.root, self.records())
        self.assertEqual(3, observed["latest_updated_record_count_since_goal_start"])
        self.assertEqual(2, observed["latest_company_content_get_attempt_count_since_goal_start"])
        self.assertEqual(1, observed["latest_company_successful_public_body_count_since_goal_start"])
        self.assertEqual(1, observed["latest_updated_record_without_content_get_count"])
        self.assertEqual(2, observed["collection_execution_count"])
        self.assertEqual(14, observed["collection_http_get_attempt_count"])
        self.assertEqual(12, observed["collection_company_http_get_attempt_count"])
        self.assertEqual(4, observed["controller_child_http_get_attempt_count"])
        self.assertEqual(1, observed["collection_http_429_count"])
        self.assertEqual(2, observed["collection_common_transport_503_count"])
        self.assertEqual(1, observed["controller_scheduled_cooldown_count"])
        self.assertEqual(60, observed["controller_scheduled_cooldown_seconds"])
        self.assertEqual([1, 0.5], [x["global_rps"] for x in observed["controller_rps_changes"]])
        self.assertEqual(self.baseline["by_investigation_status"], observed["initial_universe_statuses"])
        self.assertEqual({"confirmed": 2, "unconfirmed": 1, "provisional": 1}, observed["current_universe_statuses"])
        self.assertEqual(1, observed["controller_pending_network_company_count"])
        self.assertEqual(1, observed["controller_exhausted_network_company_count"])

    def test_local_denial_wrapper_does_not_count_as_company_get(self):
        self.assertFalse(report.content_get_attempted({"fetches": [
            {"http_status": 403, "error": "robots_access_denied_stopped"}]}))

    def test_robots_transport_stop_keeps_real_get_total_without_content_attempt(self):
        historical_path = self.root / OLD_RUN / "summary.json"
        historical_before = historical_path.read_bytes()
        for robot_status, robot_error in [(503, None), (None, "ReadTimeout")]:
            with self.subTest(robot_status=robot_status, robot_error=robot_error):
                records = self.records()
                stamp = "2026-10-11T06:14:00+00:00"
                stopped = {
                    "requested_url": "https://3333.invalid/ir/", "retrieved_at": stamp,
                    "error": "robots_unreachable_stopped", "submitted": False,
                    "http_get_attempted": False,
                    "robots_failure_reason": "http_server_error" if robot_status else "request_exception",
                    "robots": {
                        "url": "https://3333.invalid/robots.txt", "http_status": robot_status,
                        "error": robot_error, "http_get_attempted": True,
                        "http_get_started_at": stamp,
                        "http_get_completed_at": "2026-10-11T06:14:01+00:00",
                    },
                }
                self.write(records[2]["fetches"][0]["snapshot"], stopped)
                records[2]["fetches"] = [dict(stopped, snapshot=records[2]["fetches"][0]["snapshot"])]
                self.collection("robots-failure.json", 10,
                                site_specific_503_count=1 if robot_status else 0)
                self.assertFalse(report.content_get_attempted(records[2]))
                observed = report.adaptive_overview(self.root, records)
                self.assertEqual(3, observed["latest_updated_record_count_since_goal_start"])
                self.assertEqual(1, observed["latest_company_content_get_attempt_count_since_goal_start"])
                self.assertEqual(1, observed["latest_company_successful_public_body_count_since_goal_start"])
                self.assertEqual(2, observed["latest_updated_record_without_content_get_count"])
                self.assertEqual(10, observed["collection_http_get_attempt_count"])
                self.assertEqual(9, observed["collection_company_http_get_attempt_count"])
                self.assertEqual(self.old, report.retry_overview(self.root, records))
                self.assertEqual(historical_before, historical_path.read_bytes())

    def test_complete_network_phase_keeps_unconfirmed_and_watch_bundle(self):
        records = self.records()
        self.write(RUN + "/progress.json", {"status": "network_phase_complete_with_retry_candidates",
                                            "pending_network_company_count": 0, "exhausted_network_company_count": 1,
                                            "maximum_global_rps": 0.35})
        summary = {"official_get_company_count": 3, "companies_with_successful_public_page_this_run": 2}
        self.write("companies.json", {"generated_at": START, "summary": summary, "companies": records})
        for record in records:
            self.write("records/" + record["security_code"] + ".json", record)
        path = self.root / OLD_RUN / "summary.json"
        before = path.read_bytes()
        with patch.object(sys, "argv", [str(SCRIPT), str(self.root)]), redirect_stdout(io.StringIO()):
            report.main()
        self.assertEqual(before, path.read_bytes())
        self.assertEqual(records, json.loads((self.root / "companies.json").read_text())["companies"])
        coverage = json.loads((self.root / "coverage.json").read_text())
        self.assertTrue(coverage["historical_retry_summary_frozen"])
        self.assertEqual(RUN + "/summary.json", coverage["latest_adaptive_summary"])
        bundle = json.loads((self.root / "watchlist-bundle.json").read_text())
        self.assertEqual(["jp:1111", "jp:2222"], [x["id"] for x in bundle["companies"]])
        self.assertTrue(all(x["status"] == "watch" and x["held"] is False for x in bundle["companies"]))
        self.assertEqual([], bundle["theses"])
        text = (self.root / "README.md").read_text()
        self.assertIn("全社の処理と全社のIR窓口確認は同一ではない", text)
        self.assertIn("network_phase_complete_with_retry_candidates", text)
        self.assertIn("--global-rps 0.35", text)
        self.assertNotIn("--global-rps 1", text)
        self.assertIn("試行上限は0.35 RPS", text)
        self.assertNotIn("成功取得が銘柄コードの前半に偏るため、今の結果", text)
        self.assertNotIn("[制御記録](None)", text)


if __name__ == "__main__":
    unittest.main()
