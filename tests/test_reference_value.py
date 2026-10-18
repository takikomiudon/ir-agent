"""Price-free references share valuation validation and kernels, not a quote."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.cli import main
from ir_agent.valuation import calculate_reference_value, calculate_valuation


def scenario(name, method, inputs, **fields):
    return {"name": name, "method": method, "inputs": inputs, **fields}


def graham(eps="1", bps="10", name="graham", **fields):
    return scenario(name, "graham_number", {
        "eps_jpy": eps, "book_value_per_share_jpy": bps}, **fields)


def unweighted(*rows):
    return {"aggregation": "unweighted", "scenarios": list(rows)}


def six_methods():
    dcf = {"fcf_jpy": ["100"], "discount_rate": ".1",
           "terminal_growth_rate": ".02", "cash_jpy": "50",
           "debt_jpy": "100", "shares_outstanding": "10"}
    terminal = {**dcf, "fcf_jpy": ["110"], "terminal_growth_rate": "0",
                "terminal_fcff_jpy": "110"}
    return [
        scenario("eps", "eps_multiple", {"eps_jpy": "65", "pe": "20"}),
        graham(),
        scenario("dcf", "dcf", dcf),
        scenario("ddm", "dividend_discount", {
            "dividends_per_share_jpy": ["11"], "cost_of_equity": ".1",
            "terminal_cost_of_equity": ".1", "terminal_dividend_per_share_jpy": "11",
            "terminal_growth_rate": "0"}),
        scenario("terminal", "dcf_explicit_terminal", terminal),
        scenario("bridge", "dcf_explicit_terminal_equity_bridge", {
            **terminal, "non_operating_assets_jpy": "30", "minority_interests_jpy": "20"}),
    ]


class ReferenceValueTests(unittest.TestCase):
    def test_all_six_methods_have_independent_known_values_and_match_priced_kernels(self):
        # EPS65*20; sqrt225; DCF EV1250 less50 /10; DDM121/1.1;
        # explicit EV1100 less50 /10; the bridge adds30 and removes20 /10.
        valuation = unweighted(*six_methods())
        result = calculate_reference_value(valuation, include_unrounded=True)
        self.assertEqual([s["reference_value_jpy"] for s in result["scenarios"]],
                         ["1300.00", "15.00", "120.00", "110.00", "105.00", "106.00"])
        priced = calculate_valuation(valuation, "100", include_unrounded=True)
        for ref, old in zip(result["scenarios"], priced["scenarios"]):
            self.assertEqual(ref["reference_value_jpy"], old["fair_value_jpy"])
        for ref, old in zip(result["unrounded"]["scenarios"], priced["unrounded"]["scenarios"]):
            self.assertEqual(ref["reference_value_jpy"], old["fair_value_jpy"])
        self.assertEqual(result["reference_range_jpy"], {"min": "15.00", "max": "1300.00"})
        self.assertIsNone(result["expected_reference_value_jpy"])
        self.assertTrue(result["meaning_review_required"])
        self.assertFalse(result["financial_inputs_verified"])

    def test_no_price_dummy_ratios_or_old_public_wrapper_are_needed(self):
        with patch("ir_agent.valuation.calculate_valuation", side_effect=AssertionError("no dummy price")):
            result = calculate_reference_value(unweighted(
                graham("358.13", "1965.51", "1975"), graham("443.34", "2659.88", "3817")))
        self.assertEqual([s["reference_value_jpy"] for s in result["scenarios"]], ["3979.69", "5150.99"])
        encoded = json.dumps(result)
        for forbidden in ("current_price", "upside_pct", "downside_pct", "margin_of_safety",
                          "enterprise_value_jpy", "fair_value_jpy", "action"):
            self.assertNotIn(forbidden, encoded)
        with self.assertRaises(TypeError):
            calculate_reference_value(unweighted(graham()), current_price_jpy="100")

    def test_weighted_reference_uses_only_supplied_probabilities_and_unrounded_values(self):
        valuation = {"scenarios": [
            scenario("low", "eps_multiple", {"eps_jpy": ".004", "pe": "1"}, probability=".5"),
            scenario("high", "eps_multiple", {"eps_jpy": ".005", "pe": "1"}, probability=".5"),
        ]}
        result = calculate_reference_value(valuation, include_unrounded=True)
        self.assertEqual(result["aggregation"], "weighted")
        self.assertEqual([s["probability"] for s in result["scenarios"]], ["0.5", "0.5"])
        self.assertEqual(result["expected_reference_value_jpy"], "0.00")
        self.assertEqual(Decimal(result["unrounded"]["expected_reference_value_jpy"]), Decimal(".0045"))
        self.assertNotIn("reference_range_jpy", result)
        rows = deepcopy(valuation["scenarios"])
        for row in rows:
            del row["probability"]
        unknown = calculate_reference_value(unweighted(*rows), include_unrounded=True)
        self.assertIsNone(unknown["expected_reference_value_jpy"])
        self.assertIsNone(unknown["unrounded"]["expected_reference_value_jpy"])
        self.assertTrue(all(s["probability"] is None for s in unknown["scenarios"]))

    def test_probability_contract_is_not_defaulted_or_relaxed(self):
        cases = [
            {"scenarios": [graham()]},
            {"scenarios": [graham(probability=".99")]},
            {"scenarios": [graham(probability="1"), graham(name="tiny", probability="1e-100")]},
            unweighted(graham(probability="0")),
            {"aggregation": "unknown", "scenarios": [graham()]},
        ]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate_reference_value(value)

    def test_existing_priced_json_contract_is_unchanged(self):
        self.assertEqual(calculate_valuation({"scenarios": [graham(probability="1")]}, "10"), {
            "scenarios": [{"name": "graham", "probability": "1", "method": "graham_number",
                           "fair_value_jpy": "15.00", "upside_pct": "50.00"}],
            "expected_value_jpy": "15.00", "expected_upside_pct": "50.00",
            "worst_case_downside_pct": "0.00",
        })
        with self.assertRaisesRegex(ValueError, "current_price_jpy must be greater than zero"):
            calculate_valuation(unweighted(graham()), "0")

    def test_new_route_keeps_method_validation_errors(self):
        cases = [unweighted(graham("-1", "-10")),
                 unweighted(graham(True)), unweighted(graham("NaN")),
                 unweighted(graham())]
        cases[-1]["scenarios"][0]["inputs"]["coefficient"] = "22.5"
        negative_equity = six_methods()[2]
        negative_equity["inputs"]["debt_jpy"] = "1301"
        cases.append(unweighted(negative_equity))
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as reference:
                    calculate_reference_value(value)
                with self.assertRaises(ValueError) as priced:
                    calculate_valuation(value, "1")
                self.assertEqual(str(reference.exception), str(priced.exception))
        for flag in (None, 0, 1, "true"):
            with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, "include_unrounded must be boolean"):
                calculate_reference_value(unweighted(graham()), include_unrounded=flag)

    def test_graham_input_and_total_precision_limits_precede_context_allocation(self):
        dcf = scenario("long", "dcf", {
            "fcf_jpy": ["0"] * 100, "discount_rate": ".1", "terminal_growth_rate": "0",
            "cash_jpy": "0", "debt_jpy": "0", "shares_outstanding": "1"})
        huge_old = scenario("old", "eps_multiple", {"eps_jpy": "1e1000000000", "pe": "1"})
        cases = [
            unweighted(graham("1e1000000000")), unweighted(graham("1e-1000000000")),
            unweighted(graham("1" * 10001)), unweighted(graham("1e1000", "1e1000"), dcf),
            unweighted(graham(), huge_old),
            {"scenarios": [graham(name="zero", probability="0e-1000000000"),
                           graham(name="one", probability="1")]},
        ]
        for value in cases:
            with self.subTest(methods=[s["method"] for s in value["scenarios"]]):
                with patch("ir_agent.valuation.Context", side_effect=AssertionError("do not allocate")) as context:
                    with self.assertRaisesRegex(ValueError, "computation budget"):
                        calculate_reference_value(value, include_unrounded=True)
                    context.assert_not_called()

    def test_reference_route_does_not_add_graham_budget_to_legacy_only_models(self):
        value = unweighted(scenario("old", "eps_multiple", {"eps_jpy": "1e1000000000", "pe": "1"}))
        with patch("ir_agent.valuation.Context", side_effect=RuntimeError("legacy precision probe")) as context:
            with self.assertRaisesRegex(RuntimeError, "legacy precision probe"):
                calculate_reference_value(value)
            context.assert_called_once()

    def test_hostile_decimal_context_and_input_are_unchanged(self):
        valuation = unweighted(*six_methods())
        original = deepcopy(valuation)
        expected = calculate_reference_value(valuation, include_unrounded=True)
        with localcontext() as context:
            context.prec, context.rounding, context.Emin, context.Emax = 2, ROUND_DOWN, -2, 2
            context.traps[Inexact] = context.traps[Rounded] = True
            context.flags[Rounded] = True
            before = str(context)
            actual = calculate_reference_value(valuation, include_unrounded=True)
            self.assertEqual(str(context), before)
            for invalid in ("-1", "bad", "NaN", True):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    calculate_reference_value(unweighted(graham(invalid)))
                self.assertEqual(str(context), before)
        self.assertEqual(actual, expected)
        self.assertEqual(valuation, original)


class ReferenceValueCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.input = self.root / "input.json"
        self.input.write_text(json.dumps(unweighted(graham())), encoding="utf-8")

    def invoke(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("ir_agent.cli.Store", side_effect=AssertionError("Store must not open")) as store, \
                redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(list(map(str, args)))
            store.assert_not_called()
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_price_free_reference_never_opens_even_an_invalid_database(self):
        database = self.root / "existing-non-db.txt"
        database.write_bytes(b"preserve this unrelated file")
        before = sha256(database.read_bytes()).hexdigest()
        code, stdout, stderr = self.invoke("--db", database, "reference-value", self.input, "--include-unrounded")
        self.assertEqual(code, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result["scenarios"][0]["reference_value_jpy"], "15.00")
        self.assertEqual(result["unrounded"]["scenarios"][0]["reference_value_jpy"], "15.0")
        self.assertEqual(sha256(database.read_bytes()).hexdigest(), before)
        self.assertEqual(stderr, "")

    def test_cli_bad_files_and_invalid_values_also_never_open_store(self):
        for content in ('{"scenarios":[],"scenarios":[]}', json.dumps(unweighted(graham("0")))):
            self.input.write_text(content)
            code, stdout, stderr = self.invoke("reference-value", self.input)
            self.assertEqual(code, 1)
            self.assertEqual(stdout, "")
            self.assertTrue(stderr.startswith("ir-agent: "))
            self.assertNotIn("Traceback", stderr)
        code, stdout, stderr = self.invoke("reference-value", self.root / "missing.json")
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")

    def test_reference_cli_rejects_price_and_old_value_still_requires_price(self):
        for arguments in [("reference-value", self.input, "--price", "1"), ("value", self.input)]:
            with self.subTest(arguments=arguments), redirect_stderr(io.StringIO()), \
                    patch("ir_agent.cli.Store", side_effect=AssertionError("no Store")):
                with self.assertRaises(SystemExit) as error:
                    main(list(map(str, arguments)))
                self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
