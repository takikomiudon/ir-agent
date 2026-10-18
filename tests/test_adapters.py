"""Credential-free adapter contract and source-provenance regression tests."""

import json
import io
import importlib
import unittest
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ir_agent.adapters import (
    DataAdapterError,
    fetch_edinet_documents,
    fetch_jquants_daily,
    normalize_edinet_document,
    normalize_jquants_daily,
    normalize_security_code,
    parse_edinet_package,
)

RETRIEVED = "2026-06-11T01:00:00+00:00"
LATER = "2026-06-12T01:00:00+00:00"


def master(code="130A0", name="架空サンプル株式会社"):
    return {"Code": code, "CoName": name, "Date": "2026-06-10", "S33": "5250", "ProdCat": "011"}


def bar(code="130A0", close=1234):
    return {"Code": code, "Date": "2026-06-10", "C": close, "AdjC": close, "Vo": 1000}


def filing(**updates):
    record = {
        "docID": "S100TEST",
        "docTypeCode": "120",
        "secCode": "130A0",
        "edinetCode": "E99999",
        "filerName": "架空サンプル株式会社",
        "docDescription": "有価証券報告書",
        "submitDateTime": "2026-06-10 15:34",
        "periodStart": "2025-04-01",
        "periodEnd": "2026-03-31",
    }
    record.update(updates)
    return record


