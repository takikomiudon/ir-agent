"""Recheck only the two fixed native-binding boundaries; preserve the v1 probe."""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import importlib.util
import io
import json
import tempfile

OLD = Path(__file__).with_name('independent-probe.py')
SPEC = importlib.util.spec_from_file_location('frozen_v1_fixture_helpers', OLD)
helpers = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helpers)
verifier = helpers.verifier


def audit(f):
    before = f.frozen()
    with patch('socket.create_connection', side_effect=AssertionError('Network forbidden')), \
         patch('sqlite3.connect', side_effect=AssertionError('DB forbidden')), \
         patch('subprocess.run', side_effect=AssertionError('Extractor forbidden')):
        try:
            result = verifier.verify_public_capture_binding(f.path, repository_root=f.root)
            assert helpers.SECRET not in json.dumps(result)
            assert all(result[k] == 'not_performed' for k in verifier._NOT_PERFORMED)
            value = {'status': result['status'], 'all_declared_bindings_agree': result['all_declared_bindings_agree'],
                     'artifact_status': result['declared_artifact_bytes']['status'],
                     'binding_checks': {x['name']: x['status'] for x in result['transport_source_binding']['checks']},
                     'profile_status': result['profile_declaration']['status'],
                     'implementation_identity_verified': result['profile_declaration']['implementation_identity_verified'],
                     'reason_codes': result['reason_codes']}
        except ValueError as error:
            assert helpers.SECRET not in str(error)
            value = {'exception': 'ValueError', 'message': str(error)}
    assert f.frozen() == before
    value['files_unchanged_by_audit'] = True
    return value


def run():
    with tempfile.TemporaryDirectory(prefix='ir_native_capture_review_v2_', dir='/tmp') as temporary:
        f = helpers.Fixture(Path(temporary))
        baseline = audit(f)
        assert baseline['status'] == 'matched'
        (f.case / 'text.txt').write_bytes(b'\xff')
        tampered = audit(f)
        assert tampered['status'] == tampered['artifact_status'] == 'mismatch'
        assert tampered['all_declared_bindings_agree'] is False
        assert tampered['binding_checks']['extraction_record_text_bytes'] == 'unknown'
        assert tampered['binding_checks']['extraction_source_content_bytes'] == 'unknown'
        assert tampered['binding_checks']['record_source_content_bytes'] == 'matched'
        assert 'extracted_text_sha_mismatch' in tampered['reason_codes']
        before_cli = f.frozen()
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = verifier.main([str(f.path), '--repository-root', str(f.root), '--capture-binding'])
        assert code == 1 and json.loads(stdout.getvalue())['status'] == 'mismatch'
        assert helpers.SECRET not in stdout.getvalue() + stderr.getvalue()
        assert f.frozen() == before_cli
        cli = {'exit_code': code, 'report_status': 'mismatch', 'secret_omitted': True, 'files_unchanged': True}
        f.record['artifacts']['extracted_text'] = f.artifact('text.txt', b'\xff')
        f.save()
        pinned_control = audit(f)
        assert pinned_control['exception'] == 'ValueError'
        assert pinned_control['message'] == 'Native saved extraction must be valid UTF-8'

        f.reset()
        f.record['extraction']['implementation'] = []
        f.record['extraction']['profile']['name'] = 'future_profile'
        f.save()
        name_case = audit(f)
        assert name_case['exception'] == 'ValueError'
        f.reset()
        f.record['extraction']['profile']['version'] = 2
        f.record['extraction']['implementation'] = {'name': '', 'version': 3, 'sha256': 'not-SHA'}
        f.save()
        version_case = audit(f)
        assert version_case['exception'] == 'ValueError'

        valid_unknown = []
        for profile in [{'name': 'future_profile', 'version': 1}, {'name': 'plain_utf8_preserve', 'version': 2}]:
            f.reset()
            f.record['extraction']['profile'] = deepcopy(profile)
            f.record['extraction']['parameters'] = ['not inferred', {'synthetic': True}]
            f.save()
            result = audit(f)
            assert result['status'] == result['profile_status'] == 'unknown'
            assert result['all_declared_bindings_agree'] is None
            assert result['implementation_identity_verified'] is False
            valid_unknown.append({'profile': profile, 'result': result})

    return {'status': 'both_v1_findings_fixed_with_preserved_controls',
            'baseline': baseline,
            'NCB-01': {'tampered_nonUTF8': tampered, 'CLI': cli, 'pinned_nonUTF8_rejection_control': pinned_control},
            'NCB-02': {'unknown_name_bad_implementation': name_case, 'unknown_version_bad_implementation': version_case,
                       'valid_common_implementation_unsupported_profiles_remain_unknown': valid_unknown},
            'execution': {'synthetic_temporary_fixture_roots': 1, 'GETs': 0, 'Store_or_DB_constructors': 0,
                          'actual_DB_accesses': 0, 'production_or_test_edits': 0, 'full_suite_runs': 0},
            'limits': ['Reuses only the frozen v1 synthetic fixture helper; v1 assertions and producer tests were not executed.',
                       'Only the two original findings and their controls were rechecked; no broad new bug hunt.']}


if __name__ == '__main__':
    result = run()
    Path('/tmp/ir_native_capture_independent_probe_v2_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'tampered_output': result['NCB-01']['tampered_nonUTF8']['status'],
                      'CLI_exit': result['NCB-01']['CLI']['exit_code'], 'malformed_implementations': 'both ValueError',
                      'valid_unknown_profiles': len(result['NCB-02']['valid_common_implementation_unsupported_profiles_remain_unknown'])}))
