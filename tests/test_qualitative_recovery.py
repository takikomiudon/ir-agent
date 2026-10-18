"""Temporary evidence holds must not permanently suppress a review trigger."""
from copy import deepcopy
import json
import unittest

from ir_agent.models import json_text
import test_qualitative_research_integration as fixtures


class QualitativeRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.QualitativeIntegrationTests(
            'test_changed_file_supersedes_unclaimed_packet')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.f.register()
        self.path = self.f.root / 'case.json'
        self.original = self.path.read_text()

    def supersede(self, queue_minute, claim_minute):
        queued = self.f.queue(queue_minute)
        identity = queued['selected'][0]['job_id']
        self.path.write_text('Temporary evidence change')
        self.assertIsNone(self.f.claim(claim_minute))
        saved = deepcopy(self.f.store.job(identity))
        self.assertEqual(saved['status'], 'superseded')
        self.path.write_text(self.original)
        return saved

    def test_restoration_gets_fresh_packet_once_and_preserves_superseded_job(self):
        old = self.supersede(4, 5)
        recovered = self.f.queue(6)
        self.assertEqual(recovered['jobs_created'], 1)
        identity = recovered['selected'][0]['job_id']
        self.assertNotEqual(identity, old['id'])
        fresh = self.f.store.job(identity)
        self.assertEqual(fresh['packet']['supersedes_job_id'], old['id'])
        self.assertEqual(fresh['packet']['as_of'], fixtures.at(6).isoformat())
        self.assertEqual(self.f.queue(7)['jobs_created'], 0)
        claimed = self.f.claim(8)
        self.assertEqual(claimed['id'], identity)
        self.assertEqual(self.f.queue(8)['jobs_created'], 0)
        self.f.complete(claimed, self.f.result(claimed, 9), minute=9)
        self.assertEqual(self.f.registry.show_case('orders-case')['version'], 2)
        self.assertEqual(self.f.queue(10)['jobs_created'], 0)
        self.assertEqual(self.f.store.job(old['id']), old)
        self.assertEqual(self.f.store.connection.execute('select count(*) from theses').fetchone()[0], 0)

    def test_repeated_hold_recovery_walks_chain_without_reviving_old_jobs(self):
        first = self.supersede(4, 5)
        second = self.supersede(6, 7)
        self.assertNotEqual(first['id'], second['id'])
        self.assertEqual(second['packet']['supersedes_job_id'], first['id'])
        third = self.f.queue(8)
        self.assertEqual(third['jobs_created'], 1)
        identity = third['selected'][0]['job_id']
        self.assertEqual(self.f.store.job(identity)['packet']['supersedes_job_id'], second['id'])
        self.assertEqual(self.f.queue(9)['jobs_created'], 0)
        self.assertEqual(self.f.store.job(first['id']), first)
        self.assertEqual(self.f.store.job(second['id']), second)

    def test_recovery_keeps_case_and_source_holds_in_force(self):
        old = self.supersede(4, 5)
        self.path.write_text('Still changed')
        held = self.f.queue(6)
        self.assertEqual(held['jobs_created'], 0)
        self.assertEqual(held['skipped'][0]['reason'], 'case_file_changed')
        self.path.write_text(self.original)
        row = self.f.store.connection.execute(
            "select data from source_classifications where source_id='A'").fetchone()
        original = row['data']; changed = json.loads(original)
        changed['kind'] = 'unresolved'
        self.f.store.connection.execute(
            "update source_classifications set data=? where source_id='A'", (json_text(changed),))
        held = self.f.queue(7)
        self.assertEqual(held['jobs_created'], 0)
        self.assertEqual(held['skipped'][0]['reason'], 'source_evidence_held')
        self.f.store.connection.execute(
            "update source_classifications set data=? where source_id='A'", (original,))
        self.assertEqual(self.f.queue(8)['jobs_created'], 1)
        self.assertEqual(self.f.store.job(old['id']), old)

    def test_recovery_does_not_reuse_a_previously_leased_job_or_its_attempt(self):
        self.f.queue(4)
        old = self.f.claim(5, lease=1)
        self.path.write_text('Temporary evidence change')
        self.assertIsNone(self.f.claim(6))
        ended = deepcopy(self.f.store.job(old['id']))
        self.assertEqual(ended['status'], 'superseded')
        self.path.write_text(self.original)
        self.assertEqual(self.f.queue(7)['jobs_created'], 1)
        fresh = self.f.claim(8)
        self.assertNotEqual(fresh['id'], old['id'])
        self.assertEqual(fresh['attempts'], 1)
        with self.assertRaises(ValueError):
            self.f.complete(old, self.f.result(old, 9), minute=9)
        self.f.complete(fresh, self.f.result(fresh, 9), minute=9)
        self.assertEqual(self.f.store.job(old['id']), ended)


if __name__ == '__main__':
    unittest.main()
