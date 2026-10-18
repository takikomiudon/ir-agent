"""Catalog-to-SQLite contact integration; no company communication or network."""

from copy import deepcopy
import csv
import json
from pathlib import Path
import tempfile
import unittest

from ir_agent.harness import Harness
from ir_agent.store import Store
from test_contacts import IMPORTED, VERIFIED, row


LATER_IMPORT = "2026-10-16T10:30:00+09:00"


class ContactWorkflowTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "research.sqlite3"
        self.catalog = Path(directory.name) / "contacts.csv"
        self.store = Store(self.path)
        self.addCleanup(lambda: self.store.close())
        self.harness = Harness(self.store)

    def write_catalog(self, rows):
        with self.catalog.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(row()))
            writer.writeheader()
            writer.writerows(rows)
        return str(self.catalog)

    def import_rows(self, rows, *, imported_at=IMPORTED, dry_run=False):
        return self.harness.import_contacts(self.write_catalog(rows), imported_at, dry_run=dry_run)

    def snapshot(self):
        return "\n".join(self.store.connection.iterdump())

    def seed_existing_company(self):
        original = {
            "id": "jp:130A", "security_code": "130A", "name": "利用者が確認した社名",
            "status": "active", "held": True, "screening_reason": "利用者が承認した調査対象",
            "portfolio_note": "既存の個別メモも保持する",
        }
        self.harness.ingest({"schema_version": 1, "companies": [deepcopy(original)]})
        return original

    def test_dry_run_reports_valid_candidates_without_any_database_change(self):
        self.seed_existing_company()
        before = self.snapshot()
        changes = self.store.connection.total_changes
        result = self.import_rows([row(), row("1234")], dry_run=True)
        self.assertEqual(result["status"], "dry_run")
        self.assertEqual(result["summary"]["accepted_rows"], 2)
        self.assertEqual(result["summary"]["rejected_rows"], 0)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.store.connection.total_changes, changes)

    def test_one_invalid_row_holds_entire_import_including_valid_updates_and_inserts(self):
        self.seed_existing_company()
        self.import_rows([row()])
        before = self.snapshot()
        changes = self.store.connection.total_changes
        changed = row(conditions='["変更された受付条件"]')
        result = self.import_rows([changed, row("1234"), row("5678", channel_status="provisional")])
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["summary"]["accepted_rows"], 2)
        self.assertEqual(result["summary"]["rejected_rows"], 1)
        self.assertEqual(result["rejected_rows"][0]["security_code"], "5678")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.store.connection.total_changes, changes)
        self.assertEqual([x["id"] for x in self.store.companies()], ["jp:130A"])

    def test_duplicate_quarantine_holds_unrelated_valid_company_as_well(self):
        before = self.snapshot()
        result = self.import_rows([row(), row(company_name="重複行の別名"), row("1234")])
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["summary"]["accepted_rows"], 1)
        self.assertEqual(result["summary"]["rejected_rows"], 2)
        self.assertEqual(result["summary"]["duplicate_codes"], ["130A"])
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.store.companies(), [])

    def test_import_adds_contact_without_overwriting_existing_name_holdings_or_status(self):
        original = self.seed_existing_company()
        result = self.import_rows([row(company_name="カタログ上の別表記")])
        self.assertEqual(result["status"], "imported")
        self.assertEqual(result["companies_updated"], 1)
        saved = self.store.company("jp:130A")
        self.assertEqual({k: saved[k] for k in original}, original)
        self.assertEqual(saved["ir_contact"]["verified_at"], VERIFIED)
        self.assertEqual(saved["ir_contact"]["imported_at"], IMPORTED)
        self.assertEqual(saved["ir_contact"]["conditions"], ["返信の無断転載禁止", "回答を約束しない"])
        self.assertEqual(saved["ir_contact"]["provenance"]["csv_row_number"], 2)

    def test_new_company_is_watch_without_financial_sources_theses_or_jobs(self):
        result = self.import_rows([row()])
        self.assertEqual(result["status"], "imported")
        company = self.store.company("jp:130A")
        self.assertEqual(company["status"], "watch")
        self.assertFalse(company["held"])
        self.assertEqual(company["ir_contact"]["individual_access"], "explicit")
        self.assertEqual(self.store.sources("jp:130A"), [])
        self.assertIsNone(self.store.thesis("jp:130A"))
        self.assertEqual(self.store.connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 0)

    def test_identical_reimport_preserves_first_import_time_and_full_contact_snapshot(self):
        self.import_rows([row()])
        before = deepcopy(self.store.company("jp:130A"))
        dump = self.snapshot()
        result = self.harness.import_contacts(str(self.catalog), LATER_IMPORT)
        self.assertEqual(result["status"], "imported")
        self.assertEqual(result["companies_updated"], 0)
        self.assertEqual(result["contacts_unchanged"], 1)
        self.assertEqual(result["older_contacts_ignored"], 0)
        self.assertEqual(result["summary"]["imported_at"], LATER_IMPORT)
        self.assertEqual(self.store.company("jp:130A"), before)
        self.assertEqual(self.store.company("jp:130A")["ir_contact"]["imported_at"], IMPORTED)
        self.assertEqual(self.snapshot(), dump)

    def test_normal_company_master_ingest_retains_saved_contact_and_holdings(self):
        self.seed_existing_company()
        self.import_rows([row()])
        contact = deepcopy(self.store.company("jp:130A")["ir_contact"])
        # A provider refresh supplies its own name/status and no IR metadata.
        self.harness.ingest({"schema_version": 1, "companies": [{
            "id": "jp:130A", "security_code": "130A", "name": "最新SDKマスター社名",
            "status": "watch", "held": False,
        }]})
        saved = self.store.company("jp:130A")
        self.assertEqual(saved["ir_contact"], contact)
        self.assertEqual(saved["name"], "最新SDKマスター社名")
        self.assertEqual(saved["status"], "active")
        self.assertTrue(saved["held"])
        self.assertEqual(saved["screening_reason"], "利用者が承認した調査対象")

    def test_older_verification_is_ignored_even_when_catalog_content_differs(self):
        self.import_rows([row()])
        before = deepcopy(self.store.company("jp:130A"))
        older = row(reviewed_at="2026-10-10T06:31:30+00:00", conditions='["古い確認条件"]')
        observations = json.loads(older["contact_observations"])
        for observation in observations:
            observation["reviewed_at"] = older["reviewed_at"]
            for reference in observation["source_references"]:
                reference["retrieved_at"] = "2026-10-10T06:00:00+00:00"
        older["contact_observations"] = json.dumps(observations, ensure_ascii=False)
        result = self.import_rows([older], imported_at=LATER_IMPORT)
        self.assertEqual(result["status"], "imported")
        self.assertEqual(result["older_contacts_ignored"], 1)
        self.assertEqual(result["companies_updated"], 0)
        self.assertEqual(result["contacts_unchanged"], 0)
        self.assertNotEqual(result["summary"]["catalog_sha256"], before["ir_contact"]["provenance"]["catalog_sha256"])
        self.assertEqual(self.store.company("jp:130A"), before)

    def test_newer_confirmed_catalog_updates_contact_without_replacing_company_decisions(self):
        original = self.seed_existing_company()
        self.import_rows([row()])
        newer = row(reviewed_at="2026-10-14T06:31:30+00:00", conditions='["新たに確認した条件"]')
        observations = json.loads(newer["contact_observations"])
        for observation in observations:
            observation["reviewed_at"] = newer["reviewed_at"]
        newer["contact_observations"] = json.dumps(observations, ensure_ascii=False)
        result = self.import_rows([newer], imported_at=LATER_IMPORT)
        self.assertEqual(result["companies_updated"], 1)
        self.assertEqual(result["older_contacts_ignored"], 0)
        saved = self.store.company("jp:130A")
        self.assertEqual({k: saved[k] for k in original}, original)
        self.assertEqual(saved["ir_contact"]["verified_at"], newer["reviewed_at"])
        self.assertEqual(saved["ir_contact"]["conditions"], ["新たに確認した条件"])

    def test_ir_contact_survives_close_and_reopen_of_persistent_database(self):
        self.seed_existing_company()
        self.import_rows([row(), row("1234")])
        before = self.store.companies()
        self.store.close()
        self.store = Store(self.path)
        self.harness = Harness(self.store)
        self.assertEqual(self.store.companies(), before)
        self.assertEqual(self.store.company("jp:130A")["ir_contact"]["imported_at"], IMPORTED)
        self.assertEqual(self.store.company("jp:1234")["status"], "watch")


if __name__ == "__main__":
    unittest.main()
