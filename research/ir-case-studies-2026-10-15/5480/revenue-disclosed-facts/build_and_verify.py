"""Offline one-fact revenue replay from an existing June shareholder message."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from ir_agent.adapters.common import stable_source_id
from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source
from research_ir_universe import Page


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n")


def main():
    baseline = json.loads((HERE / "baseline.json").read_text())
    for relative, expected in baseline["existing_input_files"].items():
        assert file_sha(CASE / relative) == expected
    source_bundle = json.loads((CASE / "source-bundle.json").read_text())
    originals = {s["id"]: s for s in source_bundle["sources"]}
    candidate = next(c for c in json.loads((CASE / "annual-input-followup/candidate-raw-tokens.json").read_text())["candidates"]
                     if c["id"] == "annual-revenue")
    original = originals[candidate["source_id"]]
    metadata = original["metadata"]
    raw_path = CASE.parent / metadata["original_raw_file"]
    snapshot_path = CASE.parent / metadata["original_transport_snapshot"]
    raw, snapshot = raw_path.read_bytes(), json.loads(snapshot_path.read_text())
    assert file_sha(raw_path) == metadata["original_raw_sha256"] == snapshot["sha256"]
    assert len(raw) == metadata["original_raw_byte_count"] == snapshot["byte_count"]
    assert file_sha(snapshot_path) == metadata["original_transport_snapshot_sha256"]
    text = original["content"]
    assert text == snapshot["text"]
    assert hashlib.sha256(text.encode()).hexdigest() == metadata["extraction"]["saved_content_sha256"]
    page = Page()
    page.feed(raw.decode("utf-8", errors="replace"))
    assert page.extract(original["url"])["text"] == text
    assert stable_source_id("case-public", company_id=original["company_id"], url=original["url"],
                            content=text, metadata=metadata) == original["id"]
    assert original["retrieved_at"] == candidate["original_retrieved_at"] == snapshot["retrieved_at"]
    request = json.loads((HERE / "normalization-request.json").read_text())
    assert request["source"] == original and len(request["facts"]) == 1
    fact = request["facts"][0]
    assert fact["raw_value"] == candidate["raw_value"] == "150,866"
    assert fact["basis_quote"] == candidate["basis_quote"]
    loc = fact["location"]
    assert text[loc["text_character_start"]:loc["text_character_end"]] == fact["basis_quote"]
    assert text[loc["value_character_start"]:loc["value_character_end"]] == fact["raw_value"]
    assert fact["period"]["start_date"] == candidate["period_start"] == "2025-04-01"
    assert fact["period"]["end_date"] == candidate["period_end"] == "2026-03-31"
    assert fact["scope"]["accounting_basis"] is None
    old_bundle = json.loads((CASE / "disclosed-facts/normalized-bundle.json").read_text())
    old = old_bundle["sources"][1]
    old_fact = json.loads(old["content"])["facts"][0]
    assert old_bundle["sources"][0] == original
    assert old["metadata"]["original_source_id"] == original["id"]
    assert old_fact["period"]["start_date"] == fact["period"]["start_date"]
    assert old_fact["period"]["end_date"] == fact["period"]["end_date"]
    relation = json.loads((HERE / "same-source-context.json").read_text())
    assert relation["operating_income_derived_source_id"] == old["id"]
    assert relation["operating_income_fact_id"] == old_fact["id"]
    assert relation["independent_original_evidence_added"] is False
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
    extracted = json.loads(derived["content"])["facts"]
    assert len(extracted) == 1
    assert (extracted[0]["kind"], extracted[0]["value"], extracted[0]["unit"]) == ("reported_fact", "150866000000", "JPY")
    assert extracted[0]["financial_inputs_verified"] is False and extracted[0]["meaning_review_required"] is True
    assert not bundle["companies"] and not bundle["theses"]
    for relative, expected in baseline["existing_input_files"].items():
        assert file_sha(CASE / relative) == expected
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(), "new_get_count": 0, "database_reads_or_writes": 0,
        "existing_input_files_unchanged": True, "raw_sha256": file_sha(raw_path),
        "snapshot_sha256": file_sha(snapshot_path), "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "raw_text_reextraction_matched": True, "source_id_recomputed": True,
        "quote_and_value_offsets_verified": True, "reviewed_at": request["review"]["recorded_at"],
        "original_source_id": original["id"], "original_retrieved_at": original["retrieved_at"],
        "derived_source_id": derived["id"], "derived_first_retrieved_at": derived["retrieved_at"],
        "normalized_fact_count": 1, "normalized_revenue_jpy": "150866000000", "reproduction": reproduction,
        "same_original_source_and_annual_period_as_existing_operating_income": True,
        "independent_original_evidence_added": False, "accounting_basis": None,
        "formal_annual_statement_independently_reconciled": False, "financial_inputs_verified": False,
        "meaning_review_required": True, "model_adopted": False, "full_cycle_verified": False,
        "normalized_profit_or_forecast_or_roic_tax_assumptions_created": False,
        "request_sha256": file_sha(HERE / "normalization-request.json"), "bundle_sha256": file_sha(output),
    }
    write(HERE / "verification.json", report)
    print(json.dumps({key: report[key] for key in ("verified_at", "normalized_fact_count", "normalized_revenue_jpy", "original_source_id", "derived_source_id", "independent_original_evidence_added", "model_adopted")}))


if __name__ == "__main__":
    main()
