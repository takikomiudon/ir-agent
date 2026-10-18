"""Verify a frozen source and five explicit fact declarations without HTTP/DB."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
INPUT = CASE / "library-followup"
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
    frozen = {CASE / name: expected for name, expected in baseline["existing_files"].items()}
    for path, expected in frozen.items():
        assert file_sha(path) == expected
    manifest = json.loads((INPUT / "manifest.json").read_text())
    source_bundle = json.loads((INPUT / "source-bundle.json").read_text())
    assert len(manifest) == len(source_bundle["sources"]) == 3
    sources = {s["id"]: s for s in source_bundle["sources"]}
    checks = []
    for row in manifest:
        source = next(s for s in sources.values() if s["metadata"]["capture_source_id"] == row["source_id"])
        meta = source["metadata"]
        raw_path = CASE.parent / meta["original_raw_file"]
        snapshot_path = CASE.parent / meta["original_transport_snapshot"]
        text_path = CASE.parent / meta["extraction"]["saved_file"]
        raw = raw_path.read_bytes()
        snapshot = json.loads(snapshot_path.read_text())
        assert file_sha(raw_path) == row["raw_sha256"] == meta["original_raw_sha256"]
        assert len(raw) == row["byte_count"] == meta["original_raw_byte_count"]
        assert file_sha(snapshot_path) == meta["original_transport_snapshot_sha256"]
        assert file_sha(text_path) == row["text_sha256"] == meta["extraction"]["sha256"]
        assert text_path.read_bytes().decode("utf-8") == source["content"] == snapshot["text"]
        assert source["retrieved_at"] == row["retrieved_at"] == snapshot["retrieved_at"]
        if meta["extraction"]["kind"] == "pdf_text":
            actual = subprocess.run(["pdftotext", "-layout", str(raw_path), "-"], check=True, capture_output=True).stdout.decode("utf-8")
        else:
            actual = raw.decode("utf-8")  # JS/JSONP are data, never executed.
        assert actual == source["content"]
        assert source["id"] == stable_source_id("case-public", company_id=source["company_id"], url=source["url"],
                                               content=source["content"], metadata=meta)
        checks.append({"source_id": source["id"], "capture_id": row["source_id"], "raw_sha256": sha(raw),
                       "text_sha256": file_sha(text_path), "snapshot_sha256": file_sha(snapshot_path),
                       "raw_text_reextraction_matched": True})
    request = json.loads((HERE / "normalization-request.json").read_text())
    original = sources[request["source"]["id"]]
    assert request["source"] == original
    assert len(request["facts"]) == 5
    for fact in request["facts"]:
        location = fact["location"]
        page = original["content"].split("\f")[location["pdf_page"] - 1]
        assert page[location["page_text_start"]:location["page_text_end_exclusive"]] == fact["basis_quote"]
        assert location["row_label"] in fact["basis_quote"]
        assert fact["scope"]["reporting_scope"] == "non_consolidated"
        assert fact["scope"]["accounting_basis_as_stated"] == "日本基準"
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
    reproduction = reproduce_disclosed_fact_source(derived, sources)
    assert reproduction["status"] == "reproduced", reproduction
    facts = json.loads(derived["content"])["facts"]
    expected = {
        "vrain135a-2027interim-basic-eps": ("reported_fact", "26.06", "JPY-per-share"),
        "vrain135a-2027fy-company-eps": ("issuer_guidance", "94.85", "JPY-per-share"),
        "vrain135a-2027interim-operating-income": ("reported_fact", "409000000", "JPY"),
        "vrain135a-2027fy-company-operating-income": ("issuer_guidance", "1449000000", "JPY"),
        "vrain135a-2027fy-company-annual-dividend": ("issuer_guidance", "0", "JPY-per-share"),
    }
    for fact in facts:
        assert (fact["kind"], fact["value"], fact["unit"]) == expected[fact["id"]]
        assert fact["financial_inputs_verified"] is False and fact["meaning_review_required"] is True
    dividend = facts[-1]
    assert dividend["raw_value"] == "0.00"
    assert dividend["normalization"]["raw_numeric_token_verified"] is True
    assert dividend["normalization"]["status"] == "numeric_token_normalized"
    assert not bundle["companies"] and not bundle["theses"]
    for path, expected in frozen.items():
        assert file_sha(path) == expected
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(), "offline_only": True,
        "new_get_count": 0, "database_reads_or_writes": 0, "existing_files_unchanged": True,
        "raw_hashes_verified": 3, "text_hashes_verified": 3, "snapshot_hashes_verified": 3,
        "raw_text_reextractions_matched": 3, "source_ids_recomputed": 3,
        "source_checks": checks, "fact_quote_page_offsets_verified": 5,
        "meaning_review_quotes_verified": len(meaning["citations"]),
        "visual_table_review": meaning["visual_table_review"],
        "reviewed_at": request["review"]["recorded_at"],
        "original_source_id": original["id"], "original_retrieved_at": original["retrieved_at"],
        "derived_source_id": derived["id"], "derived_first_retrieved_at": derived["retrieved_at"],
        "normalized_fact_count": 5, "reproduction": reproduction,
        "normalization_request_sha256": file_sha(HERE / "normalization-request.json"),
        "normalized_bundle_sha256": file_sha(output),
        "financial_inputs_verified": False, "meaning_review_required": True, "model_adopted": False,
        "single_year_dividend_forecast_extended": False,
    }
    write(HERE / "verification.json", report)
    print(json.dumps({key: report[key] for key in ("verified_at", "raw_hashes_verified", "text_hashes_verified", "normalized_fact_count", "original_source_id", "derived_source_id", "model_adopted")}))


if __name__ == "__main__":
    main()
