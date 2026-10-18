"""Reproduce five explicit issuer disclosures from frozen files, without HTTP/DB."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
from ir_agent.adapters.common import stable_source_id
from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source


def sha(value):
    return hashlib.sha256(value).hexdigest()


def file_sha(path):
    return sha(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n")


def main():
    baseline = json.loads((HERE / "baseline.json").read_text())
    for name, expected in baseline["existing_files"].items():
        assert file_sha(CASE / name) == expected, name
    bundle_in = json.loads((CASE / "source-bundle.json").read_text())
    request = json.loads((HERE / "normalization-request.json").read_text())
    original = next(source for source in bundle_in["sources"] if source["id"] == request["source"]["id"])
    assert request["source"] == original
    assert original["company_id"] == "jp:1379"
    meta = original["metadata"]
    raw_path = CASE.parent / meta["original_raw_file"]
    text_path = CASE.parent / meta["extraction"]["saved_file"]
    snapshot_path = CASE.parent / meta["original_transport_snapshot"]
    snapshot = json.loads(snapshot_path.read_text())
    manifest = json.loads((CASE / "manifest.json").read_text())
    manifest_row = next(row for row in manifest if row["source_id"] == meta["capture_source_id"])
    assert file_sha(raw_path) == meta["original_raw_sha256"] == manifest_row["raw_sha256"] == snapshot["raw_sha256"]
    assert raw_path.stat().st_size == meta["original_raw_byte_count"] == manifest_row["byte_count"] == snapshot["byte_count"]
    assert file_sha(text_path) == meta["extraction"]["sha256"] == manifest_row["text_sha256"] == snapshot["text_sha256"]
    assert file_sha(snapshot_path) == meta["original_transport_snapshot_sha256"]
    assert text_path.read_bytes().decode("utf-8") == original["content"] == snapshot["text"]
    assert original["retrieved_at"] == manifest_row["retrieved_at"] == snapshot["retrieved_at"]
    actual = subprocess.run(["pdftotext", "-layout", str(raw_path), "-"], check=True, capture_output=True).stdout.decode("utf-8")
    assert actual == original["content"]
    assert len(actual.split("\f")) - 1 == 11
    assert original["id"] == stable_source_id("case-public", company_id=original["company_id"],
                                             url=original["url"], content=original["content"], metadata=meta)
    assert len(request["facts"]) == 5
    for fact in request["facts"]:
        location = fact["location"]
        assert location["pdf_page"] == 1
        page = original["content"].split("\f")[0]
        assert page[location["page_text_start"]:location["page_text_end_exclusive"]] == fact["basis_quote"]
        assert location["row_label"] in fact["basis_quote"]
        assert fact["scope"]["accounting_basis_as_stated"] == "日本基準"
        assert fact["scope"]["reporting_scope"] == "consolidated"
    meaning = json.loads((HERE / "meaning-review.json").read_text())
    for citation in meaning["citations"]:
        page = original["content"].split("\f")[citation["pdf_page"] - 1]
        assert page[citation["page_text_start"]:citation["page_text_end_exclusive"]] == citation["quote"]
    output = HERE / "normalized-bundle.json"
    if not output.exists():
        write(output, normalize_disclosed_facts(request, now=datetime.now(timezone.utc)))
    bundle = json.loads(output.read_text())
    derived = bundle["sources"][1]
    assert bundle == normalize_disclosed_facts(request, now=derived["retrieved_at"])
    assert bundle["sources"][0] == original
    fresh = normalize_disclosed_facts(request, now=datetime.now(timezone.utc))["sources"][1]
    assert all(fresh[key] == derived[key] for key in ("id", "content", "metadata"))
    sources = {source["id"]: source for source in bundle_in["sources"]}
    reproduction = reproduce_disclosed_fact_source(derived, sources)
    assert reproduction["status"] == "reproduced", reproduction
    expected = {
        "hokto1379-2027q1-basic-eps": ("reported_fact", "14.44", "JPY-per-share"),
        "hokto1379-2027fy-company-eps": ("issuer_guidance", "167.22", "JPY-per-share"),
        "hokto1379-2027q1-operating-income": ("reported_fact", "418000000", "JPY"),
        "hokto1379-2027fy-company-operating-income": ("issuer_guidance", "7260000000", "JPY"),
        "hokto1379-2027fy-company-annual-dividend": ("issuer_guidance", "62.00", "JPY-per-share"),
    }
    normalized = json.loads(derived["content"])["facts"]
    for fact in normalized:
        assert (fact["kind"], fact["value"], fact["unit"]) == expected[fact["id"]]
        assert fact["financial_inputs_verified"] is False and fact["meaning_review_required"] is True
        assert fact["normalization"]["raw_numeric_token_verified"] is True
    assert {fact["id"] for fact in normalized} == set(expected)
    assert not bundle["companies"] and not bundle["theses"]
    for name, expected_hash in baseline["existing_files"].items():
        assert file_sha(CASE / name) == expected_hash, name
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(), "offline_only": True,
        "new_get_count": 0, "database_reads_or_writes": 0,
        "existing_files_unchanged": True, "baseline_existing_file_count": len(baseline["existing_files"]),
        "raw_hashes_verified": 1, "text_hashes_verified": 1, "snapshot_hashes_verified": 1,
        "raw_text_reextractions_matched": 1, "source_ids_recomputed": 1,
        "original_pdf_page_count": 11, "visual_pdf_pages_reviewed": [1, 2],
        "source_checks": {"raw_sha256": file_sha(raw_path), "text_sha256": file_sha(text_path),
                          "snapshot_sha256": file_sha(snapshot_path), "raw_text_reextraction_matched": True,
                          "original_bundle_source_snapshot_unchanged": True},
        "fact_quote_page_offsets_verified": 5, "meaning_review_quotes_verified": len(meaning["citations"]),
        "visual_table_review": meaning["visual_table_review"],
        "image_rerender_commands_from_this_directory": [item["render_command_from_this_directory"]
                                                       for item in meaning["visual_table_review"]],
        "reviewed_at": request["review"]["recorded_at"],
        "original_source_id": original["id"], "original_retrieved_at": original["retrieved_at"],
        "derived_source_id": derived["id"], "derived_retrieved_at_in_saved_file": derived["retrieved_at"],
        "database_first_saved_at": None,
        "normalized_fact_count": 5, "reproduction": reproduction,
        "normalization_request_sha256": file_sha(HERE / "normalization-request.json"),
        "normalized_bundle_sha256": file_sha(output), "financial_inputs_verified": False,
        "meaning_review_required": True, "model_adopted": False, "seasonal_annualization_performed": False,
        "single_year_dividend_forecast_extended": False,
    }
    write(HERE / "verification.json", report)
    print(json.dumps({key: report[key] for key in ("verified_at", "normalized_fact_count", "original_source_id", "derived_source_id", "model_adopted")}))


if __name__ == "__main__":
    main()
