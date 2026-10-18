"""Bounded independent arithmetic and saved-byte verification recheck.

Only fixture inputs and disposable files are used. Toyota numbers reproduce
the author's historical example; this is not issuer/source/full-cycle approval.
No production file, actual DB, network, financial policy or forecast is changed.
"""
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from fractions import Fraction
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

REPO = Path('/workspace/ir-agent')
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'tests')]
from ir_agent.cli import run
from ir_agent.cyclical_margin import calculate_cyclical_margin
from ir_agent.store import Store
from test_cyclical_margin import TOYOTA_ROWS, synthetic_request, toyota_request

spec = importlib.util.spec_from_file_location('independent_case_verifier', REPO / 'scripts/verify_case_source_bundle.py')
verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)


def digest(raw):
    return sha256(raw).hexdigest()


def calculate(request):
    before = deepcopy(request)
    result = calculate_cyclical_margin(request)
    assert request == before and result['request'] == request
    assert result['status'] == 'intermediate_only' and result['adoption'] == 'unresolved'
    assert set(result['verification'].values()) == {'unverified'}
    return result


def arithmetic(directory):
    toyota = toyota_request(); result = calculate(toyota)
    # Independent exact rational ratios from the twelve original money rows.
    exact_mean = sum((Fraction(income) / Fraction(revenue) for _, revenue, income in TOYOTA_ROWS), Fraction()) / len(TOYOTA_ROWS)
    exact_income = exact_mean * Fraction(toyota['application_revenue']['revenue'])
    mean = Decimal(result['arithmetic']['mean_operating_margin_ratio'])
    income = Decimal(result['arithmetic']['applied_operating_income'])
    with localcontext() as high:
        high.prec = 200
        expected_mean = Decimal(exact_mean.numerator) / Decimal(exact_mean.denominator)
        expected_income = Decimal(exact_income.numerator) / Decimal(exact_income.denominator)
        precision = result['calculation']['working_precision_digits']
        # An arithmetic error budget in working-precision ulps, not a monetary
        # or financial acceptance threshold. Ratios need repeating division.
        mean_bound = Decimal(10) ** (mean.adjusted() - precision + 1) * (2 * len(TOYOTA_ROWS) + 5)
        income_bound = Decimal(10) ** (income.adjusted() - precision + 1) * (2 * len(TOYOTA_ROWS) + 5)
        assert abs(mean - expected_mean) <= mean_bound
        assert abs(income - expected_income) <= income_bound
        mean_error, income_error = str(abs(mean - expected_mean)), str(abs(income - expected_income))
    assert result['arithmetic']['period_count'] == 12
    with localcontext() as hostile:
        hostile.prec = 3; hostile.rounding = ROUND_DOWN
        hostile.traps[Inexact] = True; hostile.traps[Rounded] = True
        assert calculate(toyota) == result

    request = synthetic_request()
    request['annual_observations'][0].update(revenue='100', operating_income='-10')
    request['annual_observations'][1].update(revenue='300', operating_income='90')
    request['application_revenue']['revenue'] = '200'
    signed = calculate(request)
    unweighted = (Fraction(-10, 100) + Fraction(90, 300)) / 2
    weighted = Fraction(-10 + 90, 100 + 300)
    assert Fraction(signed['arithmetic']['mean_operating_margin_ratio']) == unweighted == Fraction(1, 10)
    assert Fraction(signed['arithmetic']['applied_operating_income']) == unweighted * 200 == 20
    assert weighted == Fraction(1, 5) and weighted * 200 == 40
    negative_request = deepcopy(request); negative_request['annual_observations'][1]['operating_income'] = '-90'
    negative = calculate(negative_request)
    assert Fraction(negative['arithmetic']['mean_operating_margin_ratio']) == Fraction(-1, 5)
    assert Fraction(negative['arithmetic']['applied_operating_income']) == -40
    variants = []
    value = deepcopy(request); value['annual_observations'][0]['operating_income'] = None; variants.append(('missing_income', value))
    value = deepcopy(request); value['application_revenue']['revenue'] = None; variants.append(('missing_application_sales', value))
    value = deepcopy(request); value['annual_observations'][1]['basis']['amount_unit'] = 'billions'; variants.append(('mixed_units', value))
    value = deepcopy(request); value['annual_observations'][1]['period']['kind'] = 'quarter'; variants.append(('quarter', value))
    value = deepcopy(request); value['annual_observations'][1]['period']['start'] = '2023-12-31'; variants.append(('overlap', value))
    value = deepcopy(request); value.pop('method'); variants.append(('unspecified_method', value))
    for name, value in variants:
        before = deepcopy(value)
        try:
            calculate_cyclical_margin(value)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid case was silently filled or accepted: ' + name)
        assert value == before
    input_file = directory / 'cycle-request.json'; input_file.write_text(json.dumps(request))
    store = Store(':memory:')
    try:
        before = list(store.connection.iterdump()), store.connection.total_changes
        cli_result = run(Namespace(command='cycle-margin', file=str(input_file)), store)
        assert cli_result == signed
        assert before == (list(store.connection.iterdump()), store.connection.total_changes)
    finally:
        store.close()
    return {'toyota_rows': len(TOYOTA_ROWS), 'toyota_mean': str(mean), 'toyota_applied_income': str(income),
            'independent_fraction_mean_error': mean_error, 'independent_fraction_income_error': income_error,
            'working_precision_digits': precision, 'hostile_ambient_decimal_context_identical': True,
            'synthetic_equal_mean': signed['arithmetic']['mean_operating_margin_ratio'],
            'synthetic_applied_income': signed['arithmetic']['applied_operating_income'],
            'sales_weighted_comparison_mean': '0.2', 'sales_weighted_comparison_income': '40',
            'negative_mean_retained': negative['arithmetic']['mean_operating_margin_ratio'],
            'negative_applied_income_retained': negative['arithmetic']['applied_operating_income'],
            'invalid_cases_rejected_without_input_mutation': [name for name, _ in variants],
            'cli_matches_pure_and_does_not_write_db': True, 'all_verification_unverified': True,
            'table_prose_discrepancy': 'Compared original raw money ratios only; no assertion that discrepant rounded table/prose figures are corrected or equal.'}


