"""Offline saved-case byte checks preserve CRLF and stay inside the case root."""
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

spec = importlib.util.spec_from_file_location('verify_case_source_bundle', Path(__file__).resolve().parents[1] / 'scripts/verify_case_source_bundle.py')
verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)


def digest(raw):
    return sha256(raw).hexdigest()


class CaseSourceVerifierTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.root = Path(directory.name); self.case = self.root / 'cases' / 'one'; self.case.mkdir(parents=True)
        self.content = 'Synthetic line one\r\nSynthetic line two\n'
        self.raw = self.content.encode('utf-8')
        (self.case / 'raw.bin').write_bytes(self.raw)
        (self.case / 'text.txt').write_bytes(self.raw)
        self.snapshot = {'sha256': digest(self.raw), 'byte_count': len(self.raw), 'text': self.content,
            'response_headers': {'Authorization': 'SECRET-DO-NOT-PRINT'}}
        snapshot_raw = json.dumps(self.snapshot).encode('utf-8'); (self.case / 'transport.json').write_bytes(snapshot_raw)
        self.source = {'id': 'case-public:fixture-stable-id', 'company_id': 'jp:TEST', 'title': 'Synthetic evidence',
            'url': 'https://user:SECRET-DO-NOT-PRINT@example.invalid/?token=SECRET-DO-NOT-PRINT',
            'source_type': 'public_disclosure', 'published_at': None, 'retrieved_at': '2026-10-15T09:00:00+09:00',
            'content': self.content, 'metadata': {'provider': 'finite_initial_issuer_research', 'saved_case_directory': 'cases',
                'original_raw_file': 'one/raw.bin', 'original_raw_sha256': digest(self.raw), 'original_raw_byte_count': len(self.raw),
                'original_transport_snapshot': 'one/transport.json', 'original_transport_snapshot_sha256': digest(snapshot_raw),
                'extraction': {'kind': 'plain_text', 'saved_file': 'one/text.txt', 'sha256': digest(self.raw)}}}
        self.bundle = self.case / 'bundle.json'
        self.write_bundle()

    def write_bundle(self, sources=None):
        self.bundle.write_bytes(json.dumps({'schema_version': 1, 'sources': [self.source] if sources is None else sources}).encode('utf-8'))

    def verify(self):
        return verifier.verify_case_source_bundle(self.bundle, repository_root=self.root)

    def test_crlf_bytes_match_and_report_omits_content_headers_credentials(self):
        before = {path: digest(path.read_bytes()) for path in self.case.iterdir()}
        result = self.verify()
        self.assertEqual(result['status'], 'matched'); self.assertIs(result['all_declared_bytes_match'], True)
        self.assertEqual(result['counts'], {'matched': 1, 'mismatch': 0, 'unknown': 0})
        self.assertEqual(result['sources'][0]['source_content_byte_count'], len(self.raw))
        self.assertEqual(result['sources'][0]['source_id_verification'], 'not_performed')
        output = json.dumps(result)
        self.assertNotIn('SECRET-DO-NOT-PRINT', output); self.assertNotIn(self.content, output)
        self.assertEqual({path: digest(path.read_bytes()) for path in self.case.iterdir()}, before)

    def test_newline_translation_is_detected_even_when_extraction_hash_is_updated(self):
        changed = self.raw.replace(b'\r\n', b'\n')
        (self.case / 'text.txt').write_bytes(changed)
        self.source['metadata']['extraction']['sha256'] = digest(changed); self.write_bundle()
        result = self.verify()
        self.assertEqual(result['status'], 'mismatch')
        self.assertIn('extraction_source_content_bytes_mismatch', result['sources'][0]['reason_codes'])

    def test_raw_count_zero_and_hash_mismatch_are_not_missing(self):
        self.source['metadata']['original_raw_byte_count'] = 0
        self.source['metadata']['original_raw_sha256'] = '0'*64; self.write_bundle()
        result = self.verify()
        self.assertIs(result['all_declared_bytes_match'], False)
        self.assertIn('raw_byte_count_mismatch', result['sources'][0]['reason_codes'])
        self.assertIn('raw_sha_mismatch', result['sources'][0]['reason_codes'])

    def test_empty_unknown_provider_missing_metadata_and_missing_file_stay_distinct(self):
        self.write_bundle([]); empty = self.verify()
        self.assertEqual(empty['status'], 'empty'); self.assertEqual(empty['source_count'], 0)
        self.assertIsNone(empty['all_declared_bytes_match'])
        self.source['metadata']['provider'] = 'unknown-provider'; self.write_bundle()
        self.assertEqual(self.verify()['status'], 'unknown')
        self.source['metadata']['provider'] = 'finite_initial_issuer_research'
        self.source['metadata'].pop('original_raw_byte_count'); self.write_bundle()
        self.assertEqual(self.verify()['status'], 'unknown')
        self.source['metadata']['original_raw_byte_count'] = len(self.raw)
        (self.case / 'raw.bin').unlink(); self.write_bundle()
        self.assertIn('raw_file_missing', self.verify()['sources'][0]['reason_codes'])

    def test_absolute_parent_and_symlink_escapes_are_rejected_without_reading_target(self):
        other = self.root / 'outside-case.txt'; other.write_text('PRIVATE TARGET')
        initial = deepcopy(self.source)
        (self.case / 'escape').symlink_to(other)
        for reference in (str(other), '../outside-case.txt', 'one/escape'):
            self.source = deepcopy(initial); self.source['metadata']['original_raw_file'] = reference; self.write_bundle()
            original = Path.read_bytes
            def guarded(path):
                if path.resolve() == other: raise AssertionError('Outside case file was read')
                return original(path)
            with self.subTest(reference=reference), patch.object(Path, 'read_bytes', guarded), self.assertRaises(ValueError):
                self.verify()
        self.source = deepcopy(initial); self.source['metadata']['saved_case_directory'] = str(self.root); self.write_bundle()
        with self.assertRaises(ValueError): self.verify()

    def test_malformed_json_types_hash_and_byte_count_fail_normally(self):
        for field, bad in (('original_raw_sha256', []), ('original_raw_byte_count', True), ('original_raw_file', {})):
            original = deepcopy(self.source)
            self.source['metadata'][field] = bad; self.write_bundle()
            with self.subTest(field=field), self.assertRaises(ValueError): self.verify()
            self.source = original
        for raw in ('{"schema_version": 1, "sources": [], "sources": []}', '{"value": NaN}', '[]'):
            self.bundle.write_text(raw)
            with self.subTest(raw=raw), self.assertRaises(ValueError): self.verify()

    def test_transport_own_hash_and_embedded_content_must_both_match(self):
        self.snapshot['text'] = 'Different extracted text'
        raw = json.dumps(self.snapshot).encode('utf-8'); (self.case / 'transport.json').write_bytes(raw)
        self.source['metadata']['original_transport_snapshot_sha256'] = digest(raw); self.write_bundle()
        result = self.verify()
        self.assertIn('transport_source_content_bytes_mismatch', result['sources'][0]['reason_codes'])
        self.source['metadata']['original_transport_snapshot_sha256'] = '0'*64; self.write_bundle()
        self.assertIn('transport_snapshot_sha_mismatch', self.verify()['sources'][0]['reason_codes'])

    def test_followup_provider_uses_its_explicit_raw_sha256_field(self):
        self.source['metadata']['provider'] = 'finite_issuer_statement_calendar_followup'
        self.snapshot['raw_sha256'] = self.snapshot.pop('sha256')
        raw = json.dumps(self.snapshot).encode('utf-8'); (self.case / 'transport.json').write_bytes(raw)
        self.source['metadata']['original_transport_snapshot_sha256'] = digest(raw); self.write_bundle()
        self.assertEqual(self.verify()['status'], 'matched')

    def test_cli_emits_json_and_reports_mismatch_with_nonzero_exit(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = verifier.main([str(self.bundle), '--repository-root', str(self.root)])
        self.assertEqual(code, 0); self.assertEqual(json.loads(stdout.getvalue())['status'], 'matched')
        self.assertEqual(stderr.getvalue(), '')
        self.source['content'] = 'Altered source content'; self.write_bundle()
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(verifier.main([str(self.bundle), '--repository-root', str(self.root)]), 1)


if __name__ == '__main__': unittest.main()
