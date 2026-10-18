"""Finite malformed JSON boundaries remain validation errors without mutation."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ir_agent.cli import main
from ir_agent.information_value import calculate_information_value
from ir_agent.models import (timestamp, validate_company, validate_question,
                             validate_reply, validate_result, validate_source)
from ir_agent.observation_store import ObservationStore, SCHEMA
from ir_agent.observations import validate_observation
from ir_agent.screening import evaluate_screening
from ir_agent.store import Store

ROOT = Path(__file__).resolve().parents[1]


def example(name):
    return json.loads((ROOT / "examples" / name).read_text())


class InputBoundaryTests(unittest.TestCase):
    def unchanged_error(self, function, record):
        before = deepcopy(record)
        with self.assertRaises(ValueError): function(record)
        self.assertEqual(record, before)

    def test_screening_enum_and_path_shapes_are_validation_errors(self):
        changes = [lambda v: v["policy"]["rules"][0].update(operator=[]),
                   lambda v: v["policy"]["rules"][0]["source"].update(kind={}),
                   lambda v: v["policy"]["rules"][0]["comparison"].update(kind=True),
                   lambda v: v["metrics"]["pe"]["period"].update(kind=None),
                   lambda v: v["metrics"]["pe"]["bindings"].update(value=1.5),
                   lambda v: v["sources"][0].update(source_type=[])]
        for index, change in enumerate(changes):
            value = example("screening.json"); change(value)
            with self.subTest(case=index): self.unchanged_error(evaluate_screening, value)

    def test_observation_enum_shapes_fail_before_any_store_write(self):
        changes = [lambda v: v["hypothesis"].update(state_timing=[]),
                   lambda v: v["dispatch"].update(status={}),
                   lambda v: v["replies"][0].update(signal=None),
                   lambda v: v["replies"][0].update(information_status=False),
                   lambda v: v["verification"].update(state=[]),
                   lambda v: v["verification"].update(status=1.5)]
        connection = sqlite3.connect(":memory:", isolation_level=None)
        self.addCleanup(connection.close); connection.executescript(SCHEMA)
        store = ObservationStore(connection)
        for index, change in enumerate(changes):
            value = example("ir-observations.json")["records"][0]; change(value)
            with self.subTest(case=index):
                self.unchanged_error(validate_observation, value)
                self.unchanged_error(lambda r: store.register(r, "2026-11-20T00:00:00+09:00"), value)
        self.assertEqual(connection.execute("SELECT count(*) FROM ir_observations").fetchone()[0], 0)
        self.assertEqual(connection.execute("SELECT count(*) FROM ir_observation_versions").fetchone()[0], 0)

    def test_shared_model_enums_reject_non_string_json_values(self):
        cases = [(validate_company, example("demo.json")["companies"][0], lambda v: v.update(status=[])),
                 (validate_source, example("demo.json")["sources"][0], lambda v: v.update(source_type={})),
                 (validate_question, example("question.json"), lambda v: v["branches"][0].update(action=True)),
                 (validate_reply, example("reply.json"), lambda v: v.update(information_status=None)),
                 (validate_result, example("research-result.json"), lambda v: v.update(proposed_action=1.5))]
        for function, value, change in cases:
            change(value)
            with self.subTest(function=function.__name__): self.unchanged_error(function, value)

    def test_information_value_rejects_shapes_without_mutating_financial_inputs(self):
        changes = [lambda v: v["provenance"]["prior"].update(kind=[]),
                   lambda v: v.update(states=[{}]), lambda v: v.update(question_cost=True),
                   lambda v: v.update(prior=None), lambda v: v.update(unit=1.5)]
        for index, change in enumerate(changes):
            value = example("information-value.json"); change(value)
            with self.subTest(case=index): self.unchanged_error(calculate_information_value, value)

    def test_utc_normalization_overflow_is_a_validation_error_without_clamping(self):
        for value in ("9999-12-31T23:59:59-23:59", "0001-01-01T00:00:00+23:59"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "UTC datetime range"):
                timestamp(value)
        self.assertEqual(timestamp("2026-10-15T09:00:00+09:00").isoformat(), "2026-10-15T00:00:00+00:00")

    def test_cli_reports_errors_without_traceback_or_changing_existing_db_and_files(self):
        screen = example("screening.json"); screen["policy"]["rules"][0]["operator"] = []
        observation = example("ir-observations.json"); observation["records"][0]["hypothesis"]["state_timing"] = {}
        info = example("information-value.json"); info["provenance"]["prior"]["kind"] = []
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "existing.sqlite3"
            store = Store(database); store.close()
            def dump():
                connection = sqlite3.connect(database)
                try: return list(connection.iterdump())
                finally: connection.close()
            before = dump()
            commands = [(["screen"], screen), (["observations", "summarize"], observation), (["information-value"], info)]
            for index, (command, document) in enumerate(commands):
                path = Path(directory) / f"invalid-{index}.json"
                encoded = json.dumps(document); path.write_text(encoded)
                stdout, stderr = io.StringIO(), io.StringIO()
                with self.subTest(command=command), redirect_stdout(stdout), redirect_stderr(stderr):
                    result = main(["--db", str(database), *command, str(path)])
                self.assertEqual(result, 1)
                self.assertTrue(stderr.getvalue().startswith("ir-agent:"))
                self.assertNotIn("Traceback", stderr.getvalue())
                self.assertEqual(stdout.getvalue(), "")
                self.assertEqual(path.read_text(), encoded)
                self.assertEqual(dump(), before)


if __name__ == "__main__": unittest.main()
