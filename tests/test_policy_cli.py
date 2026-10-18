"""CLI persistence and source-bound analysis across separate invocations."""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.cli import main
from test_decision import plan

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'


class PolicyCliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.db = self.directory / 'persistent.sqlite3'
        self.runtime_now = None

    def invoke(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with ExitStack() as context:
            context.enter_context(redirect_stdout(stdout)); context.enter_context(redirect_stderr(stderr))
            if self.runtime_now is not None:
                clock = context.enter_context(patch('ir_agent.harness.datetime', wraps=datetime))
                clock.now.return_value = self.runtime_now
                for name in ('ir_agent.cli.now_iso', 'ir_agent.store.now_iso', 'ir_agent.information_review.now_iso'):
                    context.enter_context(patch(name, return_value=self.runtime_now.isoformat()))
            code = main(['--db', str(self.db), *map(str, args)])
        return code, stdout.getvalue(), stderr.getvalue()

    def ok(self, *args):
        code, stdout, stderr = self.invoke(*args)
        self.assertEqual(code, 0, stderr); self.assertEqual(stderr, '')
        return json.loads(stdout)

    def save(self, name, value):
        path = self.directory / name
        path.write_text(json.dumps(value, ensure_ascii=False))
        return path

    def test_policy_question_reply_and_review_survive_reopening_database(self):
        self.runtime_now = datetime.fromisoformat('2026-10-09T10:00:00+09:00')
        value = plan()
        bundle = json.loads((EXAMPLES / 'demo.json').read_text())
        bundle['theses'] = [value['thesis']]
        bundle['sources'].append(value['sources'][1])
        self.ok('ingest', self.save('bundle.json', bundle))
        registered = self.ok('policy', 'add', self.save('policy.json', value['policy']))
        self.assertTrue(registered['added'])
        self.assertEqual(self.ok('policy', 'show', value['policy']['id'], '--version', 1), value['policy'])
        question = deepcopy(value['question'])
        question['decision_contract'] = {'policy_id': value['policy']['id'], 'policy_version': 1,
                                         'quote': value['quote'], 'synthetic': True,
                                         'synthetic_position': {'held': True, 'observed_at': '2026-10-09T09:59:00+09:00'}}
        draft = self.ok('question', 'add', self.save('question.json', question))
        self.assertEqual(draft['decision_contract']['preflight']['question_value'], 'decision_distinguishing')
        self.runtime_now = datetime.fromisoformat('2026-10-09T10:06:00+09:00')
        self.ok('question', 'mark-sent', question['id'], '--sent-at', '2026-10-09T10:05:00+09:00')
        self.runtime_now = datetime.fromisoformat('2026-10-09T16:00:00+09:00')
        self.ok('reply', 'add', EXAMPLES / 'reply.json')
        fresh = deepcopy(value['sources'][1]); fresh['id'] = 'price-after-reply'
        fresh['retrieved_at'] = '2026-10-09T16:59:00+09:00'
        fresh['metadata'].update(price_jpy='1600', observed_at=fresh['retrieved_at'])
        self.runtime_now = datetime.fromisoformat('2026-10-09T16:59:00+09:00')
        self.ok('ingest', self.save('price.json', {'schema_version': 1, 'sources': [fresh]}))
        quote = deepcopy(value['quote'])
        quote.update(source_id=fresh['id'], price_jpy='1600', retrieved_at=fresh['retrieved_at'], observed_at=fresh['retrieved_at'])
        evaluation = json.loads((EXAMPLES / 'reply-evaluation.json').read_text())
        evaluation.update(expected_thesis_version=1, decision_quote=quote)
        self.runtime_now = datetime.fromisoformat('2026-10-09T17:00:00+09:00')
        applied = self.ok('reply', 'evaluate', self.save('evaluation.json', evaluation))
        self.assertEqual(applied['precommitted_action'], 'buy_review')
        self.assertEqual(applied['action'], 'exit_review')
        review = self.ok('decision-review', 'show', applied['decision_review_id'])
        self.assertEqual(review['result']['reason_codes'], ['valuation_target_reached'])
        self.assertEqual(self.ok('reply', 'show', 'demo-reply-cost')['evaluations'][0], applied)
        self.assertEqual(self.ok('status')['decision_reviews'], 1)
        correction = {'reply_id': 'demo-reply-cost', 'expected_version': 0,
                      'information_status': 'unclear', 'basis_quote': '採用費',
                      'rationale': 'The public basis needs to be checked again.',
                      'recorded_at': '2026-10-15T00:00:00+00:00'}
        correction['basis_quote'] = json.loads((EXAMPLES / 'reply.json').read_text())['raw_text'][:10]
        self.runtime_now = datetime.fromisoformat('2026-10-15T00:00:00+00:00')
        self.ok('reply', 'classify', self.save('classification.json', correction))
        self.assertEqual(self.ok('decision-review', 'show', review['id'])['result']['proposed_action'], 'unresolved')
        self.assertEqual(self.ok('reply', 'show', 'demo-reply-cost')['evaluations'][0]['action'], 'unresolved')
        self.assertEqual(self.ok('inbox')['replies_for_review'][0]['status'], 'requires_information_review')

    def test_json_duplicate_keys_are_rejected_before_any_policy_is_added(self):
        path = self.directory / 'ambiguous.json'
        path.write_text('{"id":"first","id":"second"}')
        code, stdout, stderr = self.invoke('policy', 'add', path)
        self.assertEqual(code, 1); self.assertEqual(stdout, '')
        self.assertIn('Duplicate JSON key', stderr); self.assertNotIn('Traceback', stderr)
        self.assertEqual(self.ok('status')['decision_policies'], 0)

    def test_information_value_and_as_of_observations_remain_distinct(self):
        info = self.ok('information-value', EXAMPLES / 'information-value.json')
        self.assertEqual(info['sample_information']['evsi'], '30.00')
        observations = self.ok('observations', 'summarize', EXAMPLES / 'ir-observations.json',
                               '--as-of', '2026-10-15T10:00:00+09:00')
        self.assertEqual(observations['calibration_status'], 'needs_calibration')
        self.assertEqual(observations['status'], 'observations_only')
        self.assertEqual(self.ok('status')['theses'], 0)
        code, stdout, stderr = self.invoke('observations', 'summarize', self.save('no-records.json', {}))
        self.assertEqual(code, 1); self.assertEqual(stdout, ''); self.assertNotIn('Traceback', stderr)

    def test_quote_normalization_can_be_persisted_and_repeated_without_new_sources(self):
        source = json.loads((EXAMPLES / 'quote-source.json').read_text())
        normalized = self.ok('normalize-quote', EXAMPLES / 'quote-source.json')
        self.ok('ingest', self.save('market-bundle.json', {'schema_version': 1,
                'companies': [{'id': source['company_id'], 'name': 'Synthetic company'}], 'sources': [source]}))
        saved = self.ok('quote', 'from-source', source['id'])
        self.assertEqual(saved['quote'], normalized['quote'])
        count = self.ok('status')['sources']
        repeated = self.ok('quote', 'from-source', source['id'])
        self.assertEqual(repeated['quote'], saved['quote'])
        self.assertEqual(self.ok('status')['sources'], count)
        self.assertEqual(saved['quote']['observation_precision'], 'day')

    def test_model_input_audit_keeps_synthetic_forecasts_distinct_and_does_not_write_a_thesis(self):
        result = self.ok('model-inputs', EXAMPLES / 'model-input-review.json')
        self.assertEqual(result['status'], 'synthetic_example')
        self.assertEqual(len(result['required_paths']), 9)
        self.assertEqual(result['missing_paths'], [])
        self.assertTrue(result['meaning_review_required'])
        self.assertFalse(result['financial_inputs_verified'])
        self.assertEqual(self.ok('status')['theses'], 0)

    def test_fact_normalization_preserves_quotes_and_does_not_import_the_bundle(self):
        request = json.loads((EXAMPLES / 'disclosed-facts.json').read_text())
        result = self.ok('normalize-facts', EXAMPLES / 'disclosed-facts.json')
        self.assertEqual(result['sources'][0], request['source'])
        derived = result['sources'][1]
        facts = json.loads(derived['content'])['facts']
        self.assertEqual([fact['value'] for fact in facts], ['63000000000', '27.45', '0.08'])
        self.assertEqual(facts[1]['basis_quote'], request['facts'][1]['basis_quote'])
        self.assertFalse(derived['metadata']['financial_inputs_verified'])
        self.assertEqual(result['theses'], [])
        status = self.ok('status')
        self.assertEqual(status['sources'], 0)
        self.assertEqual(status['theses'], 0)
        invalid = deepcopy(request)
        invalid['facts'][0]['location'] = 'unstructured location'
        code, stdout, stderr = self.invoke('normalize-facts', self.save('invalid-facts.json', invalid))
        self.assertEqual(code, 1)
        self.assertEqual(stdout, '')
        self.assertIn('location', stderr)
        self.assertNotIn('Traceback', stderr)

    def test_screen_pass_is_only_a_research_candidate(self):
        result = self.ok('screen', EXAMPLES / 'screening.json')
        self.assertEqual(result['status'], 'candidate_for_research')
        self.assertEqual(self.ok('status')['companies'], 0)

    def test_probability_scoring_keeps_zero_event_infinite_and_does_not_claim_validation(self):
        value = json.loads((EXAMPLES / 'probability-scoring.json').read_text())
        result = self.ok('score-probabilities', EXAMPLES / 'probability-scoring.json')
        self.assertEqual(result['status'], 'calculation_only')
        self.assertEqual(result['brier_loss']['value'], '0.38')
        self.assertFalse(result['verification']['prior_prediction_verified'])
        self.assertFalse(result['verification']['calibration_verified'])
        labels = value['categories']
        value['probabilities'] = {label: '1' if label == labels[0] else '0' for label in labels}
        value['observed_category'] = labels[1]
        result = self.ok('score-probabilities', self.save('zero-observed-probability.json', value))
        self.assertEqual(result['log_loss'], {'status': 'positive_infinity', 'value': None, 'unit': 'nats'})
        self.assertEqual(result['brier_loss']['value'], '2')
        self.assertEqual(self.ok('status')['theses'], 0)


if __name__ == '__main__': unittest.main()
