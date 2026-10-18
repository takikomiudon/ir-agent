"""Bounded offline claim/renew receipt recheck against fictional temporary DBs.

This script changes only its own TemporaryDirectory SQLite files and /tmp JSON.
It does not run analysis, send IR, place orders, contact a network or alter the
repository's sources/tests/docs or an actual research database.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

REPO = Path('/workspace/ir-agent')
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'tests')]
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.store import Store
from test_intake import source

BASE = datetime.fromisoformat('2026-10-09T10:01:00+09:00')
NAMESPACE = 'synthetic-request-recheck'


def stamp(seconds=0):
    return BASE + timedelta(seconds=seconds)


def snapshot(db):
    return {'dump': list(db.iterdump()), 'total_changes': db.total_changes}


def readonly(db, call):
    before = snapshot(db)
    result = call()
    assert snapshot(db) == before, 'Replay/read unexpectedly mutated DB'
    return result


def seed(store, company='no-model', suffix='a', now=None):
    harness = Harness(store)
    saved = now or datetime.fromisoformat('2026-10-09T09:55:00+09:00')
    document = source(company + '-doc-' + suffix, content='Fictional public source for request receipt recheck.')
    document['company_id'] = company
    harness.ingest({'schema_version': 1, 'companies': [{'id': company, 'name': 'Fictional ' + company}],
                    'sources': [document]}, now=saved)
    return harness


def claim(harness, request_id, seconds=0, *, worker='same-worker', lease=30, synthetic=True, namespace=NAMESPACE):
    return harness.claim(worker, lease, now=stamp(seconds), measurement_synthetic=synthetic,
                         request_id=request_id, caller_namespace=namespace)


def renew(harness, job_id, generation, request_id, seconds, *, worker='same-worker', lease=40):
    return harness.renew(job_id, worker, lease, expected_attempt=generation, now=stamp(seconds),
                         request_id=request_id, caller_namespace=NAMESPACE)


def lost_ack_workflow(path):
    store = Store(path)
    try:
        harness = seed(store)
        Intake(store).queue('2026-10-09T10:00:00+09:00', now=datetime.fromisoformat('2026-10-09T10:00:00+09:00'))
        first = claim(harness, 'poll-1')
        original = first['original_response']
        job_id, generation = original['job_id'], original['generation']
        assert generation == 1 and not first['replayed']
        replay = readonly(store.connection, lambda: claim(harness, 'poll-1', 1))
        assert replay['replayed'] and replay['original_response'] == original
        assert replay['current_lease']['valid_now'] is True
        assert store.job(job_id)['attempts'] == 1

        renewed = renew(harness, job_id, generation, 'extend-1', 5)
        original_renewal = renewed['original_response']
        renewal_retry = readonly(store.connection, lambda: renew(harness, job_id, generation, 'extend-1', 7))
        assert renewal_retry['replayed'] and renewal_retry['original_response'] == original_renewal
        assert store.job(job_id)['lease_until'] == stamp(45).astimezone(timezone.utc).isoformat()
        # A later, distinct extension does not replace the earlier response.
        newer = renew(harness, job_id, generation, 'extend-2', 8, lease=50)
        old_renewal = readonly(store.connection, lambda: renew(harness, job_id, generation, 'extend-1', 9))
        assert old_renewal['original_response'] == original_renewal
        assert old_renewal['current_lease']['lease_until'] == newer['original_response']['lease_until']
        assert old_renewal['original_response']['lease_until'] != old_renewal['current_lease']['lease_until']
        # Claim replay after renew also retains its original deadline.
        old_claim = readonly(store.connection, lambda: claim(harness, 'poll-1', 10))
        assert old_claim['original_response'] == original
        assert old_claim['current_lease']['lease_until'] == newer['original_response']['lease_until']

        mismatches = [
            lambda: claim(harness, 'poll-1', 11, worker='another-worker'),
            lambda: claim(harness, 'poll-1', 11, lease=31),
            lambda: claim(harness, 'poll-1', 11, synthetic=None),
            lambda: renew(harness, job_id, generation, 'poll-1', 11),
            lambda: renew(harness, job_id, generation + 1, 'extend-1', 11),
            lambda: renew(harness, job_id, generation, 'extend-1', 11, lease=41),
        ]
        for call in mismatches:
            before = snapshot(store.connection)
            try:
                call()
            except ValueError as error:
                assert 'different semantic payload' in str(error)
            else:
                raise AssertionError('Reused ID with changed payload must be rejected')
            assert snapshot(store.connection) == before

        expired_claim = readonly(store.connection, lambda: claim(harness, 'poll-1', 60))
        expired_renewal = readonly(store.connection, lambda: renew(harness, job_id, generation, 'extend-1', 60))
        for value in (expired_claim, expired_renewal):
            assert value['current_lease']['status'] == 'expired'
            assert value['current_lease']['valid_now'] is False
        # Replay does not perform expiry cleanup or add an expiry event.
        assert store.job(job_id)['status'] == 'leased'
        reclaimed = claim(harness, 'poll-2', 61)
        assert reclaimed['original_response']['job_id'] == job_id
        assert reclaimed['original_response']['generation'] == 2
        stale_claim = readonly(store.connection, lambda: claim(harness, 'poll-1', 62))
        stale_renewal = readonly(store.connection, lambda: renew(harness, job_id, generation, 'extend-1', 62))
        for value, saved in ((stale_claim, original), (stale_renewal, original_renewal)):
            assert value['original_response'] == saved
            assert value['current_lease']['status'] == 'reclaimed'
            assert value['current_lease']['valid_now'] is False

        empty = claim(harness, 'empty-poll', 63)
        assert empty['original_response'] is None and empty['current_lease'] is None
        seed(store, company='second-company', now=stamp(64))
        queued = Intake(store).queue(stamp(64).isoformat(), company_id='second-company', now=stamp(64))
        pending_id = queued['selected'][0]['job_id']
        empty_retry = readonly(store.connection, lambda: claim(harness, 'empty-poll', 65))
        assert empty_retry['replayed'] and empty_retry['original_response'] is None
        assert store.job(pending_id)['status'] == 'pending'
        new_poll = claim(harness, 'next-poll', 66)
        assert new_poll['original_response']['job_id'] == pending_id
        assert not new_poll['replayed']
        # Namespace is an ID scope, not an authenticated identity.
        independent = claim(harness, 'empty-poll', 67, namespace='independent-synthetic-caller')
        assert not independent['replayed'] and independent['original_response'] is None
        return {'claim_original_preserved': True, 'claim_retry_no_db_write': True,
                'renew_original_preserved': True, 'renew_retry_no_db_write': True,
                'later_renew_current_deadline_separate': True, 'mismatched_payloads_rejected': len(mismatches),
                'expired_claim_and_renew_valid_now': False, 'expired_replay_no_cleanup': True,
                'reclaimed_generation': reclaimed['original_response']['generation'],
                'reclaimed_old_claim_and_renew_valid_now': False, 'stale_replay_no_db_write': True,
                'no_job_retry_fixed_null': True, 'new_poll_claimed_new_job': True,
                'different_namespace_is_separate_scope': True}
    finally:
        store.close()


def writer_clock(path):
    store = Store(path)
    try:
        harness = seed(store)
        Intake(store).queue('2026-10-09T10:00:00+09:00', now=datetime.fromisoformat('2026-10-09T10:00:00+09:00'))
        real_writer = store._record_write
        inside_writer = False
        sampled = []
        @contextmanager
        def instrumented_writer():
            nonlocal inside_writer
            with real_writer():
                assert store.connection.in_transaction
                inside_writer = True
                try:
                    yield
                finally:
                    inside_writer = False
        def runtime_sample(*_):
            assert inside_writer, 'Runtime clock sampled before writer acquisition'
            sampled.append(grant_time.isoformat())
            return grant_time
        with patch.object(store, '_record_write', instrumented_writer), \
             patch('ir_agent.harness.datetime', wraps=datetime) as runtime:
            runtime.now.side_effect = runtime_sample
            grant_time = stamp(120)
            first = harness.claim('clock-worker', 30, measurement_synthetic=True,
                request_id='clock-claim', caller_namespace=NAMESPACE)
            assert first['original_response']['lease_until'] == (grant_time + timedelta(seconds=30)).astimezone(timezone.utc).isoformat()
            grant_time = stamp(125)
            second = harness.renew(first['original_response']['job_id'], 'clock-worker', 30,
                expected_attempt=first['original_response']['generation'],
                request_id='clock-renew', caller_namespace=NAMESPACE)
            assert second['original_response']['lease_until'] == (grant_time + timedelta(seconds=30)).astimezone(timezone.utc).isoformat()
        assert len(sampled) == 2
        return {'claim_and_renew_sample_inside_acquired_writer': True, 'runtime_samples': sampled,
                'method': 'Instrumented real BEGIN IMMEDIATE transaction; no contention-load benchmark.'}
    finally:
        store.close()


def main():
    with tempfile.TemporaryDirectory(prefix='ir-job-requests-recheck-') as folder:
        directory = Path(folder)
        report = {'all_inputs_fictional': True, 'database_scope': 'two disposable TemporaryDirectory SQLite files',
                  'lost_acknowledgement': lost_ack_workflow(directory / 'requests.sqlite3'),
                  'runtime_clock': writer_clock(directory / 'clock.sqlite3'),
                  'limits': ['Same receipt is not exactly-once model analysis or authentication.',
                             'No silent restore-loss detection or deletion/TTL protocol is established.',
                             'Current lease is a read-time check; renew/complete still require fencing.',
                             'No network, real database, repository source/test/doc modification, IR or orders.']}
    Path('/tmp/ir_job_requests_recheck.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
