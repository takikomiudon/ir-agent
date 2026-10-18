#!/usr/bin/env python3
"""Build a repeatable, offline disclosure bundle from saved issuer cases.

No HTTP, PDF extraction, workbook calculation, hypothesis creation or ingestion
occurs here. A finite source map pins the original raw bytes, snapshots and
saved extractions. Verifying those hashes is not a financial-input review.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ir_agent.adapters.common import stable_source_id
from ir_agent.models import JST, day, object_value, text, timestamp, validate_company, validate_source

DEFAULT_MAP = ROOT / "research/ir-case-studies-2026-10-15/manifest-source-map.json"
_SHEET_NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _path(base: Path, relative: object) -> Path:
    relative = text(relative, "saved case path")
    candidate = Path(relative)
    resolved = (base / candidate).resolve()
    if candidate.is_absolute() or not resolved.is_relative_to(base.resolve()):
        raise ValueError("Saved case paths must remain inside the source-map directory")
    return resolved


def _json(base: Path, relative: object):
    return json.loads(_path(base, relative).read_bytes().decode("utf-8"))


def _field(value, path: object):
    if not isinstance(path, list):
        raise ValueError("Manifest/reference paths must be arrays")
    for component in path:
        if isinstance(value, dict) and isinstance(component, str) and component in value:
            value = value[component]
        elif isinstance(value, list) and type(component) is int and 0 <= component < len(value):
            value = value[component]
        else:
            raise ValueError("Manifest/reference path does not resolve to a saved field")
    return value


def _checked_file(base: Path, relative: object, expected: object, label: str) -> bytes:
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError(f"{label} requires a saved SHA-256")
    raw = _path(base, relative).read_bytes()
    if _sha(raw) != expected:
        raise ValueError(f"{label} SHA-256 mismatch: {relative}")
    return raw


def _xlsx_cache_checks(raw: bytes, saved_text: str, checks: object) -> dict:
    """Check selected numeric cached cells against raw XML; never run formulas."""
    extracted = json.loads(saved_text)
    if not isinstance(extracted, list) or any(not isinstance(x, dict) for x in extracted):
        raise ValueError("Saved workbook extraction must contain sheet objects")
    if not isinstance(checks, list) or not checks:
        raise ValueError("A workbook source requires explicit cached-cell checks")
    sheets = {x["sheet"]: x for x in extracted}
    result = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {x.attrib["Id"]: x.attrib["Target"] for x in relationships}
        actual_sheets = {}
        for sheet in workbook.findall("s:sheets/s:sheet", _SHEET_NS):
            target = targets[sheet.attrib[f"{{{_REL_NS}}}id"]]
            actual_sheets[sheet.attrib["name"]] = target.lstrip("/") if target.startswith("/") else "xl/" + target
        for check in checks:
            check = object_value(check, "cached-cell check")
            sheet_name = text(check.get("sheet"), "cached-cell sheet")
            address = text(check.get("cell"), "cached-cell address")
            expected = text(check.get("value"), "cached-cell value")
            sheet = sheets.get(sheet_name)
            if sheet is None or sheet.get("xml_path") != actual_sheets.get(sheet_name):
                raise ValueError("Saved workbook sheet does not match its raw workbook relationship")
            lines = sheet.get("rows")
            if not isinstance(lines, list) or not any(
                re.search(r"(?:^| \| )" + re.escape(address) + "=" + re.escape(expected) + r"(?: \| |$)", line)
                for line in lines if isinstance(line, str)
            ):
                raise ValueError("Expected cached cell is absent from saved workbook extraction")
            worksheet = ET.fromstring(archive.read(sheet["xml_path"]))
            cells = [x for x in worksheet.findall(".//s:c", _SHEET_NS) if x.attrib.get("r") == address]
            if len(cells) != 1 or cells[0].findtext("s:v", namespaces=_SHEET_NS) != expected:
                raise ValueError("Saved cached cell differs from raw workbook XML or has no cached value")
            result.append({**check, "raw_cache_matches": True,
                           "has_formula": cells[0].find("s:f", _SHEET_NS) is not None})
    return {
        "scope": "Saved sheet labels and cached-cell rows, not a complete workbook rendering or independently reviewed financial model",
        "saved_sheet_row_counts": {x["sheet"]: len(x.get("rows", [])) for x in extracted},
        "cached_cell_checks": result, "formulas_evaluated": False,
        "external_links_or_macros_executed": False,
        "uncalculated_formulas": "Not computed or filled; absent caches cannot supply checked cell values",
        "completeness": "Only the saved extraction and explicitly checked cached cells; other cells and formula correctness are not certified",
    }


def build_case_source_bundle(map_path=DEFAULT_MAP) -> dict:
    """Return only a schema-version-1 company/source bundle, without new dates."""
    map_path = Path(map_path)
    base = map_path.resolve().parent
    try:
        case_root_reference = base.relative_to(ROOT).as_posix()
    except ValueError:
        case_root_reference = str(base)
    mapping = object_value(json.loads(map_path.read_bytes().decode("utf-8")), "case source map")
    if type(mapping.get("schema_version")) is not int or mapping["schema_version"] != 1:
        raise ValueError("Source map schema_version must be 1")
    companies = []
    for value in mapping.get("companies", []):
        company = validate_company(value)
        if company["status"] != "watch" or company.get("held"):
            raise ValueError("Offline case import creates watch-only, unheld companies")
        if company["id"] != "jp:" + company["security_code"]:
            raise ValueError("Case company ID and security code must agree")
        companies.append(company)
    company_ids = {x["id"] for x in companies}
    if not companies or len(company_ids) != len(companies):
        raise ValueError("Source map requires unique companies")
    entries = mapping.get("sources")
    if not isinstance(entries, list) or not entries or len(entries) > 64:
        raise ValueError("A finite source map must contain 1 to 64 saved sources")
    sources, by_key, manifest_records = [], {}, {}
    for entry in entries:
        entry = object_value(entry, "source-map entry")
        key = text(entry.get("key"), "source-map key")
        if key in by_key:
            raise ValueError("Duplicate source-map keys")
        if entry.get("company_id") not in company_ids:
            raise ValueError("Mapped source belongs to an unknown case company")
        locator = object_value(entry.get("manifest"), "source manifest locator")
        manifest = object_value(_field(_json(base, locator.get("document")), locator.get("path")), "source manifest record")
        snapshot_raw = _checked_file(base, entry.get("snapshot"), entry.get("snapshot_sha256"), "Transport snapshot")
        snapshot = object_value(json.loads(snapshot_raw.decode("utf-8")), "transport snapshot")
        raw = _checked_file(base, entry.get("raw_file"), entry.get("raw_sha256"), "Original response")
        if manifest.get("sha256") != entry["raw_sha256"] or snapshot.get("sha256") != entry["raw_sha256"]:
            raise ValueError("Manifest, transport snapshot and original response hashes differ")
        if manifest.get("http_status") != 200 or manifest.get("error") or snapshot.get("http_status") != 200 or snapshot.get("error"):
            raise ValueError("Only successfully obtained public documents can become case sources")
        url = manifest.get("resolved_url") or manifest.get("url")
        if url != snapshot.get("url"):
            raise ValueError("Manifest and transport snapshot URLs differ")
        parsed_url = urlsplit(text(url, "source URL"))
        if parsed_url.scheme not in {"https", "http"} or not parsed_url.hostname or parsed_url.username or parsed_url.password:
            raise ValueError("Case source URL must be public HTTP(S) without credentials")
        retrieved_at = text(manifest.get("retrieved_at"), "original retrieved_at")
        retrieved = timestamp(retrieved_at)
        if retrieved != timestamp(snapshot.get("retrieved_at")):
            raise ValueError("Manifest and transport snapshot retrieval times differ")
        kind = entry.get("content_kind")
        content_file = entry.get("content_file")
        extraction = {"kind": kind, "saved_file": content_file or entry["snapshot"],
                      "sha256": entry.get("content_sha256"), "raw_semantic_reextraction_performed": False}
        if kind == "html_visible_text":
            if content_file is not None or "html" not in snapshot.get("content_type", "").lower():
                raise ValueError("HTML sources require saved HTML visible-text snapshots")
            content = text(snapshot.get("text"), "saved HTML text")
            if _sha(content.encode("utf-8")) != entry.get("content_sha256"):
                raise ValueError("Saved HTML content SHA-256 mismatch")
            extraction["method"] = snapshot.get("extraction_method") or "Saved visible HTML text"
            extraction["snapshot_field"] = "text"
        elif kind in {"pdf_text", "xlsx_cached_cells_json"}:
            content = _checked_file(base, content_file, entry.get("content_sha256"), "Saved extraction").decode("utf-8")
            text(content, "saved extraction content")
            if kind == "pdf_text":
                if not raw.startswith(b"%PDF-") or "pdf" not in snapshot.get("content_type", "").lower():
                    raise ValueError("PDF extraction is not linked to a PDF original")
                extraction["method"] = "Previously saved pdftotext -layout output; no re-extraction during bundle conversion"
                extraction["page_separator"] = "form-feed; one-based PDF page numbers"
            else:
                if "spreadsheetml" not in snapshot.get("content_type", "").lower():
                    raise ValueError("Cached-cell extraction is not linked to an XLSX original")
                extraction["method"] = "Previously saved XLSX ZIP/XML labels and cached values; no formula execution"
                extraction["workbook_limitations"] = _xlsx_cache_checks(raw, content, entry.get("cached_cell_checks"))
        else:
            raise ValueError("Unknown saved-content kind")
        dates = [manifest[k] for k in ("publication_date", "published_date") if manifest.get(k) is not None]
        if len(set(dates)) > 1:
            raise ValueError("Conflicting date-only publication fields")
        publication_date = day(dates[0], "publication date").isoformat() if dates else None
        if publication_date and day(publication_date) > retrieved.astimezone(JST).date():
            raise ValueError("Publication date cannot follow original retrieval")
        published_at = manifest.get("published_at") or manifest.get("publication_time")
        if published_at is not None:
            timestamp(published_at, "original publication time")
            if snapshot.get("publication_time") != published_at:
                raise ValueError("Exact publication time is not supported by its saved transport snapshot")
        metadata = {
            "provider": "saved_issuer_case", "document_kind": entry.get("document_kind", "issuer_public_document"),
            "saved_case_directory": case_root_reference, "source_map_file": map_path.name,
            "financial_inputs_verified": False, "financial_values_automatically_adopted": False,
            "publication_date": publication_date,
            "publication_precision": "timestamp" if published_at else "day" if publication_date else "unknown",
            "publication_time_known": published_at is not None,
            "availability_note": "Date-only publication does not establish an earlier usable instant; original retrieval limits availability",
            "original_raw_sha256": entry["raw_sha256"], "original_raw_file": entry["raw_file"],
            "original_transport_snapshot": entry["snapshot"], "original_transport_snapshot_sha256": entry["snapshot_sha256"],
            "original_manifest": deepcopy(locator),
            "original_manifest_source_id": manifest.get("id", manifest.get("source_id")),
            "extraction": extraction,
        }
        if manifest.get("publication_note"):
            metadata["publication_note"] = manifest["publication_note"]
        # Citations are attached before calculating stable identity below.
        item = {"company_id": entry["company_id"], "title": text(entry.get("title"), "source title"),
                "url": url, "source_type": "public_disclosure", "published_at": published_at,
                "retrieved_at": retrieved_at, "content": content, "requires_research": True, "metadata": metadata}
        sources.append(item)
        by_key[key] = item
        manifest_records[key] = manifest
    references = mapping.get("citations", [])
    if not isinstance(references, list):
        raise ValueError("Mapped citations must be a list")
    for locator in references:
        item = by_key.get(locator.get("source_key"))
        if item is None:
            raise ValueError("Citation points to an unmapped case source")
        citation = object_value(_field(_json(base, locator.get("document")), locator.get("path")), "saved citation")
        quote = text(citation.get("quote"), "saved citation quote")
        manifest = manifest_records[locator["source_key"]]
        if citation.get("source_id") is not None and citation["source_id"] != manifest.get("id", manifest.get("source_id")):
            raise ValueError("Citation source ID differs from its mapped manifest record")
        if citation.get("snapshot") is not None and citation["snapshot"] != manifest.get("snapshot"):
            raise ValueError("Citation snapshot differs from its mapped manifest record")
        if citation.get("url") is not None and citation["url"] != item["url"]:
            raise ValueError("Citation URL differs from the saved source")
        content = item["content"]
        page = citation.get("pdf_page")
        if page is not None:
            pages = content.split("\f")
            if type(page) is not int or page < 1 or page > len(pages) or item["metadata"]["extraction"]["kind"] != "pdf_text":
                raise ValueError("Citation has an invalid saved PDF page")
            content = pages[page - 1]
        if quote not in content:
            raise ValueError(f"Citation quote is absent from saved content/page: {citation.get('id')}")
        item["metadata"].setdefault("verified_saved_citations", []).append({
            "reference": {"document": locator["document"], "path": locator["path"]},
            **deepcopy(citation), "exact_quote_found": True,
            "verification_scope": "Exact match in saved extraction; not an independent financial-value or PDF rendering review",
        })
    ids = set()
    for item in sources:
        item["id"] = stable_source_id("case-public", company_id=item["company_id"], url=item["url"],
                                      content=item["content"], metadata=item["metadata"])
        validate_source(item)
        if item["id"] in ids:
            raise ValueError("Source map contains duplicate source identities")
        ids.add(item["id"])
    return {"schema_version": 1, "companies": sorted(companies, key=lambda x: x["id"]),
            "sources": sorted(sources, key=lambda x: (x["company_id"], x["url"], x["id"])), "theses": []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default=str(DEFAULT_MAP), help="Finite saved-source map JSON")
    parser.add_argument("--output", help="Write bundle here; otherwise emit JSON to stdout")
    args = parser.parse_args()
    bundle = build_case_source_bundle(args.map)
    output = json.dumps(bundle, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
