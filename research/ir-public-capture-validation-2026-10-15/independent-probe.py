"""Finite synthetic native-binding probes; no producer tests, network or DB."""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import importlib.util
import io
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.models import json_text

SPEC = importlib.util.spec_from_file_location('bounded_native_capture_review', ROOT / 'scripts/verify_case_source_bundle.py')
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)
H = lambda raw: sha256(raw).hexdigest()
SECRET = 'INDEPENDENT-SYNTHETIC-SECRET'


class Fixture:
    def __init__(self, directory):
        self.root = directory
        self.case = directory / 'research/synthetic-native-capture-fixture'
        self.case.mkdir(parents=True)
        self.example = json.loads((ROOT / 'research/ir-public-capture-validation-2026-10-15/design-v1.json').read_bytes())['synthetic_coherent_example_not_files_created']
        self.path = self.case / 'binding.json'
        self.reset()

    def artifact(self, name, raw):
        path = self.case / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {'path': name, 'sha256': H(raw), 'byte_count': len(raw)}

    def reset(self):
        self.binding = deepcopy(self.example['binding'])
        self.record = deepcopy(self.example['selected_native_transport_record'])
        self.source_doc = deepcopy(self.example['source_bundle_artifact_JSON'])
        self.source = self.source_doc['sources'][0]
        self.source['url'] += '?token=' + SECRET
        self.record['request']['url'] = self.record['response']['url'] = self.source['url']
        raw = self.example['raw_and_output_bytes_UTF8_representation'].encode()
        self.record['artifacts']['raw'] = self.artifact('raw/entity.bin', raw)
        self.record['artifacts']['extracted_text'] = self.artifact('text.txt', raw)
        self.save()

    def save(self):
        self.binding['source']['artifact'] = self.artifact('source-bundle.json', json.dumps(self.source_doc).encode())
        self.binding['source']['snapshot_sha256'] = H(json_text(self.source).encode())
        self.binding['transport']['artifact'] = self.artifact('capture.json', json.dumps({'records': [self.record]}).encode())
        self.path.write_bytes(json.dumps(self.binding).encode())

    def frozen(self):
        return {str(p.relative_to(self.root)): H(p.read_bytes()) for p in self.root.rglob('*') if p.is_file()}

    def audit(self, cli=False):
        before = self.frozen()
        with patch('socket.create_connection', side_effect=AssertionError('Network forbidden')), \
             patch('sqlite3.connect', side_effect=AssertionError('DB forbidden')), \
             patch('subprocess.run', side_effect=AssertionError('Extraction forbidden')):
            if cli:
                stdout, stderr = io.StringIO(), io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    try:
                        code = verifier.main([str(self.path), '--repository-root', str(self.root), '--capture-binding'])
                    except SystemExit as error:
                        code = error.code
                result = {'CLI_exit': code, 'stdout_present': bool(stdout.getvalue()),
                          'error_contains_UTF8_label': 'Native saved extraction must be valid UTF-8' in stderr.getvalue(),
                          'secret_omitted': SECRET not in stdout.getvalue() + stderr.getvalue()}
            else:
                try:
                    value = verifier.verify_public_capture_binding(self.path, repository_root=self.root)
                    result = {'status': value['status'], 'all_declared_bindings_agree': value['all_declared_bindings_agree'],
                              'artifact_status': value['declared_artifact_bytes']['status'],
                              'profile_status': value['profile_declaration']['status'], 'reason_codes': value['reason_codes'],
                              'secret_omitted': SECRET not in json.dumps(value)}
                    assert all(value[k] == 'not_performed' for k in verifier._NOT_PERFORMED)
                except ValueError as error:
                    result = {'exception': 'ValueError', 'message': str(error), 'secret_omitted': SECRET not in str(error)}
        assert self.frozen() == before
        assert result['secret_omitted'] is True
        result['files_unchanged_by_audit'] = True
        return result


def run():
    with tempfile.TemporaryDirectory(prefix='ir_native_capture_review_', dir='/tmp') as temporary:
        f = Fixture(Path(temporary))
        baseline = f.audit()
        assert baseline['status'] == 'matched'

        (f.case / 'text.txt').write_bytes(b'changed UTF8 output')
        utf8_mismatch = f.audit()
        assert utf8_mismatch['status'] == 'mismatch'

        (f.case / 'text.txt').write_bytes(b'\xff')
        non_utf8_mismatch = f.audit()
        assert non_utf8_mismatch['exception'] == 'ValueError'
        assert non_utf8_mismatch['message'] == 'Native saved extraction must be valid UTF-8'
        non_utf8_cli = f.audit(cli=True)
        assert non_utf8_cli['CLI_exit'] == 2

        f.record['artifacts']['extracted_text'] = f.artifact('text.txt', b'\xff')
        f.save()
        pinned_non_utf8_control = f.audit()
        assert pinned_non_utf8_control['exception'] == 'ValueError'

        f.reset()
        f.record['extraction']['implementation'] = []
        f.save()
        recognized_bad_impl_control = f.audit()
        assert recognized_bad_impl_control['exception'] == 'ValueError'
        f.record['extraction']['profile']['name'] = 'future_profile'
        f.save()
        unknown_name_bad_impl = f.audit()
        assert unknown_name_bad_impl['status'] == 'unknown'

        f.reset()
        f.record['extraction']['profile']['version'] = 2
        f.record['extraction']['implementation'] = {'name': '', 'version': 3, 'sha256': 'not-SHA'}
        f.save()
        unknown_version_bad_impl = f.audit()
        assert unknown_version_bad_impl['status'] == 'unknown'

        f.reset()
        f.record['response'].update(status_code=None, complete_body=False, error=SECRET,
                                    headers_received_at=None, body_completed_at=None)
        f.record['extraction'] = None
        f.record['artifacts']['extracted_text'] = None
        f.save()
        valid_failed_capture = f.audit()
        assert valid_failed_capture['status'] == 'mismatch'
        f.record['artifacts']['raw'] = None
        f.save()
        invalid_failed_raw_null = f.audit()
        assert invalid_failed_raw_null['exception'] == 'ValueError'

    return {'status': 'two_contract_discrepancies_reproduced',
            'baseline': baseline,
            'untrusted_output': {'UTF8_tamper': utf8_mismatch, 'non_UTF8_tamper': non_utf8_mismatch,
                                 'non_UTF8_tamper_CLI': non_utf8_cli, 'pinned_non_UTF8_control': pinned_non_utf8_control},
            'implementation_schema': {'known_profile_bad_implementation': recognized_bad_impl_control,
                                       'unknown_name_bad_implementation': unknown_name_bad_impl,
                                       'unknown_version_bad_implementation': unknown_version_bad_impl},
            'failed_capture_contract_controls': {'nonnull_raw_failed_capture': valid_failed_capture,
                                                 'raw_null_failed_capture': invalid_failed_raw_null},
            'execution': {'synthetic_temporary_fixture_roots': 1, 'GETs': 0, 'Store_or_DB_constructors': 0,
                          'real_DB_accesses': 0, 'production_or_test_edits': 0, 'producer_tests_rerun': 0,
                          'full_suite_runs': 0},
            'limits': ['No false matched result was found in these discrepancies.',
                       'Failure raw:null is not in the frozen v1 nullable list, so its rejection is a control, not a reported bug.',
                       'The audit is an internal declaration check, not authenticity, extraction replay, historical occurrence or financial certification.']}


if __name__ == '__main__':
    result = run()
    target = Path('/tmp/ir_native_capture_independent_probe_result.json')
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
