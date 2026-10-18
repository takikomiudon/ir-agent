"""Separate equity claims, explicit terminal timing and unchanged old contracts."""
from copy import deepcopy
from decimal import Decimal, Inexact, ROUND_DOWN, ROUND_HALF_UP, Rounded, localcontext
from fractions import Fraction
import json
from pathlib import Path
import unittest

from ir_agent.valuation import _prepare, calculate_valuation


ROOT = Path(__file__).resolve().parents[1]
METHOD = "dcf_explicit_terminal_equity_bridge"
BRIDGE_KEYS = {"cash_jpy", "non_operating_assets_jpy", "debt_jpy",
               "minority_interests_jpy", "equity_bridge_formula"}
EXPLICIT_KEYS = {"terminal_fcff_jpy", "forecast_periods", "terminal_value_jpy",
                 "present_value_of_terminal_value_jpy", "present_value_of_forecast_fcf_jpy"}
FORMULA = ("enterprise_value_jpy + cash_jpy + non_operating_assets_jpy"
           " - debt_jpy - minority_interests_jpy")


def scenario():
    return {"name": "synthetic", "probability": "1", "method": METHOD,
            "inputs": {"fcf_jpy": ["10000000"], "terminal_fcff_jpy": "80000000",
                       "discount_rate": ".10", "terminal_growth_rate": ".02",
                       "cash_jpy": "0", "debt_jpy": "0", "shares_outstanding": "10000000",
                       "non_operating_assets_jpy": "20000000", "minority_interests_jpy": "10000000"}}


def value(row, *, price="100", unrounded=False):
    return calculate_valuation({"scenarios": [row]}, price, include_unrounded=unrounded)


def old_explicit(row):
    old = deepcopy(row)
    old["method"] = "dcf_explicit_terminal"
    del old["inputs"]["non_operating_assets_jpy"]
    del old["inputs"]["minority_interests_jpy"]
    return old


def independent(inputs):
    """Author equation evaluated as exact rationals, independently of Decimal."""
    r, g = Fraction(inputs["discount_rate"]), Fraction(inputs["terminal_growth_rate"])
    n = len(inputs["fcf_jpy"])
    operating = sum((Fraction(cf) / (1 + r) ** t
                     for t, cf in enumerate(inputs["fcf_jpy"], 1)), Fraction(0))
    operating += Fraction(inputs["terminal_fcff_jpy"]) / (r - g) / (1 + r) ** n
    equity = (operating + Fraction(inputs["cash_jpy"]) + Fraction(inputs["non_operating_assets_jpy"])
              - Fraction(inputs["debt_jpy"]) - Fraction(inputs["minority_interests_jpy"]))
    return operating, equity, equity / Fraction(inputs["shares_outstanding"])


def money(number):
    with localcontext() as context:
        context.prec = 100
        return format((Decimal(number.numerator) / Decimal(number.denominator)).quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP), "f")


