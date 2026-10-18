"""Classification corrections are frozen, versioned research events."""
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
import unittest
from unittest.mock import patch

from ir_agent.information_review import add_assessment
from ir_agent.models import json_text
import test_decision_lifecycle as fixtures


def clock(value):
    return datetime.fromisoformat(value)


class InformationResearchTests(unittest.TestCase):
    def setUp(self):
        self.env = fixtures.DecisionLifecycleTests('runTest')
        self.env.setUp(); self.addCleanup(self.env.doCleanups)
        # Isolate the correction event from the demo's independent, unreviewed
        # disclosure. This fixture uses an in-memory database only.
        self.env.store.connection.execute("DELETE FROM sources WHERE id='demo-public-update'")
        self.env.receive()
        self.store = self.env.store; self.harness = self.env.harness
        self.harness.evaluate_reply(self.env.evaluation(self.env.fresh_quote()), now=fixtures.EVALUATED)
        self.original_reply = self.store.reply('demo-reply-cost')
        self.original_thesis = self.store.thesis('demo-services')

    def correct(self, version=0, status='potential_nonpublic', recorded='2026-10-09T18:05:00+09:00', saved=None):
        request = {'reply_id': 'demo-reply-cost', 'expected_version': version,
                   'information_status': status, 'basis_quote': self.original_reply['raw_text'][:15],
                   'rationale': 'Recheck the public basis without rewriting its original records.',
                   'recorded_at': recorded}
        return add_assessment(self.store, request, now=saved or recorded)

    def queue(self, stamp='2026-10-09T18:06:00+09:00'):
        return self.harness.daily(stamp, now=clock(stamp))

    def claim(self, stamp='2026-10-09T18:07:00+09:00'):
        return self.harness.claim('information-worker', now=clock(stamp))

    def result(self, job, recorded='2026-10-09T18:08:00+09:00'):
        thesis = deepcopy(job['packet']['thesis'])
        thesis.update(version=thesis['version'] + 1, recorded_at=recorded,
                      next_review_date='2026-10-30')
        return {'summary': 'Reviewed the frozen correction and retained an unresolved interpretation.',
                'evidence_ids': thesis['evidence_ids'], 'counterarguments': ['The public basis remains subject to verification.'],
                'proposed_action': 'unresolved', 'thesis_update': thesis,
                'information_review_refs': deepcopy(job['packet']['new_information_review_refs'])}

    def complete(self, job, result=None, now='2026-10-09T18:09:00+09:00'):
        return self.harness.complete(job['id'], 'information-worker', result or self.result(job), now=clock(now))

    def checked_count(self):
        return self.store.connection.execute('SELECT COUNT(*) FROM reply_information_research_checks').fetchone()[0]

    def test_correction_alone_queues_and_completion_checks_it_without_rewriting_history(self):
        self.assertEqual(self.queue()['selected'], [])
        correction = self.correct()
        selected = self.queue()['selected']
        self.assertEqual(selected[0]['reasons'], ['reply_information_corrected'])
        self.assertEqual(selected[0]['priority'], 150)
        self.assertEqual(self.queue()['selected'][0]['job_id'], selected[0]['job_id'])
        job = self.claim()
        self.assertEqual(job['packet']['information_reviews'], [correction])
        self.assertEqual(job['packet']['new_information_review_refs'], [{'reply_id': 'demo-reply-cost', 'version': 1}])
        result = self.result(job)
        completed = self.complete(job, result)
        self.assertEqual(completed['status'], 'completed')
        self.assertEqual(self.complete(job, result), completed)
        self.assertEqual(self.checked_count(), 1)
        self.assertEqual(self.queue('2026-10-09T18:10:00+09:00')['selected'], [])
        self.assertEqual(self.store.reply('demo-reply-cost'), self.original_reply)
        saved = self.store.connection.execute('SELECT data FROM theses WHERE company_id=? AND version=2', ('demo-services',)).fetchone()
        self.assertEqual(json.loads(saved['data']), self.original_thesis)

    def test_actual_save_time_controls_visibility_and_only_latest_unchecked_version_is_new(self):
        first = self.correct(recorded='2026-10-09T18:01:00+09:00', saved='2026-10-09T18:05:00+09:00')
        self.assertEqual(self.queue('2026-10-09T18:04:59+09:00')['selected'], [])
        second = self.correct(1, 'public_clarification', recorded='2026-10-09T18:06:00+09:00')
        selected = self.queue('2026-10-09T18:07:00+09:00')['selected']
        packet = self.store.job(selected[0]['job_id'])['packet']
        self.assertEqual(packet['information_reviews'], [first, second])
        self.assertEqual(packet['new_information_review_refs'], [{'reply_id': 'demo-reply-cost', 'version': 2}])

    def test_new_correction_during_lease_cannot_change_packet_or_be_marked_by_old_job(self):
        first = self.correct(); self.queue(); job = self.claim()
        second = self.correct(1, 'public_clarification', recorded='2026-10-09T18:10:00+09:00')
        pending = self.queue('2026-10-09T18:11:00+09:00')['selected'][0]['job_id']
        self.assertNotEqual(pending, job['id'])
        self.assertEqual(self.store.job(job['id'])['packet']['information_reviews'], [first])
        self.complete(job, self.result(job, '2026-10-09T18:12:00+09:00'), now='2026-10-09T18:12:00+09:00')
        latest = self.queue('2026-10-09T18:13:00+09:00')['selected'][0]['job_id']
        self.assertNotEqual(latest, pending)
        next_job = self.claim('2026-10-09T18:14:00+09:00')
        self.assertEqual(next_job['id'], latest)
        self.assertEqual(next_job['packet']['information_reviews'], [first, second])
        self.assertEqual(next_job['packet']['new_information_review_refs'][0]['version'], 2)
        self.assertEqual(self.checked_count(), 1)
        self.complete(next_job, self.result(next_job, '2026-10-09T18:15:00+09:00'), now='2026-10-09T18:16:00+09:00')
        self.assertIsNone(self.claim('2026-10-09T18:17:00+09:00'))
        self.assertEqual(self.store.job(pending)['status'], 'superseded')
        self.assertEqual(self.checked_count(), 2)
        self.assertEqual(self.queue('2026-10-09T18:18:00+09:00')['selected'], [])

    def test_missing_malformed_or_future_refs_cannot_complete_or_write_markers(self):
        self.correct(); self.queue(); job = self.claim()
        variants = [None, [], [{'reply_id': 'demo-reply-cost', 'version': 2}],
                    [{'reply_id': 'demo-reply-cost', 'version': True}],
                    [{'reply_id': 'demo-reply-cost', 'version': 1, 'ignore': True}],
                    [{'reply_id': 'demo-reply-cost', 'version': 1}] * 2]
        for references in variants:
            result = self.result(job); result['information_review_refs'] = references
            with self.subTest(references=references), self.assertRaises(ValueError):
                self.complete(job, result)
            self.assertEqual(self.store.thesis('demo-services')['version'], 2)
            self.assertEqual(self.store.job(job['id'])['status'], 'leased')
            self.assertEqual(self.checked_count(), 0)
        missing = self.result(job); missing.pop('information_review_refs')
        with self.assertRaisesRegex(ValueError, 'every new information correction'):
            self.complete(job, missing)

    def test_marker_error_rolls_back_thesis_job_and_all_markers(self):
        import ir_agent.information_review as information_review
        self.correct(); self.queue(); job = self.claim()
        record = information_review.record_research_checks
        def fail_after_write(store, job_id, references):
            record(store, job_id, references)
            raise ValueError('marker persistence failed')
        with patch.object(information_review, 'record_research_checks', side_effect=fail_after_write):
            with self.assertRaisesRegex(ValueError, 'marker persistence failed'):
                self.complete(job)
        self.assertEqual(self.store.thesis('demo-services')['version'], 2)
        self.assertEqual(self.store.job(job['id'])['status'], 'leased')
        self.assertEqual(self.checked_count(), 0)

    def test_original_source_dependency_is_followed_and_removed_dependency_stops_new_work(self):
        derived = deepcopy(self.store.source('reply:demo-reply-cost'))
        derived.update(id='derived-public-assumption', source_type='public_disclosure', requires_research=False)
        derived['metadata'] = {'original_source_id': 'reply:demo-reply-cost'}
        thesis = deepcopy(self.original_thesis)
        thesis.update(version=3, recorded_at='2026-10-09T17:30:00+09:00',
                      evidence_ids=['demo-public-q2', derived['id']])
        self.harness.ingest({'schema_version': 1, 'sources': [derived], 'theses': [thesis]},
                            now=clock('2026-10-09T18:01:00+09:00'))
        self.correct()
        pending = self.queue()['selected'][0]['job_id']
        self.assertEqual(self.store.job(pending)['packet']['new_information_review_refs'][0]['reply_id'], 'demo-reply-cost')
        thesis.update(version=4, recorded_at='2026-10-09T18:07:00+09:00', evidence_ids=['demo-public-q2'])
        self.harness.ingest({'schema_version': 1, 'theses': [thesis]}, now=clock('2026-10-09T18:07:00+09:00'))
        self.assertEqual(self.queue('2026-10-09T18:08:00+09:00')['selected'], [])
        self.assertIsNone(self.claim('2026-10-09T18:09:00+09:00'))
        self.assertEqual(self.store.job(pending)['status'], 'superseded')

    def test_inactive_company_is_not_queued_by_correction(self):
        self.correct()
        self.harness.set_company_status('demo-services', 'excluded', 'Outside active coverage')
        self.assertEqual(self.queue()['selected'], [])

    def test_jobs_without_new_corrections_keep_the_previous_identity(self):
        selected = self.queue('2026-10-30T10:00:00+09:00')['selected'][0]
        identity = {'company_id': 'demo-services', 'thesis_version': 2, 'new_source_ids': [], 'review_due': '2026-10-30'}
        expected = 'research-' + sha256(json_text(identity).encode()).hexdigest()[:24]
        self.assertEqual(selected['job_id'], expected)
        self.assertEqual(selected['reasons'], ['scheduled_review'])


if __name__ == '__main__': unittest.main()
