"""The maintainer's two-input formula is arithmetic, not a trading policy."""

from copy import deepcopy
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from fractions import Fraction
import json
import unittest
from unittest.mock import patch

from ir_agent.model_inputs import audit_model_inputs
from ir_agent.valuation import calculate_valuation


def graham(eps="1", bps="10", name="base", **fields):
    return {"name": name, "method": "graham_number", "inputs": {
        "eps_jpy": eps, "book_value_per_share_jpy": bps}, **fields}


def unweighted(*scenarios):
    return {"aggregation": "unweighted", "scenarios": list(scenarios)}


class GrahamNumberValuationTests(unittest.TestCase):
    def test_1975_displayed_annual_inputs_reference_only_synthetic_price(self):
        # Saved annual-arithmetic lane A. Price100 is a synthetic reference,
        # not a company price observation or an adopted investment comparison.
        result = calculate_valuation(unweighted(graham("358.13", "1965.51")),
                                     "100", include_unrounded=True)
        self.assertEqual(result["scenarios"][0]["fair_value_jpy"], "3979.69")
        value = Fraction(result["unrounded"]["scenarios"][0]["fair_value_jpy"])
        radicand = Fraction(63351728667, 4000)
        self.assertLess(abs(value * value - radicand), Fraction(1, 10**65))
        self.assertIsNone(result["expected_value_jpy"])
        self.assertIsNone(result["scenarios"][0]["probability"])

    def test_perfect_square_and_existing_json_output_contract(self):
        result = calculate_valuation({"scenarios": [graham(probability="1")]}, "10")
        self.assertEqual(result, {
            "scenarios": [{"name": "base", "probability": "1",
                           "method": "graham_number", "fair_value_jpy": "15.00",
                           "upside_pct": "50.00"}],
            "expected_value_jpy": "15.00", "expected_upside_pct": "50.00",
            "worst_case_downside_pct": "0.00",
        })
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_sqrt_cent_midpoint_and_adjacent_values_round_only_at_output(self):
        for eps, expected in [(".044889999999999999999999999999", "1.00"),
                              (".04489", "1.01"),
                              (".044890000000000000000000000001", "1.01")]:
            with self.subTest(eps=eps):
                result = calculate_valuation(unweighted(graham(eps, "1")),
                                             "1", include_unrounded=True)
                self.assertEqual(result["scenarios"][0]["fair_value_jpy"], expected)
        middle = calculate_valuation(unweighted(graham(".04489", "1")),
                                     "1", include_unrounded=True)
        self.assertEqual(Decimal(middle["unrounded"]["scenarios"][0]["fair_value_jpy"]),
                         Decimal("1.005"))
        self.assertEqual(middle["scenarios"][0]["upside_pct"], "0.50")

    def test_rounding_does_not_change_weighted_value_or_downside(self):
        # sqrt(22.5 * .0000004 * 1) = .003 and the second value is .006.
        result = calculate_valuation({"scenarios": [
            graham(".0000004", "1", "low", probability=".5"),
            graham(".0000016", "1", "high", probability=".5"),
        ]}, ".01", include_unrounded=True)
        self.assertEqual([s["fair_value_jpy"] for s in result["scenarios"]], ["0.00", "0.01"])
        self.assertEqual(result["expected_value_jpy"], "0.00")
        self.assertEqual(result["expected_upside_pct"], "-55.00")
        self.assertEqual(result["worst_case_downside_pct"], "70.00")
        self.assertEqual(Decimal(result["unrounded"]["expected_value_jpy"]), Decimal(".0045"))

    def test_each_input_must_independently_be_positive_and_finite(self):
        # Negative*negative cannot pass merely because the product is positive.
        invalid = ("0", "-0", "-1", "-1e-120", True, False, None, "", "bad",
                   "NaN", "sNaN", "Infinity", "-Infinity", float("nan"),
                   float("inf"), Decimal("NaN"), [], {})
        for key in ("eps_jpy", "book_value_per_share_jpy"):
            for value in invalid:
                row = graham(); row["inputs"][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    calculate_valuation(unweighted(row), "1")
        with self.assertRaises(ValueError):
            calculate_valuation(unweighted(graham("-1", "-10")), "1")

    def test_missing_extra_and_mixed_inputs_do_not_get_ignored_or_defaulted(self):
        for key in ("eps_jpy", "book_value_per_share_jpy"):
            row = graham(); del row["inputs"][key]
            with self.subTest(missing=key), self.assertRaisesRegex(ValueError, "exactly the two"):
                calculate_valuation(unweighted(row), "1")
        for key in ("coefficient", "pe", "current_price_jpy", "shares_outstanding",
                    "cash_jpy", "growth_rate", "book_value_per_share_jpy.extra"):
            row = graham(); row["inputs"][key] = "1"
            with self.subTest(extra=key), self.assertRaisesRegex(ValueError, "exactly the two"):
                calculate_valuation(unweighted(row), "1")

    def test_int_float_and_decimal_inputs_use_the_existing_numeric_contract(self):
        for eps, bps in [(1, 10), (1.0, 10.0), (Decimal("1"), Decimal("10"))]:
            with self.subTest(eps=eps, bps=bps):
                result = calculate_valuation(unweighted(graham(eps, bps)), "1")
                self.assertEqual(result["scenarios"][0]["fair_value_jpy"], "15.00")

    def test_caller_context_flags_rounding_traps_and_inputs_are_unchanged(self):
        valuation = unweighted(graham("358.13", "1965.51")); original = deepcopy(valuation)
        expected = calculate_valuation(valuation, "100", include_unrounded=True)
        with localcontext() as context:
            context.prec, context.rounding = 2, ROUND_DOWN
            context.Emin, context.Emax = -2, 2
            context.traps[Inexact] = context.traps[Rounded] = True
            context.flags[Rounded] = True
            before = str(context)
            actual = calculate_valuation(valuation, "100", include_unrounded=True)
            self.assertEqual(str(context), before)
        self.assertEqual(actual, expected)
        self.assertEqual(valuation, original)

    def test_small_positive_inputs_keep_unrounded_value_even_when_display_is_zero(self):
        result = calculate_valuation(unweighted(graham("1e-120", "1e-120")),
                                     "1", include_unrounded=True)
        self.assertEqual(result["scenarios"][0]["fair_value_jpy"], "0.00")
        self.assertGreater(Decimal(result["unrounded"]["scenarios"][0]["fair_value_jpy"]), 0)
        self.assertEqual(result["worst_case_downside_pct"], "100.00")

    def test_large_and_reciprocal_scales_are_not_silently_normalized_or_underflowed(self):
        reciprocal = calculate_valuation(unweighted(graham("1e200", "1e-200")),
                                          "1", include_unrounded=True)
        self.assertEqual(reciprocal["scenarios"][0]["fair_value_jpy"], "4.74")
        large = calculate_valuation(unweighted(graham("1e120", "1e120")), "1e120")
        self.assertTrue(Decimal(large["scenarios"][0]["fair_value_jpy"]).is_finite())
        self.assertEqual(large["scenarios"][0]["upside_pct"], "374.34")

    def test_pathological_input_representations_raise_before_huge_precision_allocation(self):
        for key in ("eps_jpy", "book_value_per_share_jpy"):
            for value in ("1e1000000000", "1e-1000000000", "1" * 10001):
                row = graham(); row["inputs"][key] = value
                with self.subTest(key=key, length=len(value)), self.assertRaisesRegex(ValueError, "computation budget"):
                    calculate_valuation(unweighted(row), "1")

    def test_total_precision_budget_rejects_price_probability_and_mixed_horizon_before_context(self):
        dcf = {"name": "dcf", "method": "dcf", "inputs": {
            "fcf_jpy": ["0"] * 100, "discount_rate": ".1", "terminal_growth_rate": "0",
            "cash_jpy": "0", "debt_jpy": "0", "shares_outstanding": "1"}}
        eps = {"name": "eps", "method": "eps_multiple",
               "inputs": {"eps_jpy": "1e1000000000", "pe": "1"}}
        cases = [
            (unweighted(graham()), "1e1000000000"),
            (unweighted(graham()), "1e-1000000000"),
            ({"scenarios": [graham(name="zero", probability="0e-1000000000"),
                            graham(name="one", probability="1")]}, "1"),
            (unweighted(graham("1e1000", "1e1000"), dcf), "1"),
            (unweighted(graham(), eps), "1"),
        ]
        for valuation, price in cases:
            with self.subTest(price=price, methods=[s["method"] for s in valuation["scenarios"]]):
                with patch("ir_agent.valuation.Context", side_effect=AssertionError("must not allocate")) as context:
                    with self.assertRaisesRegex(ValueError, "context computation budget"):
                        calculate_valuation(valuation, price)
                    context.assert_not_called()

    def test_new_total_precision_budget_does_not_change_legacy_only_range_contract(self):
        valuation = unweighted({"name": "old", "method": "eps_multiple",
                                "inputs": {"eps_jpy": "1", "pe": "1"}})
        # Intercept rather than allocate an enormous legacy context. Only the
        # new-method route has the new guard; this does not endorse such inputs.
        with patch("ir_agent.valuation.Context", side_effect=RuntimeError("legacy context probe")) as context:
            with self.assertRaisesRegex(RuntimeError, "legacy context probe"):
                calculate_valuation(valuation, "1e1000000000")
            context.assert_called_once()

    def test_mixed_existing_methods_share_unweighted_range_without_probabilities(self):
        eps = {"name": "eps", "method": "eps_multiple", "inputs": {"eps_jpy": "2", "pe": "10"}}
        dcf = {"name": "dcf", "method": "dcf", "inputs": {
            "fcf_jpy": ["100"], "discount_rate": ".1", "terminal_growth_rate": ".02",
            "cash_jpy": "50", "debt_jpy": "100", "shares_outstanding": "10"}}
        result = calculate_valuation(unweighted(graham(), eps, dcf), "100")
        self.assertEqual([s["fair_value_jpy"] for s in result["scenarios"]], ["15.00", "20.00", "120.00"])
        self.assertEqual(result["valuation_range_jpy"], {"min": "15.00", "max": "120.00"})
        self.assertIsNone(result["expected_value_jpy"])
        self.assertEqual(result["worst_case_downside_pct"], "85.00")

    def test_generic_audit_has_only_the_two_canonical_numerical_paths(self):
        valuation = unweighted(graham())
        value = {"company_id": "synthetic-issuer", "as_of": "2026-10-16T00:00:00+00:00",
                 "synthetic": True, "valuation": valuation, "sources": [], "provenance": {}}
        expected = ["scenarios.base.inputs.book_value_per_share_jpy", "scenarios.base.inputs.eps_jpy"]
        result = audit_model_inputs(value)
        self.assertEqual(result["required_paths"], expected)
        self.assertEqual(result["missing_paths"], expected)
        self.assertFalse(result["financial_inputs_verified"])
        self.assertFalse(result["expected_value_available"])
        extra = deepcopy(value); extra["valuation"]["scenarios"][0]["inputs"]["pe"] = "15"
        with self.assertRaisesRegex(ValueError, "exactly the two"):
            audit_model_inputs(extra)
        value["provenance"]["scenarios.base.inputs.coefficient"] = {}
        with self.assertRaisesRegex(ValueError, "Unknown provenance path"):
            audit_model_inputs(value)


if __name__ == "__main__":
    unittest.main()
