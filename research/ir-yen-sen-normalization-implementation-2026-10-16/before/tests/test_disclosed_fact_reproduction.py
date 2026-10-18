"""Known extraction replay catches inconsistent numbers without certifying meaning."""
from copy import deepcopy
import json
import unittest

from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source
from ir_agent.harness import Harness
from ir_agent.model_inputs import audit_model_inputs
from ir_agent.store import Store
from test_disclosed_facts import NOW, request as facts_request
from test_fact_model_pipeline import request as model_request


def replay(bundle):
    return reproduce_disclosed_fact_source(bundle['sources'][1], {source['id']: source for source in bundle['sources']})


def eps_row(result):
    return next(row for row in result['inputs'] if row['path'].endswith('eps_jpy'))


class DisclosedFactReproductionTests(unittest.TestCase):
    def test_known_source_reproduces_its_content_and_keeps_meaning_unverified(self):
        bundle = normalize_disclosed_facts(facts_request('27.45', '円', 'JPY-per-share', kind='issuer_guidance'), now=NOW)
        original = deepcopy(bundle)
        result = replay(bundle)
        self.assertEqual(result['status'], 'reproduced')
        self.assertEqual(result['original_content_sha256_status'], 'matched')
        self.assertEqual(result['original_snapshot_sha256_status'], 'matched_supplied_snapshot')
        self.assertEqual(result['fact_kinds'], [{'id': 'fact-1', 'kind': 'issuer_guidance'}])
        self.assertFalse(result['financial_inputs_verified']); self.assertTrue(result['meaning_review_required'])
        self.assertEqual(bundle, original)

    def test_store_defaults_do_not_turn_unchanged_content_into_a_false_corruption(self):
        value = facts_request('27.45', '円', 'JPY-per-share', kind='issuer_guidance')
        value['source'].pop('requires_research'); value['source'].pop('metadata')
        bundle = normalize_disclosed_facts(value, now=NOW)
        store = Store(':memory:'); self.addCleanup(store.close)
        harness = Harness(store)
        harness.ingest({'schema_version': 1, 'companies': [{'id': 'jp:130A', 'name': 'Fixture issuer'}]})
        harness.ingest(bundle)
        saved = [store.source(source['id']) for source in bundle['sources']]
        result = replay({'sources': saved})
        self.assertEqual(result['status'], 'reproduced')
        self.assertEqual(result['original_snapshot_sha256_status'], 'matched_without_validation_defaults')
        self.assertEqual(result['original_content_sha256_status'], 'matched')
        self.assertNotIn('requires_research', bundle['sources'][0])
        self.assertNotIn('metadata', bundle['sources'][0])

    def test_derived_value_and_model_cannot_be_changed_together_to_bypass_raw_quote(self):
        value = model_request(); derived = value['sources'][1]
        content = json.loads(derived['content']); content['facts'][0]['value'] = '100'
        derived['content'] = json.dumps(content)
        value['valuation']['scenarios'][0]['inputs']['eps_jpy'] = '100'
        value['provenance']['scenarios.example.inputs.eps_jpy']['kind'] = 'reported_fact'
        result = audit_model_inputs(value); row = eps_row(result)
        self.assertEqual(result['status'], 'needs_review')
        self.assertEqual(row['source_value'], '100')
        self.assertIn('normalized_content_not_reproduced', row['reason_codes'])
        self.assertIn('disclosed_fact_kind_mismatch', row['reason_codes'])
        self.assertEqual(row['source_fact_kind'], 'issuer_guidance')
        self.assertEqual(row['meaning_review_status'], 'unreviewed')

    def test_provenance_kind_must_preserve_the_structured_fact_category(self):
        value = model_request()
        value['provenance']['scenarios.example.inputs.eps_jpy']['kind'] = 'reported_fact'
        row = eps_row(audit_model_inputs(value))
        self.assertEqual(row['normalization_checks'][0]['status'], 'reproduced')
        self.assertEqual(row['status'], 'needs_review')
        self.assertIn('disclosed_fact_kind_mismatch', row['reason_codes'])

    def test_original_content_token_and_unit_arithmetic_are_replayed(self):
        for damage, reason in [('raw_content', 'original_content_hash_mismatch'),
                               ('raw_token', 'normalized_source_not_reproducible'),
                               ('multiplier', 'normalized_content_not_reproduced')]:
            value = model_request()
            if damage == 'raw_content':
                value['sources'][0]['content'] = value['sources'][0]['content'].replace('27.45', '29.45')
            else:
                parsed = json.loads(value['sources'][1]['content'])
                if damage == 'raw_token': parsed['facts'][0]['raw_value'] = '29.45'
                else: parsed['facts'][0]['normalization']['explicit_unit_multiplier'] = '1000'
                value['sources'][1]['content'] = json.dumps(parsed)
            with self.subTest(damage=damage):
                row = eps_row(audit_model_inputs(value))
                self.assertEqual(row['status'], 'needs_review')
                self.assertIn(reason, row['reason_codes'])

    def test_snapshot_representation_or_preserved_first_retrieval_is_separate_from_content(self):
        bundle = normalize_disclosed_facts(facts_request(), now=NOW)
        # A store may have retained an earlier first retrieval than the raw
        # input snapshot used by a later extraction; do not invent that snapshot.
        bundle['sources'][0]['retrieved_at'] = '2026-10-14T23:59:00+00:00'
        result = replay(bundle)
        self.assertEqual(result['status'], 'reproduced')
        self.assertEqual(result['original_snapshot_sha256_status'], 'not_reverified')
        self.assertEqual(result['original_content_sha256_status'], 'matched')
        self.assertEqual(result['reason_codes'], [])

    def test_unknown_provider_is_not_guessed_but_known_unsupported_version_is_held(self):
        value = model_request(); value['sources'][1]['metadata']['provider'] = 'unknown_external_provider'
        row = eps_row(audit_model_inputs(value))
        self.assertEqual(row['status'], 'source_value_matched')
        self.assertNotIn('normalization_checks', row)
        for version in (2, None, True, '1', {}, []):
            value = model_request(); value['sources'][1]['metadata']['normalization_version'] = version
            with self.subTest(version=version):
                row = eps_row(audit_model_inputs(value))
                self.assertEqual(row['status'], 'needs_review')
                self.assertIn('unsupported_normalization_version', row['reason_codes'])

    def test_malformed_known_content_is_held_without_unhandled_exception(self):
        source_content = model_request()['sources'][1]['content']
        duplicate_fact_equal = source_content.replace('"value":"27.45"', '"value":"27.45","value":"27.45"')
        duplicate_fact_different = source_content.replace('"value":"27.45"', '"value":"100","value":"27.45"')
        duplicate_top_equal = source_content[:-1] + ',"original_source_id":"saved-source"}'
        duplicate_top_different = source_content[:-1] + ',"original_source_id":"other-source"}'
        for content in ('not JSON', '[]', '{}', '{"facts":NaN}', duplicate_fact_equal, duplicate_fact_different,
                        duplicate_top_equal, duplicate_top_different):
            value = model_request(); value['sources'][1]['content'] = content
            with self.subTest(content=content):
                # The helper must reject duplicates itself, including when this
                # source is only an ancestor and no direct field lookup occurs.
                check = reproduce_disclosed_fact_source(value['sources'][1],
                    {source['id']: source for source in value['sources']})
                self.assertEqual(check['status'], 'needs_review')
                self.assertIn('normalized_source_not_reproducible', check['reason_codes'])
                row = eps_row(audit_model_inputs(value))
                self.assertEqual(row['status'], 'needs_review')
                self.assertIn('normalized_source_not_reproducible', row['reason_codes'])


if __name__ == '__main__': unittest.main()
