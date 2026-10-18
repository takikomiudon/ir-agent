"""Read-only catalog conversion, provenance and quarantine regressions."""

from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from ir_agent.contacts import build_contact_bundle


IMPORTED = "2026-10-15T10:30:00+09:00"
VERIFIED = "2026-10-12T06:31:30+00:00"


def row(code="130A", **updates):
    url = f"https://issuer.example/ir/{code}/contact"
    ref = {"snapshot": f"evidence/{code}/01.json", "url": url,
           "quote": "個人投資家からのIRお問い合わせ", "form_index": 1, "control_indices": [2, 3],
           "source_directory": "/original-research", "retrieved_at": "2026-10-12T06:00:00+00:00"}
    observation = {"security_code": code, "channel_status": "confirmed", "outreach_suitability": "candidate",
                   "contact_url": url, "channels": ["form"], "public_ir_emails": [],
                   "individual_access": "explicit", "reviewed_at": VERIFIED,
                   "source_references": [ref, deepcopy(ref)], "notes": ["Not copied into the company"],
                   "raw_page": "Huge irrelevant page body must not be copied"}
    result = {
        "security_code": code, "company_name": f"架空企業{code}", "channel_status": "confirmed",
        "contact_url": url, "channels": json.dumps(["form"]), "public_ir_emails": "[]",
        "individual_access": "explicit", "outreach_suitability": "candidate",
        "conditions": json.dumps(["返信の無断転載禁止", "回答を約束しない"], ensure_ascii=False),
        "limitations": json.dumps(["送信していない"], ensure_ascii=False), "reviewed_at": VERIFIED,
        "review_source": "saved-page-review", "source_record": f"/original-research/records/{code}.json",
        "contact_observations": json.dumps([observation], ensure_ascii=False),
    }
    result.update(updates)
    return result


class ContactBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "catalog.csv"

    def write(self, rows, *, bom=False, fields=None):
        with self.path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields or list(row()))
            writer.writeheader()
            writer.writerows(rows)
        return self.path

    def convert(self, rows, **kwargs):
        return build_contact_bundle(self.write(rows, **kwargs), imported_at=IMPORTED)

    def test_bom_alphanumeric_code_and_conditions_are_preserved_without_active_or_disclosure(self):
        original = row()
        result = self.convert([original], bom=True)
        company = result["bundle"]["companies"][0]
        self.assertEqual(company["id"], "jp:130A")
        self.assertEqual(company["security_code"], "130A")
        self.assertEqual(company["status"], "watch")
        self.assertNotIn("held", company)
        self.assertEqual(result["bundle"]["sources"], [])
        self.assertEqual(result["bundle"]["theses"], [])
        contact = company["ir_contact"]
        self.assertEqual(contact["conditions"], json.loads(original["conditions"]))
        self.assertEqual(contact["limitations"], json.loads(original["limitations"]))
        self.assertEqual(contact["verified_at"], VERIFIED)
        self.assertEqual(contact["imported_at"], IMPORTED)
        self.assertEqual(result["summary"]["individual_access_explicit"], 1)

    def test_original_refs_are_kept_and_deduplicated_without_whole_observations(self):
        result = self.convert([row()])
        company = result["bundle"]["companies"][0]
        provenance = company["ir_contact"]["provenance"]
        reference = json.loads(row()["contact_observations"])[0]["source_references"][0]
        self.assertEqual(provenance["source_references"], [reference])
        self.assertEqual(provenance["csv_row_number"], 2)
        self.assertEqual(provenance["csv_line_number"], 2)
        self.assertEqual(provenance["source_record"], row()["source_record"])
        self.assertEqual(provenance["catalog_sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())
        serialized = json.dumps(company)
        self.assertNotIn("contact_observations", serialized)
        self.assertNotIn("Huge irrelevant", serialized)
        self.assertNotIn("Not copied", serialized)

    def test_email_contact_and_legacy_space_after_mailto_are_preserved(self):
        original = row()
        original.update(contact_url="mailto: ir@issuer.example", channels='["email"]', public_ir_emails='["ir@issuer.example"]')
        obs = json.loads(original["contact_observations"])
        obs[0].update(contact_url=original["contact_url"], channels=["email"], public_ir_emails=["ir@issuer.example"])
        original["contact_observations"] = json.dumps(obs)
        company = self.convert([original])["bundle"]["companies"][0]
        self.assertEqual(company["ir_contact"]["contact_url"], "mailto: ir@issuer.example")
        original["contact_url"] = "mailto:other@issuer.example"
        self.assertEqual(self.convert([original])["summary"]["rejected_rows"], 1)

    def test_repeated_conversion_is_identical_and_does_not_change_catalog(self):
        self.write([row()])
        before = self.path.read_bytes()
        one = build_contact_bundle(self.path, imported_at=IMPORTED)
        two = build_contact_bundle(self.path, imported_at=IMPORTED)
        self.assertEqual(one, two)
        self.assertEqual(before, self.path.read_bytes())
        later = build_contact_bundle(self.path, imported_at="2026-10-16T10:30:00+09:00")
        contact = later["bundle"]["companies"][0]["ir_contact"]
        self.assertEqual(contact["verified_at"], VERIFIED)
        self.assertEqual(contact["imported_at"], "2026-10-16T10:30:00+09:00")
        self.assertEqual(contact["provenance"]["catalog_sha256"], one["summary"]["catalog_sha256"])

    def test_duplicate_codes_quarantine_both_rows_and_keep_other_company(self):
        result = self.convert([row(), row("1234"), row(company_name="Conflicting name")])
        self.assertEqual([c["id"] for c in result["bundle"]["companies"]], ["jp:1234"])
        self.assertEqual(result["summary"]["input_rows"], 3)
        self.assertEqual(result["summary"]["duplicate_codes"], ["130A"])
        self.assertEqual([x["row_number"] for x in result["rejected_rows"]], [2, 4])
        self.assertTrue(all("duplicate_security_code" in x["reason_codes"] for x in result["rejected_rows"]))

    def test_bad_rows_are_reported_and_do_not_hide_the_valid_row(self):
        bad = [row("0000"), row("ABCDE"), row("130A0"), row("130a"), row("1234", channels='["phone"]'),
               row("2345", channel_status="provisional"), row("3456", outreach_suitability="restricted"),
               row("4567", individual_access="restricted"), row("5678", conditions="not-json"),
               row("6789", conditions='["same", "same"]'), row("7890", public_ir_emails='["ir@issuer.example"]'),
               row("8901", reviewed_at="2026-10-12"), row("9012", reviewed_at="2027-01-01T00:00:00+09:00")]
        result = self.convert([*bad, row()])
        self.assertEqual(result["summary"]["input_rows"], len(bad)+1)
        self.assertEqual(result["summary"]["accepted_rows"], 1)
        self.assertEqual(result["summary"]["rejected_rows"], len(bad))
        self.assertEqual(len(result["rejected_rows"]), len(bad))
        self.assertTrue(all(x["reasons"] and x["row_number"] >= 2 for x in result["rejected_rows"]))

    def test_missing_or_mismatched_observation_and_forged_access_are_quarantined(self):
        for change in ({"contact_observations": "[]"}, {"contact_url": "https://another.example/form"}):
            with self.subTest(change=change):
                self.assertEqual(self.convert([row(**change)])["summary"]["rejected_rows"], 1)
        original = row()
        obs = json.loads(original["contact_observations"])
        for name, value in (("security_code", []), ("channels", ["email"]), ("individual_access", "not_stated")):
            bad = deepcopy(obs)
            bad[0][name] = value
            original["contact_observations"] = json.dumps(bad)
            self.assertEqual(self.convert([original])["summary"]["rejected_rows"], 1)

    def test_navigation_refs_can_have_empty_quotes_if_real_quotes_remain(self):
        original = row()
        obs = json.loads(original["contact_observations"])
        ref = deepcopy(obs[0]["source_references"][0])
        ref["quote"] = ""
        obs[0]["source_references"].append(ref)
        obs[0]["individual_access"] = "explicitly_allowed"
        original["contact_observations"] = json.dumps(obs)
        contact = self.convert([original])["bundle"]["companies"][0]["ir_contact"]
        self.assertEqual(len(contact["provenance"]["source_references"]), 2)
        self.assertEqual(contact["individual_access"], "explicit")
        obs[0]["source_references"] = [ref]
        original["contact_observations"] = json.dumps(obs)
        self.assertEqual(self.convert([original])["summary"]["rejected_rows"], 1)

    def test_bad_file_headers_and_naive_import_time_fail_explicitly(self):
        self.write([row()])
        with self.assertRaises(ValueError):
            build_contact_bundle(self.path, imported_at="2026-10-15T10:30:00")
        for content in ("", "security_code,name\n130A,name\n", "security_code,security_code\n130A,130A\n", '"unclosed header'):
            self.path.write_text(content)
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    build_contact_bundle(self.path, imported_at=IMPORTED)

    def test_duplicate_json_keys_are_not_silently_overwritten(self):
        original = row()
        original["contact_observations"] = '[{"channel_status":"confirmed","channel_status":"unconfirmed"}]'
        result = self.convert([original])
        self.assertEqual(result["summary"]["rejected_rows"], 1)
        self.assertIn("duplicate JSON keys", result["rejected_rows"][0]["reasons"][0])

    def test_logical_row_and_starting_line_survive_multiline_csv_values(self):
        result = self.convert([row(company_name="架空\n会社"), row("1234", conditions="broken")])
        rejected = result["rejected_rows"][0]
        self.assertEqual(rejected["row_number"], 3)
        self.assertEqual(rejected["line_number"], 4)

    def test_malformed_row_still_counts_and_quarantines_a_duplicate_code(self):
        self.write([row(), row("1234")])
        with self.path.open("a", newline="") as stream:
            csv.writer(stream).writerow(["130A", "wrong number of fields"])
        result = build_contact_bundle(self.path, imported_at=IMPORTED)
        self.assertEqual(result["summary"]["input_rows"], 3)
        self.assertEqual(result["summary"]["accepted_rows"], 1)
        self.assertEqual(result["summary"]["rejected_rows"], 2)
        self.assertIn("malformed_csv_columns", result["rejected_rows"][1]["reason_codes"])


if __name__ == "__main__":
    unittest.main()
