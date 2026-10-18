"""Offline guard checks only. Synthetic temporary approvals never authorize actual mode."""
import argparse
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('capital_preparation', HERE / 'prepare_connection.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ConnectionGuards(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='synthetic-5988-guard-')
        self.addCleanup(self.directory.cleanup)
        self.review = Path(self.directory.name) / 'synthetic-review.json'
        self.acceptance = Path(self.directory.name) / 'synthetic-acceptance.json'
        self.bundle_hash = module.digest(HERE / 'derived-only-bundle.json')
        pins = {'script_sha256': module.digest(HERE / 'prepare_connection.py'),
                'derived_bundle_sha256': self.bundle_hash,
                'shadow_completion_sha256': module.digest(HERE / 'shadow-completion.json'),
                'expected_database_sha256': module.EXPECTED_DB}
        self.review_data = {**pins, 'status': 'pass', 'synthetic': True}
        self.acceptance_data = {**pins, 'status': 'accepted', 'synthetic': True}
        self.args = argparse.Namespace(independent_review=str(self.review), independent_review_sha256=None,
            parent_acceptance=str(self.acceptance), parent_acceptance_sha256=None, actor='root')
        self.write_receipts()

    def write_receipts(self):
        self.review.write_text(json.dumps(self.review_data))
        self.args.independent_review_sha256 = module.digest(self.review)
        self.acceptance_data['independent_review_sha256'] = self.args.independent_review_sha256
        self.acceptance.write_text(json.dumps(self.acceptance_data))
        self.args.parent_acceptance_sha256 = module.digest(self.acceptance)

    def check(self):
        # This only parses and compares files. It neither opens a DB nor calls main/Store.
        return module.approval_files(self.args, self.bundle_hash)

    def test_all_pins_parse_without_executing_actual(self):
        self.assertEqual(self.check()['expected_database_sha256'], module.EXPECTED_DB)

    def test_missing_review_rejected(self):
        self.args.independent_review = None
        with self.assertRaisesRegex(ValueError, 'path and SHA required'):
            self.check()

    def test_review_content_sha_mismatch_rejected(self):
        self.args.independent_review_sha256 = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA mismatch'):
            self.check()

    def test_nonaffirmative_review_rejected(self):
        self.review_data['status'] = 'pending'
        self.write_receipts()
        with self.assertRaisesRegex(ValueError, 'not affirmative'):
            self.check()

    def test_changed_script_pin_rejected(self):
        self.review_data['script_sha256'] = '0' * 64
        self.write_receipts()
        with self.assertRaisesRegex(ValueError, 'pin mismatch'):
            self.check()

    def test_changed_shadow_pin_rejected(self):
        self.acceptance_data['shadow_completion_sha256'] = '0' * 64
        self.write_receipts()
        with self.assertRaisesRegex(ValueError, 'pin mismatch'):
            self.check()

    def test_parent_must_bind_same_review(self):
        self.acceptance_data['independent_review_sha256'] = '0' * 64
        self.acceptance.write_text(json.dumps(self.acceptance_data))
        self.args.parent_acceptance_sha256 = module.digest(self.acceptance)
        with self.assertRaisesRegex(ValueError, 'pin independent review'):
            self.check()

    def test_actor_must_be_parent(self):
        self.args.actor = 'child-agent'
        with self.assertRaisesRegex(ValueError, 'reserved for parent root'):
            self.check()

    def test_schema_comparison_normalizes_row_factory(self):
        connection = sqlite3.connect(':memory:')
        self.addCleanup(connection.close)
        connection.execute('CREATE TABLE synthetic (id TEXT PRIMARY KEY)')
        before = module.schema(connection)
        connection.row_factory = sqlite3.Row
        self.assertEqual(module.schema(connection), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
