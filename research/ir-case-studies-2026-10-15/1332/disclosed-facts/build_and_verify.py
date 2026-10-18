"""Offline cited-fact verification; no network/DB or source-file mutation."""
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
sys.path.insert(0, str(ROOT / "scripts"))
from ir_agent.adapters.common import stable_source_id
from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source
from research_ir_universe import Page


def sha(value):
    return hashlib.sha256(value).hexdigest()


def file_sha(path):
    return sha(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n")


def main():
    baseline = json.loads((HERE / "baseline.json").read_text())
    frozen, checks, sources = {}, [], {}
    for relative, expected in baseline["existing_input_files"].items():
        path = CASE / relative
        assert file_sha(path) == expected
        frozen[path] = expected
    for directory in (CASE, CASE / "statement-calendar-followup"):
        manifest = json.loads((directory / "manifest.json").read_text())
        bundle = json.loads((directory / "source-bundle.json").read_text())
        for row in manifest:
            source = next(s for s in bundle["sources"] if s["metadata"]["capture_source_id"] == row["source_id"])
            sources[source["id"]] = source
            metadata = source["metadata"]
            raw_path = CASE.parent / metadata["original_raw_file"]
            snapshot_path = CASE.parent / metadata["original_transport_snapshot"]
            text_path = CASE.parent / metadata["extraction"]["saved_file"]
            for path in (raw_path, snapshot_path, text_path):
                frozen[path] = file_sha(path)
            raw = raw_path.read_bytes()
            snapshot = json.loads(snapshot_path.read_text())
            assert sha(raw) == metadata["original_raw_sha256"] == row.get("sha256", row.get("raw_sha256"))
            assert len(raw) == row["byte_count"] == metadata["original_raw_byte_count"]
            assert file_sha(snapshot_path) == metadata["original_transport_snapshot_sha256"]
            assert file_sha(text_path) == metadata["extraction"]["sha256"]
            assert text_path.read_bytes().decode("utf-8") == snapshot["text"] == source["content"]
            assert source["retrieved_at"] == row["retrieved_at"] == snapshot["retrieved_at"]
            if metadata["extraction"]["kind"] == "pdf_text":
                reextracted = subprocess.run(["pdftotext", "-layout", str(raw_path), "-"], check=True, capture_output=True).stdout.decode("utf-8")
            elif metadata["extraction"]["kind"] == "html_visible_text":
                parser = Page()
                parser.feed(raw.decode("utf-8", errors="replace"))
                reextracted = parser.extract(source["url"])["text"]
            else:
                reextracted = raw.decode("utf-8")
            assert reextracted == source["content"]
            assert stable_source_id("case-public", company_id=source["company_id"], url=source["url"],
                                    content=source["content"], metadata=metadata) == source["id"]
            checks.append({"capture_id": row["source_id"], "source_id": source["id"], "url": source["url"],
                           "raw_sha256": sha(raw), "text_sha256": file_sha(text_path),
                           "snapshot_sha256": file_sha(snapshot_path), "raw_text_reextraction_matched": True,
                           "retrieved_at": source["retrieved_at"]})
    assert len(checks) == 7
    request = json.loads((HERE / "normalization-request.json").read_text())
    original = sources[request["source"]["id"]]
    assert request["source"] == original
    assert len(request["facts"]) == 4
    for fact in request["facts"]:
        location = fact["location"]
        page = original["content"].split("\f")[location["pdf_page"] - 1]
        assert page[location["page_text_start"]:location["page_text_end_exclusive"]] == fact["basis_quote"]
        assert location["column_label"]
        assert location["row_label"] in fact["basis_quote"]
    review = json.loads((HERE / "meaning-review.json").read_text())
    for citation in review["citations"]:
        page = sources[citation["source_id"]]["content"].split("\f")[citation["pdf_page"] - 1]
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
        "nissui1332-2027q1-basic-eps": ("reported_fact", "24.53", "JPY-per-share"),
        "nissui1332-2027fy-company-eps": ("issuer_guidance", "95.62", "JPY-per-share"),
        "nissui1332-2027q1-consolidated-operating-income": ("reported_fact", "12435000000", "JPY"),
        "nissui1332-2027fy-company-operating-income": ("issuer_guidance", "42500000000", "JPY"),
    }
    for fact in facts:
        assert (fact["kind"], fact["value"], fact["unit"]) == expected[fact["id"]]
        assert fact["financial_inputs_verified"] is False and fact["meaning_review_required"] is True
    assert not bundle["companies"] and not bundle["theses"]
    for path, expected_hash in frozen.items():
        assert file_sha(path) == expected_hash
    verification = {
        "verified_at": datetime.now(timezone.utc).isoformat(), "offline_only": True,
        "new_get_count": 0, "database_operations": 0, "existing_inputs_unchanged": True,
        "raw_hashes_verified": 7, "text_hashes_verified": 7, "snapshot_hashes_verified": 7,
        "raw_text_reextractions_matched": 7, "source_ids_recomputed": 7,
        "sources": checks, "fact_quote_page_offsets_verified": 4,
        "meaning_review_quotes_verified": len(review["citations"]),
        "visual_table_checks": [{"pdf_page": page, "saved_image": f"statement-p{page}.png",
                                  "image_sha256": file_sha(HERE / f"statement-p{page}.png"),
                                  "source_id": original["id"], "scope": "row/column distinction checked by agent; financial meaning remains unverified"}
                                 for page in (1, 7)],
        "original_source_id": original["id"], "original_retrieved_at": original["retrieved_at"],
        "derived_source_id": derived["id"], "derived_first_retrieved_at": derived["retrieved_at"],
        "normalized_fact_count": 4, "reproduction": reproduction,
        "normalization_request_sha256": file_sha(HERE / "normalization-request.json"),
        "normalized_bundle_sha256": file_sha(output),
        "financial_inputs_verified": False, "meaning_review_required": True,
        "model_adopted": False, "cycle_normalization_verified": False,
        "new_financial_forecasts_created": False,
    }
    write(HERE / "verification.json", verification)
    print(json.dumps({key: verification[key] for key in ("verified_at", "raw_hashes_verified", "text_hashes_verified", "snapshot_hashes_verified", "normalized_fact_count", "original_source_id", "derived_source_id", "financial_inputs_verified", "model_adopted")}))


if __name__ == "__main__":
    main()