class AdapterNormalizationTests(unittest.TestCase):
    def test_ordinary_security_codes_preserve_new_alphanumeric_tickers(self):
        for raw, expected in (("130A", "130A"), ("130A0", "130A"), ("1234", "1234"), (12340, "1234"), ("１３０ａ０", "130A")):
            with self.subTest(raw=raw):
                self.assertEqual(normalize_security_code(raw), expected)
        for raw in ("12345", "00000", None, True, 130.0, "../../", "ABCDE"):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    normalize_security_code(raw)

    def test_daily_bundle_keeps_raw_prices_without_guessing_publication_time(self):
        bundle = normalize_jquants_daily([master()], [bar()], retrieved_at=RETRIEVED)
        self.assertEqual(bundle["schema_version"], 1)
        self.assertEqual(bundle["companies"][0]["id"], "jp:130A")
        self.assertEqual(bundle["companies"][0]["security_code"], "130A")
        source = bundle["sources"][0]
        self.assertIsNone(source["published_at"])
        self.assertFalse(source["requires_research"])
        self.assertEqual(source["source_type"], "market_data")
        self.assertEqual(json.loads(source["content"])["C"], 1234)
        self.assertEqual(source["metadata"]["company_master"]["S33"], "5250")
        self.assertIn("code=130A0", source["url"])
        self.assertEqual(source["retrieved_at"], RETRIEVED)

    def test_same_content_deduplicates_across_retrieval_times(self):
        first = normalize_jquants_daily([master()], [bar(), bar()], retrieved_at=RETRIEVED)
        second = normalize_jquants_daily([master()], [bar()], retrieved_at=LATER)
        changed = normalize_jquants_daily([master()], [bar(close=1235)], retrieved_at=LATER)
        self.assertEqual(len(first["sources"]), 1)
        self.assertEqual(first["sources"][0]["id"], second["sources"][0]["id"])
        self.assertNotEqual(first["sources"][0]["id"], changed["sources"][0]["id"])

    def test_non_ordinary_shares_do_not_break_the_daily_batch(self):
        bundle = normalize_jquants_daily([master(), master(code="25935")], [bar(), bar(code="25935")], retrieved_at=RETRIEVED)
        self.assertEqual(len(bundle["companies"]), 1)
        self.assertEqual(len(bundle["sources"]), 1)
        self.assertEqual(bundle["skipped_security_codes"][0]["security_code"], "25935")
        self.assertEqual(bundle["skipped_security_codes"][0]["record_count"], 2)
        self.assertTrue(bundle["skipped_security_codes"][0]["reason"])

    def test_nan_missing_prices_are_json_null_not_zero(self):
        row = bar(close=float("nan"))
        source = normalize_jquants_daily([master()], [row], retrieved_at=RETRIEVED)["sources"][0]
        payload = json.loads(source["content"])
        self.assertIsNone(payload["C"])
        self.assertIsNone(payload["AdjC"])
        with self.assertRaises(ValueError):
            normalize_jquants_daily([master()], [bar(close=float("inf"))], retrieved_at=RETRIEVED)

    def test_datetime_trading_date_is_not_a_publication_timestamp(self):
        row = bar()
        row["Date"] = datetime(2026, 6, 10)
        source = normalize_jquants_daily([master()], [row], retrieved_at=RETRIEVED)["sources"][0]
        self.assertEqual(source["metadata"]["trading_date"], "2026-06-10")
        self.assertIsNone(source["published_at"])

    def test_normalizer_accepts_sdk_dataframe_protocol_without_importing_pandas(self):
        frames = [Mock(), Mock()]
        frames[0].to_dict.return_value = [master()]
        frames[1].to_dict.return_value = [bar()]
        bundle = normalize_jquants_daily(*frames, retrieved_at=RETRIEVED)
        self.assertEqual(len(bundle["sources"]), 1)
        for frame in frames:
            frame.to_dict.assert_called_once_with(orient="records")

    def test_no_company_name_or_master_match_is_fabricated(self):
        with self.assertRaises(ValueError):
            normalize_jquants_daily([master()], [bar(code="99990")], retrieved_at=RETRIEVED)
        with self.assertRaises(ValueError):
            normalize_jquants_daily([master(name="")], [], retrieved_at=RETRIEVED)
        with self.assertRaises(ValueError):
            normalize_jquants_daily([master(), master(name="異なる株式会社")], [], retrieved_at=RETRIEVED)

    def test_naive_retrieval_timestamp_is_rejected(self):
        for timestamp in ("2026-06-10T00:00:00", datetime(2026, 6, 10)):
            with self.assertRaises(ValueError):
                normalize_jquants_daily([master()], [], retrieved_at=timestamp)
        bundle = normalize_jquants_daily([master()], [bar()], retrieved_at=datetime(2026, 6, 10, tzinfo=timezone.utc))
        self.assertEqual(bundle["sources"][0]["retrieved_at"], "2026-06-10T00:00:00+00:00")

    def test_edinet_amendment_uses_submission_not_original_report_date(self):
        report = {"filing_date": "2025-06-10", "net_sales": None, "units": {}}
        bundle = normalize_edinet_document(filing(docTypeCode="130", docDescription="訂正有価証券報告書"), retrieved_at=RETRIEVED, parsed_report=report)
        source = bundle["sources"][0]
        self.assertEqual(source["published_at"], "2026-06-10T15:34:00+09:00")
        self.assertTrue(source["requires_research"])
        self.assertEqual(source["metadata"]["doc_type_code"], "130")
        self.assertEqual(source["metadata"]["period_end"], "2026-03-31")
        self.assertIsNone(json.loads(source["content"])["parsed_report"]["net_sales"])
        self.assertNotIn("Subscription-Key", source["url"])

    def test_edinet_date_only_or_absent_submission_remains_unknown(self):
        for value in (None, "", "2026-06-10"):
            with self.subTest(value=value):
                source = normalize_edinet_document(filing(submitDateTime=value), retrieved_at=RETRIEVED)["sources"][0]
                self.assertIsNone(source["published_at"])
        with self.assertRaises(ValueError):
            normalize_edinet_document(filing(submitDateTime="not-a-date"), retrieved_at=RETRIEVED)

    def test_edinet_no_stock_attribution_is_inferred_for_unlisted_filer(self):
        bundle = normalize_edinet_document(filing(secCode=None, docTypeCode="350", filerName="私募ファンド"), retrieved_at=RETRIEVED)
        self.assertEqual(bundle["companies"], [])
        self.assertEqual(bundle["sources"], [])
        self.assertEqual(bundle["skipped_documents"][0]["doc_id"], "S100TEST")

    def test_edinet_source_identity_changes_only_when_content_changes(self):
        first = normalize_edinet_document(filing(), retrieved_at=RETRIEVED)["sources"][0]
        later = normalize_edinet_document(filing(), retrieved_at=LATER)["sources"][0]
        changed = normalize_edinet_document(filing(docDescription="訂正"), retrieved_at=LATER)["sources"][0]
        self.assertEqual(first["id"], later["id"])
        self.assertNotEqual(first["id"], changed["id"])


