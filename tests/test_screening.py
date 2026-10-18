"""Sourced comparisons identify research candidates without investment defaults."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from ir_agent.screening import evaluate_screening


def fixture():
    return json.loads((Path(__file__).resolve().parents[1] / "examples/screening.json").read_text())


def metric_field(value, metric, field, replacement):
    value["metrics"][metric][field] = replacement
    source = next(s for s in value["sources"] if s["id"] == value["metrics"][metric]["source_id"])
    path = value["metrics"][metric]["bindings"][field]
    target = source
    for item in path[:-1]: target = target[item]
    target[path[-1]] = deepcopy(replacement)
    for other in value["metrics"].values():
        if other["source_id"] == source["id"] and other["bindings"].get(field) == path:
            other[field] = deepcopy(replacement)


class ScreeningTests(unittest.TestCase):
    def test_passing_screen_only_identifies_research_candidate(self):
        value = fixture(); original = deepcopy(value)
        result = evaluate_screening(value)
        self.assertEqual(result["status"], "candidate_for_research")
        self.assertTrue(result["synthetic"])
        self.assertEqual([r["status"] for r in result["rule_results"]], ["pass", "pass"])
        self.assertNotIn("proposed_action", result)
        self.assertEqual(value, original)

    def test_missing_policy_rules_threshold_source_or_age_never_supplies_defaults(self):
        changes = [lambda v: v.update(policy=None), lambda v: v["policy"].update(rules=[]),
                   lambda v: v["policy"]["rules"][1].pop("source"),
                   lambda v: v["policy"]["rules"][1]["comparison"].pop("value"),
                   lambda v: v["policy"]["rules"][1].pop("max_age_seconds")]
        for change in changes:
            value = fixture(); change(value)
            with self.subTest(change=changes.index(change)):
                self.assertEqual(evaluate_screening(value)["status"], "needs_policy")

    def test_externally_sourced_rules_can_run_without_synthetic_policy_defaults(self):
        value = fixture(); value["synthetic"] = False
        for s in value["sources"]: s["metadata"].pop("synthetic")
        for r in value["policy"]["rules"]: r["source"]["kind"] = "external_policy"
        self.assertEqual(evaluate_screening(value)["status"], "candidate_for_research")
        value["policy"]["rules"][0]["source"]["reference"] = ""
        self.assertEqual(evaluate_screening(value)["status"], "needs_policy")

    def test_synthetic_policy_or_data_is_not_silently_used_as_live(self):
        value = fixture(); value["synthetic"] = False
        self.assertEqual(evaluate_screening(value)["status"], "needs_policy")
        for r in value["policy"]["rules"]: r["source"]["kind"] = "user"
        self.assertEqual(evaluate_screening(value)["status"], "needs_data")

    def test_unsupported_financial_model_is_separate_from_exclusion(self):
        value = fixture(); value["company"]["financial_model"] = "bank_model"
        self.assertEqual(evaluate_screening(value)["status"], "unsupported_model")
        value["company"].pop("financial_model")
        self.assertEqual(evaluate_screening(value)["status"], "needs_data")

    def test_industry_name_ir_contact_and_db_status_do_not_decide(self):
        value = fixture(); value["company"].update(industry="banking", ir_contact_available=False, status="excluded")
        result = evaluate_screening(value)
        self.assertEqual(result["status"], "candidate_for_research")
        self.assertEqual(value["company"]["status"], "excluded")

    def test_exact_threshold_boundary_and_strict_comparison(self):
        value = fixture()
        self.assertEqual(evaluate_screening(value)["status"], "candidate_for_research")
        value["policy"]["rules"][1]["operator"] = "gt"
        self.assertEqual(evaluate_screening(value)["status"], "does_not_match_policy")
        metric_field(value, "turnover", "value", "100.000000000000000000000001")
        self.assertEqual(evaluate_screening(value)["status"], "candidate_for_research")

    def test_all_supported_operators_and_negative_values_are_numeric(self):
        for operator, threshold, expected in (("lt", "101", "candidate_for_research"), ("le", "100", "candidate_for_research"),
                ("ge", "100", "candidate_for_research"), ("gt", "100", "does_not_match_policy"),
                ("eq", "100", "candidate_for_research"), ("ne", "100", "does_not_match_policy")):
            value = fixture(); value["policy"]["rules"][1].update(operator=operator)
            value["policy"]["rules"][1]["comparison"]["value"] = threshold
            with self.subTest(operator=operator): self.assertEqual(evaluate_screening(value)["status"], expected)
        value = fixture(); metric_field(value, "turnover", "value", "-1")
        self.assertEqual(evaluate_screening(value)["status"], "does_not_match_policy")

    def test_external_benchmark_is_source_bound_and_must_be_comparable(self):
        for field, replacement in (("unit", "percent"), ("definition", "forward standalone PE"),
                                   ("period", {"kind": "instant", "end": "2026-10-14"}),
                                   ("observed_at", "2026-10-15T15:29:00+09:00")):
            value = fixture(); metric_field(value, "sector_pe", field, replacement)
            with self.subTest(field=field): self.assertEqual(evaluate_screening(value)["status"], "needs_data")

    def test_forecast_actual_duration_and_unit_mismatch_do_not_convert_automatically(self):
        for field, replacement in (("unit", "JPY million"), ("definition", "another definition"),
                                   ("period", {"kind": "duration", "start": "2026-10-01", "end": "2026-10-15"})):
            value = fixture(); value["policy"]["rules"][1]["comparison"][field] = replacement
            with self.subTest(field=field): self.assertEqual(evaluate_screening(value)["status"], "needs_data")

    def test_duration_period_must_match_full_start_and_end(self):
        value = fixture(); value["policy"]["rules"] = [value["policy"]["rules"][1]]
        period = {"kind": "duration", "start": "2026-04-01", "end": "2026-10-15"}
        metric_field(value, "turnover", "period", period)
        value["policy"]["rules"][0]["comparison"]["period"] = period.copy()
        self.assertEqual(evaluate_screening(value)["status"], "candidate_for_research")
        value["policy"]["rules"][0]["comparison"]["period"]["start"] = "2026-07-01"
        self.assertEqual(evaluate_screening(value)["status"], "needs_data")

    def test_missing_metric_source_or_binding_is_missing_data(self):
        changes = [lambda v: v["metrics"].pop("pe"), lambda v: v.update(sources=[]),
                   lambda v: v["metrics"]["pe"].pop("bindings"),
                   lambda v: v["metrics"]["sector_pe"]["bindings"].pop("unit")]
        for change in changes:
            value = fixture(); change(value)
            with self.subTest(change=changes.index(change)): self.assertEqual(evaluate_screening(value)["status"], "needs_data")

    def test_same_company_and_actual_source_field_binding_are_required(self):
        value = fixture(); value["metrics"]["pe"]["subject_id"] = "another-company"
        self.assertEqual(evaluate_screening(value)["status"], "needs_data")
        for field, replacement in (("value", "1"), ("unit", "JPY"), ("definition", "invented"),
                                   ("period", {"kind": "instant", "end": "2026-10-14"}),
                                   ("observed_at", "2026-10-15T15:29:00+09:00")):
            value = fixture(); value["metrics"]["pe"][field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError): evaluate_screening(value)

    def test_future_sources_period_observation_and_policy_are_unavailable(self):
        value = fixture(); value["as_of"] = "2026-10-15T15:30:30+09:00"
        self.assertEqual(evaluate_screening(value)["status"], "needs_data")
        value = fixture(); metric_field(value, "pe", "period", {"kind": "instant", "end": "2026-10-16"})
        self.assertEqual(evaluate_screening(value)["status"], "needs_data")
        value = fixture(); metric_field(value, "pe", "observed_at", "2026-10-16T15:30:00+09:00")
        self.assertEqual(evaluate_screening(value)["status"], "needs_data")
        value = fixture(); value["policy"]["recorded_at"] = "2026-10-16T08:00:00+09:00"
        self.assertEqual(evaluate_screening(value)["status"], "needs_policy")

    def test_freshness_boundary_is_explicit_policy_not_default(self):
        value = fixture(); value["as_of"] = "2026-10-16T15:30:00+09:00"
        self.assertEqual(evaluate_screening(value)["status"], "candidate_for_research")
        value["as_of"] = "2026-10-16T15:30:00.000001+09:00"
        self.assertEqual(evaluate_screening(value)["status"], "needs_data")

    def test_hidden_origin_held_information_is_not_screenable(self):
        value = fixture(); value["sources"][0]["metadata"]["original_source_id"] = "held"
        origin = deepcopy(value["sources"][0]); origin.update(id="held", source_type="ir_reply")
        origin["metadata"] = {"information_status": "unclear"}
        value["sources"].append(origin)
        result = evaluate_screening(value)
        self.assertEqual(result["status"], "needs_data")
        self.assertIn("source_information_held_for_review", result["rule_results"][0]["reason_codes"])

    def test_synthetic_origin_cannot_be_laundered_by_live_wrapper(self):
        value = fixture(); value["synthetic"] = False
        for rule in value["policy"]["rules"]: rule["source"]["kind"] = "user"
        for source in value["sources"]: source["metadata"].pop("synthetic")
        origin = deepcopy(value["sources"][0]); origin["id"] = "synthetic-origin"; origin["metadata"] = {"synthetic": True}
        value["sources"].append(origin)
        value["sources"][0]["metadata"]["original_source_id"] = origin["id"]
        self.assertEqual(evaluate_screening(value)["status"], "needs_data")

    def test_misspelled_duplicate_nonfinite_and_non_numeric_inputs_are_rejected(self):
        changes = [lambda v: v["policy"]["rules"][0].update(operator="greater"),
                   lambda v: v["policy"]["rules"].append(deepcopy(v["policy"]["rules"][0])),
                   lambda v: v["sources"].append(deepcopy(v["sources"][0])),
                   lambda v: v["metrics"]["pe"].update(value="NaN"),
                   lambda v: v["metrics"]["pe"].update(value=True),
                   lambda v: v["policy"]["rules"][1]["comparison"].update(value="Infinity"),
                   lambda v: v["policy"]["rules"][0].update(max_age_seconds=True),
                   lambda v: v.update(unrecognised=True)]
        for change in changes:
            value = fixture(); change(value)
            with self.subTest(change=changes.index(change)), self.assertRaises(ValueError): evaluate_screening(value)


if __name__ == "__main__": unittest.main()
