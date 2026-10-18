"""Work-accounting regressions; fixtures do not measure investment analysis."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest

from ir_agent.capacity import report_research_capacity


BASE = datetime(2026, 10, 15, 0, tzinfo=timezone.utc)


def at(seconds):
    return (BASE + timedelta(seconds=seconds)).isoformat()


def measurement(id="a", *, start=0, end=60, worker="worker-1", status="completed", **updates):
    value = {"id": id, "company_id": "jp:130A", "stage": "disclosure_review", "worker_id": worker,
             "attempt_id": id, "started_at": at(start), "ended_at": at(end) if end is not None else None,
             "status": status}
    value.update(updates)
    return value


def request(*values, capacity=None):
    return {"schema_version": 1, "window": {"started_at": at(0), "ended_at": at(600)},
            "operator_capacity": capacity or {}, "measurements": list(values)}


class CapacityTests(unittest.TestCase):
    def observed(self, value):
        return report_research_capacity(value)["cohorts"]["observed"]

    def test_resend_deduplicates_but_altered_measurement_id_is_rejected(self):
        item = measurement(active_seconds="15", tokens=100, cost={"amount": "2", "currency": "JPY"})
        value = request(item, deepcopy(item))
        result = report_research_capacity(value)
        self.assertEqual(result["duplicate_records_ignored"], 1)
        self.assertEqual(result["unique_records"], 1)
        self.assertEqual(result["cohorts"]["observed"]["usage"]["tokens"]["value"], 100)
        value["measurements"][1]["tokens"] = 101
        with self.assertRaisesRegex(ValueError, "altered"):
            report_research_capacity(value)

    def test_same_physical_attempt_cannot_be_double_counted_by_changing_id(self):
        one = measurement()
        two = deepcopy(one)
        two["id"] = "another-measurement-id"
        with self.assertRaisesRegex(ValueError, "physical attempt"):
            report_research_capacity(request(one, two))

    def test_elapsed_is_never_used_as_missing_active_tokens_or_cost(self):
        data = self.observed(request(measurement(end=300)))
        self.assertIsNone(data["usage"]["active_seconds"]["worker_total"])
        self.assertIsNone(data["usage"]["tokens"]["value"])
        self.assertIsNone(data["usage"]["cost"]["value"])
        stage = data["stages"]["disclosure_review"]
        self.assertEqual(stage["elapsed_seconds_whole_attempt_samples"]["total"], "300")
        self.assertEqual(stage["active_seconds_whole_attempt_samples"]["count"], 0)
        self.assertIsNone(stage["active_seconds_whole_attempt_samples"]["mean"])

    def test_failed_and_retry_work_remains_in_usage_and_separate_terminal_counts(self):
        data = self.observed(request(
            measurement("fail", end=60, status="failed", active_seconds="30", tokens=10, cost={"amount": "1", "currency": "JPY"}),
            measurement("retry", start=60, end=120, status="retry", active_seconds="40", tokens=20, cost={"amount": "2", "currency": "JPY"}),
            measurement("done", start=120, end=180, active_seconds="50", tokens=30, cost={"amount": "3", "currency": "JPY"}),
            capacity={"worker_seconds": "200", "cost_budget": {"amount": "10", "currency": "JPY"}},
        ))
        self.assertEqual(data["terminal_events_in_window"]["failed"], 1)
        self.assertEqual(data["terminal_events_in_window"]["retry"], 1)
        self.assertEqual(data["completed_attempts"], 1)
        self.assertEqual(data["usage"]["active_seconds"]["worker_total"], "120")
        self.assertEqual(data["usage"]["tokens"]["value"], 60)
        self.assertEqual(data["usage"]["cost"]["value"], {"amount": "6", "currency": "JPY"})
        self.assertEqual(data["budget_comparison"]["worker_seconds"]["remaining_worker_seconds"], "80")
        self.assertEqual(data["budget_comparison"]["cost"]["remaining_amount"], "4")

    def test_worker_union_prevents_same_worker_from_becoming_two_parallel_workers(self):
        data = self.observed(request(
            measurement("a", start=0, end=360, active_seconds="60"),
            measurement("b", start=180, end=540, active_seconds="60"),
            measurement("c", start=120, end=480, worker="worker-2", active_seconds="60"),
            capacity={"worker_seconds": "2000"},
        ))
        intervals = data["worker_intervals"]
        self.assertEqual(intervals["sum_record_elapsed_seconds"], "1080")
        self.assertEqual(intervals["occupied_elapsed_seconds_union_by_worker"], "900")
        self.assertEqual(intervals["overlapping_same_worker_elapsed_seconds"], "180")
        self.assertEqual(intervals["any_worker_occupied_wall_seconds"], "540")
        self.assertEqual(intervals["maximum_distinct_workers_overlapping"], 2)
        self.assertIsNone(data["usage"]["active_seconds"]["worker_total"])
        self.assertEqual(data["usage"]["active_seconds"]["known_whole_attempt_sum"], "180")
        self.assertIsNone(data["budget_comparison"]["worker_seconds"])

    def test_cross_window_totals_are_not_prorated_and_unfinished_is_not_queue_wait(self):
        data = self.observed(request(
            measurement("carry", start=-60, end=60, active_seconds="80", tokens=80, cost={"amount": "8", "currency": "JPY"}),
            measurement("future-end", start=540, end=660, active_seconds="80", tokens=80),
            measurement("open", start=300, end=None, status="in_progress"),
        ))
        self.assertEqual(data["carried_in_records"], 1)
        self.assertEqual(data["usage"]["active_seconds"]["unallocated_crossing_or_unfinished_records"], 3)
        self.assertIsNone(data["usage"]["tokens"]["value"])
        self.assertIsNone(data["usage"]["cost"]["value"])
        backlog = data["backlog_at_window_end"]
        self.assertEqual(backlog["unfinished_observed_attempts"], 2)
        self.assertEqual(backlog["longest_since_start_seconds"], "300")
        self.assertIsNone(backlog["queue_wait_seconds"])
        self.assertIsNone(backlog["overdue_attempts"])
        self.assertEqual(data["completed_attempts"], 1)

    def test_outside_window_and_end_boundary_events_are_explicit(self):
        data = self.observed(request(
            measurement("before", start=-120, end=-60),
            measurement("after", start=601, end=660),
            measurement("boundary", start=540, end=600, active_seconds="30"),
        ))
        self.assertEqual(data["outside_window_records"], 2)
        self.assertEqual(data["in_window_records"], 1)
        self.assertEqual(data["completed_attempts"], 0)
        self.assertEqual(data["terminal_events_exactly_at_window_end"], 1)
        self.assertEqual(data["backlog_at_window_end"]["unfinished_observed_attempts"], 0)

    def test_partial_missing_usage_remains_null_but_zero_is_measured(self):
        data = self.observed(request(
            measurement("known", active_seconds="0", tokens=0, cost={"amount": "0", "currency": "JPY"}),
            measurement("missing", start=60, end=120),
        ))
        self.assertEqual(data["usage"]["active_seconds"]["known_whole_attempt_sum"], "0")
        self.assertEqual(data["usage"]["tokens"]["known_whole_attempt_sum"], 0)
        self.assertIsNone(data["usage"]["tokens"]["value"])
        self.assertIsNone(data["usage"]["cost"]["value"])
        zero = self.observed(request(measurement(active_seconds="0", tokens=0, cost={"amount": "0", "currency": "JPY"})))
        self.assertEqual(zero["usage"]["tokens"]["value"], 0)
        self.assertEqual(zero["usage"]["cost"]["value"]["amount"], "0")

    def test_mixed_currencies_are_not_added_or_converted_to_budget(self):
        data = self.observed(request(
            measurement("jpy", cost={"amount": "100", "currency": "JPY"}),
            measurement("usd", start=60, end=120, cost={"amount": "1", "currency": "USD"}),
            capacity={"cost_budget": {"amount": "1000", "currency": "JPY"}},
        ))
        self.assertIsNone(data["usage"]["cost"]["value"])
        self.assertEqual(data["usage"]["cost"]["known_whole_attempt_sums_by_currency"], {"JPY": "100", "USD": "1"})
        self.assertIsNone(data["budget_comparison"]["cost"])

    def test_synthetic_and_observed_records_never_share_usage_or_budget(self):
        result = report_research_capacity(request(
            measurement("real", active_seconds="10"),
            measurement("fiction", active_seconds="50", synthetic=True),
            capacity={"worker_seconds": "100"},
        ))
        self.assertEqual(result["measurement_mode"], "mixed")
        self.assertEqual(result["cohorts"]["observed"]["usage"]["active_seconds"]["worker_total"], "10")
        self.assertEqual(result["cohorts"]["synthetic"]["usage"]["active_seconds"]["worker_total"], "50")
        self.assertIsNone(result["cohorts"]["synthetic"]["budget_comparison"]["worker_seconds"])
        self.assertIsNotNone(result["cohorts"]["observed"]["budget_comparison"]["worker_seconds"])
        self.assertIsNone(result["company_upper_bound"])

    def test_unknown_capacity_and_completed_stage_do_not_establish_company_upper_limit(self):
        result = report_research_capacity(request(measurement(active_seconds="10")))
        self.assertIsNone(result["operator_capacity"]["worker_seconds"])
        self.assertIsNone(result["operator_capacity"]["cost_budget"])
        self.assertIsNone(result["company_upper_bound"])
        self.assertEqual(result["capacity_status"], "not_estimated")
        self.assertEqual(result["cohorts"]["observed"]["completed_company_coverage"], 1)
        self.assertIsNone(result["cohorts"]["observed"]["budget_comparison"]["worker_seconds"])

    def test_invalid_time_status_or_usage_is_rejected(self):
        bad = [measurement(start=60, end=0), measurement(active_seconds="61"), measurement(tokens=True),
               measurement(active_seconds=-1), measurement(status="unknown"), measurement(ended_at=None),
               measurement(cost={"amount": "2"}), measurement(cost={"amount": "NaN", "currency": "JPY"}),
               measurement(started_at="2026-10-15T09:00:00"), measurement(active_second=1)]
        for item in bad:
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    report_research_capacity(request(item))

    def test_report_is_deterministic_and_does_not_mutate_measurements(self):
        value = request(measurement(active_seconds="10"))
        original = deepcopy(value)
        self.assertEqual(report_research_capacity(value), report_research_capacity(value))
        self.assertEqual(value, original)

    def test_sample_is_explicitly_synthetic_and_empty_observed_usage_is_unknown(self):
        path = Path(__file__).parents[1] / "examples/work-measurements.json"
        result = report_research_capacity(json.loads(path.read_text()))
        self.assertEqual(result["measurement_mode"], "synthetic_only")
        self.assertEqual(result["cohorts"]["observed"]["input_unique_records"], 0)
        self.assertIsNone(result["cohorts"]["observed"]["usage"]["tokens"]["value"])
        self.assertEqual(result["cohorts"]["synthetic"]["outside_window_records"], 1)
        self.assertIsNone(result["company_upper_bound"])


if __name__ == "__main__":
    unittest.main()