class AdapterFetchTests(unittest.TestCase):
    def test_jquants_fetch_is_two_bulk_calls_not_a_call_per_company(self):
        client = SimpleNamespace(get_eq_master=Mock(return_value=[master()]), get_eq_bars_daily=Mock(return_value=[bar()]))
        bundle = fetch_jquants_daily("2026-06-10", client=client)
        client.get_eq_master.assert_called_once_with(date="2026-06-10")
        client.get_eq_bars_daily.assert_called_once_with(date_yyyymmdd="2026-06-10")
        self.assertEqual(len(bundle["companies"]), 1)

    def test_empty_market_day_keeps_master_without_fabricating_prices(self):
        client = SimpleNamespace(get_eq_master=Mock(return_value=[master()]), get_eq_bars_daily=Mock(return_value=[]))
        bundle = fetch_jquants_daily("2026-06-10", client=client)
        self.assertEqual(len(bundle["companies"]), 1)
        self.assertEqual(bundle["sources"], [])

    def test_edinet_fetch_passes_key_to_sdk_but_does_not_store_it(self):
        key = "fake-test-key-never-use-live"
        client = SimpleNamespace(fetch_documents_list=Mock(return_value={"metadata": {"status": "200"}, "results": [filing(), filing()]}))
        bundle = fetch_edinet_documents("2026-06-10", api_key=key, client=client)
        client.fetch_documents_list.assert_called_once_with("2026-06-10", type=2, api_key=key)
        self.assertEqual(len(bundle["sources"]), 1)
        self.assertNotIn(key, json.dumps(bundle))
        self.assertTrue(bundle["sources"][0]["metadata"]["index_only"])

    def test_edinet_empty_day_is_distinct_from_error_body(self):
        valid = SimpleNamespace(fetch_documents_list=Mock(return_value={"metadata": {"status": "200"}, "results": []}))
        self.assertEqual(fetch_edinet_documents("2026-06-10", client=valid)["sources"], [])
        for response in ({"StatusCode": 401, "results": []}, {"metadata": {"status": "429"}, "results": []}, {"metadata": {"status": "200"}}):
            with self.subTest(response=response):
                bad = SimpleNamespace(fetch_documents_list=Mock(return_value=response))
                with self.assertRaises(DataAdapterError):
                    fetch_edinet_documents("2026-06-10", client=bad)

    def test_edinet_skipped_stock_types_and_unlisted_filings_are_reported(self):
        response = {"metadata": {"status": "200"}, "results": [filing(), filing(docID="S100OTHER", secCode="25935"), filing(docID="S100FUND", secCode=None)]}
        client = SimpleNamespace(fetch_documents_list=Mock(return_value=response))
        bundle = fetch_edinet_documents("2026-06-10", client=client)
        self.assertEqual(len(bundle["sources"]), 1)
        self.assertEqual(bundle["skipped_security_codes"][0]["security_code"], "25935")
        self.assertEqual(bundle["skipped_documents"][0]["doc_id"], "S100FUND")

    def test_bad_dates_fail_before_any_sdk_access(self):
        for fetch in (fetch_jquants_daily, fetch_edinet_documents):
            client = Mock()
            for value in ("20260610", "2026-02-30", "2026-06-10&secret=bad"):
                with self.subTest(fetch=fetch.__name__, value=value):
                    with self.assertRaises(ValueError):
                        fetch(value, client=client)
            self.assertEqual(client.mock_calls, [])

    def test_sdk_failure_messages_do_not_expose_credentials(self):
        key = "fake-secret-key"
        clients = (
            (fetch_jquants_daily, SimpleNamespace(get_eq_master=Mock(side_effect=RuntimeError(key)))),
            (fetch_edinet_documents, SimpleNamespace(fetch_documents_list=Mock(side_effect=RuntimeError(key)))),
        )
        for fetch, client in clients:
            with self.subTest(fetch=fetch.__name__):
                with self.assertRaises(DataAdapterError) as caught:
                    fetch("2026-06-10", api_key=key, client=client)
                self.assertNotIn(key, str(caught.exception))
                self.assertTrue(caught.exception.__suppress_context__)

    def test_saved_package_parsing_preserves_decimal_units_and_narratives(self):
        @dataclass
        class Fact:
            element_id: str
            value: Decimal

        report = SimpleNamespace(
            to_dict=lambda: {"net_sales": Decimal("123456789.12"), "net_income_owners": None, "units": {"net_sales": "JPY"}, "raw_facts": [Fact("Revenue", Decimal("123456789.12"))]},
            text_blocks={"BusinessRisks": "価格転嫁が遅れるリスク。"},
            raw_fields={"Revenue": "123456789.12"},
            unmapped_fields={"OtherMetric": "7"},
        )
        parser = SimpleNamespace(parse_xbrl=Mock(return_value=report))
        bundle = parse_edinet_package(b"PK-test-placeholder", filing(), source="instance", parser=parser, retrieved_at=RETRIEVED)
        parser.parse_xbrl.assert_called_once_with(b"PK-test-placeholder", "120", source="instance", doc_id="S100TEST")
        source = bundle["sources"][0]
        payload = json.loads(source["content"])["parsed_report"]
        self.assertEqual(payload["net_sales"], "123456789.12")
        self.assertEqual(payload["units"]["net_sales"], "JPY")
        self.assertIsNone(payload["net_income_owners"])
        self.assertEqual(payload["text_blocks"]["BusinessRisks"], "価格転嫁が遅れるリスク。")
        self.assertFalse(source["metadata"]["index_only"])

    def test_package_parser_never_silently_falls_back(self):
        parser = SimpleNamespace(parse_xbrl=Mock(side_effect=ValueError("unsupported inline construct")))
        with self.assertRaises(DataAdapterError):
            parse_edinet_package(b"PK-test-placeholder", filing(), source="xbrl", parser=parser)
        self.assertEqual(parser.parse_xbrl.call_count, 1)
        with self.assertRaises(ValueError):
            parse_edinet_package(b"PK-test-placeholder", filing(), source="csv", parser=parser)
        with self.assertRaises(ValueError):
            parse_edinet_package(b"not-a-zip", filing(), parser=parser)


