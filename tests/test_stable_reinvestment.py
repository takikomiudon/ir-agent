"""Synthetic arithmetic and explicit Damodaran example inputs; no live forecasts."""
from copy import deepcopy
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from hashlib import sha256
import json
import unittest

from ir_agent.models import json_text
from ir_agent.stable_reinvestment import calculate_stable_reinvestment


def request():
    basis = {"company_id": "synthetic-company", "currency": "JPY", "amount_unit": "millions",
             "scope": "consolidated", "accounting_basis": "synthetic accounting fixture"}
    period = {"kind": "full_fiscal_year", "label": "synthetic next stable period", "start": None, "end": None}

    def descriptor(value, concept):
        return {"value": value, "concept": concept, "period": deepcopy(period), "basis": deepcopy(basis),
                "data_kind": "synthetic_example", "source_refs": [], "rationale": "Synthetic arithmetic fixture, no forecast adoption."}

    nopat = descriptor("100", "aftertax_operating_income_before_financing")
    nopat["timing"] = "next_stable_period"
    growth = descriptor(".04", "stable_operating_income_growth")
    growth["unit"] = "annual_decimal_ratio"
    roc = descriptor(".1", "aftertax_return_on_new_investment")
    roc["unit"] = "annual_decimal_ratio"
    return {"method": "stable_growth_new_investment_roc", "basis": basis,
            "nopat_next": nopat, "growth": growth, "roc_new": roc,
            "assessment": {"tax_and_nol_rationale": None, "stable_growth_rationale": None,
                           "new_investment_roc_rationale": None, "comparability_rationale": None, "source_refs": []}}


def author_example(kind):
    value = request()
    if kind == "toyota":
        company, currency, amount_unit, nopat, growth, roc, page = (
            "author-example-toyota-2009", "JPY", "billions", "999.5670265", ".015", ".0509", 17)
    else:
        company, currency, amount_unit, nopat, growth, roc, page = (
            "author-example-exxon-2009", "USD", "millions", "21889.8936", ".02", ".21", 21)
    value["basis"].update(company_id=company, currency=currency, amount_unit=amount_unit,
                          accounting_basis="Damodaran 2009 example presentation; issuer accounting not resolved")
    source = {"id": "damodaran.cyclical-commodity.2009", "version": None,
              "sha256": "16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40",
              "location": f"PDF p{page}, stable reinvestment/value numerator",
              "quote": "Stable period reinvestment rate" if kind == "toyota" else "Reinvestment Rate = g/ ROC"}
    for key, number in (("nopat_next", nopat), ("growth", growth), ("roc_new", roc)):
        value[key]["value"] = number
        value[key]["basis"] = deepcopy(value["basis"])
        value[key]["period"]["label"] = f"{kind} author's next stable annual period; exact dates unknown"
        value[key]["source_refs"] = [deepcopy(source)]
        value[key]["data_kind"] = "author_estimate"
        value[key]["rationale"] = "Reproduce literal published example inputs; no current-company or tax/ROC adoption."
    value["nopat_next"]["rationale"] += (
        " Prepared outside this calculator as 1660.7*1.015*(1-.407)." if kind == "toyota"
        else " Prepared outside this calculator as 34614*1.02*(1-.38); use the author's displayed ROC21% path.")
    return value