class EquityBridgeValuationTests(unittest.TestCase):
    def test_explicit_bridge_changes_equity_without_changing_operating_value(self):
        new = value(scenario(), unrounded=True)
        old = value(old_explicit(scenario()), unrounded=True)
        row = new["scenarios"][0]
        self.assertEqual(row["enterprise_value_jpy"], old["scenarios"][0]["enterprise_value_jpy"])
        self.assertEqual(row["enterprise_value_jpy"], "918181818.18")
        self.assertEqual(row["equity_value_jpy"], "928181818.18")
        self.assertEqual(row["fair_value_jpy"], "92.82")
        self.assertEqual(row["non_operating_assets_jpy"], "20000000.00")
        self.assertEqual(row["minority_interests_jpy"], "10000000.00")
        self.assertEqual(row["cash_jpy"], "0.00")
        self.assertEqual(row["debt_jpy"], "0.00")
        self.assertEqual(row["equity_bridge_formula"], FORMULA)
        self.assertTrue(EXPLICIT_KEYS <= set(row))
        self.assertFalse(BRIDGE_KEYS & set(old["scenarios"][0]))
        with localcontext() as context:
            context.prec = 150
            difference = Decimal(new["unrounded"]["expected_value_jpy"]) - Decimal(old["unrounded"]["expected_value_jpy"])
            self.assertEqual(difference, 1)

    def test_signed_cashflows_and_four_distinct_adjustments_match_independent_equation(self):
        row = scenario()
        row["inputs"].update(fcf_jpy=["-110", "121", "17.125"], terminal_fcff_jpy="200.375",
                             cash_jpy="13.25", non_operating_assets_jpy="27.625",
                             debt_jpy="4.125", minority_interests_jpy="8.75", shares_outstanding="10")
        operating, equity, fair = independent(row["inputs"])
        result = value(row)["scenarios"][0]
        self.assertEqual(result["enterprise_value_jpy"], money(operating))
        self.assertEqual(result["equity_value_jpy"], money(equity))
        self.assertEqual(result["fair_value_jpy"], money(fair))
        self.assertEqual(result["cash_jpy"], "13.25")
        self.assertEqual(result["non_operating_assets_jpy"], "27.63")
        self.assertEqual(result["debt_jpy"], "4.13")
        self.assertEqual(result["minority_interests_jpy"], "8.75")

    def test_toyota_displayed_inputs_and_author_result_remain_distinct(self):
        request = json.loads((ROOT / "examples/valuation-equity-bridge.toyota-author-display.json").read_text())
        result = calculate_valuation(request, "3060", include_unrounded=True)
        row = result["scenarios"][0]
        self.assertEqual(row["forecast_periods"], 3)
        self.assertEqual(row["terminal_fcff_jpy"], "713000000000")
        self.assertEqual(row["terminal_value_jpy"], "19860724233983.29")
        self.assertEqual(row["fair_value_jpy"], "3944.09")
        self.assertEqual(request["research_context"]["author_displayed_results"]["per_share_jpy"], "3943")
        self.assertIsNone(result["expected_value_jpy"])
        self.assertIsNone(row["probability"])
        self.assertTrue(result["unrounded"]["scenarios"][0]["fair_value_jpy"].startswith("3944.089660079922747854"))
        _, _, fair = independent(request["scenarios"][0]["inputs"])
        self.assertEqual(row["fair_value_jpy"], money(fair))
        self.assertFalse(request["research_context"]["model_adopted"])
        self.assertEqual(request["research_context"]["historical_comparison_price"]["author_date_label"], "February 2009")

    def test_synthetic_example_is_unweighted_and_net_adjustment_is_one_yen_per_share(self):
        request = json.loads((ROOT / "examples/valuation-equity-bridge.synthetic.json").read_text())
        result = calculate_valuation(request, "100")
        self.assertEqual(request["research_context"]["kind"], "synthetic_example")
        self.assertEqual(result["scenarios"][0]["fair_value_jpy"], "92.82")
        self.assertEqual(result["aggregation"], "unweighted")
        self.assertIsNone(result["expected_value_jpy"])
        self.assertIsNone(result["expected_upside_pct"])

    def test_zero_adjustments_equal_old_explicit_with_no_old_output_additions(self):
        row = scenario()
        row["inputs"].update(non_operating_assets_jpy="0", minority_interests_jpy="0")
        new, old = value(row), value(old_explicit(row))
        new_row, old_row = new["scenarios"][0], old["scenarios"][0]
        self.assertEqual(new_row["fair_value_jpy"], old_row["fair_value_jpy"])
        self.assertEqual(new_row["equity_value_jpy"], old_row["equity_value_jpy"])
        self.assertEqual(set(new_row) - set(old_row), BRIDGE_KEYS)
        for key in EXPLICIT_KEYS:
            self.assertEqual(new_row[key], old_row[key])

    def test_legacy_dcf_keeps_ignoring_both_new_fields_and_terminal(self):
        old = old_explicit(scenario())
        old["method"] = "dcf"
        del old["inputs"]["terminal_fcff_jpy"]
        expected = value(old, unrounded=True)
        for ignored in (None, True, "NaN", "Infinity", "-999", [], {}):
            changed = deepcopy(old)
            for key in ("non_operating_assets_jpy", "minority_interests_jpy", "terminal_fcff_jpy"):
                changed["inputs"][key] = ignored
            with self.subTest(ignored=ignored):
                self.assertEqual(value(changed, unrounded=True), expected)
        self.assertFalse((BRIDGE_KEYS | EXPLICIT_KEYS) & set(expected["scenarios"][0]))

    def test_old_explicit_stays_strict_seven_for_new_fields_including_zero(self):
        old = old_explicit(scenario())
        for keys in (("non_operating_assets_jpy",), ("minority_interests_jpy",),
                     ("non_operating_assets_jpy", "minority_interests_jpy")):
            changed = deepcopy(old)
            changed["inputs"].update({key: "0" for key in keys})
            with self.subTest(keys=keys), self.assertRaisesRegex(ValueError, "exactly the seven"):
                value(changed)

    def test_exact_nine_inputs_reject_missing_and_unknown_financial_steps(self):
        for missing in scenario()["inputs"]:
            row = scenario()
            del row["inputs"][missing]
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, "exactly the nine"):
                value(row)
        for extra in ("nonoperating_assets_jpy", "minority_interest_jpy", "terminal_discount_rate",
                      "tax_rate", "reinvestment_rate", "approved"):
            row = scenario()
            row["inputs"][extra] = "0"
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, "exactly the nine"):
                value(row)

    def test_new_adjustments_reject_null_boolean_nonfinite_negative_or_containers(self):
        invalid = (None, True, False, "", "NaN", "Infinity", "bad", [], {},
                   float("nan"), Decimal("-Infinity"), "-1", "-1e-120")
        for key in ("non_operating_assets_jpy", "minority_interests_jpy"):
            for number in invalid:
                row = scenario()
                row["inputs"][key] = number
                with self.subTest(key=key, number=number), self.assertRaises(ValueError):
                    value(row)

    def test_explicit_zero_equity_is_valid_and_tiny_negative_is_rejected(self):
        row = scenario()
        row["inputs"].update(fcf_jpy=["0"], terminal_fcff_jpy="0", non_operating_assets_jpy="11",
                             minority_interests_jpy="7", cash_jpy="2", debt_jpy="6")
        self.assertEqual(value(row)["scenarios"][0]["fair_value_jpy"], "0.00")
        row["inputs"]["minority_interests_jpy"] = "7.00000000000000001"
        with self.assertRaisesRegex(ValueError, "negative equity value"):
            value(row)

    def test_negative_operating_value_is_preserved_when_explicit_assets_cover_claims(self):
        row = scenario()
        row["inputs"].update(fcf_jpy=["-110"], terminal_fcff_jpy="-110", discount_rate=".1",
                             terminal_growth_rate="0", cash_jpy="0", debt_jpy="10",
                             non_operating_assets_jpy="1300", minority_interests_jpy="10", shares_outstanding="10")
        result = value(row)["scenarios"][0]
        self.assertEqual(result["enterprise_value_jpy"], "-1100.00")
        self.assertEqual(result["terminal_fcff_jpy"], "-110")
        self.assertEqual(result["equity_value_jpy"], "180.00")
        self.assertEqual(result["fair_value_jpy"], "18.00")

    def test_nonempty_forecast_and_existing_rate_share_cash_debt_domains_apply(self):
        for forecasts in ([], None, "10", {}, [True], [None], ["NaN"]):
            row = scenario()
            row["inputs"]["fcf_jpy"] = forecasts
            with self.subTest(forecasts=forecasts), self.assertRaises(ValueError):
                value(row)
        for key, number in (("discount_rate", "0"), ("terminal_growth_rate", "-1"),
                            ("terminal_growth_rate", ".1"), ("shares_outstanding", "0"),
                            ("cash_jpy", "-1"), ("debt_jpy", "-1"), ("terminal_fcff_jpy", None)):
            row = scenario()
            row["inputs"][key] = number
            with self.subTest(key=key, number=number), self.assertRaises(ValueError):
                value(row)
        for bad_method in ([], {}, None, "not_a_method"):
            row = scenario()
            row["method"] = bad_method
            with self.subTest(method=bad_method), self.assertRaises(ValueError):
                value(row)

    def test_explicit_terminal_is_not_grown_taxed_or_shifted_to_n_plus_one_discount(self):
        row = scenario()
        row["inputs"].update(fcf_jpy=["-110", "121"], terminal_fcff_jpy="200", cash_jpy="0", debt_jpy="0",
                             non_operating_assets_jpy="0", minority_interests_jpy="0", shares_outstanding="10")
        result = value(row)["scenarios"][0]
        self.assertEqual(result["forecast_periods"], 2)
        self.assertEqual(result["terminal_value_jpy"], "2500.00")
        self.assertEqual(result["present_value_of_terminal_value_jpy"], "2066.12")
        self.assertEqual(result["fair_value_jpy"], "206.61")
        row["inputs"]["fcf_jpy"] = ["0", "0"]
        self.assertEqual(value(row)["scenarios"][0]["terminal_value_jpy"], "2500.00")

    def test_tiny_adjustments_are_not_quantized_before_equity_or_share_division(self):
        row = scenario()
        row["inputs"].update(fcf_jpy=["0"], terminal_fcff_jpy="0", non_operating_assets_jpy="1e-120",
                             minority_interests_jpy="0", shares_outstanding="1e-120")
        result = value(row, unrounded=True)
        self.assertEqual(result["scenarios"][0]["non_operating_assets_jpy"], "0.00")
        self.assertEqual(result["scenarios"][0]["equity_value_jpy"], "0.00")
        self.assertEqual(result["scenarios"][0]["fair_value_jpy"], "1.00")
        row["inputs"]["minority_interests_jpy"] = "0.5e-120"
        self.assertEqual(value(row)["scenarios"][0]["fair_value_jpy"], "0.50")

    def test_large_opposing_claims_preserve_small_remaining_value(self):
        row = scenario()
        row["inputs"].update(fcf_jpy=["0"], terminal_fcff_jpy="0", shares_outstanding="1",
                             non_operating_assets_jpy="100000000000000000000000000000000000000000000000000.01",
                             minority_interests_jpy="100000000000000000000000000000000000000000000000000")
        self.assertEqual(value(row)["scenarios"][0]["fair_value_jpy"], "0.01")

    def test_private_decimal_context_and_caller_flags_remain_isolated(self):
        expected = value(scenario(), unrounded=True)
        with localcontext() as context:
            context.prec = 2
            context.rounding = ROUND_DOWN
            context.Emin, context.Emax = -2, 2
            context.traps[Inexact] = context.traps[Rounded] = True
            context.clear_flags()
            flags = context.flags.copy()
            actual = value(scenario(), unrounded=True)
            self.assertEqual(context.prec, 2)
            self.assertEqual(context.flags, flags)
        self.assertEqual(actual, expected)

    def test_prepare_preserves_both_new_canonical_input_values(self):
        row = scenario()
        prepared = _prepare({"scenarios": [row]})[0]
        self.assertEqual(set(prepared.inputs), set(row["inputs"]))
        self.assertEqual(prepared.inputs["non_operating_assets_jpy"], Decimal("20000000"))
        self.assertEqual(prepared.inputs["minority_interests_jpy"], Decimal("10000000"))
        legacy = old_explicit(row)
        legacy["method"] = "dcf"
        legacy["inputs"].update(non_operating_assets_jpy="ignored", minority_interests_jpy=None)
        old_inputs = _prepare({"scenarios": [legacy]})[0].inputs
        self.assertNotIn("non_operating_assets_jpy", old_inputs)
        self.assertNotIn("minority_interests_jpy", old_inputs)

    def test_input_is_unchanged_and_output_adds_no_adoption_or_basis_verification(self):
        row = scenario()
        before = deepcopy(row)
        result = value(row, unrounded=True)
        self.assertEqual(row, before)
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        for container in (result, result["scenarios"][0]):
            self.assertFalse({"verified", "inputs_verified", "model_adopted", "adoption", "source_verified"} & set(container))

    def test_mixed_weighted_and_unweighted_scenarios_keep_existing_aggregation(self):
        row = scenario()
        row["probability"] = ".5"
        eps = {"name": "eps", "probability": ".5", "method": "eps_multiple", "inputs": {"eps_jpy": "10", "pe": "10"}}
        result = calculate_valuation({"scenarios": [row, eps]}, "100")
        self.assertEqual(result["expected_value_jpy"], "96.41")
        self.assertFalse(BRIDGE_KEYS & set(result["scenarios"][1]))
        for item in (row, eps):
            del item["probability"]
        result = calculate_valuation({"aggregation": "unweighted", "scenarios": [row, eps]}, "100")
        self.assertIsNone(result["expected_value_jpy"])
        self.assertEqual(result["valuation_range_jpy"], {"min": "92.82", "max": "100.00"})
        row["probability"] = "1"
        with self.assertRaisesRegex(ValueError, "unweighted"):
            calculate_valuation({"aggregation": "unweighted", "scenarios": [row]}, "100")

    def test_eps_and_dividend_output_shapes_are_unchanged(self):
        eps = {"name": "eps", "probability": "1", "method": "eps_multiple",
               "inputs": {"eps_jpy": "10", "pe": "10", "non_operating_assets_jpy": None,
                          "minority_interests_jpy": "ignored"}}
        self.assertEqual(set(value(eps)["scenarios"][0]),
                         {"name", "probability", "method", "fair_value_jpy", "upside_pct"})
        ddm = {"name": "ddm", "probability": "1", "method": "dividend_discount",
               "inputs": {"dividends_per_share_jpy": ["10"], "cost_of_equity": ".1",
                          "terminal_cost_of_equity": ".1", "terminal_dividend_per_share_jpy": "11",
                          "terminal_growth_rate": "0"}}
        result = value(ddm)["scenarios"][0]
        self.assertEqual(result["fair_value_jpy"], "109.09")
        self.assertFalse(BRIDGE_KEYS & set(result))
        ddm["inputs"]["non_operating_assets_jpy"] = "0"
        with self.assertRaisesRegex(ValueError, "exactly the five"):
            value(ddm)


if __name__ == "__main__":
    unittest.main()