class OptionalSdkIntegrationTests(unittest.TestCase):
    """These tests use installed SDKs with local data, never remote endpoints."""

    def test_jquants_real_sdk_dataframe_conversion(self):
        try:
            sdk = importlib.import_module("jquantsapi")
        except ImportError:
            self.skipTest("optional jquants-api-client is not installed")
        raw_master = {key: None for key in sdk.constants.EQ_MASTER_COLUMNS_V2}
        raw_master.update(master())
        with patch.object(sdk.ClientV2, "_load_config", return_value={}):
            client = sdk.ClientV2(api_key="fake-offline-test-key")
        with patch.object(client, "_get_paginated", side_effect=[[raw_master], [bar()]]) as requests:
            bundle = fetch_jquants_daily("2026-06-10", client=client)
        self.assertEqual(requests.call_count, 2)
        self.assertEqual(bundle["companies"][0]["security_code"], "130A")
        self.assertEqual(json.loads(bundle["sources"][0]["content"])["C"], 1234)

    def test_edinet_real_sdk_reads_synthetic_instance_without_key(self):
        try:
            sdk = importlib.import_module("edinet_tools")
        except ImportError:
            self.skipTest("optional edinet-tools is not installed")
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
  xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
  xmlns:jppfs_cor="http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor">
  <xbrli:context id="CurrentYearDuration">
    <xbrli:entity><xbrli:identifier scheme="http://example.test/entity">E99999</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:startDate>2025-04-01</xbrli:startDate><xbrli:endDate>2026-03-31</xbrli:endDate></xbrli:period>
  </xbrli:context>
  <xbrli:unit id="JPY"><xbrli:measure>iso4217:JPY</xbrli:measure></xbrli:unit>
  <jppfs_cor:NetSales contextRef="CurrentYearDuration" unitRef="JPY" decimals="0">123456</jppfs_cor:NetSales>
</xbrli:xbrl>'''
        memory = io.BytesIO()
        with zipfile.ZipFile(memory, "w") as archive:
            archive.writestr("XBRL/PublicDoc/synthetic.xbrl", xml)
        bundle = parse_edinet_package(memory.getvalue(), filing(), source="instance", parser=sdk, retrieved_at=RETRIEVED)
        report = json.loads(bundle["sources"][0]["content"])["parsed_report"]
        self.assertEqual(report["doc_id"], "S100TEST")
        self.assertTrue(report["raw_facts"])
        self.assertEqual(report["raw_fields"]["jppfs_cor:NetSales"], "123456")


if __name__ == "__main__":
    unittest.main()
