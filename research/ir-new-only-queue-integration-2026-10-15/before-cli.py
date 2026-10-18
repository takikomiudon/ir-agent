"""JSON CLI suitable for Codex workers and an external scheduler."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys

from .adapters.common import DataAdapterError
from .harness import Harness, evaluation_view
from .models import COMPANY_STATUSES, load_json, now_iso
from .store import Store
from .valuation import calculate_valuation


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Japanese equity hypothesis and IR research harness")
    root.add_argument("--db", default="data/ir-agent.sqlite3", help="SQLite file (default: data/ir-agent.sqlite3)")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Initialize the local database")
    ingest = commands.add_parser("ingest", help="Atomically import a schema_version=1 JSON bundle")
    ingest.add_argument("file")
    daily = commands.add_parser("daily", help="Queue changed or due active companies; does not invoke models")
    daily.add_argument("--as-of", help="Offset-aware timestamp, or YYYY-MM-DD interpreted as JST day end")
    daily.add_argument("--limit", type=int, default=10)
    claim = commands.add_parser("claim", help="Atomically lease one research job; returns JSON null if empty")
    claim.add_argument("--worker", required=True)
    claim.add_argument("--lease-seconds", type=int, default=900)
    claim.add_argument("--measurement-kind", choices=["observed", "synthetic", "unknown"], default="unknown",
                       help="Explicit provenance of the lease measurement; unknown is excluded from capacity cohorts")
    claim.add_argument("--request-id", help="Stable ID for retries of this poll; new polls need new IDs")
    claim.add_argument("--caller-namespace", help="Stable local caller namespace, supplied together with request-id")
    packet = commands.add_parser("packet", help="Show a job's frozen input packet")
    packet.add_argument("job_id")
    complete = commands.add_parser("complete", help="Atomically save numerical research, source classifications, or an opt-in qualitative review")
    complete.add_argument("job_id")
    complete.add_argument("--worker", required=True)
    complete.add_argument("--expected-attempt", required=True, type=int, help="Echo attempts from the claim that this worker received")
    complete.add_argument("--result", required=True, help="Research result JSON file")
    renew = commands.add_parser("renew", help="Extend a job's unexpired lease")
    renew.add_argument("job_id")
    renew.add_argument("--worker", required=True)
    renew.add_argument("--expected-attempt", required=True, type=int, help="Echo attempts from the claim that this worker received")
    renew.add_argument("--lease-seconds", type=int, default=900)
    renew.add_argument("--request-id", help="Stable ID for retries of this same extension")
    renew.add_argument("--caller-namespace", help="Supplied together with request-id; not authentication")
    thesis = commands.add_parser("thesis", help="Show a thesis and its deterministic valuation")
    thesis_view = commands.add_parser("thesis-view", help="Read a thesis with explicit target and DB-knowledge cutoffs")
    thesis_view.add_argument("company_id")
    thesis_view.add_argument("--as-of", required=True, help="Offset-aware target timestamp")
    thesis_view.add_argument("--knowledge-at", required=True, help="Offset-aware DB-presence cutoff")
    thesis_view.add_argument("--mode", required=True, choices=["pit", "retrospective"])
    thesis.add_argument("company_id")
    thesis.add_argument("--as-of")
    value = commands.add_parser("value", help="Calculate a scenario valuation from explicit inputs")
    value.add_argument("file", help="JSON valuation object with scenarios")
    value.add_argument("--price", required=True, help="Current price in JPY per share")
    cycle_margin = commands.add_parser("cycle-margin", help="Calculate an explicitly selected annual margin average; does not certify a cycle or value a stock")
    cycle_margin.add_argument("file", help="Explicit annual operating income/revenue and application revenue, with evidence declarations")
    for name, help_text in (("decision", "Apply an explicitly sourced decision policy; never places orders"),
                            ("ir-plan", "Compare precommitted IR answer branches at the same market quote")):
        operation = commands.add_parser(name, help=help_text)
        operation.add_argument("file", help="Decision or IR plan JSON input")
    policy = commands.add_parser("policy", help="Register immutable adopted decision policy versions")
    policy_ops = policy.add_subparsers(dest="operation", required=True)
    add_policy = policy_ops.add_parser("add")
    add_policy.add_argument("file")
    show_policy = policy_ops.add_parser("show")
    show_policy.add_argument("policy_id")
    show_policy.add_argument("--version", type=int, required=True)
    review = commands.add_parser("decision-review", help="Persist a fresh price review using the question's frozen policy")
    review_ops = review.add_subparsers(dest="operation", required=True)
    add_review = review_ops.add_parser("add")
    add_review.add_argument("file")
    show_review = review_ops.add_parser("show")
    show_review.add_argument("review_id")
    contacts = commands.add_parser("contacts", help="Import verified IR contacts as watch companies, never as investment theses")
    contact_ops = contacts.add_subparsers(dest="operation", required=True)
    import_contacts = contact_ops.add_parser("import")
    import_contacts.add_argument("file")
    import_contacts.add_argument("--imported-at", help="Offset-aware catalog import timestamp; verification dates remain unchanged")
    import_contacts.add_argument("--dry-run", action="store_true")
    info = commands.add_parser("information-value", help="Calculate explicit finite-state EVPI and EVSI")
    info.add_argument("file")
    observations = commands.add_parser("observations", help="Summarize prespecified IR observations without fitting likelihoods")
    observation_ops = observations.add_subparsers(dest="operation", required=True)
    register_observation = observation_ops.add_parser("register", help="Save an ex-ante immutable observation design")
    register_observation.add_argument("file", help="A single observation record")
    append_observation = observation_ops.add_parser("append", help="Append outcomes without changing the observation design")
    append_observation.add_argument("file", help="A complete next observation snapshot")
    append_observation.add_argument("--expected-version", required=True, type=int)
    show_observation = observation_ops.add_parser("show")
    show_observation.add_argument("observation_id")
    summarize = observation_ops.add_parser("summarize")
    summarize.add_argument("file", nargs="?", help="Optional JSON object containing a records array; omit to use saved DB snapshots")
    summarize.add_argument("--as-of", help="Offset-aware visibility cutoff; defaults to the current time")
    predictions = commands.add_parser("predictions", help="Freeze candidate signal predictions before dispatch; never fits or adopts likelihoods")
    prediction_ops = predictions.add_subparsers(dest="operation", required=True)
    register_prediction = prediction_ops.add_parser("register")
    register_prediction.add_argument("file")
    show_prediction = prediction_ops.add_parser("show")
    show_prediction.add_argument("prediction_id")
    list_predictions = prediction_ops.add_parser("list")
    list_predictions.add_argument("--as-of", help="Offset-aware visibility cutoff; defaults to the current time")
    protocols = commands.add_parser("evaluation-protocol", help="Record immutable evaluation plans without approving rules, labels or scoring")
    protocol_ops = protocols.add_subparsers(dest="operation", required=True)
    register_protocol = protocol_ops.add_parser("register")
    register_protocol.add_argument("file")
    register_protocol.add_argument("--expected-previous-version", required=True, type=int)
    show_protocol = protocol_ops.add_parser("show")
    show_protocol.add_argument("protocol_id")
    show_protocol.add_argument("--version", type=int)
    history_protocol = protocol_ops.add_parser("history")
    history_protocol.add_argument("protocol_id")
    screen = commands.add_parser("screen", help="Apply explicit sourced screening rules to bound data; returns research candidates")
    screen.add_argument("file")
    capacity = commands.add_parser("capacity", help="Summarize measured work and explicit budgets without extrapolating a company limit")
    capacity.add_argument("file")
    reinvestment = commands.add_parser("stable-reinvestment", help="Calculate explicit next-period NOPAT and growth/ROC reinvestment; no forecast adoption")
    reinvestment.add_argument("file")
    inputs = commands.add_parser("model-inputs", help="Audit the stated origins of numeric model inputs; never adopts forecasts")
    inputs.add_argument("file")
    score = commands.add_parser("score-probabilities", help="Calculate categorical Brier and log losses without fitting or verifying a prediction")
    score.add_argument("file")
    intake = commands.add_parser("intake", help="Queue classification of saved public sources before a numerical thesis exists")
    intake.add_argument("--as-of", help="Offset-aware timestamp or JST day end; default is current time")
    intake.add_argument("--limit", type=int, default=10)
    intake.add_argument("--company-id")
    qualitative = commands.add_parser("qualitative", help="Opt-in qualitative cases and jobs before a numerical thesis exists")
    qualitative_ops = qualitative.add_subparsers(dest="operation", required=True)
    qualitative_register = qualitative_ops.add_parser("register", help="Append a case configuration with compare-and-swap")
    qualitative_register.add_argument("file")
    qualitative_register.add_argument("--expected-version", type=int, required=True)
    qualitative_register.add_argument("--research-root", required=True)
    qualitative_queue = qualitative_ops.add_parser("queue", help="Queue only explicitly selected cases with new material or a due review")
    qualitative_queue.add_argument("--case-id", action="append", required=True, dest="case_ids")
    qualitative_queue.add_argument("--as-of", help="Offset-aware timestamp or JST day end; default is current time")
    qualitative_queue.add_argument("--limit", type=int, default=10)
    qualitative_show = qualitative_ops.add_parser("show", help="Show an immutable qualitative case version")
    qualitative_show.add_argument("case_id")
    qualitative_show.add_argument("--version", type=int)
    classification = commands.add_parser("source-classification", help="Show immutable source classification history")
    classification.add_argument("source_id")
    classification.add_argument("--as-of")
    quotes = commands.add_parser("quote", help="Normalize an existing immutable market source into a stored derived quote")
    quote_ops = quotes.add_subparsers(dest="operation", required=True)
    from_source = quote_ops.add_parser("from-source")
    from_source.add_argument("source_id")
    quote = commands.add_parser("normalize-quote", help="Normalize saved J-Quants daily data with explicit date precision")
    quote.add_argument("file")
    facts = commands.add_parser("normalize-facts", help="Preserve cited numeric tokens and explicit unit conversions without adopting forecasts")
    facts.add_argument("file")
    company = commands.add_parser("company", help="Manage the screened coverage universe")
    company_commands = company.add_subparsers(dest="operation", required=True)
    set_status = company_commands.add_parser("set-status")
    set_status.add_argument("company_id")
    set_status.add_argument("--status", choices=sorted(COMPANY_STATUSES), required=True)
    set_status.add_argument("--reason", required=True)
    set_status.add_argument("--held", action=argparse.BooleanOptionalAction, default=None)
    question = commands.add_parser("question", help="Manage precommitted IR questions; never sends messages")
    question_commands = question.add_subparsers(dest="operation", required=True)
    add = question_commands.add_parser("add")
    add.add_argument("file")
    show = question_commands.add_parser("show")
    show.add_argument("question_id")
    sent = question_commands.add_parser("mark-sent", help="Record a message already sent outside this tool")
    sent.add_argument("question_id")
    sent.add_argument("--sent-at", required=True)
    close = question_commands.add_parser("close", help="Close without changing investment assumptions")
    close.add_argument("question_id")
    close.add_argument("--reason", choices=["no_response", "declined", "cancelled"], required=True)
    reply = commands.add_parser("reply", help="Preserve replies and review against frozen answer branches")
    reply_commands = reply.add_subparsers(dest="operation", required=True)
    add = reply_commands.add_parser("add")
    add.add_argument("file")
    evaluate = reply_commands.add_parser("evaluate")
    evaluate.add_argument("file")
    classify = reply_commands.add_parser("classify", help="Append a correction to information classification without rewriting an applied thesis")
    classify.add_argument("file")
    show = reply_commands.add_parser("show")
    show.add_argument("reply_id")
    sync = commands.add_parser("sync", help="Read optional data SDKs and ingest a normalized bundle")
    sync.add_argument("--provider", choices=["jquants", "edinet"], required=True)
    sync.add_argument("--date", required=True, help="YYYY-MM-DD; credentials come from environment variables")
    commands.add_parser("status", help="Show record counts and work states")
    inbox = commands.add_parser("inbox", help="List IR drafts, awaiting replies, and replies needing review")
    inbox.add_argument("--limit", type=int, default=20, help="Maximum entries in each category")
    return root


_FILE_COMMANDS = frozenset({
    "value", "cycle-margin", "decision", "ir-plan", "information-value", "screen",
    "capacity", "stable-reinvestment", "model-inputs", "score-probabilities",
    "normalize-quote", "normalize-facts",
})


def _runs_without_store(args: argparse.Namespace) -> bool:
    return (args.command in _FILE_COMMANDS
            or (args.command == "observations" and args.operation == "summarize" and bool(args.file))
            or (args.command == "contacts" and args.operation == "import" and args.dry_run))


def _run_file_command(args: argparse.Namespace) -> object:
    """Keep standalone calculations separate from mutable Store startup."""
    if args.command == "value":
        return calculate_valuation(load_json(args.file), args.price)
    if args.command == "cycle-margin":
        from .cyclical_margin import calculate_cyclical_margin
        return calculate_cyclical_margin(load_json(args.file))
    if args.command in {"decision", "ir-plan"}:
        from .decision import evaluate_decision, evaluate_ir_plan
        evaluate = evaluate_decision if args.command == "decision" else evaluate_ir_plan
        return evaluate(load_json(args.file))
    if args.command == "information-value":
        from .information_value import calculate_information_value
        return calculate_information_value(load_json(args.file))
    if args.command == "screen":
        from .screening import evaluate_screening
        return evaluate_screening(load_json(args.file))
    if args.command == "capacity":
        from .capacity import report_research_capacity
        return report_research_capacity(load_json(args.file))
    if args.command == "stable-reinvestment":
        from .stable_reinvestment import calculate_stable_reinvestment
        return calculate_stable_reinvestment(load_json(args.file))
    if args.command == "model-inputs":
        from .model_inputs import audit_model_inputs
        return audit_model_inputs(load_json(args.file))
    if args.command == "score-probabilities":
        from .probability_scoring import score_categorical_forecast
        return score_categorical_forecast(load_json(args.file))
    if args.command == "normalize-quote":
        from .quotes import normalize_jquants_quote
        return normalize_jquants_quote(load_json(args.file))
    if args.command == "normalize-facts":
        from .disclosed_facts import normalize_disclosed_facts
        return normalize_disclosed_facts(load_json(args.file), now=now_iso())
    if args.command == "observations":
        from .observations import summarize_observations
        as_of = args.as_of or now_iso()
        return summarize_observations(load_json(args.file).get("records"), as_of=as_of)
    if args.command == "contacts":
        from .contacts import build_contact_bundle
        catalog = build_contact_bundle(args.file, imported_at=args.imported_at or now_iso())
        return {"summary": catalog["summary"], "rejected_rows": catalog["rejected_rows"],
                "status": "dry_run"}
    raise ValueError("Unknown file-only operation")


def run(args: argparse.Namespace, store: Store | None) -> object:
    if _runs_without_store(args):
        return _run_file_command(args)
    harness = Harness(store)
    if args.command == "init":
        return {"database": args.db, "schema_version": 1}
    if args.command == "ingest":
        return harness.ingest(load_json(args.file))
    if args.command == "daily":
        return harness.daily(args.as_of or now_iso(), args.limit)
    if args.command == "qualitative":
        from .qualitative_research import QualitativeResearch
        registry = QualitativeResearch(store)
        if args.operation == "register":
            return registry.register_case(load_json(args.file), args.expected_version,
                                          research_root=args.research_root, now=now_iso())
        if args.operation == "queue":
            return registry.queue_cases(args.case_ids, args.as_of or now_iso(), args.limit,
                                        now=now_iso())
        return registry.show_case(args.case_id, args.version)
    if args.command == "claim":
        return harness.claim(args.worker, args.lease_seconds,
                             measurement_synthetic={"observed": False, "synthetic": True, "unknown": None}[args.measurement_kind],
                             request_id=args.request_id, caller_namespace=args.caller_namespace)
    if args.command == "packet":
        return store.job(args.job_id)["packet"]
    if args.command == "thesis-view":
        return store.thesis_view(args.company_id, as_of=args.as_of, knowledge_at=args.knowledge_at, mode=args.mode)
    if args.command == "complete":
        return harness.complete(args.job_id, args.worker, load_json(args.result), expected_attempt=args.expected_attempt)
    if args.command == "renew":
        return harness.renew(args.job_id, args.worker, args.lease_seconds, expected_attempt=args.expected_attempt,
                             request_id=args.request_id, caller_namespace=args.caller_namespace)
    if args.command == "thesis":
        from .models import cutoff

        value = store.thesis(args.company_id, as_of=cutoff(args.as_of) if args.as_of else None)
        if value is None:
            raise ValueError("No thesis available for this company and time")
        return {"thesis": value, "valuation": calculate_valuation(value["valuation"], value["current_price_jpy"])}
    if args.command == "policy":
        if args.operation == "add":
            return harness.register_decision_policy(load_json(args.file))
        return store.decision_policy(args.policy_id, args.version)
    if args.command == "decision-review":
        from .information_review import current_decision_view
        if args.operation == "add":
            return harness.review_decision(load_json(args.file))
        return current_decision_view(store, store.decision_review(args.review_id))
    if args.command == "contacts":
        return harness.import_contacts(args.file, args.imported_at or now_iso(), dry_run=args.dry_run)
    if args.command == "observations":
        from .observations import summarize_observations
        from .observation_store import ObservationStore
        registry = ObservationStore(store.connection)
        if args.operation == "register":
            return registry.register(load_json(args.file), now_iso())
        if args.operation == "append":
            return registry.append(load_json(args.file), args.expected_version, now_iso())
        if args.operation == "show":
            return registry.history(args.observation_id)
        as_of = args.as_of or now_iso()
        records = load_json(args.file).get("records") if args.file else registry.records_as_of(as_of)
        return summarize_observations(records, as_of=as_of)
    if args.command == "predictions":
        from .prediction_store import PredictionStore
        registry = PredictionStore(store.connection)
        if args.operation == "register":
            return registry.register(load_json(args.file), now_iso())
        if args.operation == "show":
            return registry.show(args.prediction_id)
        return registry.list_as_of(args.as_of or now_iso())
    if args.command == "evaluation-protocol":
        from .evaluation_protocols import EvaluationProtocols
        registry = EvaluationProtocols(store.connection)
        if args.operation == "register":
            return registry.register(load_json(args.file), args.expected_previous_version, now=now_iso())
        if args.operation == "show":
            return registry.show(args.protocol_id, args.version)
        return registry.history(args.protocol_id)
    if args.command == "intake":
        from .intake import Intake
        return Intake(store).queue(args.as_of or now_iso(), args.limit, args.company_id)
    if args.command == "source-classification":
        from .intake import classifications
        return classifications(store, args.source_id, as_of=args.as_of)
    if args.command == "quote":
        return harness.normalize_quote(args.source_id)
    if args.command == "company":
        return harness.set_company_status(args.company_id, args.status, args.reason, args.held)
    if args.command == "question":
        if args.operation == "add":
            return harness.add_question(load_json(args.file))
        if args.operation == "show":
            return store.question(args.question_id)
        if args.operation == "mark-sent":
            return harness.mark_sent(args.question_id, args.sent_at)
        if args.operation == "close":
            return harness.close_question(args.question_id, args.reason)
    if args.command == "reply":
        from .information_review import add_assessment, assessments, current_evaluation_view
        if args.operation == "add":
            return harness.add_reply(load_json(args.file))
        if args.operation == "classify":
            return add_assessment(store, load_json(args.file), now=now_iso())
        if args.operation == "evaluate":
            return harness.evaluate_reply(load_json(args.file))
        if args.operation == "show":
            checked_at = now_iso()
            evaluations = [current_evaluation_view(store, json.loads(r["data"]), now=checked_at) for r in
                           store.connection.execute("SELECT data FROM evaluations WHERE reply_id=? ORDER BY version", (args.reply_id,))]
            return {"reply": store.reply(args.reply_id), "evaluations": evaluations,
                    "information_reviews": assessments(store, args.reply_id)}
    if args.command == "sync":
        from .adapters import fetch_edinet_documents, fetch_jquants_daily

        bundle = fetch_jquants_daily(args.date) if args.provider == "jquants" else fetch_edinet_documents(args.date)
        result = harness.ingest(bundle)
        for field in ("skipped_security_codes", "skipped_documents"):
            if field in bundle:
                result[field] = bundle[field]
        return result
    if args.command == "status":
        return harness.status()
    if args.command == "inbox":
        return harness.inbox(args.limit)
    raise ValueError("Unknown operation")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    store = None
    try:
        if not _runs_without_store(args):
            store = Store(args.db)
        result = run(args, store)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, sqlite3.Error, ImportError, DataAdapterError) as error:
        print(f"ir-agent: {error}", file=sys.stderr)
        return 1
    finally:
        if store is not None:
            store.close()
