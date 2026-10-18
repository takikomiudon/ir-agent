"""Only the observed saved_issuer_case PDF adapter's declared byte bindings."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('saved_issuer_pdf_verifier', Path(__file__).resolve().parents[1] / 'scripts/verify_case_source_bundle.py')
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
sha = lambda raw: sha256(raw).hexdigest()


class SavedIssuerPDFTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.case = self.root / 'case'; self.case.mkdir()
        self.raw = b'%PDF-Synthetic declaration only\r\n'
        self.output = 'Saved Japanese text 日本語\r\nSecond line\n\f'.encode()
        self.url = 'https://issuer.invalid/report.pdf'
        self.clock = '2026-10-16T00:00:02+00:00'
        self.capture = {'url': self.url, 'response_url': self.url, 'method': 'GET', 'HTTP_status': 200, 'complete_body': True,
            'error': None, 'http_get_started_at': '2026-10-16T00:00:00Z',
            'headers_received_at': '2026-10-16T00:00:01Z', 'http_get_completed_at': self.clock,
            'raw_saved_at': '2026-10-16T00:00:03Z', 'raw_sha256': sha(self.raw),
            'byte_count': len(self.raw), 'raw_file': 'raw.pdf', 'PDF_magic': True,
            'accepted_PDF_for_local_reading': True, 'response_headers': {'Authorization': 'SECRET-NOT-TO-EMIT'}}
        self.snapshot = {'url': self.url, 'sha256': sha(self.raw), 'http_status': 200, 'error': None,
            'retrieved_at': self.clock, 'publication_time': None, 'content_type': 'application/pdf',
            'original_complete_capture': self.capture, 'adapter_note': 'Offline saved PDF adapter'}
        self.source = {'id': 'case-public:synthetic-fixed-not-rederived', 'company_id': 'jp:TEST',
            'title': 'Synthetic', 'source_type': 'public_disclosure', 'url': self.url,
            'retrieved_at': self.clock, 'published_at': None, 'content': self.output.decode(),
            'metadata': {'provider': 'saved_issuer_case', 'saved_case_directory': 'case',
                'original_raw_file': 'raw.pdf', 'original_raw_sha256': sha(self.raw),
                'original_transport_snapshot': 'snapshot.json',
                'extraction': {'kind': 'pdf_text', 'saved_file': 'text.txt', 'sha256': sha(self.output)}}}
        (self.case / 'raw.pdf').write_bytes(self.raw); (self.case / 'text.txt').write_bytes(self.output)
        self.path = self.case / 'bundle.json'; self.write()

    def write(self):
        snap = json.dumps(self.snapshot).encode(); (self.case / 'snapshot.json').write_bytes(snap)
        self.source['metadata']['original_transport_snapshot_sha256'] = sha(snap)
        self.path.write_bytes(json.dumps({'schema_version': 1, 'sources': [self.source]}).encode())

    def audit(self): return v.verify_case_source_bundle(self.path, repository_root=self.root)

    def test_declared_bytes_match_without_reextracting_or_certifying_meaning(self):
        before = {p: sha(p.read_bytes()) for p in self.case.iterdir()}
        with patch('sqlite3.connect', side_effect=AssertionError('No DB')), \
             patch('socket.create_connection', side_effect=AssertionError('No network')), \
             patch('subprocess.run', side_effect=AssertionError('No extraction')):
            result = self.audit()
        self.assertEqual(result['status'], 'matched')
        self.assertTrue(result['all_declared_bytes_match'])
        self.assertEqual(result['sources'][0]['source_id_verification'], 'not_performed')
        self.assertEqual(result['sources'][0]['semantic_financial_verification'], 'not_performed')
        self.assertNotIn('SECRET-NOT-TO-EMIT', json.dumps(result))
        self.assertEqual(before, {p: sha(p.read_bytes()) for p in self.case.iterdir()})

    def test_raw_text_and_transport_byte_tampering(self):
        for filename in ['raw.pdf', 'text.txt', 'snapshot.json']:
            p = self.case / filename; old = p.read_bytes(); p.write_bytes(old + b'X')
            with self.subTest(filename=filename): self.assertEqual(self.audit()['status'], 'mismatch')
            p.write_bytes(old)

    def test_text_CRLF_change_even_with_updated_hash_is_mismatch(self):
        changed = self.output.replace(b'\r\n', b'\n'); (self.case / 'text.txt').write_bytes(changed)
        self.source['metadata']['extraction']['sha256'] = sha(changed); self.write()
        self.assertIn('extraction_source_content_bytes_mismatch', self.audit()['sources'][0]['reason_codes'])

    def test_rehashed_known_transport_contradictions(self):
        initial = deepcopy(self.snapshot)
        cases = [('url', 'https://issuer.invalid/different.pdf'), ('sha256', '0' * 64),
                 ('retrieved_at', '2026-10-16T00:00:04Z'), ('http_status', 503),
                 ('error', 'failed'), ('content_type', 'text/html'),
                 ('publication_time', '2026-10-15T00:00:00Z')]
        for key, value in cases:
            self.snapshot = deepcopy(initial); self.capture = self.snapshot['original_complete_capture']
            self.snapshot[key] = value; self.write()
            with self.subTest(key=key): self.assertEqual(self.audit()['status'], 'mismatch')

    def test_rehashed_nested_contradictions_and_false_flags(self):
        initial = deepcopy(self.snapshot)
        cases = [('url', 'https://issuer.invalid/other.pdf'), ('response_url', 'https://other.invalid/report.pdf'), ('raw_sha256', '0' * 64),
                 ('byte_count', 0), ('http_get_completed_at', '2026-10-16T00:00:04Z'),
                 ('raw_saved_at', '2026-10-15T00:00:00Z'), ('method', 'POST'),
                 ('HTTP_status', 403), ('error', 'incomplete'), ('complete_body', False),
                 ('PDF_magic', False), ('accepted_PDF_for_local_reading', False)]
        for key, value in cases:
            self.snapshot = deepcopy(initial); self.snapshot['original_complete_capture'][key] = value; self.write()
            with self.subTest(key=key): self.assertEqual(self.audit()['status'], 'mismatch')

    def test_missing_files_or_hashes_stay_unknown(self):
        p = self.case / 'raw.pdf'; old = p.read_bytes(); p.unlink()
        self.assertEqual(self.audit()['status'], 'unknown'); p.write_bytes(old)
        self.source['metadata'].pop('original_raw_sha256'); self.write()
        self.assertEqual(self.audit()['status'], 'unknown')
        self.source['metadata'].pop('original_raw_file'); self.write()
        self.assertEqual(self.audit()['status'], 'unknown')

    def test_unknown_or_incomplete_profile_not_inferred(self):
        initial = deepcopy(self.snapshot)
        for mode in ['extra', 'missing', 'nested_missing', 'nested_null']:
            self.snapshot = deepcopy(initial)
            if mode == 'extra': self.snapshot['alternative_profile'] = 2
            if mode == 'missing': self.snapshot.pop('adapter_note')
            if mode == 'nested_missing': self.snapshot['original_complete_capture'].pop('byte_count')
            if mode == 'nested_null': self.snapshot['original_complete_capture'] = None
            self.write()
            with self.subTest(mode=mode): self.assertEqual(self.audit()['status'], 'unknown')
        self.snapshot = initial; self.source['metadata']['extraction']['kind'] = 'html_visible_text'; self.write()
        self.assertEqual(self.audit()['status'], 'unknown')

    def test_unrecognized_profile_does_not_hide_known_raw_corruption(self):
        self.snapshot['new_profile'] = True; self.write(); (self.case / 'raw.pdf').write_bytes(b'altered')
        self.assertEqual(self.audit()['status'], 'mismatch')

    def test_malformed_capture_field_types(self):
        initial = deepcopy(self.snapshot)
        for key, value in [('byte_count', True), ('complete_body', 1), ('raw_sha256', []),
                           ('HTTP_status', True), ('raw_saved_at', 'not-a-time')]:
            self.snapshot = deepcopy(initial); self.snapshot['original_complete_capture'][key] = value; self.write()
            with self.subTest(key=key), self.assertRaises(ValueError): self.audit()

    def test_missing_nested_raw_file_and_unsafe_paths(self):
        initial = deepcopy(self.source)
        outside = self.root / 'outside'; outside.write_bytes(b'PRIVATE'); (self.case / 'escape').symlink_to(outside)
        for ref in ['../outside', str(outside), 'escape']:
            self.source = deepcopy(initial); self.source['metadata']['original_raw_file'] = ref; self.write()
            with self.subTest(ref=ref), self.assertRaises(ValueError): self.audit()
        self.source = initial; self.capture['raw_file'] = '../outside'; self.write()
        with self.assertRaises(ValueError): self.audit()

    def test_capture_raw_path_must_bind_even_for_identical_bytes(self):
        (self.case / 'second.pdf').write_bytes(self.raw); self.capture['raw_file'] = 'second.pdf'; self.write()
        self.assertEqual(self.audit()['status'], 'mismatch')

    def test_real_accepted_Q1_declarations_match_without_mutation(self):
        root = Path(__file__).resolve().parents[1]
        path = root / 'research/ir-case-studies-2026-10-15/4318/subsequent-Q1-public-review-2026-10-16/source-only-bundle.json'
        before = path.read_bytes(); result = v.verify_case_source_bundle(path, repository_root=root)
        self.assertEqual(result['status'], 'matched'); self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__': unittest.main()
