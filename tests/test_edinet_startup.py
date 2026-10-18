from contextlib import redirect_stdout
from io import StringIO, BytesIO
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

spec = importlib.util.spec_from_file_location('edinet_startup', Path(__file__).resolve().parents[1] / 'scripts/start_edinet_research.py')
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
KEY = 'TEST-private-key-%+987654321'


def document(**updates):
    return dict({'secCode': '68140', 'docTypeCode': '160', 'docDescription': '半期報告書',
                 'xbrlFlag': '1', 'docID': 'S100TEST', 'periodStart': None,
                 'periodEnd': '2026-08-31', 'filerName': '古野電気'}, **updates)


def package(content=b'<xbrl>synthetic</xbrl>'):
    out = BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z: z.writestr('XBRL/PublicDoc/test.xbrl', content)
    return out.getvalue()


class Response:
    def __init__(self, raw, status=200, headers=None, fail=False):
        self.raw = raw; self.status_code = status; self.headers = headers or {}; self.fail = fail
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def iter_content(self, size):
        yield self.raw
        if self.fail: raise RuntimeError('partial secret ' + KEY)


class EDINETStartupTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name); self.out = self.root / 'output'
        self.client = Mock(); self.parser = Mock(return_value={'schema_version': 1, 'companies': [], 'sources': []})

    def responses(self, rows=None, **kw):
        raw = json.dumps({'metadata': {'status': '200'}, 'results': [document()] if rows is None else rows}).encode()
        self.client.get.side_effect = [Response(raw, **kw), Response(package())]

    def run_start(self, **kwargs):
        with patch('sqlite3.connect', side_effect=AssertionError('DB forbidden')):
            return s.run(environ={'EDINET_API_KEY': KEY}, output=self.out,
                         client_factory=lambda: self.client, parser=self.parser, **kwargs)

    def assert_no_secret(self):
        for p in self.root.rglob('*'):
            if p.is_file():
                self.assertNotIn(KEY.encode(), p.read_bytes()); self.assertNotIn(s.quote(KEY, safe='').encode(), p.read_bytes())

    def test_check_and_missing_key_no_network_DB_or_output_directory(self):
        for env, check in [({}, False), ({}, True), ({'EDINET_API_KEY': KEY}, True)]:
            factory = Mock(side_effect=AssertionError('network forbidden'))
            with patch('sqlite3.connect', side_effect=AssertionError('DB forbidden')):
                result = s.run(check=check, environ=env, output=self.out, client_factory=factory)
            self.assertFalse(self.out.exists()); factory.assert_not_called(); self.assertEqual(result['GETs'], 0)
            self.assertNotIn(KEY, json.dumps(result))

    def test_one_candidate_exact_two_requests_and_instance_parser(self):
        self.responses(); result = self.run_start()
        self.assertEqual(result['status'], 'candidate_bundle_saved_meaning_review_required')
        self.assertEqual(self.client.get.call_count, 2)
        first, second = self.client.get.call_args_list
        self.assertEqual(first.args, (s.BASE + '/documents.json',))
        self.assertEqual(first.kwargs['params'], {'date': '2026-10-09', 'type': 2, 'Subscription-Key': KEY})
        self.assertEqual(second.args, (s.BASE + '/documents/S100TEST',))
        self.assertEqual(second.kwargs['params'], {'type': 1, 'Subscription-Key': KEY})
        self.assertIs(first.kwargs['verify'], True); self.assertIs(first.kwargs['allow_redirects'], False)
        self.assertEqual(self.parser.call_args.kwargs['source'], 'instance')
        self.assertEqual(self.parser.call_args.args[1]['periodStart'], None)
        self.assertTrue((self.out / 'document.zip').exists()); self.assert_no_secret()

    def test_zero_multiple_and_corrective_nonordinary_flags(self):
        for rows in [[], [document(), document(docID='S100OTHR')],
                     [document(docDescription='訂正半期報告書')], [document(secCode='68141')],
                     [document(docTypeCode='170')], [document(xbrlFlag='0')]]:
            with self.subTest(rows=rows):
                self.out = self.root / str(len(list(self.root.iterdir())))
                self.responses(rows); self.client.get.reset_mock(); result = self.run_start()
                self.assertEqual(result['GETs'], 1); self.assertEqual(self.client.get.call_count, 1)
                self.assertFalse((self.out / 'document.zip').exists())
        self.parser.assert_not_called()

    def test_HTTP_redirect_partial_length_and_size_stop_without_retry(self):
        for response in [Response(b'error', status=403), Response(b'error', status=302),
                         Response(b'{}', fail=True), Response(b'{}', headers={'Content-Length': '5'}),
                         Response(b'{}', headers={'Content-Length': str(9 * 1024 * 1024)}),
                         Response(b'{}', headers={'Content-Length': 'invalid'})]:
            with self.subTest(response=response):
                self.out = self.root / str(len(list(self.root.iterdir())))
                self.client.get.reset_mock(); self.client.get.side_effect = [response]
                result = self.run_start(); self.assertEqual(result['status'], 'stopped')
                self.assertEqual(self.client.get.call_count, 1); self.assertFalse((self.out / 'document.zip').exists())
        self.assert_no_secret()

    def test_JSON_API_status_and_missing_results_preserve_safe_success_body(self):
        for body in [b'not JSON', b'{"metadata":{"status":"401"},"results":[]}',
                     b'{"metadata":{"status":"200"}}', b'{"results":[]}',
                     b'{"metadata":{"status":"200"},"results":[],"StatusCode":503}']:
            self.out = self.root / str(len(list(self.root.iterdir())))
            self.client.get.reset_mock(); self.client.get.side_effect = [Response(body)]
            result = self.run_start(); self.assertEqual(result['status'], 'stopped')
            self.assertEqual(self.client.get.call_count, 1); self.assertEqual((self.out / 'listing.json').read_bytes(), body)

    def test_success_body_and_parsed_bundle_secret_reflection_not_saved(self):
        self.client.get.side_effect = [Response(json.dumps({'echo': KEY}).encode())]
        result = self.run_start(); self.assertEqual(result['reason_code'], 'secret_reflection')
        self.assertFalse((self.out / 'listing.json').exists()); self.assert_no_secret()
        self.out = self.root / 'zipreflection'; self.responses()
        self.client.get.side_effect = [Response(json.dumps({'metadata': {'status': '200'}, 'results': [document()]}).encode()), Response(package(KEY.encode()))]
        result = self.run_start(); self.assertEqual(result['reason_code'], 'secret_reflection')
        self.assertFalse((self.out / 'document.zip').exists()); self.assert_no_secret()
        self.out = self.root / 'parserreflection'; self.responses(); self.parser.return_value = {'echo': KEY}
        result = self.run_start(); self.assertEqual(result['reason_code'], 'secret_reflection')
        self.assertFalse((self.out / 'candidate-bundle.json').exists()); self.assert_no_secret()

    def test_parser_exception_and_prints_do_not_leak_and_existing_output_is_protected(self):
        self.responses()
        def bad_parser(*a, **kw):
            print(KEY); raise RuntimeError('authenticated URL ' + KEY)
        self.parser.side_effect = bad_parser; stdout = StringIO()
        with redirect_stdout(stdout): result = self.run_start()
        self.assertEqual(result['reason_code'], 'startup_or_parse_failed'); self.assertNotIn(KEY, stdout.getvalue()); self.assert_no_secret()
        before = {p: p.read_bytes() for p in self.out.iterdir()}
        self.client.get.reset_mock(); result = self.run_start()
        self.assertEqual(result['status'], 'existing_output_stop'); self.client.get.assert_not_called()
        self.assertEqual(before, {p: p.read_bytes() for p in self.out.iterdir()})

    def test_stream_size_and_ZIP_failure_are_bounded(self):
        self.client.get.side_effect = [Response(b'X' * (8 * 1024 * 1024 + 1))]
        result = self.run_start(); self.assertEqual(result['reason_code'], 'response_too_large')
        self.assertEqual(self.client.get.call_count, 1); self.parser.assert_not_called()
        self.out = self.root / 'ZIPfailure'; self.responses()
        listing = json.dumps({'metadata': {'status': '200'}, 'results': [document()]}).encode()
        self.client.get.reset_mock(); self.client.get.side_effect = [Response(listing), Response(b'error', status=503)]
        result = self.run_start(); self.assertEqual(result['GETs'], 2)
        self.assertEqual(self.client.get.call_count, 2); self.parser.assert_not_called()
        self.assertFalse((self.out / 'document.zip').exists())

    def test_parser_diagnostic_reflection_is_suppressed_and_rejected(self):
        self.responses()
        def reflected(*a, **kw):
            print(KEY); return {'sources': []}
        self.parser.side_effect = reflected
        stdout = StringIO()
        with redirect_stdout(stdout): result = self.run_start()
        self.assertEqual(result['reason_code'], 'secret_reflection')
        self.assertNotIn(KEY, stdout.getvalue()); self.assertFalse((self.out / 'candidate-bundle.json').exists())

    def test_default_existing_adapter_reused_not_new_normalizer(self):
        self.responses()
        with patch.object(s, 'parse_edinet_package', self.parser):
            result = s.run(environ={'EDINET_API_KEY': KEY}, output=self.out, client_factory=lambda: self.client)
        self.assertEqual(result['GETs'], 2); self.parser.assert_called_once()


if __name__ == '__main__': unittest.main()
