"""Immutable, reply-independent price reviews of saved research.

These are project persistence checks around the existing decision evaluator.
They do not certify financial meaning, issuer authenticity, market publicity,
reviewer assessments or broker holdings, and never create orders or questions.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json

from .availability import RecordAvailability
from .decision import (
    _check_decision_quote_fields, _check_decision_quote_source,
    evaluate_decision, validate_decision_policy,
)
from .decision_lifecycle import DecisionLifecycle
from .information_review import (
    _current_quote_check, _current_thesis_check, source_assessments,
)
from .models import (
    JST, day, integer, json_text, object_value, source_origins, strings, text,
    timestamp, validate_source, validate_thesis,
)
from .valuation import _number

SCHEMA = """
CREATE TABLE IF NOT EXISTS research_decision_reviews (
    id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id),
    thesis_version INTEGER NOT NULL, policy_id TEXT NOT NULL,
    policy_version INTEGER NOT NULL, request_sha256 TEXT NOT NULL,
    data TEXT NOT NULL, first_saved_at TEXT NOT NULL,
    FOREIGN KEY(company_id,thesis_version) REFERENCES theses(company_id,version),
    FOREIGN KEY(policy_id,policy_version) REFERENCES decision_policies(id,version)
);
"""
_REQUIRED = {'id', 'company_id', 'expected_thesis_version', 'policy_id',
             'policy_version', 'decision_quote', 'assessment'}


def _clock(value=None):
    return timestamp(value.isoformat() if isinstance(value, datetime) else
                     value if value is not None else datetime.now(timezone.utc).isoformat(), 'trusted runtime')


def _digest(value):
    return sha256(json_text(value).encode('utf-8')).hexdigest()


def _request(value):
    request = deepcopy(object_value(value, 'research decision review'))
    if not _REQUIRED <= set(request) or set(request) - _REQUIRED - {'synthetic'}:
        raise ValueError('Research decision review has missing or unknown fields')
    for key in ('id', 'company_id', 'policy_id'):
        text(request[key], 'review.' + key)
    for key in ('expected_thesis_version', 'policy_version'):
        integer(request[key], 'review.' + key, minimum=1)
    if type(request.get('synthetic', False)) is not bool:
        raise ValueError('review.synthetic must be boolean')
    object_value(request['decision_quote'], 'review.decision_quote')
    assessment = object_value(request['assessment'], 'review.assessment')
    if set(assessment) != {'thesis_status', 'evidence_ids', 'reviewer', 'rationale'}:
        raise ValueError('Assessment requires thesis_status, evidence_ids, reviewer and rationale')
    if assessment['thesis_status'] not in ('intact', 'invalidated', 'uncertain'):
        raise ValueError('Assessment thesis_status must be intact, invalidated or uncertain')
    strings(assessment['evidence_ids'], 'assessment.evidence_ids', nonempty=True)
    if len(set(assessment['evidence_ids'])) != len(assessment['evidence_ids']):
        raise ValueError('Assessment evidence IDs must be unique')
    text(assessment['reviewer'], 'assessment.reviewer')
    text(assessment['rationale'], 'assessment.rationale')
    return request


def _hold(result, reasons):
    held = deepcopy(result)
    held.update(status='unresolved', proposed_action='unresolved')
    held['reason_codes'] = list(dict.fromkeys([*held.get('reason_codes', []), *reasons]))
    return held


def _sources(store, roots, company_id):
    """Collect all saved parents, detecting cycles independently of timing."""
    found, missing, active, visited = {}, set(), set(), set()
    pending = [(identity, False) for identity in reversed(roots)]
    while pending:
        identity, leaving = pending.pop()
        if leaving:
            active.remove(identity); visited.add(identity)
            continue
        if identity in active:
            raise ValueError('Cyclic source provenance is not valid research decision evidence')
        if identity in visited:
            continue
        row = store.connection.execute('SELECT data FROM sources WHERE id=?', (identity,)).fetchone()
        if row is None:
            missing.add(identity); visited.add(identity)
            continue
        source = json.loads(row['data'])
        validate_source(source)  # Validate without adding defaults to the saved snapshot binding.
        if source['id'] != identity or source['company_id'] != company_id:
            raise ValueError('Research decision source identity/company mismatch')
        found[identity] = source
        active.add(identity); pending.append((identity, True))
        pending.extend((parent, False) for parent in reversed(source_origins(source)))
    return {key: found[key] for key in sorted(found)}, sorted(missing)


def _reply_bindings(store, sources, company_id, now, classifications):
    """Keep original reply/question bindings distinct from later assessments."""
    bindings, reasons = {}, []
    ledger = RecordAvailability(store.connection)
    for source in sources.values():
        if source['source_type'] != 'ir_reply':
            continue
        reply_id = source.get('metadata', {}).get('reply_id')
        if not isinstance(reply_id, str) or not reply_id.strip():
            reasons.append('origin_reply_identity_missing'); continue
        raw = store.connection.execute('SELECT data FROM replies WHERE id=?', (reply_id,)).fetchone()
        if raw is None:
            reasons.append('origin_reply_unresolved'); continue
        reply = json.loads(raw['data'])
        raw = store.connection.execute('SELECT data FROM questions WHERE id=?', (reply.get('question_id'),)).fetchone()
        if raw is None:
            reasons.append('origin_question_unresolved'); continue
        question = json.loads(raw['data'])
        if (reply.get('id') != reply_id or question.get('id') != reply.get('question_id')
                or question.get('company_id') != company_id):
            raise ValueError('Origin reply/question identity or company mismatch')
        if source['content'] != reply.get('raw_text'):
            raise ValueError('Origin IR source content differs from saved reply')
        availability = {
            kind: ledger.at(kind, record['id'], record, as_of=now,
                            knowledge_at=now, now=now)
            for kind, record in (('reply', reply), ('question', question))}
        latest = classifications.get(reply_id)
        status = latest['information_status'] if latest else source.get('metadata', {}).get('information_status')
        if status != 'public_clarification':
            reasons.append('origin_reply_information_held_or_unknown')
        if any(check['available'] is not True for check in availability.values()):
            reasons.append('origin_reply_or_question_availability_unresolved')
        bindings[reply_id] = {'reply_snapshot': reply, 'reply_sha256': _digest(reply),
            'question_snapshot': question, 'question_sha256': _digest(question),
            'availability': availability, 'effective_information_status': status,
            'classification_basis': 'saved_reply_assessment' if latest else 'immutable_IR_source_metadata',
            'raw_reply_initial_information_status': reply.get('information_status')}
    return bindings, reasons


def current_research_decision_view(store, review, *, now=None):
    """Render current holds without updating or upgrading the saved result."""
    checked_at = _clock(now).isoformat()
    timing_input = {**review['result'], 'quote': review['quote'],
                    'policy_snapshot': review['policy_snapshot']}
    quote_check = _current_quote_check(timing_input, checked_at)
    thesis_check = _current_thesis_check(store, review, checked_at)
    try:
        selected = store.thesis_view(review['company_id'], as_of=checked_at,
                                    knowledge_at=checked_at, mode='pit', now=checked_at)
        current_thesis = selected['record']
        thesis_check['strict_current_selected_version'] = current_thesis['version'] if current_thesis else None
        matches = (current_thesis is not None and current_thesis['version'] == review['thesis_version']
                   and _digest(current_thesis) == review['thesis_sha256'])
        thesis_check['saved_snapshot_and_availability'] = 'matched' if matches else 'unresolved'
        if not matches:
            thesis_check['status'] = 'unknown' if current_thesis is None else 'mismatch'
            thesis_check['reason_codes'] = list(dict.fromkeys([
                *thesis_check['reason_codes'], 'current_thesis_snapshot_or_availability_unresolved']))
    except ValueError:
        thesis_check.update(status='unknown', saved_snapshot_and_availability='unresolved')
        thesis_check['reason_codes'] = list(dict.fromkeys([
            *thesis_check['reason_codes'], 'current_thesis_snapshot_or_availability_unresolved']))
    due = day(review['thesis_snapshot']['next_review_date']) <= timestamp(checked_at).astimezone(JST).date()
    position = store.declared_position_at(review['company_id'], checked_at)
    prior = review['position_snapshot']
    position_ok = (position is not None and prior is not None and position['held'] == prior['held'])
    position_check = {'checked_at': checked_at, 'status': 'matched' if position_ok else 'unknown' if position is None else 'changed',
                      'position_snapshot': position, 'reason_codes': [] if position_ok else ['position_history_unknown' if position is None else 'reviewed_position_changed']}
    information_reasons, changes = [], {}
    try:
        latest = source_assessments(store, review['source_ids'], as_of=checked_at)
        consumed = review['context']['information_review_versions']
        changes = {key: value for key, value in latest.items()
                   if value['information_status'] != 'public_clarification' or consumed.get(key) != value['version']}
        if changes:
            information_reasons.append('dependent_reply_information_changed')
        for identity, digest in review['source_sha256'].items():
            source = store.source(identity)
            if _digest(source) != digest:
                information_reasons.append('saved_source_snapshot_changed')
            if not store.source_available(source, as_of=checked_at, now=checked_at):
                information_reasons.append('current_source_availability_unresolved')
    except ValueError:
        information_reasons.append('current_source_information_unresolved')
    requirements = []
    if information_reasons:
        requirements.append('requires_information_review')
    if thesis_check['status'] != 'matched' or due:
        requirements.append('requires_thesis_review')
    if not position_ok:
        requirements.append('requires_position_review')
    if quote_check['status'] != 'fresh':
        requirements.append('requires_price_review')
    reasons = [*information_reasons, *thesis_check['reason_codes'],
               *(['thesis_review_due'] if due else []),
               *position_check['reason_codes'], *quote_check['reason_codes']]
    result = _hold(review['result'], reasons) if requirements else deepcopy(review['result'])
    return {'checked_at': checked_at, 'result': result,
            'historical_result': deepcopy(review['result']),
            'current_validity': requirements[0] if requirements else 'no_recorded_recheck_requirement',
            'current_review_requirements': requirements, 'current_quote_check': quote_check,
            'current_thesis_check': {**thesis_check, 'management_review_due': due},
            'current_position_check': position_check, 'information_review_changes': changes,
            'information_reason_codes': list(dict.fromkeys(information_reasons))}


class ResearchDecisions:
    def __init__(self, store):
        self.store, self.db = store, store.connection

    def _row(self, identity):
        return self.db.execute('SELECT * FROM research_decision_reviews WHERE id=?', (identity,)).fetchone()

    def _envelope(self, row, *, now, added=False):
        record = json.loads(row['data'])
        return {'record': record, 'first_saved_at': row['first_saved_at'], 'added': added,
                'current_view': current_research_decision_view(self.store, record, now=now)}

    def show_review(self, identity, *, now=None):
        text(identity, 'research review ID')
        row = self._row(identity)
        if row is None:
            raise ValueError('Unknown research decision review')
        return self._envelope(row, now=now)

    def add_review(self, value, *, now=None):
        request = _request(value)
        digest = _digest(request)
        with self.store._record_write():
            current = _clock(now)
            as_of = current.isoformat()
            previous = self._row(request['id'])
            if previous is not None:
                if previous['request_sha256'] != digest or json.loads(previous['data'])['request'] != request:
                    raise ValueError('Research review ID is immutable; changed request needs a new ID')
                return self._envelope(previous, now=current)
            self.store.company(request['company_id'])
            thesis = self.store.thesis(request['company_id'])
            if thesis is None or thesis['version'] != request['expected_thesis_version']:
                raise ValueError('Research review expected version must match the current latest thesis')
            thesis = validate_thesis(thesis)
            policy = validate_decision_policy(self.store.decision_policy(request['policy_id'], request['policy_version']))
            registered = self.store.decision_policy_saved_at(request['policy_id'], request['policy_version'])
            if max(timestamp(policy['recorded_at']), timestamp(registered)) > current:
                raise ValueError('Research review policy is unavailable at current runtime')
            assessment = request['assessment']
            if not set(assessment['evidence_ids']) <= set(thesis['evidence_ids']):
                raise ValueError('Assessment evidence must belong to the selected latest thesis')
            quote = request['decision_quote']
            if quote.get('price_jpy') is not None and _number(quote['price_jpy'], 'quote.price_jpy') <= 0:
                raise ValueError('A supplied research decision quote price must be positive and finite')
            if quote.get('company_id') is not None and quote['company_id'] != thesis['company_id']:
                raise ValueError('Research decision quote belongs to another company')
            if quote.get('currency') is not None and quote['currency'] != 'JPY':
                raise ValueError('Research decision quote must use JPY')
            roots = list(thesis['evidence_ids'])
            if quote.get('source_id') is not None:
                roots.append(text(quote['source_id'], 'quote.source_id'))
            roots = list(dict.fromkeys(roots))
            sources, missing = _sources(self.store, roots, thesis['company_id'])
            # Defaults belong only to calculation copies, never to raw snapshot
            # commitments or their original availability receipt bindings.
            calculation_sources = {key: validate_source(source) for key, source in sources.items()}
            synthetic = request.get('synthetic', False)
            if not synthetic and (thesis.get('synthetic') is True or
                    any(s.get('metadata', {}).get('synthetic') is True for s in sources.values()) or
                    any(p.get('kind') == 'synthetic_example' for p in policy['parameter_sources'].values())):
                raise ValueError('Synthetic input ancestry requires an explicit synthetic research review')
            # These checks precede policy/position early returns in pure decision.
            quote_issue = _check_decision_quote_source(quote, calculation_sources, thesis['company_id'], current)
            market_source = calculation_sources.get(quote.get('source_id'))
            field_issue = None
            # Missing fields may remain unresolved, but supplied contradictions
            # must not hide behind that missingness or an unrelated policy gate.
            for field in ('observed_at', 'retrieved_at'):
                if quote.get(field) is not None:
                    timestamp(quote[field], 'quote.' + field)
            if (quote.get('observed_at') is not None and quote.get('retrieved_at') is not None
                    and timestamp(quote['observed_at']) > timestamp(quote['retrieved_at'])):
                raise ValueError('A quote cannot be retrieved before its observation')
            if market_source is not None:
                if market_source['source_type'] != 'market_data':
                    raise ValueError('Quote must be backed by a market-data source')
                if (quote.get('retrieved_at') is not None
                        and timestamp(quote['retrieved_at']) != timestamp(market_source['retrieved_at'])):
                    raise ValueError('Quote retrieval time differs from its saved source')
                field_issue = _check_decision_quote_fields(quote, market_source, validate_present_fields=True)
            view = self.store.thesis_view(thesis['company_id'], as_of=as_of, knowledge_at=as_of, mode='pit', now=as_of)
            selected = view['record']
            latest_available = selected is not None and selected['version'] == thesis['version']
            source_availability = {identity: self.store.source_availability(sources[identity], as_of=as_of, now=as_of)
                                   if identity in sources else {'available': None, 'reason_codes': ['source_snapshot_missing']}
                                   for identity in roots}
            sources_known = not missing and all(item['available'] is True for item in source_availability.values())
            lifecycle = DecisionLifecycle(self.store)
            source_holds = lifecycle.dependency_source_information_holds(
                {'company_id': thesis['company_id'], 'evidence_ids': roots}) if not missing else {}
            classifications = source_assessments(self.store, list(sources), as_of=as_of)
            reply_holds = {key: item for key, item in classifications.items() if item['information_status'] != 'public_clarification'}
            reply_bindings, binding_reasons = _reply_bindings(self.store, sources, thesis['company_id'], as_of, classifications)
            position = lifecycle.position_for(thesis['company_id'], as_of, {'synthetic': False})
            reasons = []
            if not latest_available:
                reasons.append('latest_thesis_availability_unresolved')
            if not sources_known:
                reasons.append('source_availability_unresolved')
            if source_holds:
                reasons.append('dependent_source_information_held_for_review')
            if reply_holds:
                reasons.append('dependent_reply_information_held_for_review')
            reasons.extend(binding_reasons)
            if quote_issue:
                reasons.append(quote_issue)
            if field_issue:
                reasons.append(field_issue)
            has_ir = any(s['source_type'] == 'ir_reply' for s in sources.values())
            publicity_ok = (not missing and not source_holds and not reply_holds and not binding_reasons)
            inputs = {'synthetic': synthetic, 'as_of': as_of, 'thesis': thesis, 'policy': policy,
                      'quote': quote, 'sources': list(calculation_sources.values()),
                      'context': {'held': position['held'] if position else None,
                                  'thesis_status': assessment['thesis_status'],
                                  'information_status': 'public_clarification' if has_ir else 'public_disclosure',
                                  'evidence_ids': assessment['evidence_ids']}}
            if reasons:
                result = {'company_id': thesis['company_id'], 'thesis_version': thesis['version'],
                          'as_of': as_of, 'policy_id': policy['id'], 'policy_version': policy['version'],
                          'policy_snapshot': policy, 'status': 'unresolved', 'proposed_action': 'unresolved',
                          'reason_codes': list(dict.fromkeys(reasons)), 'evidence_ids': assessment['evidence_ids']}
            else:
                result = evaluate_decision(inputs)
            if position is None:
                result = _hold(result, ['position_history_unknown'])
            record = {'schema_version': 1, 'id': request['id'], 'company_id': thesis['company_id'],
                'thesis_version': thesis['version'], 'policy_id': policy['id'], 'policy_version': policy['version'],
                'recorded_at': as_of, 'request': request, 'request_sha256': digest,
                'synthetic': synthetic, 'assessment': deepcopy(assessment),
                'assessment_is_reviewer_assertion_not_engine_fact': True,
                'basis': {'kind': 'saved_research', 'has_IR_reply_origin': True if has_ir else None if missing else False,
                          'public_information_check': publicity_ok,
                          'source_availability_check': sources_known,
                          'public_only': bool(not has_ir and publicity_ok and sources_known),
                          'meaning': 'Mechanical saved-source type/metadata/availability checks; not independent issuer authenticity or external publicity verification.'},
                'thesis_snapshot': thesis, 'thesis_sha256': _digest(thesis),
                'policy_snapshot': policy, 'policy_sha256': _digest(policy), 'policy_registered_at': registered,
                'quote': deepcopy(quote), 'position_snapshot': position,
                'source_ids': list(sources), 'source_sha256': {key: _digest(s) for key, s in sources.items()},
                'source_snapshots': list(sources.values()), 'missing_source_ids': missing,
                'availability': {'thesis_selection': view, 'source_roots': source_availability},
                'context': {**inputs['context'], 'information_review_versions': {key: item['version'] for key, item in classifications.items()}},
                'information_review_snapshots': classifications, 'reply_bindings': reply_bindings,
                'source_information_holds': source_holds, 'result': result,
                'financial_inputs_verified': False, 'external_sends_orders': 0}
            self.db.execute('INSERT INTO research_decision_reviews VALUES (?,?,?,?,?,?,?,?)',
                (record['id'], record['company_id'], record['thesis_version'], record['policy_id'],
                 record['policy_version'], digest, json_text(record), as_of))
            return self._envelope(self._row(record['id']), now=current, added=True)
