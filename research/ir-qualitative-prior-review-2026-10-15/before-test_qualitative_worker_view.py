"""Worker projection preserves frozen evidence and cannot authorize completion."""
from copy import deepcopy
from hashlib import sha256
import unittest
from ir_agent.cli import parser, run
from ir_agent.models import json_text
import test_qualitative_research_integration as fixtures

class WorkerViewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.QualitativeIntegrationTests('test_watch_without_thesis_queues_once_completes_and_never_writes_financial_records')
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.f = self.fixture
        self.f.register(); self.f.queue(); self.job = self.f.claim()

    def test_view_retains_full_case_and_pending_sources_without_mutating_job(self):
        original = deepcopy(self.f.store.job(self.job['id'])); packet = original['packet']
        view = self.f.registry.worker_packet(self.job['id'])
        self.assertEqual(view['canonical_packet_sha256'],sha256(json_text(packet).encode()).hexdigest())
        self.assertEqual(view['sources'],packet['sources'])
        self.assertEqual(view['source_snapshot_sha256'],packet['source_snapshot_sha256'])
        self.assertEqual(view['frozen_case_document'],packet['case_snapshot']['files']['case_ref'])
        self.assertEqual(view['case_context']['issue_id'],packet['case_snapshot']['issue_id'])
        self.assertEqual(view['current_completion_authorization'],'not_checked')
        view['sources'][0]['content']='modified view'
        self.assertEqual(self.f.store.job(self.job['id']),original)

    def test_CLI_full_default_and_opt_in_worker_view(self):
        full=run(parser().parse_args(['packet',self.job['id']]),self.f.store)
        view=run(parser().parse_args(['packet',self.job['id'],'--view','qualitative-worker']),self.f.store)
        self.assertEqual(full,self.job['packet'])
        self.assertEqual(view,self.f.registry.worker_packet(self.job['id']))
        self.assertNotIn('case_snapshot',view)
        self.assertEqual(view['reference_files']['manifest_ref'],self.f.request['manifest_ref'])

    def test_historical_view_keeps_frozen_case_even_after_progress_and_file_change(self):
        before=self.f.registry.worker_packet(self.job['id']);self.f.complete(self.job)
        (self.f.root/'case.json').write_text('Changed live file')
        after=self.f.registry.worker_packet(self.job['id'])
        self.assertEqual(after['canonical_packet_sha256'],before['canonical_packet_sha256'])
        self.assertEqual(after['frozen_case_document'],before['frozen_case_document'])
        self.assertEqual(after['job_status'],'completed')
        self.assertEqual(after['current_completion_authorization'],'not_checked')

    def test_intake_job_is_rejected_instead_of_falling_through(self):
        identity=self.f.store.connection.execute("select id from jobs where packet like '%source_classification%' limit 1").fetchone()[0]
        with self.assertRaisesRegex(ValueError,'requires a qualitative'):
            self.f.registry.worker_packet(identity)

    def test_bootstrap_proof_text_is_omitted_but_all_bindings_are_retained(self):
        self.f.complete(self.job)
        saved=self.f.store.source('A');digest=sha256(json_text(saved).encode()).hexdigest()
        reference=self.f.file('bootstrap.json','A '+digest+' '+('Proof text. '*100))
        request=deepcopy(self.f.request)
        request['bootstrap_reviews']=[{'source_id':'A','source_snapshot_sha256':digest,
            'reviewed_at':fixtures.at(6).isoformat(),'review_ref':reference}]
        self.f.registry.register_case(request,2,research_root=self.f.root,now=fixtures.at(7))
        self.f.add_source('B',8);self.f.queue(9);job=self.f.claim(10)
        view=self.f.registry.worker_packet(job['id'])
        self.assertNotIn('review_file',view['reviewed_sources']['A'])
        self.assertEqual(view['reviewed_sources']['A']['source_snapshot_sha256'],digest)
        self.assertEqual(view['reviewed_sources']['A']['review_ref'],reference)
        self.assertEqual(view['reference_files']['bootstrap:A'],reference)
        self.assertEqual(view['pending_source_ids'],['B'])

if __name__=='__main__':unittest.main()
