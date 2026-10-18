"""A cited extraction can match a model number without certifying its meaning."""
from copy import deepcopy
import unittest

from ir_agent.disclosed_facts import normalize_disclosed_facts
from ir_agent.model_inputs import audit_model_inputs
from test_disclosed_facts import request as fact_request


def request():
    raw = fact_request('27.45', '円', 'JPY-per-share', kind='issuer_guidance')
    raw['source']['metadata']['synthetic'] = True
    bundle = normalize_disclosed_facts(raw, now='2026-10-15T01:00:00+00:00')
    derived = bundle['sources'][1]
    attribution = {'reference': 'Synthetic pipeline fixture only', 'author': 'Fixture author',
                   'recorded_at': '2026-10-15T01:10:00+00:00',
                   'rationale': 'Check exact numbers; all financial meaning remains unverified.'}
    return {
        'synthetic': True, 'company_id': raw['source']['company_id'],
        'as_of': '2026-10-15T02:00:00+00:00', 'sources': bundle['sources'],
        'valuation': {'aggregation': 'unweighted', 'scenarios': [
            {'name': 'example', 'method': 'eps_multiple', 'inputs': {'eps_jpy': '27.45', 'pe': '12'}}]},
        'provenance': {
            'scenarios.example.inputs.eps_jpy': {**attribution, 'kind': 'issuer_guidance',
                'source_id': derived['id'], 'value_path': ['content', 'facts', 0, 'value'],
                'unit': 'JPY-per-share', 'period': 'Fixture fiscal label; not independently verified'},
            'scenarios.example.inputs.pe': {**attribution, 'kind': 'synthetic_example'}},
    }


class FactModelPipelineTests(unittest.TestCase):
    def test_numeric_match_keeps_raw_lineage_and_unset_probabilities_separate(self):
        value = request(); original = deepcopy(value)
        result = audit_model_inputs(value)
        self.assertEqual(result['status'], 'synthetic_example')
        self.assertFalse(result['expected_value_available'])
        self.assertEqual(result['unset_probability_paths'], ['scenarios.example.probability'])
        self.assertEqual(result['missing_paths'], [])
        row = next(row for row in result['inputs'] if row['path'].endswith('eps_jpy'))
        self.assertEqual(row['source_value'], '27.45')
        self.assertEqual(set(row['source_lineage_ids']), {s['id'] for s in value['sources']})
        self.assertEqual(row['meaning_review_status'], 'unreviewed')
        self.assertFalse(result['financial_inputs_verified'])
        self.assertEqual(value, original)

    def test_matching_derived_number_does_not_hide_a_missing_original(self):
        value = request(); value['sources'] = value['sources'][1:]
        result = audit_model_inputs(value)
        self.assertEqual(result['status'], 'needs_review')
        row = next(row for row in result['inputs'] if row['path'].endswith('eps_jpy'))
        self.assertEqual(row['source_value'], '27.45')
        self.assertIn('missing_origin_source_snapshot', row['reason_codes'])

    def test_original_available_before_extraction_does_not_backdate_derived_input(self):
        value = request()
        value['provenance']['scenarios.example.inputs.eps_jpy']['recorded_at'] = '2026-10-15T00:30:00+00:00'
        result = audit_model_inputs(value)
        self.assertEqual(result['status'], 'needs_review')
        row = next(row for row in result['inputs'] if row['path'].endswith('eps_jpy'))
        self.assertIn('source_not_available_at_recording', row['reason_codes'])


if __name__ == '__main__':
    unittest.main()
