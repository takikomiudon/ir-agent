#!/usr/bin/env python3
"""Fixed, finite EDINET startup. Optional data extra needed only for real fetch/parse."""
from __future__ import annotations
import argparse
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import quote, quote_plus
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.adapters.common import normalize_security_code, non_ordinary_security_code
from ir_agent.adapters.edinet import parse_edinet_package
from ir_agent.models import parse_json

BASE = 'https://api.edinet-fsa.go.jp/api/v2'
DATE = '2026-10-09'
OUTPUT = ROOT / 'data/edinet-6814-2026-10-09'
PLAN = {'security_code': '6814', 'date': DATE, 'doc_type_code': '160',
        'selection': 'ordinary-share6814; semi-annual160; non-amendment; xbrlFlag1; exactly one',
        'submission_date_basis': 'Issuer Q2 cover lists a planned semi-annual filing date; actual filing not presumed.',
        'output': 'data/edinet-6814-2026-10-09/', 'maximum_GETs': 2,
        'parser_source': 'instance', 'financial_adoption': False, 'DB_ingestion': False}


class StopRun(Exception):
    CODES = {'secret_reflection', 'http_status_not_200', 'response_size_or_length_invalid',
             'response_deadline', 'response_too_large', 'partial_response', 'transport_failed',
             'expanded_package_too_large', 'invalid_zip', 'invalid_list_JSON', 'invalid_list_metadata',
             'API_status_not_200', 'invalid_results', 'invalid_document_row', 'invalid_docID'}

    def __init__(self, code):
        self.code = code if code in self.CODES else 'startup_or_parse_failed'
        super().__init__(self.code)


def clock(): return datetime.now(timezone.utc).isoformat()


@contextmanager
def quiet():
    # SDK/HTTP exception text or diagnostics may contain authenticated URLs.
    level = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr): yield (stdout, stderr)
    finally: logging.disable(level)


def secret_check(raw, key):
    variants = {key.encode(), quote(key, safe='').encode(), quote_plus(key).encode(),
                json.dumps(key, ensure_ascii=True)[1:-1].encode()}
    if any(value and value in raw for value in variants): raise StopRun('secret_reflection')


def write_bytes(path, raw, key):
    secret_check(raw, key)
    with path.open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())


def write_json(path, value, key):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    write_bytes(path, raw, key)


def session():
    # No SDK retry/redirect transport: requests is supplied by the optional data dependencies.
    import requests
    result = requests.Session()
    result.mount('https://', requests.adapters.HTTPAdapter(max_retries=0))
    return result


def fetch(client, endpoint, params, key, maximum):
    start = clock(); deadline = time.monotonic() + 40
    try:
        with quiet(), client.get(endpoint, params={**params, 'Subscription-Key': key},
                headers={'User-Agent': 'Codex-IR-Research/0.1'}, stream=True,
                allow_redirects=False, verify=True, timeout=(10, 30)) as response:
            if response.status_code != 200: raise StopRun('http_status_not_200')
            length = response.headers.get('Content-Length')
            if length is not None and (not re.fullmatch(r'[0-9]+', length) or int(length) > maximum):
                raise StopRun('response_size_or_length_invalid')
            raw = bytearray()
            for part in response.iter_content(65536):
                if time.monotonic() > deadline: raise StopRun('response_deadline')
                if len(raw) + len(part) > maximum: raise StopRun('response_too_large')
                raw.extend(part)
            if not response.headers.get('Content-Encoding') and length is not None and len(raw) != int(length):
                raise StopRun('partial_response')
    except StopRun: raise
    except Exception: raise StopRun('transport_failed') from None
    body = bytes(raw); secret_check(body, key)
    return body, {'started_at': start, 'body_completed_at': clock(), 'byte_count': len(body),
                  'sha256': hashlib.sha256(body).hexdigest(), 'http_status': 200,
                  'complete_body': True, 'endpoint_without_credentials': endpoint,
                  'public_parameters': params, 'retry_count': 0, 'automatic_redirects': False}


def check_zip_secret(raw, key):
    # Check decoded members too: compressed key reflection must not be saved.
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            if sum(i.file_size for i in infos) > 128 * 1024 * 1024 or len(infos) > 20000:
                raise StopRun('expanded_package_too_large')
            total = 0
            for info in infos:
                with archive.open(info) as member:
                    data = member.read(128 * 1024 * 1024 + 1); total += len(data)
                    if total > 128 * 1024 * 1024: raise StopRun('expanded_package_too_large')
                    secret_check(data, key)
    except StopRun: raise
    except Exception: raise StopRun('invalid_zip') from None


