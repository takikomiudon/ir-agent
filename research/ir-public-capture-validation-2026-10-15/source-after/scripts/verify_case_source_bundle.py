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
import math
import re
from urllib.parse import urlsplit
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ir_agent.models import integer, json_text, object_value, parse_json, text, timestamp, validate_source

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


# New native contract: opt-in only. Existing provider-based checks above stay
# unchanged; declaring this format never retrofits a legacy capture.
_MISSING_POINTER = object()
_NATIVE_BINDING = 'ir-public-source-binding'
_NATIVE_CAPTURE = 'ir-public-response-capture'
_NATIVE_SNAPSHOT_HASH = 'ir_agent.models.json_text/UTF-8'
_NOT_PERFORMED = ('source_id_verification', 'extractor_reproduction', 'citation_byte_binding',
                  'citation_semantic_verification', 'issuer_authenticity_verification',
                  'semantic_financial_verification', 'current_collection_permission',
                  'DB_first_save_verification')


def _native_shape(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(label + ' must contain exactly its required fields')
    return value


def _native_json(raw, label):
    try:
        value = parse_json(raw.decode('utf-8'))
        def finite(node):
            if isinstance(node, float) and not math.isfinite(node):
                raise ValueError('Non-finite JSON')
            if isinstance(node, dict):
                for child in node.values(): finite(child)
            elif isinstance(node, list):
                for child in node: finite(child)
        finite(value)
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise ValueError(label + ' must be finite UTF-8 JSON without duplicate keys') from None


def _native_pointer(value, pointer):
    if not isinstance(pointer, str) or (pointer and not pointer.startswith('/')):
        raise ValueError('Native record pointer must be an RFC6901 string')
    if pointer == '': return value
    tokens = pointer[1:].split('/')
    if any(re.search(r'~(?![01])', token) for token in tokens):
        raise ValueError('Native record pointer has an invalid escape')
    node = value
    for token in tokens:
        token = token.replace('~1', '/').replace('~0', '~')
        if isinstance(node, dict):
            if token not in node: return _MISSING_POINTER
            node = node[token]
        elif isinstance(node, list):
            if not re.fullmatch(r'0|[1-9][0-9]*', token, flags=re.ASCII):
                raise ValueError('Native array pointer requires a strict nonnegative index')
            # Avoid int conversion limits for an arbitrary, out-of-range index.
            if len(token) > len(str(len(node))): return _MISSING_POINTER
            index = int(token)
            if index >= len(node): return _MISSING_POINTER
            node = node[index]
        else:
            return _MISSING_POINTER
    return node


def _native_version(value, expected, label):
    if not isinstance(value, dict): raise ValueError(label + ' must be an object')
    text(value.get('format'), label + ' format')
    integer(value.get('version'), label + ' version', minimum=1)
    return value['format'] == expected and value['version'] == 1


def _native_time(value, label, *, nullable=False):
    if nullable and value is None: return None
    try:
        return timestamp(value, label)
    except (ValueError, OverflowError, UnicodeError):
        raise ValueError(label + ' must be an offset-aware timestamp') from None


def _native_url(value):
    try:
        text(value, 'Native URL')
        parsed = urlsplit(value)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.fragment
                or any(char.isspace() or ord(char) < 32 for char in value)):
            raise ValueError('Invalid URL reference')
        parsed.port
    except (ValueError, UnicodeError):
        raise ValueError('Native URL must be a valid HTTP reference without a fragment') from None


def _native_artifact(case_root, reference, label):
    _native_shape(reference, ('path', 'sha256', 'byte_count'), label + ' artifact')
    text(reference['path'], label + ' artifact path')
    if '://' in reference['path']: raise ValueError('Native artifact path cannot be a URL')
    text(reference['sha256'], label + ' artifact SHA')
    _hash(reference['sha256'], label + ' artifact SHA')
    integer(reference['byte_count'], label + ' artifact byte_count')
    try:
        result, raw = _artifact(case_root, reference['path'], reference['sha256'], label,
                                byte_count=reference['byte_count'])
    except (OSError, UnicodeError):
        raise ValueError('Native artifact could not be read safely') from None
    return {'name': label, **result}, raw


def _native_fixed(value, expected, label):
    if type(value) is not type(expected):
        raise ValueError(label + ' has an invalid parameter type')
    if isinstance(expected, dict):
        _native_shape(value, expected, label)
        for key in expected: _native_fixed(value[key], expected[key], label)
    elif isinstance(expected, list):
        if len(value) != len(expected): raise ValueError(label + ' has invalid parameters')
        for a, b in zip(value, expected): _native_fixed(a, b, label)
    elif value != expected:
        raise ValueError(label + ' has invalid parameters')


