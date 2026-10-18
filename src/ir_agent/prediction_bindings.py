"""Read-only source bindings for frozen predictions and their observations.

This project record contract implements the source-preserving prerequisite in
docs/prediction-evidence-binding.md. Gneiting/Raftery's proper-score definitions
do not establish label meaning, independence, training history or calibration.
No scorer, SDK, migration, Store constructor or mutation is called here.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256

from .availability import RecordAvailability
from .models import integer, json_text, object_value, parse_json, source_origins, text, timestamp, validate_source
from .prediction_readiness import _signal_leakage, audit_prediction_readiness

_TABLES = ('ir_observation_versions', 'ir_predictions', 'ir_prediction_models', 'sources',
           'replies', 'questions', 'reply_information_reviews', 'record_availability')
_REFERENCE = {'id', 'version', 'snapshot_sha256', 'design_sha256'}


def _digest(value):
    return sha256(json_text(value).encode('utf-8')).hexdigest()


def _status(checks):
    statuses = [item['status'] for item in checks]
    return next((state for state in ('mismatch', 'held', 'unknown') if state in statuses), 'matched')


def _check(status, *reasons, **fields):
    return {'status': status, 'reason_codes': list(reasons), **fields}


def _fields(value, allowed, label):
    object_value(value, label)
    if set(value) - allowed:
        raise ValueError('Unknown ' + label + ' field')


def _optional_text(value, label, *, digest=False):
    if value is None:
        return
    text(value, label)
    if digest and (len(value) != 64 or any(char not in '0123456789abcdef' for char in value)):
        raise ValueError(label + ' must be a lowercase SHA-256')


def _validate_requests(requests):
    if not isinstance(requests, list):
        raise ValueError('binding_requests must be a list')
    seen = set()
    for request in requests:
        _fields(request, {'observation_ref', 'source_links', 'reply_links'}, 'binding request')
        reference = request.get('observation_ref')
        if reference is not None:
            _fields(reference, _REFERENCE, 'observation reference')
            _optional_text(reference.get('id'), 'observation ID')
            if reference.get('version') is not None:
                integer(reference['version'], 'observation version', minimum=1)
            for field in ('snapshot_sha256', 'design_sha256'):
                _optional_text(reference.get(field), field, digest=True)
            if reference.get('id') is not None:
                if reference['id'] in seen:
                    raise ValueError('Duplicate observation binding request')
                seen.add(reference['id'])
        for field in ('source_links', 'reply_links'):
            links = request.get(field)
            if links is None:
                continue
            if not isinstance(links, list):
                raise ValueError(field + ' must be a list or null')
            link_ids = set()
            for link in links:
                if field == 'source_links':
                    _fields(link, {'role', 'observation_evidence_id', 'source_id', 'source_snapshot_sha256'}, 'source link')
                    role = link.get('role')
                    if role is not None and role not in ('premise', 'state_evidence'):
                        raise ValueError('Invalid source link role')
                    key = (role, link.get('observation_evidence_id'))
                    for name in ('observation_evidence_id', 'source_id'):
                        _optional_text(link.get(name), name)
                    _optional_text(link.get('source_snapshot_sha256'), 'source_snapshot_sha256', digest=True)
                else:
                    _fields(link, {'reply_id', 'observation_reply_sha256', 'raw_reply_sha256', 'basis_quote'}, 'reply link')
                    for name in ('reply_id', 'basis_quote'):
                        _optional_text(link.get(name), name)
                    for name in ('observation_reply_sha256', 'raw_reply_sha256'):
                        _optional_text(link.get(name), name, digest=True)
                    key = link.get('reply_id')
                if key in link_ids:
                    raise ValueError('Duplicate evidence/reply binding')
                link_ids.add(key)


@contextmanager
def _snapshot(connection):
    nested = connection.in_transaction
    if not nested:
        connection.execute('BEGIN')
    try:
        yield
    finally:
        if not nested:
            connection.execute('ROLLBACK')


class _Reader:
    def __init__(self, connection, now):
        self.connection, self.now = connection, now
        self.tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.sources, self.replies = {}, {}

    def get(self, table, identity):
        if table not in self.tables or not isinstance(identity, str) or not identity.strip():
            return None
        row = self.connection.execute('SELECT data FROM ' + table + ' WHERE id=?', (identity,)).fetchone()
        return parse_json(row[0]) if row else None

    def readiness_snapshot(self):
        result = {}
        specifications = (
            ('observation_versions', 'ir_observation_versions', ('observation_id', 'version', 'design_sha256', 'data', 'first_saved_at')),
            ('predictions', 'ir_predictions', ('id', 'observation_id', 'observation_version', 'model_id', 'model_version', 'request_sha256', 'data', 'first_saved_at')),
            ('models', 'ir_prediction_models', ('model_id', 'model_version', 'commitment_sha256', 'data', 'first_saved_at')),
        )
        for section, table, columns in specifications:
            if table in self.tables:
                result[section] = []
                for row in self.connection.execute('SELECT ' + ','.join(columns) + ' FROM ' + table):
                    item = dict(zip(columns, row)); item['record'] = parse_json(item.pop('data'))
                    result[section].append(item)
        return result

    def availability(self, kind, identity, record, cutoff):
        if 'record_availability' not in self.tables:
            return _check('unknown', 'availability_table_missing')
        try:
            value = RecordAvailability(self.connection).at(kind, identity, record, as_of=cutoff,
                knowledge_at=cutoff, now=self.now)
        except ValueError as error:
            return _check('mismatch', 'availability_snapshot_or_record_invalid', detail=str(error))
        return _check('matched' if value['available'] is True else 'mismatch' if value['available'] is False else 'unknown',
                      *value['reason_codes'], availability=value)

    def publicity(self, source, company_id, cutoff):
        metadata = source['metadata']; classification = metadata.get('information_status')
        check = _check('matched', effective_information_status=classification, latest_review=None)
        if source['source_type'] == 'ir_reply':
            reply_id = metadata.get('reply_id')
            if not isinstance(reply_id, str) or not reply_id.strip():
                return _check('unknown', 'origin_reply_identity_missing')
            reply = self.get('replies', reply_id)
            if not isinstance(reply, dict) or reply.get('id') != reply_id:
                return _check('unknown', 'origin_reply_unresolved')
            question = self.get('questions', reply.get('question_id'))
            if not isinstance(question, dict):
                return _check('unknown', 'origin_question_unresolved')
            if question.get('id') != reply.get('question_id') or question.get('company_id') != company_id:
                return _check('mismatch', 'origin_reply_company_mismatch')
            if 'content' in source and source['content'] != reply.get('raw_text'):
                return _check('mismatch', 'origin_reply_content_mismatch')
            self.replies[reply_id] = {'record': deepcopy(reply), 'snapshot_sha256': _digest(reply)}
            reply_available = self.availability('reply', reply_id, reply, cutoff)
            question_available = self.availability('question', question['id'], question, cutoff)
            check.update(reply_availability=reply_available, question_availability=question_available)
            classification = reply.get('information_status')
            if 'reply_information_reviews' not in self.tables:
                return _check('unknown', 'information_review_table_missing')
            history = []
            try:
                for row in self.connection.execute('SELECT data,first_saved_at FROM reply_information_reviews WHERE reply_id=? ORDER BY version', (reply_id,)):
                    review = object_value(parse_json(row[0]), 'saved information review')
                    if timestamp(row[1]) <= timestamp(cutoff) and timestamp(review.get('recorded_at')) <= timestamp(cutoff):
                        if review.get('reply_id') != reply_id:
                            return _check('mismatch', 'information_review_reply_mismatch')
                        history.append(review)
            except ValueError:
                return _check('unknown', 'information_review_history_invalid')
            if history:
                check['latest_review'] = deepcopy(history[-1])
                classification = history[-1].get('information_status')
            check['effective_information_status'] = classification
            if classification not in ('public_clarification',):
                return {**check, 'status': 'held' if classification in ('unclear', 'potential_nonpublic') else 'unknown',
                        'reason_codes': ['origin_information_held_or_unknown']}
        elif classification not in (None, 'public_disclosure', 'public_clarification'):
            return {**check, 'status': 'held', 'reason_codes': ['source_information_held_for_review']}
        if 'reply_availability' in check:
            prerequisites = [check['reply_availability'], check['question_availability']]
            check['status'] = _status(prerequisites)
            check['reason_codes'] = list(dict.fromkeys(reason for prerequisite in prerequisites for reason in prerequisite['reason_codes']))
        return check

    def source_graph(self, root_id, company_id, synthetic, usage_at, as_of):
        checks, active, visited = [], set(), set()
        pending = [(root_id, False)]
        while pending:
            identity, exiting = pending.pop()
            if exiting:
                active.remove(identity); visited.add(identity)
                continue
            if identity in active:
                checks.append(_check('mismatch', 'source_provenance_cycle', source_id=identity)); continue
            if identity in visited:
                continue
            raw = self.get('sources', identity)
            if not isinstance(raw, dict):
                checks.append(_check('unknown', 'source_snapshot_missing', source_id=identity)); continue
            try:
                source = validate_source(raw)
            except ValueError:
                checks.append(_check('mismatch', 'source_snapshot_invalid', source_id=identity)); continue
            self.sources[identity] = {'record': deepcopy(raw), 'snapshot_sha256': _digest(raw),
                                      'content_sha256': sha256(source['content'].encode('utf-8')).hexdigest()}
            local = []
            if source['id'] != identity or source['company_id'] != company_id:
                local.append(_check('mismatch', 'source_identity_or_company_mismatch'))
            if not synthetic and source['metadata'].get('synthetic') is True:
                local.append(_check('mismatch', 'synthetic_source_in_real_observation'))
            historical = self.availability('source', identity, raw, as_of)
            usage = self.availability('source', identity, raw, usage_at) if usage_at is not None else _check('unknown', 'evidence_usage_time_unresolved')
            current = self.availability('source', identity, raw, self.now)
            historical_publicity = self.publicity(source, company_id, as_of)
            current_publicity = self.publicity(source, company_id, self.now)
            usage_publicity = self.publicity(source, company_id, usage_at) if usage_at is not None else _check('unknown', 'evidence_usage_time_unresolved')
            local.extend((historical, usage, current, historical_publicity, current_publicity, usage_publicity))
            try:
                parents = source_origins(source)
            except ValueError:
                parents = []
                local.append(_check('mismatch', 'source_provenance_invalid'))
            checks.append({'source_id': identity, 'status': _status(local),
                'reason_codes': list(dict.fromkeys(reason for check in local for reason in check['reason_codes'])),
                'historical_availability': historical, 'usage_availability': usage, 'current_availability': current,
                'historical_publicity': historical_publicity, 'current_publicity': current_publicity, 'usage_publicity': usage_publicity})
            active.add(identity)
            pending.append((identity, True))
            pending.extend((parent, False) for parent in reversed(parents))
        return checks


def _question_binding(reader, record, as_of):
    question = reader.get('questions', record['question_id'])
    if not isinstance(question, dict):
        return _check('unknown', 'saved_question_missing')
    checks = []
    if (question.get('id') != record['question_id'] or question.get('company_id') != record['company_id']
            or question.get('question') != record['question'] or question.get('thesis_version') != record['thesis_version']):
        checks.append(_check('mismatch', 'question_identity_text_or_thesis_mismatch'))
    historical = reader.availability('question', record['question_id'], question, as_of)
    current = reader.availability('question', record['question_id'], question, reader.now)
    checks.extend((historical, current))
    return _check(_status(checks), *(reason for check in checks for reason in check['reason_codes']),
                  record=deepcopy(question), snapshot_sha256=_digest(question), historical_availability=historical, current_availability=current)


def _source_binding(reader, record, link, as_of):
    result = {'role': link.get('role'), 'original_reference': None, 'source_ref': deepcopy(link),
              'status': 'unknown', 'reason_codes': []}
    if any(link.get(field) is None for field in ('role', 'observation_evidence_id', 'source_id', 'source_snapshot_sha256')):
        return {**result, 'reason_codes': ['source_binding_fields_missing']}
    evidence = (record['premise_evidence'] if link['role'] == 'premise'
                else (record.get('verification') or {}).get('evidence', []))
    reference = next((item for item in evidence if item['id'] == link['observation_evidence_id']), None)
    if reference is None:
        return {**result, 'status': 'mismatch', 'reason_codes': ['observation_evidence_reference_missing']}
    result.update(original_reference=deepcopy(reference), quote=reference['quote'])
    source = reader.get('sources', link['source_id'])
    if not isinstance(source, dict):
        return {**result, 'reason_codes': ['saved_source_missing']}
    checks = []
    if _digest(source) != link['source_snapshot_sha256']:
        checks.append(_check('mismatch', 'source_snapshot_sha_mismatch'))
    try:
        validated = validate_source(source)
    except ValueError:
        return {**result, 'status': 'mismatch', 'reason_codes': ['source_snapshot_invalid']}
    if validated['source_type'] != 'public_disclosure':
        checks.append(_check('mismatch', 'evidence_source_not_public_disclosure'))
    if reference['quote'] not in validated['content']:
        checks.append(_check('mismatch', 'source_quote_mismatch'))
    if validated['url'] != reference['url']:
        checks.append(_check('mismatch', 'source_url_mismatch'))
    for field in ('published_at', 'retrieved_at'):
        if validated.get(field) is None:
            checks.append(_check('unknown', 'source_' + field + '_unknown'))
        elif timestamp(validated[field]) != timestamp(reference[field]):
            checks.append(_check('mismatch', 'source_' + field + '_mismatch'))
    usage_at = record['question_created_at'] if link['role'] == 'premise' else (record.get('verification') or {}).get('recorded_at')
    graph = reader.source_graph(link['source_id'], record['company_id'], record.get('synthetic', False), usage_at, as_of)
    checks.extend(graph)
    return {**result, 'status': _status(checks), 'reason_codes': list(dict.fromkeys(reason for check in checks for reason in check['reason_codes'])),
            'snapshot_checks': checks[:len(checks)-len(graph)] if graph else checks, 'lineage_checks': graph}


def _reply_binding(reader, record, link, as_of):
    result = {'role': 'reply', 'reply_id': link.get('reply_id'), 'status': 'unknown', 'reason_codes': []}
    if any(link.get(field) is None for field in ('reply_id', 'observation_reply_sha256', 'raw_reply_sha256', 'basis_quote')):
        return {**result, 'reason_codes': ['reply_binding_fields_missing']}
    target = next((item for item in record['replies'] if item['id'] == link['reply_id']), None)
    if target is None:
        return {**result, 'status': 'mismatch', 'reason_codes': ['observation_reply_reference_missing']}
    reply = reader.get('replies', link['reply_id'])
    if not isinstance(reply, dict):
        return {**result, 'reason_codes': ['saved_reply_missing']}
    reader.replies[link['reply_id']] = {'record': deepcopy(reply), 'snapshot_sha256': _digest(reply)}
    checks = []
    if (reply.get('id') != link['reply_id'] or reply.get('question_id') != record['question_id']
            or _digest(target) != link['observation_reply_sha256']):
        checks.append(_check('mismatch', 'reply_identity_or_observation_snapshot_mismatch'))
    if not isinstance(reply.get('raw_text'), str):
        checks.append(_check('unknown', 'raw_reply_text_missing'))
    else:
        if sha256(reply['raw_text'].encode('utf-8')).hexdigest() != link['raw_reply_sha256']:
            checks.append(_check('mismatch', 'raw_reply_sha_mismatch'))
        if link['basis_quote'] not in reply['raw_text']:
            checks.append(_check('mismatch', 'raw_reply_quote_mismatch'))
    try:
        if timestamp(reply.get('received_at')) != timestamp(target['received_at']):
            checks.append(_check('mismatch', 'reply_receipt_time_mismatch'))
    except ValueError:
        checks.append(_check('unknown', 'reply_receipt_time_unknown'))
    historical = reader.availability('reply', link['reply_id'], reply, as_of)
    current = reader.availability('reply', link['reply_id'], reply, reader.now)
    subject = {'source_type': 'ir_reply', 'metadata': {'reply_id': link['reply_id'], 'information_status': reply.get('information_status')}}
    historical_publicity = reader.publicity(subject, record['company_id'], as_of)
    current_publicity = reader.publicity(subject, record['company_id'], reader.now)
    checks.extend((historical, current, historical_publicity, current_publicity))
    return {**result, 'status': _status(checks), 'reason_codes': list(dict.fromkeys(reason for check in checks for reason in check['reason_codes'])),
            'basis_quote': link['basis_quote'], 'original_reply': deepcopy(target),
            'historical_availability': historical, 'current_availability': current,
            'historical_publicity': historical_publicity, 'current_publicity': current_publicity}


def report_prediction_bindings(connection, binding_requests: list[dict], *, as_of: str, now: str) -> dict:
    """Read evidence bindings without approving labels, scoring or writes.

    Own a read snapshot only when the caller has none. An outer transaction is
    never committed or rolled back. Missing tables/data remain explicit.
    """
    _validate_requests(binding_requests)
    boundary, clock = timestamp(as_of, 'as_of'), timestamp(now, 'trusted now')
    if boundary > clock:
        raise ValueError('as_of cannot exceed trusted now')
    with _snapshot(connection):
        reader = _Reader(connection, clock.isoformat())
        snapshot = reader.readiness_snapshot()
        readiness = audit_prediction_readiness(snapshot, as_of=boundary.isoformat())
        versions = {(row['observation_id'], row['version']): row for row in snapshot.get('observation_versions', [])}
        predictions_by_id = {row['id']: row for row in snapshot.get('predictions', [])}
        requests = {}; unresolved = []
        visible_ids = {item['observation_id'] for item in readiness['observations']}
        for index, request in enumerate(binding_requests):
            reference = request.get('observation_ref') or {}
            identity = reference.get('id')
            if identity not in visible_ids:
                unresolved.append(_check('unknown', 'observation_reference_unresolved', request_index=index, request=deepcopy(request)))
            else:
                requests[identity] = request
        reports = []
        for item in readiness['observations']:
            identity = item['observation_id']; current = item['current_snapshot']
            record = versions[(identity, current['version'])]['record']
            request = requests.get(identity, {}); reference = request.get('observation_ref') or {}
            actual = {'id': identity, 'version': current['version'], 'snapshot_sha256': current['snapshot_sha256'], 'design_sha256': current['design_sha256']}
            reference_check = (_check('unknown', 'observation_binding_reference_incomplete') if any(reference.get(key) is None for key in _REFERENCE)
                else _check('matched') if reference == actual else _check('mismatch', 'observation_binding_reference_mismatch'))
            question = _question_binding(reader, record, boundary.isoformat())
            bindings = []; missing = []
            source_links = request.get('source_links') or []; reply_links = request.get('reply_links') or []
            expected = [('premise', evidence['id']) for evidence in record['premise_evidence']]
            expected += [('state_evidence', evidence['id']) for evidence in (record.get('verification') or {}).get('evidence', [])]
            for role, evidence_id in expected:
                if not any(link.get('role') == role and link.get('observation_evidence_id') == evidence_id for link in source_links):
                    missing.append({'role': role, 'observation_evidence_id': evidence_id})
            for reply in record['replies']:
                if not any(link.get('reply_id') == reply['id'] for link in reply_links):
                    missing.append({'role': 'reply', 'reply_id': reply['id']})
            # A mapping for another/old snapshot cannot verify the current one.
            if reference_check['status'] == 'matched':
                bindings.extend(_source_binding(reader, record, link, boundary.isoformat()) for link in source_links)
                bindings.extend(_reply_binding(reader, record, link, boundary.isoformat()) for link in reply_links)
            checks = [reference_check, question, *bindings]
            if missing: checks.append(_check('unknown', 'evidence_bindings_missing'))
            view = item['view']; reasons = [reason for check in checks for reason in check['reason_codes']]
            if view['response_status'] == 'no_response_by_deadline': reasons.append('response_log_completeness_unverified')
            reasons.extend(view['exclusion_reasons'])
            predictions = []
            for prediction in item['predictions']:
                stored = predictions_by_id[prediction['id']]
                predictions.append({**deepcopy(prediction), 'prediction_snapshot': deepcopy(stored['record']),
                                    'request_sha256': stored['request_sha256']})
            reports.append({'observation_ref': actual, 'observation_snapshot': deepcopy(record),
                'original_observation_view': deepcopy(view), 'predictions': predictions,
                'prediction_coverage': item['prediction_coverage'], 'reference_check': reference_check, 'question_binding': question,
                'binding_status': _status(checks), 'resolved_bindings': bindings, 'missing_bindings': missing,
                'reason_codes': list(dict.fromkeys(reasons)),
                'original_signal': [{'reply_id': reply['id'], 'signal': reply['signal']} for reply in record['replies']],
                'current_signal': view['signal'], 'applied_assessment_refs': deepcopy(view.get('assessment_views', [])),
                'reported_state': view['state'], 'selected_state': None,
                'leakage_candidates': _signal_leakage(sorted([row for row in snapshot.get('observation_versions', [])
                    if row['observation_id'] == identity and timestamp(row['first_saved_at']) <= boundary], key=lambda row: row['version']), boundary),
                'semantic_signal': 'unknown', 'state_independence': 'unknown', 'training': 'unknown', 'calibration': 'unknown',
                'score_request': None, 'score': None})
        return {'status': 'source_binding_report_only', 'as_of': boundary.isoformat(), 'checked_at': clock.isoformat(),
            'table_status': {table: 'known' if table in reader.tables else 'unknown' for table in _TABLES},
            'population': {'observation_count': readiness['observation_count'], 'visible_prediction_count': readiness['visible_prediction_count'],
                'no_prediction_count': readiness['observations_without_prediction_count'], 'orphan_prediction_count': readiness['orphan_prediction_count']},
            'observations': reports, 'orphan_predictions': deepcopy(readiness['orphan_predictions']),
            'unresolved_binding_requests': unresolved, 'sources_by_id': reader.sources, 'reply_snapshots': reader.replies,
            'semantic_signal': 'unknown', 'state_independence': 'unknown', 'training': 'unknown', 'calibration': 'unknown',
            'score_request': None, 'score': None,
            'limitations': ['Snapshot/quote/receipt agreement is not state truth, semantic signal support, label independence or verified training.',
                'No scoring, posterior validation, calibration, EVSI adoption or investment decision is performed.',
                'Source and reply snapshots may contain private text; this report is a local audit artifact.',
                'Legacy known-by receipts do not reconstruct an earlier first save or a complete deadline response log.']}
