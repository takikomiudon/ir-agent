"""Synthetic external estimates retain attribution without adopting a forecast."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from ir_agent.adapters.common import canonical_json
from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source
from ir_agent.model_inputs import audit_model_inputs
from test_disclosed_facts import NOW, LATER, request as fact_request


EPS_PATH = 'scenarios.example.inputs.eps_jpy'


def external_request():
    quote = '架空提供者の架空著者 Synthetic Analyst：2026年度 E（外部推定）EPS 12.50 円。'
    value = fact_request('12.50', '円', 'JPY-per-share', kind='external_estimate', quote=quote)
    value['source']['metadata'].update(synthetic=True, report_author='Synthetic Analyst',
                                       provider='Fictional Research', estimate_label='E（外部推定）')
    value['review']['author'] = 'Synthetic Extractor'
    value['facts'][0]['concept'] = 'external_eps_estimate'
    value['facts'][0]['definition'] = '架空著者 Synthetic Analyst のE（外部推定）。会社予想・実績ではない。'
    value['facts'][0]['scope'].update(report_author='Synthetic Analyst', estimate_label='E（外部推定）')
    return value


def pipeline_request():
    raw = external_request()
    bundle = normalize_disclosed_facts(raw, now=NOW)
    attribution = {'reference': 'Synthetic external-estimate pipeline only', 'author': 'Synthetic Extractor',
                   'recorded_at': '2026-10-15T01:10:00+00:00',
                   'rationale': 'Numerical extraction only; no authorship, forecast meaning or model adoption verified.'}
    return {'synthetic': True, 'company_id': raw['company_id'], 'as_of': LATER,
            'sources': bundle['sources'],
            'valuation': {'aggregation': 'unweighted', 'scenarios': [
                {'name': 'example', 'method': 'eps_multiple', 'inputs': {'eps_jpy': '12.50', 'pe': '10'}}]},
            'provenance': {
                EPS_PATH: {**attribution, 'kind': 'external_estimate', 'source_id': bundle['sources'][1]['id'],
                           'value_path': ['content', 'facts', 0, 'value'], 'unit': 'JPY-per-share',
                           'period': 'Synthetic 2026年度 E label; semantic alignment unverified'},
                'scenarios.example.inputs.pe': {**attribution, 'kind': 'synthetic_example',
                    'rationale': 'Pure synthetic multiplier 10; no real issuer fair multiple or adopted forecast.'}}}


def eps_row(audit):
    return next(row for row in audit['inputs'] if row['path'] == EPS_PATH)


class ExternalEstimateFactsTests(unittest.TestCase):
    def test_normalization_keeps_external_author_and_e_label_separate_from_extractor(self):
        value = external_request(); original = deepcopy(value)
        bundle = normalize_disclosed_facts(value, now=NOW)
        raw, derived = bundle['sources']
        content = json.loads(derived['content']); fact = content['facts'][0]
        self.assertEqual(value, original)
        self.assertEqual(raw, original['source'])
        self.assertEqual(fact['kind'], 'external_estimate')
        self.assertEqual(fact['value'], '12.50')
        self.assertEqual(fact['scope']['report_author'], 'Synthetic Analyst')
        self.assertEqual(raw['metadata']['report_author'], 'Synthetic Analyst')
        self.assertEqual(fact['scope']['estimate_label'], 'E（外部推定）')
        self.assertIn('E（外部推定）', fact['definition'])
        self.assertEqual(fact['basis_quote'], raw['content'])
        self.assertEqual(content['review']['author'], 'Synthetic Extractor')
        self.assertEqual(derived['metadata']['review']['author'], 'Synthetic Extractor')
        self.assertFalse(content['declarations']['forecast_values_automatically_adopted'])
        self.assertFalse(fact['financial_inputs_verified'])
        self.assertTrue(fact['meaning_review_required'])
        self.assertEqual(bundle['theses'], [])

    def test_external_estimate_replays_and_later_extraction_keeps_identity(self):
        value = external_request()
        bundle = normalize_disclosed_facts(value, now=NOW); original = deepcopy(bundle)
        check = reproduce_disclosed_fact_source(bundle['sources'][1], {s['id']: s for s in bundle['sources']})
        self.assertEqual(check['status'], 'reproduced')
        self.assertEqual(check['fact_kinds'], [{'id': 'fact-1', 'kind': 'external_estimate'}])
        self.assertEqual(check['original_content_sha256_status'], 'matched')
        self.assertEqual(check['original_snapshot_sha256_status'], 'matched_supplied_snapshot')
        self.assertFalse(check['financial_inputs_verified'])
        self.assertTrue(check['meaning_review_required'])
        later = normalize_disclosed_facts(value, now=LATER)['sources'][1]
        self.assertEqual(later['id'], bundle['sources'][1]['id'])
        self.assertEqual(later['content'], bundle['sources'][1]['content'])
        self.assertEqual(later['metadata'], bundle['sources'][1]['metadata'])
        self.assertNotEqual(later['retrieved_at'], bundle['sources'][1]['retrieved_at'])
        self.assertEqual(bundle, original)

    def test_pipeline_numeric_match_does_not_verify_author_meaning_or_adopt_probabilities(self):
        value = pipeline_request(); original = deepcopy(value)
        result = audit_model_inputs(value); row = eps_row(result)
        self.assertEqual(row['status'], 'source_value_matched')
        self.assertEqual(row['source_fact_kind'], 'external_estimate')
        self.assertEqual(row['normalization_checks'][0]['status'], 'reproduced')
        self.assertEqual(row['source_value'], '12.50')
        self.assertEqual(row['meaning_review_status'], 'unreviewed')
        self.assertIn('authorship_and_forecast_status_not_verified', row['meaning_checks'])
        self.assertEqual(result['status'], 'synthetic_example')
        self.assertFalse(result['financial_inputs_verified'])
        self.assertTrue(result['meaning_review_required'])
        self.assertFalse(result['expected_value_available'])
        self.assertEqual(result['unset_probability_paths'], ['scenarios.example.probability'])
        self.assertEqual(value, original)

    def test_external_fact_cannot_be_relabelled_as_reported_fact_or_issuer_guidance(self):
        for kind in ('reported_fact', 'issuer_guidance'):
            value = pipeline_request(); value['provenance'][EPS_PATH]['kind'] = kind
            original = deepcopy(value)
            with self.subTest(kind=kind):
                result = audit_model_inputs(value); row = eps_row(result)
                self.assertEqual(result['status'], 'needs_review')
                self.assertEqual(row['status'], 'needs_review')
                self.assertEqual(row['source_fact_kind'], 'external_estimate')
                self.assertEqual(row['normalization_checks'][0]['status'], 'reproduced')
                self.assertIn('disclosed_fact_kind_mismatch', row['reason_codes'])
                self.assertEqual(value, original)

    def test_missing_original_and_matching_tampered_model_remain_held(self):
        for damage, reason in (('missing_original', 'missing_origin_source_snapshot'),
                               ('tamper_value_and_model', 'normalized_content_not_reproduced')):
            value = pipeline_request()
            if damage == 'missing_original':
                value['sources'] = value['sources'][1:]
            else:
                derived = value['sources'][1]
                content = json.loads(derived['content']); content['facts'][0]['value'] = '999'
                derived['content'] = canonical_json(content)
                value['valuation']['scenarios'][0]['inputs']['eps_jpy'] = '999'
            original = deepcopy(value)
            with self.subTest(damage=damage):
                result = audit_model_inputs(value); row = eps_row(result)
                self.assertEqual(result['status'], 'needs_review')
                self.assertEqual(row['status'], 'needs_review')
                self.assertIn(reason, row['reason_codes'])
                self.assertEqual(row['source_value'], value['valuation']['scenarios'][0]['inputs']['eps_jpy'])
                self.assertEqual(value, original)

    def test_extraction_or_model_use_cannot_precede_available_source(self):
        value = external_request()
        value['review']['recorded_at'] = '2026-10-14T23:59:00+00:00'
        original = deepcopy(value)
        with self.assertRaises(ValueError):
            normalize_disclosed_facts(value, now=NOW)
        self.assertEqual(value, original)
        for recorded in ('2026-10-14T23:59:00+00:00', '2026-10-15T00:30:00+00:00'):
            value = pipeline_request(); value['provenance'][EPS_PATH]['recorded_at'] = recorded
            with self.subTest(recorded=recorded):
                result = audit_model_inputs(value)
                self.assertEqual(result['status'], 'needs_review')
                self.assertIn('source_not_available_at_recording', eps_row(result)['reason_codes'])

    def test_all_legacy_bundles_and_derived_identities_match_prechange_commitments(self):
        baseline_path = Path(__file__).resolve().parents[1] / 'research/ir-external-estimate-extraction-2026-10-15/baseline.json'
        baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
        fixtures = baseline['legacy_fixtures']
        self.assertEqual({item['kind'] for item in fixtures},
                         {'reported_fact', 'issuer_guidance', 'general_explanation'})
        self.assertEqual(len(fixtures), 3)
        for fixture in fixtures:
            original = deepcopy(fixture['request'])
            with self.subTest(kind=fixture['kind']):
                bundle = normalize_disclosed_facts(fixture['request'], now=fixture['now'])
                derived = bundle['sources'][1]
                self.assertEqual(sha256(canonical_json(bundle).encode()).hexdigest(), fixture['bundle_canonical_sha256'])
                self.assertEqual(derived['id'], fixture['derived_source_id'])
                self.assertEqual(sha256(derived['content'].encode()).hexdigest(), fixture['derived_content_sha256'])
                self.assertEqual(fixture['request'], original)


if __name__ == '__main__':
    unittest.main()