def _native_profile(extraction):
    profile = _native_shape(extraction['profile'], ('name', 'version'), 'Native extraction profile')
    text(profile['name'], 'Native profile name')
    integer(profile['version'], 'Native profile version', minimum=1)
    profiles = {
        'plain_utf8_preserve': {'decoder': 'utf-8', 'BOM': 'preserve', 'line_endings': 'preserve'},
        'html_visible_nodes_lf': {'decoder': 'utf-8', 'ignored_elements': ['script', 'style'],
            'convert_charrefs': True, 'node_whitespace': 'collapse', 'joiner': 'LF', 'terminal_LF': True},
        'pdftotext_layout': {'arguments': ['-layout'], 'output_encoding': 'UTF-8',
            'form_feeds': 'preserve', 'page_numbering': 'one_based'},
    }
    if profile['name'] not in profiles or profile['version'] != 1:
        return {'status': 'unknown', 'implementation_identity_verified': False,
                'reason_codes': ['unsupported_extraction_profile']}
    implementation = _native_shape(extraction['implementation'], ('name', 'version', 'sha256'),
                                    'Native extraction implementation')
    text(implementation['name'], 'Native implementation name')
    text(implementation['version'], 'Native implementation version')
    _hash(implementation['sha256'], 'Native implementation SHA')
    expected = profiles[profile['name']]
    if profile['name'] == 'html_visible_nodes_lf':
        parameters = extraction['parameters']
        if isinstance(parameters, dict) and parameters.get('decoder') == 'utf-8-sig':
            expected = {**expected, 'decoder': 'utf-8-sig'}
    _native_fixed(extraction['parameters'], expected, 'Native profile parameters')
    return {'status': 'recognized', 'implementation_identity_verified': False, 'reason_codes': []}


def _native_finish(result):
    artifact_checks = result['declared_artifact_bytes']['checks']
    binding_checks = result['transport_source_binding']['checks']
    def status(values):
        return 'mismatch' if 'mismatch' in values else 'unknown' if not values or 'unknown' in values else 'matched'
    result['declared_artifact_bytes']['status'] = status([x['status'] for x in artifact_checks])
    result['transport_source_binding']['status'] = status([x['status'] for x in binding_checks])
    result['status'] = status([result['format_support'], result['declared_artifact_bytes']['status'],
        result['transport_source_binding']['status'],
        'matched' if result['profile_declaration']['status'] == 'recognized' else 'unknown'])
    result['all_declared_bindings_agree'] = True if result['status'] == 'matched' else False if result['status'] == 'mismatch' else None
    reasons = [*result['reason_codes'], *result['profile_declaration']['reason_codes']]
    for check in [*artifact_checks, *binding_checks]: reasons.extend(check['reason_codes'])
    result['reason_codes'] = list(dict.fromkeys(reasons))
    return result


