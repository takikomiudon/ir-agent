"""Independent numeric examples and invalid-input coverage for the evaluator."""

import copy
import json
import unittest
from decimal import Decimal, localcontext

from ir_agent.valuation import calculate_valuation


def eps_scenario(name="base", probability="1", eps="65", pe="20"):
    return {
        "name": name,
        "probability": probability,
        "method": "eps_multiple",
        "inputs": {"eps_jpy": eps, "pe": pe},
    }


def dcf_scenario():
    # Independent arithmetic: (100 + 100*1.02/(.10-.02))/1.10 = 1,250.
    # Cash less debt is -50, giving 1,200 of equity, or 120 per share.
    return {
        "name": "base",
        "probability": "1",
        "method": "dcf",
        "inputs": {
            "fcf_jpy": ["100"],
            "discount_rate": "0.10",
            "terminal_growth_rate": "0.02",
            "cash_jpy": "50",
            "debt_jpy": "100",
            "shares_outstanding": "10",
        },
    }


class ValuationTests(unittest.TestCase):
    def test_three_scenario_eps_example(self):
        valuation = {"scenarios": [
            eps_scenario("bear", "0.25", "45", "15"),
            eps_scenario("base", "0.5", "65", "20"),
            eps_scenario("bull", "0.25", "80", "23"),
        ]}
        result = calculate_valuation(valuation, "1000")
        self.assertEqual([v["fair_value_jpy"] for v in result["scenarios"]], ["675.00", "1300.00", "1840.00"])
        self.assertEqual([v["upside_pct"] for v in result["scenarios"]], ["-32.50", "30.00", "84.00"])
        self.assertEqual(result["expected_value_jpy"], "1278.75")
        self.assertEqual(result["expected_upside_pct"], "27.88")
        self.assertEqual(result["worst_case_downside_pct"], "32.50")
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_dcf_end_of_year_and_terminal_value(self):
        result = calculate_valuation({"scenarios": [dcf_scenario()]}, 100)
        scenario = result["scenarios"][0]
        self.assertEqual(scenario["enterprise_value_jpy"], "1250.00")
        self.assertEqual(scenario["equity_value_jpy"], "1200.00")
        self.assertEqual(scenario["fair_value_jpy"], "120.00")
        self.assertEqual(result["expected_upside_pct"], "20.00")
        self.assertEqual(result["worst_case_downside_pct"], "0.00")

    def test_dcf_negative_early_fcf_is_allowed(self):
        scenario = dcf_scenario()
        scenario["inputs"].update({
            "fcf_jpy": ["-110", "121"], "terminal_growth_rate": "0",
            "cash_jpy": "0", "debt_jpy": "0",
        })
        # -110/1.1 + (121 + 121/.1)/1.1**2 = -100 + 1,100 = 1,000.
        result = calculate_valuation({"scenarios": [scenario]}, 100)
        self.assertEqual(result["scenarios"][0]["fair_value_jpy"], "100.00")

    def test_mix_of_valuation_methods_uses_same_per_share_jpy_units(self):
        dcf = dcf_scenario()
        dcf["probability"] = ".75"
        result = calculate_valuation({"scenarios": [
            eps_scenario("eps", ".25", "100", "1"), dcf,
        ]}, 100)
        self.assertEqual(result["expected_value_jpy"], "115.00")
        self.assertEqual(result["expected_upside_pct"], "15.00")

    def test_dcf_negative_terminal_growth_rate_is_valid(self):
        scenario = dcf_scenario()
        scenario["inputs"].update({
            "fcf_jpy": ["110"], "terminal_growth_rate": "-.1",
            "cash_jpy": "0", "debt_jpy": "0",
        })
        # (110 + 110*.9/.2)/1.1 = 550 of equity, or 55 per share.
        result = calculate_valuation({"scenarios": [scenario]}, 100)
        self.assertEqual(result["expected_value_jpy"], "55.00")
        self.assertEqual(result["worst_case_downside_pct"], "45.00")

    def test_negative_equity_is_error_and_zero_equity_is_valid(self):
        scenario = dcf_scenario()
        scenario["inputs"]["debt_jpy"] = "1300"
        result = calculate_valuation({"scenarios": [scenario]}, 100)
        self.assertEqual(result["expected_value_jpy"], "0.00")
        self.assertEqual(result["worst_case_downside_pct"], "100.00")
        scenario["inputs"]["debt_jpy"] = "1301"
        with self.assertRaisesRegex(ValueError, "negative equity value"):
            calculate_valuation({"scenarios": [scenario]}, 100)

    def test_rounding_occurs_after_weighting_and_percentage_calculation(self):
        result = calculate_valuation({"scenarios": [
            eps_scenario("first", ".5", ".004", "1"),
            eps_scenario("second", ".5", ".005", "1"),
        ]}, ".01")
        self.assertEqual([v["fair_value_jpy"] for v in result["scenarios"]], ["0.00", "0.01"])
        self.assertEqual(result["expected_value_jpy"], "0.00")
        self.assertEqual(result["expected_upside_pct"], "-55.00")

    def test_zero_weight_is_valid_and_still_part_of_supplied_worst_case(self):
        result = calculate_valuation({"scenarios": [
            eps_scenario("stress", 0, 10, 1), eps_scenario("base", 1, 100, 1),
        ]}, 100)
        self.assertEqual(result["expected_value_jpy"], "100.00")
        self.assertEqual(result["worst_case_downside_pct"], "90.00")

    def test_exact_probability_check_rejects_tiny_excess(self):
        valuation = {"scenarios": [
            eps_scenario("first", "1"),
            eps_scenario("second", "0." + "0" * 100 + "1"),
        ]}
        with self.assertRaisesRegex(ValueError, "sum exactly"):
            calculate_valuation(valuation, 100)

    def test_accepts_float_inputs_and_ignores_caller_decimal_context(self):
        valuation = {"scenarios": [eps_scenario(probability=1.0, eps=65.1, pe=20.0)]}
        with localcontext() as context:
            context.prec = 2
            result = calculate_valuation(valuation, 1000.0)
        self.assertEqual(result["expected_value_jpy"], "1302.00")
        self.assertEqual(result["expected_upside_pct"], "30.20")

    def test_valuation_does_not_mutate_input(self):
        valuation = {"scenarios": [dcf_scenario()]}
        before = copy.deepcopy(valuation)
        calculate_valuation(valuation, 100)
        self.assertEqual(valuation, before)

    def test_invalid_current_price(self):
        for value in (0, -1, True, False, None, "", "bad", "NaN", "Infinity", float("nan"), float("inf"), Decimal("-Infinity")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate_valuation({"scenarios": [eps_scenario()]}, value)

    def test_invalid_scenario_structure(self):
        cases = [
            None, [], {}, {"scenarios": []}, {"scenarios": {}}, {"scenarios": [None]},
            {"scenarios": [eps_scenario(name="")]},
            {"scenarios": [eps_scenario(name=True)]},
            {"scenarios": [eps_scenario("same", ".5"), eps_scenario(" same ", ".5")]},
            {"scenarios": [dict(eps_scenario(), method="unknown")]},
            {"scenarios": [dict(eps_scenario(), inputs=[])]},
            {"scenarios": [dict(eps_scenario(), inputs={"eps_jpy": "1"})]},
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                calculate_valuation(case, 100)

    def test_invalid_probability_and_eps_multiple_inputs(self):
        for probability in ("-.1", "1.1", ".99", "1.01", True, "NaN", "Infinity", None):
            with self.subTest(probability=probability), self.assertRaises(ValueError):
                calculate_valuation({"scenarios": [eps_scenario(probability=probability)]}, 100)
        for key in ("eps_jpy", "pe"):
            for value in ("0", "-1", True, "NaN", "Infinity", None, "bad"):
                scenario = eps_scenario()
                scenario["inputs"][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    calculate_valuation({"scenarios": [scenario]}, 100)

    def test_invalid_dcf_inputs(self):
        cases = [
            ("discount_rate", "0"), ("discount_rate", "-.1"),
            ("terminal_growth_rate", ".1"), ("terminal_growth_rate", ".11"),
            ("terminal_growth_rate", "-1"), ("terminal_growth_rate", "-1.1"),
            ("shares_outstanding", "0"), ("shares_outstanding", "-1"),
            ("cash_jpy", "-1"), ("debt_jpy", "-1"),
            ("fcf_jpy", []), ("fcf_jpy", "100"),
            ("fcf_jpy", [True]), ("fcf_jpy", ["NaN"]),
        ]
        for key, value in cases:
            scenario = dcf_scenario()
            scenario["inputs"][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                calculate_valuation({"scenarios": [scenario]}, 100)
        for key in ("discount_rate", "terminal_growth_rate", "cash_jpy", "debt_jpy", "shares_outstanding"):
            for value in (True, "NaN", "Infinity", None):
                scenario = dcf_scenario()
                scenario["inputs"][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    calculate_valuation({"scenarios": [scenario]}, 100)
            scenario = dcf_scenario()
            del scenario["inputs"][key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                calculate_valuation({"scenarios": [scenario]}, 100)


if __name__ == "__main__":
    unittest.main()
