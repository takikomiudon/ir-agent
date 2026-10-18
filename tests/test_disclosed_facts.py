"""Verbatim evidence, unit arithmetic and unset meaning remain separate."""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Inexact, Rounded, localcontext
import hashlib
import json
from pathlib import Path
import unittest

from ir_agent.disclosed_facts import normalize_disclosed_facts
from ir_agent.harness import Harness
from ir_agent.store import Store


NOW = "2026-10-15T01:00:00+00:00"
LATER = "2026-10-15T02:00:00+00:00"


def request(raw="1,234.50", raw_unit="百万円", unit="JPY", *, kind="reported_fact", quote=None):
    quote = quote or f"2026年度（単位：{raw_unit}）公表値 {raw if raw is not None else '未記載'}。"
    return {
        "company_id": "jp:130A",
        "source": {"id": "saved-source", "company_id": "jp:130A", "title": "保存済み公表資料",
                   "url": "https://issuer.example/ir/financial", "source_type": "public_disclosure",
                   "published_at": None, "retrieved_at": "2026-10-15T00:00:00+00:00", "content": quote,
                   "requires_research": True, "metadata": {"publication_date": "2026-10-14"}},
        "review": {"author": "named-reviewer", "recorded_at": "2026-10-15T00:10:00+00:00",
                   "rationale": "原文のラベルを保持。列・主体・概念対応は追加の意味確認が必要。"},
        "facts": [{"id": "fact-1", "concept": "disclosed_example_value", "kind": kind, "raw_value": raw,
                   "raw_unit_label": raw_unit, "unit": unit, "raw_period_label": "2026年度",
                   "period": {"label": "2026年度"}, "basis_quote": quote,
                   "definition": "抽出担当者が主張する公表値の定義。自動確認ではない。",
                   "scope": {"company_id": "jp:130A", "consolidation": "consolidated"}}],
    }


def facts(result):
    return json.loads(result["sources"][1]["content"])["facts"]