def run(*, check=False, environ=None, output=OUTPUT, client_factory=session, parser=None):
    env = os.environ if environ is None else environ
    key = env.get('EDINET_API_KEY')
    configured = isinstance(key, str) and bool(key.strip())
    if check or not configured:
        return {'status': 'configuration_present_not_tested' if configured else 'needs_configuration',
                'EDINET_API_KEY_present': configured, 'plan': PLAN, 'GETs': 0}
    out = Path(output)
    if out.exists(): return {'status': 'existing_output_stop', 'GETs': 0}
    # Exclusive directory is the once-only sentinel, including uncertain/failed attempts.
    try: out.mkdir(parents=True, exist_ok=False)
    except FileExistsError: return {'status': 'existing_output_stop', 'GETs': 0}
    attempts = 0; client = None
    try:
        write_json(out / 'started.json', {'started_at': clock(), 'plan': PLAN}, key)
        with quiet(): client = client_factory()
        attempts += 1
        raw, receipt = fetch(client, BASE + '/documents.json', {'date': DATE, 'type': 2}, key, 8 * 1024 * 1024)
        # Decode and detect escaped reflection before preserving the successful body.
        try: listing = parse_json(raw.decode('utf-8'))
        except Exception:
            write_bytes(out / 'listing.json', raw, key)
            write_json(out / 'listing-receipt.json', receipt, key)
            raise StopRun('invalid_list_JSON') from None
        secret_check(json.dumps(listing, ensure_ascii=False).encode(), key)
        write_bytes(out / 'listing.json', raw, key)
        write_json(out / 'listing-receipt.json', receipt, key)
        if not isinstance(listing, dict) or not isinstance(listing.get('metadata'), dict): raise StopRun('invalid_list_metadata')
        if str(listing['metadata'].get('status')) != '200': raise StopRun('API_status_not_200')
        if 'StatusCode' in listing and str(listing['StatusCode']) != '200': raise StopRun('API_status_not_200')
        if not isinstance(listing.get('results'), list): raise StopRun('invalid_results')
        candidates = []
        for row in listing['results']:
            if not isinstance(row, dict): raise StopRun('invalid_document_row')
            try:
                ordinary = non_ordinary_security_code(row.get('secCode')) is None and normalize_security_code(row.get('secCode')) == '6814'
            except ValueError: ordinary = False
            description = row.get('docDescription')
            if ordinary and row.get('docTypeCode') == '160' and type(row.get('xbrlFlag')) in (str, int) and str(row.get('xbrlFlag')) == '1' and isinstance(description, str) and '訂正' not in description:
                candidates.append(row)
        write_json(out / 'selection.json', {'selected_at': clock(), 'candidate_count': len(candidates),
                    'criteria': PLAN['selection'], 'candidate_metadata': candidates,
                    'period_policy': 'Retain returned periodStart/periodEnd; do not infer dates or certify their meaning.'}, key)
        if len(candidates) != 1:
            status = 'no_unique_document_zero' if not candidates else 'no_unique_document_multiple'
        else:
            document = candidates[0]; doc_id = document.get('docID')
            if not isinstance(doc_id, str) or not re.fullmatch('[A-Z0-9]+', doc_id): raise StopRun('invalid_docID')
            attempts += 1
            package, receipt = fetch(client, BASE + '/documents/' + doc_id, {'type': 1}, key, 64 * 1024 * 1024)
            check_zip_secret(package, key)
            write_bytes(out / 'document.zip', package, key)
            write_json(out / 'document-receipt.json', receipt, key)
            with quiet() as diagnostics:
                parse = parser or parse_edinet_package
                bundle = parse(package, document, source='instance', retrieved_at=receipt['body_completed_at'])
            for captured in diagnostics: secret_check(captured.getvalue().encode(), key)
            secret_check(json.dumps(bundle, ensure_ascii=False, allow_nan=False).encode(), key)
            write_json(out / 'candidate-bundle.json', bundle, key)
            status = 'candidate_bundle_saved_meaning_review_required'
        result = {'status': status, 'GETs': attempts, 'financial_inputs_verified': False,
                  'meaning_review_required': True, 'DB_ingested': False, 'external_send': False}
    except StopRun as error:
        result = {'status': 'stopped', 'reason_code': error.code, 'GETs': attempts}
    except Exception:
        result = {'status': 'stopped', 'reason_code': 'startup_or_parse_failed', 'GETs': attempts}
    finally:
        if client is not None:
            try:
                with quiet(): client.close()
            except Exception: pass
    # No exception text, headers, authenticated URL or key value is persisted.
    try: write_json(out / 'result.json', result, key)
    except Exception: return {'status': 'stopped', 'reason_code': 'result_save_failed', 'GETs': attempts}
    return result


def main(argv=None, *, environ=None):
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--check', action='store_true'); options = args.parse_args(argv)
    result = run(check=options.check, environ=environ)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] in ('configuration_present_not_tested', 'candidate_bundle_saved_meaning_review_required') else 1


if __name__ == '__main__': raise SystemExit(main())
