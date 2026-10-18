"""Read-only work measurement, with no extrapolated company capacity.

This is a project measurement adaptation of docs/ir-operation-design.md §13,
not a financial author's worker-allocation formula or investment strategy.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from decimal import Decimal, localcontext
import math
import re

from .adapters.common import canonical_json
from .models import integer, object_value, text, timestamp
from .valuation import _number

_STATUSES = {"completed", "failed", "retry", "in_progress", "cancelled"}
_FIELDS = {"id", "company_id", "stage", "worker_id", "attempt_id", "started_at", "ended_at",
           "active_seconds", "tokens", "cost", "status", "synthetic"}


def _number_nonnegative(value, label):
    result = _number(value, label)
    if result < 0 or abs(result.as_tuple().exponent) > 100 or len(result.as_tuple().digits) > 200:
        raise ValueError(f"{label} must be nonnegative within supported measurement precision")
    return result


def _seconds(delta):
    return Decimal((delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds) / 1000000


def _format(value):
    if value is None:
        return None
    rendered = format(value, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def _distribution(values):
    ordered = sorted(values)
    if not ordered:
        return {"count": 0, "total": None, "mean": None, "min": None, "p50": None, "p90": None, "max": None}
    with localcontext() as context:
        context.prec = 220
        total = sum(ordered, Decimal(0))
        return {"count": len(ordered), "total": _format(total), "mean": _format(total / len(ordered)),
                "min": _format(ordered[0]), "p50": _format(ordered[math.ceil(len(ordered) * .5) - 1]),
                "p90": _format(ordered[math.ceil(len(ordered) * .9) - 1]), "max": _format(ordered[-1])}


def _union(intervals):
    merged = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def _duration(intervals):
    return sum((_seconds(end - start) for start, end in intervals), Decimal(0))


def _cost(value, label):
    value = object_value(value, label)
    if set(value) != {"amount", "currency"}:
        raise ValueError(f"{label} must explicitly contain amount and currency")
    amount = _number_nonnegative(value["amount"], label + ".amount")
    currency = text(value["currency"], label + ".currency")
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError(f"{label}.currency must be an explicit three-letter code")
    return amount, currency


def _validate_measurement(value):
    record = deepcopy(object_value(value, "measurement"))
    if set(record) - _FIELDS:
        raise ValueError("Unknown measurement fields; do not silently ignore a misspelled usage field")
    for key in ("id", "company_id", "stage", "worker_id", "attempt_id"):
        text(record.get(key), "measurement." + key)
    status = record.get("status")
    if not isinstance(status, str) or status not in _STATUSES:
        raise ValueError("measurement.status must be completed, failed, retry, in_progress or cancelled")
    start = timestamp(record.get("started_at"), "measurement.started_at")
    end = timestamp(record["ended_at"], "measurement.ended_at") if record.get("ended_at") is not None else None
    if end is not None and end < start:
        raise ValueError("measurement.ended_at precedes started_at")
    if (status == "in_progress") != (end is None):
        raise ValueError("Only in_progress records have no ended_at; terminal attempts require ended_at")
    if "synthetic" in record and type(record["synthetic"]) is not bool:
        raise ValueError("measurement.synthetic must be boolean")
    active = None if record.get("active_seconds") is None else _number_nonnegative(record["active_seconds"], "active_seconds")
    if active is not None and end is not None and active > _seconds(end - start):
        raise ValueError("active_seconds exceeds the attempt's elapsed interval")
    if record.get("tokens") is not None:
        integer(record["tokens"], "measurement.tokens")
    cost = _cost(record["cost"], "measurement.cost") if record.get("cost") is not None else None
    return {"record": record, "start": start, "end": end, "active": active, "cost": cost}


def _usage(selected):
    contained = [x for x in selected if x["contained"]]
    unallocated = len(selected) - len(contained)
    missing_active = sum(x["active"] is None for x in contained)
    known_active = sum((x["active"] for x in contained if x["active"] is not None), Decimal(0))
    known_tokens = sum(x["record"]["tokens"] for x in contained if x["record"].get("tokens") is not None)
    missing_tokens = sum(x["record"].get("tokens") is None for x in contained)
    cost_sums = defaultdict(lambda: Decimal(0))
    for item in contained:
        if item["cost"] is not None:
            amount, currency = item["cost"]
            cost_sums[currency] += amount
    missing_cost = sum(x["cost"] is None for x in contained)
    complete = bool(selected) and unallocated == 0
    cost_value = None
    if complete and missing_cost == 0 and len(cost_sums) == 1:
        currency, amount = next(iter(cost_sums.items()))
        cost_value = {"amount": _format(amount), "currency": currency}
    return {
        "active_seconds": {"value": _format(known_active) if complete and missing_active == 0 else None,
                           "known_whole_attempt_sum": _format(known_active) if contained else None,
                           "missing_records": missing_active, "unallocated_crossing_or_unfinished_records": unallocated},
        "tokens": {"value": known_tokens if complete and missing_tokens == 0 else None,
                   "known_whole_attempt_sum": known_tokens if contained else None,
                   "missing_records": missing_tokens, "unallocated_crossing_or_unfinished_records": unallocated},
        "cost": {"value": cost_value, "known_whole_attempt_sums_by_currency": {k: _format(v) for k, v in sorted(cost_sums.items())},
                 "missing_records": missing_cost, "unallocated_crossing_or_unfinished_records": unallocated},
    }


def _cohort(items, start, end, capacity, *, synthetic):
    selected, outside = [], []
    for original in items:
        item = dict(original)
        finish = item["end"]
        has_completion_event = finish is not None and start <= finish < end
        overlaps = item["start"] < end and (finish is None or finish > start)
        if not overlaps and not has_completion_event:
            outside.append(item)
            continue
        item["clipped_start"] = max(start, item["start"])
        item["clipped_end"] = min(end, finish) if finish else end
        item["contained"] = finish is not None and item["start"] >= start and finish <= end
        item["terminal_event_in_window"] = has_completion_event
        selected.append(item)
    by_worker = defaultdict(list)
    for item in selected:
        if item["clipped_end"] > item["clipped_start"]:
            by_worker[item["record"]["worker_id"]].append((item["clipped_start"], item["clipped_end"]))
    unions = {key: _union(intervals) for key, intervals in by_worker.items()}
    individual_elapsed = sum((_duration(x) for x in by_worker.values()), Decimal(0))
    union_elapsed = sum((_duration(x) for x in unions.values()), Decimal(0))
    overlap = individual_elapsed - union_elapsed
    points = [(a, 1) for intervals in unions.values() for a, _ in intervals]
    points += [(b, -1) for intervals in unions.values() for _, b in intervals]
    concurrent = peak = 0
    for _, change in sorted(points):
        concurrent += change
        peak = max(peak, concurrent)
    usage = _usage(selected)
    recorded_active = usage["active_seconds"].pop("value")
    usage["active_seconds"]["worker_total"] = None if overlap > 0 else recorded_active
    usage["active_seconds"]["overlap_prevents_worker_total"] = overlap > 0
    terminal_counts = Counter(x["record"]["status"] for x in selected if x["terminal_event_in_window"])
    completed = [x for x in selected if x["record"]["status"] == "completed" and x["terminal_event_in_window"]]
    unfinished = [x for x in selected if x["end"] is None or x["end"] > end]
    stages = {}
    for stage in sorted({x["record"]["stage"] for x in selected}):
        rows = [x for x in selected if x["record"]["stage"] == stage]
        known_active = [x["active"] for x in rows if x["contained"] and x["active"] is not None]
        ended_elapsed = [_seconds(x["end"] - x["start"]) for x in rows if x["contained"]]
        clipped_elapsed = [_seconds(max(x["clipped_end"], x["clipped_start"]) - x["clipped_start"]) for x in rows]
        stages[stage] = {
            "attempt_records": len(rows), "terminal_events_in_window": dict(Counter(x["record"]["status"] for x in rows if x["terminal_event_in_window"])),
            "active_seconds_whole_attempt_samples": _distribution(known_active),
            "elapsed_seconds_whole_attempt_samples": _distribution(ended_elapsed),
            "elapsed_seconds_within_window_samples": _distribution(clipped_elapsed),
            "usage": _usage(rows),
            "note": "Distributions describe recorded attempts including failures/retries; elapsed is not active work and stages are not a full-company pipeline",
        }
    comparables = synthetic == capacity["synthetic"]
    worker_budget = capacity["worker_seconds"]
    used_worker = usage["active_seconds"]["worker_total"]
    worker_compare = None
    if comparables and worker_budget is not None and used_worker is not None:
        worker_compare = {"observed_active_seconds": used_worker, "budget_worker_seconds": _format(worker_budget),
                          "remaining_worker_seconds": _format(worker_budget - Decimal(used_worker)),
                          "exceeded": Decimal(used_worker) > worker_budget}
    budget_cost = capacity["cost_budget"]
    used_cost = usage["cost"]["value"]
    cost_compare = None
    if comparables and budget_cost and used_cost and used_cost["currency"] == budget_cost[1]:
        amount, currency = budget_cost
        cost_compare = {"currency": currency, "observed_cost": used_cost["amount"], "budget_amount": _format(amount),
                        "remaining_amount": _format(amount - Decimal(used_cost["amount"])),
                        "exceeded": Decimal(used_cost["amount"]) > amount}
    return {
        "input_unique_records": len(items), "outside_window_records": len(outside), "in_window_records": len(selected),
        "terminal_events_in_window": {key: terminal_counts[key] for key in sorted(_STATUSES - {"in_progress"})},
        "terminal_events_exactly_at_window_end": sum(x["end"] == end for x in selected),
        "completed_attempts": len(completed), "completed_company_coverage": len({x["record"]["company_id"] for x in completed}),
        "completed_company_ids": sorted({x["record"]["company_id"] for x in completed}),
        "coverage_note": "A completed stage/attempt for a company does not establish that all investment analysis or daily monitoring for that company is complete",
        "carried_in_records": sum(x["start"] < start for x in selected),
        "backlog_at_window_end": {"unfinished_observed_attempts": len(unfinished),
                                  "company_ids": sorted({x["record"]["company_id"] for x in unfinished}),
                                  "longest_since_start_seconds": _format(max((_seconds(end-x["start"]) for x in unfinished), default=None)),
                                  "queue_wait_seconds": None, "overdue_attempts": None,
                                  "note": "Only supplied started attempts are observable; queued/unsubmitted demand, due dates and queue waiting are not measured"},
        "record_counts_by_declared_status": dict(sorted(Counter(x["record"]["status"] for x in selected).items())),
        "usage": usage, "stages": stages,
        "worker_intervals": {"sum_record_elapsed_seconds": _format(individual_elapsed),
                             "occupied_elapsed_seconds_union_by_worker": _format(union_elapsed),
                             "overlapping_same_worker_elapsed_seconds": _format(overlap),
                             "any_worker_occupied_wall_seconds": _format(_duration(_union([x for intervals in unions.values() for x in intervals]))),
                             "maximum_distinct_workers_overlapping": peak,
                             "per_worker_occupied_elapsed_seconds": {k: _format(_duration(v)) for k, v in sorted(unions.items())},
                             "note": "Unioned elapsed/reservation intervals, not active CPU/analyst time or available worker capacity"},
        "budget_comparison": {"worker_seconds": worker_compare, "cost": cost_compare,
                              "budget_matches_cohort": comparables,
                              "note": "Null comparisons mean missing/incomparable measurements or capacity; unused budget is not a company-count estimate"},
    }


def report_research_capacity(request: dict) -> dict:
    """Describe recorded work, failures and backlog without inventing an upper limit.

    Window is half-open for terminal events. Intervals are clipped to it; whole
    active/token/cost observations for crossing or unfinished attempts are not
    proportionally allocated. Retry/failed intervals and usage are retained.
    Synthetic and observed cohorts never share totals or budget comparisons.
    """
    request = deepcopy(object_value(request, "capacity request"))
    if type(request.get("schema_version")) is not int or request["schema_version"] != 1:
        raise ValueError("capacity request.schema_version must be 1")
    window = object_value(request.get("window"), "measurement window")
    start, end = timestamp(window.get("started_at")), timestamp(window.get("ended_at"))
    if end <= start:
        raise ValueError("Measurement window must have positive elapsed time")
    raw_capacity = object_value(request.get("operator_capacity", {}), "operator capacity")
    if set(raw_capacity) - {"worker_seconds", "cost_budget", "synthetic"}:
        raise ValueError("Unknown operator capacity field")
    if type(raw_capacity.get("synthetic", False)) is not bool:
        raise ValueError("operator_capacity.synthetic must be boolean")
    capacity = {
        "worker_seconds": _number_nonnegative(raw_capacity["worker_seconds"], "worker capacity") if raw_capacity.get("worker_seconds") is not None else None,
        "cost_budget": _cost(raw_capacity["cost_budget"], "cost budget") if raw_capacity.get("cost_budget") is not None else None,
        "synthetic": raw_capacity.get("synthetic", False),
    }
    values = request.get("measurements")
    if not isinstance(values, list):
        raise ValueError("measurements must be an explicit list")
    unique, encoded, attempts = [], {}, set()
    duplicates = 0
    for value in values:
        item = _validate_measurement(value)
        record = item["record"]
        identity = canonical_json(record)
        if record["id"] in encoded:
            if encoded[record["id"]] != identity:
                raise ValueError("Measurement ID reused for altered data")
            duplicates += 1
            continue
        attempt = tuple(record[k] for k in ("company_id", "stage", "worker_id", "attempt_id"))
        if attempt in attempts:
            raise ValueError("Same physical attempt appears under different measurement IDs")
        attempts.add(attempt)
        encoded[record["id"]] = identity
        unique.append(item)
    observed = [x for x in unique if not x["record"].get("synthetic", False)]
    synthetic = [x for x in unique if x["record"].get("synthetic", False)]
    return {
        "schema_version": 1, "method": "project_measurement_adaptation_of_ir_operation_design_section_13",
        "window": {"started_at": start.isoformat(), "ended_at": end.isoformat(), "elapsed_seconds": _format(_seconds(end-start)),
                   "semantics": "Terminal events in [start,end); elapsed intervals clipped to window; events exactly at end listed separately"},
        "input_records": len(values), "unique_records": len(unique), "duplicate_records_ignored": duplicates,
        "measurement_mode": "mixed" if observed and synthetic else "observed_only" if observed else "synthetic_only" if synthetic else "no_measurements",
        "operator_capacity": {"worker_seconds": _format(capacity["worker_seconds"]),
                              "cost_budget": {"amount": _format(capacity["cost_budget"][0]), "currency": capacity["cost_budget"][1]} if capacity["cost_budget"] else None,
                              "synthetic": capacity["synthetic"]},
        "cohorts": {"observed": _cohort(observed, start, end, capacity, synthetic=False),
                    "synthetic": _cohort(synthetic, start, end, capacity, synthetic=True)},
        "company_upper_bound": None, "capacity_status": "not_estimated",
        "next_measurements": [
            "Record actual arrivals/queued_at, deadlines and terminal attempt IDs to measure queue waiting, overdue demand and complete task throughput",
            "Measure active worker intervals explicitly; do not substitute elapsed, waiting or fetch-only time",
            "Collect complete token and cost records with currency, including failed and retried attempts",
            "Separate normal days and earnings peaks, stage mix and repeat investigations; one company need not incur the same daily work",
            "Measure shared API/DB constraints, same-company exclusion and counter-review work before testing additional workers",
            "Define monitored, deeply researched, queried and held cohorts separately; count end-to-end completion before estimating coverage capacity",
        ],
        "limitations": [
            "Caller-supplied measurements are summarized; no scheduler, model call, financial analysis or independently verified runtime was executed",
            "No per-company daily cost or linear scaling with worker count is assumed",
            "Unknown usage, capacity and queue observations remain null; recorded sums do not establish an operational company upper limit",
        ],
    }