class DisclosedFactsTests(unittest.TestCase):
    def test_original_unchanged_and_derived_values_bind_to_json_with_raw_lineage(self):
        value = request()
        original = deepcopy(value)
        result = normalize_disclosed_facts(value, now=NOW)
        self.assertEqual(value, original)
        self.assertEqual(result["sources"][0], original["source"])
        self.assertIsNot(result["sources"][0], value["source"])
        self.assertEqual(result["companies"], [])
        self.assertEqual(result["theses"], [])
        raw, derived = result["sources"]
        parsed = json.loads(derived["content"])
        self.assertNotEqual(raw["id"], derived["id"])
        self.assertEqual(parsed["facts"][0]["value"], "1234500000.00")
        self.assertEqual(parsed["facts"][0]["raw_value"], "1,234.50")
        self.assertEqual(parsed["facts"][0]["basis_quote"], raw["content"])
        self.assertEqual(parsed["review"], original["review"])
        self.assertEqual(derived["metadata"]["original_source_id"], raw["id"])
        self.assertEqual(derived["metadata"]["original_source_content_sha256"], hashlib.sha256(raw["content"].encode()).hexdigest())
        self.assertEqual(derived["retrieved_at"], NOW)
        self.assertFalse(derived["metadata"]["financial_inputs_verified"])
        self.assertTrue(derived["metadata"]["meaning_review_required"])

    def test_only_explicit_unit_pairs_convert_without_inferring_a_financial_concept(self):
        cases = [("10", "JPY", "JPY", "10"), ("10", "円", "JPY", "10"),
                 ("10", "千円", "JPY", "10000"), ("10", "百万円", "JPY", "10000000"),
                 ("64.0", "円", "JPY-per-share", "64.0"), ("32.0", "円/株", "JPY-per-share", "32.0"),
                 ("41.1", "%", "ratio", "0.411"), ("8", "％", "ratio", "0.08"),
                 ("0.08", "ratio", "ratio", "0.08")]
        for raw, label, unit, expected in cases:
            with self.subTest(label=label, unit=unit):
                item = facts(normalize_disclosed_facts(request(raw, label, unit), now=NOW))[0]
                self.assertEqual(item["value"], expected)
                self.assertEqual(item["unit"], unit)
                self.assertEqual(item["concept"], "disclosed_example_value")
                self.assertTrue(item["meaning_review_required"])
                self.assertFalse(item["financial_inputs_verified"])

    def test_ascii_and_triangle_negative_signs_and_regular_comma_groups(self):
        for raw, expected in (("△1,234.50", "-1234.50"), ("▲1,000", "-1000"), ("-12.5", "-12.5"),
                              ("+12.5", "12.5"), ("0", "0"), ("-0.00", "0")):
            with self.subTest(raw=raw):
                self.assertEqual(facts(normalize_disclosed_facts(request(raw, "円"), now=NOW))[0]["value"], expected)

    def test_dash_empty_and_none_are_null_instead_of_zero(self):
        for raw in ("-", "－", "—", "–", "―", "", " ", None):
            with self.subTest(raw=raw):
                item = facts(normalize_disclosed_facts(request(raw), now=NOW))[0]
                self.assertIsNone(item["value"])
                self.assertFalse(item["normalization"]["raw_numeric_token_verified"])

    def test_malformed_numbers_and_unknown_words_are_never_coerced(self):
        for raw in ("1,00", "12,34,567", "1234,567", "1e3", ".5", "NaN", "Infinity", "不明", "N/A", "△-1", "12 円"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalize_disclosed_facts(request(raw), now=NOW)
        for raw in (0, 12.5, True, {}, []):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalize_disclosed_facts(request(raw), now=NOW)

    def test_quote_labels_and_full_numeric_token_must_be_in_one_exact_quote(self):
        for raw, quote in (("8", "2026年度（単位：百万円）値18。"), ("8", "2026年度（単位：百万円）値8.0。"),
                           ("8", "2026年度（単位：百万円）値8e3。"), ("-", "2026年度（単位：百万円）2026-03-31。")):
            with self.subTest(raw=raw, quote=quote), self.assertRaisesRegex(ValueError, "token"):
                normalize_disclosed_facts(request(raw, quote=quote), now=NOW)
        for field, value in (("basis_quote", "資料にない引用"), ("raw_unit_label", "千円"), ("raw_period_label", "2027年度")):
            bad = request()
            bad["facts"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                normalize_disclosed_facts(bad, now=NOW)

    def test_wrong_company_source_or_duplicate_fact_id_is_rejected(self):
        variants = []
        bad = request(); bad["company_id"] = "jp:9999"; variants.append(bad)
        bad = request(); bad["facts"][0]["company_id"] = "jp:9999"; variants.append(bad)
        bad = request(); bad["facts"][0]["scope"]["company_id"] = "jp:9999"; variants.append(bad)
        bad = request(); bad["facts"][0]["source_id"] = "other-source"; variants.append(bad)
        bad = request(); bad["facts"].append(deepcopy(bad["facts"][0])); variants.append(bad)
        for bad in variants:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                normalize_disclosed_facts(bad, now=NOW)

    def test_future_source_future_review_or_review_before_retrieval_is_rejected(self):
        variants = []
        bad = request(); bad["source"]["retrieved_at"] = LATER; variants.append(bad)
        bad = request(); bad["review"]["recorded_at"] = LATER; variants.append(bad)
        bad = request(); bad["review"]["recorded_at"] = "2026-10-14T23:59:00+00:00"; variants.append(bad)
        bad = request(); bad["source"]["published_at"] = LATER; variants.append(bad)
        for bad in variants:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                normalize_disclosed_facts(bad, now=NOW)
        with self.assertRaises(ValueError):
            normalize_disclosed_facts(request(), now=datetime(2026, 10, 15))

    def test_guidance_period_descriptor_is_preserved_without_building_future_series(self):
        value = request("64.0", "円", "JPY-per-share", kind="issuer_guidance")
        value["facts"][0]["period"] = {"raw_label": "2026年度", "fiscal_year_end_month": "2027-03"}
        result = normalize_disclosed_facts(value, now=NOW)
        item = facts(result)[0]
        self.assertEqual(item["kind"], "issuer_guidance")
        self.assertEqual(item["period"], value["facts"][0]["period"])
        self.assertNotIn("start_date", item["period"])
        self.assertNotIn("end_date", item["period"])
        self.assertNotIn("dividends_per_share_jpy", result["sources"][1]["content"])
        self.assertEqual(result["theses"], [])

    def test_bad_unit_descriptor_kind_and_reference_page_are_rejected(self):
        for field, value in (("unit", "USD"), ("raw_unit_label", "千円"), ("period", {}), ("period", "2026"),
                             ("scope", {}), ("definition", ""), ("kind", "analyst_forecast"), ("kind", {}),
                             ("location", {"pdf_page": 2})):
            bad = request()
            bad["facts"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                normalize_disclosed_facts(bad, now=NOW)
        with self.assertRaises(ValueError):
            normalize_disclosed_facts(request("8", "千円", "ratio"), now=NOW)

    def test_general_explanation_requires_null_or_numeric_token_and_keeps_text_in_definition(self):
        value = request(None, kind="general_explanation")
        result = normalize_disclosed_facts(value, now=NOW)
        self.assertIsNone(facts(result)[0]["value"])
        self.assertEqual(facts(result)[0]["definition"], value["facts"][0]["definition"])
        with self.assertRaises(ValueError):
            normalize_disclosed_facts(request("説明文", kind="general_explanation"), now=NOW)

    def test_id_is_stable_and_first_retrieval_can_be_preserved_on_reingest(self):
        value = request()
        one = normalize_disclosed_facts(value, now=NOW)
        two = normalize_disclosed_facts(value, now=LATER)
        self.assertEqual(one["sources"][1]["id"], two["sources"][1]["id"])
        self.assertEqual(one["sources"][1]["metadata"], two["sources"][1]["metadata"])
        self.assertEqual(one["sources"][1]["content"], two["sources"][1]["content"])
        self.assertNotEqual(one["sources"][1]["retrieved_at"], two["sources"][1]["retrieved_at"])
        store = Store(":memory:")
        self.addCleanup(store.close)
        harness = Harness(store)
        harness.ingest({"schema_version": 1, "companies": [{"id": "jp:130A", "name": "架空企業"}]})
        harness.ingest(one)
        self.assertEqual(harness.ingest(two)["sources_added"], 0)
        self.assertEqual(store.source(one["sources"][1]["id"])["retrieved_at"], NOW)
        changed = deepcopy(value)
        changed["review"]["rationale"] += " 別レビュー。"
        self.assertNotEqual(normalize_disclosed_facts(changed, now=LATER)["sources"][1]["id"], one["sources"][1]["id"])

    def test_numeric_normalization_is_private_and_does_not_change_caller_decimal_state(self):
        value = request("1,234.56789", "千円", "JPY")
        original = deepcopy(value)
        with localcontext() as context:
            context.prec = 2
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            result = normalize_disclosed_facts(value, now=datetime(2026, 10, 15, 1, tzinfo=timezone.utc))
            self.assertFalse(context.flags[Inexact])
            self.assertFalse(context.flags[Rounded])
        self.assertEqual(facts(result)[0]["value"], "1234567.89000")
        self.assertEqual(value, original)

    def test_synthetic_example_keeps_regulatory_capital_distinct_from_equity_cost(self):
        path = Path(__file__).parents[1] / "examples/disclosed-facts.json"
        result = normalize_disclosed_facts(json.loads(path.read_text()), now=NOW)
        disclosed = facts(result)
        self.assertEqual([x["value"] for x in disclosed], ["63000000000", "27.45", "0.08"])
        self.assertEqual(disclosed[2]["concept"], "disclosed_regulatory_capital_ratio")
        self.assertFalse(result["sources"][1]["metadata"]["financial_inputs_verified"])
        self.assertTrue(result["sources"][1]["metadata"]["synthetic"])


if __name__ == "__main__":
    unittest.main()
