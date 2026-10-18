"""Known finite decision problems, malformed models, and arithmetic boundaries."""
from copy import deepcopy
from decimal import Decimal, Inexact, localcontext
import json
from pathlib import Path
import unittest

from ir_agent.information_value import calculate_information_value


def fixture():
    return json.loads((Path(__file__).resolve().parents[1] / "examples/information-value.json").read_text())


class InformationValueTests(unittest.TestCase):
    def test_known_imperfect_signal_problem(self):
        value = fixture(); before = deepcopy(value)
        result = calculate_information_value(value)
        self.assertEqual(result["baseline"]["best_actions"], ["continue_review", "defer"])
        self.assertEqual(Decimal(result["baseline"]["expected_value"]), 0)
        self.assertEqual(Decimal(result["perfect_information"]["evpi"]), 50)
        sample = result["sample_information"]
        self.assertEqual(Decimal(sample["evsi"]), 30)
        self.assertEqual(Decimal(sample["net_evsi"]), 25)
        self.assertEqual(Decimal(sample["signals"]["temporary_explanation"]["posterior"]["temporary_cost"]), Decimal("0.8"))
        self.assertTrue(sample["worth_cost"])
        self.assertEqual(value, before)

    def test_absent_likelihoods_do_not_invent_ir_accuracy(self):
        for null in (False, True):
            value = fixture(); value["provenance"].pop("likelihoods")
            if null: value["likelihoods"] = None
            else: value.pop("likelihoods")
            result = calculate_information_value(value)
            self.assertEqual(result["status"], "needs_calibration")
            self.assertIsNone(result["sample_information"])
            self.assertEqual(Decimal(result["perfect_information"]["evpi"]), 50)

    def test_perfect_signals_attain_evpi_without_assuming_ir_is_perfect(self):
        value = fixture()
        value["likelihoods"] = {"first": {"temporary_cost": 1, "persistent_cost": 0},
                                "second": {"temporary_cost": 0, "persistent_cost": 1}}
        result = calculate_information_value(value)
        self.assertEqual(Decimal(result["sample_information"]["evsi"]), Decimal(result["perfect_information"]["evpi"]))

    def test_noninformative_signals_have_no_value(self):
        value = fixture()
        value["likelihoods"] = {"reply": {"temporary_cost": ".75", "persistent_cost": ".75"},
                                "no_reply": {"temporary_cost": ".25", "persistent_cost": ".25"}}
        sample = calculate_information_value(value)["sample_information"]
        self.assertEqual(sample["evsi"], "0")
        self.assertEqual(Decimal(sample["net_evsi"]), -5)
        self.assertFalse(sample["worth_cost"])

    def test_no_reply_is_an_explicit_signal_not_automatic_bad_news(self):
        value = fixture()
        value["likelihoods"] = {"reply": {"temporary_cost": ".5", "persistent_cost": ".5"},
                                "no_reply": {"temporary_cost": ".5", "persistent_cost": ".5"}}
        signal = calculate_information_value(value)["sample_information"]["signals"]["no_reply"]
        self.assertEqual({s: Decimal(p) for s, p in signal["posterior"].items()},
                         {s: Decimal(p) for s, p in value["prior"].items()})

    def test_informative_signal_without_action_change_has_zero_evsi(self):
        value = fixture()
        value["payoffs"]["continue_review"] = {"temporary_cost": 100, "persistent_cost": 1}
        sample = calculate_information_value(value)["sample_information"]
        self.assertEqual(sample["evsi"], "0")
        self.assertTrue(all(x["best_actions"] == ["continue_review"] for x in sample["signals"].values()))

    def test_zero_prior_and_impossible_signal_do_not_divide_by_zero(self):
        value = fixture(); value["prior"] = {"temporary_cost": 1, "persistent_cost": 0}
        value["likelihoods"] = {"seen": {"temporary_cost": 1, "persistent_cost": 0},
                                "impossible": {"temporary_cost": 0, "persistent_cost": 1}}
        result = calculate_information_value(value)
        self.assertEqual(result["perfect_information"]["evpi"], "0")
        impossible = result["sample_information"]["signals"]["impossible"]
        self.assertIsNone(impossible["posterior"])
        self.assertFalse(impossible["possible"])
        self.assertEqual(impossible["best_actions"], [])

    def test_zero_cost_and_exact_break_even(self):
        value = fixture(); value["question_cost"] = 0
        self.assertEqual(Decimal(calculate_information_value(value)["sample_information"]["net_evsi"]), 30)
        value["question_cost"] = 30
        sample = calculate_information_value(value)["sample_information"]
        self.assertEqual(sample["cost_comparison"], "break_even")
        self.assertFalse(sample["worth_cost"])

    def test_all_negative_payoffs_and_translation_do_not_change_value(self):
        value = fixture()
        original = calculate_information_value(value)
        for row in value["payoffs"].values():
            for state in row: row[state] = str(Decimal(row[state]) - 1000)
        translated = calculate_information_value(value)
        self.assertLess(Decimal(translated["baseline"]["expected_value"]), 0)
        self.assertEqual(translated["perfect_information"]["evpi"], original["perfect_information"]["evpi"])
        self.assertEqual(translated["sample_information"]["evsi"], original["sample_information"]["evsi"])

    def test_exact_tiny_improvement_is_not_rounded_to_zero(self):
        value = fixture(); value["question_cost"] = 0
        value["likelihoods"] = {
            "first": {"temporary_cost": ".500000000000000000000000000001", "persistent_cost": ".5"},
            "second": {"temporary_cost": ".499999999999999999999999999999", "persistent_cost": ".5"}}
        with localcontext() as context:
            context.prec = 2; context.traps[Inexact] = True
            result = calculate_information_value(value)
        self.assertEqual(Decimal(result["sample_information"]["evsi"]), Decimal("5e-29"))

    def test_repeating_posteriors_do_not_contaminate_evsi(self):
        value = fixture()
        value["prior"] = {"temporary_cost": ".3", "persistent_cost": ".7"}
        with localcontext() as context:
            context.prec = 2; context.traps[Inexact] = True
            result = calculate_information_value(value)
        # P(first)=.3*.8+.7*.2=.38 and P(temporary|first)=12/19.
        # Posterior division repeats, but joint expected payoff is exactly 10.
        self.assertEqual(Decimal(result["sample_information"]["evsi"]), 10)
        signal = result["sample_information"]["signals"]["temporary_explanation"]
        self.assertEqual(Decimal(signal["probability"]), Decimal(".38"))
        self.assertTrue(signal["posterior"]["temporary_cost"].startswith("0.63157894736842105263"))

    def test_strictly_unreachable_signal_and_single_action(self):
        value = fixture()
        value["actions"] = ["defer"]; value["payoffs"].pop("continue_review")
        value["likelihoods"]["impossible"] = {"temporary_cost": 0, "persistent_cost": 0}
        result = calculate_information_value(value)
        self.assertEqual(result["sample_information"]["evsi"], "0")
        self.assertEqual(result["perfect_information"]["evpi"], "0")
        self.assertIsNone(result["sample_information"]["signals"]["impossible"]["posterior"])

    def test_exact_fraction_oracle_for_multiple_actions_and_states(self):
        # Cross-check Decimal arithmetic using rational enumeration of possible
        # policies (choose one action for each signal), not posterior rounding.
        from fractions import Fraction
        from itertools import product
        from random import Random
        random = Random(317)
        for case in range(30):
            value = fixture(); value["states"] = ["a", "b", "c"]
            value["actions"] = ["x", "y", "z"]
            p = random.randrange(11); q = random.randrange(11 - p)
            value["prior"] = dict(zip(value["states"], map(lambda n: str(Decimal(n) / 10), [p, q, 10-p-q])))
            value["payoffs"] = {a: {s: random.randrange(-100, 101) for s in value["states"]} for a in value["actions"]}
            first = {s: str(Decimal(random.randrange(11)) / 10) for s in value["states"]}
            value["likelihoods"] = {"first": first, "second": {s: str(1-Decimal(p)) for s, p in first.items()}}
            prior = {s: Fraction(p) for s, p in value["prior"].items()}
            baseline = max(sum(prior[s] * value["payoffs"][a][s] for s in prior) for a in value["actions"])
            policies = product(value["actions"], repeat=2)
            sample = max(sum(prior[s] * Fraction(value["likelihoods"][signal][s]) * value["payoffs"][a][s]
                             for signal, a in zip(["first", "second"], policy) for s in prior)
                         for policy in policies)
            result = calculate_information_value(value)
            with self.subTest(case=case):
                self.assertEqual(Fraction(result["sample_information"]["evsi"]), sample-baseline)

    def test_invalid_models_are_rejected(self):
        changes = [
            lambda v: v["prior"].update(temporary_cost=".6"),
            lambda v: v["prior"].update(temporary_cost="-1", persistent_cost="2"),
            lambda v: v["prior"].pop("persistent_cost"),
            lambda v: v["prior"].update(typo=0),
            lambda v: v["payoffs"].pop("defer"),
            lambda v: v["payoffs"]["defer"].pop("persistent_cost"),
            lambda v: v["likelihoods"]["temporary_explanation"].update(temporary_cost=".7"),
            lambda v: v.update(likelihoods={}),
            lambda v: v["likelihoods"]["temporary_explanation"].pop("persistent_cost"),
            lambda v: v.update(question_cost=-1),
            lambda v: v.update(unit=""),
            lambda v: v.update(states=["temporary_cost", "temporary_cost"]),
            lambda v: v.update(actions=[]),
            lambda v: v.update(synthetic=False),
            lambda v: v["provenance"].pop("prior"),
            lambda v: v["provenance"]["prior"].update(kind="verified"),
            lambda v: v.update(likelihooods={}),
        ]
        for change in changes:
            value = fixture(); change(value)
            with self.subTest(change=changes.index(change)), self.assertRaises(ValueError):
                calculate_information_value(value)

    def test_nonfinite_boolean_and_excessive_numbers_are_rejected(self):
        for number in ("NaN", "sNaN", "Infinity", "-Infinity", True, "1e10001", None, []):
            value = fixture(); value["payoffs"]["continue_review"]["temporary_cost"] = number
            with self.subTest(number=number), self.assertRaises(ValueError):
                calculate_information_value(value)

    def test_probability_sum_is_exact_without_tolerance(self):
        value = fixture(); value["prior"]["temporary_cost"] = ".50000000000000000000000000000000001"
        with self.assertRaises(ValueError): calculate_information_value(value)

    def test_user_assumptions_remain_distinct_from_evidence(self):
        value = fixture(); value["synthetic"] = False
        for source in value["provenance"].values():
            source.update(kind="user_assumption", reference="Explicit user-supplied model", rationale="Unvalidated modeling assumption")
        result = calculate_information_value(value)
        self.assertEqual(result["provenance"]["likelihoods"]["kind"], "user_assumption")
        self.assertFalse(result["synthetic"])


if __name__ == "__main__":
    unittest.main()
