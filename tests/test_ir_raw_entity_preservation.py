"""Synthetic offline HTTP entities; never call an issuer or start a crawler."""
import importlib.util
import itertools
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from hashlib import sha256
import io
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("raw_entity_research", ROOT / "scripts/research_ir_universe.py")
research = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(research)
FOLLOWUP_SPEC = importlib.util.spec_from_file_location("raw_entity_followups", ROOT / "scripts/collect_ir_followups.py")
followups = importlib.util.module_from_spec(FOLLOWUP_SPEC)
FOLLOWUP_SPEC.loader.exec_module(followups)


class RawEntityPreservationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.raw = Path(temporary.name) / "raw"
        ticks = itertools.count(0, 10)
        clock = patch.object(research.time, "monotonic", side_effect=lambda: next(ticks))
        clock.start()
        self.addCleanup(clock.stop)

    def response(self, body, *, content_type="text/html; charset=utf-8", status=200):
        response = MagicMock()
        response.__enter__.return_value = response
        response.url, response.status_code, response.encoding = "https://issuer.invalid/", status, "utf-8"
        response.headers = {"Content-Type": content_type}
        response.iter_content.return_value = [body]
        return response

    def capture(self, response, *, directory=None):
        fetcher = research.Fetcher(delay=0, raw_directory=self.raw if directory is None else directory)
        with patch.object(research.requests, "get", return_value=response) as get:
            result = fetcher.raw_get(response.url)
        self.assertEqual(get.call_count, 1)
        return fetcher, result

    def test_original_script_iframe_and_nonvisible_bytes_survive_visible_extraction(self):
        body = b'<html>IR<script>const data="retained";</script><iframe src="/form"></iframe><!-- comment --></html>'
        fetcher, result = self.capture(self.response(body))
        self.assertEqual(Path(result["raw_file"]).read_bytes(), body)
        self.assertEqual(result["raw_sha256"], sha256(body).hexdigest())
        self.assertNotIn("retained", result["text"])
        self.assertIn("not wire", result["raw_entity_semantics"])
        self.assertIsNotNone(result["raw_body_completed_at"])
        self.assertEqual(result["raw_storage_status"], "saved")
        self.assertIsNone(result["failure_signature"])
        self.assertEqual(fetcher.http_get_attempt_count, 1)
        self.assertEqual(research.request_metadata(result)["raw_file"], result["raw_file"])

    def test_cp932_and_decoding_failure_keep_received_entity_before_decode(self):
        body = '<meta charset="Shift_JIS"><title>日本語</title>'.encode("cp932")
        _, result = self.capture(self.response(body, content_type="text/html"))
        self.assertEqual(result["title"], "日本語")
        self.assertEqual(Path(result["raw_file"]).read_bytes(), body)
        _, invalid = self.capture(self.response(body, content_type="text/html; charset=invalid-test-codec"))
        self.assertEqual(invalid["error"], "LookupError")
        self.assertEqual(invalid["raw_storage_status"], "reused")
        self.assertEqual(Path(invalid["raw_file"]).read_bytes(), body)

    def test_omitted_directory_keeps_old_api_without_raw_metadata_or_files(self):
        value = self.response(b"<title>old API</title>")
        with patch.object(research.requests, "get", return_value=value):
            result = research.Fetcher(delay=0).raw_get(value.url)
        self.assertEqual(result["title"], "old API")
        self.assertFalse(any(key.startswith("raw_") for key in result))
        self.assertFalse(self.raw.exists())

    def test_storage_failure_does_not_become_network_failure_or_hide_extraction(self):
        self.raw.write_bytes(b"directory path occupied by a file")
        fetcher, result = self.capture(self.response(b"<title>complete</title>"))
        self.assertEqual(result["raw_storage_status"], "failed")
        self.assertEqual(result["raw_storage_error"], "FileExistsError")
        self.assertNotIn("raw_file", result)
        self.assertNotIn("error", result)
        self.assertIsNone(result["failure_signature"])
        self.assertEqual(result["title"], "complete")
        self.assertEqual(fetcher.failure_counts, {})
        self.assertFalse(fetcher.environment_failed.is_set())

    def test_corrupt_existing_sha_target_is_never_overwritten(self):
        body = b"<title>new entity</title>"
        self.raw.mkdir()
        target = self.raw / sha256(body).hexdigest()
        target.write_bytes(b"corrupt older target")
        _, result = self.capture(self.response(body))
        self.assertEqual(target.read_bytes(), b"corrupt older target")
        self.assertEqual(result["raw_storage_status"], "failed")
        self.assertNotIn("raw_file", result)
        self.assertNotIn("error", result)
        self.assertEqual(list(self.raw.glob(".raw-*.tmp")), [])

    def test_failure_after_temporary_write_never_publishes_completed_filename(self):
        with patch.object(research.os, "fsync", side_effect=OSError("synthetic storage failure")):
            fetcher, result = self.capture(self.response(b"<title>received</title>"))
        self.assertEqual(result["raw_storage_status"], "failed")
        self.assertEqual(result["raw_storage_error"], "OSError")
        self.assertEqual(result["title"], "received")
        self.assertNotIn("raw_file", result)
        self.assertIsNone(result["failure_signature"])
        self.assertEqual(fetcher.http_get_attempt_count, 1)
        self.assertEqual(list(self.raw.iterdir()), [])

    def test_stream_interruption_and_three_mib_limit_never_publish_partial_entity(self):
        def interrupted():
            yield b"<html>partial"
            raise research.requests.exceptions.ChunkedEncodingError("synthetic interruption")
        response = self.response(b"")
        response.iter_content.return_value = interrupted()
        _, result = self.capture(response)
        self.assertEqual(result["error"], "ChunkedEncodingError")
        self.assertEqual(result["raw_storage_status"], "not_saved_incomplete_entity")
        self.assertNotIn("raw_body_completed_at", result)
        self.assertFalse(self.raw.exists())
        response = self.response(b"")
        response.iter_content.return_value = [b"x" * (3 * 1024 * 1024), b"x"]
        _, result = self.capture(response)
        self.assertEqual(result["error"], "ValueError")
        self.assertEqual(result["raw_storage_status"], "not_saved_incomplete_entity")
        self.assertNotIn("raw_file", result)
        self.assertFalse(self.raw.exists())

    def test_exact_three_mib_and_empty_complete_entities_are_preserved(self):
        for body in (b"x" * (3 * 1024 * 1024), b""):
            with self.subTest(size=len(body)):
                _, result = self.capture(self.response(body, content_type="text/plain"))
                self.assertEqual(Path(result["raw_file"]).read_bytes(), body)
                self.assertEqual(result["raw_storage_status"], "saved")
                self.assertNotIn("error", result)

    def test_atomic_publication_and_concurrent_same_entity_reuse_one_sha_file(self):
        body = b"<html>synthetic concurrent entity</html>"
        barrier = threading.Barrier(2)
        real_link = research.os.link
        def publish(temporary, target):
            self.assertEqual(Path(temporary).read_bytes(), body)
            self.assertFalse(Path(target).exists())
            barrier.wait(timeout=5)
            real_link(temporary, target)
        def worker():
            response = self.response(body)
            fetcher = research.Fetcher(delay=0, raw_directory=self.raw)
            return fetcher.raw_get(response.url)
        with patch.object(research.requests, "get", side_effect=lambda *a, **k: self.response(body)), \
                patch.object(research.os, "link", side_effect=publish), ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))
        self.assertEqual(sorted(x["raw_storage_status"] for x in results), ["reused", "saved"])
        self.assertEqual(list(self.raw.iterdir()), [self.raw / sha256(body).hexdigest()])
        self.assertEqual(Path(results[0]["raw_file"]).read_bytes(), body)
        before = (self.raw / sha256(body).hexdigest()).stat()
        _, reused = self.capture(self.response(body))
        self.assertEqual(reused["raw_storage_status"], "reused")
        self.assertEqual((self.raw / sha256(body).hexdigest()).stat().st_ino, before.st_ino)

    def test_empty_cli_wires_output_raw_without_dispatching_a_request(self):
        output = self.raw.parent / "synthetic-cli"
        universe, seeds = self.raw.parent / "universe.csv", self.raw.parent / "seeds.json"
        universe.write_text("security_code,company_name,market,jpx_sector\n")
        seeds.write_text("[]")
        original = research.Fetcher
        with patch.object(research, "Fetcher", wraps=original) as constructor, \
                patch.object(research.requests, "get", side_effect=AssertionError("No network")) as get, \
                patch.object(research.sys, "argv", ["research_ir_universe.py", "--universe", str(universe),
                    "--seeds", str(seeds), "--output", str(output)]), redirect_stdout(io.StringIO()):
            research.main()
        constructor.assert_called_once_with(global_rps=1.0, raw_directory=output / "raw")
        get.assert_not_called()

    def test_followup_new_fetcher_is_wired_and_supplied_configuration_is_retained(self):
        output = self.raw.parent / "synthetic-followup"
        original = followups.BoundedFetcher
        with patch.object(followups, "BoundedFetcher", wraps=original) as constructor, \
                patch.object(followups.research.requests, "get", side_effect=AssertionError("No network")) as get:
            self.assertEqual(followups.collect(output, output / "new-state.json", {"selected": []}, 3, 1), 0)
        constructor.assert_called_once_with(3, 1, raw_directory=output / "raw")
        get.assert_not_called()
        supplied = original(3, 1, raw_directory=self.raw.parent / "caller-scope")
        with patch.object(followups, "BoundedFetcher", side_effect=AssertionError("Do not replace supplied fetcher")):
            self.assertEqual(followups.collect(output, output / "supplied-state.json", {"selected": []}, 3, 1, fetcher=supplied), 0)
        self.assertEqual(supplied.raw_directory, self.raw.parent / "caller-scope")


if __name__ == "__main__":
    unittest.main()
