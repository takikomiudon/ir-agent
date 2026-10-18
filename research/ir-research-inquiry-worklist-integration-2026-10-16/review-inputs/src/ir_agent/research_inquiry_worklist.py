"""Current-only research follow-up inventory, without dispatch or financial ranking.

Use existing current_view for every reply. No Store constructor, schema installation,
write API, text interpretation or automatic branch selection is used.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

from .research_inquiries import ResearchInquiries
from .store import Store


class _ReadAdapter:
    # These existing methods only SELECT; expose no mutation/context helpers.
    _clock = staticmethod(Store._clock)
    source = Store.source
    reply = Store.reply
    question = Store.question

    def __init__(self, connection):
        self.connection = connection


_TABLE_COLUMNS = {
    'research_inquiries': {'id', 'company_id', 'status', 'data', 'first_saved_at',
                          'sent_at', 'sent_recorded_at', 'closed_at', 'closure_reason'},
    'research_inquiry_replies': {'id', 'inquiry_id', 'data', 'first_saved_at'},
    'research_inquiry_reviews': {'reply_id', 'version', 'data', 'first_saved_at'},
}
_DEPENDENCY_COLUMNS = {
    'qualitative_case_versions': {'case_id', 'version', 'config_revision', 'entry_kind',
                                 'request_sha256', 'data', 'first_saved_at'},
    'sources': {'id', 'data'},
    'record_availability': {'entity_type', 'entity_id', 'version', 'snapshot_sha256',
                            'first_saved_at', 'presence_observed_at', 'basis'},
    'source_classifications': {'source_id', 'version', 'data', 'first_saved_at'},
    'replies': {'id', 'data'},
    'questions': {'id', 'data', 'status', 'sent_at', 'closed_at', 'closure_reason'},
    'reply_information_reviews': {'reply_id', 'version', 'data', 'first_saved_at'},
}
_CATEGORIES = ('draft', 'awaiting_reply', 'unreviewed', 'evidence_held', 'comparison_note', 'unknown')
_WAIT_REASONS = {'no_reply', 'no_response', 'reply_unreviewed'}


def _current(api, inquiry_id, reply_id, now, *, dependencies_known):
    try:
        if not dependencies_known:
            raise ValueError('Incomplete dependency schema')
        view = api.current_view(inquiry_id, reply_id=reply_id, now=now)
        review = view['review']
        return {'reply_id': reply_id, 'review_version': review['version'] if review else None,
                'status': view['status'], 'reason_codes': view['reason_codes'],
                'branch_id': view['branch_id'], 'comparison_note': view['comparison_note']}
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error):
        # Never echo exception text: saved prose can be embedded in errors.
        return {'reply_id': reply_id, 'review_version': None, 'status': 'unknown',
                'reason_codes': ['current_view_unavailable'], 'branch_id': None,
                'comparison_note': None}


def _report(connection, now):
    checked_at = Store._clock(now)
    tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    sections, dependencies = {}, {}
    for table, columns in (_TABLE_COLUMNS | _DEPENDENCY_COLUMNS).items():
        reason = 'table_missing' if table not in tables else None
        if reason is None and not columns <= {r[1] for r in connection.execute('PRAGMA table_info('+table+')')}:
            reason = 'table_schema_unsupported'
        section = {'status': 'unknown' if reason else 'known', 'reason_codes': [reason] if reason else []}
        if table in _TABLE_COLUMNS:
            section['row_count'] = None if reason else connection.execute('SELECT count(*) FROM '+table).fetchone()[0]
            sections[table] = section
        else:
            dependencies[table] = section
    result = {'checked_at': checked_at, 'status': 'unknown', 'sections': sections, 'dependencies': dependencies,
              'inquiries': [], 'categories': {key: [] for key in _CATEGORIES},
              'ordering': 'ID order only; not investment or contact priority',
              'financial_inputs_verified': False, 'case_applied': False,
              'send_ready': False, 'meaning_review_required': True,
              'no_response_is_negative_evidence': False}
    if any(s['status'] == 'unknown' for s in sections.values()):
        # A partial inventory is not a complete worklist; unknown counts stay null.
        return result
    dependencies_known = all(s['status'] == 'known' for s in dependencies.values())
    api = ResearchInquiries(_ReadAdapter(connection))
    for inquiry in connection.execute('SELECT id,company_id,status,closure_reason FROM research_inquiries ORDER BY id'):
        identity = inquiry['id']
        reply_ids = [r[0] for r in connection.execute(
            'SELECT id FROM research_inquiry_replies WHERE inquiry_id=? ORDER BY id', (identity,))]
        views = [_current(api, identity, reply_id, checked_at, dependencies_known=dependencies_known) for reply_id in reply_ids]
        no_reply_view = None if reply_ids else _current(api, identity, None, checked_at, dependencies_known=dependencies_known)
        categories = []
        if inquiry['status'] in ('draft', 'awaiting_reply'):
            categories.append(inquiry['status'])
        for view in views or [no_reply_view]:
            item_categories = []
            if view['status'] == 'unknown':
                item_categories.append('unknown')
            else:
                if 'reply_unreviewed' in view['reason_codes']:
                    item_categories.append('unreviewed')
                if set(view['reason_codes']) - _WAIT_REASONS:
                    item_categories.append('evidence_held')
                if view['status'] == 'comparison_note':
                    item_categories.append('comparison_note')
            view['categories'] = item_categories
            categories.extend(item_categories)
        categories = [key for key in _CATEGORIES if key in categories]
        for key in categories:
            result['categories'][key].append(identity)
        result['inquiries'].append({'inquiry_id': identity, 'company_id': inquiry['company_id'],
            'state': inquiry['status'], 'closure_reason': inquiry['closure_reason'],
            'categories': categories, 'replies': views, 'no_reply_view': no_reply_view})
    result['status'] = 'unknown' if not dependencies_known or result['categories']['unknown'] else 'known'
    return result


def read_research_inquiry_worklist(path, *, now=None):
    """Read one transaction snapshot of an existing DB; now is internal/test only.

    No database is created on absent paths. This function never invokes Store.__init__.
    A report is current-use metadata, not authorization to send or investment advice.
    """
    database = Path(path).resolve(strict=True)
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA query_only=ON')
        connection.execute('BEGIN')
        try:
            return _report(connection, now)
        finally:
            connection.rollback()
