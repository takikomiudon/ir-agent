"""Synthetic, credential-free tests of daily SDK financial-row ingestion."""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import importlib.util
import io
import json
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from ir_agent.adapters import (
    DataAdapterError, fetch_jquants_financial_summary,
    normalize_jquants_financial_summary,
)
from ir_agent.cli import main
from ir_agent.harness import Harness
from ir_agent.quotes import normalize_jquants_quote
from ir_agent.store import Store

RECEIVED = "2026-06-11T01:00:00+00:00"
LATER = "2026-06-12T01:00:00+00:00"
SCOPE = ["jp:130A"]


def synthetic_row(**updates):
    row = {
        "synthetic": True, "Code": "130A0", "DiscDate": "2026-06-10",
        "DiscTime": "15:30:00", "DiscNo": "SYNTHETIC-001",
        "DocType": "SyntheticFinancialStatement", "CurPerType": "1Q",
        "CurPerSt": "2026-04-01", "CurPerEn": "2026-06-30",
        "CurFYSt": "2026-04-01", "CurFYEn": "2027-03-31",
        "EPS": "1.2300", "FEPS": "4.50", "NCEPS": "2.3400",
        "FNCEPS": None, "CFO": "", "UnknownFutureColumn": "do not discard",
    }
    row.update(updates)
    return row


def normalize(rows, **kwargs):
    return normalize_jquants_financial_summary(rows, company_ids=SCOPE,
                                               retrieved_at=RECEIVED, **kwargs)


class FinancialSummaryNormalizationTests(unittest.TestCase):
    def test_raw_row_dates_forecasts_nonconsolidated_and_unknown_fields_stay_separate(self):
        row = synthetic_row()
        untouched = deepcopy(row)
        bundle = normalize([row])
        self.assertEqual(bundle["companies"], [])
        source = bundle["sources"][0]
        self.assertEqual(json.loads(source["content"]), untouched)
        self.assertEqual(row, untouched)
        self.assertIsNone(source["published_at"])
        self.assertEqual(source["retrieved_at"], RECEIVED)
        self.assertTrue(source["requires_research"])
        self.assertEqual(source["source_type"], "public_disclosure")
        self.assertEqual(source["metadata"]["provider"], "jquants_financials")
        self.assertEqual(source["metadata"]["dataset"], "fins/summary")
        self.assertFalse(source["metadata"]["financial_inputs_verified"])
        self.assertFalse(source["metadata"]["financial_units_or_meaning_interpreted"])
        self.assertTrue(source["metadata"]["synthetic"])
        self.assertNotIn("company_master", source["metadata"])
        self.assertNotIn("unit", source["metadata"])
        self.assertNotIn("forecast", source["metadata"])

    def test_explicit_scope_and_nonordinary_security_are_skipped_without_new_companies(self):
        bundle = normalize([synthetic_row(), synthetic_row(Code="58310"),
                            synthetic_row(Code="25935"), synthetic_row(Code="58310")])
        self.assertEqual([s["company_id"] for s in bundle["sources"]], SCOPE)
        skipped = {s["security_code"]: s for s in bundle["skipped_security_codes"]}
        self.assertEqual(skipped["5831"]["record_count"], 2)
        self.assertEqual(skipped["5831"]["reason_code"], "outside_explicit_company_scope")
        self.assertEqual(skipped["25935"]["reason_code"], "non_ordinary_security_code")
        self.assertEqual(bundle["companies"], [])

    def test_same_disclosure_number_changed_row_is_new_immutable_source(self):
        a = normalize([synthetic_row(), synthetic_row()])["sources"]
        later = normalize_jquants_financial_summary([synthetic_row()], company_ids=SCOPE, retrieved_at=LATER)
        revision = normalize([synthetic_row(FEPS="4.60")])["sources"][0]
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0]["id"], later["sources"][0]["id"])
        self.assertNotEqual(a[0]["id"], revision["id"])
        self.assertEqual(json.loads(a[0]["content"])["FEPS"], "4.50")

    def test_missing_nan_empty_string_dash_and_absent_column_are_not_zero(self):
        source = normalize([synthetic_row(NP=float("nan"), NCEPS=None, CFO="", FEPS="－",
                                          Sales=Decimal("12.3400"))])["sources"][0]
        row = json.loads(source["content"])
        self.assertIsNone(row["NP"])
        self.assertIsNone(row["NCEPS"])
        self.assertEqual(row["CFO"], "")
        self.assertEqual(row["FEPS"], "－")
        self.assertEqual(row["Sales"], "12.3400")
        self.assertNotIn("OP", row)
        with self.assertRaises(ValueError):
            normalize([synthetic_row(NP=float("inf"))])

    def test_required_code_and_target_disclosure_date_cannot_be_guessed(self):
        for updates in ({"Code": None}, {"Code": "bad"}, {"DiscDate": None},
                        {"DiscDate": "2026-02-30"}, {"DiscDate": "2026-06-10Tgarbage"}):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                normalize([synthetic_row(**updates)])

    def test_explicit_scope_must_be_nonempty_canonical_company_ids(self):
        for scope in ([], None, "jp:130A", {"jp:130A": True}, ["130A"], ["jp:130A0"], ["jp:25935"]):
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                normalize_jquants_financial_summary([], company_ids=scope, retrieved_at=RECEIVED)

    def test_empty_snapshot_does_not_create_financial_disclosures_or_companies(self):
        self.assertEqual(normalize([]), {"schema_version": 1, "companies": [], "sources": []})

    def test_financial_summary_is_rejected_by_existing_daily_quote_normalizer(self):
        source = normalize([synthetic_row(C=100, Date="2026-06-10")])["sources"][0]
        with self.assertRaisesRegex(ValueError, "daily-bar"):
            normalize_jquants_quote(source)

    def test_offline_dataframe_protocol_is_supported(self):
        frame = Mock()
        frame.to_dict.return_value = [synthetic_row()]
        self.assertEqual(len(normalize(frame)["sources"]), 1)
        frame.to_dict.assert_called_once_with(orient="records")


