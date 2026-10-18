#!/usr/bin/env python3
"""Run one finite IR network-research queue with bounded, adaptive GET batches.

This wrapper makes no HTTP requests itself. Exactly one collector subprocess
uses the existing proxy/trust settings and its own JPX preflight. The wrapper
never changes company records or infers that an unverified IR channel exists.
It writes only execution state, batch inputs/logs, and unresolved retry lists.

Usage (from the repository root):
  .venv/bin/python scripts/run_ir_research_adaptive.py --plan-only
  .venv/bin/python scripts/run_ir_research_adaptive.py

Normal ramp: 30 companies at 1 RPS, 60 at 2 RPS, then 100 at at most 3 RPS.
Shared failures retain the queue through 5/15/30/60 minute recovery waits.
There is no elapsed-time failure cutoff, cron, detached daemon, or IR sending.
SIGINT/SIGTERM stop the child, preserve progress, and allow an explicit resume.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO / "research/ir-contacts-universe-2026-10-11"
JST = ZoneInfo("Asia/Tokyo")
BATCH_SIZES = (30, 60, 100)
COOLDOWNS = (300, 900, 1800, 3600)
LOCAL_STOPS = {
    "environment_circuit_breaker_open", "robots_disallowed",
    "robots_access_denied_stopped", "robots_unreachable_stopped", "host_access_denied_stopped",
    "redirect_loop", "redirect_limit",
}
SITE_FAILURES = {
    "site_tls_503", "site_connection_termination_503", "http_503",
    "http_404", "http_403", "request_exception:SSLError",
    "request_exception:ReadTimeout", "request_exception:ConnectTimeout",
    "request_exception:ConnectionError", "request_exception:ProxyError",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def stamps() -> dict[str, str]:
    now = utc_now()
    return {"at_utc": now.isoformat(), "at_jst": now.astimezone(JST).isoformat()}


def aware(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, TypeError):
        return None


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def positive_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) and number >= 0 else None
    except (ValueError, TypeError):
        return None


def load_context(args: argparse.Namespace) -> tuple[Path, dict, dict[str, dict], list[str]]:
    output = args.output.resolve()
    if args.manifest:
        manifest_path = args.manifest
    else:
        pointer_path = args.pointer or output / "adaptive-current-run.json"
        pointer = read_json(pointer_path)
        manifest_path = output / pointer["manifest"]
    manifest = read_json(manifest_path)
    run = manifest_path.resolve().parent
    if not aware(manifest.get("started_at")):
        raise ValueError("Adaptive manifest requires an aware started_at")
    seed_path = args.seeds or output / "seeds-current.json"
    rows = read_json(seed_path)
    if not isinstance(rows, list):
        raise ValueError("Seeds must be a JSON array")
    seeds = {}
    for row in rows:
        code = row.get("security_code") if isinstance(row, dict) else None
        if not isinstance(code, str) or code in seeds:
            raise ValueError("Seed codes must be unique strings")
        seeds[code] = row
    universe_path = args.universe or output / "universe.csv"
    with universe_path.open(encoding="utf-8-sig", newline="") as stream:
        universe = [row["security_code"] for row in csv.DictReader(stream)]
    if not universe or len(universe) != len(set(universe)):
        raise ValueError("Universe must contain unique security codes")
    args.universe = universe_path.resolve()
    args.output = output
    return run, manifest, seeds, universe


def pending_codes(output: Path, universe: list[str], exhausted: dict) -> tuple[list[str], list[str]]:
    pending, previously_exhausted = [], []
    for code in universe:
        path = output / "records" / (code + ".json")
        if not path.exists():
            continue  # This runner retries saved network failures only.
        record = read_json(path)
        if record.get("unconfirmed_reason") != "environment_transport_failure":
            continue
        (previously_exhausted if code in exhausted else pending).append(code)
    return pending, previously_exhausted


def fresh_state(args: argparse.Namespace, manifest: dict) -> dict:
    return {
        "schema_version": 1, "runner": "run_ir_research_adaptive", "started_at": utc_now().isoformat(),
        "adaptive_manifest_started_at": manifest["started_at"], "status": "ready",
        "scope": "Latest environment_transport_failure records; financial/IR review is a separate stage",
        "current_global_rps": args.initial_rps, "minimum_global_rps": args.minimum_rps,
        "maximum_global_rps": args.maximum_rps, "workers": args.workers, "max_pages": args.max_pages,
        "batch_stage": args.initial_stage, "healthy_batches_since_reduction": 0, "recovering_rate": False,
        "consecutive_environment_failures": 0, "completed_batch_count": 0,
        "actual_http_get_attempt_count": 0, "attempts_by_code": {}, "exhausted_codes": {},
        "active_batch": None, "cooldown": None, "last_batch": None,
        "IR_messages_sent": 0,
    }


def collector_command(args: argparse.Namespace, seeds: Path, count: int, rps: float) -> list[str]:
    return [args.python, str(args.collector.resolve()), "--universe", str(args.universe),
            "--seeds", str(seeds), "--output", str(args.output),
            "--workers", str(args.workers), "--max-pages", str(args.max_pages),
            "--global-rps", str(rps), "--resume-network-errors", "--only-seeded", "--limit", str(count)]


def output_objects(path: Path) -> list[dict]:
    objects = []
    if not path.exists():
        return objects
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    objects.append(obj)
            except json.JSONDecodeError:
                pass  # Traceback/non-JSON output remains in the saved log.
    return objects


def final_collection(path: Path) -> dict | None:
    for obj in reversed(output_objects(path)):
        value = obj.get("collection_run")
        if isinstance(value, dict):
            return value
    return None


def walk_responses(node: Any):
    if not isinstance(node, dict):
        return
    yield node
    yield from walk_responses(node.get("robots"))
    for redirect in node.get("redirects", []):
        yield from walk_responses(redirect)


def observed_failures(output: Path, record: dict, since: datetime) -> dict:
    signatures, seen = set(), set()
    shared = limited = 0
    retry_after = 0.0
    for fetch in record.get("fetches", []):
        relative = fetch.get("snapshot")
        if not isinstance(relative, str):
            continue
        path = (output / relative).resolve()
        if not path.is_relative_to(output) or not path.exists():
            continue
        for node in walk_responses(read_json(path)):
            if node.get("http_get_attempted") is False:
                continue  # Local circuit wrappers are not request events.
            at = aware(node.get("http_get_started_at")) or aware(node.get("retrieved_at"))
            if at is None or at < since:
                continue
            key = (at.isoformat(), node.get("url") or node.get("requested_url"))
            if key in seen:
                continue
            seen.add(key)
            signature = node.get("failure_signature")
            status, text, error = node.get("http_status"), node.get("text", ""), node.get("error")
            if status == 503 and "Invalid argument|remote address:envoy://cloudflare_" in text:
                signature = "common_transport_503"
            elif not signature and status == 503:
                if "CERTIFICATE_VERIFY_FAILED" in text or "WRONG_VERSION_NUMBER" in text or "TLS_error:" in text:
                    signature = "site_tls_503"
                elif "reset reason: connection termination" in text:
                    signature = "site_connection_termination_503"
                else:
                    signature = "http_503"
            elif not signature and status in (403, 404, 429):
                signature = "http_" + str(status)
            elif not signature and error and error not in LOCAL_STOPS:
                signature = "request_exception:" + str(error)
            if signature == "common_transport_503":
                shared += 1
            if signature == "http_429" or status == 429:
                limited += 1
            if signature in SITE_FAILURES:
                signatures.add(signature)
            value = positive_number(node.get("retry_after_seconds"))
            if value is not None:
                retry_after = max(retry_after, value)
    return {"site_failure_signature": "+".join(sorted(signatures)) or None,
            "shared_503_count": shared, "http_429_count": limited, "retry_after_seconds": retry_after}


def record_attempts(output: Path, state: dict, batch: dict, result: dict) -> dict:
    """Count only fresh records from actual GETs; never edit survey records."""
    since = aware(batch["started_at"])
    assert since is not None
    observed = {"actual_company_attempts": 0, "shared_503_count": 0, "http_429_count": 0,
                "retry_after_seconds": 0.0, "new_exhausted_codes": []}
    globally_healthy = result.get("preflight_passed") is True and not result.get("common_transport_503_count")
    staged = []
    for code in batch["security_codes"]:
        path = output / "records" / (code + ".json")
        if not path.exists():
            continue
        raw = path.read_bytes(); digest = hashlib.sha256(raw).hexdigest(); record = json.loads(raw)
        attempt = record.get("latest_attempt") if isinstance(record.get("latest_attempt"), dict) else record
        recorded = aware(attempt.get("attempted_at")) or aware(record.get("last_attempted_at"))
        count = positive_number(attempt.get("http_get_attempt_count", record.get("http_get_attempt_count")))
        if (recorded is None or recorded < since or digest == batch["before_hashes"].get(code)
                or count is None or count <= 0):
            continue
        failure = observed_failures(output, attempt, since)
        observed["actual_company_attempts"] += 1
        observed["shared_503_count"] += failure["shared_503_count"]
        observed["http_429_count"] += failure["http_429_count"]
        observed["retry_after_seconds"] = max(observed["retry_after_seconds"], failure["retry_after_seconds"])
        staged.append((code, record, digest, failure, recorded))
    globally_healthy = globally_healthy and observed["shared_503_count"] == 0
    for code, record, digest, failure, recorded in staged:
        old = state["attempts_by_code"].get(code, {})
        if old.get("last_record_sha256") == digest:
            continue
        signature = failure["site_failure_signature"]
        same = old.get("same_failure_count", 0) + 1 if signature and signature == old.get("last_failure_signature") else 1 if signature else 0
        healthy_same = (old.get("healthy_same_failure_count", 0) + 1
                        if signature == old.get("last_failure_signature") else 1) if signature and globally_healthy else 0
        state["attempts_by_code"][code] = {
            "attempt_count": old.get("attempt_count", 0) + 1, "same_failure_count": same,
            "healthy_same_failure_count": healthy_same,
            "last_failure_signature": signature, "last_attempted_at": recorded.isoformat(),
            "last_record_sha256": digest, "last_preflight_passed": result.get("preflight_passed"),
            "last_batch_id": batch["batch_id"],
        }
        if (globally_healthy and healthy_same >= 2 and signature
                and record.get("unconfirmed_reason") == "environment_transport_failure"):
            state["exhausted_codes"][code] = {
                "security_code": code, "company_name": record.get("company_name"),
                "reason": "Repeated unresolved path/destination failure with successful global preflight; cause undetermined",
                "failure_signature": signature, "same_failure_count": same,
                "healthy_same_failure_count": healthy_same,
                "attempt_count": state["attempts_by_code"][code]["attempt_count"],
                "record_path": str(path.relative_to(output)), "record_sha256": digest,
                "last_batch_id": batch["batch_id"], "excluded_from_network_queue_only": True,
                "IR_channel_verified": False, "requires_followup": True, **stamps(),
            }
            observed["new_exhausted_codes"].append(code)
    return observed


def next_rate(state: dict, result: dict, has_rate_problem: bool) -> None:
    configured = current = state["current_global_rps"]
    collector_rate = positive_number(result.get("final_global_rps"))
    if collector_rate is not None and collector_rate > 0:
        current = min(current, collector_rate)
    if has_rate_problem:
        # The collector may already have halved its rate. Apply the wrapper's
        # reduction once rather than inadvertently quartering every batch.
        state["current_global_rps"] = max(state["minimum_global_rps"], min(configured / 2, current))
        state["batch_stage"] = 0
        state["healthy_batches_since_reduction"] = 0
        state["recovering_rate"] = True
    else:
        state["consecutive_environment_failures"] = 0
        state["healthy_batches_since_reduction"] += 1
        if state["recovering_rate"]:
            if state["healthy_batches_since_reduction"] >= 2:
                current = min(state["maximum_global_rps"], current + 0.5)
                state["healthy_batches_since_reduction"] = 0
                state["batch_stage"] = min(state["batch_stage"] + 1, 2)
                if current >= state["maximum_global_rps"]:
                    state["recovering_rate"] = False
        elif collector_rate is not None and collector_rate < state["current_global_rps"]:
            state["recovering_rate"] = True  # Respect collector-origin damping.
            state["healthy_batches_since_reduction"] = 0
        else:
            state["batch_stage"] = min(state["batch_stage"] + 1, 2)
            current = min(state["maximum_global_rps"], state["batch_stage"] + 1.0)
        state["current_global_rps"] = max(state["minimum_global_rps"], current)


class Runner:
    def __init__(self, args, run, manifest, seeds, universe):
        self.args, self.run, self.manifest = args, run, manifest
        self.seeds, self.universe = seeds, universe
        self.progress_path, self.events_path = run / "progress.json", run / "events.jsonl"
        self.state = read_json(self.progress_path) if self.progress_path.exists() else fresh_state(args, manifest)
        if self.state.get("adaptive_manifest_started_at") != manifest["started_at"]:
            raise ValueError("Existing runner state belongs to a different adaptive manifest")
        self.stop = threading.Event()
        self.child: subprocess.Popen | None = None
        self.last_heartbeat = 0.0

    def save(self):
        pending, exhausted = pending_codes(self.args.output, self.universe, self.state["exhausted_codes"])
        self.state.update(updated_at=utc_now().isoformat(), updated_at_jst=utc_now().astimezone(JST).isoformat(),
                          pending_network_company_count=len(pending), exhausted_network_company_count=len(exhausted),
                          exhausted_codes_requiring_followup=list(self.state["exhausted_codes"]), runner_pid=os.getpid())
        atomic_json(self.progress_path, self.state)
        atomic_json(self.run / "retry-candidates.json", {
            "scope": "Unresolved candidates excluded from this network queue only; company records are unchanged",
            "generated_at": utc_now().isoformat(), "exhausted_codes": list(self.state["exhausted_codes"]),
            "candidates": list(self.state["exhausted_codes"].values()),
        })

    def event(self, kind, **fields):
        event = {**stamps(), "event": kind, "global_rps": self.state["current_global_rps"],
                 "actualrequests": fields.pop("actualrequests", None), **fields}
        with self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
            stream.flush()
        print(json.dumps(event, ensure_ascii=False), flush=True)

    def heartbeat(self, force=False):
        if force or time.monotonic() - self.last_heartbeat >= self.args.heartbeat_seconds:
            self.save()
            batch = self.state.get("active_batch") or {}
            self.event("heartbeat", status=self.state["status"], batchcodes=batch.get("security_codes", []),
                       batch_id=batch.get("batch_id"), cooldown=self.state.get("cooldown"),
                       pending=self.state["pending_network_company_count"],
                       exhausted=self.state["exhausted_network_company_count"],
                       actualrequests=batch.get("collector_progress", {}).get("http_get_attempt_count"))
            self.last_heartbeat = time.monotonic()

    def interrupt(self, _signal, _frame):
        self.stop.set()

    def stop_child(self):
        if self.child is None or self.child.poll() is not None:
            return
        try:
            os.killpg(self.child.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            self.child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(self.child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self.child.wait(timeout=10)

    def collector_progress(self, batch):
        since = aware(batch["started_at"])
        candidates = sorted((self.args.output / "collection-runs").glob("*-progress.json"), reverse=True)
        for path in candidates:
            try:
                data = read_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            started = aware(data.get("started_at"))
            if started and since and started >= since:
                batch["collector_progress"] = data
                batch["collector_progress_path"] = str(path.relative_to(self.args.output))
                return

    def cooldown(self):
        cooldown = self.state.get("cooldown")
        if not cooldown:
            return
        until = aware(cooldown["until_utc"])
        assert until is not None
        self.state["status"] = "waiting_for_recovery"
        while not self.stop.is_set():
            remaining = (until - utc_now()).total_seconds()
            if remaining <= 0:
                self.state["cooldown"] = None
                self.save()
                return
            self.heartbeat()
            self.stop.wait(min(remaining, self.args.heartbeat_seconds, 60))

    def schedule_cooldown(self, reason, retry_after=0.0):
        self.state["consecutive_environment_failures"] += 1
        streak = self.state["consecutive_environment_failures"]
        delay = max(COOLDOWNS[min(streak - 1, len(COOLDOWNS) - 1)], retry_after)
        until = utc_now() + timedelta(seconds=delay)
        self.state["cooldown"] = {"reason": reason, "seconds": delay, "until_utc": until.isoformat(),
                                  "until_jst": until.astimezone(JST).isoformat(), "failure_streak": streak,
                                  "server_retry_after_can_extend_backoff": retry_after > COOLDOWNS[-1]}
        self.state["status"] = "waiting_for_recovery"
        self.save()
        self.event("cooldown_scheduled", cooldown=self.state["cooldown"])

    def run_batch(self, codes):
        sequence = self.state["completed_batch_count"] + 1
        batch_id = f"{sequence:05d}-" + utc_now().strftime("%Y%m%dT%H%M%S%fZ")
        directory = self.run / "batches" / batch_id
        directory.mkdir(parents=True, exist_ok=False)
        seed_path = directory / "seeds.json"
        atomic_json(seed_path, [self.seeds[c] for c in codes])
        command = collector_command(self.args, seed_path, len(codes), self.state["current_global_rps"])
        batch = {"batch_id": batch_id, "started_at": utc_now().isoformat(), "security_codes": codes,
                 "configured_global_rps": self.state["current_global_rps"], "command": command,
                 "stdout_path": str(directory / "stdout.log"), "before_hashes": {
                     c: hashlib.sha256((self.args.output / "records" / (c + ".json")).read_bytes()).hexdigest()
                     for c in codes}, "collector_progress": {}}
        self.state["active_batch"] = batch
        self.state["status"] = "collecting"
        self.save()
        self.event("batch_started", batch_id=batch_id, batchcodes=codes, rps=batch["configured_global_rps"])
        with (directory / "stdout.log").open("wb") as output:
            self.child = subprocess.Popen(command, cwd=REPO, stdin=subprocess.DEVNULL, stdout=output,
                                          stderr=subprocess.STDOUT, start_new_session=True)
            batch["collector_pid"] = self.child.pid
            self.save()
            while self.child.poll() is None and not self.stop.is_set():
                self.collector_progress(batch)
                self.heartbeat()
                self.stop.wait(min(self.args.poll_seconds, 60))
            if self.stop.is_set():
                self.stop_child()
            return_code = self.child.wait()
            self.child = None
        result = final_collection(directory / "stdout.log")
        if result is None:
            self.state["status"] = "interrupted" if self.stop.is_set() else "collector_protocol_error"
            batch["return_code"] = return_code
            self.save()
            self.event(self.state["status"], batch_id=batch_id, batchcodes=codes, return_code=return_code)
            return 130 if self.stop.is_set() else 1
        return self.finish_batch(batch, result, return_code)

    def finish_batch(self, batch, result, return_code):
        codes = batch["security_codes"]
        observed = record_attempts(self.args.output, self.state, batch, result)
        requests = positive_number(result.get("http_get_attempt_count"))
        if requests is not None:
            self.state["actual_http_get_attempt_count"] += int(requests)
        shared = max(result.get("common_transport_503_count", 0), observed["shared_503_count"])
        limited = max(result.get("http_429_count", 0), observed["http_429_count"])
        problem = return_code == 2 or shared > 0 or limited > 0 or result.get("preflight_passed") is not True
        self.state["completed_batch_count"] += 1
        self.state["last_batch"] = {**batch, "completed_at": utc_now().isoformat(), "return_code": return_code,
                                    "collection_run": result, "wrapper_observations": observed}
        self.state["active_batch"] = None
        if self.stop.is_set():
            self.state["status"] = "interrupted"
            self.save()
            return 130
        if return_code not in (0, 2):
            self.state["status"] = "collector_error"
            self.save()
            self.event("collector_error", return_code=return_code, batchcodes=codes, actualrequests=requests)
            return 1
        next_rate(self.state, result, problem)
        self.save()
        self.event("batch_completed", batch_id=batch["batch_id"], batchcodes=codes, return_code=return_code,
                   actualrequests=requests, shared_503=shared, http_429=limited,
                   new_exhausted_codes=observed["new_exhausted_codes"], next_rps=self.state["current_global_rps"])
        if result.get("preflight_passed") is not True and result.get("preflight_http_status") in (401, 403):
            self.state["status"] = "external_access_blocked"
            self.save()
            self.event("external_access_blocked", http_status=result["preflight_http_status"], batchcodes=codes)
            return 3
        if problem:
            reason = "shared_transport_503" if shared else "http_429" if limited else "collector_preflight_or_circuit_failure"
            self.schedule_cooldown(reason, observed["retry_after_seconds"])
        return None

    def execute(self):
        # A hard-killed wrapper may leave its separately grouped child alive.
        # Never create a second collector alongside that unresolved process.
        active = self.state.get("active_batch")
        if active:
            pid = active.get("collector_pid")
            alive = False
            if isinstance(pid, int):
                try:
                    os.kill(pid, 0)
                    command_path = Path(f"/proc/{pid}/cmdline")
                    alive = (str(self.args.collector.resolve()).encode() in command_path.read_bytes()
                             if command_path.exists() else True)
                except ProcessLookupError:
                    pass
            if alive:
                self.state["status"] = "previous_collector_process_unresolved"
                self.save()
                self.event(self.state["status"], collector_pid=pid)
                return 3
            result = final_collection(Path(active["stdout_path"]))
            if result is not None:
                inferred_return = 2 if result.get("status") in {"environment_stopped", "environment_preflight_failed"} else 0
                code = self.finish_batch(active, result, inferred_return)
                self.event("interrupted_completed_batch_reconciled", batch_id=active["batch_id"])
                if code is not None:
                    return code
            else:
                progress = active.get("collector_progress", {})
                observations = record_attempts(self.args.output, self.state, active, progress)
                requests = positive_number(progress.get("http_get_attempt_count"))
                if requests is not None:
                    self.state["actual_http_get_attempt_count"] += int(requests)
                self.event("interrupted_batch_reconciled", batch_id=active["batch_id"], batchcodes=active["security_codes"],
                           observations=observations, actualrequests=requests)
                self.state["last_batch"] = {**active, "collection_run": progress, "wrapper_observations": observations,
                                            "status": "interrupted_partial", "actual_request_total_may_be_incomplete": True}
                self.state["active_batch"] = None
                self.save()
                if observations["shared_503_count"] or observations["http_429_count"]:
                    next_rate(self.state, progress, True)
                    self.schedule_cooldown("interrupted_batch_transport_failure", observations["retry_after_seconds"])
        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)
        self.event("runner_started", configured_workers=self.args.workers, configured_max_pages=self.args.max_pages)
        try:
            while not self.stop.is_set():
                pending, exhausted = pending_codes(self.args.output, self.universe, self.state["exhausted_codes"])
                eligible = [c for c in pending if c in self.seeds]
                if not eligible:
                    self.state["status"] = "blocked_missing_seeds" if pending else "network_phase_complete_with_retry_candidates" if exhausted else "network_phase_complete"
                    self.state["network_queue_drained"] = not pending
                    self.state["all_IR_channels_verified"] = False
                    self.save()
                    self.event("runner_finished", status=self.state["status"], pending=pending, exhausted_codes=exhausted)
                    return 3 if pending else 0
                if self.args.max_batches is not None and self.state["completed_batch_count"] >= self.args.max_batches:
                    self.state["status"] = "paused_at_requested_batch_limit"
                    self.save()
                    self.event("runner_finished", status=self.state["status"])
                    return 0
                if self.state.get("cooldown"):
                    self.cooldown()
                    continue  # Re-read pending records after the recovery wait.
                batch_size = BATCH_SIZES[self.state["batch_stage"]]
                result = self.run_batch(eligible[:batch_size])
                if result is not None:
                    return result
            self.state["status"] = "interrupted"
            self.save()
            self.event("runner_finished", status="interrupted")
            return 130
        finally:
            self.stop_child()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--pointer", type=Path, help="Default: OUTPUT/adaptive-current-run.json")
    result.add_argument("--manifest", type=Path, help="Override the manifest from the adaptive pointer")
    result.add_argument("--seeds", type=Path, help="Default: OUTPUT/seeds-current.json")
    result.add_argument("--universe", type=Path, help="Default: OUTPUT/universe.csv")
    result.add_argument("--collector", type=Path, default=REPO / "scripts/research_ir_universe.py")
    result.add_argument("--python", default=sys.executable, help="Collector Python interpreter; defaults to this interpreter")
    result.add_argument("--workers", type=int, default=4)
    result.add_argument("--max-pages", type=int, default=7)
    result.add_argument("--initial-rps", type=float, default=1.0)
    result.add_argument("--initial-stage", type=int, choices=(0, 1, 2), default=0,
                        help="Fresh-state batch stage 0=30, 1=60, 2=100; stage1 with initial-rps2 follows an externally completed healthy30 batch")
    result.add_argument("--maximum-rps", type=float, default=3.0)
    result.add_argument("--minimum-rps", type=float, default=0.25)
    result.add_argument("--heartbeat-seconds", type=float, default=30.0)
    result.add_argument("--poll-seconds", type=float, default=5.0)
    result.add_argument("--max-batches", type=int, help="Optional explicit batch limit; omitted means finish queue or await recovery")
    result.add_argument("--plan-only", action="store_true", help="Read-only offline plan; never start collector or write state")
    return result


def main(argv=None) -> int:
    arguments = parser()
    args = arguments.parse_args(argv)
    if (not 1 <= args.workers <= 4 or not 1 <= args.max_pages <= 7
            or not all(math.isfinite(v) for v in (args.minimum_rps, args.initial_rps, args.maximum_rps, args.heartbeat_seconds, args.poll_seconds))
            or not 0.25 <= args.minimum_rps <= args.initial_rps <= args.maximum_rps <= 3
            or not 0 < args.poll_seconds <= 60 or not 0 < args.heartbeat_seconds <= 60
            or args.max_batches is not None and args.max_batches < 1):
        arguments.error("Use workers1..4, pages1..7, .25<=minimum<=initial<=maximum<=3, waits0..60s, and positive max-batches")
    try:
        run, manifest, seeds, universe = load_context(args)
        state = read_json(run / "progress.json") if (run / "progress.json").exists() else fresh_state(args, manifest)
        pending, exhausted = pending_codes(args.output, universe, state["exhausted_codes"])
        eligible = [c for c in pending if c in seeds]
        if args.plan_only:
            size = BATCH_SIZES[state["batch_stage"]]
            codes = eligible[:size]
            print(json.dumps({"status": "offline_plan", "network_requests": 0, "writes": 0,
                              "adaptive_run": str(run), "pending_network_codes": len(pending),
                              "eligible_seeded_codes": len(eligible), "missing_seed_codes": [c for c in pending if c not in seeds],
                              "exhausted_codes": exhausted, "first_batch_codes": codes,
                              "first_batch_rps": state["current_global_rps"], "ramp_batch_sizes": list(BATCH_SIZES),
                              "maximum_global_rps": state["maximum_global_rps"], "cooldown_seconds": list(COOLDOWNS),
                              "collector_command": collector_command(args, run / "batches/PLAN/seeds.json", len(codes), state["current_global_rps"]),
                              "waiting_is_interruptible": True, "completion_scope": state["scope"]}, ensure_ascii=False, indent=2))
            return 0
        run.mkdir(parents=True, exist_ok=True)
        with (run / "runner.lock").open("a+") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print(json.dumps({"status": "another_adaptive_runner_is_active", "run": str(run)}), flush=True)
                return 3
            return Runner(args, run, manifest, seeds, universe).execute()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"status": "runner_input_or_state_error", "error_type": type(error).__name__, "detail": str(error)}, ensure_ascii=False), flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