def inventory(root):
    return {str(path.relative_to(root)): ('symlink', str(path.readlink())) if path.is_symlink() else ('file', path.read_bytes())
            for path in root.rglob('*') if path.is_file() or path.is_symlink()}


def verify_files(directory):
    root = directory / 'repository'; case = root / 'cases' / 'one'; case.mkdir(parents=True)
    content = 'BODY-MUST-NOT-APPEAR\r\n架空の抽出本文\n'
    raw = content.encode('utf-8')
    raw_path, text_path, transport_path = (case / name for name in ('raw.bin', 'text.txt', 'transport.json'))
    raw_path.write_bytes(raw); text_path.write_bytes(raw)
    transport = {'sha256': digest(raw), 'byte_count': len(raw), 'text': content,
                 'response_headers': {'Authorization': 'HEADER-MUST-NOT-APPEAR'}}
    transport_bytes = json.dumps(transport, ensure_ascii=False).encode('utf-8'); transport_path.write_bytes(transport_bytes)
    source = {'id': 'fictional-case-source', 'company_id': 'fictional-company', 'title': 'Fictional byte fixture',
        'url': 'https://user:URL-MUST-NOT-APPEAR@example.invalid/', 'source_type': 'public_disclosure',
        'published_at': None, 'retrieved_at': '2026-10-15T09:00:00+09:00', 'content': content,
        'metadata': {'provider': 'finite_initial_issuer_research', 'saved_case_directory': 'cases/one',
            'original_raw_file': 'raw.bin', 'original_raw_sha256': digest(raw), 'original_raw_byte_count': len(raw),
            'original_transport_snapshot': 'transport.json', 'original_transport_snapshot_sha256': digest(transport_bytes),
            'extraction': {'kind': 'plain_text', 'saved_file': 'text.txt', 'sha256': digest(raw)}}}
    bundle = case / 'bundle.json'
    def save(value):
        bundle.write_bytes(json.dumps({'schema_version': 1, 'sources': value}, ensure_ascii=False).encode('utf-8'))
    def audit():
        before = inventory(root)
        result = verifier.verify_case_source_bundle(bundle, repository_root=root)
        assert inventory(root) == before
        output = json.dumps(result, ensure_ascii=False)
        for secret in ('BODY-MUST-NOT-APPEAR', 'HEADER-MUST-NOT-APPEAR', 'URL-MUST-NOT-APPEAR', '架空の抽出本文'):
            assert secret not in output
        return result
    save([source]); baseline = audit()
    assert baseline['status'] == 'matched' and baseline['all_declared_bytes_match'] is True
    assert baseline['sources'][0]['source_content_byte_count'] == len(raw)
    assert baseline['sources'][0]['semantic_financial_verification'] == 'not_performed'
    assert baseline['sources'][0]['source_id_verification'] == 'not_performed'
    stdout, stderr = io.StringIO(), io.StringIO(); before = inventory(root)
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = verifier.main([str(bundle), '--repository-root', str(root)])
    assert code == 0 and json.loads(stdout.getvalue()) == baseline and not stderr.getvalue()
    assert inventory(root) == before
    assert all(secret not in stdout.getvalue() for secret in ('BODY-MUST-NOT-APPEAR', 'HEADER-MUST-NOT-APPEAR', 'URL-MUST-NOT-APPEAR'))
    raw_path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:]); changed = audit()
    assert changed['status'] == 'mismatch' and 'raw_sha_mismatch' in changed['sources'][0]['reason_codes']
    raw_path.write_bytes(raw)
    wrong_count = deepcopy(source); wrong_count['metadata']['original_raw_byte_count'] -= 1
    save([wrong_count]); count = audit()
    assert count['status'] == 'mismatch' and 'raw_byte_count_mismatch' in count['sources'][0]['reason_codes']
    translated = raw.replace(b'\r\n', b'\n'); text_path.write_bytes(translated)
    wrong_text = deepcopy(source); wrong_text['metadata']['extraction']['sha256'] = digest(translated)
    save([wrong_text]); text = audit()
    assert text['status'] == 'mismatch' and 'extraction_source_content_bytes_mismatch' in text['sources'][0]['reason_codes']
    text_path.write_bytes(raw)
    bad_snapshot = {**transport, 'text': 'Different caller-controlled transport text'}
    bad_snapshot_bytes = json.dumps(bad_snapshot).encode('utf-8'); transport_path.write_bytes(bad_snapshot_bytes)
    wrong_transport = deepcopy(source); wrong_transport['metadata']['original_transport_snapshot_sha256'] = digest(bad_snapshot_bytes)
    save([wrong_transport]); snapshot_result = audit()
    assert snapshot_result['status'] == 'mismatch' and 'transport_source_content_bytes_mismatch' in snapshot_result['sources'][0]['reason_codes']
    transport_path.write_bytes(transport_bytes)
    unknown_source = deepcopy(source); unknown_source['metadata']['provider'] = 'unknown-provider'
    save([unknown_source]); unknown = audit()
    assert unknown['status'] == 'unknown' and unknown['all_declared_bytes_match'] is None
    save([]); empty = audit()
    assert empty['status'] == 'empty' and empty['all_declared_bytes_match'] is None
    outside = root / 'outside-case.bin'; outside.write_bytes(b'OUTSIDE-CONTENT-MUST-NOT-BE-READ')
    (case / 'escape').symlink_to(outside)
    original_read = Path.read_bytes
    def guarded_read(path):
        if path.resolve() == outside.resolve(): raise AssertionError('Verifier read outside declared case root')
        return original_read(path)
    for reference in ('../outside-case.bin', 'escape'):
        invalid = deepcopy(source); invalid['metadata']['original_raw_file'] = reference; save([invalid])
        before = inventory(root)
        try:
            with patch.object(Path, 'read_bytes', guarded_read):
                verifier.verify_case_source_bundle(bundle, repository_root=root)
        except ValueError:
            pass
        else:
            raise AssertionError('Path boundary was not rejected')
        assert inventory(root) == before
    return {'crlf_raw_text_transport_matched': True, 'byte_count': len(raw), 'one_byte_change_detected': True,
            'wrong_declared_byte_count_detected': True, 'newline_change_detected_even_with_updated_extraction_hash': True,
            'transport_content_change_detected_even_with_updated_snapshot_hash': True,
            'unknown_provider': unknown['status'], 'empty_bundle': empty['status'],
            'parent_and_symlink_escape_rejected_before_target_read': True, 'all_files_unchanged_during_each_audit': True,
            'api_and_cli_omit_body_headers_and_url_credentials': True, 'semantic_financial_and_identity_verification': 'not_performed'}


def main():
    with tempfile.TemporaryDirectory(prefix='ir-cycle-margin-recheck-') as folder:
        directory = Path(folder)
        report = {'scope': 'two bounded offline features only', 'arithmetic': arithmetic(directory), 'byte_verifier': verify_files(directory),
            'limits': ['Historical author Table 2 arithmetic only; no present issuer facts, full-cycle coverage or forecast adopted.',
                       'Matching files and caller-controlled expected hashes is not authenticity, semantic extraction or financial validation.',
                       'Finite fixtures; no broad fuzz/performance/restore investigation, production edit, actual DB or network access.']}
    Path('/tmp/ir_cyclical_margin_recheck.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
