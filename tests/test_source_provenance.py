"""Multiple source parents retain the same identity, visibility and review gates."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from ir_agent.decision import _check_source_origins
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.models import source_origins, timestamp
from ir_agent.screening import evaluate_screening
import test_information_research as research_fixtures


BOUNDARY = timestamp("2026-10-09T18:00:00+09:00")


def source(source_id, **metadata):
    return {"id": source_id, "company_id": "demo-services", "source_type": "public_disclosure",
            "title": "Synthetic source graph", "url": "https://example.invalid/source",
            "published_at": "2026-10-01T15:00:00+09:00", "retrieved_at": "2026-10-01T16:00:00+09:00",
            "content": "Synthetic source graph only", "metadata": metadata}


class SourceProvenanceTests(unittest.TestCase):
    def test_legacy_plural_and_cross_field_overlap_are_validated_without_mutation(self):
        value = source("root", original_source_id="first", original_source_ids=["first", "second"])
        before = deepcopy(value)
        self.assertEqual(source_origins(value), ["first", "second"])
        self.assertEqual(value, before)
        self.assertEqual(source_origins(source("root")), [])
        self.assertEqual(source_origins(source("root", original_source_ids=[])), [])
        for field, invalid in (("original_source_id", None), ("original_source_id", []),
                               ("original_source_id", " "), ("original_source_ids", "first"),
                               ("original_source_ids", None), ("original_source_ids", {}),
                               ("original_source_ids", [True]), ("original_source_ids", ["first", "first"])):
            with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                source_origins(source("root", **{field: invalid}))

    def test_shared_parent_dag_is_not_a_cycle_but_a_back_edge_is(self):
        nodes = [source("root", original_source_id="left", original_source_ids=["left", "right"]),
                 source("left", original_source_ids=["shared"]), source("right", original_source_ids=["shared"]),
                 source("shared")]
        mapping = {s["id"]: s for s in nodes}
        self.assertIsNone(_check_source_origins(["root"], mapping, "demo-services", BOUNDARY))
        mapping["shared"]["metadata"]["original_source_ids"] = ["root"]
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            _check_source_origins(["root"], mapping, "demo-services", BOUNDARY)

    def test_second_origin_cannot_hide_future_missing_other_company_or_held_information(self):
        for variant in ("future", "missing", "other_company", "unclear"):
            nodes = [source("root", original_source_id="first", original_source_ids=["second"]), source("first"), source("second")]
            mapping = {s["id"]: s for s in nodes}
            if variant == "future": mapping["second"]["retrieved_at"] = "2027-01-01T00:00:00+09:00"
            elif variant == "missing": del mapping["second"]
            elif variant == "other_company": mapping["second"]["company_id"] = "another-company"
            else: mapping["second"].update(source_type="ir_reply", metadata={"information_status": "unclear"})
            with self.subTest(variant=variant):
                if variant == "other_company":
                    with self.assertRaisesRegex(ValueError, "another company"):
                        _check_source_origins(["root"], mapping, "demo-services", BOUNDARY)
                else:
                    expected = {"future": "source_origin_not_available", "missing": "missing_origin_source_snapshot", "unclear": "source_information_held_for_review"}[variant]
                    self.assertEqual(_check_source_origins(["root"], mapping, "demo-services", BOUNDARY), expected)

    def test_lifecycle_collects_every_parent_once_and_preserves_source_snapshots(self):
        nodes = [source("root", original_source_id="left", original_source_ids=["left", "right"]),
                 source("left", original_source_ids=["shared"]), source("right", original_source_ids=["shared"]), source("shared"), source("quote")]
        mapping = {s["id"]: s for s in nodes}; before = deepcopy(mapping)
        class Saved:
            def source(self, source_id): return deepcopy(mapping[source_id])
        collected = DecisionLifecycle(Saved()).sources_for({"company_id": "demo-services", "evidence_ids": ["root"]}, {"source_id": "quote"})
        self.assertEqual([s["id"] for s in collected], ["left", "quote", "right", "root", "shared"])
        self.assertEqual(mapping, before)

    def test_plural_parent_information_correction_queues_daily_without_rewriting_sources(self):
        env = research_fixtures.InformationResearchTests("runTest"); env.setUp(); self.addCleanup(env.doCleanups)
        auxiliary = deepcopy(env.store.source("demo-public-q2")); auxiliary.update(id="auxiliary-parent", requires_research=False)
        derived = deepcopy(env.store.source("reply:demo-reply-cost"))
        derived.update(id="multi-parent-derived", source_type="public_disclosure", requires_research=False)
        derived["metadata"] = {"original_source_id": "demo-public-q2", "original_source_ids": ["auxiliary-parent", "reply:demo-reply-cost"]}
        thesis = deepcopy(env.original_thesis)
        thesis.update(version=3, recorded_at="2026-10-09T17:30:00+09:00", evidence_ids=[derived["id"]])
        env.harness.ingest({"schema_version": 1, "sources": [auxiliary, derived], "theses": [thesis]})
        saved = env.store.source(derived["id"])
        env.correct()
        selected = env.queue()["selected"]
        self.assertEqual(len(selected), 1)
        packet = env.store.job(selected[0]["job_id"])["packet"]
        self.assertEqual(packet["new_information_review_refs"], [{"reply_id": "demo-reply-cost", "version": 1}])
        self.assertEqual(env.store.source(derived["id"]), saved)

    def test_screening_checks_synthetic_status_in_second_origin(self):
        value = json.loads((Path(__file__).resolve().parents[1] / "examples/screening.json").read_text())
        value["synthetic"] = False
        for rule in value["policy"]["rules"]: rule["source"]["kind"] = "user"
        for item in value["sources"]: item["metadata"].pop("synthetic")
        original = value["sources"][0]
        first = deepcopy(original); first.update(id="plain-parent", metadata={})
        second = deepcopy(original); second.update(id="synthetic-parent", metadata={"synthetic": True})
        original["metadata"].update(original_source_id="plain-parent", original_source_ids=["synthetic-parent"])
        value["sources"].extend([first, second])
        result = evaluate_screening(value)
        self.assertEqual(result["status"], "needs_data")
        self.assertIn("synthetic_source_requires_synthetic_context", result["rule_results"][0]["reason_codes"])


if __name__ == "__main__": unittest.main()
