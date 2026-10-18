#!/usr/bin/env python3
"""Run one synthetic qualitative review in memory; no network or real DB."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.models import json_text
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.store import Store


def now():
    return datetime.now(timezone.utc)


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        case = root / 'case.md'; case.write_text('Synthetic issue: interpret order observations.')
        manifest = root / 'manifest.md'; manifest.write_text('Explicitly selected synthetic demo case.')
        def ref(path):
            return {'path': path.name, 'sha256': sha256(path.read_bytes()).hexdigest()}
        store = Store(':memory:')
        try:
            harness = Harness(store); current = now()
            harness.ingest({'schema_version': 1, 'companies': [
                {'id': 'synthetic-demo', 'name': 'Synthetic qualitative demonstration', 'status': 'watch'}],
                'sources': [{'id': 'synthetic-orders', 'company_id': 'synthetic-demo',
                    'title': 'Synthetic order statement', 'url': 'https://example.invalid/synthetic-orders',
                    'source_type': 'public_disclosure', 'published_at': None,
                    'retrieved_at': (current - timedelta(seconds=1)).isoformat(),
                    'content': 'Order observations do not independently establish future earnings.',
                    'metadata': {'synthetic': True}}]}, now=current)
            current = now(); Intake(store).queue(current.isoformat(), now=current)
            job = harness.claim('demo-classifier', now=now(), measurement_synthetic=True)
            saved = job['packet']['sources'][0]
            harness.complete(job['id'], 'demo-classifier', {'classifications': [{
                'source_id': saved['id'], 'expected_version': 0, 'kind': 'other', 'financial_content': False,
                'basis_quote': saved['content'], 'rationale': 'Classify the synthetic source, without adopting a forecast.'}]}, now=now())
            registry = QualitativeResearch(store)
            registry.register_case({'case_id': 'synthetic-orders-case', 'company_id': 'synthetic-demo',
                'issue_id': 'synthetic-orders-interpretation', 'synthetic': True, 'enabled': True,
                'recorded_at': now().isoformat(), 'case_ref': ref(case), 'manifest_ref': ref(manifest),
                'management_review': None, 'bootstrap_reviews': []}, research_root=root, now=now())
            current = now(); first = registry.queue_cases(['synthetic-orders-case'], current.isoformat(), now=current)
            current = now(); duplicate = registry.queue_cases(['synthetic-orders-case'], current.isoformat(), now=current)
            job = harness.claim('demo-reviewer', now=now(), measurement_synthetic=True)
            packet = job['packet']
            result = {'summary': 'Evidence remains insufficient for a future earnings conclusion.',
                'recorded_at': now().isoformat(), 'source_reviews': [{
                    'source_id': saved['id'], 'snapshot_sha256': packet['source_snapshot_sha256'][saved['id']],
                    'read_state': 'reviewed', 'outcome': 'unresolved', 'basis_quote': saved['content'],
                    'rationale': 'The statement does not specify a future profit effect.'}],
                'case_observation': {'issue_id': 'synthetic-orders-interpretation', 'outcome': 'unresolved',
                    'rationale': 'Do not convert a qualitative observation into a numerical forecast.',
                    'evidence_source_ids': [saved['id']]}, 'management_review_update': {'mode': 'retain'}}
            harness.complete(job['id'], 'demo-reviewer', result, now=now())
            current = now(); after = registry.queue_cases(['synthetic-orders-case'], current.isoformat(), now=current)
            output = {'synthetic': True, 'in_memory_only': True, 'first_jobs_created': first['jobs_created'],
                'duplicate_jobs_created': duplicate['jobs_created'], 'after_review_jobs_created': after['jobs_created'],
                'case_version': registry.show_case('synthetic-orders-case')['version'],
                'financial_theses': store.connection.execute('SELECT count(*) FROM theses').fetchone()[0],
                'financial_inputs_verified': False, 'network_requests_IR_orders': 0}
            assert output['first_jobs_created'] == 1 and output['case_version'] == 2
            assert output['duplicate_jobs_created'] == output['after_review_jobs_created'] == output['financial_theses'] == 0
            print(json_text(output))
        finally:
            store.close()


if __name__ == '__main__':
    main()
