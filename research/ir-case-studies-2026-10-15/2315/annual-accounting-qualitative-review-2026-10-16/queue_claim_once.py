"""Root-only queue/claim of the newly saved annual report; never replay blindly."""
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sqlite3

from ir_agent.harness import Harness
from ir_agent.models import json_text
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.store import Store

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED = '2e7942f370600decb2fc7f49eb681ca5e6841aa9b40b3b96722f04f8f4382540'
CASE = '2315-profit-perimeter-financial-definition-and-share-basis-monitor'
SOURCE = 'case-public:2dc3cd6dce430a43a4fd8ae58f2ddc37e94cee90d08b4c32e5e49f0df1f0b112'
WORKER = 'codex-2315-annual-accounting-qualitative'
SPEC = importlib.util.spec_from_file_location('readonly_checks', ROOT / 'research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/actual-connection/shadow_preflight.py')
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)


def clock():
    return datetime.now(timezone.utc)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x', encoding='utf8') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        output.flush()
        os.fsync(output.fileno())


def main():
    assert not (HERE / 'queue-claim-stage.jsonl').exists()
    assert digest(DB) == EXPECTED
    code_file = ROOT / 'research/ir-2315-annual-accounting-intake-2026-10-16/prepared-code-pins.json'
    assert digest(code_file) == '9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60'
    for path, expected in json.loads(code_file.read_bytes()).items():
        assert digest(ROOT / path) == expected
    backup = ROOT / 'data/backups/ir-research-before-2315-annual-qualitative-2026-10-16.sqlite3'
    assert not backup.exists()
    with closing(CHECKS.readonly()) as original:
        before, schema = CHECKS.snapshot(original), CHECKS.schema(original)
        assert CHECKS.state(original) == {'current_cases': 24, 'reviewed_sources': 141}
        assert original.execute("SELECT COUNT(*) FROM jobs WHERE status!='completed'").fetchone()[0] == 0
        assert original.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] == 111
        with closing(sqlite3.connect(backup)) as copied:
            original.backup(copied)
            assert CHECKS.snapshot(copied) == before and CHECKS.schema(copied) == schema
    store = None
    with (HERE / 'queue-claim-stage.jsonl').open('x', encoding='utf8') as journal:
        def event(operation, phase, value):
            journal.write(json.dumps({'recorded_at': clock().isoformat(), 'operation': operation,
                                      'phase': phase, 'value': value}, ensure_ascii=False) + '\n')
            journal.flush()
            os.fsync(journal.fileno())
        try:
            event('baseline_backup', 'succeeded', {'backup_file': str(backup), 'SHA': digest(backup)})
            store = Store(str(DB))
            assert CHECKS.snapshot(store.connection) == before and CHECKS.schema(store.connection) == schema
            now = clock()
            event('queue', 'begin', {'case_id': CASE, 'as_of': now.isoformat()})
            queued = QualitativeResearch(store).queue_cases([CASE], now.isoformat(), now=now)
            event('queue', 'succeeded', queued)
            assert queued['jobs_created'] == 1 and len(queued['selected']) == 1 and not queued['skipped']
            job_id = queued['selected'][0]['job_id']
            packet = store.job(job_id)['packet']
            assert packet['kind'] == 'qualitative_review' and packet['stage'] == 'author_condition_review'
            assert packet['pending_source_ids'] == [SOURCE] and len(packet['sources']) == 1
            assert packet['head_version'] == packet['config_revision'] == 1
            save('job-packet.json', packet)
            event('claim', 'begin', {'worker': WORKER, 'lease_seconds': 1800})
            claimed = Harness(store).claim(WORKER, lease_seconds=1800, now=clock(), measurement_synthetic=False,
                                           caller_namespace=WORKER, request_id='2315-annual-qualitative-20261016-1')
            event('claim', 'succeeded', claimed)
            assert not claimed['replayed']
            assert claimed['original_response']['job_id'] == claimed['current_lease']['job_id'] == job_id
            assert claimed['current_lease']['valid_now'] is True
            assert claimed['original_response']['generation'] == 1
            assert claimed['original_response']['packet_sha256'] == sha256(json_text(packet).encode()).hexdigest()
            assert CHECKS.state(store.connection) == {'current_cases': 24, 'reviewed_sources': 141}
            save('claim-receipt.json', claimed)
            store.close()
            store = None
            result = {'status': 'queued_and_claimed_once_pending_review', 'recorded_at': clock().isoformat(),
                      'job_id': job_id, 'worker': WORKER, 'generation': 1,
                      'lease_until': claimed['original_response']['lease_until'],
                      'packet_SHA': digest(HERE / 'job-packet.json'),
                      'DB_before_SHA': EXPECTED, 'DB_after_SHA': digest(DB),
                      'backup_file': str(backup), 'pending_source_ids': [SOURCE],
                      'financial_inputs_adopted': False, 'GETs': 0}
            save('queue-claim-completion.json', result)
            print(json.dumps(result))
        except BaseException as error:
            if store is not None:
                store.close()
            event('failure', 'failed', {'type': type(error).__name__, 'message': str(error),
                                        'instruction': 'Inspect journal/current job; never replay successful or uncertain mutations.'})
            raise


if __name__ == '__main__':
    main()
