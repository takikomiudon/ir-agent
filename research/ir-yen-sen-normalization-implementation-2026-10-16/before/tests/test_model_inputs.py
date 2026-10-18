"""Saved-number matching and declared assumptions remain distinct from meaning."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from ir_agent.model_inputs import audit_model_inputs

ROOT = Path(__file__).resolve().parents[1]


def request():
    source = {'id': 'saved-values', 'company_id': 'example-issuer', 'title': 'Structured example values',
              'url': 'https://example.invalid/saved-values', 'source_type': 'public_disclosure',
              'published_at': '2026-10-08T09:00:00+09:00', 'retrieved_at': '2026-10-08T10:00:00+09:00',
              'content': 'Synthetic test data for provenance checks, not company information.',
              'metadata': {'values': {'probability': '1', 'eps_jpy': '10', 'pe': '12'}}}
    valuation = {'scenarios': [{'name': 'base', 'probability': '1', 'method': 'eps_multiple',
                               'inputs': {'eps_jpy': '10', 'pe': '12'}}]}
    provenance = {}
    for path, field in [('scenarios.base.probability', 'probability'), ('scenarios.base.inputs.eps_jpy', 'eps_jpy'),
                        ('scenarios.base.inputs.pe', 'pe')]:
        provenance[path] = {'kind': 'reported_fact', 'reference': 'Saved test source; attribution still needs review',
                            'rationale': 'Compare the saved numeric field with the supplied valuation input.',
                            'recorded_at': '2026-10-09T09:00:00+09:00', 'author': 'Test fixture author',
                            'source_id': source['id'], 'value_path': ['metadata', 'values', field]}
    return {'company_id': 'example-issuer', 'as_of': '2026-10-10T10:00:00+09:00',
            'valuation': valuation, 'sources': [source], 'provenance': provenance}


class ModelInputTests(unittest.TestCase):
    def test_exact_saved_fields_match_without_certifying_meaning_or_mutating_request(self):
        value = request(); before = deepcopy(value)
        result = audit_model_inputs(value)
        self.assertEqual(result['status'], 'source_values_matched')
        self.assertEqual(len(result['required_paths']), 3)
        self.assertEqual(result['missing_paths'], [])
        self.assertEqual(result['aggregation'], 'weighted')
        self.assertTrue(result['expected_value_available'])
        self.assertEqual(result['unset_probability_paths'], [])
        self.assertTrue(result['meaning_review_required']); self.assertFalse(result['financial_inputs_verified'])
        self.assertEqual(value, before)
        for row in result['inputs']:
            self.assertEqual(row['status'], 'source_value_matched')
            self.assertEqual(row['missing_meaning_fields'], ['unit', 'period'])
            self.assertEqual(row['meaning_review_status'], 'unreviewed')
        for origin in value['provenance'].values():
            origin.update(unit='Caller-supplied definition', period='Caller-supplied period')
        rows = audit_model_inputs(value)['inputs']
        self.assertTrue(all(row['missing_meaning_fields'] == [] for row in rows))
        self.assertTrue(all(row['meaning_review_status'] == 'unreviewed' for row in rows))
        self.assertTrue(any('does not consult live database classification corrections' in item for item in result['limitations']))

    def test_all_parent_snapshots_and_shared_dag_are_checked_without_false_cycles(self):
        value = request(); direct = value['sources'][0]
        direct['metadata'].update(original_source_id='parent-a', original_source_ids=['parent-a', 'parent-b'])
        for identifier in ('parent-a', 'parent-b', 'shared'):
            parent = deepcopy(direct); parent['id'] = identifier
            parent['metadata'] = {'original_source_ids': ['shared']} if identifier != 'shared' else {}
            value['sources'].append(parent)
        result = audit_model_inputs(value)
        self.assertEqual(result['status'], 'source_values_matched')
        self.assertTrue(all(set(row['source_lineage_ids']) == {'saved-values', 'parent-a', 'parent-b', 'shared'}
                            and len(row['source_lineage_ids']) == 4 for row in result['inputs']))
        for damage, reason in [('synthetic', 'synthetic_source_requires_synthetic_context'),
                               ('future', 'source_not_available_at_recording'),
                               ('company', 'source_company_mismatch'),
                               ('private', 'source_information_held_for_review')]:
            changed = deepcopy(value); second = changed['sources'][2]
            if damage == 'synthetic': second['metadata']['synthetic'] = True
            elif damage == 'future': second['retrieved_at'] = '2026-10-09T12:00:00+09:00'
            elif damage == 'company': second['company_id'] = 'another-issuer'
            else: second.update(source_type='ir_reply'); second['metadata']['information_status'] = 'potential_nonpublic'
            with self.subTest(damage=damage):
                audited = audit_model_inputs(changed)
                self.assertEqual(audited['status'], 'needs_review')
                self.assertTrue(all(reason in row['reason_codes'] for row in audited['inputs']))
        value['sources'][3]['metadata']['original_source_ids'] = ['saved-values']
        cyclic = audit_model_inputs(value)
        self.assertEqual(cyclic['status'], 'needs_review')
        self.assertTrue(all('cyclic_source_provenance' in row['reason_codes'] for row in cyclic['inputs']))

    def test_relabeling_synthetic_source_as_reported_fact_does_not_promote_it(self):
        value = request(); value['sources'][0]['metadata']['synthetic'] = True
        result = audit_model_inputs(value)
        self.assertEqual(result['status'], 'needs_review')
        self.assertTrue(all('synthetic_source_requires_synthetic_context' in row['reason_codes'] for row in result['inputs']))
        value['synthetic'] = True
        self.assertEqual(audit_model_inputs(value)['status'], 'source_values_matched')

    def test_unweighted_probabilities_remain_unset_and_configured_numbers_still_need_provenance(self):
        for declared in ('absent', None):
            value = request(); value['valuation']['aggregation'] = 'unweighted'
            scenario = value['valuation']['scenarios'][0]
            if declared == 'absent': scenario.pop('probability')
            else: scenario['probability'] = None
            probability = value['provenance'].pop('scenarios.base.probability')
            before = deepcopy(value)
            with self.subTest(declared=declared):
                result = audit_model_inputs(value)
                self.assertEqual(result['status'], 'source_values_matched')
                self.assertEqual(result['aggregation'], 'unweighted')
                self.assertFalse(result['expected_value_available'])
                self.assertEqual(result['unset_probability_paths'], ['scenarios.base.probability'])
                self.assertEqual(result['required_paths'], ['scenarios.base.inputs.eps_jpy', 'scenarios.base.inputs.pe'])
                self.assertEqual(result['missing_paths'], [])
                self.assertEqual(value, before)
                value['provenance']['scenarios.base.probability'] = probability
                with self.assertRaisesRegex(ValueError, 'Unknown provenance path'):
                    audit_model_inputs(value)
                value['provenance'].pop('scenarios.base.probability')
                value['provenance'].pop('scenarios.base.inputs.pe')
                missing = audit_model_inputs(value)
                self.assertEqual(missing['status'], 'needs_review')
                self.assertEqual(missing['missing_paths'], ['scenarios.base.inputs.pe'])

    def test_dcf_all_canonical_numbers_and_probabilities_are_required_without_auto_completion(self):
        value = request()
        value['valuation'] = {'scenarios': [{'name': 'base', 'probability': '1', 'method': 'dcf',
                            'inputs': {'discount_rate': '.1', 'terminal_growth_rate': '.02', 'cash_jpy': '0',
                                       'debt_jpy': '0', 'shares_outstanding': '100', 'fcf_jpy': ['1000', '1100']}}]}
        value['provenance'] = {}
        result = audit_model_inputs(value)
        paths = {'scenarios.base.probability', *('scenarios.base.inputs.' + field for field in
                 ['discount_rate', 'terminal_growth_rate', 'cash_jpy', 'debt_jpy', 'shares_outstanding', 'fcf_jpy.0', 'fcf_jpy.1'])}
        self.assertEqual(set(result['required_paths']), paths)
        self.assertEqual(set(result['missing_paths']), paths)
        self.assertEqual(result['status'], 'needs_review')
        self.assertTrue(all(row['reason_codes'] == ['missing_provenance'] for row in result['inputs']))

    def test_missing_sources_fields_and_different_numbers_require_review(self):
        for damage, reason in [('snapshot', 'missing_source_snapshot'), ('source_id', 'missing_source_id'),
                               ('value_path', 'missing_value_path'), ('field', 'source_field_not_found'),
                               ('value', 'source_value_mismatch')]:
            value = request(); origin = value['provenance']['scenarios.base.inputs.eps_jpy']
            if damage == 'snapshot': value['sources'] = []
            elif damage in {'source_id', 'value_path'}: origin.pop(damage)
            elif damage == 'field': origin['value_path'] = ['metadata', 'missing']
            else: value['sources'][0]['metadata']['values']['eps_jpy'] = '11'
            with self.subTest(damage=damage):
                result = audit_model_inputs(value)
                self.assertEqual(result['status'], 'needs_review')
                row = next(row for row in result['inputs'] if row['path'] == 'scenarios.base.inputs.eps_jpy')
                self.assertIn(reason, row['reason_codes'])

    def test_source_issuer_time_and_entire_origin_chain_are_checked(self):
        for damage, reason in [('company', 'source_company_mismatch'), ('future', 'source_not_available_at_recording'),
                               ('late_record', 'provenance_not_available_at_audit'),
                               ('origin', 'missing_origin_source_snapshot'), ('origin_company', 'source_company_mismatch'),
                               ('origin_future', 'source_not_available_at_recording'),
                               ('origin_private', 'source_information_held_for_review'), ('cycle', 'cyclic_source_provenance')]:
            value = request(); source = value['sources'][0]
            if damage == 'company': source['company_id'] = 'another-issuer'
            elif damage == 'future': source['retrieved_at'] = '2026-10-09T12:00:00+09:00'
            elif damage == 'late_record':
                value['provenance']['scenarios.base.probability']['recorded_at'] = '2026-10-11T00:00:00+09:00'
            else:
                source['metadata']['original_source_id'] = 'origin'
                if damage == 'cycle': source['metadata']['original_source_id'] = source['id']
                elif damage != 'origin':
                    original = deepcopy(source); original['id'] = 'origin'; original['metadata'] = {}
                    if damage == 'origin_company': original['company_id'] = 'another-issuer'
                    elif damage == 'origin_future': original['retrieved_at'] = '2026-10-09T12:00:00+09:00'
                    else: original.update(source_type='ir_reply', metadata={'information_status': 'potential_nonpublic'})
                    value['sources'].append(original)
            with self.subTest(damage=damage):
                result = audit_model_inputs(value)
                self.assertEqual(result['status'], 'needs_review')
                self.assertTrue(any(reason in row['reason_codes'] for row in result['inputs']))

    def test_explicit_assumptions_are_attributed_and_synthetic_examples_cannot_be_promoted(self):
        value = request()
        for origin in value['provenance'].values():
            origin.update(kind='explicit_assumption')
            origin.pop('source_id'); origin.pop('value_path')
        result = audit_model_inputs(value)
        self.assertEqual(result['status'], 'assumptions_declared')
        self.assertTrue(all(row['author'] == 'Test fixture author' for row in result['inputs']))
        self.assertTrue(all(row['status'] == 'explicit_assumption' and 'source_value' not in row for row in result['inputs']))
        value['provenance']['scenarios.base.probability']['kind'] = 'synthetic_example'
        with self.assertRaisesRegex(ValueError, 'Synthetic example'): audit_model_inputs(value)
        value['synthetic'] = True
        self.assertEqual(audit_model_inputs(value)['status'], 'synthetic_example')

    def test_pdf_words_are_not_parsed_as_values_and_structured_saved_json_is_explicit(self):
        value = request(); origin = value['provenance']['scenarios.base.inputs.eps_jpy']
        value['sources'][0]['content'] = 'PDF text: EPS 10円。対象期間と定義の確認が必要。'
        origin['value_path'] = ['content']
        result = audit_model_inputs(value)
        row = next(row for row in result['inputs'] if row['path'] == 'scenarios.base.inputs.eps_jpy')
        self.assertIn('source_field_not_numeric', row['reason_codes'])
        value['sources'][0]['content'] = json.dumps({'eps_jpy': '10'})
        origin['value_path'] = ['content', 'eps_jpy']
        self.assertEqual(audit_model_inputs(value)['status'], 'source_values_matched')

    def test_unknown_paths_malformed_types_and_invalid_model_contract_are_errors(self):
        variants = []
        value = request(); value['provenance']['scenarios.base.method'] = {}; variants.append(value)
        value = request(); value['provenance']['scenarios.base.probability']['kind'] = []; variants.append(value)
        value = request(); value['provenance']['scenarios.base.probability']['value_path'] = 'metadata'; variants.append(value)
        value = request(); value['provenance']['scenarios.base.probability']['value_path'] = [True]; variants.append(value)
        value = request(); value['provenance']['scenarios.base.probability'].pop('author'); variants.append(value)
        value = request(); value['valuation']['scenarios'][0]['probability'] = '.5'; variants.append(value)
        value = request(); value['sources'].append(deepcopy(value['sources'][0])); variants.append(value)
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError): audit_model_inputs(value)

    def test_saved_example_is_explicitly_synthetic_and_does_not_verify_inputs(self):
        value = json.loads((ROOT / 'examples/model-input-review.json').read_text())
        result = audit_model_inputs(value)
        self.assertTrue(result['synthetic'])
        self.assertEqual(result['status'], 'synthetic_example')
        self.assertFalse(result['financial_inputs_verified'])
        self.assertEqual(result['missing_paths'], [])


if __name__ == '__main__': unittest.main()
