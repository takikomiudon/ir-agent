"""Append-only corrections to reply classification and current decision views.

A correction never rewrites the received text, an applied thesis, or a saved
review. Subsequent calculations consult visible assessments. Current views mark
superseded decisions for review while their original snapshots stay auditable.
These are recordkeeping safeguards, not financial rules from an author.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json

from .models import available, integer, json_text, now_iso, object_value, source_origins, text, timestamp

SCHEMA = """
CREATE TABLE IF NOT EXISTS reply_information_reviews (
    reply_id TEXT NOT NULL REFERENCES replies(id), version INTEGER NOT NULL,
    data TEXT NOT NULL, first_saved_at TEXT NOT NULL,
    PRIMARY KEY(reply_id,version)
);
CREATE TABLE IF NOT EXISTS reply_information_research_checks (
    reply_id TEXT NOT NULL, version INTEGER NOT NULL,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    PRIMARY KEY(reply_id,version,job_id),
    FOREIGN KEY(reply_id,version) REFERENCES reply_information_reviews(reply_id,version)
);
"""


def research_information(store, thesis: dict, *, as_of: str) -> tuple[list[dict], list[dict]]:
    """Freeze visible classification history for the thesis's actual dependencies.

    Origins outside the visibility boundary cannot expose their reply metadata.
    A previously completed company's review covers only that saved version; a
    later classification is a fresh event even if its wording is identical.
    """
    boundary = timestamp(as_of)
    pending = list(thesis['evidence_ids'])
    visited, subjects = set(), set()
    while pending:
        source_id = pending.pop()
        if source_id in visited:
            continue
        visited.add(source_id)
        source = store.source(source_id)
        if source['company_id'] != thesis['company_id']:
            raise ValueError('Research evidence provenance belongs to another company')
        if not available(source, boundary):
            continue
        metadata = source.get('metadata', {})
        if source['source_type'] == 'ir_reply' and metadata.get('reply_id'):
            subject = text(metadata['reply_id'], 'source reply_id')
            reply = store.reply(subject)
            if store.question(reply['question_id'])['company_id'] != thesis['company_id']:
                raise ValueError('Research reply classification belongs to another company')
            subjects.add(subject)
        pending.extend(source_origins(source))
    checked = {(row['reply_id'], row['version']) for row in store.connection.execute(
        'SELECT c.reply_id,c.version FROM reply_information_research_checks c '
        'JOIN jobs j ON j.id=c.job_id WHERE j.company_id=? AND j.status=\'completed\' AND j.completed_at<=?',
        (thesis['company_id'], boundary.isoformat()))}
    visible, unreviewed = [], []
    for subject in sorted(subjects):
        history = assessments(store, subject, as_of=as_of)
        visible.extend(history)
        if history and (subject, history[-1]['version']) not in checked:
            unreviewed.append({'reply_id': subject, 'version': history[-1]['version']})
    return visible, unreviewed


def validate_research_refs(result: dict, packet: dict) -> list[dict]:
    required = packet.get('new_information_review_refs', [])
    references = result.get('information_review_refs', [])
    if not isinstance(references, list):
        raise ValueError('result.information_review_refs must be a list')
    allowed = {(item['reply_id'], item['version']) for item in packet.get('information_reviews', [])}
    seen = set()
    normalized = []
    for reference in references:
        reference = object_value(reference, 'information review reference')
        if set(reference) != {'reply_id', 'version'}:
            raise ValueError('An information review reference requires only reply_id and version')
        key = (text(reference['reply_id'], 'information review reply_id'),
               integer(reference['version'], 'information review version', minimum=1))
        if key in seen:
            raise ValueError('Duplicate information review reference')
        if key not in allowed:
            raise ValueError('Information review reference is outside the frozen research packet')
        seen.add(key)
        normalized.append({'reply_id': key[0], 'version': key[1]})
    if any((item['reply_id'], item['version']) not in seen for item in required):
        raise ValueError('Account for every new information correction in information_review_refs')
    return normalized


def record_research_checks(store, job_id: str, references: list[dict]) -> None:
    """Called in the same transaction as the research result and thesis append."""
    for reference in references:
        store.connection.execute('INSERT OR IGNORE INTO reply_information_research_checks VALUES (?,?,?)',
                                 (reference['reply_id'], reference['version'], job_id))


def assessments(store, reply_id: str, *, as_of: str | None = None) -> list[dict]:
    rows = store.connection.execute(
        'SELECT data,first_saved_at FROM reply_information_reviews WHERE reply_id=? ORDER BY version',
        (reply_id,))
    result = []
    boundary = timestamp(as_of) if as_of is not None else None
    for row in rows:
        value = json.loads(row['data'])
        if boundary is None or (timestamp(row['first_saved_at']) <= boundary and
                                timestamp(value['recorded_at']) <= boundary):
            result.append(value)
    return result


def add_assessment(store, value: dict, *, now: str) -> dict:
    request = deepcopy(object_value(value, 'reply information review'))
    required = {'reply_id', 'expected_version', 'information_status', 'basis_quote', 'rationale', 'recorded_at'}
    if set(request) != required:
        raise ValueError('Information review requires exactly reply_id, expected_version, information_status, basis_quote, rationale, recorded_at')
    for field in ('reply_id', 'basis_quote', 'rationale', 'recorded_at'):
        text(request[field], field)
    expected = integer(request['expected_version'], 'expected_version')
    if request['information_status'] not in ('public_clarification', 'unclear', 'potential_nonpublic'):
        raise ValueError('Invalid reply information classification')
    recorded = timestamp(request['recorded_at'])
    if recorded > timestamp(now):
        raise ValueError('Information review cannot be recorded in the future')
    with store.transaction():
        reply = store.reply(request['reply_id'])
        if request['basis_quote'] not in reply['raw_text']:
            raise ValueError('Information review quote must occur in the immutable reply text')
        if recorded < timestamp(reply['received_at']):
            raise ValueError('Information review cannot predate reply receipt')
        history = assessments(store, reply['id'])
        # A transport retry returns its original record even after later versions.
        for previous in history:
            if previous['request'] == request:
                return previous
        if len(history) != expected:
            raise ValueError('Information review version changed; read the latest review before appending')
        if history and recorded < timestamp(history[-1]['recorded_at']):
            raise ValueError('Information reviews cannot be backdated before the previous review')
        result = {'reply_id': reply['id'], 'version': expected + 1,
                  'information_status': request['information_status'], 'recorded_at': request['recorded_at'],
                  'first_saved_at': now, 'request': request}
        store.connection.execute('INSERT INTO reply_information_reviews VALUES (?,?,?,?)',
                                 (reply['id'], result['version'], json_text(result), now))
        return result


def source_assessments(store, source_ids: list[str], *, as_of: str | None = None,
                       reply_id: str | None = None) -> dict[str, dict]:
    subjects = {reply_id} if reply_id is not None else set()
    for source_id in source_ids:
        source = store.source(source_id)
        if source['source_type'] == 'ir_reply':
            subject = source.get('metadata', {}).get('reply_id')
            if subject:
                subjects.add(text(subject, 'source reply_id'))
    result = {}
    for subject in sorted(subjects):
        history = assessments(store, subject, as_of=as_of)
        if history:
            result[subject] = history[-1]
    return result


def hold_result(result: dict, *, reason: str, reviews: dict) -> dict:
    viewed = deepcopy(result)
    viewed['status'] = 'unresolved'
    viewed['proposed_action'] = 'unresolved'
    viewed['reason_codes'] = list(dict.fromkeys([*viewed.get('reason_codes', []), reason]))
    viewed['information_reviews'] = deepcopy(reviews)
    return viewed


def _current_time(now):
    return timestamp(now.isoformat() if isinstance(now, datetime) else now if now is not None else now_iso(), "trusted current time").isoformat()


def _current_quote_check(result, checked_at):
    from .decision import check_quote_timing, validate_decision_policy
    unknown = {"checked_at": checked_at, "status": "unknown", "reason_codes": ["saved_quote_or_policy_unresolved"],
               "age_microseconds": None, "max_quote_age_seconds": None}
    if not isinstance(result, dict) or not isinstance(result.get('quote'), dict) or not isinstance(result.get('policy_snapshot'), dict):
        return unknown
    try:
        quote = result['quote']
        if any(quote.get(field) is None for field in ('company_id', 'source_id', 'price_jpy', 'currency', 'observed_at', 'retrieved_at')):
            return unknown
        text(quote['company_id'], 'saved quote company'); text(quote['source_id'], 'saved quote source')
        if quote['currency'] != 'JPY' or quote['company_id'] != result.get('company_id'):
            return unknown
        policy = validate_decision_policy(result['policy_snapshot'])
        return check_quote_timing(quote, policy['parameters'].get('max_quote_age_seconds'), as_of=checked_at)
    except ValueError:
        # Legacy/incomplete snapshots cannot establish freshness. Preserve the
        # historical result rather than repair a malformed saved snapshot.
        return unknown


def _current_thesis_check(store, review, checked_at):
    check = {'reviewed_version': None, 'current_version': None, 'status': 'unknown', 'checked_at': checked_at,
             'reason_codes': ['saved_review_thesis_reference_unresolved'],
             'scope': 'Raw latest DB version comparison only; not financial validation, historical PIT reconstruction or acceptance of a future thesis.'}
    try:
        company_id = text(review.get('company_id'), 'review company ID')
        check['reviewed_version'] = integer(review.get('thesis_version'), 'review thesis version', minimum=1)
    except ValueError:
        return check
    check['reason_codes'] = ['current_thesis_unresolved']
    try:
        current = store.thesis(company_id)
        if not isinstance(current, dict) or current.get('company_id') != company_id:
            return check
        check['current_version'] = integer(current.get('version'), 'current thesis version', minimum=1)
    except ValueError:
        return check
    matches = check['reviewed_version'] == check['current_version']
    check.update(status='matched' if matches else 'mismatch',
                 reason_codes=[] if matches else ['reviewed_thesis_version_not_current'])
    return check


def current_decision_view(store, review: dict, *, now=None) -> dict:
    """Show current recheck requirements without altering the historical record."""
    viewed = deepcopy(review)
    checked_at = _current_time(now)
    latest = source_assessments(store, review['source_ids'], reply_id=review['reply_id'], as_of=checked_at)
    consumed = review.get('context', {}).get('information_review_versions', {})
    changes = {key: value for key, value in latest.items()
               if value['information_status'] != 'public_clarification' or
               consumed.get(key) != value['version']}
    quote_check = _current_quote_check(review.get('result'), checked_at)
    thesis_check = _current_thesis_check(store, review, checked_at)
    price_hold = quote_check['status'] != 'fresh'
    thesis_hold = thesis_check['status'] != 'matched'
    requirements = ((['requires_information_review'] if changes else [])
                    + (['requires_thesis_review'] if thesis_hold else [])
                    + (['requires_price_review'] if price_hold else []))
    viewed['current_quote_check'] = quote_check
    viewed['current_thesis_check'] = thesis_check
    viewed['current_review_requirements'] = requirements
    viewed['current_validity'] = requirements[0] if requirements else 'no_recorded_information_correction'
    if changes:
        viewed['historical_result'] = deepcopy(review['result'])
        viewed['result'] = hold_result(review['result'], reason='reply_information_corrected', reviews=changes)
    if (thesis_hold or price_hold) and viewed['result'].get('proposed_action') != 'unresolved':
        viewed.setdefault('historical_result', deepcopy(review['result']))
        viewed['result'].update(status='unresolved', proposed_action='unresolved')
        viewed['result']['reason_codes'] = list(dict.fromkeys([*viewed['result'].get('reason_codes', []),
            *(thesis_check['reason_codes'] if thesis_hold else []), *(quote_check['reason_codes'] if price_hold else [])]))
        if 'action' in viewed['result']:
            viewed['result']['action'] = 'unresolved'
    return viewed


def current_evaluation_view(store, value: dict, *, now=None) -> dict:
    """Expose a correction on both contracted and legacy applied evaluations."""
    from .harness import evaluation_view
    viewed = evaluation_view(value)
    checked_at = _current_time(now)
    if not value.get('applied'):
        saved_review = value.get('decision_review')
        viewed['current_quote_check'] = _current_quote_check(saved_review.get('result') if isinstance(saved_review, dict) else None, checked_at)
        viewed['current_thesis_check'] = _current_thesis_check(store, saved_review if isinstance(saved_review, dict) else value, checked_at)
        return viewed
    if value.get('decision_review_id'):
        review = current_decision_view(store, store.decision_review(value['decision_review_id']), now=checked_at)
        viewed.update(decision_review=review, current_quote_check=deepcopy(review['current_quote_check']),
                      current_thesis_check=deepcopy(review['current_thesis_check']),
                      current_validity=review['current_validity'], current_review_requirements=deepcopy(review['current_review_requirements']))
        if review['current_review_requirements']:
            viewed.update(action='unresolved', decision_status=review['current_validity'])
    else:
        quote_check = _current_quote_check(None, checked_at)
        thesis_check = _current_thesis_check(store, value, checked_at)
        requirements = (['requires_thesis_review'] if thesis_check['status'] != 'matched' else []) + ['requires_price_review']
        viewed.update(current_quote_check=quote_check, current_thesis_check=thesis_check, current_validity=requirements[0],
                      current_review_requirements=requirements)
        if viewed.get('action') != 'unresolved':
            viewed.update(action='unresolved', decision_status=requirements[0])
        history = assessments(store, value['request']['reply_id'], as_of=checked_at)
        if history:
            viewed.update(action='unresolved', decision_status='requires_information_review',
                          current_validity='requires_information_review',
                          current_review_requirements=['requires_information_review', *requirements], information_reviews=history)
    return viewed
