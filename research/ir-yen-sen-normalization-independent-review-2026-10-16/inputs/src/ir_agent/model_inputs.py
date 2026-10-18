"""Audit the declared origin of canonical valuation inputs without adopting them.

This is a project adaptation of explicit, dated assumption tracking. It checks
saved numerical fields and records assumptions; it does not certify accounting
definitions, units, periods, forecasts, or a strategy's investment performance.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256

from .decision import _flatten, _source_field
from .disclosed_facts import reproduce_disclosed_fact_source
from .models import available, json_text, object_value, source_origins, text, timestamp, validate_source
from .valuation import _number, calculate_valuation

SOURCED_KINDS = frozenset({'reported_fact', 'issuer_guidance', 'external_estimate'})
KINDS = SOURCED_KINDS | {'explicit_assumption', 'synthetic_example'}
_FIELDS = {'kind', 'reference', 'rationale', 'recorded_at', 'author', 'source_id', 'value_path', 'unit', 'period'}


def _value_path(value):
    if not isinstance(value, list) or not value:
        raise ValueError('provenance.value_path must be a nonempty list of saved field names or indices')
    for part in value:
        if isinstance(part, str):
            text(part, 'provenance.value_path component')
        elif type(part) is not int or part < 0:
            raise ValueError('provenance.value_path components must be field names or nonnegative integer indices')


def _origin_issues(source_id, sources, company_id, boundary, *, synthetic):
    visited, active, lineage, issues = set(), set(), [], []
    pending = [(source_id, False)]
    while pending:
        identifier, exiting = pending.pop()
        if exiting:
            active.remove(identifier)
            visited.add(identifier)
            continue
        if identifier in active:
            issues.append('cyclic_source_provenance')
            continue
        if identifier in visited:
            continue
        source = sources.get(identifier)
        if source is None:
            issues.append('missing_source_snapshot' if identifier == source_id else 'missing_origin_source_snapshot')
            continue
        lineage.append(identifier)
        if source['company_id'] != company_id:
            issues.append('source_company_mismatch')
        if not available(source, boundary):
            issues.append('source_not_available_at_recording')
        if source['metadata'].get('synthetic') is True and not synthetic:
            issues.append('synthetic_source_requires_synthetic_context')
        classification = source['metadata'].get('information_status')
        if ((source['source_type'] == 'ir_reply' and classification != 'public_clarification')
                or classification not in (None, 'public_disclosure', 'public_clarification')):
            issues.append('source_information_held_for_review')
        active.add(identifier)
        pending.append((identifier, True))
        pending.extend((parent, False) for parent in source_origins(source))
    return list(dict.fromkeys(issues)), lineage


def audit_model_inputs(request: dict) -> dict:
    request = deepcopy(object_value(request, 'model input audit'))
    if set(request) - {'as_of', 'company_id', 'valuation', 'sources', 'provenance', 'synthetic'}:
        raise ValueError('Unknown model input audit field')
    as_of = timestamp(request.get('as_of'), 'audit.as_of')
    company_id = text(request.get('company_id'), 'audit.company_id')
    synthetic = request.get('synthetic', False)
    if type(synthetic) is not bool:
        raise ValueError('audit.synthetic must be boolean')
    valuation = object_value(request.get('valuation'), 'audit.valuation')
    # A unit reference price checks the existing calculator's full contract;
    # it is neither supplied as a market observation nor returned as an input.
    computed = calculate_valuation(valuation, '1')
    canonical = _flatten(valuation)
    unset_probabilities = sorted(path for path, value in canonical.items()
                                 if value is None and path.endswith('.probability'))
    values = {path: _number(value, path) for path, value in canonical.items()
              if value is not None and not path.endswith('.method')}
    provenance = object_value(request.get('provenance', {}), 'audit.provenance')
    if set(provenance) - values.keys():
        raise ValueError('Unknown provenance path; reference only canonical numerical valuation inputs')
    raw_sources = request.get('sources', [])
    if not isinstance(raw_sources, list):
        raise ValueError('audit.sources must be a list')
    sources = {}
    for raw in raw_sources:
        source = validate_source(raw)
        if source['id'] in sources:
            raise ValueError('Duplicate source IDs in audit snapshots')
        sources[source['id']] = source
    rows, missing, consumed, normalization_cache = [], [], set(), {}
    for path in sorted(values):
        row = {'path': path, 'value': format(values[path], 'f'), 'status': 'needs_review',
               'reason_codes': [], 'meaning_review_status': 'unreviewed',
               'meaning_checks': ['unit_not_verified', 'period_not_verified', 'definition_not_verified',
                                  'authorship_and_forecast_status_not_verified']}
        if path not in provenance:
            missing.append(path)
            row.update(reason_codes=['missing_provenance'], missing_meaning_fields=['unit', 'period'])
            rows.append(row)
            continue
        origin = object_value(provenance[path], f'provenance.{path}')
        if set(origin) - _FIELDS:
            raise ValueError('Unknown provenance descriptor field')
        kind = origin.get('kind')
        if not isinstance(kind, str) or kind not in KINDS:
            raise ValueError('Invalid model input provenance kind')
        for field in ('reference', 'rationale', 'recorded_at', 'author'):
            text(origin.get(field), f'provenance.{path}.{field}')
        recorded = timestamp(origin['recorded_at'], f'provenance.{path}.recorded_at')
        if kind == 'synthetic_example' and not synthetic:
            raise ValueError('Synthetic example inputs cannot be promoted to a non-synthetic audit')
        for field in ('unit', 'period'):
            if origin.get(field) is not None:
                text(origin[field], f'provenance.{path}.{field}')
        row.update(deepcopy(origin), missing_meaning_fields=[field for field in ('unit', 'period') if origin.get(field) is None])
        if recorded > as_of:
            row['reason_codes'].append('provenance_not_available_at_audit')
        source_id, value_path = origin.get('source_id'), origin.get('value_path')
        if source_id is not None:
            text(source_id, f'provenance.{path}.source_id')
            issues, lineage = _origin_issues(source_id, sources, company_id, min(recorded, as_of), synthetic=synthetic)
            row['reason_codes'].extend(issues)
            row['source_lineage_ids'] = lineage
            consumed.update(lineage)
            normalization_checks = []
            for identifier in lineage:
                if identifier not in normalization_cache:
                    normalization_cache[identifier] = reproduce_disclosed_fact_source(sources[identifier], sources)
                check = normalization_cache[identifier]
                if check['applicable']:
                    normalization_checks.append({key: deepcopy(value) for key, value in check.items()
                                                 if key != 'fact_kinds'})
                    row['reason_codes'].extend(check['reason_codes'])
            if normalization_checks:
                row['normalization_checks'] = normalization_checks
        elif kind in SOURCED_KINDS:
            row['reason_codes'].append('missing_source_id')
        if value_path is not None:
            _value_path(value_path)
            direct_check = normalization_cache.get(source_id, {})
            if (direct_check.get('applicable') and len(value_path) == 4
                    and value_path[:2] == ['content', 'facts'] and type(value_path[2]) is int
                    and value_path[3] == 'value'):
                facts = direct_check.get('fact_kinds', [])
                if 0 <= value_path[2] < len(facts):
                    fact = facts[value_path[2]]
                    row.update(source_fact_id=fact['id'], source_fact_kind=fact['kind'])
                    if kind in SOURCED_KINDS and kind != fact['kind']:
                        row['reason_codes'].append('disclosed_fact_kind_mismatch')
            if source_id is None:
                row['reason_codes'].append('value_path_without_source_id')
            elif source_id in sources:
                try:
                    source_value = _source_field(sources[source_id], value_path)
                except ValueError:
                    row['reason_codes'].append('source_field_not_found')
                else:
                    try:
                        number = _number(source_value, 'saved source field')
                    except ValueError:
                        row['reason_codes'].append('source_field_not_numeric')
                    else:
                        row['source_value'] = format(number, 'f')
                        if number != values[path]:
                            row['reason_codes'].append('source_value_mismatch')
        elif kind in SOURCED_KINDS:
            row['reason_codes'].append('missing_value_path')
        if not row['reason_codes']:
            row['status'] = 'source_value_matched' if kind in SOURCED_KINDS else kind
        row['reason_codes'] = list(dict.fromkeys(row['reason_codes']))
        rows.append(row)
    if any(row['status'] == 'needs_review' for row in rows):
        status = 'needs_review'
    elif any(row['status'] == 'synthetic_example' for row in rows):
        status = 'synthetic_example'
    elif any(row['status'] == 'explicit_assumption' for row in rows):
        status = 'assumptions_declared'
    else:
        status = 'source_values_matched'
    return {'company_id': company_id, 'as_of': as_of.isoformat(), 'synthetic': synthetic,
            'status': status, 'required_paths': sorted(values), 'missing_paths': missing, 'inputs': rows,
            'aggregation': valuation.get('aggregation', 'weighted'),
            'expected_value_available': computed['expected_value_jpy'] is not None,
            'unset_probability_paths': unset_probabilities,
            'meaning_review_required': True, 'financial_inputs_verified': False,
            'source_snapshot_sha256': {identifier: sha256(json_text(sources[identifier]).encode()).hexdigest()
                                       for identifier in sorted(consumed) if identifier in sources},
            'limitations': ['Numerical equality with a saved field does not verify units, periods, accounting definitions, authorship, or the meaning of a forecast.',
                            'Missing unit or period labels remain explicit meaning-review tasks; supplied labels are not automatically verified.',
                            'Explicit assumptions and synthetic examples are recorded declarations, not recommended or empirically validated inputs.',
                            'Audit status concerns only configured numerical paths; unset probabilities are neither audited nor supplied and do not produce an expected value.',
                            'This standalone audit reads only supplied source snapshots and does not consult live database classification corrections.',
                            'Known disclosed-fact normalization is replayed against its supplied original; unknown providers are not inferred to use that contract, and whole-snapshot commitments are reported separately from content reproduction.',
                            'No values, scenario probabilities, costs, or trading conditions are inferred; saved timestamps are supplied records, not independent proof of collection.']}
