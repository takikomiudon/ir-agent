"""Run the complete synthetic workflow in a disposable local database."""

import json
from datetime import datetime
import tempfile
from pathlib import Path

from ir_agent.harness import Harness
from ir_agent.models import load_json
from ir_agent.store import Store
from ir_agent.valuation import calculate_valuation


def main() -> None:
    examples = Path(__file__).resolve().parents[1] / "examples"
    with tempfile.TemporaryDirectory(prefix="ir-agent-demo-") as temporary:
        store = Store(Path(temporary) / "demo.sqlite3")
        try:
            harness = Harness(store)
            harness.ingest(load_json(examples / "demo.json"), now=datetime.fromisoformat("2026-10-08T15:06:00+09:00"))
            initial = store.thesis("demo-services")
            initial_value = calculate_valuation(initial["valuation"], initial["current_price_jpy"])
            daily = harness.daily("2026-10-08", limit=5, now=datetime.fromisoformat("2026-10-09T08:58:00+09:00"))
            job = harness.claim("demo-worker", measurement_synthetic=True, now=datetime.fromisoformat("2026-10-09T08:59:00+09:00"))
            if job is None:
                raise RuntimeError("Expected a synthetic research job")
            harness.complete(job["id"], "demo-worker", load_json(examples / "research-result.json"), expected_attempt=job["attempts"], now=datetime.fromisoformat("2026-10-09T09:00:00+09:00"))
            harness.add_question(load_json(examples / "question.json"), now=datetime.fromisoformat("2026-10-09T10:01:00+09:00"))
            harness.mark_sent("demo-question-cost", "2026-10-09T11:00:00+09:00")
            harness.add_reply(load_json(examples / "reply.json"), now=datetime.fromisoformat("2026-10-09T16:00:00+09:00"))
            evaluated = harness.evaluate_reply(load_json(examples / "reply-evaluation.json"), now=datetime.fromisoformat("2026-10-09T17:00:00+09:00"))
            print(json.dumps({
                "synthetic": True, "network_requests": 0,
                "queued_companies": [item["company_id"] for item in daily["selected"]],
                "initial_expected_value_jpy": initial_value["expected_value_jpy"],
                "updated_expected_value_jpy": evaluated["valuation"]["expected_value_jpy"],
                "thesis_version": evaluated["thesis_version"],
                "price_checked_action": evaluated["action"], "precommitted_action": evaluated["precommitted_action"], "records": harness.status(),
            }, ensure_ascii=False, indent=2))
        finally:
            store.close()


if __name__ == "__main__":
    main()
