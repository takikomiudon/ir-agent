"""Financial evidence, IR lifecycle, and concurrent worker regressions.

All companies, disclosures, replies, and valuations are fictional. These tests
exercise the local state machine; they never contact companies or place orders.
"""

from __future__ import annotations

import copy
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ir_agent.harness import Harness
from ir_agent.store import Store


AS_OF = "2026-10-10T03:00:00+00:00"
NOW = datetime(2026, 10, 10, 3, tzinfo=timezone.utc)
CREATED = "2026-10-10T04:00:00+00:00"
SENT = "2026-10-10T04:05:00+00:00"
RECEIVED = "2026-10-10T04:10:00+00:00"
EVALUATED = "2026-10-10T04:15:00+00:00"
EVALUATION_NOW = datetime(2026, 10, 10, 4, 20, tzinfo=timezone.utc)
RAW_REPLY = "既に公表した資料の補足です。価格改定効果は継続しています。"
QUOTE = "価格改定効果は継続しています。"


def valuation(eps="50"):
    return {"scenarios": [{
        "name": "base", "probability": "1", "method": "eps_multiple",
        "inputs": {"eps_jpy": eps, "pe": "20"},
    }]}


def source(company_id, source_id, *, published="2026-10-01T00:00:00+00:00",
           retrieved="2026-10-01T00:05:00+00:00"):
    return {
        "id": source_id, "company_id": company_id, "title": "架空企業の公開資料",
        "url": f"https://example.com/{company_id}/ir/{source_id}",
        "source_type": "public_disclosure", "published_at": published,
        "retrieved_at": retrieved, "content": "公表済みの価格改定と利益率の説明。",
    }


