"""Small saved-snapshot coverage checks and a genuinely read-only DB reader."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

from ir_agent.coverage import summarize_coverage
from ir_agent.models import json_text, validate_source

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from report_coverage_gaps import read_snapshot

AS_OF = "2026-10-15T17:00:00+09:00"


def fixture():
    return {"companies": [{"id": "jp:0001", "name": "Synthetic", "status": "watch", "held": False,
                           "ir_contact": {"channel_status": "confirmed", "contact_url": "https://example.invalid/ir",
                                          "channels": ["form"], "individual_access": "not_stated",
                                          "verified_at": "2026-10-13T10:00:00+09:00", "imported_at": "2026-10-15T10:00:00+09:00"}}],
            "sources": [], "theses": [], "policies": [], "questions": []}


def source(source_id="financial", source_type="public_disclosure", metadata=None):
    return {"id": source_id, "company_id": "jp:0001", "title": "Synthetic public record", "source_type": source_type,
            "url": "https://example.invalid/disclosure", "published_at": "2026-10-14T15:00:00+09:00",
            "retrieved_at": "2026-10-14T16:00:00+09:00", "content": "0", "metadata": metadata or {}}


class CoverageReportTests(unittest.TestCase):
    def classified(self, document, *, financial=True, kind="financial_statement"):
        document = validate_source(document)
        return {"source_id": document["id"], "version": 1, "kind": kind, "financial_content": financial,
                "basis_quote": document["content"], "recorded_at": "2026-10-15T10:00:00+09:00",
                "first_saved_at": "2026-10-15T10:00:00+09:00", "inputs_verified": False,
                "source_sha256": hashlib.sha256(document["content"].encode()).hexdigest(),
                "source_snapshot_sha256": hashlib.sha256(json_text(document).encode()).hexdigest()}

    def test_saved_classification_is_time_bound_and_does_not_rewrite_source(self):
        value = fixture(); value["sources"] = [source()]
        value["source_classifications"] = [self.classified(value["sources"][0])]
        before = deepcopy(value)
        result = summarize_coverage(value, as_of=AS_OF)
        self.assertEqual(result["summary"]["with_financial_content"], 1)
        self.assertEqual(result["companies"][0]["source_classification_refs"], [{"source_id": "financial", "version": 1}])
        value["source_classifications"][0]["first_saved_at"] = "2026-10-16T10:00:00+09:00"
        self.assertEqual(summarize_coverage(value, as_of=AS_OF)["summary"]["with_financial_content"], 0)
        self.assertEqual(value["sources"], before["sources"])

    def test_known_nonfinancial_classification_is_not_requeued_as_unknown(self):
        value = fixture(); value["sources"] = [source()]
        value["source_classifications"] = [self.classified(value["sources"][0], financial=False, kind="schedule")]
        result = summarize_coverage(value, as_of=AS_OF)
        self.assertEqual(result["companies"][0]["unclassified_public_source_ids"], [])
        self.assertIn("obtain_public_financial_content", result["next_material_counts"])
        self.assertNotIn("classify_saved_public_disclosures", result["next_material_counts"])
        value["source_classifications"][0]["financial_content"] = None
        self.assertIn("classify_saved_public_disclosures", summarize_coverage(value, as_of=AS_OF)["next_material_counts"])

    def test_classification_must_match_the_immutable_source_and_quote(self):
        value = fixture(); value["sources"] = [source()]
        record = self.classified(value["sources"][0]); value["source_classifications"] = [record]
        for field, replacement in (("source_sha256", "bad"), ("source_snapshot_sha256", "bad"), ("basis_quote", "Not in source")):
            changed = deepcopy(value); changed["source_classifications"][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError): summarize_coverage(changed, as_of=AS_OF)

    def test_catalog_is_not_investment_eligibility_and_missing_sources_are_zero(self):
        value = fixture(); before = deepcopy(value)
        result = summarize_coverage(value, as_of=AS_OF)
        self.assertEqual(result["summary"]["confirmed_contact_available"], 1)
        self.assertEqual(result["summary"]["individual_access"], {"not_stated": 1})
        self.assertEqual(result["summary"]["with_available_thesis"], 0)
        self.assertEqual(result["companies"][0]["current_status"], "watch")
        self.assertEqual(result["companies"][0]["saved_source_count"], 0)
        self.assertEqual(value, before)

    def test_missing_inventory_section_is_unknown_not_zero(self):
        value = fixture(); value.pop("sources"); value.pop("policies")
        result = summarize_coverage(value, as_of=AS_OF)
        self.assertIsNone(result["companies"][0]["saved_source_count"])
        self.assertIsNone(result["policy_registry"]["recorded"])
        self.assertIsNone(result["summary"]["with_financial_content"])
        self.assertIsNone(result["summary"]["with_company_policy_assignment"])
        self.assertEqual(result["snapshot_sections_missing"], ["sources", "policies"])

    def test_zero_financial_values_are_saved_data_and_not_missing(self):
        value = fixture(); value["sources"] = [source(metadata={"financial_document": True, "operating_profit": 0}), source("market", "market_data")]
        value["theses"] = [{"company_id": "jp:0001", "version": 1, "recorded_at": "2026-10-14T17:00:00+09:00", "current_price_jpy": 0, "evidence_ids": ["financial"]}]
        result = summarize_coverage(value, as_of=AS_OF)
        self.assertEqual(result["summary"]["with_financial_content"], 1)
        self.assertEqual(result["summary"]["with_market_source"], 1)
        self.assertEqual(result["companies"][0]["latest_thesis"]["current_price_jpy"], 0)
        self.assertEqual(result["summary"]["with_available_thesis"], 1)

    def test_future_source_thesis_and_contact_import_are_unavailable(self):
        value = fixture(); value["sources"] = [source()]
        value["sources"][0]["retrieved_at"] = "2026-10-16T16:00:00+09:00"
        value["theses"] = [{"company_id": "jp:0001", "version": 1, "recorded_at": "2026-10-16T17:00:00+09:00", "evidence_ids": ["financial"]}]
        value["companies"][0]["ir_contact"]["imported_at"] = "2026-10-16T10:00:00+09:00"
        result = summarize_coverage(value, as_of=AS_OF)
        self.assertEqual(result["summary"]["confirmed_contact_available"], 0)
        self.assertEqual(result["companies"][0]["future_thesis_count"], 1)
        self.assertIsNone(result["companies"][0]["latest_thesis"])
        self.assertEqual(result["companies"][0]["unavailable_sources"][0]["reason"], "source_after_as_of")

    def test_index_entry_and_unclassified_public_document_are_not_financial_completion(self):
        value = fixture(); value["sources"] = [source("index", metadata={"provider": "edinet", "index_only": True}), source("unclassified")]
        result = summarize_coverage(value, as_of=AS_OF)
        company = result["companies"][0]
        self.assertEqual(company["index_only_source_ids"], ["index"])
        self.assertEqual(company["unclassified_public_source_ids"], ["unclassified"])
        self.assertEqual(result["summary"]["with_financial_content"], 0)
        self.assertIn("classify_saved_public_disclosures", [a["kind"] for a in company["next_required_materials"]])

    def test_held_status_is_preserved_and_unknown_does_not_become_false(self):
        value = fixture(); value["companies"][0].update(status="special_model", held=True, industry="banking")
        other = deepcopy(value["companies"][0]); other.update(id="jp:0002"); other.pop("held")
        value["companies"].append(other)
        result = summarize_coverage(value, as_of=AS_OF)
        self.assertEqual(result["summary"]["held_true"], 1)
        self.assertEqual(result["summary"]["held_unknown"], 1)
        self.assertEqual(result["companies"][0]["current_status"], "special_model")

    def test_registry_policy_does_not_assign_every_company_and_zero_fees_are_configured(self):
        value = fixture()
        parameters = {"minimum_upside_pct": "0", "maximum_downside_pct": "0", "entry_cost_pct": "0", "exit_cost_pct": "0", "max_quote_age_seconds": 1, "target_scenario": "base"}
        policy = {"id": "explicit", "version": 1, "recorded_at": "2026-10-14T10:00:00+09:00", "parameters": parameters,
                  "parameter_sources": {k: {"kind": "user", "reference": "Synthetic test user instruction", "rationale": "Arithmetic test, no investment advice"} for k in parameters}}
        value["policies"] = [{"policy": policy, "first_saved_at": "2026-10-14T11:00:00+09:00"}]
        result = summarize_coverage(value, as_of=AS_OF)
        self.assertEqual(result["policy_registry"]["configured_available_nonsynthetic"], 1)
        self.assertEqual(result["summary"]["with_company_policy_assignment"], 0)
        value["companies"][0]["decision_policy_ref"] = {"id": "explicit", "version": 1, "recorded_at": "2026-10-14T12:00:00+09:00"}
        self.assertEqual(summarize_coverage(value, as_of=AS_OF)["summary"]["with_company_policy_assignment"], 1)
        value["policies"][0]["first_saved_at"] = "2026-10-16T11:00:00+09:00"
        self.assertEqual(summarize_coverage(value, as_of=AS_OF)["summary"]["with_company_policy_assignment"], 0)

    def test_reader_does_not_initialize_schema_or_write_to_database(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory)/"minimal.sqlite3"
            c = sqlite3.connect(database)
            c.execute("CREATE TABLE companies(id TEXT,data TEXT)")
            c.execute("INSERT INTO companies VALUES (?,?)", ("jp:0001", json.dumps(fixture()["companies"][0])))
            c.commit(); c.close()
            before = hashlib.sha256(database.read_bytes()).hexdigest()
            result = read_snapshot(database)
            after = hashlib.sha256(database.read_bytes()).hexdigest()
            self.assertEqual(before, after)
            self.assertEqual(list(result), ["companies"])
            self.assertEqual(len(result["companies"]), 1)
            with self.assertRaises(FileNotFoundError): read_snapshot(Path(directory)/"missing.sqlite3")


if __name__ == "__main__": unittest.main()
