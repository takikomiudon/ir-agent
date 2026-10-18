"""Persist pre-question policy contracts and reply-linked decision reviews.

This is the project's implementation of ex-ante thesis/branch preservation, not
an investment strategy. Authoritative inputs are resolved from immutable records.
Transactions and actual send-state confirmation remain with Harness.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

from .decision import _flatten, _same, evaluate_decision, evaluate_ir_plan
from .models import integer, json_text, now_iso, object_value, source_origins, text, timestamp
from .store import Store
from .information_review import source_assessments, hold_result

CONTRACT_INPUTS = {'policy_id', 'policy_version', 'quote', 'synthetic', 'synthetic_position'}


class DecisionLifecycle:
    def __init__(self, store: Store):
        self.store = store

    def sources_for(self, thesis: dict, quote: dict) -> list[dict]:
        pending = list(thesis['evidence_ids'])
        if quote.get('source_id'):
            pending.append(text(quote['source_id'], 'decision quote source_id'))
        sources = {}
        while pending:
            source_id = pending.pop()
            if source_id in sources:
                continue
            source = self.store.source(source_id)
            if source['company_id'] != thesis['company_id']:
                raise ValueError('Decision source belongs to another company')
            sources[source_id] = source
            pending.extend(source_origins(source))
        return [sources[key] for key in sorted(sources)]

    def dependency_information_holds(self, thesis: dict, *, as_of: str) -> dict:
        """Read corrections for the selected thesis's complete source lineage.

        Original source classifications remain immutable. Callers making a new
        write use their trusted runtime cutoff, even for a historical request.
        """
        sources = self.sources_for(thesis, {})
        reviews = source_assessments(self.store, [source['id'] for source in sources], as_of=as_of)
        return {key: value for key, value in reviews.items()
                if value['information_status'] != 'public_clarification'}

    def dependency_source_information_holds(self, thesis: dict) -> dict:
        """Keep immutable source-publicity holds separate from reply reviews.

        Match decision._check_source_origins: an IR reply needs an explicit
        public_clarification, while other sources may omit classification.
        A later reply assessment never rewrites the original source snapshot.
        """
        holds = {}
        for source in self.sources_for(thesis, {}):
            classification = source.get('metadata', {}).get('information_status')
            if ((source['source_type'] == 'ir_reply' and classification != 'public_clarification')
                    or classification not in (None, 'public_disclosure', 'public_clarification')):
                holds[source['id']] = {
                    'source_id': source['id'], 'source_type': source['source_type'],
                    'information_status': classification, 'classification_origin': 'source_snapshot_metadata',
                    'source_sha256': sha256(json_text(source).encode()).hexdigest(),
                    'reason_code': 'source_information_held_for_review',
                }
        return holds

    def position_for(self, company_id: str, as_of: str, reference: dict) -> dict | None:
        position = self.store.declared_position_at(company_id, as_of)
        assumed = reference.get('synthetic_position')
        if assumed is not None:
            if reference.get('synthetic') is not True:
                raise ValueError('A synthetic position assumption cannot be used for a real decision')
            if timestamp(assumed['observed_at']) <= timestamp(as_of) and (
                    position is None or timestamp(assumed['observed_at']) > timestamp(position['observed_at'])):
                position = {'company_id': company_id, 'held': assumed['held'],
                            'observed_at': assumed['observed_at'], 'kind': 'synthetic_assumption'}
        return position

    def freeze(self, question: dict, thesis: dict, saved_at: str) -> dict:
        reference = deepcopy(object_value(question['decision_contract'], 'decision contract'))
        if set(reference) - CONTRACT_INPUTS:
            raise ValueError('Only policy reference, quote and synthetic flag may be supplied in a decision contract')
        text(reference.get('policy_id'), 'contract.policy_id')
        integer(reference.get('policy_version'), 'contract.policy_version', minimum=1)
        object_value(reference.get('quote', {}), 'contract.quote')
        if type(reference.get('synthetic', False)) is not bool:
            raise ValueError('contract.synthetic must be boolean')
        reference.setdefault('synthetic', False)
        reference.setdefault('quote', {})
        reference.setdefault('synthetic_position', None)
        assumed = reference['synthetic_position']
        if assumed is not None:
            object_value(assumed, 'contract.synthetic_position')
            if set(assumed) != {'held', 'observed_at'} or type(assumed['held']) is not bool:
                raise ValueError('A synthetic position requires only held and observed_at')
            if not reference['synthetic']:
                raise ValueError('A synthetic position assumption cannot be used for a real decision')
            if timestamp(assumed['observed_at']) > timestamp(question['created_at']):
                raise ValueError('A synthetic position assumption cannot postdate question creation')
        policy = self.store.decision_policy(reference['policy_id'], reference['policy_version'])
        registered_at = self.store.decision_policy_saved_at(reference['policy_id'], reference['policy_version'])
        if timestamp(question['created_at']) > timestamp(saved_at):
            raise ValueError('A question cannot be saved with a future creation time')
        if not reference['synthetic'] and timestamp(registered_at) > timestamp(question['created_at']):
            raise ValueError('Register the policy before creating a real precommitted question')
        position = self.position_for(thesis['company_id'], question['created_at'], reference)
        held = position['held'] if position is not None else None
        value = self.plan(question, thesis, reference, policy, held, question['created_at'], now=saved_at)
        reference.update(policy_snapshot=policy, policy_registered_at=registered_at,
                         frozen_at=saved_at, held=held, position_snapshot=position, preflight=value,
                         policy_sha256=sha256(json_text(policy).encode()).hexdigest())
        return reference

    def plan(self, question, thesis, reference, policy, held, as_of, *, now=None):
        value = evaluate_ir_plan({'synthetic': reference['synthetic'], 'as_of': as_of,
            'thesis': thesis, 'question': question, 'policy': policy, 'quote': reference['quote'],
            'sources': self.sources_for(thesis, reference['quote']), 'context': {'held': held}})
        checked_at = timestamp(now if now is not None else now_iso()).isoformat()
        historical = self.dependency_information_holds(thesis, as_of=as_of)
        current = self.dependency_information_holds(thesis, as_of=checked_at)
        if historical or current:
            value.update(question_value='needs_review',
                         dependency_information_holds={**historical, **current},
                         dependency_information_check={'as_of': as_of, 'checked_at': checked_at,
                                                       'as_of_holds': historical, 'current_holds': current})
            value['incomplete_reviews'] = list(dict.fromkeys(
                [*value['incomplete_reviews'], 'dependent_reply_information']))
        source_holds = self.dependency_source_information_holds(thesis)
        if source_holds:
            value.update(question_value='needs_review', dependency_source_information_holds=source_holds)
            value['incomplete_reviews'] = list(dict.fromkeys(
                [*value['incomplete_reviews'], 'dependent_source_information']))
        return value

    def verify_saved_contract(self, question: dict) -> dict:
        contract = question['decision_contract']
        stored = self.store.decision_policy(contract['policy_id'], contract['policy_version'])
        if stored != contract['policy_snapshot'] or sha256(json_text(stored).encode()).hexdigest() != contract['policy_sha256']:
            raise ValueError('Frozen decision policy differs from its registered version')
        return contract

    def validate_send(self, question: dict, sent_at: str, *, now: str | None = None) -> None:
        contract = self.verify_saved_contract(question)
        if not contract['synthetic'] and timestamp(sent_at) < timestamp(contract['frozen_at']):
            raise ValueError('A real sent-state record cannot predate its saved decision contract')
        position = self.position_for(question['company_id'], sent_at, contract)
        held = position['held'] if position is not None else None
        if held != contract['held']:
            raise ValueError('Position changed since question creation; prepare a new contract')
        result = self.plan(question, question['thesis_snapshot'], contract, contract['policy_snapshot'], held, sent_at,
                           now=now)
        if result['question_value'] != 'decision_distinguishing':
            raise ValueError('Decision contract needs review: no complete, distinguishing answer analysis at sending time')

    def validate_branch(self, question: dict, branch: dict) -> None:
        self.verify_saved_contract(question)
        if branch['action'] == 'unresolved':
            return
        if branch.get('thesis_status') not in ('intact', 'invalidated', 'uncertain'):
            raise ValueError('A contracted branch needs its precommitted thesis status')
        before = _flatten(question['thesis_snapshot']['valuation'])
        after = _flatten(branch.get('valuation', question['thesis_snapshot']['valuation']))
        changes = {key for key in before.keys() | after.keys()
                   if key not in before or key not in after or not _same(before[key], after[key])}
        if not changes <= set(question.get('parameter_paths', [])):
            raise ValueError('Reply branch changes valuation inputs outside precommitted parameter paths')

    def review_applied(self, question: dict, reply: dict, evaluation: dict, thesis: dict,
                       quote: dict, as_of: str, saved_at: str, review_request: dict | None = None) -> dict:
        contract = self.verify_saved_contract(question)
        branch = next(x for x in question['branches'] if x['id'] == evaluation['request']['branch_id'])
        self.validate_branch(question, branch)
        position = self.position_for(thesis['company_id'], as_of, contract)
        context = {'held': position['held'] if position is not None else None, 'position_snapshot': position,
                   'thesis_status': branch['thesis_status'], 'information_status': evaluation['information_status'],
                   'evidence_ids': thesis['evidence_ids']}
        inputs = {'synthetic': contract['synthetic'], 'as_of': as_of, 'thesis': thesis,
                  'policy': contract['policy_snapshot'], 'quote': object_value(quote, 'decision quote'),
                  'sources': self.sources_for(thesis, quote), 'context': context}
        result = evaluate_decision(inputs)
        classifications = source_assessments(self.store, [s['id'] for s in inputs['sources']],
                                            as_of=as_of, reply_id=reply['id'])
        holds = {key: value for key, value in classifications.items()
                 if value['information_status'] != 'public_clarification'}
        if holds:
            result = hold_result(result, reason='reply_information_corrected', reviews=holds)
        if classifications:
            context['information_review_versions'] = {key: value['version'] for key, value in classifications.items()}
        if position is None and result['reason_codes'] == ['position_not_verified']:
            result['reason_codes'] = ['position_history_unknown']
        identity = {'reply_id': reply['id'], 'evaluation_version': evaluation['version'],
                    'thesis_version': thesis['version'], 'recorded_at': as_of,
                    'policy_sha256': contract['policy_sha256'], 'quote': quote, 'context': context}
        if review_request is not None:
            identity['review_request_sha256'] = sha256(json_text(review_request).encode()).hexdigest()
        review = {'id': 'decision-' + sha256(json_text(identity).encode()).hexdigest()[:32],
                  'reply_id': reply['id'], 'evaluation_version': evaluation['version'], 'question_id': question['id'],
                  'company_id': thesis['company_id'], 'thesis_version': thesis['version'],
                  'policy_id': contract['policy_id'], 'policy_version': contract['policy_version'],
                  'recorded_at': as_of, 'source_ids': [source['id'] for source in inputs['sources']],
                  'source_sha256': {source['id']: sha256(json_text(source).encode()).hexdigest() for source in inputs['sources']},
                  'context': context, 'result': result}
        if review_request is not None:
            review.update(review_request=deepcopy(review_request),
                          review_request_sha256=identity['review_request_sha256'])
        self.store.put_decision_review(review, saved_at)
        return review

    def add_review(self, value: dict, now: str) -> dict:
        request = object_value(value, 'decision review request')
        if set(request) - {'reply_id', 'expected_thesis_version', 'recorded_at', 'decision_quote'}:
            raise ValueError('A saved decision review cannot override its frozen policy or unknown fields')
        text(request.get('reply_id'), 'review.reply_id')
        expected = integer(request.get('expected_thesis_version'), 'review.expected_thesis_version', minimum=1)
        as_of = text(request.get('recorded_at'), 'review.recorded_at')
        if timestamp(as_of) > timestamp(now):
            raise ValueError('Decision review cannot be recorded in the future')
        previous = self.store.decision_review_for_request(request)
        if previous is not None:
            return previous
        reply = self.store.reply(request['reply_id'])
        question = self.store.question(reply['question_id'])
        if 'decision_contract' not in question:
            raise ValueError('This question has no frozen decision policy contract')
        row = self.store.connection.execute('SELECT data FROM evaluations WHERE reply_id=? ORDER BY version DESC LIMIT 1', (reply['id'],)).fetchone()
        if row is None:
            raise ValueError('Evaluate the reply before reviewing its investment decision')
        evaluation = json.loads(row['data'])
        if not evaluation['applied']:
            raise ValueError('A held or unresolved reply cannot supply an applied investment decision')
        thesis = self.store.thesis(question['company_id'])
        if thesis['version'] != expected or expected != evaluation['thesis_version']:
            raise ValueError('Thesis changed; review fresh research instead of reusing stale IR branches')
        if timestamp(as_of) < timestamp(evaluation['request']['recorded_at']):
            raise ValueError('Decision review cannot predate reply evaluation')
        return self.review_applied(question, reply, evaluation, thesis,
                                   object_value(request.get('decision_quote', {}), 'review.decision_quote'), as_of, now,
                                   review_request=request)
