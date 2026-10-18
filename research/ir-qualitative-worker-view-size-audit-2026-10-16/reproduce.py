"""Measure the existing reading projection using only a saved job adapter.

Default stdout is deterministic for pinned inputs. --output creates a NEW file
only, never overwrites a frozen report. No Store, SQLite, network, queue or tests.
"""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ir_agent.models import json_text
from ir_agent.qualitative_research import QualitativeResearch


def sha(raw):
    return sha256(raw).hexdigest()


def encoded(value):
    return json_text(value).encode("utf-8")


def cli_pretty(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def fields(value):
    result = []
    for key, item in value.items():
        result.append({"key": key, "value_native_JSON_bytes": len(encoded(item)),
                       "key_value_entry_native_JSON_bytes": len(encoded({key: item})) - 2})
    result.sort(key=lambda item: (-item["value_native_JSON_bytes"], item["key"]))
    # Default separators are comma-space / colon-space. This additive accounting
    # proves reported entry sizes include their actual JSON key/value overhead.
    assert 2 + sum(item["key_value_entry_native_JSON_bytes"] for item in result) + 2 * (len(result) - 1) == len(encoded(value))
    return result


def strings(value, path="", output=None):
    if output is None:
        output = defaultdict(list)
    if isinstance(value, dict):
        for key, item in value.items():
            escaped = key.replace("~", "~0").replace("/", "~1")
            strings(item, path + "/" + escaped, output)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            strings(item, path + "/" + str(index), output)
    elif isinstance(value, str):
        output[value].append(path)
    return output


class SavedJobOnly:
    """Minimal adapter for the existing method, not a Store or new API."""
    connection = None

    def __init__(self, job):
        self.saved = deepcopy(job)
        self.calls = []

    def job(self, job_id):
        if job_id != self.saved["id"]:
            raise ValueError("Unexpected saved job ID")
        self.calls.append(job_id)
        return deepcopy(self.saved)


def run():
    pins = json.loads((HERE / "input-pins.json").read_bytes())
    assert all(sha((ROOT / path).read_bytes()) == digest for path, digest in pins["files"].items())
    base = ROOT / "research/ir-case-studies-2026-10-15/2315/annual-accounting-qualitative-review-2026-10-16"
    packet_bytes = (base / "job-packet.json").read_bytes()
    packet = json.loads(packet_bytes)
    job = json.loads((base / "actual-job.json").read_bytes())
    assert packet == job["packet"] and job["status"] == "completed"
    before = encoded(job)
    adapter = SavedJobOnly(job)
    view = QualitativeResearch(adapter).worker_packet(job["id"])
    assert adapter.calls == [job["id"]] and encoded(job) == before
    assert view["canonical_packet_sha256"] == sha(encoded(packet))
    assert view["sources"] == packet["sources"]
    assert view["frozen_case_document"] == packet["case_snapshot"]["files"]["case_ref"]
    assert view["reference_files"] == {key: item["reference"] for key, item in packet["case_snapshot"]["files"].items() if item is not None}
    assert view["reviewed_sources"] == {key: {name: item for name, item in value.items() if name != "review_file"} for key, value in packet["case_snapshot"]["reviewed_sources"].items()}
    assert view["prior_review"] == packet["prior_review"]
    assert packet_bytes == cli_pretty(packet)
    full_strings, view_strings = strings(packet), strings(view)
    duplicate_records = []
    for text, paths in full_strings.items():
        if len(paths) < 2 or len(text.encode("utf-8")) < 1000:
            continue
        duplicate_records.append({"value_UTF8_sha256": sha(text.encode("utf-8")),
            "value_UTF8_bytes": len(text.encode("utf-8")), "one_JSON_string_bytes": len(encoded(text)),
            "occurrences_in_full": len(paths), "occurrences_in_worker": len(view_strings.get(text, [])),
            "full_JSON_string_bytes_all_occurrences": len(paths) * len(encoded(text)),
            "duplicate_JSON_string_bytes_beyond_one_copy": (len(paths) - 1) * len(encoded(text)),
            "full_JSON_pointers": paths})
    duplicate_records.sort(key=lambda item: -item["duplicate_JSON_string_bytes_beyond_one_copy"])
    prior = packet.get("prior_review")
    completed_request = job["result"]["request"]
    result = {
        "audit_input_recorded_at": pins["recorded_at"], "reproducer_sha256": sha(Path(__file__).read_bytes()),
        "job_id": job["id"], "job_status_as_saved": job["status"],
        "size_convention": {"native": "models.json_text UTF8; sorted keys, default separators, no trailing newline", "CLI_pretty": "json.dumps ensure_ascii=False indent=2 allow_nan=False plus trailing LF; same as current CLI output", "comparison_same_format": True, "token_or_cost_estimation": False},
        "bytes": {"full_saved_file": len(packet_bytes), "full_native": len(encoded(packet)),
                  "worker_native": len(encoded(view)), "native_difference": len(encoded(packet)) - len(encoded(view)),
                  "full_CLI_pretty": len(cli_pretty(packet)), "worker_CLI_pretty": len(cli_pretty(view)),
                  "CLI_pretty_difference": len(cli_pretty(packet)) - len(cli_pretty(view))},
        "SHA256": {"full_native": sha(encoded(packet)), "worker_native": sha(encoded(view)), "worker_CLI_pretty": sha(cli_pretty(view))},
        "full_top_level": fields(packet), "worker_top_level": fields(view),
        "case_snapshot_fields": fields(packet["case_snapshot"]),
        "frozen_file_sizes": [{"key": key, "frozen_object_native_bytes": len(encoded(item)),
            "content_UTF8_bytes": len(item["content"].encode("utf-8")),
            "content_JSON_string_bytes": len(encoded(item["content"])),
            "content_UTF8_sha256": sha(item["content"].encode("utf-8"))}
            for key, item in packet["case_snapshot"]["files"].items() if item is not None],
        "exact_repeated_large_string_values": duplicate_records,
        "duplicate_measure_limit": "Exact equal string values only, UTF8>=1000bytes; no semantic or substring dedup. Duplicate payload counts are not a new API or independent prediction of all JSON savings.",
        "preservation": {"new_sources_whole_objects_exact": True, "source_count": len(view["sources"]),
            "frozen_original_case_document_content_and_reference_exact": True,
            "all_existing_file_references_exact": True, "reviewed_sources_keep_all_fields_except_review_file": True,
            "prior_review_whole_value_exact": True, "prior_review_value_in_this_packet": prior,
            "prior_review_availability": view["prior_review_availability"],
            "frozen_last_review_id": packet["case_snapshot"]["last_review_id"],
            "completed_result_summary_present_in_saved_job": "summary" in completed_request,
            "completed_result_case_observation_present_in_saved_job": "case_observation" in completed_request,
            "completed_result_summary_native_bytes": len(encoded(completed_request["summary"])),
            "completed_result_case_observation_native_bytes": len(encoded(completed_request["case_observation"])),
            "current_completed_result_not_part_of_original_packet_or_projection": "result" not in packet and "result" not in view,
            "implementation_prior_review_path": "qualitative_research.py:_prior_review returns previous request.summary and case_observation with timestamps/hashes; worker_packet copies packet.prior_review wholesale. No new queue or non-null prior fixture executed."},
        "authorization": {"saved_job_status": view["job_status"],
            "current_completion_authorization": view["current_completion_authorization"],
            "not_current_lease_or_complete_permission": True, "authoritative_full_packet_retained": True,
            "frozen_projection_does_not_merge_later_sources_or_current_case": True},
        "execution": {"existing_worker_packet_calls": 1, "saved_job_adapter_job_calls": adapter.calls,
            "actual_Store_initializations": 0, "DB_connections_or_writes": 0, "GETs": 0,
            "new_tests_or_projection_API": 0, "production_changes": 0, "financial_adoptions": 0,
            "capacity_cohort_or_company_limit_or_time_cost_forecasts": 0},
        "input_pins": pins["files"]}
    assert all(sha((ROOT / path).read_bytes()) == digest for path, digest in pins["files"].items())
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(run(), ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as destination:
            destination.write(rendered)
    else:
        print(rendered, end="")
