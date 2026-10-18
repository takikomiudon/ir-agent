"""Optional exact-source bindings for a review of already public information.

Presence, scope and time checks do not certify that an answer is absent, that a
review was actually performed, or that all later public information was read.
No investment inputs or actions are inferred from this record.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import re

from .models import available, json_text, object_value, source_origins, text, timestamp, validate_source


def validate_public_information_review(value, *, created_at):
    review = deepcopy(object_value(value, 'public_information_review'))
    if set(review) != {'reviewed_at', 'reviewer', 'rationale', 'sources'}:
        raise ValueError('Public information review has missing or unknown fields')
    reviewed = timestamp(review['reviewed_at'], 'public_information_review.reviewed_at')
    if reviewed > timestamp(created_at, 'question.created_at'):
        raise ValueError('Public information review cannot postdate question creation')
    text(review['reviewer'], 'public_information_review.reviewer')
    text(review['rationale'], 'public_information_review.rationale')
    if not isinstance(review['sources'], list) or not review['sources']:
        raise ValueError('Public information review sources must be a nonempty list')
    seen = set()
    for item in review['sources']:
        item = object_value(item, 'public information review source')
        if set(item) != {'source_id', 'source_snapshot_sha256', 'scope', 'basis_quote'}:
            raise ValueError('Public information review source has missing or unknown fields')
        identity = text(item['source_id'], 'public review source_id')
        if identity in seen:
            raise ValueError('Duplicate public information review source_id')
        seen.add(identity)
        digest = item['source_snapshot_sha256']
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Public review source_snapshot_sha256 must be lowercase SHA256')
        text(item['scope'], 'public review scope')
        text(item['basis_quote'], 'public review basis_quote')
    return review


def check_public_information_review(question, sources, *, as_of):
    """Check only this opt-in binding against the supplied source snapshots."""
    review = validate_public_information_review(question['public_information_review'],
                                                created_at=question['created_at'])
    if timestamp(question['created_at']) > timestamp(as_of):
        raise ValueError('Question creation cannot postdate the public review boundary')
    if not isinstance(sources, list):
        raise ValueError('Public information review requires source snapshots')
    raw, checked = {}, {}
    for item in sources:
        source = validate_source(item)
        if source['id'] in checked:
            raise ValueError('Duplicate source IDs in public information review snapshots')
        raw[source['id']] = item
        checked[source['id']] = source
    roots = [item['source_id'] for item in review['sources']]
    for item in review['sources']:
        source = raw.get(item['source_id'])
        if source is None:
            raise ValueError('Missing public information review source snapshot')
        if sha256(json_text(source).encode('utf-8')).hexdigest() != item['source_snapshot_sha256']:
            raise ValueError('Public information review source snapshot SHA differs')
        if item['basis_quote'] not in source['content']:
            raise ValueError('Public information review quote is absent from its source')
    reasons, active, visited = [], set(), set()
    boundary = timestamp(review['reviewed_at'])

    pending = [(identity, False) for identity in roots]
    while pending:
        identity, exiting = pending.pop()
        if exiting:
            active.remove(identity)
            visited.add(identity)
            continue
        if identity in active:
            raise ValueError('Cyclic public information review provenance')
        if identity in visited:
            continue
        source = checked.get(identity)
        if source is None:
            reasons.append('missing_origin_source_snapshot')
            continue
        if source['company_id'] != question['company_id']:
            raise ValueError('Public information review source belongs to another company')
        if source['source_type'] == 'market_data':
            raise ValueError('Market data is not a public information review source')
        if not available(source, boundary):
            reasons.append('source_origin_not_available')
        classification = source['metadata'].get('information_status')
        if ((source['source_type'] == 'ir_reply' and classification != 'public_clarification')
                or classification not in (None, 'public_disclosure', 'public_clarification')):
            reasons.append('source_information_held_for_review')
        active.add(identity)
        pending.append((identity, True))
        pending.extend((parent, False) for parent in source_origins(source))
    return {'reviewed_at': review['reviewed_at'], 'source_ids': roots,
            'source_closure_ids': sorted(visited),
            'source_snapshot_sha256': {item['source_id']: item['source_snapshot_sha256']
                                       for item in review['sources']},
            'reason_codes': list(dict.fromkeys(reasons)),
            'meaning_review_required': True, 'answer_absence_verified': False}
