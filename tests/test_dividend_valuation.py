"""Independent rational DDM checks; all payout/risk inputs are fictional."""

from copy import deepcopy
from decimal import Inexact, ROUND_DOWN, Rounded, localcontext
from fractions import Fraction
import json
from pathlib import Path
import unittest

from ir_agent.valuation import calculate_valuation


def ddm(**updates):
    inputs = {
        "dividends_per_share_jpy": ["10", "12", "14"], "cost_of_equity": "0.12",
        "terminal_cost_of_equity": "0.08", "terminal_dividend_per_share_jpy": "15",
        "terminal_growth_rate": "0.02",
    }
    inputs.update(updates)
    return {"name": "base", "probability": "1", "method": "dividend_discount", "inputs": inputs}


def rational_price(inputs):
    """An independent Fraction oracle, with separate forecast and stable rates."""
    discount = 1 + Fraction(inputs["cost_of_equity"])
    dividends = inputs["dividends_per_share_jpy"]
    pv = sum((Fraction(value) / discount**year for year, value in enumerate(dividends, 1)), Fraction(0))
    terminal = Fraction(inputs["terminal_dividend_per_share_jpy"]) / (
        Fraction(inputs["terminal_cost_of_equity"]) - Fraction(inputs["terminal_growth_rate"])
    )
    return pv + terminal / discount**len(dividends)


def positive_money(value):
    """Round a nonnegative Fraction HALF_UP using integer arithmetic only."""
    scaled = value * 100
    cents = (2 * scaled.numerator + scaled.denominator) // (2 * scaled.denominator)
    return f"{cents // 100}.{cents % 100:02d}"


