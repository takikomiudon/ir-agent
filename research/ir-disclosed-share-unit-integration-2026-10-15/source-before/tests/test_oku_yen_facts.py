"""Only the explicit oku-yen currency conversion is added; meaning stays open."""
from copy import deepcopy
from decimal import Inexact, Rounded, localcontext
from hashlib import sha256
import json
from pathlib import Path
import unittest

from ir_agent.adapters.common import canonical_json
from ir_agent.disclosed_facts import (
    _UNIT_MULTIPLIERS, normalize_disclosed_facts, reproduce_disclosed_fact_source,
)
from test_disclosed_facts import NOW, LATER, request as fact_request


BASELINE = Path(__file__).resolve().parents[1] / 'research/ir-oku-yen-normalization-2026-10-15/baseline.json'


def request(raw='1,234.50', *, kind='issuer_guidance'):
    value = fact_request(raw, '億円', 'JPY', kind=kind)
    value['source']['metadata']['synthetic'] = True
    return value


def first_fact(bundle):
    return json.loads(bundle['sources'][1]['content'])['facts'][0]


class OkuYenFactsTests(unittest.TestCase):
    def test_exact_conversion_preserves_raw_quote_and_unverified_meaning(self):
        value = request(); original = deepcopy(value)
        bundle = normalize_disclosed_facts(value, now=NOW)
        fact = first_fact(bundle)
        self.assertEqual(fact['raw_value'], '1,234.50')
        self.assertEqual(fact['value'], '123450000000.00')
        self.assertEqual(fact['normalization']['explicit_unit_multiplier'], '100000000')
        self.assertEqual(fact['unit'], 'JPY')
        self.assertEqual(fact['raw_unit_label'], '億円')
        for key in ('basis_quote', 'definition', 'scope', 'period', 'kind', 'raw_period_label'):
            self.assertEqual(fact[key], original['facts'][0][key])
        self.assertTrue(fact['meaning_review_required'])
        self.assertFalse(fact['financial_inputs_verified'])
        parsed = json.loads(bundle['sources'][1]['content'])
        self.assertFalse(parsed['declarations']['forecast_values_automatically_adopted'])
        self.assertEqual(bundle['theses'], [])
        self.assertEqual(bundle['sources'][0], original['source'])
        self.assertEqual(value, original)

    def test_decimal_sign_zero_and_large_value_are_exact_under_host_precision(self):
        cases = [('△1.25', '-125000000.00'), ('▲2', '-200000000'),
                 ('+0.01', '1000000.00'), ('-0.00', '0'),
                 ('123456789012345678901234567890.123456789',
                  '12345678901234567890123456789012345678.900000000')]
        with localcontext() as context:
            context.prec = 3
            context.traps[Inexact] = context.traps[Rounded] = True
            for raw, expected in cases:
                with self.subTest(raw=raw):
                    self.assertEqual(first_fact(normalize_disclosed_facts(request(raw), now=NOW))['value'], expected)

    def test_missing_and_dash_values_remain_null_and_zero_is_explicit(self):
        for raw in (None, '', '-', '—'):
            with self.subTest(raw=raw):
                fact = first_fact(normalize_disclosed_facts(request(raw), now=NOW))
                self.assertIsNone(fact['value'])
                self.assertFalse(fact['normalization']['raw_numeric_token_verified'])
        self.assertEqual(first_fact(normalize_disclosed_facts(request('0'), now=NOW))['value'], '0')

    def test_no_per_share_ratio_trillion_or_implicit_alias_conversion(self):
        for raw_unit, unit in [('億円', 'JPY-per-share'), ('億円', 'ratio'),
                               ('兆円', 'JPY'), ('億', 'JPY'), ('億 円', 'JPY')]:
            value = fact_request('10', raw_unit, unit)
            original = deepcopy(value)
            with self.subTest(raw_unit=raw_unit, unit=unit), self.assertRaisesRegex(ValueError, 'mapping'):
                normalize_disclosed_facts(value, now=NOW)
            self.assertEqual(value, original)

    def test_all_oku_labels_and_tokens_must_be_in_the_original_quote(self):
        for key, replacement in [('basis_quote', '保存原文にない2026年度 10 億円'),
                                  ('raw_unit_label', '百万円'), ('raw_period_label', '2027年度'),
                                  ('raw_value', '1234')]:
            value = request(); value['facts'][0][key] = replacement
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize_disclosed_facts(value, now=NOW)

    def test_future_source_and_review_before_retrieval_remain_rejected(self):
        for target, field, stamp in [('source', 'retrieved_at', LATER), ('source', 'published_at', LATER),
                                     ('review', 'recorded_at', LATER),
                                     ('review', 'recorded_at', '2026-10-14T23:59:00+00:00')]:
            value = request(); value[target][field] = stamp
            original = deepcopy(value)
            with self.subTest(target=target, field=field, stamp=stamp), self.assertRaises(ValueError):
                normalize_disclosed_facts(value, now=NOW)
            self.assertEqual(value, original)

    def test_oku_replay_retains_version_identity_and_holds_arithmetic_tampering(self):
        bundle = normalize_disclosed_facts(request(), now=NOW)
        sources = {s['id']: s for s in bundle['sources']}
        derived = bundle['sources'][1]
        replay = reproduce_disclosed_fact_source(derived, sources)
        self.assertEqual(replay['status'], 'reproduced')
        self.assertFalse(replay['financial_inputs_verified'])
        self.assertEqual(derived['metadata']['normalization_version'], 1)
        later = normalize_disclosed_facts(request(), now=LATER)['sources'][1]
        for key in ('id', 'content', 'metadata'):
            self.assertEqual(later[key], derived[key])
        damaged = deepcopy(derived)
        content = json.loads(damaged['content'])
        content['facts'][0]['value'] = '1234500000.00'
        content['facts'][0]['normalization']['explicit_unit_multiplier'] = '1000000'
        damaged['content'] = canonical_json(content)
        check = reproduce_disclosed_fact_source(damaged, sources)
        self.assertEqual(check['status'], 'needs_review')
        self.assertIn('normalized_content_not_reproduced', check['reason_codes'])
        self.assertEqual(reproduce_disclosed_fact_source(derived, {})['status'], 'needs_review')

    def test_only_one_mapping_added_and_all_legacy_bundle_hashes_and_ids_unchanged(self):
        baseline = json.loads(BASELINE.read_text(encoding='utf-8'))
        fixtures = baseline['legacy_fixtures']
        old_mappings = {(row['raw_unit_label'], row['unit']): row['multiplier'] for row in fixtures}
        self.assertEqual(len(old_mappings), baseline['legacy_mapping_count'])
        self.assertEqual(len(fixtures), len(old_mappings) * len(baseline['legacy_kinds']))
        self.assertEqual(_UNIT_MULTIPLIERS, {**old_mappings, ('億円', 'JPY'): '100000000'})
        for fixture in fixtures:
            original = deepcopy(fixture['request'])
            with self.subTest(raw_unit=fixture['raw_unit_label'], unit=fixture['unit'], kind=fixture['kind']):
                bundle = normalize_disclosed_facts(fixture['request'], now=fixture['now'])
                derived = bundle['sources'][1]
                self.assertEqual(sha256(canonical_json(bundle).encode()).hexdigest(), fixture['bundle_canonical_sha256'])
                self.assertEqual(derived['id'], fixture['derived_source_id'])
                self.assertEqual(sha256(derived['content'].encode()).hexdigest(), fixture['derived_content_sha256'])
                self.assertEqual(fixture['request'], original)


if __name__ == '__main__':
    unittest.main()
