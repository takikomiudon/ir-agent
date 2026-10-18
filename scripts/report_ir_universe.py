#!/usr/bin/env python3
"""Build reviewable IR directory files from saved, audited records; no network."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path


LEVEL = {"form_fields_verified": "質問入力欄確認", "ir_email_verified": "IRメール確認", "official_form_link_only": "案内・リンクのみ", "none": "未確認"}
ACCESS = {"not_stated": "個人条件の明示未確認", "explicit": "個人受付の明示あり", "explicitly_allowed": "個人受付の明示あり", "explicit_individual": "個人受付の明示あり", "restricted": "個人等に制限あり"}
SUITABILITY = {"candidate": "窓口候補", "restricted": "受付対象に制限", "no_individual_reply": "個別回答なし", "unconfirmed": "未確認"}
STATUS = {"confirmed": "確認済み", "provisional": "追加確認", "unconfirmed": "未確認"}
LOCAL_GET_STOPS = {"robots_disallowed", "robots_access_denied_stopped", "robots_unreachable_stopped", "host_access_denied_stopped", "environment_circuit_breaker_open"}


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cell(value):
    text = str(value or "").replace("\n", " ")
    return "".join("\\" + character if character in "\\`*_{}[]()<>#!|~" else character
                   for character in text)


def subset_csv(root, filename, records):
    fields = ["security_code", "company_name", "market", "jpx_sector", "investigation_status", "verification_level", "outreach_suitability", "individual_access", "contact_url", "public_ir_emails", "manual_review_required", "unconfirmed_reason", "limitations"]
    with (root / filename).open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = {key: record.get(key, "") for key in fields}
            for key, value in row.items():
                if isinstance(value, list):
                    row[key] = " | ".join(value)
            writer.writerow(row)


def evidence_index(root, records):
    paths = {str(path.relative_to(root)) for path in (root / "evidence").rglob("*") if path.is_file()}
    paths.update(x["snapshot"] for record in records for x in record.get("evidence", []))
    paths.update(x["snapshot"] for record in records for x in record.get("fetches", []))
    items = []
    for relative in sorted(paths):
        path = root / relative
        raw = path.read_bytes()
        item = {"snapshot": relative, "archive_file_sha256": hashlib.sha256(raw).hexdigest(), "byte_count": len(raw)}
        if path.suffix == ".json":
            data = json.loads(raw)
            if isinstance(data, dict):
                for key in ("requested_url", "url", "retrieved_at", "http_status", "extraction_method"):
                    if key in data:
                        item[key] = data[key]
                if data.get("sha256"):
                    item["recorded_capture_sha256"] = data["sha256"]
        items.append(item)
    save(root / "evidence-index.json", {"generated_at": datetime.now(timezone.utc).isoformat(), "snapshot_count": len(items),
         "hash_note": "archive_file_sha256 hashes the stored file bytes. recorded_capture_sha256 preserves the original capture's digest; an extracted JSON archive is not the original HTTP response body and cannot reproduce its digest.", "snapshots": items})


def retry_overview(root, records):
    marker_path = root / "retry-current-run.json"
    if not marker_path.exists():
        return None
    marker = json.loads(marker_path.read_text())
    manifest = json.loads((root / marker["manifest"]).read_text())
    summary_path = root / manifest["run_directory"] / "summary.json"
    # A later survey must not make the old execution appear to have fetched
    # its new records. Its saved observation is historical and immutable.
    if (root / "adaptive-current-run.json").exists():
        return json.loads(summary_path.read_text()) if summary_path.exists() else None
    selected = set(manifest["selected_security_codes"])
    current = [r for r in records if r["security_code"] in selected
               and r.get("attempted_at", "") >= manifest["started_at"] and r.get("previous_attempts")]
    local_stops = LOCAL_GET_STOPS

    def attempted(record):
        return any(f.get("http_status") is not None or (f.get("error") and f["error"] not in local_stops)
                   for f in record.get("fetches", []))

    attempted_rows = [r for r in current if attempted(r)]
    before_path = root / manifest["run_directory"] / "before" / "companies.json"
    before_records = json.loads(before_path.read_text())["companies"]
    ever_attempted_codes = {r["security_code"] for r in [*before_records, *records] if attempted(r)}
    circuit_only = [r for r in current if r.get("fetches")
                    and all(f.get("error") == "environment_circuit_breaker_open" for f in r["fetches"])]
    policy_only = [r for r in current if not attempted(r)
                   and any(f.get("error") in local_stops - {"environment_circuit_breaker_open"} for f in r.get("fetches", []))]
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "started_at": manifest["started_at"],
        "collection_status": "stopped_by_environment_circuit" if circuit_only else manifest.get("collection_status", "not_declared"),
        "selected_company_count": len(selected),
        "updated_record_count": len(current),
        "company_content_get_attempt_count": len(attempted_rows),
        "universe_company_content_get_attempt_count_across_baseline_and_retry": len(ever_attempted_codes),
        "company_successful_public_body_count": sum(r.get("successful_official_page_count", 0) > 0 for r in current),
        "company_no_get_circuit_stop_count": len(circuit_only),
        "company_no_get_policy_stop_count": len(policy_only),
        "company_no_get_other_count": len(current) - len(attempted_rows) - len(circuit_only) - len(policy_only),
        "company_not_updated_count": len(selected) - len(current),
        "retry_record_statuses": dict(Counter(r["investigation_status"] for r in current)),
        "new_known_channels_pending_codex_review": sum(r.get("manual_review_required") is not False for r in current
                                                        if r["investigation_status"] in ("confirmed", "provisional")),
        "before_universe_statuses": manifest["baseline_summary"]["by_investigation_status"],
        "after_universe_statuses": dict(Counter(r["investigation_status"] for r in records)),
        "before_environment_failure_count": manifest["baseline_summary"]["blocked_network_count"],
        "after_environment_failure_count": sum(r.get("unconfirmed_reason") == "environment_transport_failure" for r in records),
        "count_note": "Updated records include local circuit-stop diagnostics. They do not prove company GETs. Content GET attempts exclude robots checks, preflight, and local access/circuit stops; HTTP failures and request exceptions count as attempts.",
        "request_scope": "public GET only; no form or email submissions",
        "baseline_directory": str(Path(marker["run_directory"]) / "before"),
    }
    save(summary_path, result)
    return result


def at_or_after(value, boundary):
    if not isinstance(value, str) or not isinstance(boundary, str):
        return False
    try:
        left = datetime.fromisoformat(value.replace("Z", "+00:00"))
        right = datetime.fromisoformat(boundary.replace("Z", "+00:00"))
        return left.utcoffset() is not None and right.utcoffset() is not None and left >= right
    except ValueError:
        return False


def content_get_attempted(record):
    # These are company content-page attempts; robots and preflight belong
    # to the aggregate HTTP request counters in collection-runs instead.
    # An unreachable-robots wrapper retains nested robot GETs but dispatches
    # no company body request. Its local stop must not count as content.
    return any(f.get("error") not in LOCAL_GET_STOPS and (f.get("http_status") is not None or f.get("error"))
               for f in record.get("fetches", []))


def adaptive_collection_runs(root, started_at):
    """Use one observation per execution, preferring its final over progress.

    The collector's total counts actual requests.get attempts, including
    robots, preflight and redirects; it is not a count of investigated firms.
    """
    observations = {}
    for path in sorted((root / "collection-runs").glob("*.json")):
        value = json.loads(path.read_text())
        if not isinstance(value, dict) or not at_or_after(value.get("started_at"), started_at):
            continue
        key = path.name.removesuffix("-progress.json").removesuffix(".json")
        final = not path.name.endswith("-progress.json")
        if key not in observations or final:
            observations[key] = {"snapshot": str(path.relative_to(root)), "final": final, **value}
    return list(observations.values())


def adaptive_overview(root, records):
    marker_path = root / "adaptive-current-run.json"
    if not marker_path.exists():
        return None
    marker = json.loads(marker_path.read_text())
    manifest = json.loads((root / marker["manifest"]).read_text())
    started_at = manifest["started_at"]
    baseline = manifest["baseline_summary"]
    current = [record for record in records if at_or_after(record.get("attempted_at"), started_at)]
    attempts = [record for record in current if content_get_attempted(record)]
    runs = adaptive_collection_runs(root, started_at)
    controller = None
    controller_path = None
    for relative in [marker.get("progress"), str(Path(marker["run_directory"]) / "controller-progress.json"),
                     str(Path(marker["run_directory"]) / "progress.json")]:
        if relative and (root / relative).exists():
            controller_path = relative
            controller = json.loads((root / relative).read_text())
            break
    rate_changes = [{"collection_snapshot": run["snapshot"], **change}
                    for run in runs for change in run.get("rate_adjustments", [])]
    events_path = root / marker["run_directory"] / "events.jsonl"
    controller_events = []
    malformed_event_count = 0
    if events_path.exists():
        for line in events_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                malformed_event_count += 1
                continue
            if isinstance(event, dict) and at_or_after(event.get("at_utc"), started_at):
                controller_events.append(event)
    cooldowns = [event for event in controller_events if event.get("event") == "cooldown_scheduled"]
    controller_rates = []
    for event in controller_events:
        rate = event.get("global_rps")
        if rate is not None and (not controller_rates or controller_rates[-1]["global_rps"] != rate):
            controller_rates.append({key: event.get(key) for key in ("at_utc", "event", "global_rps")})
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "started_at": started_at,
        "run_directory": marker["run_directory"],
        "goal": manifest.get("goal"),
        "universe_company_count": manifest["universe_count"],
        "initial_environment_failure_count": len(manifest.get("network_pending_codes", [])),
        "initial_additional_followup_count": len(manifest.get("followup_codes", [])),
        "initial_universe_statuses": baseline["by_investigation_status"],
        "current_universe_statuses": dict(Counter(record["investigation_status"] for record in records)),
        "latest_updated_record_count_since_goal_start": len(current),
        "latest_company_content_get_attempt_count_since_goal_start": len(attempts),
        "latest_company_successful_public_body_count_since_goal_start": sum(
            record.get("successful_official_page_count", 0) > 0 for record in attempts),
        "latest_updated_record_without_content_get_count": len(current) - len(attempts),
        "current_environment_failure_count": sum(record.get("unconfirmed_reason") == "environment_transport_failure" for record in records),
        "current_known_channels_pending_review_count": sum(record.get("manual_review_required") is not False for record in records
                                                            if record["investigation_status"] in ("confirmed", "provisional")),
        "collection_execution_count": len(runs),
        "collection_http_get_attempt_count": sum(run.get("http_get_attempt_count", 0) for run in runs),
        "collection_preflight_http_get_attempt_count": sum(run.get("preflight_http_get_attempt_count", 0) for run in runs),
        "collection_company_http_get_attempt_count": sum(run.get("company_http_get_attempt_count", 0) for run in runs),
        "collection_http_429_count": sum(run.get("http_429_count", 0) for run in runs),
        "collection_common_transport_503_count": sum(run.get("common_transport_503_count", 0) for run in runs),
        "collection_site_specific_503_count": sum(run.get("site_specific_503_count", 0) for run in runs),
        "collection_rps_observations": [{"snapshot": run["snapshot"], "configured_global_rps": run.get("configured_global_rps"),
                                         "final_global_rps": run.get("final_global_rps"), "minimum_global_rps": run.get("minimum_global_rps"),
                                         "started_at": run.get("started_at"), "status": run.get("status")}
                                        for run in runs],
        "collection_rate_adjustments": rate_changes,
        "collection_runs": runs,
        "controller_progress_snapshot": controller_path,
        "controller_progress": controller,
        "controller_status": controller.get("status") if controller else "not_observed",
        "controller_phase_scope": "network recovery; completion of this phase does not imply completion of additional contact followups or verification of all IR contacts",
        "controller_pending_network_company_count": controller.get("pending_network_company_count") if controller else None,
        "controller_exhausted_network_company_count": controller.get("exhausted_network_company_count") if controller else None,
        "controller_exhausted_codes_requiring_followup": controller.get("exhausted_codes_requiring_followup", []) if controller else [],
        "controller_completed_batch_count": controller.get("completed_batch_count") if controller else None,
        "controller_child_http_get_attempt_count": controller.get("actual_http_get_attempt_count") if controller else None,
        "controller_current_global_rps": controller.get("current_global_rps") if controller else None,
        "controller_current_cooldown": controller.get("cooldown") if controller else None,
        "controller_events_snapshot": str(events_path.relative_to(root)) if events_path.exists() else None,
        "controller_malformed_event_line_count": malformed_event_count,
        "controller_rps_changes": controller_rates,
        "controller_scheduled_cooldown_count": len(cooldowns),
        "controller_scheduled_cooldown_seconds": sum(event.get("cooldown", {}).get("seconds", 0) for event in cooldowns),
        "controller_cooldown_events": cooldowns,
        "initial_followup_codes_not_updated_since_goal_start": sorted(set(manifest.get("followup_codes", [])) - {record["security_code"] for record in current}),
        "initial_configuration": manifest.get("configuration", {}),
        "count_note": "Latest records count companies once; repeated executions are not retained in those counts. Collection totals sum each execution once, prefer final over progress, and include robots, preflight and redirects. Controller diagnostics and cooldowns are reported separately. Completion of collection does not mean every company has a verified IR contact.",
        "request_scope": "finite public GET survey; no scheduled recurring collection or IR submissions",
        "baseline_directory": str(Path(marker["run_directory"]) / "before"),
    }
    save(root / marker["run_directory"] / "summary.json", result)
    return result


def adaptive_communication_lines(adaptive, retry=None, retry_path=None):
    path = str(Path(adaptive["run_directory"]) / "summary.json")
    initial = adaptive["initial_universe_statuses"]
    pending = adaptive["controller_pending_network_company_count"]
    exhausted = adaptive["controller_exhausted_network_company_count"]
    pending_text = "未観測" if pending is None else f"{pending:,}社"
    exhausted_text = "未観測" if exhausted is None else f"{exhausted:,}社"
    rates = adaptive["collection_rps_observations"]
    controller_reference = (f"[制御記録]({adaptive['controller_progress_snapshot']})を参照する。"
                            if adaptive["controller_progress_snapshot"] else "制御記録はまだ保存されていない。")
    rate_text = "取得実行の観測なし"
    if rates:
        rate_text = f"最初の設定{rates[0]['configured_global_rps']} RPS／最後の実行の最終値{rates[-1]['final_global_rps']} RPS"
    lines = [
        f"[今回の適応型調査集計]({path})（開始 {adaptive['started_at']}）。目標は{adaptive['universe_company_count']:,}社。開始時点は窓口確認{initial.get('confirmed', 0)}社／案内等{initial.get('provisional', 0)}社、通信失敗の再開対象{adaptive['initial_environment_failure_count']:,}社、用途・入力欄等の追加点検対象{adaptive['initial_additional_followup_count']:,}社だった。[開始時の一覧・検証]({adaptive['baseline_directory']}/)を保存している。", "",
        f"開始後に新しい取得記録へ更新された会社は{adaptive['latest_updated_record_count_since_goal_start']:,}社。各社の最新記録に企業本文GETの試行がある会社は{adaptive['latest_company_content_get_attempt_count_since_goal_start']:,}社、公開本文の成功がある会社は{adaptive['latest_company_successful_public_body_count_since_goal_start']:,}社。GET前の停止も行更新に含まれ得るため、更新社数と取得社数を分けている。再取得を繰り返した会社は、この社数では一度だけ数える。", "",
        f"今回のcollection-runs {adaptive['collection_execution_count']}実行を合算した実HTTP GET試行は{adaptive['collection_http_get_attempt_count']:,}回（robots・事前接続確認・リダイレクトも含む）。最終記録と進行記録を重複計上しない。HTTP429は{adaptive['collection_http_429_count']}回、共通経路のHTTP503は{adaptive['collection_common_transport_503_count']}回、サイト固有のHTTP503は{adaptive['collection_site_specific_503_count']}回。企業本文GETの社数やIR受付確認数とは異なる。", "",
        f"取得頻度の観測：{rate_text}。[集計]({path})に実行ごとの設定・最終値、実行中の減速、制御側のRPS推移を記録する。制御側だけの子collector GET累計は{adaptive['controller_child_http_get_attempt_count'] if adaptive['controller_child_http_get_attempt_count'] is not None else '未観測'}回で、開始後の手動実行も含む上記の全実行合算とは区別する。", "",
        f"制御状況は `{adaptive['controller_status']}`。通信再開工程の未処理は{pending_text}、試行上限等で別途再点検が必要な会社は{exhausted_text}。{controller_reference}この工程が完了しても、追加窓口点検や全社のIR受付確認が完了したとは扱わない。confirmed／provisional／unconfirmedは各社の証拠に従って維持する。", "",
        f"制御側が予定したcooldownは{adaptive['controller_scheduled_cooldown_count']}回・計{adaptive['controller_scheduled_cooldown_seconds']:g}秒。予定時間であり、実際に待ち終えた時間の測定ではない。現在の待機理由・再開予定時刻は[集計]({path})の controller_current_cooldown に保存する。", "",
    ]
    if retry and retry_path:
        lines += [
            f"[過去の再試行集計]({retry_path})は当時の観測を凍結して参照する。当時の企業本文GETは{retry['company_content_get_attempt_count']}社、公開本文成功は{retry['company_successful_public_body_count']}社だった。過去の共通HTTP503と銘柄コード前半への取得の偏りを、今回の取得結果へ無条件に当てはめない。サービス内部の根本原因は特定していない。", "",
        ]
    maximum_rps = (adaptive.get("controller_progress") or {}).get("maximum_global_rps")
    if isinstance(maximum_rps, (int, float)) and not isinstance(maximum_rps, bool) and 0 < maximum_rps < float("inf"):
        lines += [
            f"保存された制御設定の試行上限は{maximum_rps:g} RPS。以下の再開例もこの上限以下に抑える。調査側の試行方針であり、サービスの公開quotaや安全な頻度を実証した値ではない。", "",
        ]
    lines += [
        "単一collectorを使い、robots・事前接続確認・リダイレクトを含む全GETの合算頻度を制限する。サイトごとの間隔も維持し、Retry-After、robots、403・429など個別のアクセス制限を尊重する。共通経路の失敗は減速・停止・cooldownの根拠として記録し、会社によるIR受付拒否と混同しない。TLS検証と管理された接続経路を維持する。", "",
        "以下は通信失敗の会社だけを再取得する一度限りのコマンド。実行中のcollectorと同時に起動しない。開始前に接続状況を確認し、共通障害時は待機する。旧試行・証拠と未着手会社の旧記録を保持し、定期取得は登録しない。追加窓口点検は保存された公式リンク・個別証拠に従って進める。", "",
    ]
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory
    document = json.loads((root / "companies.json").read_text())
    records = document["companies"]
    saved_paths = list((root / "records").glob("*.json"))
    if saved_paths:
        saved = {path.stem: json.loads(path.read_text()) for path in saved_paths}
        compiled = {record["security_code"]: record for record in records}
        if saved != compiled:
            parser.error("companies.json differs from records/. Run research_ir_universe.py --compile-only before building the report.")
    known = [x for x in records if x["investigation_status"] in ("confirmed", "provisional")]
    candidates = [x for x in known if x["outreach_suitability"] == "candidate" and x.get("manual_review_required") is False]
    blocked = [x for x in records if x.get("unconfirmed_reason") == "environment_transport_failure"]
    blocked_codes = {x["security_code"] for x in blocked}
    other_unconfirmed = [x for x in records if x["investigation_status"] == "unconfirmed" and x["security_code"] not in blocked_codes]
    other_followups = [x for x in records if x["investigation_status"] != "confirmed" and x["security_code"] not in blocked_codes]
    restricted = [x for x in known if x["outreach_suitability"] in ("restricted", "no_individual_reply")]
    summary = dict(document["summary"])
    summary["codex_reviewed_contact_candidate_count"] = len(candidates)
    summary["codex_reviewed_verified_candidate_count"] = sum(x["investigation_status"] == "confirmed" for x in candidates)
    summary["reviewer_kind"] = "codex_agents; not human investor approval"
    summary["known_channels_with_pending_manual_review"] = sum(x.get("manual_review_required") is not False for x in known)
    summary["blocked_network_count"] = len(blocked)
    summary["additional_contact_followup_count"] = len(other_followups)
    summary["official_get_attempt_company_count_latest_records"] = summary["official_get_company_count"]
    summary["successful_public_page_company_count_latest_records"] = summary["companies_with_successful_public_page_this_run"]
    summary["get_count_scope_note"] = "Legacy *_current_run and *_this_run counts summarize latest saved company records, not a single collector execution. See the separately dated retry/adaptive summaries for each execution's GETs."
    retry = retry_overview(root, records)
    adaptive = adaptive_overview(root, records)
    if retry:
        summary["latest_retry_summary"] = str(Path(json.loads((root / "retry-current-run.json").read_text())["run_directory"]) / "summary.json")
        summary["official_get_attempt_company_count_across_baseline_and_retry"] = retry["universe_company_content_get_attempt_count_across_baseline_and_retry"]
        if adaptive:
            summary["historical_retry_summary"] = summary["latest_retry_summary"]
            summary["historical_retry_summary_frozen"] = True
    if adaptive:
        summary["latest_adaptive_summary"] = str(Path(adaptive["run_directory"]) / "summary.json")
        summary["adaptive_company_content_get_attempt_count_latest_records"] = adaptive["latest_company_content_get_attempt_count_since_goal_start"]
        summary["adaptive_collection_http_get_attempt_count"] = adaptive["collection_http_get_attempt_count"]
    save(root / "coverage.json", summary)
    document["summary"] = summary
    save(root / "companies.json", document)
    evidence_index(root, records)
    for filename, subset in [("contact-candidates.csv", candidates), ("restricted.csv", restricted), ("retry-network-errors.csv", blocked), ("other-unconfirmed.csv", other_unconfirmed), ("additional-followups.csv", other_followups)]:
        subset_csv(root, filename, subset)
    save(root / "retry-network-errors.json", {"generated_at": document["generated_at"], "reason": "environment_transport_failure", "company_count": len(blocked), "security_codes": [x["security_code"] for x in blocked], "automatically_scheduled": False})

    companies, sources = [], []
    for record in candidates:
        code = record["security_code"]
        company_id = "jp:" + code
        companies.append({"id": company_id, "name": record["company_name"], "security_code": code,
                          "status": "watch", "held": False,
                          "screening_reason": "公開IR窓口の調査候補。株価・流動性・業績・投資仮説は未検証。",
                          "ir_contact": {key: record.get(key) for key in ("contact_url", "channels", "public_ir_emails", "verification_level", "individual_access", "conditions", "completed_at", "manual_review")},
                          "listing_verification": {"market": record["market"], "jpx_sector": record["jpx_sector"], "base_data_as_of": "2026-09-30", "observed_changes_through": "2026-10-11", "current_day_listing_guaranteed": False}})
        groups = defaultdict(list)
        for evidence in record.get("evidence", []):
            groups[(evidence["url"], evidence["retrieved_at"], evidence["snapshot"])].append(evidence)
        for (url, retrieved, snapshot), group in groups.items():
            quotes = [x["quote"] for x in group]
            content = "\n".join(dict.fromkeys(quotes))
            metadata = {"source_role": "ir_contact_details", "financial_evidence": False,
                        "snapshot": snapshot, "extraction_method": "verbatim public contact evidence; contact details are not earnings evidence",
                        "quote_locations": [{key: x[key] for key in ("quote", "extraction_scope", "field_path", "source_link_url", "role") if key in x} for x in group]}
            derivation = record.get("manual_review", {}).get("public_email_derivation")
            if derivation and derivation.get("snapshot") == snapshot:
                metadata["public_email_derivation"] = derivation
            identity = json.dumps([company_id, url, retrieved, content, metadata], ensure_ascii=False, sort_keys=True)
            digest = hashlib.sha256(identity.encode()).hexdigest()[:24]
            sources.append({"id": "ir-universe-contact:" + digest, "company_id": company_id,
                            "title": record["company_name"] + "：公開IR窓口・受付条件", "url": url,
                            "source_type": "public_disclosure", "published_at": None, "retrieved_at": retrieved,
                            "content": content, "requires_research": False,
                            "metadata": metadata})
    save(root / "watchlist-bundle.json", {"schema_version": 1, "companies": companies, "sources": sources, "theses": []})

    statuses = Counter(x["investigation_status"] for x in records)
    resume_rps = 1
    maximum_rps = ((adaptive or {}).get("controller_progress") or {}).get("maximum_global_rps")
    if isinstance(maximum_rps, (int, float)) and not isinstance(maximum_rps, bool) and 0 < maximum_rps < resume_rps:
        resume_rps = maximum_rps
    report_created_at_jst = datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
    lines = [
        "# 東証国内普通株のIR窓口・全社調査一覧", "",
        f"母集団基準日：2026年10月11日（日本時間）。集計作成時刻：{report_created_at_jst}。各社の取得・点検時刻は保存記録を参照。保有期間の前提は数カ月〜1年。", "",
        f"対象は **{len(records):,}社**。全社の銘柄とサイトURLを用意し、取得結果・未確認理由を各社に保存した。ただし、**全社のIR窓口確認は完了していない**。接続失敗や通信停止で{len(blocked):,}社が未確認。接続失敗をIR窓口不存在・企業側の受付拒否と判定していない。", "",
        f"IRメール・質問入力欄までの確認済みは **{statuses['confirmed']}社**、案内リンクや会社との対応など追加確認が必要な会社は **{statuses['provisional']}社**。Codexが個別レビューした返信調査向け窓口候補は **{len(candidates)}社**（確認済み{summary['codex_reviewed_verified_candidate_count']}社、追加確認{len(candidates)-summary['codex_reviewed_verified_candidate_count']}社）。受付制限・個別回答なしは別枠。個人受付が未記載の会社を、個人の無条件利用可能と解釈しない。", "",
        "## ファイル", "",
        "- [companies.csv](companies.csv)：全社一覧。UTF-8 BOM付き。確認水準、窓口URL、メール、受付条件、未確認理由を含む。",
        "- [companies.json](companies.json)：全社の詳細。引用、取得時刻、保存証拠、Codexの個別レビュー履歴を含む。",
        "- [contact-candidates.csv](contact-candidates.csv)：Codexが個別レビューした返信調査向け窓口候補。",
        "- [restricted.csv](restricted.csv)：個人等に受付制限のある窓口・個別回答なし。",
        "- [retry-network-errors.csv](retry-network-errors.csv)：通信障害で未確認。復旧後の再開対象。",
        "- [other-unconfirmed.csv](other-unconfirmed.csv)：IR用途未実証、robots・アクセス制限、取得・解析の失敗など。窓口不存在の一覧ではない。",
        "- [additional-followups.csv](additional-followups.csv)：通信復旧用の再開対象以外で、入力欄・メール・用途等の追加確認が必要な会社。案内リンクのみの会社も含む。",
        "- [watchlist-bundle.json](watchlist-bundle.json)：個別レビュー済み窓口候補を既存ハーネスのwatchへ取り込む入力。金融仮説・売買指示は含まない。",
        "- [coverage.json](coverage.json)、[validation.json](validation.json)：対象・取得・窓口確認の別集計とデータ検証。",
        "- [evidence](evidence/)・[parts](parts/)：公開取得証拠と分担レビュー結果。[evidence-index.json](evidence-index.json) は保存ファイルのSHA-256を記録し、取得時の本文ハッシュと区別する。", "",
        "## 母集団と上場照合", "",
        "[JPX月末一覧](https://www.jpx.co.jp/markets/statistics-equities/misc/01.html)の2026年9月末データを基準にした。[元Excel](../ir-contacts-2026-10-11/evidence/jpx-data-2026-09.xlsx)・[変換CSV](../ir-contacts-2026-10-11/evidence/jpx-listing-universe.csv)・[取得記録](../ir-contacts-2026-10-11/evidence/jpx-listing-manifest.json)を保存済み。内国株式3,702行のうち、5桁コードの優先株・社債型種類株式7行を除くと普通株は3,695社。前回の調査レポートではこの7行を普通株の母集団へ含めていたため、今回は[除外記録](excluded-share-classes.json)に分けた。", "",
        "10月1日〜11日の[新規上場](https://www.jpx.co.jp/listing/stocks/new/index.html)3社と[上場廃止](https://www.jpx.co.jp/listing/stocks/delisted/index.html)12社を公式表で照合し、3,695＋3−12＝3,686社へ補正した。承認日・公表日と効力日を区別し、10月12日以降の予定は適用しない。[変更記録](listing-deltas.json)には根拠・効力日・取得時刻を残している。新規640A・641A・642Aの公式URL・市場・業種も別途照合した。", "",
        "対象は東証プライム・スタンダード・グロースの国内普通株。ETF・ETN・REIT・インフラファンド・外国株・種類株・TOKYO PRO Market、および名証・福証・札証だけの上場会社はこの母集団に含めない。これは窓口調査の範囲で、投資一般の優劣や除外判定ではない。銀行・保険など専用評価が必要な業種も窓口一覧には含めた。", "",
        "現在価格・売買代金・値動き・個別財務・適時開示・決算日程の検証は未実施。現在の買付可否や金融投資対象の確定を保証しない。", "",
        "## サイト発見と窓口確認", "",
        "サイトURLの発見は[出典と版](seed-sources.md)に記録した。第三者の2024年10月一覧と2026年3月プライム一覧は発見の入口として使い、不足分はJPX公式の2024〜2026年新規上場表から補完した。古いURLは最新の受付根拠に使わず、取得した公式本文で会社名・コード・用途を点検する。JPXの承認時URLにも更新されない旨の注意がある。", "",
        "メールは企業がIR用に指定した公開宛先だけを採用。記入例、privacy・製品・採用・広報のメールや株主優待専用メールをIR業績質問の宛先に推定しない。フォームはIR専用見出し、IRカテゴリ、公式IRの明示リンクとリンク先の実メール・質問欄を確認する。全ページのIRナビ、個人情報方針の投資家という語、電話のIR案内に隣接する製品フォームだけでは確認済みにしない。", "",
        "外部フォームは公式親ページのリンク／埋め込みからたどる。JavaScript画面、空本文、HTTP200のみ、検索欄、メール認証だけでは質問入力欄の確認にならない。個人可の明示は投資家種別・個人の記入説明・公開placeholder等から確認し、それ以外は未確認とする。規約や沈黙期間は取得できた公開範囲の記録で、別ページの全規約を網羅した確認ではない。", "",
        "公開ページのメール表示用エンコードを保存hrefから復元した場合は、原文引用と派生値を分け、元href・復元手法・IR用途の公式リンクを保持する。復元したアドレスが保存された可視本文に存在するとは扱わない。", "",
        "公開GETのみ。メール・フォーム送信、認証メール、会員登録、回答実績の確認は行っていない。回答の到達・所要時間・返信保証も未検証。前回37社の保存証拠は再利用し、取得日時と確認水準を昇格させずに引き継いだ。", "",
        "## 通信障害と再開", "",
        f"保存した各社の最新取得記録では{summary['companies_with_successful_public_page_this_run']}社に成功した公開本文がある（別途、以前の37社の証拠を再利用）。初回の全社取得では、途中から異なる企業・JPX・前に取得できたラクスまで共通のHTTP503が返り、本文が `Invalid argument|remote address:envoy://cloudflare_https_tunnel/` 等になった。[診断記録](network-diagnostics.json)と[接続確認](network-healthchecks/)に保存した。同一エラーが共通経路の問題を示しているが、サービス内部の根本原因は特定できていない。ネット設定を迂回せず、TLS検証も維持した。", "",
        "成功取得が銘柄コードの前半に偏るため、今の結果から全市場のIR受付率や業界別の受付率を推定できない。全社行の作成率と公式本文の取得率、窓口確認率は別の指標として残す。", "",
        "通信復旧後はリポジトリルートから一度だけ以下を実行する。先にJPXへの接続と本文を確認し、失敗中は再試行を開始しない。同じ通信失敗が複数ホストに出た場合も取得を止める。robots・403・429は迂回せず、1ホストずつ間隔を空け、1社のページ数を制限する。確認済み記録は保持し、接続失敗の会社だけ再調査する。回路停止後の未着手会社は再調査済みと扱わず、旧記録を保持する。旧試行・証拠は別ファイルに保ち、定期取得は登録しない。", "",
        "```bash", ".venv/bin/python scripts/research_ir_universe.py \\",
        "  --universe research/ir-contacts-2026-10-11/evidence/jpx-listing-universe.csv \\",
        "  --seeds research/ir-contacts-universe-2026-10-11/seeds-current.json \\",
        "  --output research/ir-contacts-universe-2026-10-11 \\",
        "  --previous research/ir-contacts-2026-10-11 \\",
        "  --listing-deltas research/ir-contacts-universe-2026-10-11/listing-deltas.json \\",
        f"  --resume-network-errors --workers 4 --max-pages 7 --global-rps {resume_rps:g}", "```", "",
        "新しく取得した結果は再びIR用途・個人条件を点検し、検証器で照合してから候補一覧へ反映する。再取得を終えたことと、全社の窓口確認完了は同一視しない。", "",
        f"この再開コマンドの対象以外にも、{len(other_followups)}社で追加確認が必要。取得済み本文から専用フォームへのリンクを見つけたがリンク先を取得できなかった会社などを含み、[別の作業一覧](additional-followups.csv)へ保存した。アクセス制限は尊重し、未取得を『メール・フォームなし』とは判定しない。", "",
        "再取得・個別レビュー後は、上のコマンドの `--resume-network-errors` を `--compile-only` に置き換えて再集計し、次の順に検証とレポート生成を実行する。レポート生成は `records/` と集計JSONが一致しない場合に停止する。", "",
        "```bash", ".venv/bin/python scripts/validate_ir_universe.py research/ir-contacts-universe-2026-10-11 \\",
        "  --universe research/ir-contacts-universe-2026-10-11/universe.csv \\",
        "  --previous-root research/ir-contacts-2026-10-11 \\",
        "  --output research/ir-contacts-universe-2026-10-11/validation.json --require-complete",
        ".venv/bin/python scripts/report_ir_universe.py research/ir-contacts-universe-2026-10-11", "```", "",
    ]
    if adaptive:
        lines[4] = f"対象は **{len(records):,}社**。全社の銘柄・サイトURL・保存記録を母集団として、取得頻度を制御しながらIR受付の調査を進めている。**全社の処理と全社のIR窓口確認は同一ではない**。現在の通信失敗による未確認は{len(blocked):,}社。未取得やアクセス制限を窓口不存在・企業側のIR受付拒否とは判定しない。"
        start = lines.index("## 通信障害と再開") + 2
        end = lines.index("```bash", start)
        lines[start:end] = adaptive_communication_lines(adaptive, retry, summary.get("historical_retry_summary"))
    elif retry:
        retry_path = summary["latest_retry_summary"]
        position = lines.index("## 通信障害と再開") + 2
        lines[position:position] = [
            f"[今回の再試行集計]({retry_path})：前回通信失敗の{retry['selected_company_count']:,}社を選択し、実際の企業本文GETは{retry['company_content_get_attempt_count']}社、本文取得成功は{retry['company_successful_public_body_count']}社。{retry['company_no_get_circuit_stop_count']:,}社は回路停止によりGET前に終了し、{retry['company_no_get_policy_stop_count']}社はrobots等のアクセス方針を守って本文GETを行わなかった。更新された企業行の数を、アクセス済みの社数と混同しない。", "",
            f"初回の全社取得と今回の再試行を合わせ、本文GETを一度でも試みた会社は{retry['universe_company_content_get_attempt_count_across_baseline_and_retry']:,}社。失敗も含む試行数で、本文取得成功や窓口確認の社数ではない。再利用した37社の以前の取得は別枠。legacy集計名の `*_current_run` / `*_this_run` は各社の最新記録を集計しており、今回だけの実GET社数は再試行集計の{retry['company_content_get_attempt_count']}社で確認する。", "",
            f"再試行前のメール・入力欄確認{retry['before_universe_statuses'].get('confirmed', 0)}社／案内等{retry['before_universe_statuses'].get('provisional', 0)}社から、現在の{statuses['confirmed']}社／{statuses['provisional']}社へ更新した。前回の一覧・検証・証拠ハッシュは[再試行前の保存]({retry['baseline_directory']}/)に残した。新しい取得証拠は取得時刻別の別ファイルで保持している。", "",
            "接続回復後に再開できたが、途中で同じEnvoy503が再発し、JPXとラクスの再確認でも同じ応答だった。取得できた記録をレビューして反映し、残りは復旧後の対象として保存した。並列数の変更とエラーの再発は記録するが、並列数が原因とは断定しない。", "",
        ]
    validation_path = root / "validation.json"
    if validation_path.exists():
        checked = json.loads(validation_path.read_text())
        lines += ["## 保存データの検証", "",
                  f"[構造・引用の検証](validation.json)：エラー{checked['error_count']}件、警告{checked['warning_count']}件（検証 {checked['validated_at']}）。これは窓口の実送信・回答や投資適格性の検証ではない。", ""]
        company_warnings = [x["security_code"] for x in checked.get("issues", []) if x.get("kind") == "company_field_unresolved"]
        if company_warnings:
            lines += ["警告対象は会社名等が必須なのに個人の記入方法が明示されていない窓口：" + "、".join(company_warnings) + "。IR用途の確認は保持し、個人利用の可否・入力方法は未確認としている。", ""]
    if (root / "integration-validation.json").exists():
        lines += ["[一覧・保存ハッシュ・一時DBでの取り込み検証](integration-validation.json)も保存した。watchのみの取り込みで仮説・調査job・質問は作成されず、同じ資料の再取り込みで重複が生じないことを確認した。", ""]
    lines += ["## 確認した窓口", "",
              "| コード | 会社 | 窓口 | 調査判定 | 確認水準 | 個人条件 | 返信運用 |", "|---|---|---|---|---|---|---|",]
    for record in sorted(known, key=lambda x: x["security_code"]):
        url = record.get("contact_url")
        link = f"[公式窓口]({url})" if url else "未確認"
        lines.append("| " + " | ".join([record["security_code"], cell(record["company_name"]), link, STATUS[record["investigation_status"]], LEVEL.get(record["verification_level"], record["verification_level"]), ACCESS.get(record.get("individual_access"), str(record.get("individual_access"))), SUITABILITY.get(record["outreach_suitability"], record["outreach_suitability"])]) + " |")
    lines += ["", "## 受付条件・根拠", ""]
    for record in sorted(known, key=lambda x: x["security_code"]):
        lines += [f"### {record['security_code']} {cell(record['company_name'])}", "", f"確認：{LEVEL.get(record['verification_level'])}。{ACCESS.get(record.get('individual_access'), record.get('individual_access'))}。{SUITABILITY.get(record['outreach_suitability'])}。", ""]
        if record.get("public_ir_emails"):
            lines += ["公開IRメール：" + "、".join("`" + x + "`" for x in record["public_ir_emails"]) + "。", ""]
        conditions = list(dict.fromkeys(record.get("conditions", [])))
        if conditions:
            lines.append("取得範囲の受付条件：")
            lines.append("")
            lines.extend("- " + cell(x) for x in conditions)
            lines.append("")
        if record.get("limitations"):
            lines.append("注意・未確認：" + " / ".join(cell(value) for value in dict.fromkeys(record["limitations"])))
            lines.append("")
        lines.extend(["根拠：", ""])
        for evidence in record.get("evidence", []):
            lines.append(f"- [公式ページ]({evidence['url']})／[保存証拠]({evidence['snapshot']})（取得 {evidence['retrieved_at']}）：{cell(evidence['quote'])}")
        lines.append("")
    (root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summary, "bundle_companies": len(companies), "bundle_sources": len(sources)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