class FinancialSummaryFetchTests(unittest.TestCase):
    def test_single_daily_bulk_call_no_master_no_cursor_no_per_company_calls(self):
        client = Mock()
        client.get_fin_summary_cursor.return_value = ([synthetic_row(), synthetic_row(Code="58310")], "PRIVATE-CURSOR")
        bundle = fetch_jquants_financial_summary("2026-06-10", company_ids=[*SCOPE, "jp:5831"], client=client)
        self.assertEqual(client.mock_calls, [unittest.mock.call.get_fin_summary_cursor(date_yyyymmdd="2026-06-10")])
        self.assertEqual(len(bundle["sources"]), 2)
        self.assertEqual(bundle["companies"], [])
        self.assertNotIn("PRIVATE-CURSOR", json.dumps(bundle))

    def test_bad_date_and_empty_scope_fail_before_client_initialization_or_call(self):
        client = Mock()
        for date, scope in (("20260610", SCOPE), ("2026-02-30", SCOPE), ("2026-06-10", [])):
            with self.subTest(date=date, scope=scope), self.assertRaises(ValueError):
                fetch_jquants_financial_summary(date, company_ids=scope, client=client)
        self.assertEqual(client.mock_calls, [])
        if importlib.util.find_spec("jquantsapi"):
            with patch("jquantsapi.ClientV2") as factory:
                with self.assertRaises(ValueError):
                    fetch_jquants_financial_summary("2026-06-10", company_ids=[])
                factory.assert_not_called()

    def test_wrong_disclosure_day_stops_instead_of_importing_another_day(self):
        client = SimpleNamespace(get_fin_summary_cursor=Mock(return_value=([synthetic_row(DiscDate="2026-06-09")], None)))
        with self.assertRaisesRegex(DataAdapterError, "DiscDate"):
            fetch_jquants_financial_summary("2026-06-10", company_ids=SCOPE, client=client)

    def test_disclosure_datetime_preserved_as_sdk_value_without_publication_timezone(self):
        client = SimpleNamespace(get_fin_summary_cursor=Mock(return_value=([
            synthetic_row(DiscDate=datetime(2026, 6, 10), DiscTime=None)], None)))
        source = fetch_jquants_financial_summary("2026-06-10", company_ids=SCOPE, client=client)["sources"][0]
        self.assertEqual(json.loads(source["content"])["DiscDate"], "2026-06-10T00:00:00")
        self.assertIsNone(source["published_at"])
        self.assertEqual(source["metadata"]["disclosure_date"], "2026-06-10")

    def test_retrieval_clock_is_sampled_after_sdk_returns(self):
        events = []
        def sdk(**kwargs):
            events.append("SDK return")
            return [synthetic_row()], None
        def clock(value=None):
            events.append("receipt clock")
            return RECEIVED
        with patch("ir_agent.adapters.jquants_financials.retrieval_timestamp", side_effect=clock):
            bundle = fetch_jquants_financial_summary("2026-06-10", company_ids=SCOPE,
                                                    client=SimpleNamespace(get_fin_summary_cursor=sdk))
        self.assertEqual(events[:2], ["SDK return", "receipt clock"])
        self.assertEqual(bundle["sources"][0]["retrieved_at"], RECEIVED)

    def test_empty_day_and_bad_sdk_result_are_distinct(self):
        good = SimpleNamespace(get_fin_summary_cursor=Mock(return_value=([], None)))
        self.assertEqual(fetch_jquants_financial_summary("2026-06-10", company_ids=SCOPE, client=good)["sources"], [])
        for response in ([], None, ([synthetic_row()],), ([synthetic_row()], None, None)):
            with self.subTest(response=response), self.assertRaises(DataAdapterError):
                fetch_jquants_financial_summary("2026-06-10", company_ids=SCOPE,
                                                client=SimpleNamespace(get_fin_summary_cursor=Mock(return_value=response)))

    def test_sdk_failure_does_not_expose_credentials_or_exception_message(self):
        key = "synthetic-secret-key-never-use-live"
        client = SimpleNamespace(get_fin_summary_cursor=Mock(side_effect=RuntimeError(key)))
        with self.assertRaises(DataAdapterError) as error:
            fetch_jquants_financial_summary("2026-06-10", company_ids=SCOPE, api_key=key, client=client)
        self.assertNotIn(key, str(error.exception))
        self.assertNotIn("RuntimeError", str(error.exception))
        if importlib.util.find_spec("jquantsapi"):
            with patch("jquantsapi.ClientV2", side_effect=RuntimeError(key)):
                with self.assertRaises(DataAdapterError) as error:
                    fetch_jquants_financial_summary("2026-06-10", company_ids=SCOPE, api_key=key)
                self.assertNotIn(key, str(error.exception))

    @unittest.skipUnless(importlib.util.find_spec("jquantsapi"), "optional J-Quants SDK unavailable")
    def test_installed_sdk_dataframe_and_internal_pagination_preserve_all_columns(self):
        # Entire payload is synthetic; only the installed SDK transformation
        # runs. _get below is an in-memory fake, never an HTTP client.
        from jquantsapi import constants
        from jquantsapi.apis.v2.fins import FinSummaryApiV2
        raw = {key: None for key in constants.FIN_SUMMARY_COLUMNS_V2}
        raw.update({k: v for k, v in synthetic_row().items() if k in raw})
        transport = SimpleNamespace(JQUANTS_API_BASE="https://synthetic.invalid/v2", _get=Mock(side_effect=[
            SimpleNamespace(json=lambda: {"data": [raw], "pagination_key": "SYNTHETIC-PAGE"}),
            SimpleNamespace(json=lambda: {"data": [], "cursor": "SYNTHETIC-CURSOR"})]))
        client = SimpleNamespace(get_fin_summary_cursor=Mock(side_effect=lambda **kw: FinSummaryApiV2().execute(transport, **kw)))
        source = fetch_jquants_financial_summary("2026-06-10", company_ids=SCOPE, client=client)["sources"][0]
        client.get_fin_summary_cursor.assert_called_once_with(date_yyyymmdd="2026-06-10")
        self.assertEqual(transport._get.call_count, 2)
        row = json.loads(source["content"])
        self.assertEqual(set(row), set(constants.FIN_SUMMARY_COLUMNS_V2))
        self.assertEqual(row["DiscDate"], "2026-06-10T00:00:00")
        self.assertEqual(row["FEPS"], "4.50")
        self.assertIsNone(row["FNCEPS"])
        self.assertNotIn("SYNTHETIC-CURSOR", source["content"])


