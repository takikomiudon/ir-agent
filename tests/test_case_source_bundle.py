"""Offline saved-document provenance, date precision and citation regressions."""

from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from ir_agent.models import available, timestamp, validate_source


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("case_source_builder", ROOT / "scripts/build_case_source_bundle.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
build_case_source_bundle = BUILDER.build_case_source_bundle

RETRIEVED = "2026-10-15T01:10:00+00:00"
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


class CaseSourceBundleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.mapping = {
            "schema_version": 1,
            "companies": [{"id": "jp:3774", "security_code": "3774", "name": "架空データ企業", "status": "watch"}],
            "sources": [], "citations": [],
        }
        self.manifest = {"sources": [], "references": []}
        self.map_path = self.base / "map.json"

    def save(self):
        (self.base / "draft.json").write_text(json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
        self.map_path.write_text(json.dumps(self.mapping, ensure_ascii=False), encoding="utf-8")

    def add_source(self, *, kind="html_visible_text", content="公開済みの説明。", raw=None, publication_date=None, url=None):
        index = len(self.mapping["sources"])
        key = f"fixture-{index}"
        url = url or f"https://issuer.example/ir/{key}"
        raw = raw if raw is not None else b"%PDF-fixture-original" if kind == "pdf_text" else b"<html>saved original</html>"
        content_type = {"pdf_text": "application/pdf", "html_visible_text": "text/html", "xlsx_cached_cells_json": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}[kind]
        raw_file = f"{key}.raw"
        snapshot_file = f"{key}.json"
        (self.base / raw_file).write_bytes(raw)
        snapshot = {"url": url, "sha256": SHA(raw), "retrieved_at": RETRIEVED,
                    "http_status": 200, "error": None, "publication_time": None,
                    "content_type": content_type, "text": content,
                    "extraction_method": "Saved visible text fixture"}
        (self.base / snapshot_file).write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
        record = {"id": key, "url": url, "sha256": SHA(raw), "retrieved_at": RETRIEVED,
                  "http_status": 200, "error": None, "snapshot": snapshot_file,
                  "publication_date": publication_date, "publication_time": None}
        self.manifest["sources"].append(record)
        content_file = None
        if kind != "html_visible_text":
            content_file = f"{key}.txt"
            (self.base / content_file).write_bytes(content.encode("utf-8"))
        entry = {"key": key, "company_id": "jp:3774",
                 "manifest": {"document": "draft.json", "path": ["sources", index]},
                 "snapshot": snapshot_file, "snapshot_sha256": SHA((self.base / snapshot_file).read_bytes()),
                 "raw_file": raw_file, "raw_sha256": SHA(raw), "content_kind": kind,
                 "content_file": content_file, "content_sha256": SHA(content.encode("utf-8")),
                 "title": f"公開資料{index}", "document_kind": "issuer_public_document"}
        self.mapping["sources"].append(entry)
        return entry, record

    def add_reference(self, entry, *, quote, page=None):
        index = len(self.manifest["references"])
        reference = {"id": f"quote-{index}", "source_id": entry["key"], "quote": quote, "pdf_page": page}
        self.manifest["references"].append(reference)
        self.mapping["citations"].append({"document": "draft.json", "path": ["references", index], "source_key": entry["key"]})
        return reference

    def build(self):
        self.save()
        return build_case_source_bundle(self.map_path)

    def refresh_snapshot_hash(self, entry, **updates):
        path = self.base / entry["snapshot"]
        snapshot = json.loads(path.read_text())
        snapshot.update(updates)
        path.write_text(json.dumps(snapshot), encoding="utf-8")
        entry["snapshot_sha256"] = SHA(path.read_bytes())

    def test_date_only_and_unknown_publication_keep_original_retrieval_availability(self):
        self.add_source(publication_date="2026-08-07")
        self.add_source()
        bundle = self.build()
        self.assertEqual(bundle["schema_version"], 1)
        self.assertEqual(bundle["theses"], [])
        self.assertEqual(bundle["companies"][0]["status"], "watch")
        self.assertFalse(bundle["companies"][0]["held"])
        for source in bundle["sources"]:
            validate_source(source)
            self.assertEqual(source["source_type"], "public_disclosure")
            self.assertEqual(source["retrieved_at"], RETRIEVED)
            self.assertIsNone(source["published_at"])
            self.assertFalse(available(source, timestamp("2026-10-15T01:09:59+00:00")))
            self.assertTrue(available(source, timestamp(RETRIEVED)))
            self.assertFalse(source["metadata"]["financial_inputs_verified"])
            self.assertFalse(source["metadata"]["financial_values_automatically_adopted"])
        dated = next(x for x in bundle["sources"] if x["metadata"]["publication_date"])
        unknown = next(x for x in bundle["sources"] if x["metadata"]["publication_date"] is None)
        self.assertEqual(dated["metadata"]["publication_precision"], "day")
        self.assertEqual(unknown["metadata"]["publication_precision"], "unknown")

    def test_pdf_uses_saved_extraction_with_raw_pdf_lineage_and_exact_page_quote(self):
        entry, record = self.add_source(kind="pdf_text", content="表紙。\f二頁の原文。\f")
        self.add_reference(entry, quote="二頁の原文。", page=2)
        source = self.build()["sources"][0]
        self.assertEqual(source["content"], "表紙。\f二頁の原文。\f")
        self.assertEqual(source["url"], record["url"])
        self.assertEqual(source["metadata"]["original_raw_sha256"], entry["raw_sha256"])
        self.assertEqual(source["metadata"]["extraction"]["saved_file"], entry["content_file"])
        self.assertFalse(source["metadata"]["extraction"]["raw_semantic_reextraction_performed"])
        self.assertEqual(source["metadata"]["verified_saved_citations"][0]["pdf_page"], 2)

    def test_rebuild_is_identical_without_changing_original_files_or_timestamps(self):
        entry, _ = self.add_source()
        self.add_reference(entry, quote="公開済み")
        self.save()
        before = {p.name: p.read_bytes() for p in self.base.iterdir()}
        first = build_case_source_bundle(self.map_path)
        self.assertEqual(first, build_case_source_bundle(self.map_path))
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.base.iterdir()})

    def test_modified_raw_snapshot_and_extraction_fail_their_own_hash_checks(self):
        for field in ("raw_file", "snapshot", "content_file"):
            with self.subTest(field=field):
                self.mapping["sources"] = []
                self.manifest["sources"] = []
                entry, _ = self.add_source(kind="pdf_text")
                self.save()
                (self.base / entry[field]).write_bytes(b"modified evidence")
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    build_case_source_bundle(self.map_path)

    def test_manifest_hash_url_time_and_response_errors_cannot_be_imported(self):
        for update in ({"sha256": "0"*64}, {"url": "https://other.example"},
                       {"retrieved_at": "2026-10-16T01:10:00+00:00"}, {"http_status": 403}, {"error": "transport failure"}):
            with self.subTest(update=update):
                self.mapping["sources"] = []
                self.manifest["sources"] = []
                _, record = self.add_source()
                record.update(update)
                with self.assertRaises(ValueError):
                    self.build()

    def test_quote_on_wrong_page_or_from_wrong_source_is_rejected(self):
        entry, _ = self.add_source(kind="pdf_text", content="表紙。\f二頁の原文。")
        ref = self.add_reference(entry, quote="二頁の原文。", page=1)
        with self.assertRaisesRegex(ValueError, "absent"):
            self.build()
        ref["pdf_page"] = 2
        ref["source_id"] = "wrong-source"
        with self.assertRaisesRegex(ValueError, "source ID"):
            self.build()
        ref["source_id"] = entry["key"]
        ref["quote"] = "資料に存在しない説明"
        with self.assertRaisesRegex(ValueError, "absent"):
            self.build()

    def test_date_only_does_not_allow_invented_timestamp_or_future_publication(self):
        _, record = self.add_source(publication_date="2026-10-16")
        with self.assertRaisesRegex(ValueError, "Publication date"):
            self.build()
        record["publication_date"] = "2026-08-07"
        record["published_at"] = "2026-08-07T15:00:00+09:00"
        with self.assertRaisesRegex(ValueError, "not supported"):
            self.build()

    def test_paths_cannot_escape_and_companies_cannot_be_activated(self):
        entry, _ = self.add_source()
        original = entry["raw_file"]
        entry["raw_file"] = "../outside.raw"
        with self.assertRaisesRegex(ValueError, "inside"):
            self.build()
        entry["raw_file"] = original
        self.mapping["companies"][0]["status"] = "active"
        with self.assertRaisesRegex(ValueError, "watch-only"):
            self.build()

    def workbook(self, cache):
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w") as z:
            z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="CF" r:id="rId1"/></sheets></workbook>')
            z.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            value = f"<v>{cache}</v>" if cache is not None else ""
            z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r="A1"><f>1+2</f>'+value+'</c></row></sheetData></worksheet>')
        return raw.getvalue()

    def test_xlsx_cached_value_is_checked_without_executing_formula(self):
        extraction = json.dumps([{"sheet": "CF", "xml_path": "xl/worksheets/sheet1.xml", "rows": ["A1=3"]}])
        entry, _ = self.add_source(kind="xlsx_cached_cells_json", content=extraction, raw=self.workbook("3"))
        entry["cached_cell_checks"] = [{"sheet": "CF", "cell": "A1", "value": "3"}]
        source = self.build()["sources"][0]
        limitations = source["metadata"]["extraction"]["workbook_limitations"]
        self.assertFalse(limitations["formulas_evaluated"])
        self.assertFalse(limitations["external_links_or_macros_executed"])
        self.assertTrue(limitations["cached_cell_checks"][0]["has_formula"])
        self.assertTrue(limitations["cached_cell_checks"][0]["raw_cache_matches"])
        self.assertFalse(source["metadata"]["financial_inputs_verified"])

    def test_missing_or_inconsistent_formula_cache_is_not_computed_or_filled(self):
        extraction = json.dumps([{"sheet": "CF", "xml_path": "xl/worksheets/sheet1.xml", "rows": ["A1=3"]}])
        for cache in (None, "4"):
            with self.subTest(cache=cache):
                self.mapping["sources"] = []
                self.manifest["sources"] = []
                entry, _ = self.add_source(kind="xlsx_cached_cells_json", content=extraction, raw=self.workbook(cache))
                entry["cached_cell_checks"] = [{"sheet": "CF", "cell": "A1", "value": "3"}]
                with self.assertRaisesRegex(ValueError, "cached cell"):
                    self.build()

    def test_actual_two_cases_have_twenty_sources_and_twenty_nine_exact_citations(self):
        base = BUILDER.DEFAULT_MAP.parent
        mapping = json.loads(BUILDER.DEFAULT_MAP.read_text())
        originals = {BUILDER.DEFAULT_MAP}
        for entry in mapping["sources"]:
            originals.update(base / entry[k] for k in ("snapshot", "raw_file"))
            originals.add(base / entry["manifest"]["document"])
            if entry.get("content_file"):
                originals.add(base / entry["content_file"])
        before = {str(p): SHA(p.read_bytes()) for p in originals}
        bundle = build_case_source_bundle()
        self.assertEqual([x["id"] for x in bundle["companies"]], ["jp:3774", "jp:5988"])
        self.assertEqual(len(bundle["sources"]), 20)
        self.assertEqual(sum(x["company_id"] == "jp:3774" for x in bundle["sources"]), 12)
        self.assertEqual(sum(x["company_id"] == "jp:5988" for x in bundle["sources"]), 8)
        self.assertEqual(sum(len(x["metadata"].get("verified_saved_citations", [])) for x in bundle["sources"]), 29)
        self.assertTrue(all(x["published_at"] is None and x["source_type"] == "public_disclosure" for x in bundle["sources"]))
        self.assertEqual(bundle["theses"], [])
        self.assertEqual(before, {str(p): SHA(p.read_bytes()) for p in originals})


if __name__ == "__main__":
    unittest.main()
