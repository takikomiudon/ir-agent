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

CONTRACT_INPUTS = {'policy_id', 'policy_version', 'quote', 'synthetic', 'synthetic_position',
                   'research_baseline_id'}


def _digest(value):
    return sha256(json_text(value).encode('utf-8')).hexdigest()


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

    def public_information_sources_for(self, question: dict) -> list[dict]:
        """Resolve review-only roots without adding them to financial evidence."""
        from .public_information_review import validate_public_information_review
        review = validate_public_information_review(question['public_information_review'],
                                                    created_at=question['created_at'])
        roots = {item['source_id'] for item in review['sources']}
        pending, visited, sources = list(roots), set(), {}
        while pending:
            identity = pending.pop()
            if identity in visited:
                continue
            visited.add(identity)
            try:
                source = self.store.source(identity)
            except ValueError:
                if identity in roots:
                    raise ValueError('Unknown public information review source') from None
                # The pure check and PIT reader retain a missing-origin hold.
                continue
            sources[identity] = source
            pending.extend(source_origins(source))
        return [sources[key] for key in sorted(sources)]

    def review_public_information(self, question: dict, *, as_of: str, now: str) -> dict:
        """Keep claimed review time, saved presence and current corrections apart."""
        from .public_information_review import check_public_information_review
        if timestamp(as_of) > timestamp(now):
            raise ValueError('Public information review boundary exceeds trusted runtime')
        sources = self.public_information_sources_for(question)
        check = check_public_information_review(question, sources, as_of=as_of)
        reviewed = question['public_information_review']['reviewed_at']
        reasons = check['reason_codes']
        availability = {}
        source_map = {source['id']: source for source in sources}
        from .availability import RecordAvailability
        ledger = RecordAvailability(self.store.connection)
        # The pure check already traversed this complete DAG iteratively.
        # Check each saved snapshot once, without recursing through it again.
        for identity in check['source_closure_ids']:
            result = ledger.at('source', identity, source_map[identity], as_of=reviewed,
                               knowledge_at=reviewed, now=now)
            availability[identity] = result
            if result['available'] is not True:
                reasons.append('public_information_review_source_availability_unresolved')
        # Do not let a same-company source impersonate another company's reply
        # classification subject through metadata.reply_id.
        for source in sources:
            if source['source_type'] != 'ir_reply':
                continue
            subject = source.get('metadata', {}).get('reply_id')
            if not subject:
                reasons.append('public_information_review_reply_binding_unknown')
                continue
            subject = text(subject, 'public review reply_id')
            reply = self.store.reply(subject)
            origin_id = text(reply.get('question_id'), 'public review reply.question_id')
            origin_question = self.store.question(origin_id)
            if reply.get('id') != subject or origin_question.get('id') != origin_id:
                raise ValueError('Public information review reply/question identity mismatch')
            if origin_question.get('company_id') != question['company_id']:
                raise ValueError('Public information review reply belongs to another company')
            if source['content'] != reply.get('raw_text'):
                raise ValueError('Public information review source differs from its saved reply')
        corrections = {}
        for label, boundary in (('at_review', reviewed), ('at_boundary', as_of), ('at_runtime', now)):
            corrections[label] = source_assessments(self.store, list(source_map), as_of=boundary)
            if any(item['information_status'] != 'public_clarification'
                   for item in corrections[label].values()):
                reasons.append('public_information_review_information_held_for_review')
        check.update(availability_at_review=availability, information_reviews=corrections,
                     checked_at=timestamp(now).isoformat(),
                     reason_codes=list(dict.fromkeys(reasons)))
        return check

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

    def _research_baseline(self, reference):
        """Resolve only immutable history, never the baseline's current_view."""
        identity = text(reference.get('research_baseline_id'), 'contract.research_baseline_id')
        row = self.store.connection.execute(
            'SELECT * FROM research_decision_reviews WHERE id=?', (identity,)).fetchone()
        if row is None:
            raise ValueError('Unknown research baseline ID')
        record = object_value(json.loads(row['data']), 'research baseline record')
        for key in ('id', 'company_id', 'thesis_version', 'policy_id', 'policy_version'):
            if record.get(key) != row[key]:
                raise ValueError('Research baseline row identity differs from its record')
        timestamp(row['first_saved_at'], 'baseline.first_saved_at')
        timestamp(record.get('recorded_at'), 'baseline.recorded_at')
        binding = {'id': identity, 'record_sha256': _digest(record),
                   'first_saved_at': row['first_saved_at'], 'recorded_at': record['recorded_at'],
                   'basis': deepcopy(object_value(record.get('basis'), 'baseline.basis')),
                   'result_status': object_value(record.get('result'), 'baseline.result').get('status')}
        return record, binding

    def _baseline_preflight(self, question, thesis, reference, policy, checked_at):
        record, binding = self._research_baseline(reference)
        if reference.get('research_baseline_binding') != binding:
            raise ValueError('Frozen research baseline binding differs from its saved history')
        created = timestamp(question['created_at'])
        if max(timestamp(binding['first_saved_at']), timestamp(binding['recorded_at'])) > created:
            raise ValueError('Research baseline must be saved and recorded before question creation')
        if (record['company_id'] != question['company_id'] or
                record['thesis_version'] != thesis['version'] or
                record.get('thesis_sha256') != _digest(thesis) or
                _digest(record.get('thesis_snapshot')) != _digest(thesis)):
            raise ValueError('Research baseline must match the question company and thesis snapshot')
        if (record['policy_id'] != policy['id'] or record['policy_version'] != policy['version'] or
                record.get('policy_sha256') != _digest(policy) or
                _digest(record.get('policy_snapshot')) != _digest(policy)):
            raise ValueError('Research baseline must match the frozen decision policy')
        if record.get('synthetic') is not reference['synthetic']:
            raise ValueError('Research baseline synthetic flag differs from the question contract')
        if _digest(record.get('quote')) != _digest(reference['quote']):
            raise ValueError('Research baseline must use the same quote snapshot')
        sources = {s['id']: s for s in self.sources_for(thesis, reference['quote'])}
        snapshots = record.get('source_snapshots', [])
        if (not isinstance(snapshots, list) or
                any(not isinstance(s, dict) or not isinstance(s.get('id'), str) for s in snapshots)):
            raise ValueError('Research baseline source snapshots are malformed')
        saved_sources = {s['id']: s for s in snapshots}
        hashes = {identity: _digest(source) for identity, source in sources.items()}
        if (len(saved_sources) != len(snapshots) or set(record.get('source_ids', [])) != set(sources) or
                set(saved_sources) != set(sources) or record.get('source_sha256') != hashes or
                any(_digest(saved_sources[key]) != hashes[key] for key in sources)):
            raise ValueError('Research baseline source closure or snapshot SHA differs')
        has_ir = any(s['source_type'] == 'ir_reply' for s in sources.values())
        basis = binding['basis']
        if (basis.get('kind') != 'saved_research' or
                (has_ir and (basis.get('public_only') is not False or basis.get('has_IR_reply_origin') is not True))):
            raise ValueError('Research baseline must retain its saved research/IR origin distinction')
        for reply in record.get('reply_bindings', {}).values():
            if reply.get('question_snapshot', {}).get('id') == question['id']:
                raise ValueError('Research baseline cannot contain this question own reply')
        reasons = []
        if binding['result_status'] != 'reviewed':
            reasons.append('research_baseline_unresolved')
        # Missing historical knowledge stays a hold; it never gains an earlier receipt.
        selected = self.store.thesis_view(question['company_id'], as_of=question['created_at'],
            knowledge_at=question['created_at'], mode='pit', now=checked_at)['record']
        if selected is None or _digest(selected) != _digest(thesis):
            reasons.append('research_baseline_thesis_availability_unresolved')
        for source in sources.values():
            if (not self.store.source_available(source, as_of=question['created_at'], now=checked_at) or
                    not self.store.source_available(source, as_of=record['recorded_at'], now=checked_at)):
                reasons.append('research_baseline_source_availability_unresolved')
        prior = record.get('position_snapshot')
        historical = self.store.declared_position_at(question['company_id'], record['recorded_at'])
        position = self.position_for(question['company_id'], question['created_at'], reference)
        if prior is None or historical is None or position is None:
            reasons.append('research_baseline_position_unknown')
        elif (prior.get('company_id') != question['company_id'] or
                prior.get('held') != historical['held'] or prior.get('held') != position['held']):
            raise ValueError('Research baseline effective position differs from the question')
        # Include quote-only IR ancestors. Price/position remain at the existing sent_at
        # boundary; information corrections are also checked at trusted runtime now.
        for as_of in (question['created_at'], checked_at):
            reviews = source_assessments(self.store, list(sources), as_of=as_of)
            if any(item['information_status'] != 'public_clarification' for item in reviews.values()):
                reasons.append('research_baseline_information_held_for_review')
            consumed = record.get('context', {}).get('information_review_versions', {})
            if any(consumed.get(identity) != item['version'] for identity, item in reviews.items()):
                reasons.append('research_baseline_information_review_changed')
        for source in sources.values():
            status = source.get('metadata', {}).get('information_status')
            if ((source['source_type'] == 'ir_reply' and status != 'public_clarification') or
                    status not in (None, 'public_disclosure', 'public_clarification')):
                reasons.append('research_baseline_source_information_held_for_review')
        return list(dict.fromkeys(reasons))

    def freeze(self, question: dict, thesis: dict, saved_at: str) -> dict:
        reference = deepcopy(object_value(question['decision_contract'], 'decision contract'))
        if set(reference) - CONTRACT_INPUTS:
            raise ValueError('Only policy reference, quote, synthetic position and research baseline ID may be supplied in a decision contract')
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
        if 'research_baseline_id' in reference:
            _, reference['research_baseline_binding'] = self._research_baseline(reference)
        value = self.plan(question, thesis, reference, policy, held, question['created_at'], now=saved_at)
        reference.update(policy_snapshot=policy, policy_registered_at=registered_at,
                         frozen_at=saved_at, held=held, position_snapshot=position, preflight=value,
                         policy_sha256=sha256(json_text(policy).encode()).hexdigest())
        return reference

    def plan(self, question, thesis, reference, policy, held, as_of, *, now=None):
        sources = self.sources_for(thesis, reference['quote'])
        if 'public_information_review' in question:
            # This pool serves the plan only. Thesis/valuation evidence and
            # sources_for's other callers retain their existing roots.
            combined = {source['id']: source for source in sources}
            combined.update({source['id']: source for source in self.public_information_sources_for(question)})
            sources = [combined[key] for key in sorted(combined)]
        value = evaluate_ir_plan({'synthetic': reference['synthetic'], 'as_of': as_of,
            'thesis': thesis, 'question': question, 'policy': policy, 'quote': reference['quote'],
            'sources': sources, 'context': {'held': held}})
        checked_at = timestamp(now if now is not None else now_iso()).isoformat()
        if 'public_information_review' in question:
            check = self.review_public_information(question, as_of=as_of, now=checked_at)
            value['public_information_review_check'] = check
            if check['reason_codes']:
                value['question_value'] = 'needs_review'
                value['incomplete_reviews'] = list(dict.fromkeys(
                    [*value['incomplete_reviews'], 'public_information_review_binding']))
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
        if 'research_baseline_id' in reference:
            reasons = self._baseline_preflight(question, thesis, reference, policy, checked_at)
            if reasons:
                value.update(question_value='needs_review', research_baseline_reason_codes=reasons)
                value['incomplete_reviews'] = list(dict.fromkeys(
                    [*value['incomplete_reviews'], 'research_baseline']))
        return value

    def verify_saved_contract(self, question: dict) -> dict:
        contract = question['decision_contract']
        stored = self.store.decision_policy(contract['policy_id'], contract['policy_version'])
        if stored != contract['policy_snapshot'] or sha256(json_text(stored).encode()).hexdigest() != contract['policy_sha256']:
            raise ValueError('Frozen decision policy differs from its registered version')
        if 'research_baseline_id' in contract:
            _, binding = self._research_baseline(contract)
            if binding != contract.get('research_baseline_binding'):
                raise ValueError('Frozen research baseline binding differs from its saved history')
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
