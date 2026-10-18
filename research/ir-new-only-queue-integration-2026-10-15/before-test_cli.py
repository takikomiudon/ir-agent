"""Exercise the JSON CLI boundary without network requests or IR sends."""

from __future__ import annotations

import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from ir_agent.adapters.common import DataAdapterError
from ir_agent.cli import main


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class CliTests(unittest.TestCase):
    def setUp(self):
        clock = patch("ir_agent.harness.datetime", wraps=datetime)
        clock.start().now.return_value = datetime(2026, 10, 11, tzinfo=timezone.utc)
        self.addCleanup(clock.stop)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.database = self.directory / "research.sqlite3"

    def invoke(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["--db", str(self.database), *map(str, arguments)])
        return code, stdout.getvalue(), stderr.getvalue()

    def succeed(self, *arguments):
        code, output, error = self.invoke(*arguments)
        self.assertEqual(code, 0, error)
        self.assertEqual(error, "")
        return json.loads(output)

    def fail(self, *arguments):
        code, output, error = self.invoke(*arguments)
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertTrue(error.startswith("ir-agent: "), error)
        self.assertNotIn("Traceback", error)
        return error

    def seed(self):
        # Seed the multi-day fixture after its latest retrieved disclosure,
        # before the historical daily cutoff; later CLI operations keep their
        # independent runtime clock from setUp.
        with patch("ir_agent.harness.datetime", wraps=datetime) as seed_clock:
            seed_clock.now.return_value = datetime.fromisoformat("2026-10-08T15:06:00+09:00")
            self.succeed("ingest", EXAMPLES / "demo.json")
        selected = self.succeed("daily", "--as-of", "2026-10-08")["selected"]
        self.assertEqual([item["company_id"] for item in selected], ["demo-services"])
        return selected[0]["job_id"]

    def research(self):
        job_id = self.seed()
        claimed = self.succeed("claim", "--worker", "cli-worker")
        self.assertEqual(claimed["id"], job_id)
        self.succeed("complete", job_id, "--worker", "cli-worker",
                     "--expected-attempt", claimed['attempts'], "--result", EXAMPLES / "research-result.json")
        return job_id

    def test_claim_measurement_provenance_is_explicit_and_unknown_by_default(self):
        for label, expected in (('observed', False), ('synthetic', True), ('unknown', None)):
            with self.subTest(label=label):
                self.database = self.directory / (label + '.sqlite3')
                self.seed()
                flags = [] if label == 'unknown' else ['--measurement-kind', label]
                self.succeed('claim', '--worker', 'cli-worker', *flags)
                with sqlite3.connect(self.database) as connection:
                    record = json.loads(connection.execute('SELECT data FROM job_attempts').fetchone()[0])
                self.assertIs(record['synthetic'], expected)

    def test_json_workflow_exposes_drafts_replies_and_updated_valuation(self):
        self.research()
        self.succeed("question", "add", EXAMPLES / "question.json")
        inbox = self.succeed("inbox")
        self.assertEqual([item["id"] for item in inbox["drafts"]], ["demo-question-cost"])
        self.assertFalse(inbox["drafts"][0]["stale_thesis"])
        self.succeed("question", "mark-sent", "demo-question-cost",
                     "--sent-at", "2026-10-09T11:00:00+09:00")
        inbox = self.succeed("inbox")
        self.assertEqual(inbox["drafts"], [])
        self.assertEqual(len(inbox["awaiting_replies"]), 1)
        self.succeed("reply", "add", EXAMPLES / "reply.json")
        inbox = self.succeed("inbox")
        self.assertEqual(inbox["awaiting_replies"], [])
        self.assertEqual(inbox["replies_for_review"][0]["status"], "unevaluated")
        applied = self.succeed("reply", "evaluate", EXAMPLES / "reply-evaluation.json")
        self.assertTrue(applied["applied"])
        self.assertEqual(applied["thesis_version"], 3)
        self.assertEqual(applied["valuation"]["expected_value_jpy"], "1328.75")
        self.assertEqual(self.succeed("inbox")["replies_for_review"], [])
        self.assertEqual(self.succeed("reply", "evaluate", EXAMPLES / "reply-evaluation.json"), applied)
        history = self.succeed("reply", "show", "demo-reply-cost")
        self.assertEqual(len(history["evaluations"]), 1)

    def test_lease_renewal_rejects_other_worker_without_losing_job(self):
        job_id = self.seed()
        initial = self.succeed("claim", "--worker", "cli-worker", "--lease-seconds", "120")
        self.assertIn("lease owner", self.fail("renew", job_id, "--worker", "other-worker", "--expected-attempt", initial['attempts']))
        renewed = self.succeed("renew", job_id, "--worker", "cli-worker", "--expected-attempt", initial['attempts'], "--lease-seconds", "600")
        self.assertGreater(renewed["lease_until"], initial["lease_until"])
        self.assertEqual(renewed["attempts"], 1)
        self.assertIsNone(self.succeed("claim", "--worker", "other-worker"))
        self.succeed("complete", job_id, "--worker", "cli-worker",
                     "--expected-attempt", initial['attempts'], "--result", EXAMPLES / "research-result.json")

    def test_held_reply_stays_in_inbox_until_review_is_applied(self):
        self.research()
        self.succeed("question", "add", EXAMPLES / "question.json")
        self.succeed("question", "mark-sent", "demo-question-cost",
                     "--sent-at", "2026-10-09T11:00:00+09:00")
        reply = json.loads((EXAMPLES / "reply.json").read_text())
        reply["information_status"] = "unclear"
        reply_file = self.directory / "reply.json"
        reply_file.write_text(json.dumps(reply, ensure_ascii=False))
        self.succeed("reply", "add", reply_file)
        evaluation = json.loads((EXAMPLES / "reply-evaluation.json").read_text())
        evaluation.pop("information_status", None)
        evaluation_file = self.directory / "evaluation.json"
        evaluation_file.write_text(json.dumps(evaluation, ensure_ascii=False))
        first = self.succeed("reply", "evaluate", evaluation_file)
        self.assertEqual(first["status"], "held_for_review")
        inbox = self.succeed("inbox")
        self.assertEqual(inbox["replies_for_review"][0]["evaluation_version"], 1)
        self.assertEqual(self.succeed("thesis", "demo-services")["thesis"]["version"], 2)
        evaluation.update(expected_evaluation_version=1, information_status="public_clarification",
                          recorded_at="2026-10-09T17:30:00+09:00")
        evaluation_file.write_text(json.dumps(evaluation, ensure_ascii=False))
        self.assertTrue(self.succeed("reply", "evaluate", evaluation_file)["applied"])
        self.assertEqual(self.succeed("inbox")["replies_for_review"], [])

    def test_non_finite_json_is_rejected_before_ingest(self):
        invalid = self.directory / "invalid.json"
        invalid.write_text('{"schema_version": 1, "companies": [], "value": NaN}')
        self.fail("ingest", invalid)
        self.assertEqual(self.succeed("status")["companies"], 0)

    def test_sdk_errors_return_a_normal_cli_failure(self):
        for provider, function in (("jquants", "fetch_jquants_daily"), ("edinet", "fetch_edinet_documents")):
            with self.subTest(provider=provider), patch(
                f"ir_agent.adapters.{function}", side_effect=DataAdapterError("Check API credentials and permissions")
            ) as fetch:
                error = self.fail("sync", "--provider", provider, "--date", "2026-10-08")
                self.assertIn("Check API credentials", error)
                fetch.assert_called_once_with("2026-10-08")
        self.assertEqual(self.succeed("status")["sources"], 0)


if __name__ == "__main__":
    unittest.main()
