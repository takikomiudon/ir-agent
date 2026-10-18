"""Explicit share-count scaling only; all definitions and adoption stay unverified."""
from copy import deepcopy
from decimal import Inexact, Rounded, localcontext
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ir_agent.adapters.common import canonical_json
from ir_agent.disclosed_facts import _UNIT_MULTIPLIERS, normalize_disclosed_facts, reproduce_disclosed_fact_source
from ir_agent.model_inputs import audit_model_inputs
from test_disclosed_facts import NOW, LATER, request as fact_request

ROOT = Path(__file__).resolve().parents[1]
ADDED = {('shares', 'shares'): '1', ('株', 'shares'): '1', ('千株', 'shares'): '1000',
         ('万株', 'shares'): '10000', ('百万株', 'shares'): '1000000'}


def request(raw='10,256,000', label='株', unit='shares', *, kind='reported_fact'):
    value = fact_request(raw, label, unit, kind=kind)
    value['source']['metadata']['synthetic'] = True
    value['facts'][0].update(concept='issued_shares_including_treasury',
        definition='Synthetic period-end issued ordinary shares including treasury; not a valuation denominator.',
        scope={'company_id': 'jp:130A', 'treasury_included': True, 'security_class': 'ordinary'})
    return value


def first(bundle): return json.loads(bundle['sources'][1]['content'])['facts'][0]


def replay(bundle):
    return reproduce_disclosed_fact_source(bundle['sources'][1], {s['id']: s for s in bundle['sources']})


def model_request():
    raw = request('10', '千株'); bundle = normalize_disclosed_facts(raw, now=NOW)
    valuation = json.loads((ROOT / 'examples/valuation-equity-bridge.synthetic.json').read_bytes())
    valuation.pop('research_context')
    scenario = valuation['scenarios'][0]; scenario['inputs']['shares_outstanding'] = '10000'
    prefix = 'scenarios.synthetic-equity-bridge.inputs.'
    attribution = {'reference': 'Synthetic unit pipeline only', 'author': 'Fixture author',
                   'recorded_at': '2026-10-15T01:10:00+00:00', 'rationale': 'No financial meaning adopted.'}
    provenance = {}
    for key, item in scenario['inputs'].items():
        if isinstance(item, list):
            for index in range(len(item)):
                provenance[prefix + key + '.' + str(index)] = {**attribution, 'kind': 'synthetic_example'}
        else: provenance[prefix + key] = {**attribution, 'kind': 'synthetic_example'}
    provenance[prefix + 'shares_outstanding'] = {**attribution, 'kind': 'reported_fact',
        'source_id': bundle['sources'][1]['id'], 'value_path': ['content', 'facts', 0, 'value'],
        'unit': 'shares', 'period': 'Synthetic period-end label, not independently verified'}
    return {'company_id': raw['company_id'], 'synthetic': True, 'as_of': LATER,
            'valuation': valuation, 'sources': bundle['sources'], 'provenance': provenance}


def share_row(result): return next(row for row in result['inputs'] if row['path'].endswith('shares_outstanding'))


