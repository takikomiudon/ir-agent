"""Offline verification and fact normalization of the frozen 5480 case only.

No HTTP calls or DB operations. Existing case captures/bundle remain unchanged.
The first build uses the execution clock for the derived retrieval; a replay
uses that saved retrieval to reproduce the prior artifact, not to backdate a
new collection. Missing metrics are never generated.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from ir_agent.adapters.common import canonical_json, stable_source_id
from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source
from research_ir_universe import Page


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def file_hash(path):
    return digest_bytes(path.read_bytes())


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n")


def main():
    baseline = json.loads((HERE / "baseline.json").read_text())
    manifest_path = CASE / "manifest.json"
    bundle_path = CASE / "source-bundle.json"
    assert file_hash(manifest_path) == baseline["manifest_sha256"]
    assert file_hash(bundle_path) == baseline["source_bundle_sha256"]
    manifest = json.loads(manifest_path.read_text())
    source_bundle = json.loads(bundle_path.read_text())
    assert len(manifest) == len(source_bundle["sources"]) == 8
    originals = {s["id"]: s for s in source_bundle["sources"]}
    checks = []
    frozen = {manifest_path: file_hash(manifest_path), bundle_path: file_hash(bundle_path)}
    for row in manifest:
        source = next(s for s in originals.values() if s["metadata"]["capture_source_id"] == row["source_id"])
        metadata = source["metadata"]
        raw_path, snapshot_path = CASE / row["raw_file"], CASE / row["snapshot"]
        raw = raw_path.read_bytes()
        snapshot = json.loads(snapshot_path.read_text())
        frozen[raw_path], frozen[snapshot_path] = file_hash(raw_path), file_hash(snapshot_path)
        assert len(raw) == row["byte_count"] == metadata["original_raw_byte_count"]
        assert digest_bytes(raw) == row["sha256"] == snapshot["sha256"] == metadata["original_raw_sha256"]
        assert file_hash(snapshot_path) == metadata["original_transport_snapshot_sha256"]
        assert snapshot["text"] == source["content"]
        assert digest_bytes(source["content"].encode()) == metadata["extraction"]["saved_content_sha256"]
        decoded = raw.decode("utf-8", errors="replace")
        if "html" in row["content_type"]:
            parser = Page()
            parser.feed(decoded)
            reextracted = parser.extract(row["url"])["text"]
        else:
            reextracted = decoded
        assert reextracted == snapshot["text"]
        assert source["id"] == stable_source_id("case-public", company_id=source["company_id"],
                                               url=source["url"], content=source["content"], metadata=metadata)
        checks.append({"capture_id": row["source_id"], "source_id": source["id"], "url": source["url"],
                       "raw_sha256": digest_bytes(raw), "snapshot_sha256": file_hash(snapshot_path),
                       "text_sha256": digest_bytes(source["content"].encode()),
                       "raw_visible_or_plain_text_reextraction_matched": True,
                       "retrieved_at": source["retrieved_at"]})
    policy_path = ROOT / "research/valuation-model-routing-2026-10-15/sources.json"
    policy = json.loads(policy_path.read_text())
    paper = next(s for s in policy["sources"] if s["source_id"] == "damodaran.cyclical-commodity.2009")
    assert digest_bytes(base64.b64decode(paper["raw_pdf_base64"])) == paper["sha256"] == "16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40"
    policy_quotes = []
    for reference in policy["reference_evidence"]:
        if reference["reference_id"] not in {"cyclical-normalize-all", "cyclical-cycle-window", "cyclical-scale"}:
            continue
        page = paper["extracted_text"].split("\f")[reference["pdf_page"] - 1]
        assert re.sub(r"\s+", " ", reference["quote"]) in re.sub(r"\s+", " ", page)
        policy_quotes.append(reference)
    request = json.loads((HERE / "normalization-request.json").read_text())
    assert request["source"] == originals[request["source"]["id"]]
    assert request["company_id"] == "jp:5480"
    assert len(request["facts"]) == 1 <= 4
    fact = request["facts"][0]
    location = fact["location"]
    content = request["source"]["content"]
    assert content[location["source_text_start"]:location["source_text_end_exclusive"]] == fact["basis_quote"]
    period_evidence = location["period_basis"]
    assert content[period_evidence["source_text_start"]:period_evidence["source_text_end_exclusive"]] == period_evidence["quote"]
    output_path = HERE / "normalized-bundle.json"
    first_build = not output_path.exists()
    if first_build:
        bundle = normalize_disclosed_facts(request, now=datetime.now(timezone.utc))
        write_json(output_path, bundle)
    else:
        bundle = json.loads(output_path.read_text())
    replay = normalize_disclosed_facts(request, now=bundle["sources"][1]["retrieved_at"])
    assert replay == bundle
    assert bundle["sources"][0] == request["source"]
    derived = bundle["sources"][1]
    reproduction = reproduce_disclosed_fact_source(derived, originals)
    assert reproduction["status"] == "reproduced", reproduction
    fresh_replay = normalize_disclosed_facts(request, now=datetime.now(timezone.utc))["sources"][1]
    assert fresh_replay["id"] == derived["id"]
    assert fresh_replay["content"] == derived["content"]
    assert fresh_replay["metadata"] == derived["metadata"]
    extracted = json.loads(derived["content"])["facts"]
    assert extracted[0]["value"] == "10973000000"
    assert extracted[0]["kind"] == "reported_fact"
    assert extracted[0]["financial_inputs_verified"] is False
    assert extracted[0]["meaning_review_required"] is True
    assert not bundle["companies"] and not bundle["theses"]
    for path, expected in frozen.items():
        assert file_hash(path) == expected
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(), "offline_only": True,
        "new_get_count": 0, "database_operations": 0,
        "raw_hashes_verified": 8, "snapshot_hashes_verified": 8,
        "saved_text_hashes_verified": 8, "raw_text_reextractions_matched": 8,
        "source_ids_recomputed": 8, "original_case_files_unchanged": True,
        "source_checks": checks, "method_source": {
            "source_id": paper["source_id"], "url": paper["url"], "raw_pdf_sha256": paper["sha256"],
            "raw_pdf_sha256_verified": True, "references": policy_quotes},
        "normalization_request_sha256": file_hash(HERE / "normalization-request.json"),
        "normalized_bundle_sha256": file_hash(output_path),
        "original_source_id": request["source"]["id"], "derived_source_id": derived["id"],
        "derived_first_retrieved_at": derived["retrieved_at"], "normalized_fact_count": 1,
        "normalized_value_jpy": "10973000000", "reproduction": reproduction,
        "deterministic_content_and_id_across_retrieval_times": True,
        "financial_inputs_verified": False, "meaning_review_required": True,
        "newest_financial_release_verified": False, "full_cycle_normalization_verified": False,
        "reinvestment_forecasts_created": False, "valuation_created": False,
    }
    write_json(HERE / "verification.json", report)
    print(json.dumps({key: report[key] for key in ("verified_at", "new_get_count", "raw_hashes_verified", "saved_text_hashes_verified", "normalized_fact_count", "normalized_value_jpy", "original_source_id", "derived_source_id", "financial_inputs_verified", "newest_financial_release_verified")}))


if __name__ == "__main__":
    main()