class StableReinvestmentTests(unittest.TestCase):
    def test_three_input_decomposition_does_not_repeat_growth_or_tax(self):
        result = calculate_stable_reinvestment(request())
        self.assertEqual(result["status"], "intermediate_only")
        self.assertEqual(result["adoption"], "unresolved")
        self.assertEqual(result["arithmetic"]["reinvestment_rate"], "0.4")
        self.assertEqual(result["arithmetic"]["reinvestment_amount"], "40")
        self.assertEqual(result["arithmetic"]["fcff"], "60")
        self.assertEqual(result["calculation"]["formula"]["fcff"], "nopat_next - reinvestment_amount")
        self.assertEqual(result["calculation"]["author_reference"]["pdf_pages"], [17, 21])

    def test_author_toyota_literal_inputs_preserve_rounding_difference(self):
        result = calculate_stable_reinvestment(author_example("toyota"))
        self.assertTrue(result["arithmetic"]["reinvestment_rate"].startswith("0.2946954813359528487"))
        self.assertTrue(result["arithmetic"]["reinvestment_amount"].startswith("294.5678860019646365"))
        self.assertTrue(result["arithmetic"]["fcff"].startswith("704.9991404980353634"))
        self.assertNotEqual(result["arithmetic"]["reinvestment_rate"], "0.2946")
        self.assertEqual(result["arithmetic"]["basis"]["amount_unit"], "billions")
        self.assertEqual(result["verification"]["tax_and_nol_treatment"], "unverified")

    def test_author_exxon_displayed_21percent_roc_path_is_explicit(self):
        result = calculate_stable_reinvestment(author_example("exxon"))
        self.assertTrue(result["arithmetic"]["reinvestment_rate"].startswith("0.095238095238095238"))
        self.assertTrue(result["arithmetic"]["reinvestment_amount"].startswith("2084.751771428571428"))
        self.assertTrue(result["arithmetic"]["fcff"].startswith("19805.141828571428571"))
        self.assertEqual(result["request"]["roc_new"]["value"], ".21")
        self.assertEqual(result["arithmetic"]["basis"]["currency"], "USD")

    def test_rates_above_one_and_negative_fcff_are_not_clamped(self):
        value = request()
        value["growth"]["value"] = ".12"
        value["roc_new"]["value"] = ".06"
        result = calculate_stable_reinvestment(value)
        self.assertEqual(result["arithmetic"]["reinvestment_rate"], "2")
        self.assertEqual(result["arithmetic"]["reinvestment_amount"], "200")
        self.assertEqual(result["arithmetic"]["fcff"], "-100")
        self.assertEqual(result["verification"]["funding_and_survival"], "unverified")
        value["growth"]["value"] = "2"
        self.assertEqual(calculate_stable_reinvestment(value)["adoption"], "unresolved")

    def test_zero_roc_remains_undefined_including_explicit_zero_growth(self):
        value = request()
        value["roc_new"]["value"] = "0"
        with self.assertRaisesRegex(ValueError, "undefined denominator"):
            calculate_stable_reinvestment(value)
        value["growth"]["value"] = "0"
        with self.assertRaisesRegex(ValueError, "undefined denominator"):
            calculate_stable_reinvestment(value)
        value["roc_new"]["value"] = ".1"
        result = calculate_stable_reinvestment(value)
        self.assertEqual(result["arithmetic"]["reinvestment_rate"], "0")
        self.assertEqual(result["arithmetic"]["reinvestment_amount"], "0")
        self.assertEqual(result["arithmetic"]["fcff"], "100")

    def test_explicit_decimal_zero_preserves_declarations_without_economic_adoption(self):
        for token in ("0", "0.00", "+0", "-0", "0e-1000"):
            value = author_example("toyota")
            value["growth"]["value"] = token
            value["growth"]["data_kind"] = "explicit_assumption"
            value["growth"]["rationale"] = "Synthetic zero-growth boundary, not the author's positive forecast."
            before = deepcopy(value)
            with self.subTest(token=token):
                result = calculate_stable_reinvestment(value)
                self.assertEqual(value, before)
                self.assertEqual(result["request"], before)
                self.assertEqual(result["request_sha256"], sha256(json_text(before).encode()).hexdigest())
                self.assertEqual(result["arithmetic"]["reinvestment_rate"], "0")
                self.assertEqual(result["arithmetic"]["reinvestment_amount"], "0")
                self.assertEqual(result["arithmetic"]["fcff"], "999.5670265")
                self.assertEqual(result["status"], "intermediate_only")
                self.assertEqual(result["adoption"], "unresolved")
                self.assertEqual(set(result["verification"].values()), {"unverified"})
                self.assertIn("do not establish zero-growth economic applicability", result["calculation"]["project_adaptation"])
                self.assertTrue(any("zero gross capex or maintenance spending" in item for item in result["limitations"]))
                self.assertEqual(set(result["arithmetic"]), {"reinvestment_rate", "reinvestment_amount", "fcff", "basis"})

    def test_zero_growth_does_not_fill_missing_values_or_expand_other_sign_boundaries(self):
        value = request()
        del value["growth"]["value"]
        with self.assertRaisesRegex(ValueError, "exactly"):
            calculate_stable_reinvestment(value)
        for missing in (None, "", 0):
            value = request()
            value["growth"]["value"] = missing
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                calculate_stable_reinvestment(value)
        for key, number in (("nopat_next", "0"), ("nopat_next", "-1"), ("roc_new", "-.1")):
            value = request()
            value["growth"]["value"] = "0"
            value[key]["value"] = number
            with self.subTest(key=key, number=number), self.assertRaisesRegex(ValueError, "scope"):
                calculate_stable_reinvestment(value)

    def test_zero_growth_keeps_precise_nopat_and_ignores_ambient_decimal_traps(self):
        value = request()
        value["growth"]["value"] = "0"
        value["roc_new"]["value"] = "1e-1000"
        value["nopat_next"]["value"] = "123456789." + "1234567890" * 20 + "1"
        expected = calculate_stable_reinvestment(value)
        with localcontext() as context:
            context.prec = 2
            context.rounding = ROUND_DOWN
            context.Emin, context.Emax = -2, 2
            context.traps[Inexact] = context.traps[Rounded] = True
            context.clear_flags()
            flags = context.flags.copy()
            actual = calculate_stable_reinvestment(value)
            self.assertEqual(context.flags, flags)
        self.assertEqual(actual, expected)
        self.assertEqual(actual["arithmetic"]["fcff"], value["nopat_next"]["value"])

    def test_initial_positive_scope_rejects_losses_and_negative_rates_without_adjustment(self):
        for key, number in (("nopat_next", "0"), ("nopat_next", "-1"), ("growth", "-.01"), ("roc_new", "-.1")):
            value = request()
            value[key]["value"] = number
            with self.subTest(key=key, number=number), self.assertRaisesRegex(ValueError, "scope"):
                calculate_stable_reinvestment(value)

    def test_pretax_base_period_equity_earnings_and_historical_roc_are_not_converted(self):
        for key, concept in (("nopat_next", "pretax_operating_income"), ("nopat_next", "net_income"),
                             ("nopat_next", "ebitda"), ("nopat_next", "operating_cash_flow"),
                             ("roc_new", "historical_average_roc"), ("roc_new", "wacc"),
                             ("growth", "eps_growth"), ("growth", "revenue_growth")):
            value = request()
            value[key]["concept"] = concept
            with self.subTest(key=key, concept=concept), self.assertRaisesRegex(ValueError, "concept"):
                calculate_stable_reinvestment(value)
        value = request()
        value["nopat_next"]["timing"] = "base_period"
        with self.assertRaisesRegex(ValueError, "next_stable_period"):
            calculate_stable_reinvestment(value)

    def test_company_currency_unit_scope_and_accounting_must_match_all_descriptors(self):
        for field, replacement in (("company_id", "other"), ("currency", "USD"), ("amount_unit", "units"),
                                   ("scope", "standalone"), ("accounting_basis", "different basis")):
            for key in ("nopat_next", "growth", "roc_new"):
                value = request()
                value[key]["basis"][field] = replacement
                with self.subTest(field=field, descriptor=key), self.assertRaisesRegex(ValueError, "basis"):
                    calculate_stable_reinvestment(value)

    def test_same_next_stable_annual_period_and_decimal_rate_units_are_required(self):
        for key in ("growth", "roc_new"):
            value = request()
            value[key]["period"]["label"] = "different stable annual period"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "same next stable annual period"):
                calculate_stable_reinvestment(value)
            value = request()
            value[key]["unit"] = "percent"
            with self.assertRaisesRegex(ValueError, "annual_decimal_ratio"):
                calculate_stable_reinvestment(value)
        for kind in ("quarter", "YTD"):
            value = request()
            value["nopat_next"]["period"]["kind"] = kind
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "full_fiscal_year"):
                calculate_stable_reinvestment(value)

    def test_missing_dates_and_53week_declarations_do_not_verify_annual_applicability(self):
        missing = calculate_stable_reinvestment(request())
        self.assertEqual(len(missing["period_dates_incomplete"]), 6)
        value = request()
        for key in ("nopat_next", "growth", "roc_new"):
            value[key]["period"].update(start="2024-01-01", end="2025-01-05")
        result = calculate_stable_reinvestment(value)
        self.assertEqual(result["period_dates_incomplete"], [])
        self.assertEqual(result["verification"]["next_annual_period_and_comparability"], "unverified")
        self.assertTrue(any("52/53-week" in item for item in result["limitations"]))

    def test_invalid_reversed_and_mismatched_partial_dates_are_not_repaired(self):
        for start, end in (("2024-12-31", "2024-01-01"), ("2023-02-29", None), ("2024-01-01T00:00:00Z", None)):
            value = request()
            value["nopat_next"]["period"].update(start=start, end=end)
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                calculate_stable_reinvestment(value)
        value = request()
        value["growth"]["period"]["end"] = "2024-12-31"
        with self.assertRaisesRegex(ValueError, "same next stable annual period"):
            calculate_stable_reinvestment(value)

    def test_missing_zero_nonfinite_and_nonstrings_are_not_defaulted(self):
        for key in ("nopat_next", "growth", "roc_new"):
            for number in (None, "", "-", True, 1, 1.0, Decimal("1"), "NaN", "Infinity", "1,000", " 1", "1_0"):
                value = request()
                value[key]["value"] = number
                with self.subTest(key=key, number=number), self.assertRaises(ValueError):
                    calculate_stable_reinvestment(value)

    def test_filled_rationales_and_references_remain_declarations_not_approval(self):
        value = author_example("exxon")
        for key in value["assessment"]:
            if key != "source_refs":
                value["assessment"][key] = "Caller claims complete review; not evidence of independent verification."
        value["assessment"]["source_refs"] = deepcopy(value["roc_new"]["source_refs"])
        result = calculate_stable_reinvestment(value)
        self.assertEqual(result["assessment_fields_unset"], [])
        self.assertEqual(set(result["verification"].values()), {"unverified"})
        self.assertEqual(result["adoption"], "unresolved")
        for field in ("tax", "wacc", "dcf", "terminal_value", "price", "probability", "action"):
            self.assertNotIn(field, result["arithmetic"])
            self.assertNotIn(field, result)

    def test_unknown_fields_cannot_add_tax_growth_conversion_capex_or_approval(self):
        mutations = [lambda r: r.update(approved=True), lambda r: r.update(now="2026-10-15T00:00:00Z"),
                     lambda r: r["basis"].update(profit_concept="pretax_operating_income"),
                     lambda r: r["nopat_next"].update(tax_rate=".3"),
                     lambda r: r["growth"].update(apply_growth_again=True),
                     lambda r: r["roc_new"].update(capital_stock="1000"),
                     lambda r: r["assessment"].update(capex="10"),
                     lambda r: r["nopat_next"]["period"].update(verified=True)]
        for mutate in mutations:
            value = request()
            mutate(value)
            with self.subTest(mutation=mutations.index(mutate)), self.assertRaises(ValueError):
                calculate_stable_reinvestment(value)
        value = author_example("exxon")
        value["nopat_next"]["source_refs"][0]["verified"] = True
        with self.assertRaises(ValueError):
            calculate_stable_reinvestment(value)

    def test_invalid_enum_container_types_are_value_errors_not_type_errors(self):
        for replacement in ([], {}, True):
            mutations = [lambda r: r.update(method=replacement),
                         lambda r: r["basis"].update(amount_unit=replacement),
                         lambda r: r["basis"].update(currency=replacement),
                         lambda r: r["nopat_next"].update(concept=replacement),
                         lambda r: r["nopat_next"].update(timing=replacement),
                         lambda r: r["growth"].update(unit=replacement),
                         lambda r: r["roc_new"].update(data_kind=replacement),
                         lambda r: r["nopat_next"]["period"].update(kind=replacement)]
            for index, mutate in enumerate(mutations):
                value = request()
                mutate(value)
                with self.subTest(replacement=replacement, mutation=index), self.assertRaises(ValueError):
                    calculate_stable_reinvestment(value)

    def test_missing_keys_and_method_do_not_have_defaults(self):
        for key in request():
            value = request()
            del value[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                calculate_stable_reinvestment(value)
        for method in ("g_roc", "", None):
            value = request()
            value["method"] = method
            with self.subTest(method=method), self.assertRaises(ValueError):
                calculate_stable_reinvestment(value)

    def test_private_decimal_context_is_independent_of_ambient_state(self):
        value = author_example("exxon")
        expected = calculate_stable_reinvestment(value)
        with localcontext() as context:
            context.prec = 2
            context.rounding = ROUND_DOWN
            context.Emin, context.Emax = -2, 2
            context.traps[Inexact] = context.traps[Rounded] = True
            context.clear_flags()
            flags = context.flags.copy()
            actual = calculate_stable_reinvestment(value)
            self.assertEqual(context.flags, flags)
            self.assertEqual(context.prec, 2)
        self.assertEqual(actual, expected)

    def test_high_precision_retains_tiny_reinvestment_when_subtracting_from_nopat(self):
        value = request()
        value["nopat_next"]["value"] = "1"
        value["growth"]["value"] = "1e-1000"
        value["roc_new"]["value"] = "1e1000"
        result = calculate_stable_reinvestment(value)
        self.assertEqual(result["arithmetic"]["reinvestment_amount"], format(Decimal("1e-2000"), "f"))
        self.assertEqual(result["arithmetic"]["fcff"], "0." + "9" * 2000)
        self.assertGreater(result["calculation"]["working_precision_digits"], 2000)
        self.assertIsNone(result["calculation"]["display_quantization"])

    def test_json_request_and_numeric_resource_bounds_fail_explicitly(self):
        for number in ("1e1001", "1e-1001", "9" * 257, float("nan"), {1: "bad key"}):
            value = request()
            value["nopat_next"]["value"] = number
            with self.subTest(number=number), self.assertRaises(ValueError):
                calculate_stable_reinvestment(value)
        value = request()
        value["assessment"]["tax_and_nol_rationale"] = "x" * (2 * 1024 * 1024)
        with self.assertRaisesRegex(ValueError, "2 MiB"):
            calculate_stable_reinvestment(value)
        value = request()
        value["assessment"]["tax_and_nol_rationale"] = value
        with self.assertRaisesRegex(ValueError, "nesting"):
            calculate_stable_reinvestment(value)

    def test_reference_format_and_duplicate_refs_do_not_create_resolution_guarantees(self):
        for version, digest in ((True, "a" * 64), (0, "a" * 64), (None, "A" * 64), (None, [])):
            value = author_example("exxon")
            value["nopat_next"]["source_refs"][0].update(version=version, sha256=digest)
            with self.subTest(version=version, digest=digest), self.assertRaises(ValueError):
                calculate_stable_reinvestment(value)
        value = author_example("exxon")
        value["nopat_next"]["source_refs"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate"):
            calculate_stable_reinvestment(value)

    def test_input_is_not_mutated_and_output_is_json_safe(self):
        value = author_example("toyota")
        before = deepcopy(value)
        result = calculate_stable_reinvestment(value)
        self.assertEqual(value, before)
        self.assertEqual(result["request_sha256"], sha256(json_text(before).encode()).hexdigest())
        json.dumps(result, allow_nan=False)
        result["request"]["nopat_next"]["value"] = "1"
        result["arithmetic"]["basis"]["company_id"] = "caller mutation"
        self.assertEqual(value, before)


if __name__ == "__main__":
    unittest.main()
