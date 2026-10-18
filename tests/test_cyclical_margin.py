"""Synthetic cases and Damodaran's preserved 2009 Toyota arithmetic example."""
from copy import deepcopy
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from hashlib import sha256
import json
import unittest

from ir_agent.cyclical_margin import calculate_cyclical_margin
from ir_agent.models import json_text


# Original Table 2, PDF p.15; amounts are million JPY, not current-company inputs.
# Preserve raw revenue/OI rather than calculating from displayed annual margins.
TOYOTA_ROWS = [
    ("FY1 1998", "11678400", "779800"),
    ("FY1 1999", "12749010", "774947"),
    ("FY1 2000", "12879560", "775982"),
    ("FY1 2001", "13424420", "870131"),
    ("FY1 2002", "15106300", "1123475"),
    ("FY1 2003", "16054290", "1363680"),
    ("FY1 2004", "17294760", "1666894"),
    ("FY1 2005", "18551530", "1672187"),
    ("FY1 2006", "21036910", "1878342"),
    ("FY1 2007", "23948090", "2238683"),
    ("FY1 2008", "26289240", "2270375"),
    ("FY 2009 (Est)", "22661325", "267904"),
]


def period(label, start=None, end=None):
    return {"kind": "full_fiscal_year", "label": label, "start": start, "end": end}


def basis(company="synthetic-company"):
    return {"company_id": company, "currency": "JPY", "amount_unit": "millions",
            "scope": "consolidated", "accounting_basis": "synthetic accounting fixture",
            "profit_concept": "pretax_operating_income"}


def observation(identifier, revenue, income, *, row_basis=None, row_period=None):
    return {"id": identifier, "basis": row_basis or basis(),
            "period": row_period or period(identifier), "revenue": revenue,
            "operating_income": income, "data_kind": "synthetic_example",
            "source_refs": [], "selection_rationale": "Synthetic arithmetic fixture only."}


def synthetic_request():
    return {
        "method": "arithmetic_equal_annual_periods", "basis": basis(),
        "annual_observations": [
            observation("synthetic-fy1", "100", "10", row_period=period("synthetic-fy1", "2023-01-01", "2023-12-31")),
            observation("synthetic-fy2", "200", "40", row_period=period("synthetic-fy2", "2024-01-01", "2024-12-31")),
        ],
        "application_revenue": {"basis": basis(), "period": period("synthetic-application"),
            "revenue": "300", "data_kind": "synthetic_example", "source_refs": [],
            "selection_rationale": "Synthetic same-unit application amount."},
        "assessment": {"cycle_driver": None, "full_cycle_rationale": None,
            "comparability_rationale": None, "application_rationale": None,
            "source_refs": [], "excluded_observations": []},
    }


def toyota_request():
    request = synthetic_request()
    author_basis = basis("author-example-toyota-2009")
    author_basis["accounting_basis"] = "Damodaran 2009 Table 2 presentation; issuer accounting not resolved"
    source = {"id": "damodaran.cyclical-commodity.2009", "version": None,
              "sha256": "16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40",
              "location": "PDF p15 Table 2, original revenue and operating-income columns",
              "quote": "Table 2: Toyota’s Operating Performance – 1998-2009 (in millions of Yen)"}
    request["basis"] = author_basis
    request["annual_observations"] = []
    for label, revenue, income in TOYOTA_ROWS:
        row = observation(label, revenue, income, row_basis=deepcopy(author_basis))
        row["data_kind"] = "author_estimate" if label == "FY 2009 (Est)" else "reported_fact"
        row["source_refs"] = [deepcopy(source)]
        row["selection_rationale"] = "Reproduce every author Table 2 row, including the labelled 2009 estimate; not current investment inputs."
        request["annual_observations"].append(row)
    request["application_revenue"] = {
        "basis": deepcopy(author_basis), "period": period("FY 2009 (Est)"),
        "revenue": "22661325", "data_kind": "author_estimate", "source_refs": [deepcopy(source)],
        "selection_rationale": "Use the author's specified 2009 revenue scale; no forecast adoption.",
    }
    request["assessment"]["source_refs"] = [deepcopy(source)]
    request["assessment"]["full_cycle_rationale"] = "Reproduce the author's selected 1998–2009 history; do not certify full-cycle coverage."
    return request


