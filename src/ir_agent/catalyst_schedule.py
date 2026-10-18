"""Read-only, date-only schedule candidates; never occurrence or trading logic.

Anthropic catalyst-calendar supplies the tracking procedure. This bounded
project contract keeps caller date interpretations and source matches separate.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256

from .intake import KINDS
from .models import day, integer, json_text, object_value, parse_json, text, timestamp
from .prediction_bindings import _Reader, _check, _digest, _snapshot, _status

_EVENT_FIELDS = {'id', 'company_id', 'synthetic', 'kind', 'label', 'period', 'claims'}
_PERIOD_FIELDS = {'raw_label', 'fiscal_year_label', 'quarter_label', 'basis_quote', 'interpretation'}
_CLAIM_FIELDS = {'id', 'kind', 'source_id', 'source_snapshot_sha256', 'basis_quote',
                'basis_quote_location', 'raw_date_label', 'date', 'time', 'timezone',
                'date_context_quote', 'date_context_rationale', 'supersedes_claim_id'}
_LOCATION_FIELDS = {'character_start', 'character_end', 'offset_unit', 'pdf_page',
                    'printed_page', 'saved_text_file', 'section'}
_COLUMNS = {'sources': {'id', 'data'},
            'record_availability': {'entity_type', 'entity_id', 'version', 'snapshot_sha256',
                                    'first_saved_at', 'presence_observed_at', 'basis'},
            'source_classifications': {'source_id', 'version', 'data', 'first_saved_at'}}
_DOMAIN_REASONS = {'source_identity_or_company_mismatch', 'synthetic_source_in_real_observation',
                   'source_provenance_cycle', 'source_provenance_invalid',
                   'source_snapshot_missing', 'source_snapshot_invalid'}


def _fields(value, fields, label, *, required=True):
    object_value(value, label)
    if set(value) - fields or (required and set(value) != fields):
        raise ValueError(label + ' has missing or unknown fields')


def _validate_requests(requests):
    if not isinstance(requests, list):
        raise ValueError('event_requests must be a list')
    events, claims = set(), set()
    for event in requests:
        _fields(event, _EVENT_FIELDS, 'event')
        for key in ('id', 'company_id', 'label'):
            text(event[key], 'event.' + key)
        if event['id'] in events:
            raise ValueError('Duplicate event ID')
        events.add(event['id'])
        if type(event['synthetic']) is not bool:
            raise ValueError('event.synthetic must be boolean')
        if event['kind'] not in ('earnings_release', 'earnings_presentation'):
            raise ValueError('Unsupported event kind')
        _fields(event['period'], _PERIOD_FIELDS, 'event.period')
        for key in _PERIOD_FIELDS:
            text(event['period'][key], 'event.period.' + key)
        if not isinstance(event['claims'], list) or len(event['claims']) != 1:
            raise ValueError('Exactly one schedule claim is required in this version')
        claim = event['claims'][0]
        _fields(claim, _CLAIM_FIELDS, 'schedule claim')
        for key in ('id', 'source_id', 'source_snapshot_sha256', 'basis_quote',
                    'raw_date_label', 'date_context_quote', 'date_context_rationale'):
            text(claim[key], 'claim.' + key)
        if claim['id'] in claims:
            raise ValueError('Duplicate claim ID')
        claims.add(claim['id'])
        digest = claim['source_snapshot_sha256']
        if len(digest) != 64 or any(char not in '0123456789abcdef' for char in digest):
            raise ValueError('source_snapshot_sha256 must be a lowercase SHA-256')
        if claim['kind'] != 'schedule':
            raise ValueError('Only schedule claims are supported')
        if any(claim[key] is not None for key in ('time', 'timezone', 'supersedes_claim_id')):
            raise ValueError('Only date-only timezone-unknown schedules without changes are supported')
        if claim['date'] is not None:
            day(claim['date'], 'claim.date')
        location = claim['basis_quote_location']
        if location is not None:
            _fields(location, _LOCATION_FIELDS, 'basis_quote_location')
            for key in ('character_start', 'character_end'):
                integer(location[key], 'location.' + key)
            if location['character_end'] <= location['character_start']:
                raise ValueError('Quote location must be a nonempty interval')
            for key in ('pdf_page', 'printed_page'):
                if location[key] is not None:
                    integer(location[key], 'location.' + key, minimum=1)
            for key in ('offset_unit', 'saved_text_file', 'section'):
                text(location[key], 'location.' + key)


class _ScheduleReader(_Reader):
    def __init__(self, connection, now):
        super().__init__(connection, now)
        self.sections = {}
        for table, required in _COLUMNS.items():
            if table not in self.tables:
                self.sections[table] = {'status': 'unknown', 'row_count': None, 'reason_codes': ['table_missing']}
                continue
            columns = {row[1] for row in connection.execute('PRAGMA table_info(' + table + ')')}
            if not required <= columns:
                self.tables.remove(table)
                self.sections[table] = {'status': 'unknown', 'row_count': None, 'reason_codes': ['table_schema_unsupported']}
            else:
                count = connection.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                self.sections[table] = {'status': 'known', 'row_count': count, 'reason_codes': []}

    def publicity(self, source, company_id, cutoff):
        # Public IR replies remain outside this bounded first version, even
        # when a reply's separate information review calls them public.
        if source['source_type'] != 'public_disclosure':
            return _check('held', 'source_type_outside_schedule_scope')
        return super().publicity(source, company_id, cutoff)

    def classification(self, source_id, *, boundary, root_id):
        if 'source_classifications' not in self.tables:
            return _check('unknown', 'classification_table_missing_or_unsupported')
        visible = []
        try:
            for row in self.connection.execute(
                'SELECT version,data,first_saved_at FROM source_classifications WHERE source_id=? ORDER BY version', (source_id,)):
                value = object_value(parse_json(row[1]), 'saved classification')
                saved, recorded = timestamp(row[2]), timestamp(value.get('recorded_at'))
                if saved > timestamp(boundary) or recorded > timestamp(boundary):
                    continue
                integer(row[0], 'classification version', minimum=1)
                integer(value.get('version'), 'saved classification version', minimum=1)
                if value.get('source_id') != source_id or value.get('version') != row[0]:
                    return _check('mismatch', 'classification_identity_mismatch')
                visible.append(value)
        except ValueError:
            return _check('unknown', 'classification_history_invalid')
        if not visible:
            return _check('unknown', 'classification_not_available')
        latest = visible[-1]
        source = self.sources.get(source_id, {}).get('record')
        if not isinstance(source, dict):
            return _check('unknown', 'classification_source_missing')
        quote = latest.get('basis_quote')
        if (latest.get('source_snapshot_sha256') != _digest(source)
                or latest.get('source_sha256') != sha256(source['content'].encode('utf-8')).hexdigest()
                or not isinstance(quote, str) or not quote.strip() or quote not in source['content']):
            return _check('mismatch', 'classification_source_binding_mismatch', version=latest['version'])
        kind = latest.get('kind')
        if not isinstance(kind, str) or kind not in KINDS or kind == 'unresolved':
            return _check('held', 'classification_unresolved', version=latest['version'])
        if source_id == root_id and kind != 'schedule':
            return _check('held', 'schedule_classification_required', kind=kind, version=latest['version'])
        return _check('matched', kind=kind, version=latest['version'], recorded_at=latest['recorded_at'])


def _binding(reader, event, as_of):
    claim = event['claims'][0]; root_id = claim['source_id']
    source = reader.get('sources', root_id)
    checks = []
    if not isinstance(source, dict):
        return _check('unknown', 'saved_source_missing'), [], _check('unknown', 'saved_source_missing'), _check('unknown', 'saved_source_missing')
    if _digest(source) != claim['source_snapshot_sha256']:
        checks.append(_check('mismatch', 'source_snapshot_sha_mismatch'))
    content = source.get('content')
    if not isinstance(content, str):
        checks.append(_check('mismatch', 'source_content_invalid'))
    else:
        for field, quote in (('basis_quote', claim['basis_quote']), ('raw_date_label', claim['raw_date_label']),
                             ('date_context_quote', claim['date_context_quote']), ('period_quote', event['period']['basis_quote'])):
            target = claim['basis_quote'] if field in ('raw_date_label', 'date_context_quote') else content
            if quote not in target:
                checks.append(_check('mismatch', field + '_mismatch'))
        location = claim['basis_quote_location']
        if location is not None:
            pages = content.split('\f')
            page_index = location['pdf_page'] - 1 if location['pdf_page'] is not None else None
            selected = content if page_index is None else pages[page_index] if page_index < len(pages) else ''
            if selected[location['character_start']:location['character_end']] != claim['basis_quote']:
                checks.append(_check('mismatch', 'quote_location_mismatch'))
    graph = reader.source_graph(root_id, event['company_id'], event['synthetic'], as_of, as_of)
    historical, current = [], []
    for node in graph:
        domain = [reason for reason in node['reason_codes'] if reason in _DOMAIN_REASONS]
        if domain:
            checks.append(_check(node['status'], *domain, source_id=node['source_id']))
        for target, prefix, boundary in ((historical, 'historical', as_of), (current, 'current', reader.now)):
            for suffix in ('availability', 'publicity'):
                if prefix + '_' + suffix in node:
                    target.append(node[prefix + '_' + suffix])
            classification = reader.classification(node['source_id'], boundary=boundary, root_id=root_id)
            node[prefix + '_classification'] = classification
            target.append(classification)
    def summary(items):
        return _check(_status(items), *dict.fromkeys(reason for item in items for reason in item['reason_codes']))
    binding = summary(checks)
    binding.update(source_id=root_id, source_snapshot_sha256=claim['source_snapshot_sha256'],
                   url=source.get('url'), published_at=source.get('published_at'), retrieved_at=source.get('retrieved_at'))
    return binding, graph, summary([binding, *historical]), summary([binding, *current])


def report_catalyst_schedule(connection, event_requests, *, as_of, now, calendar_window=None):
    """Inspect explicit schedule mappings on a read snapshot without mutations.

    A bound quote is neither a semantic date verification nor occurrence proof.
    All supplied events, including outside-window and unknown dates, survive.
    """
    _validate_requests(event_requests)
    boundary, clock = timestamp(as_of, 'as_of'), timestamp(now, 'trusted now')
    if boundary > clock:
        raise ValueError('as_of cannot exceed trusted now')
    if calendar_window is not None:
        _fields(calendar_window, {'date_from', 'date_through'}, 'calendar_window')
        if day(calendar_window['date_from']) > day(calendar_window['date_through']):
            raise ValueError('calendar_window is reversed')
    result = {'schema_version': 1, 'status': 'schedule_monitor_only', 'as_of': boundary.isoformat(),
              'checked_at': clock.isoformat(), 'events': [], 'calendar_window': deepcopy(calendar_window),
              'limitations': ['Date interpretations and period correspondence are caller mappings requiring semantic review.',
                  'Mapping prospectiveness is unverified; event registration and full-universe completeness are not established.',
                  'Occurrence, cancellation, rescheduling, results, fingerprints, change detection and exact-time resolution are not implemented.',
                  'No jobs, questions, forecasts, thesis updates, messages or orders are created.']}
    with _snapshot(connection):
        reader = _ScheduleReader(connection, clock.isoformat())
        result['source_sections'] = deepcopy(reader.sections)
        result['table_status'] = {key: value['status'] for key, value in reader.sections.items()}
        for event in event_requests:
            claim = event['claims'][0]; date_value = claim['date']
            window_group = ('date_unknown' if date_value is None else 'in_window' if calendar_window is None
                or calendar_window['date_from'] <= date_value <= calendar_window['date_through'] else 'outside_window')
            binding, graph, historical, current = _binding(reader, event, boundary.isoformat())
            combined = _status([historical, current])
            result['events'].append({'id': event['id'], 'company_id': event['company_id'], 'kind': event['kind'],
                'label': event['label'], 'period': deepcopy(event['period']), 'request': deepcopy(event),
                'window_group': window_group, 'status': 'source_bound_candidate' if combined == 'matched' else combined,
                'reason_codes': list(dict.fromkeys([*historical['reason_codes'], *current['reason_codes']])),
                'source_binding': binding, 'lineage_checks': graph, 'historical_usability': historical, 'current_use': current,
                'schedule': {'status': 'candidate_only', 'claim_id': claim['id'], 'date': date_value,
                             'date_interpretation': 'caller_mapping_unverified'},
                'timing': {'status': 'floating_date' if date_value is not None else 'unknown', 'scheduled_date': date_value,
                           'scheduled_at': None, 'time': None, 'timezone': None, 'relation_to_as_of': 'unknown_timezone'},
                'due': None, 'occurrence': {'status': 'not_established'},
                'result_documents': {'status': 'none_linked'}, 'semantic_review_required': True,
                'mapping_prospectiveness': 'unverified'})
    result['coverage'] = {'event_count': len(event_requests),
        **{key + '_count': sum(event['window_group'] == key for event in result['events'])
           for key in ('in_window', 'outside_window', 'date_unknown')},
        'source_bound_candidate_count': sum(event['status'] == 'source_bound_candidate' for event in result['events'])}
    return result
