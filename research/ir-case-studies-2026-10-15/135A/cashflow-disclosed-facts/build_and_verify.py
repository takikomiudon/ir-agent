"""Offline extraction replay of four reported CF rows; no CF/model arithmetic."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
INPUT = CASE / "library-followup"
sys.path.insert(0, str(HERE.parents[3] / "src"))
from ir_agent.adapters.common import stable_source_id
from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n")


def main():
    baseline = json.loads((HERE / "baseline.json").read_text())
    frozen = {CASE / name: expected for name, expected in baseline["existing_input_files"].items()}
    for path, expected in frozen.items():
        assert file_sha(path) == expected
    manifest = json.loads((INPUT / "manifest.json").read_text())
    originals = {s["id"]: s for s in json.loads((INPUT / "source-bundle.json").read_text())["sources"]}
    checks = []
    for row in manifest:
        source = next(s for s in originals.values() if s["metadata"]["capture_source_id"] == row["source_id"])
        meta = source["metadata"]
        raw = CASE.parent / meta["original_raw_file"]
        snapshot = CASE.parent / meta["original_transport_snapshot"]
        saved_text = CASE.parent / meta["extraction"]["saved_file"]
        assert file_sha(raw) == row["raw_sha256"] == meta["original_raw_sha256"]
        assert raw.stat().st_size == row["byte_count"] == meta["original_raw_byte_count"]
        assert file_sha(snapshot) == meta["original_transport_snapshot_sha256"]
        assert file_sha(saved_text) == row["text_sha256"] == meta["extraction"]["sha256"]
        capture = json.loads(snapshot.read_text())
        assert saved_text.read_bytes().decode("utf-8") == capture["text"] == source["content"]
        assert capture["retrieved_at"] == row["retrieved_at"] == source["retrieved_at"]
        if meta["extraction"]["kind"] == "pdf_text":
            text = subprocess.run(["pdftotext", "-layout", str(raw), "-"], check=True, capture_output=True).stdout.decode("utf-8")
        else:
            text = raw.read_bytes().decode("utf-8")  # Code/index are data only.
        assert text == source["content"]
        assert source["id"] == stable_source_id("case-public", company_id=source["company_id"], url=source["url"],
                                               content=source["content"], metadata=meta)
        checks.append({"source_id": source["id"], "raw_sha256": file_sha(raw), "text_sha256": file_sha(saved_text),
                       "snapshot_sha256": file_sha(snapshot), "raw_text_reextraction_matched": True})
    request = json.loads((HERE / "normalization-request.json").read_text())
    original = originals[request["source"]["id"]]
    assert request["source"] == original
    assert len(request["facts"]) == 4
    for fact in request["facts"]:
        location = fact["location"]
        assert location["pdf_page"] == 8 and location["printed_page"] == 6
        page = original["content"].split("\f")[7]
        assert page[location["page_text_start"]:location["page_text_end_exclusive"]] == fact["basis_quote"]
        assert page[location["row_text_start"]:location["row_text_end_exclusive"]] == location["raw_row_text"]
        assert page[location["cell_token_start"]:location["cell_token_end_exclusive"]] == fact["raw_value"]
        assert fact["period"]["start_date"] == "2026-03-01" and fact["period"]["end_date"] == "2026-08-31"
        assert fact["kind"] == "reported_fact"
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
    reproduction = reproduce_disclosed_fact_source(derived, originals)
    assert reproduction["status"] == "reproduced", reproduction
    facts = json.loads(derived["content"])["facts"]
    expected = {
        "vrain135a-2027interim-operating-cashflow": ("223", "223000000"),
        "vrain135a-2027interim-depreciation-cf-adjustment": ("30", "30000000"),
        "vrain135a-2027interim-ppe-acquisition-cashflow": ("△100", "-100000000"),
        "vrain135a-2027interim-receivables-contract-assets-cf-adjustment": ("154", "154000000"),
    }
    for fact in facts:
        assert (fact["raw_value"], fact["value"]) == expected[fact["id"]]
        assert fact["unit"] == "JPY" and fact["kind"] == "reported_fact"
        assert fact["financial_inputs_verified"] is False and fact["meaning_review_required"] is True
        assert fact["normalization"]["status"] == "numeric_token_normalized"
    assert not bundle["companies"] and not bundle["theses"]
    for path, expected_hash in frozen.items():
        assert file_sha(path) == expected_hash
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(), "new_get_count": 0, "database_reads_or_writes": 0,
        "existing_inputs_unchanged": True, "raw_hashes_verified": 3, "text_hashes_verified": 3,
        "snapshot_hashes_verified": 3, "raw_text_reextractions_matched": 3, "source_ids_recomputed": 3,
        "source_checks": checks, "fact_quote_row_cell_offsets_verified": 4,
        "meaning_review_quotes_verified": len(meaning["citations"]), "visual_table_review": meaning["visual_table_review"],
        "reviewed_at": request["review"]["recorded_at"], "original_source_id": original["id"],
        "original_retrieved_at": original["retrieved_at"], "derived_source_id": derived["id"],
        "derived_first_retrieved_at": derived["retrieved_at"], "normalized_fact_count": 4,
        "normalized_bundle_sha256": file_sha(output), "normalization_request_sha256": file_sha(HERE / "normalization-request.json"),
        "reproduction": reproduction, "financial_inputs_verified": False, "meaning_review_required": True,
        "working_capital_or_reinvestment_or_fcff_calculated": False, "model_adopted": False,
    }
    write(HERE / "verification.json", report)
    print(json.dumps({key: report[key] for key in ("verified_at", "raw_hashes_verified", "normalized_fact_count", "original_source_id", "derived_source_id", "model_adopted")}))


if __name__ == "__main__":
    main()
