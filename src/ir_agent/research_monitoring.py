"""Read-only research follow-up triggers, without numerical theses or adoption.

Anthropic thesis-tracker supplies quarterly review and new-data/pillar review.
This project prerequisite only reports saved-source coverage and caller dates.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .catalyst_schedule import _DOMAIN_REASONS, _ScheduleReader
from .models import day, object_value, parse_json, text, timestamp
from .prediction_bindings import _check, _digest, _snapshot, _status

_CASE_FIELDS = {'id', 'company_id', 'issue_id', 'synthetic', 'recorded_at', 'last_review_at',
                'case_ref', 'source_inventory', 'management_review'}


def _fields(value, fields, label):
    object_value(value, label)
    if set(value) != fields:
        raise ValueError(label + ' has missing or unknown fields')


def _hash(value, label):
    text(value, label)
    if len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError(label + ' must be a lowercase SHA-256')


def _path(value, root):
    text(value, 'reference.path')
    candidate = Path(value)
    try:
        candidate = (candidate if candidate.is_absolute() else root / candidate).resolve()
    except (OSError, RuntimeError) as error:
        raise ValueError('Research reference path cannot be resolved') from error
    if not candidate.is_relative_to(root):
        raise ValueError('Research reference escapes research_root')
    return candidate


def _reference(value, root):
    _fields(value, {'path', 'sha256'}, 'file reference')
    _hash(value['sha256'], 'reference.sha256')
    _path(value['path'], root)


def _validate(requests, root, clock):
    if not isinstance(requests, list):
        raise ValueError('case_requests must be a list')
    ids = set()
    for case in requests:
        _fields(case, _CASE_FIELDS, 'research case')
        for key in ('id', 'company_id', 'issue_id'):
            text(case[key], 'case.' + key)
        if case['id'] in ids:
            raise ValueError('Duplicate research case ID')
        ids.add(case['id'])
        if type(case['synthetic']) is not bool:
            raise ValueError('case.synthetic must be boolean')
        recorded = timestamp(case['recorded_at'], 'case.recorded_at')
        reviewed = timestamp(case['last_review_at'], 'case.last_review_at')
        if recorded > clock or reviewed > recorded:
            raise ValueError('Case chronology exceeds trusted now or recorded_at')
        _reference(case['case_ref'], root)
        inventory = case['source_inventory']
        if inventory is not None:
            if not isinstance(inventory, list):
                raise ValueError('source_inventory must be a list or null')
            source_ids = set()
            for item in inventory:
                _fields(item, {'source_id', 'source_snapshot_sha256', 'issue_review_status'}, 'inventory entry')
                text(item['source_id'], 'inventory.source_id')
                _hash(item['source_snapshot_sha256'], 'inventory.source_snapshot_sha256')
                if item['source_id'] in source_ids:
                    raise ValueError('Duplicate source inventory ID')
                source_ids.add(item['source_id'])
                if item['issue_review_status'] not in ('reviewed', 'not_reviewed', 'unknown'):
                    raise ValueError('Invalid issue_review_status')
        management = case['management_review']
        if management is not None:
            _fields(management, {'date', 'timezone', 'basis_ref', 'basis_quote'}, 'management_review')
            if management['date'] is not None:
                day(management['date'], 'management_review.date')
            zone = management['timezone']
            if zone is not None:
                text(zone, 'management_review.timezone')
                try:
                    ZoneInfo(zone)
                except (ZoneInfoNotFoundError, ValueError) as error:
                    raise ValueError('Unknown management review timezone') from error
            _reference(management['basis_ref'], root)
            text(management['basis_quote'], 'management_review.basis_quote')


def _file(reference, root):
    path = _path(reference['path'], root)
    try:
        raw = path.read_bytes()
    except OSError:
        return _check('unknown', 'research_file_missing_or_unreadable', path=reference['path']), None
    digest = sha256(raw).hexdigest()
    check = _check('matched' if digest == reference['sha256'] else 'mismatch',
                   *([] if digest == reference['sha256'] else ['research_file_sha_mismatch']),
                   path=reference['path'], sha256=digest)
    try:
        content = raw.decode('utf-8')
    except UnicodeError:
        return _check('unknown', 'research_file_not_utf8', path=reference['path'], sha256=digest), None
    return check, content


def _summary(checks):
    return _check(_status(checks), *dict.fromkeys(reason for check in checks for reason in check['reason_codes']))


def _management(case, root, boundary, manifest_check):
    management = case['management_review']
    result = {'due': None, 'date': None, 'timezone': None, 'local_calendar_date': None,
              'status': 'unknown', 'reason_codes': [], 'date_is_project_management_only': True}
    if management is None:
        return {**result, 'reason_codes': ['management_date_not_configured']}
    result.update(date=management['date'], timezone=management['timezone'])
    binding, content = _file(management['basis_ref'], root)
    if content is not None and management['basis_quote'] not in content:
        binding = {**binding, **_summary([binding, _check('mismatch', 'management_basis_quote_missing')])}
    if content is not None and management['date'] is not None and management['date'] not in management['basis_quote']:
        binding = {**binding, **_summary([binding, _check('unknown', 'management_date_not_bound_to_quote')])}
    combined = _summary([manifest_check, binding])
    result.update(status=combined['status'], reason_codes=combined['reason_codes'], basis_binding=binding)
    if management['date'] is None or management['timezone'] is None:
        result['status'] = 'unknown'
        result['reason_codes'].append('management_date_or_timezone_unknown')
    elif combined['status'] == 'matched':
        try:
            local = boundary.astimezone(ZoneInfo(management['timezone'])).date()
        except OverflowError as error:
            raise ValueError('Management local date exceeds the supported datetime range') from error
        result.update(local_calendar_date=local.isoformat(), due=local >= day(management['date']))
    return result


def _source(reader, identity, case, inventory, boundary):
    try:
        source = reader.get('sources', identity)
    except ValueError:
        source = None
    result = {'source_id': identity, 'source_snapshot_sha256': None,
              'arrival': 'unknown', 'first_saved_at': None, 'first_save_known': False,
              'issue_review_status': inventory.get('issue_review_status', 'unknown') if inventory else 'unknown'}
    checks = []
    if source is None:
        return {**result, 'status': 'unknown', 'reason_codes': ['source_snapshot_missing'], 'lineage_checks': []}
    if not isinstance(source, dict):
        return {**result, 'status': 'mismatch', 'reason_codes': ['source_snapshot_invalid'], 'lineage_checks': []}
    result['source_snapshot_sha256'] = _digest(source)
    if inventory and result['source_snapshot_sha256'] != inventory['source_snapshot_sha256']:
        checks.append(_check('mismatch', 'inventory_source_sha_mismatch'))
    try:
        graph = reader.source_graph(identity, case['company_id'], case['synthetic'], boundary, boundary)
    except ValueError:
        return {**result, 'status': 'unknown', 'reason_codes': ['source_lineage_unreadable'], 'lineage_checks': []}
    historical, current = [], []
    for node in graph:
        domain = [reason for reason in node['reason_codes'] if reason in _DOMAIN_REASONS]
        if domain:
            checks.append(_check(node['status'], *domain))
        for target, prefix, cutoff in ((historical, 'historical', boundary), (current, 'current', reader.now)):
            for suffix in ('availability', 'publicity'):
                if prefix + '_' + suffix in node:
                    target.append(node[prefix + '_' + suffix])
            classification = reader.classification(node['source_id'], boundary=cutoff, root_id=None)
            node[prefix + '_classification'] = classification
            target.append(classification)
    historical_check = _summary([*checks, *historical])
    current_check = _summary([*checks, *current])
    # Classification/publicity/receipt checks are delegated to the existing reader.
    root_node = next((node for node in graph if node['source_id'] == identity), {})
    available = root_node.get('historical_availability', {}).get('availability', {})
    receipt = available.get('receipt') or {}
    result.update(first_save_known=available.get('first_save_known', False),
                  first_saved_at=receipt.get('first_saved_at'),
                  historical_usability=historical_check, current_use=current_check, lineage_checks=graph)
    if not result['first_save_known']:
        checks.append(_check('unknown', 'source_first_save_unknown'))
    root_domain = [reason for reason in root_node.get('reason_codes', []) if reason in _DOMAIN_REASONS]
    # Arrival is a receipt fact, independent of classification or pillar review.
    # Such a source can be newly saved while its usability is still held.
    if root_node.get('historical_availability', {}).get('status') == 'matched' and not root_domain:
        if inventory:
            result['arrival'] = 'listed_previous_inventory'
        elif result['first_save_known'] and result['first_saved_at'] is not None:
            result['arrival'] = ('new_saved' if timestamp(result['first_saved_at']) > timestamp(case['last_review_at'])
                                 else 'previously_unlisted')
    combined = _summary([historical_check, current_check, *checks])
    return {**result, **combined}


def report_research_monitoring(connection, case_requests, *, as_of, now, research_root):
    """Report explicit research cases on a read snapshot; never creates work."""
    boundary, clock = timestamp(as_of, 'as_of'), timestamp(now, 'trusted now')
    if boundary > clock:
        raise ValueError('as_of cannot exceed trusted now')
    try:
        root = Path(research_root).resolve(strict=True)
    except (TypeError, OSError, RuntimeError) as error:
        raise ValueError('research_root must be an existing directory') from error
    if not root.is_dir():
        raise ValueError('research_root must be an existing directory')
    _validate(case_requests, root, clock)
    result = {'schema_version': 1, 'status': 'research_monitor_only', 'as_of': boundary.isoformat(),
              'checked_at': clock.isoformat(), 'cases': [], 'jobs_created': 0,
              'limitations': [
                  'Only explicitly supplied cases and saved public-disclosure sources are checked; no web or full-universe monitoring is performed.',
                  'Manifest recorded_at, last_review_at and issue_review_status are caller declarations; research-file first-save and prospective commitment are unverified.',
                  'Source binding and administrative due dates do not establish pillar impact, author-condition satisfaction, financial meaning, forecasts or investment adoption.',
                  'Classification changes, case revision history and IR replies are outside this first-version scope; current holds remain visible.',
                  'No questions, jobs, management dates, numerical theses, forecasts, messages or orders are generated.']}
    with _snapshot(connection):
        reader = _ScheduleReader(connection, clock.isoformat())
        result['sections'] = deepcopy(reader.sections)
        for case in case_requests:
            file_check, _ = _file(case['case_ref'], root)
            manifest = _summary([file_check, _check('held', 'manifest_recorded_after_as_of')
                                 if timestamp(case['recorded_at']) > boundary else _check('matched')])
            old = {item['source_id']: item for item in case['source_inventory'] or []}
            issues = []
            if case['source_inventory'] is None:
                issues.append(_check('unknown', 'previous_source_inventory_unknown'))
            identities = set(old); outside = 0
            if 'sources' in reader.tables:
                for row in connection.execute('SELECT id,data FROM sources'):
                    try:
                        source = object_value(parse_json(row[1]), 'saved source')
                    except ValueError:
                        issues.append(_check('unknown', 'saved_source_row_unreadable', source_id=row[0]))
                        continue
                    if source.get('company_id') != case['company_id']:
                        continue
                    if source.get('source_type') == 'public_disclosure':
                        identities.add(row[0])
                    else:
                        outside += 1
            else:
                issues.append(_check('unknown', 'sources_table_missing_or_unsupported'))
            sources = [_source(reader, identity, case, old.get(identity), boundary.isoformat())
                       for identity in sorted(identities)]
            changes = {name: [item['source_id'] for item in sources if item['arrival'] == kind]
                       for name, kind in (('new_saved_sources', 'new_saved'),
                                          ('previously_unlisted_sources', 'previously_unlisted'))}
            pending = [item['source_id'] for item in sources if item['issue_review_status'] != 'reviewed']
            management = _management(case, root, boundary, manifest)
            problems = [*issues, *[item for item in sources if item['status'] != 'matched']]
            if manifest['status'] != 'matched':
                problems.append(manifest)
            if management['status'] != 'matched':
                problems.append(management)
            triggered = bool(changes['new_saved_sources'] or changes['previously_unlisted_sources'] or pending or management['due'])
            status = ('insufficient_evidence' if problems else 'needs_manual_review' if triggered
                      else 'no_new_trigger_in_checked_scope')
            result['cases'].append({'id': case['id'], 'company_id': case['company_id'], 'issue_id': case['issue_id'],
                'status': status, 'manifest_check': manifest, 'source_changes': changes,
                'pending_issue_review_sources': pending, 'sources': sources,
                'source_count': len(sources) if 'sources' in reader.tables else None,
                'outside_scope_source_count': outside if 'sources' in reader.tables else None,
                'management_review_check': management, 'evidence_issues': problems,
                'reason_codes': list(dict.fromkeys(reason for check in problems for reason in check['reason_codes'])),
                'pillar_impact': None, 'investment_action': None, 'meaning_review_required': True,
                'manifest_prospectiveness': 'unverified', 'jobs_created': 0})
    result['coverage'] = {'case_count': len(case_requests),
        **{status + '_count': sum(case['status'] == status for case in result['cases'])
           for status in ('insufficient_evidence', 'needs_manual_review', 'no_new_trigger_in_checked_scope')}}
    return result
