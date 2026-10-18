"""Pre-thesis research inquiries; no financial decisions, dispatch or case writes.

Only the three tables below are mutated. Install SCHEMA on the owning Store.
First-save clocks are trusted runtime observations, separate from claimed dates.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

from .decision_lifecycle import DecisionLifecycle
from .models import integer, json_text, object_value, text, timestamp
from .qualitative_research import QualitativeResearch


SCHEMA = """
CREATE TABLE IF NOT EXISTS research_inquiries (
    id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id),
    topic TEXT NOT NULL, status TEXT NOT NULL, data TEXT NOT NULL,
    first_saved_at TEXT NOT NULL, sent_at TEXT, sent_recorded_at TEXT,
    closed_at TEXT, closure_reason TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS one_open_research_inquiry_per_topic
    ON research_inquiries(company_id,topic) WHERE status IN ('draft','awaiting_reply');
CREATE TABLE IF NOT EXISTS research_inquiry_replies (
    id TEXT PRIMARY KEY, inquiry_id TEXT NOT NULL REFERENCES research_inquiries(id),
    data TEXT NOT NULL, first_saved_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS research_inquiry_reviews (
    reply_id TEXT NOT NULL REFERENCES research_inquiry_replies(id),
    version INTEGER NOT NULL, data TEXT NOT NULL, first_saved_at TEXT NOT NULL,
    PRIMARY KEY(reply_id,version)
);
"""


def _digest(value):
    return sha256(json_text(value).encode('utf-8')).hexdigest()


def _fields(value, required, optional=()):
    value = deepcopy(object_value(value, 'research inquiry request'))
    if not set(required) <= set(value) or set(value) - set(required) - set(optional):
        raise ValueError('Research inquiry request has missing or unknown fields')
    return value


class ResearchInquiries:
    def __init__(self, store):
        self.store = store
        self.db = store.connection

    def _now(self, now):
        return self.store._clock(now)

    def _check_new_write_time(self, now):
        # Retry returns happen before this guard. Never mint an earlier trusted
        # receipt after observing a later write in this isolated subsystem.
        clocks = self.db.execute(
            'SELECT first_saved_at FROM research_inquiries UNION ALL '
            'SELECT sent_recorded_at FROM research_inquiries WHERE sent_recorded_at IS NOT NULL UNION ALL '
            'SELECT closed_at FROM research_inquiries WHERE closed_at IS NOT NULL UNION ALL '
            'SELECT first_saved_at FROM research_inquiry_replies UNION ALL '
            'SELECT first_saved_at FROM research_inquiry_reviews').fetchall()
        if any(timestamp(row[0]) > timestamp(now) for row in clocks):
            raise ValueError('Trusted runtime clock precedes research inquiry saving history')

    @staticmethod
    def _time(value, now, label):
        instant = timestamp(value, label)
        if instant > timestamp(now):
            raise ValueError(label + ' exceeds trusted now')
        return instant

    def _row(self, identity):
        row = self.db.execute('SELECT * FROM research_inquiries WHERE id=?',
                              (text(identity, 'inquiry_id'),)).fetchone()
        if row is None:
            raise ValueError('Unknown research inquiry')
        return row

    def show_inquiry(self, inquiry_id):
        row = self._row(inquiry_id)
        replies = self.db.execute(
            'SELECT id,first_saved_at FROM research_inquiry_replies WHERE inquiry_id=?',
            (inquiry_id,)).fetchall()
        return {'record': json.loads(row['data']),
                'state': {k: row[k] for k in ('status', 'sent_at', 'sent_recorded_at',
                                             'closed_at', 'closure_reason')},
                'replies': [r['id'] for r in sorted(replies,
                    key=lambda r: (timestamp(r['first_saved_at']), r['id']))]}

    def list_inquiries(self, *, limit=20):
        """Inventory only; no financial inbox, ranking or current-use certification."""
        integer(limit, 'limit', minimum=1)
        return [{key: row[key] for key in ('id', 'company_id', 'topic', 'status', 'first_saved_at')}
                for row in self.db.execute('SELECT id,company_id,topic,status,first_saved_at '
                                           'FROM research_inquiries ORDER BY id LIMIT ?', (limit,))]

    def show_reply(self, reply_id):
        row = self.db.execute('SELECT * FROM research_inquiry_replies WHERE id=?',
                              (text(reply_id, 'reply_id'),)).fetchone()
        if row is None:
            raise ValueError('Unknown research inquiry reply')
        return {'record': json.loads(row['data']), 'reviews': [json.loads(r[0]) for r in
                self.db.execute('SELECT data FROM research_inquiry_reviews WHERE reply_id=? '
                                'ORDER BY version', (reply_id,))]}

    def _case(self, request, boundary, *, now=None):
        now = boundary if now is None else now
        case = QualitativeResearch(self.store).show_case(request['case_id'])
        record = case['record']
        if (case['version'] != request['expected_case_version'] or
                case['config_revision'] != request['expected_config_revision'] or
                record['issue_id'] != request['issue_id'] or not record['enabled']):
            raise ValueError('Research inquiry case version, configuration or issue changed')
        if timestamp(case['first_saved_at']) > min(timestamp(boundary), timestamp(now)):
            raise ValueError('Case was not saved at the requested boundary')
        if not QualitativeResearch._files_match(record):
            raise ValueError('Research inquiry case files changed')
        registry = QualitativeResearch(self.store)
        for identity, previous in record['reviewed_sources'].items():
            source = self.store.source(identity)
            inventory = {'issue_review_status': 'reviewed',
                         'source_snapshot_sha256': previous['source_snapshot_sha256']}
            check = registry._source_check(record, source, timestamp(boundary),
                                           timestamp(now), inventory)
            if (_digest(source) != previous['source_snapshot_sha256'] or
                    check['status'] != 'matched'):
                raise ValueError('Research inquiry case source evidence held')
        return {k: deepcopy(case[k]) for k in ('case_id', 'version', 'config_revision',
                                               'record', 'first_saved_at')}

    def _public(self, company_id, created_at, review, now, *, synthetic):
        # Reuse review-only closure/PIT/current-correction checks, never thesis inputs.
        value = {'company_id': company_id, 'created_at': created_at,
                 'public_information_review': review}
        lifecycle = DecisionLifecycle(self.store)
        check = lifecycle.review_public_information(value, as_of=created_at, now=now)
        if check['reason_codes']:
            raise ValueError('Public information review held: ' + ', '.join(check['reason_codes']))
        sources = lifecycle.public_information_sources_for(value)
        # Match the existing monitor rule: real observations cannot consume
        # a demo source, including any parent in the complete source DAG.
        if not synthetic and any(s['metadata'].get('synthetic') is True for s in sources):
            raise ValueError('Synthetic source cannot support a real research inquiry')
        return {'check': check, 'sources': sources,
                'source_snapshot_sha256': {s['id']: _digest(s) for s in sources}}

    def _current_inquiry_reasons(self, saved, now):
        reasons = []
        try:
            case = self._case(saved['request'], now)
            if case != saved['case_snapshot'] or _digest(case) != saved['case_snapshot_sha256']:
                reasons.append('case_snapshot_changed')
        except (ValueError, KeyError, OSError):
            reasons.append('case_or_files_changed')
        try:
            public = self._public(saved['company_id'], saved['request']['created_at'],
                                  saved['request']['public_information_review'], now,
                                  synthetic=saved['case_snapshot']['record']['synthetic'])
            if public['sources'] != saved['public_information']['sources']:
                reasons.append('public_source_snapshot_changed')
        except (ValueError, KeyError, OSError):
            reasons.append('public_information_held')
        if timestamp(saved['first_saved_at']) > timestamp(now):
            reasons.append('inquiry_not_saved_at_boundary')
        return reasons

    def add_inquiry(self, value, *, now=None):
        now = self._now(now)
        required = {'id', 'case_id', 'issue_id', 'expected_case_version',
                    'expected_config_revision', 'created_at', 'topic', 'question',
                    'already_answered', 'remaining_uncertainty', 'branches',
                    'public_information_review'}
        request = _fields(value, required)
        for key in required - {'expected_case_version', 'expected_config_revision',
                               'branches', 'public_information_review'}:
            text(request[key], key)
        for key in ('expected_case_version', 'expected_config_revision'):
            integer(request[key], key, minimum=1)
        created = self._time(request['created_at'], now, 'created_at')
        branches = request['branches']
        if not isinstance(branches, list) or len(branches) < 2:
            raise ValueError('Research inquiry needs at least two comparison branches')
        identities = []
        for branch in branches:
            branch = _fields(branch, {'id', 'condition', 'comparison_note'})
            for key in branch:
                text(branch[key], 'branch.' + key)
            identities.append(branch['id'])
        if len(set(identities)) != len(identities) or 'unresolved' not in identities:
            raise ValueError('Include unique branches and an unresolved branch')
        with self.store._record_write():
            prior = self.db.execute('SELECT data FROM research_inquiries WHERE id=?',
                                    (request['id'],)).fetchone()
            if prior:
                saved = json.loads(prior[0])
                if saved['request'] != request:
                    raise ValueError('A research inquiry and its branches are immutable')
                self._time(saved['first_saved_at'], now, 'first_saved_at')
                return saved
            case = self._case(request, request['created_at'], now=now)
            company_id = case['record']['company_id']
            # The inverse check in Harness is installed by the integration owner.
            for table in ('questions', 'research_inquiries'):
                if self.db.execute('SELECT 1 FROM ' + table + ' WHERE company_id=? AND topic=? '
                                   "AND status IN ('draft','awaiting_reply')",
                                   (company_id, request['topic'])).fetchone():
                    raise ValueError('An open question already exists for this company and topic')
            if created < timestamp(case['first_saved_at']):
                raise ValueError('Inquiry predates case saving')
            public = self._public(company_id, request['created_at'],
                                  request['public_information_review'], now,
                                  synthetic=case['record']['synthetic'])
            saved = {'id': request['id'], 'company_id': company_id, 'request': request,
                     'case_snapshot': case, 'case_snapshot_sha256': _digest(case),
                     'public_information': public, 'first_saved_at': now,
                     'financial_inputs_verified': False}
            self._check_new_write_time(now)
            self.db.execute('INSERT INTO research_inquiries '
                            '(id,company_id,topic,status,data,first_saved_at) VALUES (?,?,?,?,?,?)',
                            (saved['id'], company_id, request['topic'], 'draft', json_text(saved), now))
            return saved

    def mark_sent(self, inquiry_id, sent_at, *, now=None):
        now = self._now(now)
        sent = self._time(sent_at, now, 'sent_at')
        with self.store._record_write():
            row = self._row(inquiry_id)
            if row['sent_at'] == sent_at:
                self._time(row['sent_recorded_at'], now, 'sent_recorded_at')
                return {'inquiry_id': inquiry_id, 'sent_at': sent_at,
                        'first_saved_at': row['sent_recorded_at']}
            if row['status'] != 'draft':
                raise ValueError('Only a draft research inquiry can be marked sent')
            saved = json.loads(row['data'])
            if sent < timestamp(saved['request']['created_at']) or sent < timestamp(row['first_saved_at']):
                raise ValueError('Sending cannot predate inquiry preparation and saving')
            reasons = self._current_inquiry_reasons(saved, now)
            if reasons:
                raise ValueError('Research inquiry held: ' + ', '.join(reasons))
            # Recording an already sent inquiry can be delayed. Check the
            # actual claimed send boundary as well as preparation and runtime.
            self._public(saved['company_id'], sent_at,
                         saved['request']['public_information_review'], now,
                         synthetic=saved['case_snapshot']['record']['synthetic'])
            self._check_new_write_time(now)
            self.db.execute("UPDATE research_inquiries SET status='awaiting_reply',sent_at=?,"
                            'sent_recorded_at=? WHERE id=?', (sent_at, now, inquiry_id))
            return {'inquiry_id': inquiry_id, 'sent_at': sent_at, 'first_saved_at': now}

    def close_inquiry(self, inquiry_id, reason, *, now=None):
        now = self._now(now)
        states = {'no_response': 'expired', 'declined': 'declined', 'cancelled': 'cancelled'}
        if not isinstance(reason, str) or reason not in states:
            raise ValueError('Invalid research inquiry closure reason')
        with self.store._record_write():
            row = self._row(inquiry_id)
            if row['closure_reason'] == reason:
                self._time(row['closed_at'], now, 'closed_at')
                return {'inquiry_id': inquiry_id, 'reason': reason, 'first_saved_at': row['closed_at']}
            if row['closed_at'] is not None or row['status'] == 'answered':
                raise ValueError('An answered or closed research inquiry cannot be closed again')
            if reason != 'cancelled' and row['sent_at'] is None:
                raise ValueError('Decline/no-response requires a recorded sent inquiry')
            if timestamp(now) < timestamp(row['sent_recorded_at'] or row['first_saved_at']):
                raise ValueError('Closure predates saved inquiry state')
            self._check_new_write_time(now)
            self.db.execute('UPDATE research_inquiries SET status=?,closed_at=?,closure_reason=? WHERE id=?',
                            (states[reason], now, reason, inquiry_id))
            return {'inquiry_id': inquiry_id, 'reason': reason, 'first_saved_at': now}

    def add_reply(self, value, *, now=None):
        now = self._now(now)
        request = _fields(value, {'id', 'inquiry_id', 'received_at', 'raw_text'}, {'information_status'})
        request.setdefault('information_status', 'unclear')
        for key in ('id', 'inquiry_id', 'raw_text'):
            text(request[key], key)
        if request['information_status'] != 'unclear':
            raise ValueError('Research inquiry receipts start unclear; use a separate review')
        received = self._time(request['received_at'], now, 'received_at')
        with self.store._record_write():
            prior = self.db.execute('SELECT data FROM research_inquiry_replies WHERE id=?',
                                    (request['id'],)).fetchone()
            if prior:
                saved = json.loads(prior[0])
                if saved['request'] != request:
                    raise ValueError('A research inquiry reply is immutable')
                self._time(saved['first_saved_at'], now, 'first_saved_at')
                return saved
            row = self._row(request['inquiry_id'])
            if row['sent_at'] is None or row['status'] == 'cancelled':
                raise ValueError('Reply requires an externally sent research inquiry')
            if timestamp(row['sent_recorded_at']) > timestamp(now):
                raise ValueError('Sending was not saved at trusted now')
            if received < timestamp(row['sent_at']):
                raise ValueError('Reply cannot predate sending')
            saved = {'id': request['id'], 'inquiry_id': request['inquiry_id'],
                     'company_id': row['company_id'], 'request': request, 'first_saved_at': now}
            self._check_new_write_time(now)
            self.db.execute('INSERT INTO research_inquiry_replies VALUES (?,?,?,?)',
                            (saved['id'], saved['inquiry_id'], json_text(saved), now))
            self.db.execute("UPDATE research_inquiries SET status='answered' WHERE id=?", (saved['inquiry_id'],))
            return saved

    def add_review(self, value, *, now=None):
        now = self._now(now)
        request = _fields(value, {'reply_id', 'expected_version', 'branch_id', 'basis_quote',
                                  'rationale', 'recorded_at', 'information_status'},
                          {'public_information_review'})
        for key in ('reply_id', 'branch_id', 'basis_quote', 'rationale'):
            text(request[key], key)
        integer(request['expected_version'], 'expected_version', minimum=0)
        recorded = self._time(request['recorded_at'], now, 'recorded_at')
        if (not isinstance(request['information_status'], str) or
                request['information_status'] not in {'public_clarification', 'unclear', 'potential_nonpublic'}):
            raise ValueError('Invalid research reply information classification')
        if request['information_status'] == 'public_clarification' and 'public_information_review' not in request:
            raise ValueError('Public clarification requires source-bound public information review')
        if request['information_status'] != 'public_clarification' and 'public_information_review' in request:
            raise ValueError('Only a public clarification carries a public information review')
        with self.store._record_write():
            reply_view = self.show_reply(request['reply_id'])
            for previous in reply_view['reviews']:
                if previous['request'] == request:
                    self._time(previous['first_saved_at'], now, 'first_saved_at')
                    return previous
            if len(reply_view['reviews']) != request['expected_version']:
                raise ValueError('Research inquiry review version changed')
            reply = reply_view['record']
            inquiry = json.loads(self._row(reply['inquiry_id'])['data'])
            reasons = self._current_inquiry_reasons(inquiry, now)
            if reasons and request['information_status'] == 'public_clarification':
                raise ValueError('Research inquiry held: ' + ', '.join(reasons))
            if recorded < timestamp(reply['first_saved_at']) or recorded < timestamp(reply['request']['received_at']):
                raise ValueError('Review predates reply receipt or actual saving')
            if reply_view['reviews'] and recorded < timestamp(reply_view['reviews'][-1]['request']['recorded_at']):
                raise ValueError('Research inquiry reviews cannot be backdated')
            if reply_view['reviews'] and recorded < timestamp(reply_view['reviews'][-1]['first_saved_at']):
                raise ValueError('A revised review cannot predate the previous actual saving')
            if request['basis_quote'] not in reply['request']['raw_text']:
                raise ValueError('Research review quote must occur in immutable reply text')
            branch = next((b for b in inquiry['request']['branches'] if b['id'] == request['branch_id']), None)
            if branch is None:
                raise ValueError('Unknown precommitted research branch')
            public = None
            if 'public_information_review' in request:
                public = self._public(reply['company_id'], request['recorded_at'],
                                      request['public_information_review'], now,
                                      synthetic=inquiry['case_snapshot']['record']['synthetic'])
            saved = {'reply_id': reply['id'], 'version': request['expected_version'] + 1,
                     'request': request, 'first_saved_at': now,
                     'reply_snapshot_sha256': _digest(reply),
                     'inquiry_snapshot_sha256': _digest(inquiry),
                     'branch': deepcopy(branch), 'public_information': public,
                     'financial_inputs_verified': False, 'case_applied': False}
            self._check_new_write_time(now)
            self.db.execute('INSERT INTO research_inquiry_reviews VALUES (?,?,?,?)',
                            (reply['id'], saved['version'], json_text(saved), now))
            return saved

    def current_view(self, inquiry_id, *, reply_id=None, now=None):
        now = self._now(now)
        inquiry_view = self.show_inquiry(inquiry_id)
        inquiry = inquiry_view['record']
        reasons = self._current_inquiry_reasons(inquiry, now)
        identity = reply_id or (inquiry_view['replies'][-1] if inquiry_view['replies'] else None)
        latest = None
        if identity is None:
            reasons.append('no_response' if inquiry_view['state']['closure_reason'] == 'no_response' else 'no_reply')
        else:
            reply_view = self.show_reply(identity)
            reply = reply_view['record']
            if reply['inquiry_id'] != inquiry_id:
                raise ValueError('Reply belongs to another inquiry')
            if timestamp(reply['first_saved_at']) > timestamp(now):
                reasons.append('reply_not_saved_at_boundary')
            latest = reply_view['reviews'][-1] if reply_view['reviews'] else None
            if latest is None:
                reasons.append('reply_unreviewed')
            else:
                if timestamp(latest['first_saved_at']) > timestamp(now):
                    reasons.append('review_not_saved_at_boundary')
                if (_digest(reply) != latest['reply_snapshot_sha256'] or
                        _digest(inquiry) != latest['inquiry_snapshot_sha256']):
                    reasons.append('reply_or_inquiry_snapshot_changed')
                if latest['request']['information_status'] != 'public_clarification':
                    reasons.append('reply_information_held')
                else:
                    try:
                        public = self._public(inquiry['company_id'], latest['request']['recorded_at'],
                                              latest['request']['public_information_review'], now,
                                              synthetic=inquiry['case_snapshot']['record']['synthetic'])
                        if public['sources'] != latest['public_information']['sources']:
                            reasons.append('review_public_source_snapshot_changed')
                    except (ValueError, KeyError, OSError):
                        reasons.append('review_public_information_held')
        return {'inquiry_id': inquiry_id, 'reply_id': identity, 'checked_at': now,
                'status': 'held' if reasons else 'comparison_note',
                'reason_codes': list(dict.fromkeys(reasons)),
                'review': latest, 'comparison_note': latest['branch']['comparison_note']
                if latest is not None and not reasons else None,
                'branch_id': latest['branch']['id'] if latest else 'unresolved',
                'financial_inputs_verified': False, 'case_applied': False,
                'meaning_review_required': True}