class DividendValuationTests(unittest.TestCase):
    def test_multi_year_ddm_matches_independent_fraction_with_two_equity_costs(self):
        scenario = ddm()
        result = calculate_valuation({"scenarios": [scenario]}, "100", include_unrounded=True)
        expected = rational_price(scenario["inputs"])
        self.assertEqual(result["expected_value_jpy"], positive_money(expected))
        exact = Fraction(result["unrounded"]["scenarios"][0]["fair_value_jpy"])
        self.assertLess(abs(exact-expected), Fraction(1, 10**70))
        # Terminal value is 15/(.08-.02)=250 at year n, not divided by .12-.02.
        self.assertEqual(result["scenarios"][0]["terminal_value_per_share_jpy"], "250.00")
        self.assertNotIn("enterprise_value_jpy", result["scenarios"][0])

    def test_next_period_dividend_is_explicit_and_not_derived_from_last_dividend(self):
        scenario = ddm(dividends_per_share_jpy=["10"], cost_of_equity="0.1",
                       terminal_cost_of_equity="0.1", terminal_dividend_per_share_jpy="50", terminal_growth_rate="0")
        # (10 + 50/.1)/1.1 = 5100/11; inferring next DPS=10 would give 100.
        result = calculate_valuation({"scenarios": [scenario]}, "100")
        self.assertEqual(result["expected_value_jpy"], "463.64")
        self.assertEqual(result["scenarios"][0]["terminal_value_per_share_jpy"], "500.00")
        del scenario["inputs"]["terminal_dividend_per_share_jpy"]
        with self.assertRaises(ValueError):
            calculate_valuation({"scenarios": [scenario]}, "100")

    def test_zero_payouts_are_zero_model_value_but_current_price_must_be_positive(self):
        scenario = ddm(dividends_per_share_jpy=["0", "0"], terminal_dividend_per_share_jpy="0")
        result = calculate_valuation({"scenarios": [scenario]}, "100", include_unrounded=True)
        self.assertEqual(result["expected_value_jpy"], "0.00")
        self.assertEqual(result["expected_upside_pct"], "-100.00")
        self.assertEqual(result["worst_case_downside_pct"], "100.00")
        self.assertEqual(Fraction(result["unrounded"]["expected_value_jpy"]), 0)
        with self.assertRaises(ValueError):
            calculate_valuation({"scenarios": [scenario]}, "0")

    def test_negative_growth_and_zero_forecast_dividend_are_valid(self):
        for growth in ("-0.1", "-0.999"):
            scenario = ddm(dividends_per_share_jpy=["0", "10"], terminal_growth_rate=growth)
            result = calculate_valuation({"scenarios": [scenario]}, "100")
            self.assertEqual(result["expected_value_jpy"], positive_money(rational_price(scenario["inputs"])))

    def test_growth_bound_is_terminal_cost_not_forecast_cost(self):
        scenario = ddm(cost_of_equity="0.03", terminal_cost_of_equity="0.10", terminal_growth_rate="0.05")
        result = calculate_valuation({"scenarios": [scenario]}, "100")
        self.assertEqual(result["expected_value_jpy"], positive_money(rational_price(scenario["inputs"])))
        for key, value in (("cost_of_equity", "0"), ("terminal_cost_of_equity", "0"),
                           ("cost_of_equity", "-0.1"), ("terminal_cost_of_equity", "-0.1"),
                           ("terminal_growth_rate", "0.10"), ("terminal_growth_rate", "0.11"),
                           ("terminal_growth_rate", "-1"), ("terminal_growth_rate", "-1.1")):
            bad = deepcopy(scenario)
            bad["inputs"][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                calculate_valuation({"scenarios": [bad]}, "100")

    def test_exact_input_keys_reject_firm_valuation_data_and_missing_equity_costs(self):
        for key, value in (("fcf_jpy", ["1"]), ("cash_jpy", "1"), ("debt_jpy", "1"),
                           ("shares_outstanding", "1"), ("discount_rate", "0.1"), ("wacc", "0.1"),
                           ("eps_jpy", "10"), ("cost_of_equity_typo", "0.1")):
            scenario = ddm()
            scenario["inputs"][key] = value
            with self.subTest(extra=key), self.assertRaisesRegex(ValueError, "exactly"):
                calculate_valuation({"scenarios": [scenario]}, "100")
        for key in ddm()["inputs"]:
            scenario = ddm()
            del scenario["inputs"][key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                calculate_valuation({"scenarios": [scenario]}, "100")

    def test_bad_payouts_empty_forecast_and_nonfinite_numbers_are_rejected(self):
        cases = [("dividends_per_share_jpy", []), ("dividends_per_share_jpy", "10"),
                 ("dividends_per_share_jpy", ["-1"]), ("dividends_per_share_jpy", [True]),
                 ("dividends_per_share_jpy", ["NaN"]), ("terminal_dividend_per_share_jpy", "-1")]
        cases += [(key, value) for key in ("cost_of_equity", "terminal_cost_of_equity", "terminal_growth_rate", "terminal_dividend_per_share_jpy")
                  for value in (None, True, "NaN", "Infinity")]
        for key, value in cases:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                calculate_valuation({"scenarios": [ddm(**{key: value})]}, "100")

    def test_caller_decimal_context_and_input_are_unchanged(self):
        valuation = {"scenarios": [ddm()]}
        original = deepcopy(valuation)
        expected = calculate_valuation(valuation, "100", include_unrounded=True)
        with localcontext() as context:
            context.prec = 2
            context.rounding = ROUND_DOWN
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            context.Emax = 9
            context.Emin = -9
            actual = calculate_valuation(valuation, "100", include_unrounded=True)
            self.assertEqual(context.prec, 2)
            self.assertEqual(context.rounding, ROUND_DOWN)
            self.assertFalse(context.flags[Inexact])
            self.assertFalse(context.flags[Rounded])
        self.assertEqual(actual, expected)
        self.assertEqual(valuation, original)

    def test_ddm_mixes_with_existing_eps_and_fcff_without_changing_old_results(self):
        eps = {"name": "eps", "probability": "0.25", "method": "eps_multiple", "inputs": {"eps_jpy": "10", "pe": "10"}}
        fcff = {"name": "fcff", "probability": "0.25", "method": "dcf", "inputs": {
            "fcf_jpy": ["100"], "discount_rate": ".1", "terminal_growth_rate": ".02",
            "cash_jpy": "50", "debt_jpy": "100", "shares_outstanding": "10",
        }}
        payout = ddm(dividends_per_share_jpy=["10"], cost_of_equity=".1", terminal_cost_of_equity=".1",
                     terminal_dividend_per_share_jpy="10", terminal_growth_rate="0")
        payout.update(name="ddm", probability="0.5")
        result = calculate_valuation({"scenarios": [eps, fcff, payout]}, "100")
        self.assertEqual([x["fair_value_jpy"] for x in result["scenarios"]], ["100.00", "120.00", "100.00"])
        self.assertEqual(result["expected_value_jpy"], "105.00")
        self.assertEqual(result["scenarios"][1]["enterprise_value_jpy"], "1250.00")
        self.assertEqual(result["scenarios"][1]["equity_value_jpy"], "1200.00")

    def test_synthetic_example_has_explicit_risk_and_payout_assumptions(self):
        path = Path(__file__).parents[1] / "examples/dividend-valuation.json"
        value = json.loads(path.read_text())
        self.assertTrue(value["synthetic"])
        self.assertEqual(value["method_reference"]["pdf_pages"], [14, 15])
        self.assertEqual(calculate_valuation(value, "100")["expected_value_jpy"],
                         positive_money(rational_price(value["scenarios"][0]["inputs"])))


if __name__ == "__main__":
    unittest.main()