class CyclicalMarginTests(unittest.TestCase):
    def test_equal_annual_margins_are_not_sales_weighted(self):
        result = calculate_cyclical_margin(synthetic_request())
        self.assertEqual(result["status"], "intermediate_only")
        self.assertEqual(result["adoption"], "unresolved")
        self.assertEqual(result["arithmetic"]["mean_operating_margin_ratio"], "0.15")
        self.assertEqual(result["arithmetic"]["applied_operating_income"], "45")
        self.assertNotEqual(result["arithmetic"]["applied_operating_income"], "50")
        self.assertEqual(result["arithmetic"]["annual_margins"], [
            {"id": "synthetic-fy1", "operating_margin_ratio": "0.1"},
            {"id": "synthetic-fy2", "operating_margin_ratio": "0.2"}])
        self.assertEqual(result["calculation"]["formula"]["application"],
                         "mean_operating_margin_ratio * application_revenue")

    def test_author_toyota_raw_12_rows_reproduce_unrounded_mean_path(self):
        result = calculate_cyclical_margin(toyota_request())
        arithmetic = result["arithmetic"]
        self.assertEqual(arithmetic["period_count"], 12)
        self.assertTrue(arithmetic["mean_operating_margin_ratio"].startswith("0.073283985287165616271727743555"))
        self.assertTrue(arithmetic["applied_operating_income"].startswith("1660712.207887678359158910708218"))
        self.assertNotEqual(arithmetic["applied_operating_income"], "1660697.43375")
        self.assertNotEqual(arithmetic["applied_operating_income"], "1661075.1225")
        self.assertEqual(result["request"]["annual_observations"][-1]["data_kind"], "author_estimate")
        self.assertTrue(all(item["data_kind"] == "reported_fact" for item in result["request"]["annual_observations"][:-1]))
        self.assertEqual(result["adoption"], "unresolved")
        self.assertEqual(result["verification"]["source_references"], "unverified")

    def test_negative_and_zero_income_are_retained_without_tax_or_loss_adjustment(self):
        request = synthetic_request()
        request["annual_observations"][0]["operating_income"] = "-10"
        request["annual_observations"][1]["operating_income"] = "0"
        result = calculate_cyclical_margin(request)
        self.assertEqual(result["arithmetic"]["mean_operating_margin_ratio"], "-0.05")
        self.assertEqual(result["arithmetic"]["applied_operating_income"], "-15")
        self.assertEqual(result["arithmetic"]["period_count"], 2)
        request["annual_observations"][1]["operating_income"] = "20"
        zero = calculate_cyclical_margin(request)
        self.assertEqual(zero["arithmetic"]["applied_operating_income"], "0")

    def test_revenue_is_positive_explicit_decimal_and_missing_is_not_zero(self):
        invalid = (None, "-", "", "NaN", "Infinity", "0", "-1", True, 100, 100.0, "1,000", " 100", "1_000")
        for value in invalid:
            for path in ("observation", "application"):
                request = synthetic_request()
                target = request["annual_observations"][0] if path == "observation" else request["application_revenue"]
                target["revenue"] = value
                with self.subTest(value=value, path=path), self.assertRaises(ValueError):
                    calculate_cyclical_margin(request)
        for value in (None, "-", "NaN", True, 0, Decimal("0")):
            request = synthetic_request()
            request["annual_observations"][0]["operating_income"] = value
            with self.subTest(income=value), self.assertRaises(ValueError):
                calculate_cyclical_margin(request)

    def test_mixed_company_currency_unit_scope_accounting_and_concept_are_rejected(self):
        mutations = {"company_id": "other-company", "currency": "USD", "amount_unit": "billions",
                     "scope": "standalone", "accounting_basis": "different accounting", "profit_concept": "net_income"}
        for field, value in mutations.items():
            for target in ("observation", "application"):
                request = synthetic_request()
                row = request["annual_observations"][0] if target == "observation" else request["application_revenue"]
                row["basis"][field] = value
                with self.subTest(field=field, target=target), self.assertRaises(ValueError):
                    calculate_cyclical_margin(request)

    def test_method_is_explicit_and_weighted_or_displayed_margin_input_is_not_accepted(self):
        for method in (None, "sales_weighted", "arithmetic_mean", "", [], {}):
            request = synthetic_request()
            request["method"] = method
            with self.subTest(method=method), self.assertRaises(ValueError):
                calculate_cyclical_margin(request)
        request = synthetic_request()
        del request["method"]
        with self.assertRaises(ValueError):
            calculate_cyclical_margin(request)
        for field, value in (("weight", "0.5"), ("operating_margin", "0.1")):
            request = synthetic_request()
            request["annual_observations"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                calculate_cyclical_margin(request)

    def test_quarter_ytd_and_bad_enum_types_raise_regular_validation_errors(self):
        cases = [("period", "kind", value) for value in ("quarter", "YTD", "annual", [], {})]
        cases += [("row", "data_kind", value) for value in ("assumed_actual", [], {}, True)]
        cases += [("basis", "amount_unit", value) for value in ("percent", [], {})]
        cases += [("basis", "currency", value) for value in ("jpy", [], {})]
        for category, key, value in cases:
            request = synthetic_request()
            target = request["annual_observations"][0]
            if category == "period":
                target = target["period"]
            elif category == "basis":
                target = target["basis"]
            target[key] = value
            with self.subTest(category=category, key=key, value=value), self.assertRaises(ValueError):
                calculate_cyclical_margin(request)
        request = synthetic_request()
        request["application_revenue"]["period"]["kind"] = "quarter"
        with self.assertRaises(ValueError):
            calculate_cyclical_margin(request)

    def test_unknown_and_partial_dates_are_preserved_and_never_inferred(self):
        request = synthetic_request()
        request["annual_observations"][0]["period"] = period("unknown start", end="2023-12-31")
        request["annual_observations"][1]["period"] = period("unknown dates")
        result = calculate_cyclical_margin(request)
        self.assertIsNone(result["request"]["annual_observations"][0]["period"]["start"])
        self.assertIn("annual_observations[0].period.start", result["period_dates_incomplete"])
        self.assertIn("annual_observations[1].period.end", result["period_dates_incomplete"])
        self.assertEqual(result["verification"]["declared_annual_periods"], "unverified")

    def test_reversed_invalid_and_overlapping_known_history_is_rejected(self):
        for start, end in (("2023-12-31", "2023-01-01"), ("2023-02-29", "2023-12-31"),
                           ("2023-01-01T00:00:00Z", "2023-12-31")):
            request = synthetic_request()
            request["annual_observations"][0]["period"].update(start=start, end=end)
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                calculate_cyclical_margin(request)
        for start, end in (("2023-12-31", "2024-12-31"), ("2023-01-01", "2023-12-31"),
                           ("2022-01-01", "2025-01-01"), (None, "2023-12-31")):
            request = synthetic_request()
            request["annual_observations"][1]["period"].update(start=start, end=end)
            with self.subTest(start=start, end=end), self.assertRaisesRegex(ValueError, "overlapping"):
                calculate_cyclical_margin(request)

    def test_duplicate_id_and_period_labels_with_unknown_dates_are_rejected(self):
        for field in ("id", "label"):
            request = synthetic_request()
            if field == "id":
                request["annual_observations"][1]["id"] = request["annual_observations"][0]["id"]
            else:
                request["annual_observations"][1]["period"]["label"] = request["annual_observations"][0]["period"]["label"]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "Duplicate"):
                calculate_cyclical_margin(request)

    def test_52_53_week_declarations_remain_semantically_unverified(self):
        request = synthetic_request()
        request["annual_observations"][0]["period"] = period("52-week declaration", "2023-01-02", "2023-12-31")
        request["annual_observations"][1]["period"] = period("53-week declaration", "2024-01-01", "2025-01-05")
        result = calculate_cyclical_margin(request)
        self.assertEqual(result["verification"]["fiscal_year_duration_comparability"], "unverified")
        self.assertEqual(result["adoption"], "unresolved")
        self.assertTrue(any("52/53-week" in note for note in result["limitations"]))

    def test_gapped_single_period_and_unlisted_years_do_not_create_history(self):
        request = synthetic_request()
        request["annual_observations"][1]["period"] = period("gapped", "2026-01-01", "2026-12-31")
        result = calculate_cyclical_margin(request)
        self.assertEqual(result["arithmetic"]["period_count"], 2)
        request["annual_observations"] = request["annual_observations"][:1]
        result = calculate_cyclical_margin(request)
        self.assertEqual(result["arithmetic"]["period_count"], 1)
        self.assertEqual(result["verification"]["full_cycle_coverage"], "unverified")
        self.assertEqual(result["adoption"], "unresolved")

    def test_mixed_actual_guidance_and_author_estimate_keep_their_declared_status(self):
        request = synthetic_request()
        request["annual_observations"][0]["data_kind"] = "reported_fact"
        request["annual_observations"][1]["data_kind"] = "issuer_guidance"
        request["application_revenue"]["data_kind"] = "author_estimate"
        result = calculate_cyclical_margin(request)
        self.assertEqual(result["request"], request)
        self.assertEqual(result["adoption"], "unresolved")
        self.assertEqual(result["verification"]["source_references"], "unverified")

    def test_prose_and_complete_references_never_set_verification_true(self):
        request = toyota_request()
        for key in ("cycle_driver", "full_cycle_rationale", "comparability_rationale", "application_rationale"):
            request["assessment"][key] = "Caller claims the analysis is complete; do not adopt this assertion."
        result = calculate_cyclical_margin(request)
        self.assertEqual(result["assessment_fields_unset"], [])
        self.assertEqual(set(result["verification"].values()), {"unverified"})
        self.assertEqual(result["adoption"], "unresolved")
        for key in ("roc", "reinvestment", "wacc", "fcff", "price", "probabilities", "action"):
            self.assertNotIn(key, result)
            self.assertNotIn(key, result["arithmetic"])

    def test_unknown_or_approval_fields_rejected_in_all_contract_sections(self):
        mutations = [lambda r: r.update(approved=True),
                     lambda r: r["basis"].update(verified=True),
                     lambda r: r["assessment"].update(full_cycle_verified=True),
                     lambda r: r["annual_observations"][0].update(weight="1"),
                     lambda r: r["application_revenue"].update(price="1"),
                     lambda r: r["annual_observations"][0]["period"].update(annual_verified=True)]
        for mutate in mutations:
            request = synthetic_request()
            mutate(request)
            with self.subTest(mutation=mutations.index(mutate)), self.assertRaises(ValueError):
                calculate_cyclical_margin(request)
        request = toyota_request()
        request["annual_observations"][0]["source_refs"][0]["verified"] = True
        with self.assertRaises(ValueError):
            calculate_cyclical_margin(request)

    def test_missing_fields_and_empty_history_are_not_defaulted(self):
        for field in synthetic_request():
            request = synthetic_request()
            del request[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                calculate_cyclical_margin(request)
        request = synthetic_request()
        request["annual_observations"] = []
        with self.assertRaises(ValueError):
            calculate_cyclical_margin(request)
        request = synthetic_request()
        del request["annual_observations"][0]["operating_income"]
        with self.assertRaises(ValueError):
            calculate_cyclical_margin(request)

    def test_private_decimal_context_ignores_hostile_precision_traps_and_exponents(self):
        request = toyota_request()
        expected = calculate_cyclical_margin(request)
        with localcontext() as context:
            context.prec = 2
            context.rounding = ROUND_DOWN
            context.Emin, context.Emax = -2, 2
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            context.clear_flags()
            flags = context.flags.copy()
            actual = calculate_cyclical_margin(request)
            self.assertEqual(context.prec, 2)
            self.assertEqual(context.flags, flags)
        self.assertEqual(actual, expected)

    def test_scale_cancellation_preserves_small_signed_income_and_no_display_rounding(self):
        request = synthetic_request()
        request["annual_observations"] = [observation(str(i), "1", income)
                                          for i, income in enumerate(("1e1000", "-1e1000", "1e-1000", "0"))]
        request["application_revenue"]["revenue"] = "4"
        result = calculate_cyclical_margin(request)
        self.assertEqual(result["arithmetic"]["applied_operating_income"], format(Decimal("1e-1000"), "f"))
        self.assertGreater(result["calculation"]["working_precision_digits"], 2000)
        self.assertIsNone(result["calculation"]["display_quantization"])
        self.assertTrue(result["calculation"]["division_may_round"])

    def test_input_and_return_are_json_safe_and_original_request_is_not_mutated(self):
        request = toyota_request()
        before = deepcopy(request)
        result = calculate_cyclical_margin(request)
        self.assertEqual(request, before)
        self.assertEqual(result["request_sha256"], sha256(json_text(before).encode()).hexdigest())
        json.dumps(result, allow_nan=False)
        result["request"]["annual_observations"][0]["revenue"] = "1"
        self.assertEqual(request, before)

    def test_exclusions_and_source_reference_limits_preserve_missingness(self):
        request = synthetic_request()
        request["assessment"]["excluded_observations"] = [{
            "label": "unknown omitted period", "reason": "Synthetic unavailable history; no invented replacement.", "source_refs": []}]
        result = calculate_cyclical_margin(request)
        self.assertEqual(result["request"]["assessment"], request["assessment"])
        self.assertEqual(result["arithmetic"]["period_count"], 2)
        request["assessment"]["excluded_observations"][0]["label"] = "synthetic-fy1"
        with self.assertRaises(ValueError):
            calculate_cyclical_margin(request)
        for version, digest in ((True, "a" * 64), (1, "A" * 64), (1, [])):
            request = toyota_request()
            request["annual_observations"][0]["source_refs"][0].update(version=version, sha256=digest)
            with self.subTest(version=version, digest=digest), self.assertRaises(ValueError):
                calculate_cyclical_margin(request)

    def test_numeric_json_and_exponent_resource_failures_are_value_errors(self):
        for value in ("1e1001", "1e-1001", "9" * 257, float("inf"), Decimal("1"), {1: "bad key"}):
            request = synthetic_request()
            request["annual_observations"][0]["operating_income"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate_cyclical_margin(request)


if __name__ == "__main__":
    unittest.main()
