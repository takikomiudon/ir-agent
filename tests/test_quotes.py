"""Offline raw-bar price, issuer and date-precision contract regressions."""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import unittest

from ir_agent.adapters.jquants import normalize_jquants_daily
from ir_agent.decision import _source_field
from ir_agent.models import timestamp, validate_source
from ir_agent.quotes import normalize_jquants_quote


def source(**updates):
    row = {"Code": "130A0", "Date": "2026-06-10", "C": "1234.50", "AdjC": "617.25", "Vo": 1000}
    row.update(updates)
    return normalize_jquants_daily(
        [{"Code": "130A0", "CoName": "架空サンプル株式会社"}], [row],
        retrieved_at="2026-06-11T01:00:00+00:00",
    )["sources"][0]


class JQuantsQuoteTests(unittest.TestCase):
    def test_raw_close_is_bound_to_separate_derived_snapshot_without_mutating_source(self):
        original = source()
        before = deepcopy(original)
        normalized = normalize_jquants_quote(original)
        quote = normalized["quote"]
        raw, derived = normalized["sources"]
        self.assertEqual(original, before)
        self.assertEqual(raw, before)
        self.assertIsNot(raw, original)
        self.assertNotEqual(derived["id"], raw["id"])
        validate_source(derived)
        self.assertEqual(quote["source_id"], derived["id"])
        self.assertEqual(quote["company_id"], "jp:130A")
        self.assertEqual(quote["currency"], "JPY")
        self.assertEqual(quote["price_jpy"], "1234.50")
        self.assertEqual(_source_field(derived, quote["price_path"]), quote["price_jpy"])
        self.assertEqual(_source_field(derived, quote["observed_at_path"]), quote["observed_at"])
        self.assertEqual(quote["retrieved_at"], raw["retrieved_at"])
        self.assertEqual(json.loads(derived["content"])["raw_record"], json.loads(raw["content"]))
        self.assertEqual(derived["metadata"]["original_source_id"], raw["id"])
        self.assertEqual(derived["metadata"]["original_price_field"], "C")
        derived["metadata"]["original_source_id"] = "modified-copy"
        raw["metadata"]["trading_date"] = "modified-copy"
        self.assertEqual(original, before)

    def test_daily_precision_is_not_fabricated_close_or_publication_time(self):
        normalized = normalize_jquants_quote(source())
        quote, derived = normalized["quote"], normalized["sources"][1]
        self.assertEqual(quote["observed_at"], "2026-06-10T00:00:00+09:00")
        self.assertEqual(quote["observation_precision"], "day")
        self.assertEqual(quote["observation_basis"], "date_lower_bound")
        self.assertEqual(derived["metadata"]["observation_precision"], "day")
        self.assertFalse(derived["metadata"]["publication_time_known"])
        self.assertIsNone(derived["published_at"])
        # The lower bound overstates age instead of pretending to be 15:30.
        age = timestamp(quote["retrieved_at"]) - timestamp(quote["observed_at"])
        self.assertEqual(age.total_seconds(), 34 * 3600)
        self.assertTrue(normalized["limitations"])

    def test_stable_identity_excludes_retrieval_time_but_includes_raw_content(self):
        first = source()
        later = deepcopy(first)
        later["retrieved_at"] = "2026-06-12T01:00:00+00:00"
        first_result = normalize_jquants_quote(first)
        later_result = normalize_jquants_quote(later)
        self.assertEqual(first_result["sources"][1]["id"], later_result["sources"][1]["id"])
        self.assertNotEqual(first_result["quote"]["retrieved_at"], later_result["quote"]["retrieved_at"])
        changed = normalize_jquants_quote(source(C="1234.51"))
        self.assertNotEqual(first_result["sources"][1]["id"], changed["sources"][1]["id"])

    def test_missing_close_never_falls_back_to_adjusted_close(self):
        for value in (None, 0, -1, False, "NaN", "Infinity", "", {}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_jquants_quote(source(C=value))
        original = source()
        row = json.loads(original["content"])
        del row["C"]
        original["content"] = json.dumps(row)
        with self.assertRaises(ValueError):
            normalize_jquants_quote(original)
        with self.assertRaises(ValueError):
            normalize_jquants_quote(source(), price_field="AdjC")

    def test_zero_or_negative_volume_cannot_supply_a_tradable_bar(self):
        for volume in (0, "0", -1, False, "NaN"):
            with self.subTest(volume=volume):
                with self.assertRaises(ValueError):
                    normalize_jquants_quote(source(Vo=volume))
        # Some saved API rows omit volume; do not invent a volume/status.
        original = source()
        row = json.loads(original["content"])
        del row["Vo"]
        original["content"] = json.dumps(row)
        self.assertEqual(normalize_jquants_quote(original)["quote"]["price_jpy"], "1234.50")

    def test_issuer_master_date_and_currency_contradictions_are_rejected(self):
        original = source()
        cases = []
        other_company = deepcopy(original)
        other_company["company_id"] = "jp:9999"
        cases.append(other_company)
        other_master = deepcopy(original)
        other_master["metadata"]["company_master"]["Code"] = "99990"
        cases.append(other_master)
        other_date = deepcopy(original)
        other_date["metadata"]["trading_date"] = "2026-06-09"
        cases.append(other_date)
        for location in ("metadata", "master", "raw"):
            other_currency = deepcopy(original)
            if location == "metadata":
                other_currency["metadata"]["currency"] = "USD"
            elif location == "master":
                other_currency["metadata"]["company_master"]["Currency"] = "USD"
            else:
                row = json.loads(original["content"])
                row["Currency"] = "USD"
                other_currency["content"] = json.dumps(row)
            cases.append(other_currency)
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_jquants_quote(value)

    def test_only_saved_jquants_v2_market_data_sources_are_accepted(self):
        for change in ({"source_type": "public_disclosure"}, {"metadata": {}}, {"content": "not JSON"}, {"content": "[]"}):
            with self.subTest(change=change):
                original = source()
                original.update(change)
                with self.assertRaises(ValueError):
                    normalize_jquants_quote(original)
        original = source()
        original["metadata"]["dataset"] = "prices/daily_quotes"
        with self.assertRaises(ValueError):
            normalize_jquants_quote(original)

    def test_future_trading_day_is_rejected_using_jst_not_utc_date(self):
        original = source()
        original["retrieved_at"] = "2026-06-09T14:59:59+00:00"
        with self.assertRaises(ValueError):
            normalize_jquants_quote(original)
        # 15:00 UTC is already the next JST day. No close time is inferred.
        original["retrieved_at"] = "2026-06-09T15:00:00+00:00"
        quote = normalize_jquants_quote(original)["quote"]
        self.assertEqual(timestamp(quote["observed_at"]), timestamp(quote["retrieved_at"]))

    def test_pandas_style_date_does_not_become_an_exact_observation(self):
        quote = normalize_jquants_quote(source(Date=datetime(2026, 6, 10)))["quote"]
        self.assertEqual(quote["trading_date"], "2026-06-10")
        self.assertEqual(quote["observed_at"], "2026-06-10T00:00:00+09:00")
        self.assertEqual(quote["observation_precision"], "day")

    def test_duplicate_json_keys_cannot_shadow_a_saved_price(self):
        original = source()
        original["content"] = '{"Code":"130A0","Date":"2026-06-10","C":1234,"C":1}'
        with self.assertRaisesRegex(ValueError, "duplicate"):
            normalize_jquants_quote(original)

    def test_decimal_price_precision_is_preserved(self):
        quote = normalize_jquants_quote(source(C=Decimal("1234.1234567890123456789")))["quote"]
        self.assertEqual(quote["price_jpy"], "1234.1234567890123456789")

    def test_offline_example_is_a_source_not_an_asserted_live_quote(self):
        original = json.loads((Path(__file__).parents[1] / "examples" / "quote-source.json").read_text())
        result = normalize_jquants_quote(original)
        self.assertTrue(original["metadata"]["synthetic"])
        self.assertTrue(result["sources"][1]["metadata"]["synthetic"])
        self.assertEqual(result["quote"]["price_jpy"], "1000")
        self.assertEqual(result["quote"]["observation_precision"], "day")


if __name__ == "__main__":
    unittest.main()
