"""Later processing must not change the thesis known at an earlier instant."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import test_decision_lifecycle as fixtures
from ir_agent.harness import Harness
from ir_agent.models import timestamp
from ir_agent.store import Store


class HistoricalAvailabilityTests(unittest.TestCase):
    def environment(self):
        env = fixtures.DecisionLifecycleTests('runTest')
        env.setUp(); self.addCleanup(env.doCleanups)
        return env

    def test_late_reply_processing_keeps_past_thesis_and_daily_packet_unchanged(self):
        env = self.environment()
        env.save()
        env.harness.mark_sent(env.question['id'], '2026-10-09T10:05:00+09:00',
                              now=datetime.fromisoformat('2026-10-09T10:06:00+09:00'))
        boundary = timestamp('2026-10-09T17:30:00+09:00')
        before = env.store.thesis('demo-services', as_of=boundary, now=fixtures.EVALUATED)
        first_job = env.harness.daily(boundary.isoformat(), now=fixtures.EVALUATED)['selected'][0]['job_id']
        reply = json.loads((fixtures.ROOT / 'examples/reply.json').read_text())
        env.harness.add_reply(reply, now=fixtures.EVALUATED)
        quote = env.fresh_quote('1000', '2026-10-09T17:15:00+09:00', 'late-arrival')
        request = env.evaluation(quote); request['recorded_at'] = '2026-10-09T17:20:00+09:00'
        applied = env.harness.evaluate_reply(request, now=fixtures.EVALUATED)
        after = env.store.thesis('demo-services', as_of=boundary, now=fixtures.EVALUATED)
        last_job = env.harness.daily(boundary.isoformat(), now=fixtures.EVALUATED)['selected'][0]['job_id']
        self.assertEqual(before, after); self.assertEqual(after['version'], 1)
        self.assertEqual(first_job, last_job)
        self.assertEqual(env.store.thesis('demo-services')['version'], 2)
        review = applied['decision_review']
        saved = env.store.connection.execute('SELECT first_saved_at FROM decision_reviews WHERE id=?', (review['id'],)).fetchone()[0]
        self.assertEqual(timestamp(saved), fixtures.EVALUATED)
        retrospective = env.store.thesis_view('demo-services', as_of=boundary,
            knowledge_at=fixtures.EVALUATED, mode='retrospective', now=fixtures.EVALUATED)
        self.assertEqual(retrospective['record']['version'], 2)
        self.assertEqual(retrospective['temporal_mode'], 'retrospective')
        with self.assertRaisesRegex(ValueError, 'PIT requires equal'):
            env.store.thesis_view('demo-services', as_of=boundary, knowledge_at=fixtures.EVALUATED,
                                  mode='pit', now=fixtures.EVALUATED)

    def test_late_disclosure_is_not_in_a_pre_arrival_packet(self):
        env = self.environment()
        boundary = datetime.fromisoformat('2026-10-09T17:30:00+09:00')
        new = deepcopy(env.store.source('demo-public-q2'))
        new.update(id='late-public-disclosure', published_at='2026-10-09T16:00:00+09:00',
                   retrieved_at='2026-10-09T16:05:00+09:00')
        env.harness.ingest({'schema_version': 1, 'sources': [new]}, now=fixtures.EVALUATED)
        outcome = env.harness.daily(boundary.isoformat(), now=fixtures.EVALUATED)
        packet = env.store.job(outcome['selected'][0]['job_id'])['packet']
        self.assertNotIn(new['id'], [source['id'] for source in packet['sources']])
        self.assertFalse(env.store.source_available(env.store.source(new['id']), as_of=boundary, now=fixtures.EVALUATED))
        self.assertTrue(env.store.source_available(env.store.source(new['id']), as_of=fixtures.EVALUATED, now=fixtures.EVALUATED))

    def test_missing_parent_receipt_holds_a_derived_source_and_its_thesis(self):
        env = self.environment()
        parent = env.store.source('demo-public-q2')
        derived = deepcopy(parent); derived['id'] = 'derived-fact'
        derived['metadata']['original_source_ids'] = [parent['id']]
        thesis = deepcopy(env.store.thesis('demo-services'))
        thesis.update(version=2, recorded_at=fixtures.SAVED.isoformat(), evidence_ids=[derived['id']])
        env.harness.ingest({'schema_version': 1, 'sources': [derived], 'theses': [thesis]}, now=fixtures.SAVED)
        env.store.connection.execute("DELETE FROM record_availability WHERE entity_type='source' AND entity_id=?", (parent['id'],))
        check = env.store.source_availability(env.store.source(derived['id']), as_of=fixtures.EVALUATED, now=fixtures.EVALUATED)
        self.assertIsNone(check['available'])
        self.assertIn('availability_receipt_missing', check['reason_codes'])
        view = env.store.thesis_view('demo-services', as_of=fixtures.EVALUATED,
                                    knowledge_at=fixtures.EVALUATED, mode='pit', now=fixtures.EVALUATED)
        self.assertIsNone(view['record'])
        self.assertEqual(view['availability_status'], 'unknown')
        self.assertEqual(env.store.thesis('demo-services')['version'], 2)

    def test_source_and_thesis_receipt_failures_roll_back_base_inserts(self):
        for kind in ('source', 'thesis'):
            with self.subTest(kind=kind):
                env = self.environment()
                env.store.connection.execute("CREATE TRIGGER reject_presence BEFORE INSERT ON record_availability "
                    "WHEN NEW.entity_type='" + kind + "' BEGIN SELECT RAISE(ABORT,'injected receipt failure'); END")
                if kind == 'source':
                    value = deepcopy(env.store.source('demo-public-q2')); value['id'] = 'rollback-source'
                    bundle = {'schema_version': 1, 'sources': [value]}
                else:
                    value = deepcopy(env.store.thesis('demo-services')); value['version'] = 2
                    bundle = {'schema_version': 1, 'theses': [value]}
                with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected receipt failure'):
                    env.harness.ingest(bundle, now=fixtures.SAVED)
                if kind == 'source':
                    with self.assertRaisesRegex(ValueError, 'Unknown source'): env.store.source(value['id'])
                else: self.assertEqual(env.store.thesis('demo-services')['version'], 1)

    def test_legacy_presence_keeps_json_and_old_unknown_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'legacy.sqlite3'
            old = Store(path)
            Harness(old).ingest(json.loads((fixtures.ROOT / 'examples/demo.json').read_text()), now=fixtures.CREATED)
            snapshots = {row['id']: row['data'] for row in old.connection.execute('SELECT id,data FROM sources')}
            old.connection.execute('DROP TABLE record_availability'); old.close()
            with patch('ir_agent.store.now_iso', return_value=fixtures.EVALUATED.isoformat()):
                migrated = Store(path)
            self.addCleanup(migrated.close)
            self.assertEqual({row['id']: row['data'] for row in migrated.connection.execute('SELECT id,data FROM sources')}, snapshots)
            earlier = migrated.thesis_view('demo-services', as_of=fixtures.CREATED,
                                           knowledge_at=fixtures.CREATED, mode='pit', now=fixtures.EVALUATED)
            self.assertIsNone(earlier['record']); self.assertEqual(earlier['availability_status'], 'unknown')
            current = migrated.thesis_view('demo-services', as_of=fixtures.EVALUATED,
                                           knowledge_at=fixtures.EVALUATED, mode='pit', now=fixtures.EVALUATED)
            self.assertEqual(current['record']['version'], 1)
            self.assertFalse(current['selected_availability']['thesis']['first_save_known'])
            self.assertIsNone(current['selected_availability']['thesis']['receipt']['first_saved_at'])


if __name__ == '__main__':
    unittest.main()
