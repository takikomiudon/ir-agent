"""Cutoff-time IR observation coverage, explicit missingness and strict history."""
from copy import deepcopy
from decimal import Decimal, Inexact, localcontext
import json
from pathlib import Path
import unittest

from ir_agent.observations import summarize_observations, validate_observation

AS_OF = "2026-11-20T17:00:00+09:00"


def fixture():
    return json.loads((Path(__file__).resolve().parents[1] / "examples/ir-observations.json").read_text())["records"][0]


def distinct(value, suffix):
    value = deepcopy(value)
    value["id"] += suffix; value["question_id"] += suffix
    for reply in value["replies"]: reply["id"] += suffix
    return value


class ObservationTests(unittest.TestCase):
    def test_empty_input_is_normal_and_does_not_claim_calibration(self):
        result = summarize_observations([], as_of=AS_OF)
        self.assertEqual(result["record_count"], 0)
        self.assertEqual(result["cohorts"], [])
        self.assertEqual(result["calibration_status"], "needs_calibration")
        self.assertEqual(result["status"], "observations_only")

    def test_fixture_is_independent_copy_and_all_ratios_have_denominators(self):
        value = fixture(); original = deepcopy(value)
        validated = validate_observation(value)
        self.assertEqual(validated, value); self.assertIsNot(validated, value)
        result = summarize_observations([value], as_of=AS_OF)
        self.assertEqual(result["eligible_count"], 1)
        group = result["cohorts"][0]
        cell = group["descriptive_signal_ratios_given_verified_state"]["temporary"]["temporary_explanation"]
        self.assertEqual(cell, {"numerator": 1, "denominator": 1, "ratio": "1"})
        absent = group["descriptive_signal_ratios_given_verified_state"]["persistent"]["temporary_explanation"]
        self.assertIsNone(absent["ratio"]); self.assertEqual(absent["denominator"], 0)
        self.assertEqual(value, original)
        self.assertNotIn("likelihoods", result)

    def test_future_publication_and_verification_are_not_used_at_cutoff(self):
        result = summarize_observations([fixture()], as_of="2026-10-15T17:00:00+09:00")
        view = result["observations"][0]
        self.assertEqual(view["signal"], "temporary_explanation")
        self.assertIsNone(view["state"])
        self.assertEqual(result["eligible_count"], 0)
        self.assertEqual(view["verification_status"], "awaiting_verification_deadline")

    def test_future_design_is_retained_without_counting_as_active(self):
        result = summarize_observations([fixture()], as_of="2026-09-01T00:00:00+09:00")
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["not_yet_recorded_count"], 1)
        self.assertEqual(result["active_count"], 0)
        self.assertEqual(result["cohorts"][0]["active_count"], 0)

    def test_response_not_verified_is_not_invented_as_no_response(self):
        value = fixture(); value["replies"] = []; value.pop("response_check")
        result = summarize_observations([value], as_of=AS_OF)
        self.assertEqual(result["response_counts"], {"response_not_verified": 1})
        self.assertEqual(result["eligible_count"], 0)
        self.assertIsNone(result["observations"][0]["signal"])

    def test_no_response_and_late_reply_preserve_deadline_outcome(self):
        value = fixture()
        value["replies"][0].update(received_at="2026-10-10T10:00:00+09:00", recorded_at="2026-10-10T10:01:00+09:00")
        result = summarize_observations([value], as_of=AS_OF)
        self.assertEqual(result["response_counts"], {"no_response_by_deadline": 1})
        self.assertEqual(result["records_with_late_replies"], 1)
        self.assertEqual(result["cohorts"][0]["state_signal_counts"]["temporary"]["no_response_by_deadline"], 1)
        before_late = summarize_observations([value], as_of="2026-10-09T17:00:00+09:00")
        self.assertEqual(before_late["records_with_late_replies"], 0)

    def test_unrecorded_future_response_check_cannot_prove_no_response(self):
        value = fixture(); value["replies"] = []
        value["response_check"]["recorded_at"] = "2026-11-20T18:00:00+09:00"
        result = summarize_observations([value], as_of=AS_OF)
        self.assertEqual(result["response_counts"], {"response_not_verified": 1})

    def test_awaiting_deadline_is_distinct_from_no_response(self):
        value = fixture(); value["replies"] = []
        result = summarize_observations([value], as_of="2026-10-03T12:00:00+09:00")
        self.assertEqual(result["response_counts"], {"awaiting_reply_deadline": 1})

    def test_failed_unknown_and_unsent_are_retained_but_not_signal_denominators(self):
        records = []
        for status in ("failed", "unknown", "unsent"):
            value = distinct(fixture(), status); value["replies"] = []; value.pop("response_check")
            if status == "unsent": value.pop("dispatch")
            else: value["dispatch"]["status"] = status
            records.append(value)
        result = summarize_observations(records, as_of=AS_OF)
        self.assertEqual(result["active_count"], 3)
        self.assertEqual(result["eligible_count"], 0)
        self.assertEqual(result["response_counts"], {"delivery_failed": 1, "delivery_unknown": 1, "not_applicable": 1})
        self.assertEqual(result["excluded_active_count"], 3)

    def test_unclear_declined_and_held_reply_have_different_meanings(self):
        records = []
        for signal, information in (("unclear", "public_clarification"), ("declined", "public_clarification"), ("temporary_explanation", "unclear")):
            value = distinct(fixture(), signal); value["replies"][0].update(signal=signal, information_status=information)
            records.append(value)
        result = summarize_observations(records, as_of=AS_OF)
        self.assertEqual(result["eligible_count"], 2)
        counts = result["cohorts"][0]["state_signal_counts"]["temporary"]
        self.assertEqual(counts["unclear"], 1); self.assertEqual(counts["declined"], 1)
        self.assertEqual(counts["temporary_explanation"], 0)
        self.assertIn("reply_information_held_for_review", result["observations"][2]["exclusion_reasons"])

    def test_verification_missing_pending_changed_and_unknown_are_not_wrong_answers(self):
        records = []
        for status in ("missing", "pending", "not_identifiable", "state_changed", "definition_mismatch"):
            value = distinct(fixture(), status)
            if status == "missing": value.pop("verification")
            else:
                value["verification"].update(status=status, recorded_at="2026-11-20T12:00:00+09:00", evidence=[])
                value["verification"].pop("state")
            records.append(value)
        result = summarize_observations(records, as_of=AS_OF)
        self.assertEqual(result["active_count"], 5); self.assertEqual(result["eligible_count"], 0)
        self.assertEqual(result["cohorts"][0]["excluded_count"], 5)
        self.assertEqual(result["verification_counts"]["verification_missing_after_deadline"], 1)

    def test_external_change_blocks_hindsight_state_inference(self):
        value = fixture()
        value["external_changes"] = [{"id": "shock", "occurred_at": "2026-10-20T12:00:00+09:00", "recorded_at": "2026-10-20T13:00:00+09:00", "description": "Synthetic acquisition changes cost structure", "impact": "invalidates_question_time_inference"}]
        result = summarize_observations([value], as_of=AS_OF)
        self.assertEqual(result["eligible_count"], 0)
        self.assertIn("external_change_blocks_state_inference", result["observations"][0]["exclusion_reasons"])
        value["external_changes"][0]["impact"] = "reviewed_no_change"
        self.assertEqual(summarize_observations([value], as_of=AS_OF)["eligible_count"], 1)

    def test_different_cohorts_are_not_pooled_and_policy_mix_is_exposed(self):
        first = fixture(); second = distinct(first, "2")
        second["policy_ref"] = {"id": "synthetic-policy", "version": 2}
        result = summarize_observations([first, second], as_of=AS_OF)
        self.assertEqual(result["unknown_policy_count"], 1)
        self.assertEqual(len(result["cohorts"][0]["policy_counts"]), 2)
        self.assertTrue(result["cohorts"][0]["within_company_repetition_present"])
        second["cohort_id"] = "different-cohort"
        second["hypothesis"]["states"]["temporary"] = "A different operational definition"
        self.assertEqual(len(summarize_observations([first, second], as_of=AS_OF)["cohorts"]), 2)

    def test_incompatible_state_signal_period_or_synthetic_definition_is_rejected(self):
        changes = [lambda v: v["hypothesis"]["states"].update(temporary="different definition"),
                   lambda v: v["signals"].update(unclear="different definition"),
                   lambda v: v["hypothesis"].update(state_timing="future_outcome"),
                   lambda v: v["hypothesis"]["target_period"].update(end="2026-10-01"),
                   lambda v: v.update(synthetic=False)]
        for change in changes:
            second = distinct(fixture(), "2"); change(second)
            with self.subTest(change=changes.index(change)), self.assertRaises(ValueError):
                summarize_observations([fixture(), second], as_of=AS_OF)

    def test_duplicate_observation_question_reply_and_evidence_ids_are_rejected(self):
        value = fixture()
        with self.assertRaisesRegex(ValueError, "Duplicate observation"):
            summarize_observations([value, deepcopy(value)], as_of=AS_OF)
        duplicate = deepcopy(value); duplicate["id"] += "second"
        with self.assertRaisesRegex(ValueError, "company/question"):
            summarize_observations([value, duplicate], as_of=AS_OF)
        duplicate = distinct(value, "2"); duplicate["replies"][0]["id"] = value["replies"][0]["id"]
        with self.assertRaisesRegex(ValueError, "reply ID"):
            summarize_observations([value, duplicate], as_of=AS_OF)
        for field in ("replies", "premise_evidence"):
            value = fixture(); value[field].append(deepcopy(value[field][0]))
            with self.assertRaises(ValueError): validate_observation(value)

    def test_malformed_and_backdated_histories_are_rejected(self):
        changes = [
            lambda v: v.update(design_recorded_at="2026-10-01T09:59:00+09:00"),
            lambda v: v["dispatch"].update(attempted_at="2026-10-01T10:00:00+09:00"),
            lambda v: v["dispatch"].update(attempted_at="2026-10-09T10:00:00+09:00", recorded_at="2026-10-09T10:00:00+09:00"),
            lambda v: v["replies"][0].update(received_at="2026-10-01T09:00:00+09:00"),
            lambda v: v["replies"][0].update(signal="no_response_by_deadline"),
            lambda v: v["response_check"].update(recorded_at="2026-10-07T17:00:00+09:00"),
            lambda v: v["verification"].update(recorded_at="2026-10-01T09:00:00+09:00"),
            lambda v: v["verification"].update(state="invented"),
            lambda v: v["verification"]["evidence"][0].update(retrieved_at="2026-11-03T17:00:00+09:00"),
            lambda v: v["verification"]["evidence"][0].update(company_id="other-company"),
            lambda v: v["premise_evidence"][0].update(retrieved_at="2026-10-01T10:00:01+09:00"),
            lambda v: v.update(reply_deadline="2026-10-01T10:00:00+09:00"),
            lambda v: v.update(policy_ref={"id": "policy", "version": True}),
            lambda v: v.update(typo="not silently ignored"),
        ]
        for change in changes:
            value = fixture(); change(value)
            with self.subTest(change=changes.index(change)), self.assertRaises(ValueError): validate_observation(value)

    def test_prior_is_optional_but_never_filled_from_observed_counts(self):
        value = fixture(); value["prior"] = {"temporary": ".3", "persistent": ".3", "mixed": ".4"}
        value["prior_provenance"] = {"kind": "synthetic_example", "reference": "arithmetic fixture", "rationale": "Not a fitted prior"}
        self.assertEqual(validate_observation(value)["prior"], value["prior"])
        value["prior"]["temporary"] = ".30000000000000000000000000000001"
        with self.assertRaises(ValueError): validate_observation(value)
        value["prior"]["temporary"] = "NaN"
        with self.assertRaises(ValueError): validate_observation(value)

    def test_conflicting_simultaneous_first_replies_are_not_arbitrarily_selected(self):
        value = fixture(); another = deepcopy(value["replies"][0]); another.update(id="second", signal="persistent_explanation")
        value["replies"].append(another)
        result = summarize_observations([value], as_of=AS_OF)
        self.assertEqual(result["eligible_count"], 0)
        self.assertEqual(result["response_counts"], {"conflicting_first_replies": 1})

    def test_repeating_ratio_reports_exact_fraction_and_independent_decimal_context(self):
        records = []
        for i, signal in enumerate(("temporary_explanation", "unclear", "declined")):
            value = distinct(fixture(), str(i)); value["replies"][0]["signal"] = signal; records.append(value)
        with localcontext() as context:
            context.prec = 2; context.traps[Inexact] = True
            result = summarize_observations(records, as_of=AS_OF)
        cell = result["cohorts"][0]["descriptive_signal_ratios_given_verified_state"]["temporary"]["unclear"]
        self.assertEqual((cell["numerator"], cell["denominator"]), (1, 3))
        self.assertTrue(cell["ratio"].startswith("0.3333333333333333"))


if __name__ == "__main__": unittest.main()
