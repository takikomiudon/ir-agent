#!/usr/bin/env python3
"""Check declared saved-case bytes offline; never certify financial meaning.

Scope: finite_initial_issuer_research and
finite_issuer_statement_calendar_followup metadata (1332/135A convention).
No GET, extraction, source-ID derivation, ingestion or file mutation occurs.
Hashes are comparisons against caller-controlled metadata, not proof that the
issuer published a document or that a financial interpretation is correct.
CLI exit 0 means the audit completed, including unknown/empty; inspect status.
Exit 1 reports mismatched bytes; exit 2 reports malformed input or an I/O error.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ir_agent.models import integer, json_text, object_value, parse_json, text, validate_source

_PROVIDERS = ('finite_initial_issuer_research', 'finite_issuer_statement_calendar_followup')
_EXTRACTIONS = ('plain_text', 'html_visible_text', 'pdf_text')


def _sha(raw):
    return sha256(raw).hexdigest()


def _hash(value, label):
    if value is not None:
        text(value, label)
        if len(value) != 64 or any(char not in '0123456789abcdef' for char in value):
            raise ValueError(label + ' must be a lowercase SHA-256')


def _relative(base, value):
    text(value, 'saved case path')
    candidate = Path(value)
    if candidate.is_absolute() or '..' in candidate.parts or '\x00' in value:
        raise ValueError('Saved case references must be relative and remain within their case root')
    try:
        resolved = (base / candidate).resolve()
    except (OSError, RuntimeError) as error:
        raise ValueError('Saved case reference cannot be resolved safely') from error
    if not resolved.is_relative_to(base):
        raise ValueError('Saved case reference escapes its case root')
    return resolved


def _artifact(case_root, relative, expected, label, *, byte_count=None):
    if relative is not None:
        text(relative, label + ' file')
    _hash(expected, label + ' SHA')
    if byte_count is not None:
        integer(byte_count, label + ' byte_count')
    result = {'path': relative, 'status': 'unknown', 'expected_sha256': expected,
              'actual_sha256': None, 'actual_byte_count': None, 'reason_codes': []}
    if relative is None:
        result['reason_codes'] = [label + '_file_unspecified']; return result, None
    path = _relative(case_root, relative)
    if not path.is_file():
        result['reason_codes'] = [label + '_file_missing']; return result, None
    raw = path.read_bytes()
    result.update(actual_sha256=_sha(raw), actual_byte_count=len(raw))
    if expected is None:
        result['reason_codes'].append(label + '_sha_unspecified')
    elif result['actual_sha256'] != expected:
        result['reason_codes'].append(label + '_sha_mismatch')
    if byte_count is not None and len(raw) != byte_count:
        result['reason_codes'].append(label + '_byte_count_mismatch')
    result['status'] = ('mismatch' if any(reason.endswith('_mismatch') for reason in result['reason_codes'])
                        else 'unknown' if result['reason_codes'] else 'matched')
    return result, raw


def _comparison(name, actual, expected):
    unknown = actual is None or expected is None
    return {'name': name, 'status': 'unknown' if unknown else 'matched' if actual == expected else 'mismatch',
            'reason_codes': [name + '_unspecified'] if unknown else [] if actual == expected else [name + '_mismatch']}


def _source_audit(source, repository):
    checked = validate_source(source)
    metadata = checked['metadata']
    result = {'id': checked['id'], 'source_snapshot_sha256': _sha(json_text(source).encode('utf-8')),
              'source_content_sha256': _sha(checked['content'].encode('utf-8')), 'source_content_byte_count': len(checked['content'].encode('utf-8')),
              'status': 'unknown', 'case_directory': None, 'checks': [], 'reason_codes': [],
              'source_id_verification': 'not_performed', 'semantic_financial_verification': 'not_performed'}
    provider = metadata.get('provider')
    if provider is not None: text(provider, 'metadata.provider')
    if provider not in _PROVIDERS:
        result['reason_codes'] = ['unsupported_or_unspecified_provider']; return result
    extraction = metadata.get('extraction')
    if extraction is not None: object_value(extraction, 'metadata.extraction')
    extraction = extraction or {}
    kind = extraction.get('kind')
    if kind is not None: text(kind, 'extraction.kind')
    if kind not in _EXTRACTIONS:
        result['reason_codes'] = ['unsupported_or_unspecified_extraction']; return result
    case_directory = metadata.get('saved_case_directory')
    if case_directory is None:
        result['reason_codes'] = ['saved_case_directory_unspecified']; return result
    case_root = _relative(repository, case_directory)
    result['case_directory'] = case_root.relative_to(repository).as_posix()
    raw_check, raw = _artifact(case_root, metadata.get('original_raw_file'), metadata.get('original_raw_sha256'),
        'raw', byte_count=metadata.get('original_raw_byte_count'))
    if metadata.get('original_raw_byte_count') is None:
        raw_check['reason_codes'].append('raw_byte_count_unspecified')
        if raw_check['status'] == 'matched': raw_check['status'] = 'unknown'
    snapshot_check, snapshot_raw = _artifact(case_root, metadata.get('original_transport_snapshot'),
        metadata.get('original_transport_snapshot_sha256'), 'transport_snapshot')
    extraction_check, extracted_raw = _artifact(case_root, extraction.get('saved_file'), extraction.get('sha256'), 'extraction')
    result['checks'].extend(({'name': 'raw', **raw_check}, {'name': 'transport_snapshot', **snapshot_check},
                             {'name': 'extraction', **extraction_check}))
    content_raw = checked['content'].encode('utf-8')
    if extracted_raw is not None:
        try:
            # Decode bytes directly: universal-newline translation must not
            # turn CRLF into LF before comparing the saved source content.
            extracted_raw.decode('utf-8')
        except UnicodeError as error:
            raise ValueError('Saved extraction must be valid UTF-8') from error
    result['checks'].append(_comparison('extraction_source_content_bytes',
        extracted_raw, content_raw))
    if snapshot_raw is not None and snapshot_check['status'] == 'matched':
        try:
            snapshot = object_value(parse_json(snapshot_raw.decode('utf-8')), 'transport snapshot')
        except (ValueError, UnicodeError) as error:
            raise ValueError('Transport snapshot must contain valid finite JSON without duplicate keys') from error
        # These are the two inspected finite-provider contracts, not a search
        # for a convenient hash among unknown legacy snapshot fields.
        raw_hash_field = 'sha256' if provider == 'finite_initial_issuer_research' else 'raw_sha256'
        expected_raw_sha = snapshot.get(raw_hash_field); _hash(expected_raw_sha, 'transport raw SHA')
        expected_count = snapshot.get('byte_count')
        if expected_count is not None: integer(expected_count, 'transport byte_count')
        result['checks'].append(_comparison('transport_raw_sha', _sha(raw) if raw is not None else None, expected_raw_sha))
        result['checks'].append(_comparison('transport_raw_byte_count', len(raw) if raw is not None else None, expected_count))
        snapshot_text = snapshot.get('text')
        if snapshot_text is not None and not isinstance(snapshot_text, str):
            raise ValueError('Transport text must be text or null')
        result['checks'].append(_comparison('transport_source_content_bytes',
            snapshot_text.encode('utf-8') if snapshot_text is not None else None, content_raw))
    else:
        result['checks'].append({'name': 'transport_content_binding', 'status': 'unknown', 'reason_codes': ['transport_snapshot_not_matched']})
    statuses = [check['status'] for check in result['checks']]
    result['status'] = 'mismatch' if 'mismatch' in statuses else 'unknown' if 'unknown' in statuses else 'matched'
    result['reason_codes'] = list(dict.fromkeys(reason for check in result['checks'] for reason in check['reason_codes']))
    return result


def verify_case_source_bundle(bundle_path, *, repository_root) -> dict:
    """Audit only the declared saved-case byte contract, without rewriting it.

    A positive result means nonempty declared files/metadata agree. The caller
    controls both; authenticity, semantic extraction and financial meaning stay
    unverified. Missing facts/files/providers remain unknown. Empty is explicit.
    """
    if not isinstance(repository_root, (str, Path)) or not isinstance(bundle_path, (str, Path)):
        raise ValueError('Bundle and repository root must be filesystem paths')
    repository = Path(repository_root).resolve(strict=True)
    if not repository.is_dir(): raise ValueError('repository_root must be a directory')
    candidate = Path(bundle_path)
    if '..' in candidate.parts: raise ValueError('Bundle must remain within repository_root')
    bundle = candidate.resolve() if candidate.is_absolute() else (repository / candidate).resolve()
    if not bundle.is_relative_to(repository): raise ValueError('Bundle must remain within repository_root')
    raw = bundle.read_bytes()
    try:
        value = object_value(parse_json(raw.decode('utf-8')), 'case source bundle')
    except (ValueError, UnicodeError) as error:
        raise ValueError('Bundle must contain valid finite JSON without duplicate keys') from error
    if type(value.get('schema_version')) is not int or value['schema_version'] != 1:
        raise ValueError('Bundle schema_version must be 1')
    sources = value.get('sources')
    if not isinstance(sources, list): raise ValueError('Bundle sources must be a list')
    audits = [_source_audit(object_value(source, 'bundle source'), repository) for source in sources]
    if len({audit['id'] for audit in audits}) != len(audits): raise ValueError('Duplicate bundle source ID')
    counts = {state: sum(audit['status'] == state for audit in audits) for state in ('matched', 'mismatch', 'unknown')}
    status = 'empty' if not audits else 'mismatch' if counts['mismatch'] else 'unknown' if counts['unknown'] else 'matched'
    return {'status': status, 'scope': 'declared_saved_case_bytes_only', 'bundle_path': bundle.relative_to(repository).as_posix(),
        'bundle_sha256': _sha(raw), 'source_count': len(audits), 'counts': counts,
        'all_declared_bytes_match': True if status == 'matched' else False if status == 'mismatch' else None,
        'sources': audits, 'limitations': ['Expected hashes and saved files share the caller trust boundary; matching is not independent authenticity evidence.',
            'No raw semantic re-extraction, source-ID derivation, citation support, financial validation, classification or ingestion is performed.',
            'Files are assumed stable during this offline audit; CRLF and all other UTF-8 bytes are preserved.',
            'Empty and unknown results do not establish a successful source verification.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle_file')
    parser.add_argument('--repository-root', required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_case_source_bundle(args.bundle_file, repository_root=args.repository_root)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2, allow_nan=False)
    sys.stdout.write('\n')
    return 1 if result['status'] == 'mismatch' else 0


if __name__ == '__main__':
    raise SystemExit(main())
