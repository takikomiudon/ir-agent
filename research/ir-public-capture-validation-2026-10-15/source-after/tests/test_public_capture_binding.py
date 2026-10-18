"""Native capture declaration checks only; no extraction, GET, DB or adoption."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.models import json_text

spec = importlib.util.spec_from_file_location('native_case_verifier', Path(__file__).resolve().parents[1] / 'scripts/verify_case_source_bundle.py')
verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)


def digest(raw): return sha256(raw).hexdigest()


class PublicCaptureBindingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.root = Path(directory.name); self.case = self.root / 'cases' / 'native'; self.case.mkdir(parents=True)
        self.content = 'Synthetic first\r\nSynthetic second\n\f'
        self.raw = b'<html>Synthetic unrelated input</html>\r\n'
        self.output = self.content.encode()
        self.source = {'id': 'synthetic:source-not-derived', 'company_id': 'jp:TEST', 'title': 'Synthetic evidence',
            'source_type': 'public_disclosure', 'url': 'https://issuer.invalid/report?token=SECRET-DO-NOT-PRINT',
            'retrieved_at': '2026-10-15T09:00:02+09:00', 'published_at': None,
            'content': self.content, 'metadata': {'synthetic': True, 'provider': 'unknown-topic'}}
        self.record = {'format': 'ir-public-response-capture', 'version': 1,
            'request': {'method': 'GET', 'url': self.source['url'], 'user_agent_configured': 'Synthetic-UA/1',
                'user_agent_prepared': 'Synthetic-UA/1', 'started_at': '2026-10-15T00:00:00Z'},
            'response': {'url': self.source['url'], 'status_code': 200, 'complete_body': True, 'error': None,
                'headers_received_at': '2026-10-15T00:00:01+00:00', 'body_completed_at': '2026-10-15T00:00:02Z',
                'body_representation': 'response_entity_after_content_decoding', 'content_length_header': '999'},
            'artifacts': {}, 'extraction': {'profile': {'name': 'html_visible_nodes_lf', 'version': 1},
                'implementation': {'name': 'Synthetic extractor', 'version': 'not-run', 'sha256': None},
                'parameters': {'decoder': 'utf-8-sig', 'ignored_elements': ['script', 'style'],
                    'convert_charrefs': True, 'node_whitespace': 'collapse', 'joiner': 'LF', 'terminal_LF': True},
                'text': self.content}}
        self.binding = {'format': 'ir-public-source-binding', 'version': 1, 'case_root': 'cases/native',
            'source': {'artifact': {}, 'pointer': '/sources/0', 'snapshot_sha256': '',
                       'snapshot_hash_profile': 'ir_agent.models.json_text/UTF-8'},
            'transport': {'artifact': {}, 'record_pointer': '/records/0'}}
        self.source_doc = None; self.transport_doc = None
        self.path = self.case / 'binding.json'; self.save()

    def artifact(self, path, raw):
        (self.case / path).write_bytes(raw)
        return {'path': path, 'sha256': digest(raw), 'byte_count': len(raw)}

    def save(self):
        self.record['artifacts'] = {'raw': self.artifact('raw.bin', self.raw),
                                    'extracted_text': self.artifact('output.txt', self.output)}
        source_doc = {'sources': [self.source]} if self.source_doc is None else self.source_doc
        transport_doc = {'records': [self.record]} if self.transport_doc is None else self.transport_doc
        self.binding['source']['artifact'] = self.artifact('source.json', json.dumps(source_doc).encode())
        self.binding['source']['snapshot_sha256'] = digest(json_text(self.source).encode())
        self.binding['transport']['artifact'] = self.artifact('transport.json', json.dumps(transport_doc).encode())
        self.write_binding()

    def write_binding(self): self.path.write_bytes(json.dumps(self.binding).encode())
    def audit(self): return verifier.verify_public_capture_binding(self.path, repository_root=self.root)
    def frozen(self): return {str(p.relative_to(self.root)): digest(p.read_bytes()) for p in self.root.rglob('*') if p.is_file()}

    def test_crlf_instants_default_free_snapshot_and_no_implicit_replay(self):
        before = self.frozen()
        with patch('socket.create_connection', side_effect=AssertionError('GET forbidden')), \
             patch('sqlite3.connect', side_effect=AssertionError('DB forbidden')), \
             patch('subprocess.run', side_effect=AssertionError('Tool replay forbidden')):
            result = self.audit()
        self.assertEqual(result['status'], 'matched')
        self.assertTrue(result['all_declared_bindings_agree'])
        self.assertEqual(result['source_snapshot_sha256'], digest(json_text(self.source).encode()))
        self.assertNotIn('requires_research', self.source)
        self.assertEqual(result['profile_declaration']['status'], 'recognized')
        self.assertFalse(result['profile_declaration']['implementation_identity_verified'])
        for key in verifier._NOT_PERFORMED: self.assertEqual(result[key], 'not_performed')
        self.assertNotIn('SECRET-DO-NOT-PRINT', json.dumps(result))
        self.assertNotIn(self.content, json.dumps(result))
        self.assertEqual(self.frozen(), before)
        # A declared Content-Length of999 is not the decoded entity byte count.
        self.assertNotEqual(self.record['response']['content_length_header'], str(len(self.raw)))

    def test_root_pointer_and_escaped_empty_and_once_decoded_object_keys(self):
        self.source_doc = self.source; self.binding['source']['pointer'] = ''
        self.transport_doc = {'a/b': {'~1': {'': self.record}}}
        self.binding['transport']['record_pointer'] = '/a~1b/~01/'
        self.save()
        self.assertEqual(self.audit()['status'], 'matched')
        self.transport_doc = self.record; self.binding['transport']['record_pointer'] = ''
        self.save(); self.assertEqual(self.audit()['status'], 'matched')

    def test_missing_pointer_is_unknown_and_invalid_syntax_or_array_index_is_validation_error(self):
        self.binding['transport']['record_pointer'] = '/records/99'; self.write_binding()
        self.assertEqual(self.audit()['status'], 'unknown')
        for pointer in ('records/0', '/records/~2', '/records/01', '/records/-', None, True, []):
            self.binding['transport']['record_pointer'] = pointer; self.write_binding()
            with self.subTest(pointer=pointer), self.assertRaises(ValueError): self.audit()
        self.binding['transport']['record_pointer'] = '/records/9999999999999999999999999999999999999'; self.write_binding()
        self.assertEqual(self.audit()['status'], 'unknown')

    def test_unknown_binding_format_or_version_never_reads_references_or_falls_back(self):
        for field, value in [('version', 2), ('format', 'unknown-native-format')]:
            self.binding[field] = value
            self.binding['source']['provider'] = 'finite_initial_issuer_research'
            self.write_binding()
            with patch.object(verifier, '_artifact', side_effect=AssertionError('No artifact reads')):
                result = self.audit()
            self.assertEqual(result['status'], 'unknown')
            self.assertIsNone(result['all_declared_bindings_agree'])

    def test_unknown_native_record_version_and_wire_remain_unknown(self):
        self.record['version'] = 2; self.save()
        self.assertEqual(self.audit()['status'], 'unknown')
        self.record['version'] = 1; self.record['response']['body_representation'] = 'wire_capture'; self.save()
        result = self.audit()
        self.assertEqual(result['status'], 'unknown')
        self.assertIn('response_entity_scope_unspecified', result['reason_codes'])

    def test_known_schema_types_unknown_fields_and_boolean_numbers_rejected(self):
        original = deepcopy(self.record)
        for section, key, value in [('response', 'status_code', True), ('response', 'complete_body', 1),
                                    ('request', 'method', []), ('response', 'body_representation', {}),
                                    ('response', 'content_length_header', False)]:
            self.record = deepcopy(original); self.record[section][key] = value; self.save()
            with self.subTest(section=section, key=key), self.assertRaises(ValueError): self.audit()
        self.record = deepcopy(original); self.record['caller_verified'] = True; self.save()
        with self.assertRaises(ValueError): self.audit()
        for value in (True, 1.0, None, [], {}):
            self.binding['version'] = value; self.write_binding()
            with self.subTest(version=value), self.assertRaises(ValueError): self.audit()

    def test_duplicate_nonfinite_JSON_and_invalid_UTF8_fail_without_echo(self):
        original = self.path.read_bytes()
        for raw in (b'{"format":"SECRET-DO-NOT-PRINT","format":"x"}', b'{"x":NaN}', b'{"x":1e999}', b'\xff'):
            self.path.write_bytes(raw)
            with self.subTest(raw=raw), self.assertRaises(ValueError) as caught: self.audit()
            self.assertNotIn('SECRET-DO-NOT-PRINT', str(caught.exception))
        self.path.write_bytes(original)
        for raw in (b'{"records":[],"records":[]}', b'{"records":[],"unselected":Infinity}', b'{"unselected":1e999}'):
            self.binding['transport']['artifact'] = self.artifact('transport.json', raw); self.write_binding()
            with self.subTest(capture=raw), self.assertRaises(ValueError): self.audit()

    def test_known_hash_count_and_content_mismatches_do_not_get_accepted(self):
        self.binding['source']['snapshot_sha256'] = '0'*64; self.write_binding()
        self.assertEqual(self.audit()['status'], 'mismatch')
        self.save(); self.binding['transport']['artifact']['sha256'] = '0'*64; self.write_binding()
        self.assertEqual(self.audit()['status'], 'mismatch')
        self.save(); self.output = self.content.replace('\r\n', '\n').encode(); self.save()
        self.assertEqual(self.audit()['status'], 'mismatch')
        self.assertIn('extraction_source_content_bytes_mismatch', self.audit()['reason_codes'])
        self.output = self.content.encode(); self.record['extraction']['text'] = 'Changed'; self.save()
        self.assertEqual(self.audit()['status'], 'mismatch')

    def test_empty_raw_byte_count_is_real_zero_missing_file_is_unknown(self):
        self.raw = b''; self.save()
        result = self.audit()
        raw_check = next(x for x in result['declared_artifact_bytes']['checks'] if x['name'] == 'raw')
        self.assertEqual(raw_check['status'], 'matched'); self.assertEqual(raw_check['actual_byte_count'], 0)
        self.assertEqual(result['extractor_reproduction'], 'not_performed')
        (self.case / 'raw.bin').unlink()
        self.assertEqual(self.audit()['status'], 'unknown')
        self.save(); self.binding['source']['artifact']['byte_count'] = True; self.write_binding()
        with self.assertRaises(ValueError): self.audit()

    def test_tampered_transport_file_is_not_parsed_or_used_to_bind(self):
        (self.case / 'transport.json').write_bytes(b'INVALID SECRET-DO-NOT-PRINT')
        result = self.audit()
        self.assertEqual(result['status'], 'mismatch')
        self.assertEqual(result['transport_source_binding']['status'], 'unknown')
        self.assertNotIn('SECRET-DO-NOT-PRINT', json.dumps(result))

    def test_time_order_and_retrieval_inequality_are_mismatch_bad_time_is_safe_error(self):
        self.record['response']['body_completed_at'] = '2026-10-15T00:00:01.999999Z'; self.save()
        self.assertEqual(self.audit()['status'], 'mismatch')
        self.record['response']['body_completed_at'] = '2026-10-14T23:59:59Z'; self.save()
        self.assertIn('transport_time_order_mismatch', self.audit()['reason_codes'])
        for stamp in ('2026-10-15T00:00:01', 'SECRET-DO-NOT-PRINT', [], None):
            self.record['request']['started_at'] = stamp; self.save()
            with self.subTest(stamp=stamp), self.assertRaises(ValueError) as caught: self.audit()
            self.assertNotIn('SECRET-DO-NOT-PRINT', str(caught.exception))
        self.record['request']['started_at'] = '2026-10-15T00:00:00Z'
        self.source['retrieved_at'] = 'SECRET-DO-NOT-PRINT'; self.save()
        with self.assertRaises(ValueError) as caught: self.audit()
        self.assertNotIn('SECRET-DO-NOT-PRINT', str(caught.exception))

    def test_failed_partial_and_redirect_records_never_bind_successful_source(self):
        for status in (302, 403, 503):
            self.record['response']['status_code'] = status; self.save()
            self.assertEqual(self.audit()['status'], 'mismatch')
            self.assertIn('successful_complete_response_mismatch', self.audit()['reason_codes'])
        self.record['response'].update(status_code=None, complete_body=False,
            error='SECRET-DO-NOT-PRINT', headers_received_at=None, body_completed_at=None)
        self.save()
        result = self.audit(); self.assertEqual(result['status'], 'mismatch')
        self.assertNotIn('SECRET-DO-NOT-PRINT', json.dumps(result))
        # Explicitly absent output is allowed only for an unsuccessful record.
        self.record['extraction'] = None; self.record['artifacts']['extracted_text'] = None
        self.binding['transport']['artifact'] = self.artifact('transport.json', json.dumps({'records':[self.record]}).encode()); self.write_binding()
        self.assertEqual(self.audit()['status'], 'mismatch')

    def test_success_without_completeness_evidence_or_output_is_malformed(self):
        self.record['response']['body_completed_at'] = None; self.save()
        with self.assertRaises(ValueError): self.audit()
        self.record['response']['body_completed_at'] = '2026-10-15T00:00:02Z'
        self.record['extraction'] = None; self.save()
        with self.assertRaises(ValueError): self.audit()

    def test_known_profiles_declared_without_execution_and_unknown_profiles_not_inferred(self):
        profiles = [('plain_utf8_preserve', {'decoder': 'utf-8', 'BOM':'preserve','line_endings':'preserve'}),
                    ('pdftotext_layout', {'arguments':['-layout'],'output_encoding':'UTF-8','form_feeds':'preserve','page_numbering':'one_based'})]
        for name, params in profiles:
            self.record['extraction']['profile'] = {'name': name, 'version': 1}
            self.record['extraction']['parameters'] = params; self.save()
            result = self.audit(); self.assertEqual(result['status'], 'matched')
            self.assertEqual(result['extractor_reproduction'], 'not_performed')
        self.record['extraction']['profile']['version'] = 2; self.save()
        self.assertEqual(self.audit()['status'], 'unknown')
        self.record['extraction']['profile'] = {'name':'unrecognized','version':1}; self.save()
        self.assertEqual(self.audit()['status'], 'unknown')
        self.record['extraction']['profile'] = {'name':'pdftotext_layout','version':1}
        self.record['extraction']['parameters']['arguments'] = ['-layout','-x']; self.save()
        with self.assertRaises(ValueError): self.audit()

    def test_UTF8_output_required_and_zero_lone_surrogate_not_silently_changed(self):
        self.output = b'\xff'; self.save()
        with self.assertRaises(ValueError): self.audit()
        self.output = self.content.encode(); self.record['extraction']['text'] = '\ud800'; self.save()
        with self.assertRaises(ValueError): self.audit()

    def test_url_and_UA_mismatch_report_only_labels_and_no_secret_data(self):
        self.record['request']['user_agent_prepared'] = 'SECRET-DO-NOT-PRINT'
        self.record['response']['url'] = 'https://issuer.invalid/SECRET-DO-NOT-PRINT'; self.save()
        result = self.audit(); self.assertEqual(result['status'], 'mismatch')
        self.assertNotIn('SECRET-DO-NOT-PRINT', json.dumps(result))
        self.record['request']['url'] = 'SECRET-DO-NOT-PRINT'; self.save()
        with self.assertRaises(ValueError) as caught: self.audit()
        self.assertNotIn('SECRET-DO-NOT-PRINT', str(caught.exception))
        self.record['request']['url'] = self.source['url']
        self.record['response']['headers'] = {'Authorization':'SECRET-DO-NOT-PRINT'}; self.save()
        with self.assertRaises(ValueError) as caught: self.audit()
        self.assertNotIn('SECRET-DO-NOT-PRINT', str(caught.exception))

    def test_all_declared_artifact_escapes_rejected_before_read(self):
        outside = self.root / 'outside-secret.txt'; outside.write_bytes(b'SECRET-DO-NOT-PRINT')
        (self.case / 'escape').symlink_to(outside)
        original = deepcopy(self.binding)
        for path in ('../outside-secret.txt', str(outside), 'escape', 'bad\x00path'):
            self.binding = deepcopy(original); self.binding['source']['artifact']['path'] = path; self.write_binding()
            original_read = Path.read_bytes
            def guarded(p):
                if p.resolve() == outside: raise AssertionError('Escape target read')
                return original_read(p)
            with self.subTest(path=path), patch.object(Path, 'read_bytes', guarded), self.assertRaises(ValueError): self.audit()
        self.binding = deepcopy(original); self.binding['case_root'] = '..'; self.write_binding()
        with self.assertRaises(ValueError): self.audit()

    def test_source_metadata_cannot_opt_out_or_upgrade_but_other_source_types_remain_unknown(self):
        self.source['metadata']['verified'] = True; self.save()
        result = self.audit(); self.assertEqual(result['semantic_financial_verification'], 'not_performed')
        self.source['source_type'] = 'market_data'; self.save()
        self.assertEqual(self.audit()['status'], 'unknown')

    def test_CLI_opt_in_exit_status_and_validation_error_never_dump_secret(self):
        def run():
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                try: code = verifier.main([str(self.path),'--repository-root',str(self.root),'--capture-binding'])
                except SystemExit as error: code = error.code
            self.assertNotIn('SECRET-DO-NOT-PRINT', stdout.getvalue()+stderr.getvalue())
            return code, stdout.getvalue(), stderr.getvalue()
        self.assertEqual(run()[0], 0)
        self.record['response']['status_code'] = 403; self.save(); self.assertEqual(run()[0], 1)
        self.record['request']['started_at'] = 'SECRET-DO-NOT-PRINT'; self.save(); self.assertEqual(run()[0], 2)
        self.binding['version'] = 99; self.write_binding(); self.assertEqual(run()[0], 0)


if __name__ == '__main__': unittest.main()