def verify_public_capture_binding(binding_path, *, repository_root) -> dict:
    """Audit one native-v1 declaration offline, without replay or certification.

    Raw source JSON is committed before validation defaults. Unknown formats or
    versions never fall back to a provider. This reports internal agreement of
    caller-controlled artifacts, not transport occurrence, issuer authenticity,
    extraction correctness, financial meaning or permission for a future GET.
    """
    if not isinstance(binding_path, (str, Path)) or not isinstance(repository_root, (str, Path)):
        raise ValueError('Native binding and repository root must be filesystem paths')
    try:
        repository = Path(repository_root).resolve(strict=True)
        if not repository.is_dir(): raise ValueError('Native repository root must be a directory')
        candidate = Path(binding_path)
        if '..' in candidate.parts or '\x00' in str(candidate):
            raise ValueError('Native binding must remain within repository root')
        path = candidate.resolve() if candidate.is_absolute() else _relative(repository, str(candidate))
        if not path.is_relative_to(repository): raise ValueError('Native binding must remain within repository root')
        raw_binding = path.read_bytes()
    except (OSError, UnicodeError, RuntimeError):
        raise ValueError('Native binding file or repository could not be read safely') from None
    binding = _native_json(raw_binding, 'Native binding')
    supported = _native_version(binding, _NATIVE_BINDING, 'Native binding')
    result = {'status': 'unknown', 'scope': 'native_declared_saved_bytes_and_fields_only',
        'binding_sha256': _sha(raw_binding), 'format_support': 'matched' if supported else 'unknown',
        'declared_artifact_bytes': {'status': 'unknown', 'checks': []},
        'transport_source_binding': {'status': 'unknown', 'checks': []},
        'profile_declaration': {'status': 'unknown', 'implementation_identity_verified': False, 'reason_codes': []},
        'all_declared_bindings_agree': None, 'source_snapshot_sha256': None, 'reason_codes': [],
        **{key: 'not_performed' for key in _NOT_PERFORMED},
        'limitations': ['All artifacts and expected declarations share the caller trust boundary.',
            'Files are assumed stable during this audit; no extraction tools, network or database are invoked.',
            'Times, URLs, implementation identity and publication claims are not independently authenticated.',
            'Matched means declared saved bytes and known fields agree; other verification dimensions remain not_performed.']}
    if not supported:
        result['reason_codes'] = ['unsupported_binding_format_or_version']; return _native_finish(result)
    _native_shape(binding, ('format', 'version', 'case_root', 'source', 'transport'), 'Native binding')
    case_root = _relative(repository, binding['case_root'])
    try:
        if case_root.exists() and not case_root.is_dir(): raise ValueError('Native case root must be a directory')
    except OSError:
        raise ValueError('Native case root could not be checked safely') from None
    source_ref = _native_shape(binding['source'], ('artifact', 'pointer', 'snapshot_sha256', 'snapshot_hash_profile'), 'Native source reference')
    transport_ref = _native_shape(binding['transport'], ('artifact', 'record_pointer'), 'Native transport reference')
    text(source_ref['snapshot_sha256'], 'Native source snapshot SHA'); _hash(source_ref['snapshot_sha256'], 'Native source snapshot SHA')
    if source_ref['snapshot_hash_profile'] != _NATIVE_SNAPSHOT_HASH:
        raise ValueError('Native source snapshot hash profile is unsupported')
    # Validate pointer syntax even if the pinned artifact happens to be absent.
    _native_pointer({}, source_ref['pointer']); _native_pointer({}, transport_ref['record_pointer'])
    checks = result['transport_source_binding']['checks']
    artifacts = result['declared_artifact_bytes']['checks']
    source = None
    source_check, source_raw = _native_artifact(case_root, source_ref['artifact'], 'source_artifact')
    artifacts.append(source_check)
    if source_check['status'] == 'matched':
        selected = _native_pointer(_native_json(source_raw, 'Native source artifact'), source_ref['pointer'])
        if selected is _MISSING_POINTER:
            checks.append(_comparison('source_pointer_target', None, True))
        else:
            if not isinstance(selected, dict): raise ValueError('Native source pointer must select an object')
            try:
                snapshot_sha = _sha(json_text(selected).encode('utf-8'))
            except (ValueError, UnicodeError, RecursionError):
                raise ValueError('Native source snapshot cannot be represented as finite UTF-8 JSON') from None
            result['source_snapshot_sha256'] = snapshot_sha
            snapshot_check = _comparison('source_snapshot_sha256', snapshot_sha, source_ref['snapshot_sha256'])
            checks.append(snapshot_check)
            if snapshot_check['status'] == 'matched':
                try:
                    source = validate_source(selected)
                    source['content'].encode('utf-8')
                except (ValueError, UnicodeError):
                    raise ValueError('Native source snapshot is invalid') from None
                checks.append(_comparison('public_disclosure_source_scope', True if source['source_type'] == 'public_disclosure' else None, True))
    else:
        checks.append(_comparison('source_artifact_binding', None, True))
    transport_check, transport_raw = _native_artifact(case_root, transport_ref['artifact'], 'transport_artifact')
    artifacts.append(transport_check)
    if transport_check['status'] != 'matched':
        checks.append(_comparison('transport_artifact_binding', None, True)); return _native_finish(result)
    record = _native_pointer(_native_json(transport_raw, 'Native transport artifact'), transport_ref['record_pointer'])
    if record is _MISSING_POINTER:
        checks.append(_comparison('transport_pointer_target', None, True)); return _native_finish(result)
    if not _native_version(record, _NATIVE_CAPTURE, 'Native transport record'):
        result['format_support'] = 'unknown'
        result['reason_codes'].append('unsupported_transport_format_or_version'); return _native_finish(result)
    _native_shape(record, ('format', 'version', 'request', 'response', 'artifacts', 'extraction'), 'Native transport record')
    request = _native_shape(record['request'], ('method', 'url', 'user_agent_configured', 'user_agent_prepared', 'started_at'), 'Native request')
    response = _native_shape(record['response'], ('url', 'status_code', 'complete_body', 'error', 'headers_received_at', 'body_completed_at', 'body_representation', 'content_length_header'), 'Native response')
    body_artifacts = _native_shape(record['artifacts'], ('raw', 'extracted_text'), 'Native body artifacts')
    if request['method'] != 'GET': raise ValueError('Native request method must be GET')
    _native_url(request['url']); _native_url(response['url'])
    text(request['user_agent_configured'], 'Native configured user agent'); text(request['user_agent_prepared'], 'Native prepared user agent')
    if response['status_code'] is not None:
        integer(response['status_code'], 'Native HTTP status', minimum=100)
        if response['status_code'] > 599: raise ValueError('Native HTTP status is invalid')
    if type(response['complete_body']) is not bool: raise ValueError('Native body completeness must be boolean')
    if response['error'] is not None: text(response['error'], 'Native transport error')
    if response['body_representation'] not in ('response_entity_after_content_decoding', 'wire_capture'):
        raise ValueError('Native body representation is invalid')
    length = response['content_length_header']
    if length is not None and (not isinstance(length, str) or not re.fullmatch(r'[0-9]+', length, flags=re.ASCII)):
        raise ValueError('Native Content-Length declaration must be decimal text or null')
    started = _native_time(request['started_at'], 'Native request start')
    headers = _native_time(response['headers_received_at'], 'Native response headers', nullable=True)
    completed = _native_time(response['body_completed_at'], 'Native body completion', nullable=True)
    success = response['status_code'] == 200 and response['complete_body'] and response['error'] is None
    if success and (headers is None or completed is None):
        raise ValueError('Native successful response must record headers and body completion')
    checks.append(_comparison('successful_complete_response', success, True))
    checks.append(_comparison('body_completion_consistency', completed is not None, response['complete_body']))
    checks.append(_comparison('request_response_URL', request['url'], response['url']))
    checks.append(_comparison('configured_prepared_UA', request['user_agent_configured'], request['user_agent_prepared']))
    checks.append(_comparison('response_entity_scope', True if response['body_representation'] == 'response_entity_after_content_decoding' else None, True))
    checks.append(_comparison('transport_time_order', started <= headers <= completed if headers is not None and completed is not None else None, True))
    if source is not None:
        _native_url(source['url'])
    checks.append(_comparison('response_source_URL', response['url'], source['url'] if source is not None else None))
    checks.append(_comparison('source_retrieved_completion_instant', _native_time(source['retrieved_at'], 'Native source retrieval') if source is not None else None, completed))
    raw_check, _ = _native_artifact(case_root, body_artifacts['raw'], 'raw')
    artifacts.append(raw_check)
    if record['extraction'] is None or body_artifacts['extracted_text'] is None:
        if success: raise ValueError('Native successful response must declare extracted text')
        checks.append(_comparison('failed_capture_has_no_successful_extraction', None, True)); return _native_finish(result)
    extraction = _native_shape(record['extraction'], ('profile', 'implementation', 'parameters', 'text'), 'Native extraction')
    if not isinstance(extraction['text'], str): raise ValueError('Native extraction text must be a string')
    try:
        record_text_bytes = extraction['text'].encode('utf-8')
    except UnicodeError:
        raise ValueError('Native extraction text must be valid UTF-8') from None
    result['profile_declaration'] = _native_profile(extraction)
    output_check, output_raw = _native_artifact(case_root, body_artifacts['extracted_text'], 'extracted_text')
    artifacts.append(output_check)
    if output_raw is not None:
        try: output_raw.decode('utf-8')
        except UnicodeError: raise ValueError('Native saved extraction must be valid UTF-8') from None
    # Artifact hash mismatch never becomes a trusted content comparison.
    trusted_output = output_raw if output_check['status'] == 'matched' else None
    source_bytes = source['content'].encode('utf-8') if source is not None else None
    checks.extend((_comparison('extraction_record_text_bytes', trusted_output, record_text_bytes),
                   _comparison('extraction_source_content_bytes', trusted_output, source_bytes),
                   _comparison('record_source_content_bytes', record_text_bytes, source_bytes)))
    return _native_finish(result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle_file')
    parser.add_argument('--repository-root', required=True)
    parser.add_argument('--capture-binding', action='store_true',
                        help='Interpret the positional file as an explicit native source-binding sidecar')
    args = parser.parse_args(argv)
    try:
        audit = verify_public_capture_binding if args.capture_binding else verify_case_source_bundle
        result = audit(args.bundle_file, repository_root=args.repository_root)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2, allow_nan=False)
    sys.stdout.write('\n')
    return 1 if result['status'] == 'mismatch' else 0


if __name__ == '__main__':
    raise SystemExit(main())
