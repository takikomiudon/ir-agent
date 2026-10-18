"""Repeated scheduler admissions count new jobs, without changing legacy mode."""
from datetime import datetime, timezone
import unittest
from ir_agent.cli import parser, run
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.store import Store
from test_workflow import source, thesis

NOW = datetime(2026, 10, 10, 3, tzinfo=timezone.utc)

class NewOnlyQueuesTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(':memory:'); self.addCleanup(self.store.close)
        self.harness = Harness(self.store); self.intake = Intake(self.store)
        for identity in ('a','b','c'):
            self.harness.ingest({'schema_version':1,
                'companies':[{'id':identity,'name':'Synthetic '+identity,'status':'active'}],
                'sources':[source(identity, identity+'-baseline'),source(identity,identity+'-new')],
                'theses':[thesis(identity)]}, now=datetime(2026,10,1,1,tzinfo=timezone.utc))

    def admission(self, kind, *, new_only=False):
        if kind == 'daily':
            return self.harness.daily(NOW.isoformat(), limit=1, now=NOW, new_only=new_only)
        return self.intake.queue(NOW.isoformat(), limit=1, now=NOW, new_only=new_only)

    def test_daily_and_intake_skip_existing_before_applying_limit(self):
        for kind in ('daily','intake'):
            with self.subTest(kind=kind):
                first=self.admission(kind); original=self.store.job(first['selected'][0]['job_id'])
                self.assertEqual(first['deferred_count'],2)
                legacy=self.admission(kind)
                self.assertEqual(legacy['selected'][0]['job_id'],original['id'])
                self.assertNotIn('new_only',legacy)
                second=self.admission(kind,new_only=True)
                self.assertEqual(second['jobs_created'],1)
                self.assertEqual(second['selected'][0]['company_id'],'b')
                self.assertEqual(second['deferred_count'],1)
                self.assertEqual(len(second['skipped']),1)
                third=self.admission(kind,new_only=True)
                self.assertEqual(third['selected'][0]['company_id'],'c')
                self.assertEqual(third['deferred_count'],0)
                empty=self.admission(kind,new_only=True)
                self.assertEqual(empty['jobs_created'],0)
                self.assertEqual(empty['deferred_count'],0)
                self.assertEqual(len(empty['skipped']),3)
                self.assertEqual(self.store.job(original['id']),original)

    def test_both_CLI_flags_dispatch_to_new_only_admission(self):
        for kind in ('daily','intake'):
            with self.subTest(kind=kind):
                arguments=[kind,'--as-of',NOW.isoformat(),'--limit','1','--new-only']
                first=run(parser().parse_args(arguments),self.store)
                second=run(parser().parse_args(arguments),self.store)
                self.assertTrue(first['new_only']);self.assertEqual(first['jobs_created'],1)
                self.assertEqual(second['selected'][0]['company_id'],'b')
                self.assertNotEqual(first['selected'][0]['job_id'],second['selected'][0]['job_id'])

    def test_non_boolean_modes_fail_without_queue_writes(self):
        for kind in ('daily','intake'):
            for invalid in (1,'true',None):
                with self.subTest(kind=kind,value=invalid),self.assertRaises(ValueError):
                    self.admission(kind,new_only=invalid)
        self.assertEqual(self.store.connection.execute('SELECT count(*) FROM jobs').fetchone()[0],0)

if __name__=='__main__': unittest.main()