def thesis(company_id="c1", *, version=1, eps="50",
           recorded="2026-10-01T01:00:00+00:00", evidence=None):
    return {
        "company_id": company_id, "version": version, "recorded_at": recorded,
        "statement": "価格改定による利益率の改善が翌期も続くと仮定する。",
        "pillars": ["価格改定の効果が続く"],
        "invalidation_conditions": ["販売数量の減少が価格効果を上回る"],
        "evidence_ids": evidence if evidence is not None else [f"{company_id}-baseline"],
        "next_review_date": "2026-10-20", "current_price_jpy": "1000",
        "valuation": valuation(eps),
    }


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "research.sqlite3"
        self.store = Store(self.path)
        self.addCleanup(self.store.close)
        self.harness = Harness(self.store)
        self._seed()

    def _seed(self, company_id="c1", *, held=False):
        bundle = {
            "schema_version": 1,
            "companies": [{"id": company_id, "name": f"架空企業 {company_id}",
                           "security_code": "0000", "status": "active", "held": held}],
            "sources": [source(company_id, f"{company_id}-baseline")],
            "theses": [thesis(company_id)],
        }
        # Explicit fictional persistence time, after the baseline thesis/data.
        self.harness.ingest(bundle, now=datetime(2026, 10, 1, 1, tzinfo=timezone.utc))
        return bundle

    def _add_source(self, source_id="c1-new", company_id="c1", *, now=None, **kwargs):
        value = source(company_id, source_id, **kwargs)
        saved = now or max(NOW, datetime.fromisoformat(value["retrieved_at"]))
        self.harness.ingest({"schema_version": 1, "sources": [value]}, now=saved)
        return value

    def _queue(self):
        self._add_source(published="2026-10-10T00:00:00+00:00",
                         retrieved="2026-10-10T00:05:00+00:00")
        selected = self.harness.daily(AS_OF, now=NOW)["selected"]
        self.assertEqual(len(selected), 1)
        return self.store.job(selected[0]["job_id"])

    def _result(self, job, *, eps="60", recorded="2026-10-10T03:01:00+00:00"):
        updated = copy.deepcopy(job["packet"]["thesis"])
        updated.update(version=updated["version"] + 1, recorded_at=recorded,
                       next_review_date="2026-10-20", valuation=valuation(eps))
        updated["evidence_ids"] = list(dict.fromkeys(
            updated["evidence_ids"] + job["packet"]["new_source_ids"]
        ))
        return {
            "summary": "公開資料の価格改定効果を反映し、EPS仮定を更新した。",
            "evidence_ids": list(updated["evidence_ids"]),
            "counterarguments": ["数量減少によって利益率の改善が続かない可能性がある。"],
            "proposed_action": "buy_review", "thesis_update": updated,
        }

    def _question(self, question_id="q1", *, company_id="c1", topic="margin_driver"):
        current = self.store.thesis(company_id)
        return {
            "id": question_id, "company_id": company_id, "topic": topic,
            "thesis_version": current["version"], "created_at": CREATED,
            "question": "公開資料の価格改定効果は継続的なものとの理解でよいでしょうか。",
            "target_parameter": "eps_jpy", "evidence_ids": list(current["evidence_ids"]),
            "contact_url": f"https://example.com/{company_id}/ir/contact",
            "branches": [
                {"id": "sustained", "condition": "価格効果が持続すると説明される",
                 "interpretation": "利益率の持続改善を支持", "action": "buy_review",
                 "valuation": valuation("70")},
                {"id": "temporary", "condition": "価格効果が一時的と説明される",
                 "interpretation": "利益率の持続改善を反証", "action": "exit_review",
                 "valuation": valuation("40")},
                {"id": "unclear", "condition": "判断に必要な説明がない",
                 "interpretation": "既存の仮説と評価額を維持", "action": "unresolved"},
            ],
        }

    def _sent_question(self, question=None):
        question = question or self._question()
        self.harness.add_question(question, now=datetime.fromisoformat(CREATED))
        return self.harness.mark_sent(question["id"], SENT, now=datetime.fromisoformat(SENT))

    def _reply(self, *, reply_id="r1", question_id="q1", information="public_clarification"):
        return {
            "id": reply_id, "question_id": question_id, "raw_text": RAW_REPLY,
            "received_at": RECEIVED, "information_status": information,
        }

    def _evaluation(self, *, version=1, branch="sustained", reply_id="r1"):
        return {
            "reply_id": reply_id, "branch_id": branch, "basis_quote": QUOTE,
            "rationale": "公開済み情報の補足が、送信前に定義した回答分岐に一致する。",
            "recorded_at": EVALUATED, "expected_thesis_version": version,
            "next_review_date": "2026-10-20",
        }

    def test_reingest_is_idempotent_and_preserves_first_retrieval(self):
        bundle = self._seed()
        before = self.harness.status()
        refreshed = copy.deepcopy(bundle)
        refreshed["sources"][0]["retrieved_at"] = "2026-10-02T00:05:00+00:00"
        result = self.harness.ingest(refreshed, now=datetime(2026, 10, 2, 1, tzinfo=timezone.utc))
        self.assertEqual(result["sources_added"], 0)
        self.assertEqual(result["theses_added"], 0)
        self.assertEqual(self.harness.status(), before)
        self.assertEqual(self.store.source("c1-baseline")["retrieved_at"],
                         "2026-10-01T00:05:00+00:00")
        self.assertEqual(self.store.thesis("c1")["version"], 1)

    def test_ingest_failure_rolls_back_earlier_company_and_source_writes(self):
        before = self.harness.status()
        old_company = self.store.company("c1")
        changed_source = source("c1", "c1-baseline")
        changed_source["content"] = "別の証拠で同じIDを使おうとする。"
        bundle = {
            "schema_version": 1,
            "companies": [dict(old_company, name="変更してはいけない名称"),
                          {"id": "c2", "name": "新しい架空企業", "status": "active"}],
            "sources": [source("c2", "c2-new"), changed_source],
        }
        with self.assertRaisesRegex(ValueError, "reused"):
            self.harness.ingest(bundle, now=NOW)
        self.assertEqual(self.harness.status(), before)
        self.assertEqual(self.store.company("c1"), old_company)
        with self.assertRaises(ValueError):
            self.store.company("c2")
        with self.assertRaises(ValueError):
            self.store.source("c2-new")

    def test_saved_thesis_and_retrieval_time_cannot_be_rewritten(self):
        changed = thesis(eps="90")
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.harness.ingest({"schema_version": 1, "theses": [changed]}, now=NOW)
        skipped = thesis(version=3, recorded=AS_OF)
        with self.assertRaisesRegex(ValueError, "Stale or skipped"):
            self.harness.ingest({"schema_version": 1, "theses": [skipped]}, now=NOW)
        earlier = source("c1", "c1-baseline", retrieved="2026-10-01T00:01:00+00:00")
        with self.assertRaisesRegex(ValueError, "backdate"):
            self.harness.ingest({"schema_version": 1, "sources": [earlier]}, now=NOW)
        self.assertEqual(self.store.thesis("c1")["valuation"], valuation())
        self.assertEqual(self.harness.status()["theses"], 1)

    def test_thesis_and_question_reject_evidence_for_another_company(self):
        self._seed("c2")
        foreign = thesis(version=2, recorded=AS_OF, evidence=["c2-baseline"])
        with self.assertRaisesRegex(ValueError, "another company"):
            self.harness.ingest({"schema_version": 1, "theses": [foreign]}, now=NOW)
        question = self._question()
        question["evidence_ids"] = ["c2-baseline"]
        with self.assertRaisesRegex(ValueError, "same company"):
            self.harness.add_question(question, now=datetime.fromisoformat(CREATED))
        self.assertEqual(self.harness.status()["questions"], {})
        self.assertEqual(self.store.thesis("c1")["version"], 1)

    def test_daily_excludes_future_publication_and_future_retrieval(self):
        self._add_source("available", published="2026-10-10T01:00:00+00:00",
                         retrieved="2026-10-10T01:05:00+00:00")
        self._add_source("future-publication", published="2026-10-10T04:00:00+00:00",
                         retrieved="2026-10-10T04:05:00+00:00")
        self._add_source("future-retrieval", published="2026-10-09T01:00:00+00:00",
                         retrieved="2026-10-10T04:05:00+00:00")
        selected = self.harness.daily(AS_OF, now=NOW)["selected"]
        packet = self.store.job(selected[0]["job_id"])["packet"]
        self.assertEqual(packet["new_source_ids"], ["available"])
        self.assertEqual({s["id"] for s in packet["sources"]}, {"c1-baseline", "available"})

    def test_date_as_of_uses_japan_day_boundary(self):
        self._add_source("before-midnight-jst", published="2026-10-10T14:58:00+00:00",
                         retrieved="2026-10-10T14:59:00+00:00")
        self._add_source("after-midnight-jst", published="2026-10-10T14:58:00+00:00",
                         retrieved="2026-10-10T15:00:00+00:00")
        result = self.harness.daily("2026-10-10", now=datetime.fromisoformat("2026-10-10T23:59:59.999999+09:00"))
        packet = self.store.job(result["selected"][0]["job_id"])["packet"]
        self.assertEqual(packet["new_source_ids"], ["before-midnight-jst"])

    def test_daily_uses_historical_thesis_without_future_version(self):
        self._add_source()
        future = thesis(version=2, eps="90", recorded="2026-10-11T01:00:00+00:00")
        self.harness.ingest({"schema_version": 1, "theses": [future]}, now=datetime.fromisoformat(future["recorded_at"]))
        result = self.harness.daily(AS_OF, now=NOW)
        packet = self.store.job(result["selected"][0]["job_id"])["packet"]
        self.assertEqual(packet["thesis"]["version"], 1)
        self.assertEqual(packet["valuation"]["expected_value_jpy"], "1000.00")

    def test_daily_repeated_selection_creates_one_frozen_job(self):
        queued = self._queue()
        again = self.harness.daily(AS_OF, now=NOW)
        self.assertEqual(again["selected"][0]["job_id"], queued["id"])
        self.assertEqual(self.harness.status()["jobs"], {"pending": 1})
        self.assertEqual(self.store.job(queued["id"])["packet"], queued["packet"])

    def test_normal_daily_claim_completion_advances_thesis_once(self):
        self._queue()
        job = self.harness.claim("worker-a", now=NOW)
        self.assertEqual(job["status"], "leased")
        result = self._result(job)
        completed = self.harness.complete(job["id"], "worker-a", result,
                                          now=NOW + timedelta(minutes=1))
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(self.store.thesis("c1")["version"], 2)
        self.assertEqual(self.store.thesis("c1")["valuation"], valuation("60"))
        retry = self.harness.complete(job["id"], "worker-a", result,
                                     now=NOW + timedelta(minutes=2))
        self.assertEqual(retry, completed)
        self.assertEqual(self.harness.status()["theses"], 2)
        self.assertEqual(self.harness.daily("2026-10-11", now=datetime.fromisoformat("2026-10-11T23:59:59.999999+09:00"))["selected"], [])

    def test_worker_identity_and_lease_expiry_protect_completion(self):
        self._queue()
        job = self.harness.claim("worker-a", lease_seconds=60, now=NOW)
        result = self._result(job, recorded=AS_OF)
        with self.assertRaisesRegex(ValueError, "lease owner"):
            self.harness.complete(job["id"], "worker-b", result, now=NOW)
        with self.assertRaisesRegex(ValueError, "Lease expired"):
            self.harness.complete(job["id"], "worker-a", result,
                                  now=NOW + timedelta(seconds=60))
        reclaimed = self.harness.claim("worker-b", lease_seconds=60,
                                      now=NOW + timedelta(seconds=60))
        self.assertEqual(reclaimed["id"], job["id"])
        self.assertEqual(reclaimed["attempts"], 2)
        with self.assertRaisesRegex(ValueError, "lease owner"):
            self.harness.complete(job["id"], "worker-a", result,
                                  expected_attempt=reclaimed['attempts'],
                                  now=NOW + timedelta(seconds=61))
        self.assertEqual(self.store.thesis("c1")["version"], 1)

    def _assert_completion_clock_rejected_atomically(self, recorded):
        self._queue()
        job = self.harness.claim("worker-a", now=NOW)
        result = self._result(job, recorded=recorded)
        before = self.harness.status()
        before_thesis = self.store.thesis("c1")
        before_reviews = self.store.connection.execute(
            "SELECT COUNT(*) FROM source_reviews"
        ).fetchone()[0]
        with self.assertRaisesRegex(ValueError, "recorded_at must be between"):
            self.harness.complete(job["id"], "worker-a", result,
                                  now=NOW + timedelta(minutes=1))
        self.assertEqual(self.harness.status(), before)
        self.assertEqual(self.store.job(job["id"]), job)
        self.assertEqual(self.store.thesis("c1"), before_thesis)
        self.assertEqual(self.store.connection.execute(
            "SELECT COUNT(*) FROM source_reviews"
        ).fetchone()[0], before_reviews)

    def test_completion_recorded_before_packet_as_of_is_rejected_atomically(self):
        # The evidence is already available at 00:05; only the report's claimed
        # creation time, earlier than the 03:00 research packet, is invalid.
        self._assert_completion_clock_rejected_atomically("2026-10-10T02:59:59+00:00")

    def test_completion_recorded_after_completion_clock_is_rejected_atomically(self):
        self._assert_completion_clock_rejected_atomically("2026-10-10T03:02:00+00:00")

    def test_incomplete_or_out_of_packet_result_does_not_modify_state(self):
        self._queue()
        job = self.harness.claim("worker-a", now=NOW)
        incomplete = self._result(job)
        incomplete["counterarguments"] = []
        with self.assertRaises(ValueError):
            self.harness.complete(job["id"], "worker-a", incomplete,
                                  now=NOW + timedelta(minutes=1))
        self._add_source("late", published="2026-10-10T03:05:00+00:00",
                         retrieved="2026-10-10T03:06:00+00:00")
        outside = self._result(job, recorded="2026-10-10T03:10:00+00:00")
        outside["evidence_ids"].append("late")
        outside["thesis_update"]["evidence_ids"].append("late")
        with self.assertRaisesRegex(ValueError, "outside the frozen"):
            self.harness.complete(job["id"], "worker-a", outside,
                                  now=NOW + timedelta(minutes=10))
        self.assertEqual(self.store.job(job["id"])["status"], "leased")
        self.assertIsNone(self.store.job(job["id"])["result"])
        self.assertEqual(self.store.thesis("c1")["version"], 1)

    def test_stale_worker_result_cannot_overwrite_newer_thesis(self):
        self._queue()
        job = self.harness.claim("worker-a", now=NOW)
        external_update = thesis(version=2, eps="80", recorded=AS_OF)
        self.harness.ingest({"schema_version": 1, "theses": [external_update]}, now=NOW)
        with self.assertRaises(ValueError):
            self.harness.complete(job["id"], "worker-a", self._result(job),
                                  now=NOW + timedelta(minutes=1))
        self.assertEqual(self.store.thesis("c1")["valuation"], valuation("80"))
        self.assertEqual(self.harness.status()["theses"], 2)
        self.assertEqual(self.store.job(job["id"])["status"], "leased")

    def test_independent_connections_serialize_same_company_leases(self):
        self._queue()
        self._add_source("c1-second")
        self.harness.daily(AS_OF, now=NOW)
        self.assertEqual(self.harness.status()["jobs"], {"pending": 2})
        other_store = Store(self.path)
        self.addCleanup(other_store.close)
        other_harness = Harness(other_store)
        first = self.harness.claim("worker-a", lease_seconds=60, now=NOW)
        self.assertIsNone(other_harness.claim("worker-b", now=NOW))
        self.assertEqual(self.harness.status()["jobs"], {"leased": 1, "pending": 1})
        reclaimed = other_harness.claim("worker-b", now=NOW + timedelta(seconds=60))
        self.assertEqual(reclaimed["id"], first["id"])
        self.assertEqual(reclaimed["lease_owner"], "worker-b")
        self.assertEqual(reclaimed["attempts"], 2)
        self.assertIsNone(self.harness.claim("worker-c", now=NOW + timedelta(seconds=61)))

    def test_parallel_claims_never_assign_same_job_or_company_twice(self):
        self._seed("c2")
        self._add_source()
        self._add_source("c2-new", "c2")
        self.harness.daily(AS_OF, now=NOW)
        barrier = threading.Barrier(2)

        def claim_in_thread(worker):
            store = Store(self.path)
            try:
                barrier.wait(timeout=5)
                return Harness(store).claim(worker, now=NOW)
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = list(pool.map(claim_in_thread, ("worker-a", "worker-b")))
        self.assertTrue(all(job is not None for job in jobs))
        self.assertEqual(len({job["id"] for job in jobs}), 2)
        self.assertEqual({job["company_id"] for job in jobs}, {"c1", "c2"})
        self.assertEqual(self.harness.status()["jobs"], {"leased": 2})

    def test_question_branches_are_frozen_before_send_and_reply(self):
        question = self._question()
        stored = self.harness.add_question(question, now=datetime.fromisoformat(CREATED))
        self.assertEqual(stored["thesis_snapshot"], self.store.thesis("c1"))
        self.assertEqual(self.harness.add_question(question, now=datetime.fromisoformat(CREATED)), stored)
        changed = copy.deepcopy(question)
        changed["branches"][0]["valuation"] = valuation("99")
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.harness.add_question(changed, now=datetime.fromisoformat(CREATED))
        self.assertEqual(self.store.question("q1")["branches"], question["branches"])
        self._sent_question(question)
        self.harness.add_reply(self._reply(), now=datetime.fromisoformat(RECEIVED))
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.harness.add_question(changed, now=datetime.fromisoformat(CREATED))

    def test_question_requires_time_unresolved_branch_and_available_evidence(self):
        no_time = self._question()
        del no_time["created_at"]
        no_unresolved = self._question()
        no_unresolved["branches"] = no_unresolved["branches"][:2]
        self._add_source("future-for-question", published="2026-10-10T05:00:00+00:00",
                         retrieved="2026-10-10T05:05:00+00:00")
        future_evidence = self._question()
        future_evidence["evidence_ids"] = ["future-for-question"]
        for question in (no_time, no_unresolved, future_evidence):
            with self.subTest(question=question), self.assertRaises(ValueError):
                self.harness.add_question(question, now=datetime.fromisoformat(CREATED))
        self.assertEqual(self.harness.status()["questions"], {})

    def test_thesis_change_requires_regenerating_question_before_sending(self):
        question = self._question()
        self.harness.add_question(question, now=datetime.fromisoformat(CREATED))
        self.harness.ingest({"schema_version": 1, "theses": [
            thesis(version=2, eps="60", recorded=AS_OF),
        ]}, now=datetime.fromisoformat(CREATED) + timedelta(minutes=1))
        with self.assertRaisesRegex(ValueError, "Thesis changed"):
            self.harness.mark_sent("q1", SENT, now=datetime.fromisoformat(SENT))
        stored = self.store.question("q1")
        self.assertEqual(stored["status"], "draft")
        self.assertEqual(stored["thesis_snapshot"]["version"], 1)
        self.assertEqual(stored["thesis_snapshot"]["valuation"], valuation())

    def test_one_open_question_per_topic_and_expiry_preserves_thesis(self):
        self._sent_question()
        with self.assertRaisesRegex(ValueError, "open question"):
            self.harness.add_question(self._question("q2"), now=datetime.fromisoformat(CREATED))
        self.harness.close_question("q1", "no_response")
        self.assertEqual(self.store.question("q1")["status"], "expired")
        self.assertEqual(self.store.thesis("c1")["version"], 1)
        self.assertEqual(self.store.thesis("c1")["valuation"], valuation())
        self.assertEqual(self.harness.add_question(self._question("q2"), now=datetime.fromisoformat(CREATED))["status"], "draft")
        # A late response remains attached to the original recorded sent question.
        self.harness.add_reply(self._reply(), now=datetime.fromisoformat(RECEIVED))
        self.assertEqual(self.store.question("q1")["status"], "answered")

    def test_send_and_reply_timestamps_and_reply_immutability(self):
        self.harness.add_question(self._question(), now=datetime.fromisoformat(CREATED))
        with self.assertRaises(ValueError):
            self.harness.add_reply(self._reply(), now=datetime.fromisoformat(RECEIVED))
        with self.assertRaisesRegex(ValueError, "predate"):
            self.harness.mark_sent("q1", "2026-10-10T03:59:00+00:00", now=datetime.fromisoformat(SENT))
        sent = self.harness.mark_sent("q1", SENT, now=datetime.fromisoformat(SENT))
        self.assertEqual(self.harness.mark_sent("q1", SENT, now=datetime.fromisoformat(SENT)), sent)
        early = self._reply()
        early["received_at"] = "2026-10-10T04:04:00+00:00"
        with self.assertRaisesRegex(ValueError, "predate"):
            self.harness.add_reply(early, now=datetime.fromisoformat(RECEIVED))
        reply = self._reply()
        self.assertEqual(self.harness.add_reply(reply, now=datetime.fromisoformat(RECEIVED)), self.harness.add_reply(reply, now=datetime.fromisoformat(RECEIVED)))
        edited = dict(reply, raw_text="返信を後から改変する。")
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.harness.add_reply(edited, now=datetime.fromisoformat(RECEIVED))
        self.assertEqual(self.store.reply("r1")["raw_text"], RAW_REPLY)

    def test_ir_reply_updates_frozen_branch_valuation_after_research_v2(self):
        self._queue()
        job = self.harness.claim("worker-a", now=NOW)
        self.harness.complete(job["id"], "worker-a", self._result(job),
                              now=NOW + timedelta(minutes=1))
        self._sent_question()
        self.harness.add_reply(self._reply(), now=datetime.fromisoformat(RECEIVED))
        request = self._evaluation(version=2)
        evaluation = self.harness.evaluate_reply(request, now=EVALUATION_NOW)
        self.assertTrue(evaluation["applied"])
        self.assertEqual(evaluation["action"], "unresolved")
        self.assertEqual(evaluation["precommitted_action"], "buy_review")
        self.assertEqual(evaluation["decision_status"], "missing_decision_contract")
        self.assertEqual(evaluation["thesis_version"], 3)
        self.assertEqual(evaluation["valuation"]["expected_value_jpy"], "1400.00")
        current = self.store.thesis("c1")
        self.assertEqual(current["valuation"], valuation("70"))
        self.assertIn("reply:r1", current["evidence_ids"])
        evidence = self.store.source("reply:r1")
        self.assertEqual(evidence["content"], RAW_REPLY)
        self.assertEqual(evidence["source_type"], "ir_reply")
        self.assertIsNone(evidence["published_at"])
        self.assertFalse(evidence["requires_research"])
        self.assertEqual(self.harness.evaluate_reply(request, now=EVALUATION_NOW), evaluation)
        self.assertEqual(self.harness.status()["evaluations"], 1)
        self.assertEqual(self.harness.status()["theses"], 3)

    def test_ambiguous_and_potential_nonpublic_replies_are_held_without_application(self):
        # Both questions are saved/sent before either reply is persisted. This
        # keeps the fixture's shared runtime clock monotone across subcases.
        for index in range(2):
            self._sent_question(self._question(f"q{index}", topic=f"topic{index}"))
        for index, information in enumerate(("unclear", "potential_nonpublic")):
            with self.subTest(information=information):
                question_id, reply_id = f"q{index}", f"r{index}"
                self.harness.add_reply(self._reply(reply_id=reply_id, question_id=question_id,
                                                   information=information), now=datetime.fromisoformat(RECEIVED))
                evaluation = self.harness.evaluate_reply(self._evaluation(reply_id=reply_id),
                                                          now=EVALUATION_NOW)
                self.assertFalse(evaluation["applied"])
                self.assertEqual(evaluation["status"], "held_for_review")
                self.assertEqual(evaluation["action"], "unresolved")
                self.assertEqual(self.store.thesis("c1")["version"], 1)
                self.assertEqual(self.store.thesis("c1")["valuation"], valuation())
                with self.assertRaises(ValueError):
                    self.store.source(f"reply:{reply_id}")

    def test_public_but_unresolved_branch_preserves_valuation(self):
        self._sent_question()
        self.harness.add_reply(self._reply(), now=datetime.fromisoformat(RECEIVED))
        evaluation = self.harness.evaluate_reply(self._evaluation(branch="unclear"),
                                                  now=EVALUATION_NOW)
        self.assertFalse(evaluation["applied"])
        self.assertEqual(evaluation["status"], "unresolved")
        self.assertEqual(self.harness.status()["theses"], 1)
        self.assertEqual(self.store.thesis("c1")["valuation"], valuation())

    def test_invalid_quote_branch_and_evaluation_time_roll_back(self):
        self._sent_question()
        self.harness.add_reply(self._reply(), now=datetime.fromisoformat(RECEIVED))
        invalid_requests = [
            dict(self._evaluation(), basis_quote="価格改定効果は一時的です。"),
            self._evaluation(branch="not-a-frozen-branch"),
            dict(self._evaluation(), recorded_at="2026-10-10T04:09:00+00:00"),
            dict(self._evaluation(), next_review_date="2026-10-10"),
        ]
        no_next_review = self._evaluation()
        del no_next_review["next_review_date"]
        invalid_requests.append(no_next_review)
        before = self.harness.status()
        for request in invalid_requests:
            with self.subTest(request=request), self.assertRaises(ValueError):
                self.harness.evaluate_reply(request, now=EVALUATION_NOW)
            self.assertEqual(self.harness.status(), before)
            self.assertEqual(self.store.thesis("c1")["version"], 1)

    def test_stale_question_branch_cannot_be_rebased_by_changing_expected_version(self):
        self._sent_question()
        self.harness.add_reply(self._reply(), now=datetime.fromisoformat(RECEIVED))
        self.harness.ingest({"schema_version": 1, "theses": [
            thesis(version=2, eps="80", recorded=AS_OF),
        ]}, now=datetime.fromisoformat(RECEIVED) + timedelta(minutes=1))
        for expected in (1, 2):
            with self.subTest(expected=expected), self.assertRaisesRegex(ValueError, "Thesis changed"):
                self.harness.evaluate_reply(self._evaluation(version=expected), now=EVALUATION_NOW)
        self.assertEqual(self.harness.status()["evaluations"], 0)
        self.assertEqual(self.store.thesis("c1")["valuation"], valuation("80"))

    def test_evaluation_revision_requires_its_own_version_and_keeps_original_reply(self):
        self._sent_question()
        reply = self._reply(information="unclear")
        self.harness.add_reply(reply, now=datetime.fromisoformat(RECEIVED))
        first_request = self._evaluation()
        first = self.harness.evaluate_reply(first_request, now=EVALUATION_NOW)
        self.assertFalse(first["applied"])
        revised = dict(first_request, information_status="public_clarification",
                       rationale="原文と公開資料を再確認し、公開内容の補足として分類した。")
        with self.assertRaisesRegex(ValueError, "Stale evaluation version"):
            self.harness.evaluate_reply(revised, now=EVALUATION_NOW)
        revised["expected_evaluation_version"] = 1
        second = self.harness.evaluate_reply(revised, now=EVALUATION_NOW)
        self.assertEqual(second["version"], 2)
        self.assertTrue(second["applied"])
        self.assertEqual(self.harness.status()["evaluations"], 2)
        self.assertEqual(self.store.reply("r1"), reply)

    def test_evaluation_recorded_in_future_is_rejected_atomically(self):
        self._sent_question()
        self.harness.add_reply(self._reply(), now=datetime.fromisoformat(RECEIVED))
        before = self.harness.status()
        before_thesis = self.store.thesis("c1")
        with self.assertRaisesRegex(ValueError, "cannot be recorded in the future"):
            self.harness.evaluate_reply(self._evaluation(),
                                        now=EVALUATION_NOW - timedelta(minutes=6))
        self.assertEqual(self.harness.status(), before)
        self.assertEqual(self.store.thesis("c1"), before_thesis)
        with self.assertRaises(ValueError):
            self.store.source("reply:r1")

    def test_revised_evaluation_cannot_predate_previous_evaluation(self):
        self._sent_question()
        self.harness.add_reply(self._reply(information="unclear"), now=datetime.fromisoformat(RECEIVED))
        first_request = self._evaluation()
        first = self.harness.evaluate_reply(first_request, now=EVALUATION_NOW)
        self.assertFalse(first["applied"])
        revised = dict(
            first_request, expected_evaluation_version=1,
            recorded_at="2026-10-10T04:14:00+00:00",
            rationale="受信後だが前回評価より古い日時で再評価しようとする。",
        )
        before = self.harness.status()
        before_thesis = self.store.thesis("c1")
        with self.assertRaisesRegex(ValueError, "cannot predate the previous evaluation"):
            self.harness.evaluate_reply(revised, now=EVALUATION_NOW)
        self.assertEqual(self.harness.status(), before)
        self.assertEqual(self.store.thesis("c1"), before_thesis)
        self.assertEqual(self.harness.evaluate_reply(first_request, now=EVALUATION_NOW), first)


if __name__ == "__main__":
    unittest.main()
