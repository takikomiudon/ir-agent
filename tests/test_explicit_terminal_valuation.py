"""Explicit n+1 FCFF DCF contract and legacy compatibility; synthetic values."""
from copy import deepcopy
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
import json
import unittest

from ir_agent.valuation import calculate_valuation


NEW_DETAIL_KEYS = {"terminal_fcff_jpy", "forecast_periods", "terminal_value_jpy",
                   "present_value_of_terminal_value_jpy", "present_value_of_forecast_fcf_jpy"}


def explicit_scenario():
    return {"name": "synthetic", "probability": "1", "method": "dcf_explicit_terminal",
            "inputs": {"fcf_jpy": ["-110", "121"], "terminal_fcff_jpy": "200",
                       "discount_rate": ".1", "terminal_growth_rate": ".02",
                       "cash_jpy": "0", "debt_jpy": "0", "shares_outstanding": "10"}}


def value(scenario, *, current_price="100", include_unrounded=False):
    return calculate_valuation({"scenarios": [scenario]}, current_price, include_unrounded=include_unrounded)


class ExplicitTerminalValuationTests(unittest.TestCase):
    def test_explicit_year_three_numerator_is_used_once_at_year_two(self):
        result = value(explicit_scenario(), include_unrounded=True)
        row = result["scenarios"][0]
        self.assertEqual(row["terminal_fcff_jpy"], "200")
        self.assertEqual(row["forecast_periods"], 2)
        self.assertEqual(row["present_value_of_forecast_fcf_jpy"], "0.00")
        self.assertEqual(row["terminal_value_jpy"], "2500.00")
        self.assertEqual(row["present_value_of_terminal_value_jpy"], "2066.12")
        self.assertEqual(row["enterprise_value_jpy"], "2066.12")
        self.assertEqual(row["fair_value_jpy"], "206.61")
        self.assertTrue(result["unrounded"]["expected_value_jpy"].startswith("206.61157024793388429752"))
        self.assertNotEqual(row["fair_value_jpy"], "210.74")  # Reapplying (1+g).
        self.assertNotEqual(row["fair_value_jpy"], "187.83")  # Discounting n+1 periods.

    def test_legacy_dcf_keeps_ignored_terminal_fields_and_output_shape(self):
        legacy = explicit_scenario()
        legacy["method"] = "dcf"
        del legacy["inputs"]["terminal_fcff_jpy"]
        baseline = value(legacy, include_unrounded=True)
        self.assertEqual(baseline["expected_value_jpy"], "127.50")
        self.assertEqual(set(baseline["scenarios"][0]),
                         {"name", "probability", "method", "fair_value_jpy", "upside_pct",
                          "enterprise_value_jpy", "equity_value_jpy"})
        for previously_ignored in ("200", "9999999", None, True, "NaN", [], {}):
            changed = deepcopy(legacy)
            changed["inputs"]["terminal_fcff_jpy"] = previously_ignored
            with self.subTest(previously_ignored=previously_ignored):
                self.assertEqual(value(changed, include_unrounded=True), baseline)
        self.assertNotEqual(value(explicit_scenario())["expected_value_jpy"], baseline["expected_value_jpy"])

    def test_explicit_legacy_numerator_gives_equal_arithmetic(self):
        explicit = explicit_scenario()
        explicit["inputs"]["terminal_fcff_jpy"] = "123.42"  # 121*(1+.02).
        legacy = deepcopy(explicit)
        legacy["method"] = "dcf"
        new = value(explicit, include_unrounded=True)
        old = value(legacy, include_unrounded=True)
        self.assertEqual(new["expected_value_jpy"], old["expected_value_jpy"])
        self.assertEqual(Decimal(new["unrounded"]["expected_value_jpy"]), Decimal(old["unrounded"]["expected_value_jpy"]))
        self.assertEqual(new["scenarios"][0]["enterprise_value_jpy"], old["scenarios"][0]["enterprise_value_jpy"])

    def test_explicit_terminal_does_not_depend_on_final_forecast_amount(self):
        scenario = explicit_scenario()
        scenario["inputs"]["fcf_jpy"] = ["0", "0"]
        result = value(scenario)["scenarios"][0]
        self.assertEqual(result["terminal_value_jpy"], "2500.00")
        self.assertEqual(result["fair_value_jpy"], "206.61")
        self.assertEqual(result["forecast_periods"], 2)

    def test_zero_terminal_is_explicit_and_zero_equity_is_valid(self):
        scenario = explicit_scenario()
        scenario["inputs"].update(fcf_jpy=["0"], terminal_fcff_jpy="0")
        row = value(scenario)["scenarios"][0]
        self.assertEqual(row["terminal_fcff_jpy"], "0")
        self.assertEqual(row["terminal_value_jpy"], "0.00")
        self.assertEqual(row["equity_value_jpy"], "0.00")
        self.assertEqual(row["fair_value_jpy"], "0.00")

    def test_negative_forecast_and_terminal_are_retained_with_equity_constraint(self):
        scenario = explicit_scenario()
        scenario["inputs"]["terminal_fcff_jpy"] = "-200"
        with self.assertRaisesRegex(ValueError, "negative equity value"):
            value(scenario)
        scenario["inputs"]["cash_jpy"] = "3000"
        row = value(scenario)["scenarios"][0]
        self.assertEqual(row["terminal_fcff_jpy"], "-200")
        self.assertEqual(row["terminal_value_jpy"], "-2500.00")
        self.assertEqual(row["present_value_of_terminal_value_jpy"], "-2066.12")
        self.assertEqual(row["enterprise_value_jpy"], "-2066.12")
        self.assertEqual(row["equity_value_jpy"], "933.88")
        self.assertEqual(row["fair_value_jpy"], "93.39")

    def test_zero_equity_boundary_does_not_clamp_negative_values(self):
        scenario = explicit_scenario()
        scenario["inputs"].update(fcf_jpy=["0"], terminal_fcff_jpy="-1100",
                                  terminal_growth_rate="0", cash_jpy="10000")
        self.assertEqual(value(scenario)["expected_value_jpy"], "0.00")
        scenario["inputs"]["debt_jpy"] = ".01"
        with self.assertRaisesRegex(ValueError, "negative equity value"):
            value(scenario)

    def test_exact_seven_fields_are_required_and_unknown_financial_steps_are_rejected(self):
        for missing in explicit_scenario()["inputs"]:
            scenario = explicit_scenario()
            del scenario["inputs"][missing]
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, "exactly the seven"):
                value(scenario)
        for extra in ("terminal_discount_rate", "tax_rate", "reinvestment_rate", "apply_growth", "terminal_fcf_jpy", "approved"):
            scenario = explicit_scenario()
            scenario["inputs"][extra] = ".2"
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, "exactly the seven"):
                value(scenario)

    def test_null_bool_nonfinite_and_invalid_terminal_do_not_fall_back(self):
        for terminal in (None, True, False, "", "NaN", "Infinity", "bad", [], {}, float("nan"), Decimal("-Infinity")):
            scenario = explicit_scenario()
            scenario["inputs"]["terminal_fcff_jpy"] = terminal
            with self.subTest(terminal=terminal), self.assertRaises(ValueError):
                value(scenario)

    def test_nonempty_forecast_array_is_required(self):
        for forecast in ([], "100", None, {}, [None], [True], ["NaN"]):
            scenario = explicit_scenario()
            scenario["inputs"]["fcf_jpy"] = forecast
            with self.subTest(forecast=forecast), self.assertRaises(ValueError):
                value(scenario)

    def test_existing_rate_share_and_equity_bridge_domains_are_inherited(self):
        cases = [("discount_rate", "0"), ("discount_rate", "-.1"),
                 ("terminal_growth_rate", "-1"), ("terminal_growth_rate", ".1"),
                 ("terminal_growth_rate", ".11"), ("cash_jpy", "-1"),
                 ("debt_jpy", "-1"), ("shares_outstanding", "0"), ("shares_outstanding", "-1")]
        for key, number in cases:
            scenario = explicit_scenario()
            scenario["inputs"][key] = number
            with self.subTest(key=key, number=number), self.assertRaises(ValueError):
                value(scenario)
        scenario = explicit_scenario()
        scenario["inputs"]["terminal_growth_rate"] = "-.1"
        self.assertEqual(value(scenario)["scenarios"][0]["terminal_value_jpy"], "1000.00")

    def test_terminal_input_precision_is_retained_in_diagnostic_and_arithmetic(self):
        scenario = explicit_scenario()
        scenario["inputs"]["terminal_fcff_jpy"] = "200.00000000000000000001"
        precise = value(scenario, include_unrounded=True)
        baseline = value(explicit_scenario(), include_unrounded=True)
        self.assertEqual(precise["scenarios"][0]["terminal_fcff_jpy"], "200.00000000000000000001")
        self.assertGreater(Decimal(precise["unrounded"]["expected_value_jpy"]),
                           Decimal(baseline["unrounded"]["expected_value_jpy"]))

    def test_tiny_terminal_enters_precision_without_early_money_quantization(self):
        scenario = explicit_scenario()
        scenario["inputs"].update(fcf_jpy=["0"], terminal_fcff_jpy="1e-120", terminal_growth_rate="0")
        result = value(scenario, include_unrounded=True)
        self.assertEqual(result["scenarios"][0]["terminal_fcff_jpy"], format(Decimal("1e-120"), "f"))
        self.assertEqual(result["expected_value_jpy"], "0.00")
        self.assertGreater(Decimal(result["unrounded"]["expected_value_jpy"]), 0)

    def test_private_context_is_independent_of_ambient_precision_rounding_and_traps(self):
        expected = value(explicit_scenario(), include_unrounded=True)
        with localcontext() as context:
            context.prec = 2
            context.rounding = ROUND_DOWN
            context.Emin, context.Emax = -2, 2
            context.traps[Inexact] = context.traps[Rounded] = True
            context.clear_flags()
            flags = context.flags.copy()
            actual = value(explicit_scenario(), include_unrounded=True)
            self.assertEqual(context.prec, 2)
            self.assertEqual(context.flags, flags)
        self.assertEqual(actual, expected)

    def test_new_method_preserves_input_and_has_no_verification_or_adoption_flag(self):
        scenario = explicit_scenario()
        before = deepcopy(scenario)
        result = value(scenario, include_unrounded=True)
        self.assertEqual(scenario, before)
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        for container in (result, result["scenarios"][0]):
            self.assertFalse({"verified", "inputs_verified", "adoption", "source_verified"} & set(container))

    def test_unweighted_and_weighted_aggregation_reuse_existing_contract(self):
        scenario = explicit_scenario()
        scenario["probability"] = ".5"
        eps = {"name": "eps", "probability": ".5", "method": "eps_multiple",
               "inputs": {"eps_jpy": "10", "pe": "20"}}
        weighted = calculate_valuation({"scenarios": [scenario, eps]}, "100")
        self.assertEqual(weighted["expected_value_jpy"], "203.31")
        for row in (scenario, eps):
            del row["probability"]
        unweighted = calculate_valuation({"aggregation": "unweighted", "scenarios": [scenario, eps]}, "100")
        self.assertIsNone(unweighted["expected_value_jpy"])
        self.assertEqual(unweighted["status"], "scenario_values_only")
        self.assertEqual(unweighted["valuation_range_jpy"], {"min": "200.00", "max": "206.61"})
        self.assertFalse(NEW_DETAIL_KEYS & set(unweighted["scenarios"][1]))

    def test_legacy_eps_and_dividend_outputs_are_unchanged(self):
        eps = {"name": "eps", "probability": "1", "method": "eps_multiple",
               "inputs": {"eps_jpy": "65", "pe": "20", "terminal_fcff_jpy": "ignored"}}
        result = value(eps, current_price="1000")
        self.assertEqual(result, {
            "scenarios": [{"name": "eps", "probability": "1", "method": "eps_multiple",
                           "fair_value_jpy": "1300.00", "upside_pct": "30.00"}],
            "expected_value_jpy": "1300.00", "expected_upside_pct": "30.00", "worst_case_downside_pct": "0.00"})
        ddm = {"name": "dividend", "probability": "1", "method": "dividend_discount",
               "inputs": {"dividends_per_share_jpy": ["10"], "cost_of_equity": ".1",
                          "terminal_cost_of_equity": ".1", "terminal_dividend_per_share_jpy": "11", "terminal_growth_rate": "0"}}
        expected = {"scenarios": [{"name": "dividend", "probability": "1", "method": "dividend_discount",
                    "fair_value_jpy": "109.09", "upside_pct": "9.09",
                    "present_value_of_forecast_dividends_jpy": "9.09", "terminal_value_per_share_jpy": "110.00",
                    "present_value_of_terminal_value_jpy": "100.00"}],
                    "expected_value_jpy": "109.09", "expected_upside_pct": "9.09", "worst_case_downside_pct": "0.00"}
        self.assertEqual(value(ddm), expected)
        self.assertNotIn("terminal_fcff_jpy", expected["scenarios"][0])
        ddm["inputs"]["terminal_fcff_jpy"] = "1"
        with self.assertRaises(ValueError):
            value(ddm)  # DDM's prior exact-five contract remains strict.


if __name__ == "__main__":
    unittest.main()
