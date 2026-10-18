"""Four-field provider stock snapshot from frozen HTML; no HTTP, DB or JS.

Initial --build records the real extraction clock once. Default execution only
reproduces/compares that saved extraction; it does not invent a fresh retrieval.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ORIGIN = HERE.parent / 'external-report-discovery'
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.adapters.common import canonical_json, stable_source_id
from ir_agent.decision import _source_field
from ir_agent.models import json_text, parse_json, timestamp, validate_source

PARENT_ID = 'case-public:a14372edbaf8c2897b8553a1a93dc1e4b1dc63859a14ce2f716bdb571a862e7b'
FIELDS = ('ticker', 'currency', 'price', 'quotedAt')
EXPECTED = {'ticker': '1379', 'currency': 'JPY', 'price': 2048, 'quotedAt': '2026-10-14T06:30:00.000Z'}


def digest(raw):
    return sha256(raw).hexdigest()


def read(path):
    return parse_json(path.read_bytes().decode('utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def location(path):
    return str(path.relative_to(ROOT))


def repo_file(relative):
    raw = Path(relative)
    if raw.is_absolute() or '..' in raw.parts:
        raise ValueError('Expected a repository-relative evidence path')
    resolved = (ROOT / raw).resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError('Evidence path escapes repository')
    return resolved


def literal_state(raw_text):
    matches = list(re.finditer(r'\bwindow\.state\s*=\s*', raw_text))
    if len(matches) != 1:
        raise ValueError('Exactly one literal window.state assignment is required')
    start = matches[0].end()
    _, length = json.JSONDecoder().raw_decode(raw_text[start:])
    end = start + length
    if not raw_text[end:].lstrip().startswith(';'):
        raise ValueError('Literal JSON assignment must end with a semicolon')
    payload = raw_text[start:end]
    state = parse_json(payload)
    if not isinstance(state, dict):
        raise ValueError('Embedded state must be an object')
    return state, {'marker_count': 1, 'raw_character_start': start, 'raw_character_end': end,
        'json_payload_sha256': digest(payload.encode('utf-8')), 'wrapper_suffix_semicolon_valid': True}


def selected_stock(state, origin_retrieved_at):
    company = state.get('company')
    if not isinstance(company, dict) or company.get('tick') != '1379':
        raise ValueError('Provider company tick differs from 1379')
    stock = company.get('stock')
    if not isinstance(stock, dict) or any(field not in stock for field in FIELDS):
        raise ValueError('Required four raw stock fields are missing')
    selected = {field: stock[field] for field in FIELDS}
    if (selected['ticker'] != '1379' or selected['currency'] != 'JPY'
            or type(selected['price']) is not int or selected['price'] <= 0):
        raise ValueError('Expected positive integer JPY price for ticker 1379')
    if timestamp(selected['quotedAt']) > timestamp(origin_retrieved_at):
        raise ValueError('Provider quote timestamp is after original transport retrieval')
    return selected


def rebuild(extracted_at):
    parent_bundle = read(ORIGIN / 'source-bundle.json')
    parent = next(s for s in parent_bundle['sources'] if s['id'] == PARENT_ID)
    validate_source(parent)
    if parent['company_id'] != 'jp:1379':
        raise ValueError('Original source company mismatch')
    meta = parent['metadata']; base = repo_file(meta['saved_case_directory'])
    raw_path = base / meta['original_raw_file']
    capture_path = base / meta['original_transport_snapshot']
    state_path = base / meta['extraction']['embedded_state_file']
    guard_path = base / meta['extraction']['original_JSON_extraction_record']
    report_text_path = base / meta['extraction']['saved_file']
    report_html_path = base / meta['extraction']['extracted_report_HTML_file']
    original_files = [ORIGIN / 'source-bundle.json', raw_path, capture_path, state_path,
                     guard_path, report_text_path, report_html_path, ORIGIN / '02.txt']
    existing_hashes = {location(path): digest(path.read_bytes()) for path in original_files}
    raw = raw_path.read_bytes(); html = raw.decode('utf-8')
    capture = read(capture_path)
    assert capture['http_status'] == 200 and capture['complete_body'] is True
    assert digest(raw) == meta['original_raw_sha256'] == capture['raw_sha256']
    assert len(raw) == meta['original_raw_byte_count'] == capture['byte_count']
    assert digest(capture_path.read_bytes()) == meta['original_transport_snapshot_sha256']
    assert html == capture['text'] == (ORIGIN / '02.txt').read_bytes().decode('utf-8')
    assert parent['retrieved_at'] == capture['retrieved_at'] == '2026-10-15T05:28:30.141744+00:00'
    assert digest(state_path.read_bytes()) == meta['extraction']['embedded_state_sha256']
    state, guard = literal_state(html)
    old_guard = read(guard_path)
    assert all(guard[key] == old_guard[key] for key in guard)
    assert state == read(state_path)
    assert state['originalUrl'] == '/ja/companies/1379'
    assert state['reportContent'].encode('utf-8') == report_html_path.read_bytes()
    assert digest(report_html_path.read_bytes()) == meta['extraction']['extracted_report_HTML_sha256']
    assert digest(report_text_path.read_bytes()) == meta['extraction']['sha256']
    assert parent['content'] == report_text_path.read_bytes().decode('utf-8')
    assert meta['extraction']['field_path'] == ['reportContent']
    assert stable_source_id('case-public', company_id=parent['company_id'], url=parent['url'],
                            content=parent['content'], metadata=parent['metadata']) == PARENT_ID
    selected = selected_stock(state, parent['retrieved_at'])
    assert selected == EXPECTED
    assert timestamp(parent['retrieved_at']) <= timestamp(extracted_at)
    payload = {'company_id': 'jp:1379', 'currency': selected['currency'], 'price_jpy': str(selected['price']),
        'observed_at': selected['quotedAt'], 'observation_precision': 'instant',
        'observation_basis': 'provider_reported_timestamp', 'raw_stock_fields': selected}
    encoded = canonical_json(payload)
    bindings = [{'raw_field_path': ['company', 'stock', field], 'raw_value': selected[field],
                 'normalized_field': {'ticker': 'company_id', 'currency': 'currency', 'price': 'price_jpy', 'quotedAt': 'observed_at'}[field]}
                for field in FIELDS]
    proof = {'original_source_id': PARENT_ID, 'original_source_snapshot_sha256': digest(json_text(parent).encode()),
        'original_source_content_role': 'Report visible text only; stock is absent as a structured field. Raw transport/embedded-state paths below are necessary for the stock binding.',
        'original_raw_file': location(raw_path), 'original_raw_sha256': digest(raw), 'original_raw_byte_count': len(raw),
        'original_transport_snapshot': location(capture_path), 'original_transport_snapshot_sha256': digest(capture_path.read_bytes()),
        'embedded_state_file': location(state_path), 'embedded_state_file_sha256': digest(state_path.read_bytes()),
        'original_guard_file': location(guard_path), 'original_guard_file_sha256': digest(guard_path.read_bytes()),
        'guard_reproduced': guard, 'company_identity_checks': {'parent_company_id': 'jp:1379', 'company_tick_matches_ticker': True,
            'original_route_matches_1379': True}, 'field_bindings': bindings,
        'raw_selected_fields': selected, 'derived_content_sha256': digest(encoded.encode('utf-8')),
        'extraction_recorded_at': extracted_at, 'no_javascript_or_network': True}
    metadata = {'provider': 'shared_research', 'publisher_display_name': 'Shared Research', 'dataset': 'company.stock',
        'normalization_version': 1, 'original_source_ids': [PARENT_ID],
        'original_transport_retrieved_at': parent['retrieved_at'], 'observation_precision': 'instant',
        'observation_basis': 'provider_reported_timestamp', 'currency': 'JPY',
        'publication_time_known': False, 'saved_case_directory': 'research/ir-case-studies-2026-10-15',
        'original_raw_file': str(raw_path.relative_to(ROOT / 'research/ir-case-studies-2026-10-15')),
        'original_raw_sha256': digest(raw), 'original_raw_byte_count': len(raw),
        'original_transport_snapshot': str(capture_path.relative_to(ROOT / 'research/ir-case-studies-2026-10-15')),
        'original_transport_snapshot_sha256': digest(capture_path.read_bytes()),
        'raw_stock_binding': proof,
        'extraction': {'kind': 'strict_static_JSON_four_stock_fields',
            'saved_file': '1379/provider-market-snapshot/normalized-stock.json',
            'sha256': digest(encoded.encode('utf-8')), 'method': 'Reparse raw window.state literal JSON with unique/finite guards; compare saved embedded state; read only company.stock ticker/currency/price/quotedAt.'},
        'financial_inputs_verified': False, 'model_adopted': False, 'financial_values_automatically_adopted': False,
        'provider_reported_snapshot_only': True, 'exchange_independently_verified': False, 'live_quote_verified': False,
        'price_type': None, 'price_adjustment_basis': None, 'feed_delay_verified': False,
        'out_of_scope_fields_not_extracted': ['marketCap', 'sharesOutstanding', 'priceToEarningsRatio', 'priceToBookRatio', 'returnOnEquity']}
    identity = stable_source_id('sharedresearch-stock', company_id='jp:1379', url=parent['url'], content=encoded, metadata=metadata)
    source = validate_source({'id': identity, 'company_id': 'jp:1379', 'title': 'Shared Research — provider-reported stock snapshot for 1379 at 2026-10-14T06:30:00.000Z',
        'url': parent['url'], 'source_type': 'market_data', 'published_at': None, 'retrieved_at': extracted_at,
        'content': encoded, 'requires_research': False, 'metadata': metadata})
    quote = {'company_id': 'jp:1379', 'source_id': identity, 'price_jpy': '2048', 'currency': 'JPY',
        'observed_at': selected['quotedAt'], 'retrieved_at': extracted_at, 'observation_precision': 'instant',
        'observation_basis': 'provider_reported_timestamp', 'price_path': ['content', 'price_jpy'],
        'observed_at_path': ['content', 'observed_at']}
    assert _source_field(source, quote['price_path']) == quote['price_jpy']
    assert _source_field(source, quote['observed_at_path']) == quote['observed_at']
    return source, quote, proof, existing_hashes


def negative_checks():
    base = {'company': {'tick': '1379', 'stock': deepcopy(EXPECTED)}}
    variants = []
    for key, bad in [('ticker', '1332'), ('currency', 'USD'), ('price', True), ('quotedAt', '2026-10-16T00:00:00Z')]:
        bad_state = deepcopy(base); bad_state['company']['stock'][key] = bad; variants.append(bad_state)
    for value in variants:
        try: selected_stock(value, '2026-10-15T05:28:30.141744+00:00')
        except ValueError: pass
        else: raise AssertionError('Malformed raw stock accepted')
    for raw in ('window.state={}; window.state={};', 'window.state={"a":1,"a":2};', 'window.state={"a":NaN};', 'window.state={} trailing'):
        try: literal_state(raw)
        except ValueError: pass
        else: raise AssertionError('Invalid literal/JSON guard accepted')
    return {'stock_mismatch_or_type_or_future_timestamp_cases': len(variants), 'literal_guard_cases': 4}


def verify():
    baseline = read(HERE / 'baseline.json')
    source, quote, proof, originals = rebuild(baseline['actual_extracted_at'])
    assert originals == baseline['original_files']
    bundle = read(HERE / 'source-bundle.json')
    assert bundle == {'schema_version': 1, 'companies': [], 'sources': [source], 'theses': []}
    assert read(HERE / 'quote-candidate.json') == quote
    assert read(HERE / 'stock-field-extraction.json') == proof
    assert (HERE / 'normalized-stock.json').read_bytes() == source['content'].encode('utf-8')
    assert set(parse_json(source['content'])['raw_stock_fields']) == set(FIELDS)
    assert source['published_at'] is None and source['requires_research'] is False
    assert source['metadata']['original_source_ids'] == [PARENT_ID]
    assert source['metadata']['financial_inputs_verified'] is False and source['metadata']['model_adopted'] is False
    return {'status': 'reproduced_provider_claim_only', 'verified_at': datetime.now(timezone.utc).isoformat(),
        'derived_source_id': source['id'], 'source_snapshot_sha256': digest(json_text(source).encode()),
        'raw_fields_checked': 4, 'source_contract_and_quote_paths_checked': True,
        'original_files_unchanged': True, 'raw_guard_and_embedded_JSON_reproduced': True,
        'negative_checks': negative_checks(), 'financial_inputs_verified': False, 'model_adopted': False,
        'database_accesses': 0, 'HTTP_requests': 0, 'javascript_executed': False}


def main():
    if sys.argv[1:] not in ([], ['--build']):
        raise ValueError('Use no arguments for read-only reproduction, or --build once')
    if sys.argv[1:] == ['--build']:
        if (HERE / 'baseline.json').exists():
            raise ValueError('Initial extraction already recorded; run read-only reproduction')
        extracted_at = datetime.now(timezone.utc).isoformat()
        source, quote, proof, originals = rebuild(extracted_at)
        write(HERE / 'baseline.json', {'actual_extracted_at': extracted_at, 'original_files': originals,
            'clock_note': 'Real first extraction clock. Reproduction preserves it; not a new capture or database first-save.'})
        write(HERE / 'source-bundle.json', {'schema_version': 1, 'companies': [], 'sources': [source], 'theses': []})
        write(HERE / 'quote-candidate.json', quote)
        write(HERE / 'stock-field-extraction.json', proof)
        (HERE / 'normalized-stock.json').write_bytes(source['content'].encode('utf-8'))
        report = verify(); write(HERE / 'verification.json', report)
    else:
        report = verify()
    print(json_text(report))


if __name__ == '__main__':
    main()