class FinancialSummaryCliTests(unittest.TestCase):
    def test_opt_in_uses_existing_scope_and_preserves_company_rows_and_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.sqlite3"
            store = Store(str(path))
            harness = Harness(store)
            companies = [{"id": "jp:130A", "security_code": "130A", "name": "架空A社", "status": "watch", "held": False},
                         {"id": "jp:5831", "security_code": "5831", "name": "架空B社", "status": "excluded", "held": True,
                          "screening_reason": "synthetic preservation test"}]
            harness.ingest({"schema_version": 1, "companies": companies, "sources": []})
            before = store.companies()
            store.close()
            def offline_fetch(date, *, company_ids):
                self.assertEqual(date, "2026-06-10")
                self.assertEqual(company_ids, ["jp:130A", "jp:5831"])
                return normalize_jquants_financial_summary([synthetic_row(), synthetic_row(Code="99990")],
                                                           company_ids=company_ids, retrieved_at=RECEIVED)
            with patch("ir_agent.adapters.fetch_jquants_financial_summary", side_effect=offline_fetch) as fetch:
                for expected_added in (1, 0):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        code = main(["--db", str(path), "sync", "--provider", "jquants-financials", "--date", "2026-06-10"])
                    self.assertEqual(code, 0, stderr.getvalue())
                    result = json.loads(stdout.getvalue())
                    self.assertEqual(result["sources_added"], expected_added)
                    self.assertEqual(result["companies"], 0)
                    self.assertEqual(result["skipped_security_codes"][0]["security_code"], "9999")
                self.assertEqual(fetch.call_count, 2)
            store = Store(str(path))
            self.assertEqual(store.companies(), before)
            self.assertEqual(len(store.sources("jp:130A")), 1)
            store.close()

    def test_empty_cli_scope_reports_error_before_sdk_call(self):
        with tempfile.TemporaryDirectory() as directory:
            if importlib.util.find_spec("jquantsapi"):
                with patch("jquantsapi.ClientV2") as factory:
                    out, err = io.StringIO(), io.StringIO()
                    with redirect_stdout(out), redirect_stderr(err):
                        code = main(["--db", str(Path(directory) / "synthetic.sqlite3"), "sync", "--provider", "jquants-financials", "--date", "2026-06-10"])
                    self.assertEqual(code, 1)
                    self.assertEqual(out.getvalue(), "")
                    self.assertIn("nonempty existing company scope", err.getvalue())
                    factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
