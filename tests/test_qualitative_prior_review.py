"""Successive reviews carry observations without rewriting the original case."""
from copy import deepcopy
from hashlib import sha256
import json
import unittest
from ir_agent.models import json_text
import test_qualitative_research_integration as fixtures

class PriorReviewTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.QualitativeIntegrationTests('test_watch_without_thesis_queues_once_completes_and_never_writes_financial_records')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.f.register();self.f.queue();self.first=self.f.claim();self.saved=self.f.complete(self.first)
        self.f.add_source('B',7)

    def test_next_packet_freezes_observation_but_keeps_original_case_and_only_new_source(self):
        self.f.queue(8);job=self.f.claim(9);packet=job['packet'];prior=packet['prior_review']
        self.assertEqual(packet['pending_source_ids'],['B'])
        self.assertEqual(prior['job_id'],self.first['id'])
        self.assertEqual(prior['case_observation'],self.saved['result']['request']['case_observation'])
        self.assertEqual(prior['result_sha256'],sha256(json_text(self.saved['result']).encode()).hexdigest())
        self.assertEqual(prior['source_snapshot_sha256'],self.first['packet']['source_snapshot_sha256'])
        self.assertEqual(packet['case_snapshot']['files']['case_ref'],self.first['packet']['case_snapshot']['files']['case_ref'])
        view=self.f.registry.worker_packet(job['id'])
        self.assertEqual(view['prior_review'],prior)
        self.assertEqual(view['prior_review_availability'],'frozen')
        self.f.complete(job,self.f.result(job,10),minute=10)
        self.assertEqual(self.f.registry.show_case('orders-case')['version'],3)
        self.assertEqual(self.f.store.connection.execute('select count(*) from theses').fetchone()[0],0)

    def test_changed_prior_result_fences_claim_but_frozen_view_stays_unchanged(self):
        self.f.queue(8);row=self.f.store.connection.execute("select id from jobs where status='pending'").fetchone()
        before=self.f.registry.worker_packet(row['id']);modified=deepcopy(self.saved['result'])
        modified['request']['summary']='changed historical observation'
        self.f.store.connection.execute('update jobs set result=? where id=?',(json_text(modified),self.first['id']))
        self.assertEqual(self.f.registry.worker_packet(row['id']),before)
        self.assertIsNone(self.f.claim(9))
        self.assertEqual(self.f.store.job(row['id'])['status'],'superseded')

    def test_bad_prior_reference_holds_only_that_case_and_does_not_block_another(self):
        row=self.f.registry._row('orders-case');record=json.loads(row['data'])
        intake=self.f.store.connection.execute("select id from jobs where packet like '%source_classification%' limit 1").fetchone()[0]
        record['last_review_id']=intake
        self.f.store.connection.execute('update qualitative_case_versions set data=? where case_id=? and version=?',
            (json_text(record),'orders-case',2))
        second=deepcopy(self.f.request);second.update(case_id='second-case',issue_id='other-issue',recorded_at=fixtures.at(8).isoformat())
        self.f.registry.register_case(second,research_root=self.f.root,now=fixtures.at(8))
        result=self.f.registry.queue_cases(['orders-case','second-case'],fixtures.at(9).isoformat(),now=fixtures.at(9))
        self.assertEqual(result['jobs_created'],1)
        self.assertEqual(result['selected'][0]['case_id'],'second-case')
        self.assertEqual(result['skipped'][0]['reason'],'prior_review_evidence_held')

    def test_legacy_packet_does_not_reconstruct_an_observation_from_live_state(self):
        self.f.queue(8);row=self.f.store.connection.execute("select id,packet from jobs where status='pending'").fetchone()
        packet=json.loads(row['packet']);packet.pop('prior_review')
        self.f.store.connection.execute('update jobs set packet=? where id=?',(json_text(packet),row['id']))
        view=self.f.registry.worker_packet(row['id'])
        self.assertIsNone(view['prior_review'])
        self.assertEqual(view['prior_review_availability'],'not_in_legacy_packet')
        job=self.f.claim(9);self.assertEqual(job['id'],row['id'])
        self.f.complete(job,self.f.result(job,10),minute=10)

if __name__=='__main__':unittest.main()