class DisclosedShareUnitsTests(unittest.TestCase):
    def test_exact_scaling_preserves_raw_labels_definition_and_unverified_meaning(self):
        cases = [('10,256,000', '株', '10256000'), ('1.234', '千株', '1234.000'),
                 ('1025.6', '万株', '10256000.0'), ('1.25', '百万株', '1250000.00'),
                 ('2.50', 'shares', '2.50')]
        with patch('sqlite3.connect', side_effect=AssertionError('No database')), \
             patch('socket.create_connection', side_effect=AssertionError('No GET')):
            for raw, label, expected in cases:
                value = request(raw, label); original = deepcopy(value)
                with self.subTest(label=label):
                    bundle = normalize_disclosed_facts(value, now=NOW); fact = first(bundle)
                    self.assertEqual(fact['value'], expected)
                    self.assertEqual(fact['normalization']['explicit_unit_multiplier'], ADDED[label, 'shares'])
                    for key in original['facts'][0]: self.assertEqual(fact[key], original['facts'][0][key])
                    self.assertFalse(fact['financial_inputs_verified']); self.assertTrue(fact['meaning_review_required'])
                    self.assertEqual(bundle['theses'], []); self.assertEqual(bundle['sources'][0], original['source'])
                    self.assertEqual(value, original)

    def test_zero_fraction_and_sign_not_clamped_or_restricted_to_positive_integers(self):
        with localcontext() as context:
            context.prec = 3; context.traps[Inexact] = context.traps[Rounded] = True
            for raw, expected in [('0', '0'), ('-0.00', '0'), ('△1.25', '-1250.00'),
                                  ('▲2', '-2000'), ('+0.0001', '0.1000'),
                                  ('12345678901234567890.123456789', '12345678901234567890123.456789000')]:
                with self.subTest(raw=raw):
                    self.assertEqual(first(normalize_disclosed_facts(request(raw, '千株'), now=NOW))['value'], expected)
        for raw in (None, '', '-', '－'):
            with self.subTest(missing=raw):
                fact = first(normalize_disclosed_facts(request(raw), now=NOW))
                self.assertIsNone(fact['value']); self.assertFalse(fact['normalization']['raw_numeric_token_verified'])

    def test_dimensions_and_unregistered_aliases_are_not_inferred(self):
        for label, unit in [('株', 'JPY'), ('千株', 'JPY-per-share'), ('百万株', 'ratio'),
                            ('円', 'shares'), ('％', 'shares'), ('億株', 'shares'),
                            ('株式', 'shares'), ('million shares', 'shares')]:
            value = request('10', label, unit); original = deepcopy(value)
            with self.subTest(label=label, unit=unit), self.assertRaisesRegex(ValueError, 'mapping'):
                normalize_disclosed_facts(value, now=NOW)
            self.assertEqual(value, original)

    def test_same_quote_and_source_review_time_guards_remain_required(self):
        for key, changed in [('raw_value', '256'), ('raw_unit_label', '千株'),
                             ('raw_period_label', '2027年度'), ('basis_quote', '保存本文にない株式数')]:
            value = request(); value['facts'][0][key] = changed
            with self.subTest(key=key), self.assertRaises(ValueError): normalize_disclosed_facts(value, now=NOW)
        for section, field, stamp in [('source', 'retrieved_at', LATER), ('source', 'published_at', LATER),
                                      ('review', 'recorded_at', LATER),
                                      ('review', 'recorded_at', '2026-10-14T23:59:00+00:00')]:
            value = request(); value[section][field] = stamp; original = deepcopy(value)
            with self.subTest(section=section, field=field, stamp=stamp), self.assertRaises(ValueError):
                normalize_disclosed_facts(value, now=NOW)
            self.assertEqual(value, original)

    def test_reproduction_identity_and_arithmetic_tampering_keep_originals_immutable(self):
        value = request('10', '千株'); bundle = normalize_disclosed_facts(value, now=NOW); original = deepcopy(bundle)
        self.assertEqual(replay(bundle)['status'], 'reproduced')
        self.assertFalse(replay(bundle)['financial_inputs_verified'])
        later = normalize_disclosed_facts(value, now=LATER)['sources'][1]
        for key in ('id', 'content', 'metadata'): self.assertEqual(later[key], bundle['sources'][1][key])
        self.assertEqual(later['metadata']['normalization_version'], 1)
        for field in ('value', 'multiplier'):
            damaged = deepcopy(bundle); content = json.loads(damaged['sources'][1]['content'])
            if field == 'value': content['facts'][0]['value'] = '10'
            else: content['facts'][0]['normalization']['explicit_unit_multiplier'] = '1'
            damaged['sources'][1]['content'] = canonical_json(content)
            with self.subTest(field=field):
                self.assertEqual(replay(damaged)['status'], 'needs_review')
                self.assertIn('normalized_content_not_reproduced', replay(damaged)['reason_codes'])
        self.assertEqual(reproduce_disclosed_fact_source(bundle['sources'][1], {})['status'], 'needs_review')
        self.assertEqual(bundle, original)

    def test_model_numeric_match_is_not_meaning_probability_or_valuation_adoption(self):
        value = model_request(); original = deepcopy(value); result = audit_model_inputs(value); row = share_row(result)
        self.assertEqual(row['status'], 'source_value_matched'); self.assertEqual(row['source_value'], '10000')
        self.assertEqual(row['normalization_checks'][0]['status'], 'reproduced')
        self.assertEqual(row['meaning_review_status'], 'unreviewed')
        self.assertIn('definition_not_verified', row['meaning_checks'])
        self.assertFalse(result['financial_inputs_verified']); self.assertFalse(result['expected_value_available'])
        self.assertEqual(result['aggregation'], 'unweighted'); self.assertEqual(value, original)
        for damage, reason in [('kind', 'disclosed_fact_kind_mismatch'), ('value', 'source_value_mismatch'),
                               ('source', 'missing_origin_source_snapshot'), ('time', 'source_not_available_at_recording')]:
            damaged = model_request(); path = next(p for p in damaged['provenance'] if p.endswith('shares_outstanding'))
            if damage == 'kind': damaged['provenance'][path]['kind'] = 'issuer_guidance'
            elif damage == 'value': damaged['valuation']['scenarios'][0]['inputs']['shares_outstanding'] = '10001'
            elif damage == 'source': damaged['sources'] = damaged['sources'][1:]
            else: damaged['provenance'][path]['recorded_at'] = '2026-10-15T00:30:00+00:00'
            with self.subTest(damage=damage):
                row = share_row(audit_model_inputs(damaged))
                self.assertEqual(row['status'], 'needs_review'); self.assertIn(reason, row['reason_codes'])

    def test_same_numeric_count_does_not_merge_period_end_average_or_net_definitions(self):
        value = request('100'); second = deepcopy(value['facts'][0])
        second.update(id='period-average', concept='weighted_average_shares', definition='Synthetic period average, not period end.')
        value['facts'].append(second)
        bundle = normalize_disclosed_facts(value, now=NOW)
        facts = json.loads(bundle['sources'][1]['content'])['facts']
        self.assertEqual([f['value'] for f in facts], ['100', '100'])
        self.assertNotEqual(facts[0]['concept'], facts[1]['concept'])
        self.assertNotEqual(facts[0]['definition'], facts[1]['definition'])
        self.assertEqual(len(facts), 2)
        self.assertTrue(all(f['meaning_review_required'] and not f['financial_inputs_verified'] for f in facts))

    def test_legacy52_full_bundle_hashes_and_ids_and_existing_oku_outputs_unchanged(self):
        baseline = json.loads((ROOT / 'research/ir-oku-yen-normalization-2026-10-15/baseline.json').read_bytes())
        self.assertEqual(len(baseline['legacy_fixtures']), 52)
        for fixture in baseline['legacy_fixtures']:
            with self.subTest(unit=fixture['raw_unit_label'], kind=fixture['kind']):
                bundle = normalize_disclosed_facts(fixture['request'], now=fixture['now']); derived = bundle['sources'][1]
                self.assertEqual(sha256(canonical_json(bundle).encode()).hexdigest(), fixture['bundle_canonical_sha256'])
                self.assertEqual(derived['id'], fixture['derived_source_id'])
                self.assertEqual(sha256(derived['content'].encode()).hexdigest(), fixture['derived_content_sha256'])
        before_path = ROOT / 'research/ir-disclosed-share-unit-integration-2026-10-15/source-before/src/ir_agent/disclosed_facts.py'
        spec = importlib.util.spec_from_file_location('ir_agent._before_share_units', before_path)
        before = importlib.util.module_from_spec(spec); spec.loader.exec_module(before)
        self.assertEqual(_UNIT_MULTIPLIERS, {**before._UNIT_MULTIPLIERS, **ADDED})
        for kind in sorted(before._KINDS):
            value = fact_request('1,234.50', '億円', 'JPY', kind=kind)
            self.assertEqual(normalize_disclosed_facts(value, now=NOW), before.normalize_disclosed_facts(value, now=NOW))


if __name__ == '__main__': unittest.main()
