"""Conditional scenario prices never imply configured scenario probabilities."""

from copy import deepcopy
from decimal import Inexact, ROUND_DOWN, Rounded, localcontext
from fractions import Fraction
import json
from pathlib import Path
import unittest

from ir_agent.valuation import _prepare, calculate_valuation


def eps(name="base", value="100", **fields):
    return {"name": name, "method": "eps_multiple", "inputs": {"eps_jpy": value, "pe": "1"}, **fields}


def unweighted(*scenarios):
    return {"aggregation": "unweighted", "scenarios": list(scenarios)}


class UnweightedValuationTests(unittest.TestCase):
    def test_bear_base_bull_prices_and_range_without_expected_value_or_equal_weights(self):
        valuation = unweighted(eps("bear", "75"), eps("base", "100", probability=None), eps("bull", "160"))
        result = calculate_valuation(valuation, "100", include_unrounded=True)
        self.assertEqual(result["aggregation"], "unweighted")
        self.assertEqual(result["status"], "scenario_values_only")
        self.assertEqual([x["fair_value_jpy"] for x in result["scenarios"]], ["75.00", "100.00", "160.00"])
        self.assertEqual([x["upside_pct"] for x in result["scenarios"]], ["-25.00", "0.00", "60.00"])
        self.assertTrue(all(x["probability"] is None for x in result["scenarios"]))
        self.assertEqual(result["valuation_range_jpy"], {"min": "75.00", "max": "160.00"})
        self.assertEqual(result["worst_case_downside_pct"], "25.00")
        self.assertIsNone(result["expected_value_jpy"])
        self.assertIsNone(result["expected_upside_pct"])
        self.assertIsNone(result["unrounded"]["expected_value_jpy"])
        self.assertTrue(all(x.probability is None for x in _prepare(valuation)))

    def test_single_scenario_does_not_implicitly_become_probability_one(self):
        result = calculate_valuation(unweighted(eps(value="120")), "100")
        self.assertEqual(result["valuation_range_jpy"], {"min": "120.00", "max": "120.00"})
        self.assertEqual(result["worst_case_downside_pct"], "0.00")
        self.assertIsNone(result["expected_value_jpy"])
        self.assertIsNone(result["scenarios"][0]["probability"])

    def test_all_three_methods_share_per_share_jpy_range_and_keep_zero_value(self):
        fcff = {"name": "fcff", "method": "dcf", "inputs": {
            "fcf_jpy": ["100"], "discount_rate": ".1", "terminal_growth_rate": ".02",
            "cash_jpy": "50", "debt_jpy": "100", "shares_outstanding": "10",
        }}
        ddm = {"name": "ddm", "method": "dividend_discount", "inputs": {
            "dividends_per_share_jpy": ["0", "0"], "cost_of_equity": ".12", "terminal_cost_of_equity": ".08",
            "terminal_dividend_per_share_jpy": "0", "terminal_growth_rate": ".02",
        }}
        result = calculate_valuation(unweighted(eps(), fcff, ddm), "100")
        self.assertEqual([x["fair_value_jpy"] for x in result["scenarios"]], ["100.00", "120.00", "0.00"])
        self.assertEqual(result["valuation_range_jpy"], {"min": "0.00", "max": "120.00"})
        self.assertEqual(result["worst_case_downside_pct"], "100.00")
        self.assertEqual(result["scenarios"][1]["enterprise_value_jpy"], "1250.00")

    def test_supplied_probabilities_cannot_mix_with_unset_probabilities(self):
        for probability in (0, 1, ".5", True, False, "NaN", "Infinity", "", {}, []):
            with self.subTest(probability=probability), self.assertRaisesRegex(ValueError, "absent or null"):
                calculate_valuation(unweighted(eps("a"), eps("b", probability=probability)), "100")
        with self.assertRaises(ValueError):
            calculate_valuation(unweighted(eps(probability="1")), "100")

    def test_default_and_explicit_weighted_preserve_the_old_contract_and_output(self):
        old = {"scenarios": [eps("a", "75", probability=".25"), eps("b", "175", probability=".75")]}
        result = calculate_valuation(old, "100", include_unrounded=True)
        self.assertEqual(result["expected_value_jpy"], "150.00")
        self.assertEqual(result["expected_upside_pct"], "50.00")
        self.assertNotIn("aggregation", result)
        self.assertNotIn("status", result)
        self.assertNotIn("valuation_range_jpy", result)
        self.assertNotIn("valuation_range_jpy", result["unrounded"])
        self.assertEqual(result, calculate_valuation({**old, "aggregation": "weighted"}, "100", include_unrounded=True))
        for missing in (eps(), eps(probability=None)):
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                calculate_valuation({"scenarios": [missing]}, "100")
        with self.assertRaisesRegex(ValueError, "sum exactly"):
            calculate_valuation({"scenarios": [eps(probability=".99")]}, "100")

    def test_invalid_aggregation_and_empty_scenarios_raise_normal_value_errors(self):
        for value in (None, [], {}, "", "probability_weighted", True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate_valuation({"aggregation": value, "scenarios": [eps()]}, "100")
        for scenarios in ([], {}, None):
            with self.subTest(scenarios=scenarios), self.assertRaises(ValueError):
                calculate_valuation({"aggregation": "unweighted", "scenarios": scenarios}, "100")

    def test_range_unrounded_values_are_not_rounded_before_boundary_comparisons(self):
        result = calculate_valuation(unweighted(eps("lo", ".004"), eps("hi", ".005")), ".01", include_unrounded=True)
        self.assertEqual(result["valuation_range_jpy"], {"min": "0.00", "max": "0.01"})
        self.assertEqual(result["unrounded"]["valuation_range_jpy"], {"min": "0.004", "max": "0.005"})
        self.assertEqual(result["worst_case_downside_pct"], "60.00")
        self.assertIsNone(result["unrounded"]["expected_value_jpy"])

    def test_unweighted_ddm_exact_values_and_caller_decimal_state_are_preserved(self):
        scenario = {"name": "conditional", "method": "dividend_discount", "inputs": {
            "dividends_per_share_jpy": ["10"], "cost_of_equity": ".12", "terminal_cost_of_equity": ".08",
            "terminal_dividend_per_share_jpy": "15", "terminal_growth_rate": ".02",
        }}
        valuation = unweighted(scenario)
        original = deepcopy(valuation)
        with localcontext() as context:
            context.prec = 2
            context.rounding = ROUND_DOWN
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            result = calculate_valuation(valuation, "100", include_unrounded=True)
            self.assertEqual(context.prec, 2)
            self.assertFalse(context.flags[Inexact])
            self.assertFalse(context.flags[Rounded])
        # (10 + 15/(.08-.02))/(1+.12) = 1625/7.
        self.assertLess(abs(Fraction(result["unrounded"]["scenarios"][0]["fair_value_jpy"])-Fraction(1625, 7)), Fraction(1, 10**70))
        self.assertEqual(valuation, original)

    def test_example_marks_synthetic_values_and_never_calculates_average(self):
        path = Path(__file__).parents[1] / "examples/unweighted-valuation.json"
        value = json.loads(path.read_text())
        result = calculate_valuation(value, "1000")
        self.assertTrue(value["synthetic"])
        self.assertIsNone(result["expected_value_jpy"])
        self.assertEqual(result["valuation_range_jpy"], {"min": "675.00", "max": "1840.00"})


if __name__ == "__main__":
    unittest.main()
