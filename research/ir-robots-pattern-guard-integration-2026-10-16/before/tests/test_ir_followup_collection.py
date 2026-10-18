"""Local-only regressions for bounded followups and evidence preservation."""
import importlib.util
import io
import itertools
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/collect_ir_followups.py"
SPEC = importlib.util.spec_from_file_location("ir_followups", SCRIPT)
followups = importlib.util.module_from_spec(SPEC)
try:
    SPEC.loader.exec_module(followups)
except ModuleNotFoundError:
    followups = None


@unittest.skipIf(followups is None, "requires the optional data environment")
class FollowupCollectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name) / "survey"
        self.research = followups.research

    def save(self, relative, value):
        self.research.write_json(self.output / relative, value)
        return relative

    def fixture(self, code="500A", links=None, status="provisional"):
        root = f"https://issuer{code.lower()}.example/"
        snapshot = self.save(f"evidence/{code}/root.json", {
            "security_code": code, "requested_url": root, "url": root,
            "retrieved_at": "2026-10-11T00:00:00+00:00", "http_status": 200,
            "text": "テスト会社 IRお問い合わせ", "title": "テスト会社", "headings": [],
            "links": links if links is not None else [{"url": root + "ir/contact", "label": "IRお問い合わせ"}], "forms": []})
        record = {"security_code": code, "company_name": "テスト会社", "official_url": root,
                  "investigation_status": status, "verification_level": "official_form_link_only",
                  "outreach_suitability": "candidate", "identity_status": "name_or_security_code_observed",
                  "public_ir_emails": [], "conditions": ["原条件"], "limitations": ["原制限"],
                  "manual_review_required": False, "manual_review": {"reviewer": "human", "notes": "原レビュー"},
                  "evidence": [{"snapshot": snapshot, "quote": "IRお問い合わせ"}],
                  "fetches": [{"snapshot": snapshot, "url": root, "http_status": 200}]}
        self.save(f"records/{code}.json", record)
        return record

    def response(self, url, status, text, headers=None):
        response = MagicMock()
        response.__enter__.return_value = response
        response.url, response.status_code, response.encoding = url, status, "utf-8"
        response.headers = {"Content-Type": "text/html; charset=utf-8", **(headers or {})}
        response.iter_content.return_value = [text.encode("utf-8")]
        return response

    def network(self, reply):
        ticks = itertools.count(0, 10)
        return (patch.object(self.research.time, "monotonic", side_effect=lambda: next(ticks)),
                patch.object(self.research.requests, "get", side_effect=reply))

    def parser_refresh_fixture(self):
        rows, hashes, records = [], {}, {}
        for code, target in followups.PARSER_REFRESH_TARGETS.items():
            record = self.fixture(code, links=[])
            root = record["official_url"]
            parent_ref = record["fetches"][0]["snapshot"]
            link = {"url": root + "ir/" if code == "2752" else target, "label": "IRお問い合わせ"}
            parent = followups.read_json(self.output / parent_ref)
            parent["links"] = [link]
            self.save(parent_ref, parent)
            old = {"requested_url": link["url"], "url": target, "http_status": 200,
                   "title": "テスト会社 IR情報", "text": "テスト会社 IR情報", "links": []}
            if link["url"] != target:
                old["redirects"] = [{"requested_url": link["url"], "http_status": 301, "redirect_target": target}]
            target_ref = self.save(f"evidence/{code}/old-target.json", old)
            record["fetches"].append({"snapshot": target_ref, "url": link["url"], "final_url": target, "http_status": 200})
            self.save(f"records/{code}.json", record)
            records[code] = followups.file_sha256(self.output / "records" / (code + ".json"))
            hashes.update({reference: followups.file_sha256(self.output / reference) for reference in (parent_ref, target_ref)})
            rows.append({"security_code": code, "target_url": target, "parent_url": root,
                         "parent_snapshot": parent_ref, "target_snapshot": target_ref, "parent_link": link,
                         "identity_and_ir_scope_evidence": [{"snapshot": target_ref, "quote": old["title"], "quote_source": "title"}]})
        self.save(followups.PARSER_REFRESH_AUDIT, {"refreshes": rows, "source_snapshots_to_preserve": hashes,
                                                "original_record_hashes_at_preparation": records})

    def identity_transition_fixture(self, code):
        record = self.fixture(code, links=[], status="unconfirmed")
        root = record["official_url"]
        name, legacy_name = "現テスト持株会社", "旧テスト企業"
        target = root + "news/holding-transition" if code == "3440" else "https://new" + code + ".example/"
        if code == "2300":
            quote = name + "のWEBサイトは 移転いたしました。"
            label = target
            role = "official_site_move"
        elif code == "3695":
            quote = ("旧テスト企業は持株会社体制へ移行し、社名を" + name + "に変更いたしました。 "
                     + name + "のWEBサイトは下記リンク先へ移行しております。 本サイトは子会社のWEBサイトです。")
            label = name
            role = "issuer_site_migration"
        else:
            quote = "2025.6.2 持株会社体制移行に伴うホームページリニューアルのお知らせ"
            label, role = quote, "holding_company_transition_notice"
        reference = record["fetches"][0]["snapshot"]
        page = followups.read_json(self.output / reference)
        page.update(title=legacy_name, text=quote + " " + label,
                    links=[{"url": target, "href": target, "label": label}])
        self.save(reference, page)
        record.update(company_name=name, verification_level="none", channels=[],
                      identity_status="unverified" if code == "3440" else "name_or_security_code_observed",
                      discovery={"seed_company_name": legacy_name},
                      manual_review={"reviewer": "manual_transition_tester", "reviewed_at": "2026-10-11T01:00:00+00:00"})
        evidence = {"snapshot": reference, "url": root, "retrieved_at": page["retrieved_at"], "quote": quote, "role": role}
        if code == "3440":
            evidence["source_link_url"] = target
        record["evidence"] = [evidence]
        self.save("records/" + code + ".json", record)
        proposal = {"security_code": code, "target_url": target, "source_url": root, "source_snapshot": reference,
                    "source_snapshot_sha256": followups.file_sha256(self.output / reference), "quote": label}
        part = "parts/adaptive-audit-transition-" + code + ".json"
        self.save(part, {"reviewed": [{"security_code": code, "todo": [proposal]}]})
        return record, page, reference, part

    def test_reviewed_identity_discovery_selects_exact_three_routes_without_channel_claim(self):
        for code in ("2300", "3440", "3695"):
            self.identity_transition_fixture(code)
        plan = followups.build_plan(self.output)
        self.assertEqual(3, plan["selected_company_count"])
        self.assertEqual(3, plan["selected_url_count"])
        for task in plan["selected"]:
            proof = task["identity_discovery_proof"]
            self.assertEqual("issuer_identity_discovery", task["purpose"])
            self.assertFalse(task["explicit_ir_link"])
            self.assertFalse(proof["IR_purpose_verified"])
            self.assertEqual("manual_transition_tester", proof["manual_reviewer"])
            self.assertEqual(task["company_name"], proof["current_jpx_company_name"])
            self.assertEqual(followups.file_sha256(self.output / task["parent_snapshot"]), proof["source_snapshot_sha256"])
            self.assertEqual(followups.file_sha256(self.output / "records" / (task["security_code"] + ".json")), proof["source_record_sha256"])
            if task["security_code"] == "3440":
                self.assertEqual("unverified", proof["identity_status"])
                self.assertFalse(proof["current_issuer_name_observed_in_notice"])

    def test_identity_discovery_rejects_forged_unreviewed_or_customer_routes(self):
        for damage in ("reviewer", "pending", "quote", "sha", "name", "customer_label"):
            with self.subTest(damage=damage):
                record, page, reference, part = self.identity_transition_fixture("3695")
                if damage == "reviewer":
                    record["manual_review"].pop("reviewer")
                elif damage == "pending":
                    record["manual_review_required"] = True
                elif damage == "quote":
                    record["evidence"][0]["quote"] += " original にない句"
                elif damage == "name":
                    record["company_name"] = "異なる上場企業"
                elif damage == "sha":
                    data = followups.read_json(self.output / part)
                    data["reviewed"][0]["todo"][0]["source_snapshot_sha256"] = "0" * 64
                    self.save(part, data)
                else:
                    page["links"][0]["label"] = "製品お問い合わせ"
                    self.save(reference, page)
                    data = followups.read_json(self.output / part)
                    data["reviewed"][0]["todo"][0].update(
                        quote="製品お問い合わせ", source_snapshot_sha256=followups.file_sha256(self.output / reference))
                    self.save(part, data)
                self.save("records/3695.json", record)
                self.assertEqual([], followups.build_plan(self.output)["selected"])
        # A holding notice allows only its exact same-host news link, not the
        # legacy site's other links, even when they are labelled IR contact.
        record, page, reference, part = self.identity_transition_fixture("3440")
        page["links"].append({"url": "https://customer.example/contact", "label": "IRお問い合わせ"})
        self.save(reference, page)
        data = followups.read_json(self.output / part)
        data["reviewed"][0]["todo"][0]["source_snapshot_sha256"] = followups.file_sha256(self.output / reference)
        self.save(part, data)
        tasks = followups.build_plan(self.output, only_codes=["3440"])["selected"]
        self.assertEqual([record["official_url"] + "news/holding-transition"], [task["url"] for task in tasks])
        record["discovery"]["seed_company_name"] = "別の旧会社"
        self.save("records/3440.json", record)
        self.assertEqual([], followups.build_plan(self.output, only_codes=["3440"])["selected"])
        record, page, reference, part = self.identity_transition_fixture("3440")
        external = "https://other-company.example/news/holding-transition"
        page["links"][0]["url"] = page["links"][0]["href"] = external
        record["evidence"][0]["source_link_url"] = external
        self.save(reference, page)
        self.save("records/3440.json", record)
        data = followups.read_json(self.output / part)
        data["reviewed"][0]["todo"][0].update(target_url=external,
            source_snapshot_sha256=followups.file_sha256(self.output / reference))
        self.save(part, data)
        self.assertEqual([], followups.build_plan(self.output, only_codes=["3440"])["selected"])
        record, page, reference, part = self.identity_transition_fixture("2300")
        page["links"].append({"url": "https://other-company.example/", "label": "他ブランド"})
        self.save(reference, page)
        data = followups.read_json(self.output / part)
        data["reviewed"][0]["todo"][0]["source_snapshot_sha256"] = followups.file_sha256(self.output / reference)
        self.save(part, data)
        self.assertEqual([], followups.build_plan(self.output, only_codes=["2300"])["selected"])

    def test_identity_discovery_rechecks_frozen_record_proof_before_company_get(self):
        record, page, reference, part = self.identity_transition_fixture("3695")
        plan = followups.build_plan(self.output)
        record["manual_review"]["notes"] = "review changed after selection"
        self.save("records/3695.json", record)
        calls = []

        def reply(url, **kwargs):
            calls.append(url)
            self.assertEqual(followups.PREFLIGHT, url)
            return self.response(url, 200, "新規上場")

        state_path = self.output / "run.json"
        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(2, followups.collect(self.output, state_path, plan, 1000, 0.25))
        self.assertEqual([], calls)
        self.assertEqual("identity_source_changed_stopped", followups.read_json(state_path)["status"])
        self.assertFalse((self.output / "attempts").exists())

    def test_identity_discovery_failed_get_keeps_unconfirmed_and_requires_manual_review(self):
        original, page, reference, part = self.identity_transition_fixture("3440")
        task = followups.build_plan(self.output)["selected"][0]
        followups.append_observation(self.output, task, {"url": task["url"], "http_status": 403}, "evidence/3440/denied.json", 1)
        updated = followups.read_json(self.output / "records/3440.json")
        self.assertEqual("unconfirmed", updated["investigation_status"])
        self.assertEqual("unverified", updated["identity_status"])
        self.assertEqual(original["evidence"], updated["evidence"])
        self.assertTrue(updated["manual_review_required"])
        self.assertEqual("issuer_identity_discovery", updated["followup_review_pending"][-1]["purpose"])
        self.assertEqual([original["manual_review"]], updated["previous_manual_review"])

    def identity_reference_fixture(self, code):
        route = followups.IDENTITY_REFERENCE_ROUTES[code]
        record = self.fixture(code, links=[], status="unconfirmed")
        reference = route["parent_snapshot"]
        links = [{"url": target, "href": target, "label": label} for target, label, _ in route["links"]]
        if code == "3853":
            links.insert(0, {**links[0], "label": "Global Site Global Site"})
        else:
            links.append(dict(links[0]))
        page = {"security_code": code, "requested_url": route["parent_url"], "url": route["parent_url"],
                "http_status": 200, "retrieved_at": "2026-10-11T00:00:00+00:00", "title": "English issuer page",
                "headings": [], "text": route["public_issuer_quote"] + " " + " ".join(link["label"] for link in links),
                "links": links, "forms": []}
        self.save(reference, page)
        record.update(company_name=route["company_name"], official_url=route["official_url"], identity_status="unverified",
                      evidence=[], discovery={"seed_company_name": route["company_name"], "official_url": route["official_url"]},
                      manual_review={"reviewer": "reference_tester", "reviewed_at": "2026-10-11T01:00:00+00:00"},
                      fetches=[{"snapshot": reference, "url": route["parent_url"], "http_status": 200}])
        self.save("records/" + code + ".json", record)
        part = followups.IDENTITY_REFERENCE_AUDIT
        data = followups.read_json(self.output / part) if (self.output / part).exists() else {"reviewer": "reference_tester", "reviewed": []}
        data["reviewed"] = [row for row in data["reviewed"] if row["security_code"] != code]
        data["reviewed"].append({"security_code": code, "company_name": record["company_name"],
            "reviewed_at": record["manual_review"]["reviewed_at"],
            "record_sha256_after_review": followups.file_sha256(self.output / "records" / (code + ".json")),
            "original_evidence_sha256": {reference: followups.file_sha256(self.output / reference)},
            "todo": [{"url": target, "quote": label, "parent_snapshot": reference, "method": "GET"}
                     for target, label, _ in route["links"]]})
        self.save(part, data)
        return record, page, reference, part

    def test_fixed_language_and_company_info_links_are_discovery_only(self):
        for code in ("3853", "3901"):
            self.identity_reference_fixture(code)
        plan = followups.build_plan(self.output)
        self.assertEqual(2, plan["selected_company_count"])
        self.assertEqual(3, plan["selected_url_count"])
        for task in plan["selected"]:
            proof = task["identity_discovery_proof"]
            self.assertEqual("issuer_identity_discovery", task["purpose"])
            self.assertFalse(task["explicit_ir_link"])
            self.assertFalse(proof["IR_purpose_verified"])
            self.assertFalse(proof["current_issuer_reception_verified"])
            self.assertFalse(proof["current_issuer_name_observed_in_source"])
            self.assertEqual(proof["current_jpx_company_name"], proof["seed_company_name"])
            self.assertEqual(task["official_url"], proof["official_seed_url"])
            self.assertEqual(followups.file_sha256(self.output / task["parent_snapshot"]), proof["source_snapshot_sha256"])
            self.assertEqual(followups.file_sha256(self.output / followups.IDENTITY_REFERENCE_AUDIT), proof["proposal_source_sha256"])
            if task["security_code"] == "3853":
                self.assertEqual("Japanese", task["discovery_link_label"])
                self.assertEqual(1, task["source_link_index"])
        with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")), \
                patch.object(self.research, "write_json", side_effect=AssertionError("write prohibited")), redirect_stdout(io.StringIO()):
            self.assertEqual(0, followups.main(["--output", str(self.output), "--plan-only"]))

    def test_fixed_identity_references_require_review_seed_and_original_hashes(self):
        for damage in ("pending", "reviewer", "review_time", "seed", "company", "official", "record_hash", "source_hash", "part"):
            with self.subTest(damage=damage):
                record, page, reference, part = self.identity_reference_fixture("3901")
                data = followups.read_json(self.output / part)
                row = next(row for row in data["reviewed"] if row["security_code"] == "3901")
                if damage == "pending":
                    record["manual_review_required"] = True
                elif damage == "reviewer":
                    record["manual_review"].pop("reviewer")
                elif damage == "review_time":
                    record["manual_review"]["reviewed_at"] = "2026-10-11T01:00:00"
                elif damage == "seed":
                    record["discovery"]["seed_company_name"] = "他社"
                elif damage == "company":
                    record["company_name"] = "他社"
                elif damage == "official":
                    record["official_url"] = "https://unrelated.example/"
                elif damage == "source_hash":
                    row["original_evidence_sha256"][reference] = "0" * 64
                elif damage == "record_hash":
                    row["record_sha256_after_review"] = "0" * 64
                self.save("records/3901.json", record)
                if damage not in {"record_hash", "part"}:
                    row["record_sha256_after_review"] = followups.file_sha256(self.output / "records/3901.json")
                self.save(part, data)
                if damage == "part":
                    (self.output / part).rename(self.output / "parts/adaptive-audit-other.json")
                self.assertEqual([], followups.build_plan(self.output, only_codes=["3901"])["selected"])

        # Exact language labels still do not allow arbitrary externally hosted
        # brands, forums or customer routes, even with updated audit hashes.
        for damage in ("external", "href", "customer_label", "missing_public_quote"):
            with self.subTest(damage=damage):
                record, page, reference, part = self.identity_reference_fixture("3901")
                data = followups.read_json(self.output / part)
                row = next(row for row in data["reviewed"] if row["security_code"] == "3901")
                for link in page["links"]:
                    if link["label"] == "JAPANESE":
                        if damage == "external":
                            link["url"] = link["href"] = "https://customer.example/forum/"
                        elif damage == "href":
                            link["href"] = "https://customer.example/"
                        elif damage == "customer_label":
                            link["label"] = "Customer Sign Up for a Free Trial"
                if damage == "external":
                    row["todo"][0]["url"] = "https://customer.example/forum/"
                elif damage == "customer_label":
                    row["todo"][0]["quote"] = "Customer Sign Up for a Free Trial"
                elif damage == "missing_public_quote":
                    page["text"] = page["text"].replace("JAPANESE", "ENGLISH")
                self.save(reference, page)
                row["original_evidence_sha256"][reference] = followups.file_sha256(self.output / reference)
                self.save(part, data)
                selected = followups.build_plan(self.output, only_codes=["3901"])["selected"]
                self.assertEqual(["https://www.marklines.com/en/corporate_profile/"], [task["url"] for task in selected])

    def test_two_identity_urls_preserve_classification_and_detect_other_writer(self):
        for concurrent_change in (False, True):
            with self.subTest(concurrent_change=concurrent_change):
                if (self.output / "run.json").exists():
                    (self.output / "run.json").unlink()
                original, page, reference, part = self.identity_reference_fixture("3901")
                plan, calls = followups.build_plan(self.output, only_codes=["3901"]), []

                def reply(url, **kwargs):
                    calls.append(url)
                    if url == followups.PREFLIGHT:
                        return self.response(url, 200, "新規上場")
                    if url.endswith("/robots.txt"):
                        return self.response(url, 404, "")
                    return self.response(url, 200, "<title>会社案内</title>マークラインズ")

                append = followups.append_observation

                def observe(*args):
                    own_sha = append(*args)
                    if concurrent_change:
                        modified = followups.read_json(self.output / "records/3901.json")
                        modified["conditions"].append("他writerの変更")
                        self.save("records/3901.json", modified)
                    return own_sha

                clock, http = self.network(reply)
                with clock, http, patch.object(followups, "append_observation", side_effect=observe):
                    result = followups.collect(self.output, self.output / "run.json", plan, 1000, 0.25)
                state = followups.read_json(self.output / "run.json")
                self.assertEqual(2 if concurrent_change else 0, result)
                self.assertEqual("identity_source_changed_stopped" if concurrent_change else "completed", state["status"])
                self.assertEqual(1 if concurrent_change else 2, len([url for url in calls if url in {task["url"] for task in plan["selected"]}]))
                updated = followups.read_json(self.output / "records/3901.json")
                self.assertEqual("unconfirmed", updated["investigation_status"])
                self.assertEqual("unverified", updated["identity_status"])
                self.assertEqual(original["evidence"], updated["evidence"])
                self.assertTrue(updated["manual_review_required"])
                self.assertEqual(1 if concurrent_change else 2, len(updated["followup_review_pending"]))
                self.assertEqual([original["manual_review"]], updated["previous_manual_review"])

    def stop_identity_run(self, code="3901", budget_stop=False):
        if code == "3901":
            self.identity_reference_fixture(code)
        else:
            self.identity_transition_fixture(code)
        plan, calls = followups.build_plan(self.output, only_codes=[code]), []
        state_path = self.output / (code + "-identity-run.json")
        if state_path.exists():
            state_path.unlink()

        def reply(url, **kwargs):
            calls.append(url)
            if url == followups.PREFLIGHT:
                return self.response(url, 200, "新規上場")
            if url.endswith("/robots.txt"):
                return self.response(url, 404, "")
            if code == "3901" and url.endswith("/corporate_profile/"):
                return self.response(url, 200, "MarkLines Co., Ltd. Company Overview")
            return self.response(url, 503, "Invalid argument|remote address:envoy://cloudflare_https_tunnel/")

        clock, http = self.network(reply)
        with clock, http:
            result = followups.collect(self.output, state_path, plan, 3 if budget_stop else 1000, 0.25)
        self.assertEqual(0 if budget_stop else 2, result)
        stopped = followups.read_json(state_path)
        self.assertEqual("get_budget_exhausted" if budget_stop else "environment_stopped", stopped["status"])
        self.assertEqual(1, len(stopped["todo"]))
        self.assertEqual([], followups.build_plan(self.output, only_codes=[code])["selected"])
        return state_path, plan, calls

    def test_identity_resume_retains_failed_and_unstarted_urls_after_own_updates(self):
        for code, budget_stop in (("3901", False), ("3901", True), ("3695", False)):
            with self.subTest(code=code, budget_stop=budget_stop):
                state_path, plan, calls = self.stop_identity_run(code, budget_stop)
                stopped = followups.read_json(state_path)
                lineage = stopped["identity_record_lineage"][code]
                self.assertEqual(followups.file_sha256(self.output / "records" / (code + ".json")), lineage["expected_record_sha256"])
                self.assertEqual(lineage["source_record_sha256"], followups.file_sha256(self.output / lineage["original_record_archive"]))
                resumed_calls = []

                def healthy(url, **kwargs):
                    resumed_calls.append(url)
                    return self.response(url, 404 if url.endswith("/robots.txt") else 200,
                                         "新規上場" if url == followups.PREFLIGHT else "公開企業案内")

                clock, http = self.network(healthy)
                with clock, http, redirect_stdout(io.StringIO()):
                    # Exercise the real CLI path: its rebuilt fresh plan is empty.
                    self.assertEqual(0, followups.main(["--output", str(self.output), "--state", str(state_path),
                                                       "--only-codes", code, "--global-rps", "0.25"]))
                finished = followups.read_json(state_path)
                self.assertEqual("completed", finished["status"])
                self.assertEqual([], finished["todo"])
                self.assertEqual(len(plan["selected"]), len(finished["done"]))
                pending_url = stopped["todo"][0]["url"]
                self.assertEqual(1, resumed_calls.count(pending_url))
                for task in plan["selected"]:
                    if task["url"] != pending_url:
                        self.assertEqual(1, calls.count(task["url"]))
                        self.assertNotIn(task["url"], resumed_calls)
                self.assertEqual(len(calls) + len(resumed_calls), finished["http_get_attempt_count"])
                updated = followups.read_json(self.output / "records" / (code + ".json"))
                self.assertTrue(updated["manual_review_required"])
                self.assertEqual("unconfirmed", updated["investigation_status"])
                record_bytes = (self.output / "records" / (code + ".json")).read_bytes()
                with patch.object(self.research.requests, "get", side_effect=AssertionError("completed GET prohibited")), redirect_stdout(io.StringIO()):
                    self.assertEqual(0, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", code]))
                self.assertEqual(record_bytes, (self.output / "records" / (code + ".json")).read_bytes())

    def test_identity_resume_blocks_other_writer_changed_evidence_and_old_states(self):
        for damage in ("record", "source", "part", "archive", "old_state", "saved_url"):
            with self.subTest(damage=damage):
                state_path, plan, _ = self.stop_identity_run()
                stopped = followups.read_json(state_path)
                lineage = stopped["identity_record_lineage"]["3901"]
                if damage == "record":
                    record = followups.read_json(self.output / "records/3901.json")
                    record["conditions"].append("他writerが追加した条件")
                    self.save("records/3901.json", record)
                elif damage == "source":
                    reference = plan["selected"][0]["parent_snapshot"]
                    page = followups.read_json(self.output / reference)
                    page["text"] += " source changed"
                    self.save(reference, page)
                elif damage == "part":
                    part = followups.read_json(self.output / followups.IDENTITY_REFERENCE_AUDIT)
                    part["new_review_note"] = "別更新"
                    self.save(followups.IDENTITY_REFERENCE_AUDIT, part)
                elif damage == "archive":
                    archive = followups.read_json(self.output / lineage["original_record_archive"])
                    archive["conditions"].append("元review後にarchiveが変更された")
                    self.save(lineage["original_record_archive"], archive)
                elif damage == "old_state":
                    stopped.pop("identity_record_lineage")
                    self.research.write_json(state_path, stopped)
                else:
                    for task in stopped["selected"]:
                        if followups.task_key(task) not in stopped["done"]:
                            task["url"] = "https://customer.example/contact"
                    self.research.write_json(state_path, stopped)
                before = (self.output / "records/3901.json").read_bytes()
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET before verified resume prohibited")), redirect_stdout(io.StringIO()):
                    self.assertEqual(2, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", "3901"]))
                blocked = followups.read_json(state_path)
                self.assertEqual("identity_resume_proof_missing_stopped" if damage == "old_state" else "identity_source_changed_stopped", blocked["status"])
                self.assertEqual(stopped["done"], blocked["done"])
                self.assertEqual(1, len(blocked["todo"]))
                self.assertEqual(before, (self.output / "records/3901.json").read_bytes())

    def ir_portal_reference_fixture(self):
        route = dict(followups.IR_PORTAL_REFERENCE)
        code, ref, part_ref = route["security_code"], route["parent_snapshot"], route["audit_snapshot"]
        record = self.fixture(code, links=[], status="unconfirmed")
        links = [{"url": route["parent_url"] + "#nav" + str(i), "href": "#nav" + str(i), "label": ""}
                 for i in range(route["source_link_index"])]
        links.append({"url": route["target_url"], "href": route["target_url"], "label": route["quote"]})
        page = {"security_code": code, "requested_url": route["parent_url"], "url": route["parent_url"],
                "http_status": 200, "retrieved_at": "2026-10-11T00:00:00+00:00", "title": route["company_name"],
                "headings": [], "text": route["quote"], "links": links, "forms": []}
        self.save(ref, page)
        release_ref = self.save("evidence/4444/event-release.json", {
            "url": route["official_url"] + "news/event-2020", "http_status": 200,
            "retrieved_at": page["retrieved_at"], "title": "2020年イベント",
            "text": "2020.08.27 本リリース問い合わせ先 IR担当 investor_relations@e-infonet.jp",
            "links": [], "forms": []})
        record.update(company_name=route["company_name"], official_url=route["official_url"],
            investigation_status="unconfirmed", verification_level="none", contact_url=None, channels=[],
            identity_status="unverified", public_ir_emails=[],
            discovery={"seed_company_name": route["company_name"], "official_url": route["official_url"]},
            manual_review={"reviewer": route["reviewer"], "reviewed_at": "2026-10-11T01:00:00+00:00",
                           "notes": "旧イベント宛先を現IR窓口として継承しない"},
            evidence=[{"snapshot": ref, "url": page["url"], "retrieved_at": page["retrieved_at"],
                       "quote": route["quote"], "role": "ir_issuer_transition_link", "source_link_url": route["target_url"]}],
            fetches=[{"snapshot": ref, "url": page["url"], "http_status": 200},
                     {"snapshot": release_ref, "url": route["official_url"] + "news/event-2020", "http_status": 200}])
        self.save("records/4444.json", record)
        route.update(source_sha256=followups.file_sha256(self.output / ref),
                     record_sha256=followups.file_sha256(self.output / "records/4444.json"))
        self.save(part_ref, {"reviewer": route["reviewer"], "status": "completed", "pending_validation": [],
            "reviewed": [{"security_code": code, "company_name": record["company_name"],
                "reviewed_at": record["manual_review"]["reviewed_at"], "record_sha256_after_review": route["record_sha256"],
                "original_evidence_sha256": {ref: route["source_sha256"]},
                "todo": [{"url": route["target_url"], "quote": route["quote"], "parent_snapshot": ref, "method": "GET"}]}]})
        route["audit_sha256"] = followups.file_sha256(self.output / part_ref)
        route_patch = patch.dict(followups.IR_PORTAL_REFERENCE, route)
        route_patch.start()
        self.addCleanup(route_patch.stop)
        return record, page, ref, part_ref

    def test_fixed_shareholder_portal_reference_is_read_only_identity_discovery(self):
        original, page, ref, part_ref = self.ir_portal_reference_fixture()
        plan = followups.build_plan(self.output, only_codes=["4444"])
        self.assertEqual(1, plan["selected_url_count"])
        task = plan["selected"][0]
        self.assertEqual("https://www.infonet-group.co.jp/", task["url"])
        self.assertEqual(44, task["source_link_index"])
        self.assertEqual("issuer_identity_discovery", task["purpose"])
        self.assertFalse(task["explicit_ir_link"])
        proof = task["identity_discovery_proof"]
        self.assertEqual("official_ir_portal_reference_discovery", proof["kind"])
        self.assertEqual("unverified", proof["identity_status"])
        for key in ("current_issuer_identity_verified", "current_issuer_name_observed_in_source",
                    "IR_purpose_verified", "current_issuer_reception_verified"):
            self.assertFalse(proof[key])
        self.assertEqual(followups.file_sha256(self.output / part_ref), proof["proposal_source_sha256"])
        with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")), \
                patch.object(self.research, "write_json", side_effect=AssertionError("write prohibited")), redirect_stdout(io.StringIO()):
            self.assertEqual(0, followups.main(["--output", str(self.output), "--plan-only", "--only-codes", "4444"]))
        self.assertEqual(original, followups.read_json(self.output / "records/4444.json"))

    def test_fixed_portal_reference_rejects_source_review_and_external_purpose_changes(self):
        for damage in ("record", "source", "part", "company", "seed", "reviewer", "naive_time", "pending",
                       "event_mail", "customer_url", "href", "generic_quote", "incomplete_audit", "missing_binding"):
            with self.subTest(damage=damage):
                record, page, ref, part_ref = self.ir_portal_reference_fixture()
                audit = followups.read_json(self.output / part_ref)
                if damage == "record":
                    record["conditions"].append("別担当の変更")
                elif damage == "source":
                    page["text"] += " 別の保存資料"
                elif damage == "part":
                    audit["additional_note"] = "別の監査変更"
                elif damage == "company":
                    record["company_name"] = "別の発行体"
                elif damage == "seed":
                    record["discovery"]["seed_company_name"] = "別の旧会社"
                elif damage == "reviewer":
                    record["manual_review"]["reviewer"] = "other_reviewer"
                elif damage == "naive_time":
                    record["manual_review"]["reviewed_at"] = "2026-10-11T01:00:00"
                elif damage == "pending":
                    record["manual_review_required"] = True
                elif damage == "event_mail":
                    record["public_ir_emails"] = ["investor_relations@e-infonet.jp"]
                elif damage == "customer_url":
                    page["links"][44]["url"] = page["links"][44]["href"] = "https://brand.example/"
                elif damage == "href":
                    page["links"][44]["href"] = "https://brand.example/forum"
                elif damage == "generic_quote":
                    page["text"] = page["links"][44]["label"] = "関連ブランドサイトはこちら"
                elif damage == "incomplete_audit":
                    audit["status"] = "saving"
                else:
                    record["evidence"][0]["role"] = "general_brand_reference"
                self.save("records/4444.json", record)
                self.save(ref, page)
                self.save(part_ref, audit)
                if damage not in {"record", "source", "part"}:
                    # Re-freeze local fixture hashes so these cases verify
                    # semantic binding, beyond immutable-file mismatch alone.
                    followups.IR_PORTAL_REFERENCE["record_sha256"] = followups.file_sha256(self.output / "records/4444.json")
                    followups.IR_PORTAL_REFERENCE["source_sha256"] = followups.file_sha256(self.output / ref)
                    audit["reviewed"][0]["record_sha256_after_review"] = followups.IR_PORTAL_REFERENCE["record_sha256"]
                    audit["reviewed"][0]["original_evidence_sha256"][ref] = followups.IR_PORTAL_REFERENCE["source_sha256"]
                    self.save(part_ref, audit)
                    followups.IR_PORTAL_REFERENCE["audit_sha256"] = followups.file_sha256(self.output / part_ref)
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                    self.assertEqual([], followups.build_plan(self.output, only_codes=["4444"])["selected"])

    def stop_portal_reference_run(self):
        original, page, ref, part_ref = self.ir_portal_reference_fixture()
        state_path, calls = self.output / "4444-run.json", []
        if state_path.exists():
            state_path.unlink()
        plan = followups.build_plan(self.output, only_codes=["4444"])

        def reply(url, **kwargs):
            calls.append(url)
            return self.response(url, 200 if url == followups.PREFLIGHT else 404 if url.endswith("/robots.txt") else 503,
                "新規上場" if url == followups.PREFLIGHT else "" if url.endswith("/robots.txt")
                else "Invalid argument|remote address:envoy://cloudflare_https_tunnel/")

        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(2, followups.collect(self.output, state_path, plan, 1000, 0.25))
        stopped = followups.read_json(state_path)
        self.assertEqual("environment_stopped", stopped["status"])
        self.assertEqual([], stopped["done"])
        self.assertEqual(1, len(stopped["todo"]))
        self.assertEqual([], followups.build_plan(self.output, only_codes=["4444"])["selected"])
        return state_path, plan, calls, original

    def test_portal_reference_resume_preserves_unverified_identity_and_no_event_mail(self):
        state_path, plan, calls, original = self.stop_portal_reference_run()
        resumed_calls = []

        def healthy(url, **kwargs):
            resumed_calls.append(url)
            return self.response(url, 404 if url.endswith("/robots.txt") else 200,
                "新規上場" if url == followups.PREFLIGHT else "IRお問い合わせ ir@new.example 株式情報")

        clock, http = self.network(healthy)
        with clock, http, redirect_stdout(io.StringIO()):
            self.assertEqual(0, followups.main(["--output", str(self.output), "--state", str(state_path),
                                               "--only-codes", "4444", "--global-rps", "0.25"]))
        final = followups.read_json(state_path)
        self.assertEqual("completed", final["status"])
        self.assertEqual([], final["todo"])
        self.assertEqual(1, len(final["done"]))
        self.assertEqual(1, resumed_calls.count(plan["selected"][0]["url"]))
        self.assertEqual(len(calls) + len(resumed_calls), final["http_get_attempt_count"])
        updated = followups.read_json(self.output / "records/4444.json")
        self.assertEqual("unconfirmed", updated["investigation_status"])
        self.assertEqual("unverified", updated["identity_status"])
        self.assertEqual([], updated["public_ir_emails"])
        self.assertEqual(original["evidence"], updated["evidence"])
        self.assertEqual([original["manual_review"]], updated["previous_manual_review"])
        self.assertTrue(updated["manual_review_required"])
        self.assertTrue(all(p["purpose"] == "issuer_identity_discovery" for p in updated["followup_review_pending"]))
        before = (self.output / "records/4444.json").read_bytes()
        with patch.object(self.research.requests, "get", side_effect=AssertionError("completed GET prohibited")), redirect_stdout(io.StringIO()):
            self.assertEqual(0, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", "4444"]))
        self.assertEqual(before, (self.output / "records/4444.json").read_bytes())

    def test_portal_reference_resume_stops_tampering_before_any_get(self):
        for damage in ("record", "source", "part", "archive", "old_state", "saved_url"):
            with self.subTest(damage=damage):
                state_path, plan, _, _ = self.stop_portal_reference_run()
                stopped = followups.read_json(state_path)
                lineage = stopped["identity_record_lineage"]["4444"]
                if damage == "record":
                    record = followups.read_json(self.output / "records/4444.json")
                    record["conditions"].append("他writerの変更")
                    self.save("records/4444.json", record)
                elif damage == "source":
                    page = followups.read_json(self.output / plan["selected"][0]["parent_snapshot"])
                    page["text"] += " source changed"
                    self.save(plan["selected"][0]["parent_snapshot"], page)
                elif damage == "part":
                    audit = followups.read_json(self.output / followups.IR_PORTAL_REFERENCE["audit_snapshot"])
                    audit["changed"] = True
                    self.save(followups.IR_PORTAL_REFERENCE["audit_snapshot"], audit)
                elif damage == "archive":
                    archive = followups.read_json(self.output / lineage["original_record_archive"])
                    archive["conditions"].append("archive changed")
                    self.save(lineage["original_record_archive"], archive)
                elif damage == "old_state":
                    stopped.pop("identity_record_lineage")
                    self.research.write_json(state_path, stopped)
                else:
                    stopped["selected"][0]["url"] = "https://brand.example/contact"
                    self.research.write_json(state_path, stopped)
                before = (self.output / "records/4444.json").read_bytes()
                with patch.object(self.research.requests, "get", side_effect=AssertionError("unverified resume GET prohibited")), redirect_stdout(io.StringIO()):
                    self.assertEqual(2, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", "4444"]))
                blocked = followups.read_json(state_path)
                self.assertEqual("identity_resume_proof_missing_stopped" if damage == "old_state" else "identity_source_changed_stopped", blocked["status"])
                self.assertEqual([], blocked["done"])
                self.assertEqual(1, len(blocked["todo"]))
                self.assertEqual(before, (self.output / "records/4444.json").read_bytes())

    def completed_identity_fixture(self):
        frozen = followups.COMPLETED_IDENTITY_PROPOSAL
        audit = {"status": "closed", "scope_closed": True, "reviewer": frozen["reviewer"],
                 "pending_security_codes": [], "completed_at_utc": "2026-10-11T02:00:00+00:00",
                 "records": [], "reviewed": [], "final_record_sha256": {}}
        packet = {"completed_audit_part": frozen["audit_path"], "finite_discovery_proposals": []}
        records = {}
        for code, route in followups.COMPLETED_IDENTITY_ROUTES.items():
            ref, index = route["parent_snapshot"], route["source_link_index"]
            links = [{"url": route["parent_url"] + "#nav" + str(i), "href": "#nav" + str(i), "label": ""}
                     for i in range(index)]
            links.append({"url": route["target_url"], "href": route["target_url"], "label": route["label"]})
            links.append({"url": "https://other-issuer.example/ir/contact", "href": "https://other-issuer.example/ir/contact",
                          "label": "IRお問い合わせ"})
            if code == "4651":
                links.extend([{"url": route["parent_url"] + "#gap", "href": "#gap", "label": ""},
                              {"url": "https://s.sanix.jp/", "href": "https://s.sanix.jp/", "label": route["label"]}])
            page = {"security_code": code, "requested_url": route["parent_requested_url"], "url": route["parent_url"],
                    "http_status": 200, "http_get_attempted": True, "retrieved_at": "2026-10-11T00:00:00+00:00",
                    "title": "Saved operating/service website", "headings": [], "forms": [], "links": links,
                    "text": route["quote"] + " " + (route["ir_transition_quote"] or "")}
            self.save(ref, page)
            record = self.fixture(code, links=[], status="unconfirmed")
            record.update(company_name=route["company_name"], official_url=route["official_url"],
                          verification_level="none", channels=[], public_ir_emails=[], contact_url=None,
                          individual_access="not_stated", outreach_suitability="unconfirmed", evidence=[],
                          identity_status="unverified" if code == "4651" else "name_or_security_code_observed",
                          discovery={"security_code": code, "official_url": route["official_url"],
                                     "seed_company_name": "サニックス" if code == "4651" else "（株）ＦＵＮＤＩＮＮＯ"},
                          manual_review={"reviewer": frozen["reviewer"], "reviewed_at": "2026-10-11T01:00:00+00:00",
                                         "notes": "金融IRではなく会社確認用の実公開リンク"},
                          fetches=[{"snapshot": ref, "url": route["parent_requested_url"], "http_status": 200}])
            self.save("records/" + code + ".json", record)
            records[code] = record
            audit["records"].append({"security_code": code, "company_name": record["company_name"], "state": "reviewed"})
            audit["reviewed"].append({"security_code": code})
            packet["finite_discovery_proposals"].append({
                "security_code": code, "company_name": route["company_name"], "official_seed_url": route["official_url"],
                "source_record_path": "records/" + code + ".json", "source_audit_part": frozen["audit_path"],
                "parent_snapshot": ref, "parent_url": route["parent_url"], "parent_requested_url": route["parent_requested_url"],
                "parent_retrieved_at": page["retrieved_at"], "source_link_index": index, "source_link": dict(links[index]),
                "url": route["target_url"], "target_url": route["target_url"], "quote": route["quote"],
                "kind": route["kind"], "ir_transition_quote": route["ir_transition_quote"], "method": "GET",
                "purpose": "issuer_identity_discovery", "current_issuer_identity_verified": False,
                "IR_purpose_verified": False, "current_issuer_reception_verified": False})
        self.save(frozen["audit_path"], audit)
        self.save(frozen["path"], packet)
        frozen_patch = patch.dict(followups.COMPLETED_IDENTITY_PROPOSAL, dict(frozen))
        frozen_patch.start()
        self.addCleanup(frozen_patch.stop)
        self.refreeze_completed_identity_fixture()
        return records

    def refreeze_completed_identity_fixture(self):
        """Freeze mock files so semantic counterexamples do not rely on SHA alone."""
        frozen = followups.COMPLETED_IDENTITY_PROPOSAL
        audit, packet = followups.read_json(self.output / frozen["audit_path"]), followups.read_json(self.output / frozen["path"])
        for proposal in packet["finite_discovery_proposals"]:
            code, ref = proposal["security_code"], proposal["parent_snapshot"]
            record = followups.read_json(self.output / "records" / (code + ".json"))
            record_sha, source_sha = followups.file_sha256(self.output / "records" / (code + ".json")), followups.file_sha256(self.output / ref)
            row = next(r for r in audit["records"] if r["security_code"] == code)
            row.update(draft_record=record, reviewed_record_sha256=record_sha, original_source_sha256={ref: source_sha})
            next(r for r in audit["reviewed"] if r["security_code"] == code)["record_sha256"] = record_sha
            audit["final_record_sha256"][code] = record_sha
            proposal.update(source_record_sha256=record_sha, parent_snapshot_sha256=source_sha)
        self.save(frozen["audit_path"], audit)
        frozen["audit_sha256"] = followups.file_sha256(self.output / frozen["audit_path"])
        packet["completed_audit_sha256"] = frozen["audit_sha256"]
        for proposal in packet["finite_discovery_proposals"]:
            proposal["source_audit_sha256"] = frozen["audit_sha256"]
        self.save(frozen["path"], packet)
        frozen["sha256"] = followups.file_sha256(self.output / frozen["path"])

    def test_completed_identity_plan_is_only_two_literal_links_and_does_not_write(self):
        originals = self.completed_identity_fixture()
        with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")), \
                patch.object(self.research, "write_json", side_effect=AssertionError("write prohibited")), redirect_stdout(io.StringIO()):
            self.assertEqual(0, followups.main(["--output", str(self.output), "--plan-only", "--only-codes", "462A", "4651"]))
            plan = followups.build_plan(self.output, only_codes=["462A", "4651"])
        self.assertEqual((2, 2), (plan["selected_company_count"], plan["selected_url_count"]))
        for task in plan["selected"]:
            code = task["security_code"]
            route, proof = followups.COMPLETED_IDENTITY_ROUTES[code], task["identity_discovery_proof"]
            self.assertEqual(route["source_link_index"], task["source_link_index"])
            self.assertEqual(route["target_url"], task["url"])
            self.assertEqual("issuer_identity_discovery", task["purpose"])
            self.assertFalse(task["explicit_ir_link"])
            for key in ("current_issuer_identity_verified", "IR_purpose_verified", "current_issuer_reception_verified"):
                self.assertIs(False, proof[key])
            self.assertEqual(followups.COMPLETED_IDENTITY_PROPOSAL["audit_sha256"], proof["completed_audit_source_sha256"])
            self.assertEqual(originals[code], followups.read_json(self.output / "records" / (code + ".json")))
        self.assertNotIn("https://s.sanix.jp/", [t["url"] for t in plan["selected"]])

    def test_completed_identity_rejects_hash_changes_and_semantic_fallbacks(self):
        damages = ("record", "source", "proposal", "audit", "company", "seed", "discovery_code", "discovery_name", "restricted", "pending", "reviewer",
                   "naive_review", "naive_capture", "http_404", "no_actual_get", "source_issuer", "quote", "raw_href",
                   "label", "alternate_index", "post_method", "claims_reception", "incomplete_audit", "wrong_audit_record")
        for damage in damages:
            with self.subTest(damage=damage):
                self.completed_identity_fixture()
                frozen, route = followups.COMPLETED_IDENTITY_PROPOSAL, followups.COMPLETED_IDENTITY_ROUTES["4651"]
                record = followups.read_json(self.output / "records/4651.json")
                page = followups.read_json(self.output / route["parent_snapshot"])
                packet, audit = followups.read_json(self.output / frozen["path"]), followups.read_json(self.output / frozen["audit_path"])
                proposal = next(p for p in packet["finite_discovery_proposals"] if p["security_code"] == "4651")
                if damage == "record": record["conditions"].append("other writer")
                elif damage == "source": page["text"] += " other source"
                elif damage == "proposal": packet["extra_note"] = "changed"
                elif damage == "audit": audit["extra_note"] = "changed"
                elif damage == "company": record["company_name"] = "別発行体"
                elif damage == "seed": record["official_url"] = "https://other-issuer.example/"
                elif damage == "discovery_code": record["discovery"]["security_code"] = "462A"
                elif damage == "discovery_name": record["discovery"]["seed_company_name"] = "別の事業会社"
                elif damage == "restricted": record["individual_access"] = record["outreach_suitability"] = "restricted"
                elif damage == "pending": record["manual_review_required"] = True
                elif damage == "reviewer": record["manual_review"]["reviewer"] = "other writer"
                elif damage == "naive_review": record["manual_review"]["reviewed_at"] = "2026-10-11T01:00:00"
                elif damage == "naive_capture": page["retrieved_at"] = proposal["parent_retrieved_at"] = "2026-10-11T00:00:00"
                elif damage == "http_404": page["http_status"] = 404
                elif damage == "no_actual_get": page["http_get_attempted"] = False
                elif damage == "source_issuer": page["security_code"] = "462A"
                elif damage == "quote": page["text"] = proposal["quote"] = "関連企業はこちら"
                elif damage == "raw_href": page["links"][99]["href"] = "https://s.sanix.jp/"
                elif damage == "label": page["links"][99]["label"] = "サニックスの別会社"
                elif damage == "alternate_index":
                    page["links"][99] = {"url": "https://s.sanix.jp/", "href": "https://s.sanix.jp/", "label": route["label"]}
                    proposal["source_link_index"] = 102
                elif damage == "post_method": proposal["method"] = "POST"
                elif damage == "claims_reception": proposal["current_issuer_reception_verified"] = True
                elif damage == "incomplete_audit": audit["status"] = "drafts_ready"
                else: next(r for r in audit["records"] if r["security_code"] == "4651")["state"] = "draft_ready"
                if damage in {"raw_href", "label", "alternate_index"}:
                    proposal["source_link"] = dict(page["links"][proposal["source_link_index"]])
                self.save("records/4651.json", record)
                self.save(route["parent_snapshot"], page)
                self.save(frozen["path"], packet)
                self.save(frozen["audit_path"], audit)
                if damage not in {"record", "source", "proposal", "audit"}:
                    self.refreeze_completed_identity_fixture()
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                    self.assertEqual([], followups.build_plan(self.output, only_codes=["4651"])["selected"])

    def test_completed_identity_changed_selected_proof_stops_before_preflight(self):
        for damage in ("record", "source", "proposal", "audit"):
            with self.subTest(damage=damage):
                self.completed_identity_fixture()
                plan = followups.build_plan(self.output, only_codes=["462A", "4651"])
                path = self.output / ("records/462A.json" if damage == "record" else
                    followups.COMPLETED_IDENTITY_ROUTES["462A"]["parent_snapshot"] if damage == "source" else
                    followups.COMPLETED_IDENTITY_PROPOSAL["path" if damage == "proposal" else "audit_path"])
                data = followups.read_json(path)
                data["other_writer_note"] = "external write"
                self.research.write_json(path, data)
                state_path = self.output / (damage + "-before-preflight.json")
                with patch.object(self.research.requests, "get", side_effect=AssertionError("unverified preflight GET prohibited")):
                    self.assertEqual(2, followups.collect(self.output, state_path, plan, 1000, 0.25))
                state = followups.read_json(state_path)
                self.assertEqual("identity_source_changed_stopped", state["status"])
                self.assertEqual((0, 2, []), (state["http_get_attempt_count"], len(state["todo"]), state["done"]))

    def test_completed_identity_capture_keeps_classification_and_identity_pending(self):
        originals, calls = self.completed_identity_fixture(), []
        plan = followups.build_plan(self.output, only_codes=["462A", "4651"])

        def healthy(url, **kwargs):
            calls.append(url)
            return self.response(url, 404 if url.endswith("/robots.txt") else 200,
                "新規上場" if url == followups.PREFLIGHT else "<form><input type='email' name='email'><textarea name='question'></textarea>IR</form>")

        clock, http = self.network(healthy)
        state_path = self.output / "completed-identity-success.json"
        with clock, http:
            self.assertEqual(0, followups.collect(self.output, state_path, plan, 1000, 0.25))
        self.assertEqual(5, len(calls))  # preflight + two robots + two literal bodies
        self.assertEqual(len(calls), followups.read_json(state_path)["http_get_attempt_count"])
        for code, original in originals.items():
            updated = followups.read_json(self.output / "records" / (code + ".json"))
            for key in ("investigation_status", "verification_level", "identity_status", "channels", "public_ir_emails", "conditions"):
                self.assertEqual(original[key], updated[key])
            self.assertTrue(updated["manual_review_required"])
            self.assertEqual("issuer_identity_discovery", updated["followup_review_pending"][-1]["purpose"])
            self.assertIs(False, updated["followup_review_pending"][-1]["identity_discovery_proof"]["current_issuer_reception_verified"])

    def stop_completed_identity_run(self, budget=False):
        originals = self.completed_identity_fixture()
        plan, calls = followups.build_plan(self.output, only_codes=["462A", "4651"]), []
        state_path = self.output / "completed-identity-stop.json"
        if state_path.exists(): state_path.unlink()

        def first(url, **kwargs):
            calls.append(url)
            return self.response(url, 200 if url == followups.PREFLIGHT or budget else 404 if url.endswith("/robots.txt") else 503,
                "新規上場" if url == followups.PREFLIGHT else "" if url.endswith("/robots.txt") else
                "IR <form><input type='email'><textarea name='question'></textarea></form>" if budget else
                "Invalid argument|remote address:envoy://cloudflare_https_tunnel/")

        clock, http = self.network(first)
        with clock, http:
            self.assertEqual(0 if budget else 2, followups.collect(self.output, state_path, plan, 3 if budget else 1000, 0.25))
        state = followups.read_json(state_path)
        self.assertEqual("get_budget_exhausted" if budget else "environment_stopped", state["status"])
        return originals, state_path, plan, calls

    def test_completed_identity_resume_uses_own_archive_and_keeps_unstarted_routes(self):
        for budget in (False, True):
            with self.subTest(budget=budget):
                originals, state_path, plan, calls = self.stop_completed_identity_run(budget)
                before, resumed_calls = followups.read_json(state_path), []
                lineage = before["identity_record_lineage"]["462A"]
                self.assertEqual(lineage["source_record_sha256"], followups.file_sha256(self.output / lineage["original_record_archive"]))

                def healthy(url, **kwargs):
                    resumed_calls.append(url)
                    return self.response(url, 404 if url.endswith("/robots.txt") else 200,
                        "新規上場" if url == followups.PREFLIGHT else "公開会社案内 IRお問い合わせ")

                clock, http = self.network(healthy)
                with clock, http, redirect_stdout(io.StringIO()):
                    self.assertEqual(0, followups.main(["--output", str(self.output), "--state", str(state_path),
                                                       "--only-codes", "462A", "4651", "--global-rps", "0.25"]))
                state = followups.read_json(state_path)
                self.assertEqual(("completed", [], 2), (state["status"], state["todo"], len(state["done"])))
                self.assertEqual(len(calls) + len(resumed_calls), state["http_get_attempt_count"])
                if budget: self.assertNotIn(plan["selected"][0]["url"], resumed_calls)
                for code in originals:
                    updated = followups.read_json(self.output / "records" / (code + ".json"))
                    self.assertEqual(originals[code]["identity_status"], updated["identity_status"])
                    self.assertEqual("unconfirmed", updated["investigation_status"])
                    self.assertTrue(updated["manual_review_required"])
                original_archive = state["identity_record_lineage"]["462A"]["original_record_archive"]
                self.assertEqual(lineage["original_record_archive"], original_archive)
                with patch.object(self.research.requests, "get", side_effect=AssertionError("completed GET prohibited")), redirect_stdout(io.StringIO()):
                    self.assertEqual(0, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", "462A", "4651"]))

    def test_completed_identity_resume_rejects_other_writers_sources_and_forged_urls(self):
        for damage in ("record", "source", "proposal", "audit", "archive", "old_state", "saved_url", "other_issuer"):
            with self.subTest(damage=damage):
                _, state_path, plan, _ = self.stop_completed_identity_run()
                state = followups.read_json(state_path)
                lineage = state["identity_record_lineage"]["462A"]
                if damage in {"record", "source", "proposal", "audit", "archive"}:
                    relative = ("records/462A.json" if damage == "record" else plan["selected"][0]["parent_snapshot"] if damage == "source" else
                        followups.COMPLETED_IDENTITY_PROPOSAL["path" if damage == "proposal" else "audit_path"] if damage in {"proposal", "audit"} else lineage["original_record_archive"])
                    data = followups.read_json(self.output / relative)
                    data["other_writer_note"] = "changed"
                    self.save(relative, data)
                elif damage == "old_state": state.pop("identity_record_lineage")
                elif damage == "saved_url": state["selected"][0]["url"] = "https://other-issuer.example/contact"
                else: state["selected"][0]["security_code"] = "999A"
                if damage in {"old_state", "saved_url", "other_issuer"}: self.research.write_json(state_path, state)
                record_before = (self.output / "records/462A.json").read_bytes()
                with patch.object(self.research.requests, "get", side_effect=AssertionError("resume GET prohibited")), redirect_stdout(io.StringIO()):
                    self.assertEqual(2, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", "462A", "4651"]))
                blocked = followups.read_json(state_path)
                self.assertEqual("identity_resume_proof_missing_stopped" if damage == "old_state" else "identity_source_changed_stopped", blocked["status"])
                self.assertEqual((state["done"], len(state["todo"])), (blocked["done"], len(blocked["todo"])))
                self.assertEqual(record_before, (self.output / "records/462A.json").read_bytes())

    def test_completed_identity_rechecks_completed_audit_after_preflight(self):
        originals, calls = self.completed_identity_fixture(), []
        plan = followups.build_plan(self.output, only_codes=["462A", "4651"])

        def preflight(url, **kwargs):
            calls.append(url)
            self.assertEqual(followups.PREFLIGHT, url)
            relative = followups.COMPLETED_IDENTITY_PROPOSAL["audit_path"]
            audit = followups.read_json(self.output / relative)
            audit["other_writer_note"] = "changed during preflight"
            self.save(relative, audit)
            return self.response(url, 200, "新規上場")

        clock, http = self.network(preflight)
        state_path = self.output / "audit-after-preflight.json"
        with clock, http:
            self.assertEqual(2, followups.collect(self.output, state_path, plan, 1000, 0.25))
        state = followups.read_json(state_path)
        self.assertEqual([followups.PREFLIGHT], calls)
        self.assertEqual(("identity_source_changed_stopped", 2, []), (state["status"], len(state["todo"]), state["done"]))
        for code, original in originals.items(): self.assertEqual(original, followups.read_json(self.output / "records" / (code + ".json")))

    def test_completed_identity_keeps_saved_access_and_post_action_rejections(self):
        for denial in ("http_403", "robots_disallow", "robots_unreachable", "post_action"):
            with self.subTest(denial=denial):
                self.completed_identity_fixture()
                route = followups.COMPLETED_IDENTITY_ROUTES["462A"]
                page = followups.read_json(self.output / route["parent_snapshot"])
                if denial == "post_action": page["forms"] = [{"action": route["target_url"], "method": "post"}]
                else:
                    page["robots"] = {"url": "https://corp.fundinno.com/robots.txt", "requested_url": "https://corp.fundinno.com/robots.txt",
                        "retrieved_at": "2026-10-11T00:10:00+00:00", "http_get_attempted": True,
                        "http_status": 403 if denial == "http_403" else 503 if denial == "robots_unreachable" else 200,
                        "text": "User-agent: *\nDisallow: /company/\n" if denial == "robots_disallow" else "unavailable"}
                self.save(route["parent_snapshot"], page)
                self.refreeze_completed_identity_fixture()
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                    self.assertEqual([], followups.build_plan(self.output, only_codes=["462A"])["selected"])

    def reviewed_ir_route_fixture(self, code="4046", with_generic=False):
        route = followups.REVIEWED_IR_ROUTES[code]
        record = self.fixture(code, links=[])
        reference = route["parent_snapshot"]
        links = [{"url": route["official_url"], "href": route["official_url"], "label": "会社案内"}
                 for _ in range(route["source_link_index"])]
        link = {"url": route["target_url"], "href": route["target_url"], "label": route["label"]}
        links.append(link)
        links.extend([{"url": route["official_url"] + "/form/individual", "href": "/form/individual", "label": "個人株主"},
                      {"url": route["official_url"] + "/form/other", "href": "/form/other", "label": "その他"},
                      {"url": "https://customer.example/form", "href": "https://customer.example/form", "label": "製品お問い合わせ"}])
        page = {"security_code": code, "requested_url": route["parent_url"], "url": route["parent_url"],
                "http_status": 200, "retrieved_at": "2026-10-11T00:00:00+00:00", "title": "お問い合わせ", "headings": [],
                "text": route["company_name"] + " " + route["section_quote"], "links": links, "forms": []}
        self.save(reference, page)
        record.update(company_name=route["company_name"], official_url=route["official_url"], contact_url=route["target_url"],
                      individual_access="restricted" if code == "4004" else "not_stated",
                      outreach_suitability="restricted" if code == "4004" else "unconfirmed",
                      discovery={"seed_company_name": route["company_name"], "official_url": route["official_url"]},
                      manual_review={"reviewer": "codex_audit_manufacturing", "reviewed_at": "2026-10-11T01:00:00+00:00"},
                      evidence=[{"snapshot": reference, "url": route["parent_url"], "retrieved_at": page["retrieved_at"],
                          "quote": route["quote"], "source_link_url": route["target_url"], "source_link_index": route["source_link_index"]}],
                      fetches=[{"snapshot": reference, "url": route["parent_url"], "http_status": 200}])
        if with_generic:
            ir_url = route["official_url"].rstrip("/") + "/ir/"
            generic_url = route["official_url"].rstrip("/") + "/contact/general/"
            generic_ref = self.save(f"evidence/{code}/generic-ir-parent.json", {
                "url": ir_url, "requested_url": ir_url, "http_status": 200, "title": "IR情報", "text": route["company_name"] + " IR情報 お問い合わせ",
                "retrieved_at": "2026-10-11T00:00:00+00:00", "headings": [], "forms": [],
                "links": [{"url": generic_url, "href": generic_url, "label": "お問い合わせ"}]})
            record["fetches"].append({"snapshot": generic_ref, "url": ir_url, "http_status": 200})
        self.save("records/" + code + ".json", record)
        record_sha = followups.file_sha256(self.output / "records" / (code + ".json"))
        source_sha = followups.file_sha256(self.output / reference)
        path = followups.REVIEWED_IR_AUDIT
        part = followups.read_json(self.output / path) if (self.output / path).exists() else {
            "reviewer": "codex_audit_manufacturing", "reviewed": [], "followup_candidates": []}
        part["reviewed"] = [r for r in part["reviewed"] if r["security_code"] != code]
        part["followup_candidates"] = [r for r in part["followup_candidates"] if r["security_code"] != code]
        part["reviewed"].append({"security_code": code, "company_name": record["company_name"], "saved": True,
            "reviewed_at": record["manual_review"]["reviewed_at"], "record_sha256_after_review": record_sha,
            "original_evidence_sha256": {reference: source_sha}})
        part["followup_candidates"].append({"security_code": code, "url": route["target_url"], "parent_url": route["parent_url"],
            "source_snapshot": reference, "source_link_index": route["source_link_index"], "source_link": link,
            "source_sha256": source_sha, "record_sha256_after_review": record_sha, "quote": route["quote"],
            "reviewer": "codex_audit_manufacturing", "ir_scope_verified": True, "method": "GET"})
        self.save(path, part)
        return record, page, reference, path

    def test_fixed_reviewed_ir_sections_select_only_their_actual_financial_targets(self):
        for code in ("4004", "4046"):
            self.reviewed_ir_route_fixture(code)
        plan = followups.build_plan(self.output)
        self.assertEqual(2, plan["selected_url_count"])
        for task in plan["selected"]:
            route = followups.REVIEWED_IR_ROUTES[task["security_code"]]
            self.assertEqual(route["target_url"], task["url"])
            self.assertEqual(1, task["priority"])
            self.assertTrue(task["explicit_ir_link"])
            self.assertEqual("ir_contact_followup", task["purpose"])
            self.assertNotIn("identity_discovery_proof", task)
            proof = task["reviewed_ir_route_proof"]
            self.assertTrue(proof["IR_purpose_verified"])
            self.assertFalse(proof["actual_form_fields_verified"])
            self.assertFalse(proof["current_issuer_reception_verified"])
            self.assertEqual(route["section_quote"], proof["section_quote"])
            self.assertEqual(followups.file_sha256(self.output / followups.REVIEWED_IR_AUDIT), proof["proposal_source_sha256"])

    def test_reviewed_ir_binding_requires_section_actual_href_review_and_frozen_hashes(self):
        for damage in ("source", "part_hash", "individual_url", "other_section", "reviewer", "record", "post", "unrelated_quote"):
            with self.subTest(damage=damage):
                record, page, ref, part_ref = self.reviewed_ir_route_fixture("4004")
                route = followups.REVIEWED_IR_ROUTES["4004"]
                part = followups.read_json(self.output / part_ref)
                row = next(r for r in part["reviewed"] if r["security_code"] == "4004")
                proposal = next(r for r in part["followup_candidates"] if r["security_code"] == "4004")
                if damage == "source":
                    page["text"] += " changed saved source"
                elif damage == "part_hash":
                    row["original_evidence_sha256"][ref] = "0" * 64
                elif damage == "individual_url":
                    target = route["target_url"].replace("typeId=ir", "typeId=individual")
                    page["links"][route["source_link_index"]].update(url=target, href=target)
                    proposal["url"] = target
                    record["contact_url"] = target
                    record["evidence"][0]["source_link_url"] = target
                elif damage == "other_section":
                    page["text"] = record["company_name"] + " その他 問い合わせフォーム"
                    record["evidence"][0]["quote"] = proposal["quote"] = "その他 問い合わせフォーム"
                elif damage == "reviewer":
                    record["manual_review"]["reviewer"] = "unrelated"
                elif damage == "record":
                    record["conditions"].append("independent writer")
                elif damage == "post":
                    proposal["method"] = "POST"
                else:
                    proposal["quote"] = "個人株主 問い合わせフォーム"
                self.save(ref, page)
                self.save("records/4004.json", record)
                self.save(part_ref, part)
                # Even updating hashes cannot turn another table row into IR.
                if damage in {"individual_url", "other_section"}:
                    row["record_sha256_after_review"] = proposal["record_sha256_after_review"] = followups.file_sha256(self.output / "records/4004.json")
                    row["original_evidence_sha256"][ref] = proposal["source_sha256"] = followups.file_sha256(self.output / ref)
                    proposal["source_link"] = page["links"][route["source_link_index"]]
                    self.save(part_ref, part)
                self.assertEqual([], followups.build_plan(self.output, only_codes=["4004"])["selected"])

    def stop_reviewed_ir_run_after_generic(self, budget_stop=False):
        self.reviewed_ir_route_fixture("4046", with_generic=True)
        plan = followups.build_plan(self.output, only_codes=["4046"])
        # Saved queues may legitimately put the ordinary same-issuer page first.
        plan["selected"].sort(key=lambda t: "reviewed_ir_route_proof" in t)
        self.assertEqual(2, len(plan["selected"]))
        generic, frozen = plan["selected"]
        calls, state_path = [], self.output / "reviewed-ir-run.json"
        if state_path.exists():
            state_path.unlink()

        def reply(url, **kwargs):
            calls.append(url)
            if url == followups.PREFLIGHT:
                return self.response(url, 200, "新規上場")
            if url.endswith("/robots.txt"):
                return self.response(url, 404, "")
            if url == generic["url"]:
                return self.response(url, 200, "公開お問い合わせ")
            return self.response(url, 503, "Invalid argument|remote address:envoy://cloudflare_https_tunnel/")

        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(0 if budget_stop else 2, followups.collect(self.output, state_path, plan, 3 if budget_stop else 1000, 0.25))
        stopped = followups.read_json(state_path)
        self.assertEqual(1, len(stopped["done"]))
        self.assertEqual([frozen], stopped["todo"])
        self.assertEqual([], followups.build_plan(self.output, only_codes=["4046"])["selected"])
        return state_path, plan, calls

    def test_reviewed_ir_resume_after_prior_generic_append_retains_common_or_budget_pending(self):
        for budget_stop in (False, True):
            with self.subTest(budget_stop=budget_stop):
                path, plan, calls = self.stop_reviewed_ir_run_after_generic(budget_stop)
                stopped = followups.read_json(path)
                lineage = stopped["reviewed_ir_record_lineage"]["4046"]
                self.assertEqual(lineage["source_record_sha256"], followups.file_sha256(self.output / lineage["original_record_archive"]))
                self.assertEqual(lineage["expected_record_sha256"], followups.file_sha256(self.output / "records/4046.json"))
                resumed_calls = []

                def healthy(url, **kwargs):
                    resumed_calls.append(url)
                    return self.response(url, 404 if url.endswith("/robots.txt") else 200,
                                         "新規上場" if url == followups.PREFLIGHT else "IRお問い合わせ")

                clock, http = self.network(healthy)
                with clock, http, redirect_stdout(io.StringIO()):
                    self.assertEqual(0, followups.main(["--output", str(self.output), "--state", str(path), "--only-codes", "4046"]))
                finished = followups.read_json(path)
                self.assertEqual("completed", finished["status"])
                self.assertEqual([], finished["todo"])
                self.assertEqual(2, len(finished["done"]))
                self.assertNotIn(plan["selected"][0]["url"], resumed_calls)
                self.assertEqual(1, resumed_calls.count(plan["selected"][1]["url"]))
                self.assertEqual(len(calls) + len(resumed_calls), finished["http_get_attempt_count"])
                updated = followups.read_json(self.output / "records/4046.json")
                self.assertEqual("provisional", updated["investigation_status"])
                self.assertTrue(updated["manual_review_required"])
                with patch.object(self.research.requests, "get", side_effect=AssertionError("completed URL repeated")), redirect_stdout(io.StringIO()):
                    self.assertEqual(0, followups.main(["--output", str(self.output), "--state", str(path), "--only-codes", "4046"]))

    def test_reviewed_ir_resume_rejects_external_changes_missing_lineage_and_forged_target_before_get(self):
        for damage in ("record", "source", "part", "archive", "old_state", "saved_url"):
            with self.subTest(damage=damage):
                path, plan, _ = self.stop_reviewed_ir_run_after_generic()
                stopped = followups.read_json(path)
                lineage = stopped["reviewed_ir_record_lineage"]["4046"]
                if damage == "record":
                    data = followups.read_json(self.output / "records/4046.json")
                    data["conditions"].append("different writer")
                    self.save("records/4046.json", data)
                elif damage == "source":
                    ref = plan["selected"][1]["parent_snapshot"]
                    data = followups.read_json(self.output / ref)
                    data["text"] += " changed"
                    self.save(ref, data)
                elif damage == "part":
                    data = followups.read_json(self.output / followups.REVIEWED_IR_AUDIT)
                    data["later_note"] = "independent part update"
                    self.save(followups.REVIEWED_IR_AUDIT, data)
                elif damage == "archive":
                    data = followups.read_json(self.output / lineage["original_record_archive"])
                    data["conditions"].append("archive changed")
                    self.save(lineage["original_record_archive"], data)
                elif damage == "old_state":
                    stopped.pop("reviewed_ir_record_lineage")
                    self.research.write_json(path, stopped)
                else:
                    stopped["selected"][1]["url"] = "https://customer.example/form"
                    self.research.write_json(path, stopped)
                before = (self.output / "records/4046.json").read_bytes()
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET before frozen proof verification")), redirect_stdout(io.StringIO()):
                    self.assertEqual(2, followups.main(["--output", str(self.output), "--state", str(path), "--only-codes", "4046"]))
                blocked = followups.read_json(path)
                self.assertEqual("reviewed_ir_resume_proof_missing_stopped" if damage == "old_state" else "reviewed_ir_source_changed_stopped", blocked["status"])
                self.assertEqual(stopped["done"], blocked["done"])
                self.assertEqual(1, len(blocked["todo"]))
                self.assertEqual(before, (self.output / "records/4046.json").read_bytes())

    def test_parser_refresh_is_two_exact_once_only_gets_with_preserved_sources(self):
        self.parser_refresh_fixture()
        source_bytes = {str(path): path.read_bytes() for path in (self.output / "evidence").rglob("*.json")}
        plan = followups.build_parser_refresh_plan(self.output)
        self.assertEqual([], followups.build_plan(self.output)["selected"])
        self.assertEqual(2, plan["selected_url_count"])
        self.assertEqual(0, plan["claimed_once_count"])
        with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")), \
                patch.object(self.research, "write_json", side_effect=AssertionError("write prohibited")), redirect_stdout(io.StringIO()):
            self.assertEqual(0, followups.main(["--output", str(self.output), "--parser-refresh", "--plan-only"]))
        calls = []

        def reply(url, **kwargs):
            calls.append(url)
            return self.response(url, 404 if url.endswith("robots.txt") else 200,
                                 "新規上場" if "jpx.co.jp" in url else "新しい公開ページ")

        state_path = self.output / followups.PARSER_REFRESH_STATE
        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(0, followups.collect(self.output, state_path, plan, 12, 0.25))
        state = followups.read_json(state_path)
        self.assertEqual(5, state["http_get_attempt_count"])
        self.assertEqual(5, state["reserved_get_count"])
        self.assertEqual(2, len(state["refresh_claims"]))
        self.assertEqual([], state["todo"])
        for target in followups.PARSER_REFRESH_TARGETS.values():
            self.assertEqual(1, calls.count(target))
        self.assertEqual(source_bytes, {path: Path(path).read_bytes() for path in source_bytes})
        for code in followups.PARSER_REFRESH_TARGETS:
            record = followups.read_json(self.output / "records" / (code + ".json"))
            self.assertEqual("provisional", record["investigation_status"])
            self.assertTrue(record["manual_review_required"])
            self.assertIn("parser_refresh_proof", record["fetches"][-1])
            self.assertTrue(record["previous_attempts"])
        records_before = {path: path.read_bytes() for path in (self.output / "records").glob("*.json")}
        with patch.object(self.research.requests, "get", side_effect=AssertionError("duplicate GET prohibited")):
            self.assertEqual(0, followups.collect(self.output, state_path,
                                                 followups.build_parser_refresh_plan(self.output), 12, 0.25))
        self.assertEqual(records_before, {path: path.read_bytes() for path in records_before})

    def test_parser_refresh_rejects_unpreserved_sources_records_or_arbitrary_targets(self):
        for damaged in ("target", "snapshot", "record"):
            with self.subTest(damaged=damaged):
                self.parser_refresh_fixture()
                if damaged == "target":
                    audit = followups.read_json(self.output / followups.PARSER_REFRESH_AUDIT)
                    audit["refreshes"][0]["target_url"] = "https://arbitrary.example/ir/"
                    self.save(followups.PARSER_REFRESH_AUDIT, audit)
                elif damaged == "snapshot":
                    self.save("evidence/2752/old-target.json", {"http_status": 200, "text": "changed"})
                else:
                    record = followups.read_json(self.output / "records/2752.json")
                    record["manual_review"]["notes"] = "changed after preparation"
                    self.save("records/2752.json", record)
                before = {path: path.read_bytes() for path in self.output.rglob("*") if path.is_file()}
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")), \
                        patch.object(self.research, "write_json", side_effect=AssertionError("write prohibited")):
                    with self.assertRaises(ValueError):
                        followups.build_parser_refresh_plan(self.output)
                self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_parser_refresh_claim_survives_interruption_without_repeating_url(self):
        self.parser_refresh_fixture()
        calls = []

        def reply(url, **kwargs):
            calls.append(url)
            if url == followups.PARSER_REFRESH_TARGETS["2752"]:
                raise RuntimeError("mock interruption after dispatch")
            return self.response(url, 404 if url.endswith("robots.txt") else 200, "新規上場")

        state_path = self.output / followups.PARSER_REFRESH_STATE
        clock, http = self.network(reply)
        with clock, http, self.assertRaises(RuntimeError):
            followups.collect(self.output, state_path, followups.build_parser_refresh_plan(self.output), 12, 0.25)
        state = followups.read_json(state_path)
        self.assertEqual("refresh_interrupted", state["status"])
        self.assertEqual(3, state["reserved_get_count"])
        self.assertEqual(3, state["http_get_attempt_count"])
        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(0, followups.collect(self.output, state_path,
                                                 followups.build_parser_refresh_plan(self.output), 12, 0.25))
        self.assertEqual(1, calls.count(followups.PARSER_REFRESH_TARGETS["2752"]))
        self.assertEqual(1, calls.count(followups.PARSER_REFRESH_TARGETS["2784"]))
        self.assertEqual(6, followups.read_json(state_path)["reserved_get_count"])

    def test_parser_refresh_reservations_enforce_get_cap_before_dispatch(self):
        self.parser_refresh_fixture()
        calls = []

        def reply(url, **kwargs):
            calls.append(url)
            return self.response(url, 404 if url.endswith("robots.txt") else 200, "新規上場")

        state_path = self.output / followups.PARSER_REFRESH_STATE
        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(0, followups.collect(self.output, state_path,
                                                 followups.build_parser_refresh_plan(self.output), 4, 0.25))
        state = followups.read_json(state_path)
        self.assertEqual(4, len(calls))
        self.assertEqual(4, state["http_get_attempt_count"])
        self.assertEqual(4, state["reserved_get_count"])
        self.assertEqual(1, calls.count(followups.PARSER_REFRESH_TARGETS["2752"]))
        self.assertNotIn(followups.PARSER_REFRESH_TARGETS["2784"], calls)
        self.assertEqual("get_budget_exhausted", state["status"])
        record = followups.read_json(self.output / "records/2784.json")
        self.assertFalse(record["manual_review_required"])
        with patch.object(self.research.requests, "get", side_effect=AssertionError("claimed URL cannot be rerun")):
            self.assertEqual(0, followups.collect(self.output, state_path,
                                                 followups.build_parser_refresh_plan(self.output), 12, 0.25))

    def test_selection_requires_real_ir_links_and_allows_explicit_external_form(self):
        root = "https://issuer500a.example/"
        links = [{"url": root + "contact", "label": "お問い合わせ"},
                 {"url": root + "ir/contact", "label": "IRお問い合わせ"},
                 {"url": "https://public.forms.example/inquiry", "label": "IRお問い合わせフォーム"},
                 {"url": root + "ir/contact?sid=secret", "label": "IRお問い合わせ"},
                 {"url": root + "ir/financial_information/summary", "label": "財務情報"},
                 {"url": root + "ir/performance/summary", "label": "業績情報"},
                 {"url": root + "ir/recruit", "label": "採用お問い合わせ"},
                 {"url": "https://www.googletagmanager.com/ns.html?id=GTM-X", "label": "IRお問い合わせ"},
                 {"url": "http://127.0.0.1/contact", "label": "IRお問い合わせ"}]
        record = self.fixture(links=links)
        reference = self.save("evidence/500A/ir.json", {"url": root + "ir/", "http_status": 200,
            "title": "投資家情報", "text": "投資家情報", "links": [
                {"url": root + "general-form", "label": "お問い合わせ"},
                {"url": "https://customer.other.example/contact", "label": "お問い合わせ"}]})
        record["fetches"].append({"url": root + "ir/", "snapshot": reference, "http_status": 200})
        self.save("records/500A.json", record)
        plan = followups.build_plan(self.output)
        self.assertEqual({root + "ir/contact", root + "general-form", "https://public.forms.example/inquiry"},
                         {task["url"] for task in plan["selected"]})
        self.assertEqual(3, plan["selected_url_count"])
        self.assertTrue(all(task["parent_snapshot_sha256"] for task in plan["selected"]))
        self.assertEqual([], followups.company_candidates(self.output, {**record, "investigation_status": "confirmed"}, [])[0])

    def literal_robots_fixture(self, target="https://inquiry.daifuku.com/others_jp"):
        # Exact saved 6383 policy; the synthetic issuer parent supplies a bound IR link.
        rules = ("User-agent: *\nDisallow: /\nAllow: /products_jp\nAllow: /after_salesservices_jp\n"
                 "Allow: /others_jp\nAllow: /supplier\nAllow: /training\nAllow: /products_en\n"
                 "Allow: /after_salesservices_en\nAllow: /others_en\nAllow: /newsletter_input\n"
                 "Allow: /member/login\nAllow: /logimat_2024")
        record = self.fixture("6383", links=[{"url": target, "href": target, "label": "IRお問い合わせ"}])
        robot = {"requested_url": "https://inquiry.daifuku.com/robots.txt", "url": "https://inquiry.daifuku.com/robots.txt",
                 "retrieved_at": "2026-10-11T17:35:34.132724+00:00", "http_status": 200, "text": rules}
        stopped_ref = self.save("evidence/6383/stopped.json", {"requested_url": target,
            "retrieved_at": "2026-10-11T17:35:48.960250+00:00", "error": "robots_disallowed",
            "http_get_attempted": False, "submitted": False, "robots": robot})
        record["fetches"].append({"url": target, "snapshot": stopped_ref, "error": "robots_disallowed"})
        self.save("records/6383.json", record)
        return record, robot, stopped_ref

    def test_actual_6383_saved_literal_block_is_requeued_with_immutable_proof_get_zero(self):
        record, _, stopped = self.literal_robots_fixture()
        before = {str(p): p.read_bytes() for p in self.output.rglob("*.json")}
        with patch.object(self.research.requests, "get", side_effect=AssertionError("planning must not GET")):
            plan = followups.build_plan(self.output)
        self.assertEqual(["https://inquiry.daifuku.com/others_jp"], [t["url"] for t in plan["selected"]])
        proof = plan["selected"][0]["robots_literal_allow_correction"]
        self.assertEqual([stopped], proof["historical_stop_snapshots"])
        self.assertEqual(followups.file_sha256(self.output / stopped), proof["source_snapshot_sha256"][stopped])
        self.assertFalse(proof["financial_ir_reception_verified"])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.output.rglob("*.json")})
        self.assertEqual("provisional", record["investigation_status"])

    def test_saved_literal_correction_does_not_clear_genuine_or_unknown_old_stop(self):
        for mode in ("genuine_disallow", "missing_robots", "missing_body_flag", "old_robots_404", "missing_time"):
            with self.subTest(mode=mode):
                record, robot, stopped = self.literal_robots_fixture()
                event = followups.read_json(self.output / stopped)
                if mode == "genuine_disallow": event["robots"]["text"] = "User-agent: *\nDisallow: /"
                elif mode == "missing_robots": event.pop("robots")
                elif mode == "missing_body_flag": event.pop("http_get_attempted")
                elif mode == "old_robots_404": event["robots"]["http_status"] = 404
                else: event["robots"].pop("retrieved_at")
                self.save(stopped, event)
                latest = self.save("evidence/6383/new-policy.json", {"url": record["official_url"] + "ir/status", "http_status": 200,
                    "text": "テスト会社", "robots": {**robot, "retrieved_at": "2026-10-11T18:00:00+00:00"}})
                record["fetches"].append({"snapshot": latest, "url": record["official_url"] + "ir/status", "http_status": 200})
                self.save("records/6383.json", record)
                self.assertEqual([], followups.build_plan(self.output)["selected"])

    def test_saved_literal_correction_requires_latest_same_origin_success_and_specific_rule(self):
        modes = [401, 403, 429, 503, 302, None, "transport", "only_allow", "tie", "wildcard", "dollar",
                 "specific_agent", "naive_time", "narrower_disallow", "other_http", "other_host"]
        for mode in modes:
            with self.subTest(mode=mode):
                target = "https://inquiry.daifuku.com/others_jp/private" if mode == "narrower_disallow" else "https://inquiry.daifuku.com/others_jp"
                record, robot, stopped = self.literal_robots_fixture(target)
                latest_robot = {**robot, "retrieved_at": "2026-10-11T18:00:00+00:00"}
                if mode in (401,403,429,503,302,None): latest_robot["http_status"] = mode
                elif mode == "transport": latest_robot.update(error="ConnectionError", http_status=None)
                elif mode == "only_allow": latest_robot["text"] = "User-agent: *\nAllow: /others_jp"
                elif mode == "tie": latest_robot["text"] = "User-agent: *\nDisallow: /others_jp\nAllow: /others_jp"
                elif mode in ("wildcard","dollar"): latest_robot["text"] += "\nDisallow: /else" + ("*" if mode == "wildcard" else "$")
                elif mode == "specific_agent": latest_robot["text"] = "User-agent: ir-agent\nDisallow: /\n\n" + robot["text"]
                elif mode == "naive_time": latest_robot["retrieved_at"] = "2026-10-11T18:00:00"
                elif mode == "narrower_disallow": latest_robot["text"] += "\nDisallow: /others_jp/private"
                else:
                    # A different origin's newer Allow cannot clear a true block here.
                    old = followups.read_json(self.output / stopped);old["robots"]["text"] = "User-agent: *\nDisallow: /";self.save(stopped,old)
                    origin = "http://inquiry.daifuku.com" if mode == "other_http" else "https://www.inquiry.daifuku.com"
                    latest_robot.update(requested_url=origin+"/robots.txt",url=origin+"/robots.txt")
                latest = self.save("evidence/6383/new-policy.json", {"url": record["official_url"] + "ir/status", "http_status": 200,
                    "text": "テスト会社", "robots": latest_robot})
                record["fetches"].append({"snapshot": latest, "url": record["official_url"] + "ir/status", "http_status": 200})
                self.save("records/6383.json", record)
                self.assertEqual([], followups.build_plan(self.output)["selected"])

    def test_literal_allow_correction_retains_denied_post_unbound_and_fetched_stops(self):
        for mode in ("denied_host", "post_action", "unbound", "product_link", "already_fetched"):
            with self.subTest(mode=mode):
                record, _, _ = self.literal_robots_fixture();parent_ref=record["fetches"][0]["snapshot"]
                parent=followups.read_json(self.output / parent_ref);target="https://inquiry.daifuku.com/others_jp"
                if mode == "post_action": parent["forms"]=[{"method":"post","action":target}]
                elif mode == "unbound": parent["links"]=[]
                elif mode == "product_link": parent["links"][0]["label"]="製品のお問い合わせ"
                else:
                    ref=self.save("evidence/6383/extra.json",{"requested_url":target if mode=="already_fetched" else target+"/other",
                        "url":target if mode=="already_fetched" else target+"/other","http_status":200 if mode=="already_fetched" else 403,"text":""})
                    record["fetches"].append({"snapshot":ref,"url":target if mode=="already_fetched" else target+"/other","http_status":200 if mode=="already_fetched" else 403})
                self.save(parent_ref,parent);self.save("records/6383.json",record)
                self.assertEqual([],followups.build_plan(self.output)["selected"])

    def test_requeued_literal_block_rechecks_fresh_robots_before_body(self):
        record, _, stopped = self.literal_robots_fixture()
        old_bytes = (self.output / stopped).read_bytes()
        plan = followups.build_plan(self.output);calls=[]
        def reply(url, **kwargs):
            calls.append(url)
            if url == followups.PREFLIGHT: return self.response(url,200,"新規上場")
            self.assertEqual("https://inquiry.daifuku.com/robots.txt",url,"fresh denial must prevent target body GET")
            return self.response(url,200,"User-agent: *\nDisallow: /", {"Content-Type":"text/plain; charset=utf-8"})
        state=self.output/"run.json";clock,http=self.network(reply)
        with clock,http:
            self.assertEqual(0,followups.collect(self.output,state,plan,6,0.25))
        self.assertEqual([followups.PREFLIGHT,"https://inquiry.daifuku.com/robots.txt"],calls)
        self.assertEqual(old_bytes,(self.output/stopped).read_bytes())
        current=followups.read_json(self.output/"records/6383.json")
        self.assertEqual("robots_disallowed",current["fetches"][-1]["error"])
        self.assertEqual(record["investigation_status"],current["investigation_status"])

    def test_saved_denials_robots_post_actions_and_retrieved_urls_are_not_queued(self):
        root = "https://issuer500a.example/"
        record = self.fixture(links=[{"url": root + path, "label": "IRお問い合わせ"}
                                    for path in ("ir/blocked", "ir/old", "ir/post")] +
                                   [{"url": "https://external.example/form", "label": "IRお問い合わせ"}])
        page = followups.read_json(self.output / "evidence/500A/root.json")
        page["forms"] = [{"method": "post", "action": root + "ir/post"}]
        page["robots"] = {"url": root + "robots.txt", "http_status": 200,
                          "text": "User-agent: *\nDisallow: /ir/blocked\n"}
        self.save("evidence/500A/root.json", page)
        for name, url, status in (("old", root + "ir/old", 200), ("denied", "https://external.example/other", 403)):
            snapshot = self.save(f"evidence/500A/{name}.json", {"url": url, "http_status": status, "text": ""})
            record["fetches"].append({"url": url, "snapshot": snapshot, "http_status": status})
        self.save("records/500A.json", record)
        plan = followups.build_plan(self.output)
        self.assertEqual([], plan["selected"])
        self.assertEqual(2, plan["rejected_counts"]["saved_access_denial"])
        self.assertEqual(1, plan["rejected_counts"]["post_action"])

    def test_manual_proposals_do_not_authorize_unlinked_urls(self):
        record = self.fixture()
        root = record["official_url"]
        self.save("parts/adaptive-followup-test.json", {"followups": [
            {"security_code": "500A", "url": root + "ir/contact", "parent_url": root,
             "parent_snapshot": "evidence/500A/root.json", "quote": "IRお問い合わせ", "method": "GET"},
            {"security_code": "500A", "url": "https://arbitrary.example/form", "parent_url": root,
             "parent_snapshot": "evidence/500A/root.json", "quote": "IRお問い合わせ", "method": "GET"}]})
        plan = followups.build_plan(self.output)
        self.assertEqual([root + "ir/contact"], [task["url"] for task in plan["selected"]])
        self.assertIn("manual_proposal_source", plan["selected"][0])

    def test_audit_referenced_old_form_prevents_duplicate_redirected_get(self):
        record = self.fixture()
        target = record["official_url"] + "ir/contact"
        snapshot = self.save("evidence/500A/old-form.json", {"requested_url": target,
            "url": "https://linked.form.example/waiting", "http_status": 200, "text": "IR Contact"})
        self.save("parts/adaptive-followup-test.json", {"records": [{"security_code": "500A",
            "evidence": [{"snapshot": snapshot, "quote": "IR Contact"}], "additional_get_candidates": []}]})
        self.assertEqual([], followups.build_plan(self.output)["selected"])

    def test_latest_robots_failure_is_temporary_and_does_not_count_body_as_fetched(self):
        record = self.fixture()
        root = record["official_url"]
        target = root + "ir/contact"
        stopped = self.save("evidence/500A/robots-stopped.json", {
            "requested_url": target, "retrieved_at": "2026-10-11T01:00:00+00:00",
            "error": "robots_unreachable_stopped", "http_get_attempted": False,
            "robots": {"requested_url": root + "robots.txt", "retrieved_at": "2026-10-11T01:00:00+00:00",
                       "http_status": 503, "text": "temporarily unavailable", "http_get_attempted": True}})
        record["fetches"].append({"snapshot": stopped, "url": target, "error": "robots_unreachable_stopped"})
        self.save("records/500A.json", record)
        plan = followups.build_plan(self.output)
        self.assertEqual([], plan["selected"])
        self.assertEqual(1, plan["rejected_counts"]["saved_robots_unreachable_current_route_unconfirmed"])
        self.assertNotIn("already_fetched", plan["rejected_counts"])
        # A newer result on HTTP or www does not clear this HTTPS origin's gap.
        for other_root in (root.replace("https://", "http://"), root.replace("https://", "https://www.")):
            other = self.save("evidence/500A/other-origin.json", {"requested_url": other_root + "status",
                "url": other_root + "status", "http_status": 200, "text": "テスト会社", "robots": {
                    "requested_url": other_root + "robots.txt", "retrieved_at": "2026-10-11T02:00:00+00:00",
                    "http_status": 200, "text": ""}})
            self.save("records/500A.json", {**record, "fetches": [*record["fetches"], {"snapshot": other, "url": other_root + "status"}]})
            self.assertEqual([], followups.build_plan(self.output)["selected"])
        for status in (200, 404, 410):
            recovered = self.save("evidence/500A/recovered.json", {"requested_url": root + "status", "url": root + "status",
                "http_status": 200, "text": "テスト会社", "robots": {"requested_url": root + "robots.txt",
                "retrieved_at": "2026-10-11T02:00:00+00:00", "http_status": status, "text": ""}})
            self.save("records/500A.json", {**record, "fetches": [*record["fetches"], {"snapshot": recovered, "url": root + "status"}]})
            self.assertEqual([target], [task["url"] for task in followups.build_plan(self.output)["selected"]])
        # A fresh exception with no HTTP status is also a route gap, not a denial.
        page = followups.read_json(self.output / recovered)
        page["robots"].update(error="ConnectionError", http_status=None)
        self.save(recovered, page)
        self.assertEqual([], followups.build_plan(self.output)["selected"])

    def test_old_audit_glob_reads_only_proposals_that_match_actual_ir_source(self):
        record = self.fixture(links=[])
        root = record["official_url"]
        path = "evidence/500A/root.json"
        page = followups.read_json(self.output / path)
        page["links"] = [{"url": root + "ir/", "label": "IR情報"},
                         {"url": root + "contact/", "label": "お問い合わせ"}]
        self.save(path, page)
        self.save("parts/adaptive-old-audit-12.json", {"reviews": [{"security_code": "500A", "todos": [
            {"url": root + "ir/", "parent_snapshot": path, "parent_url": root, "quote": "IR情報"},
            {"url": root + "contact/", "parent_snapshot": path, "parent_url": root, "quote": "お問い合わせ"},
            {"url": "https://arbitrary.example/ir/", "parent_snapshot": path, "parent_url": root, "quote": "IR情報"}]}]})
        plan = followups.build_plan(self.output)
        self.assertEqual([root + "ir/"], [task["url"] for task in plan["selected"]])
        self.assertEqual("parts/adaptive-old-audit-12.json", plan["selected"][0]["manual_proposal_source"])

    def test_new_audit_ir_discovery_requires_real_link_and_observed_redirect_identity(self):
        record = self.fixture("291A", links=[])
        destination = "https://migrated.example/corp/"
        path = "evidence/291A/root.json"
        page = followups.read_json(self.output / path)
        page.update(url=destination, redirects=[{"requested_url": record["official_url"], "http_status": 301,
                    "redirect_target": destination}], links=[
                        {"url": destination + "ir", "label": "IR情報"},
                        {"url": destination + "contact", "label": "お問い合わせ"}])
        self.save(path, page)
        self.save("parts/adaptive-audit-new.json", {"reviews": [{"security_code": "291A", "todos": [
            {"url": destination + "ir", "parent_url": destination, "parent_snapshot": path, "quote": "IR情報"},
            {"url": destination + "contact", "parent_url": destination, "parent_snapshot": path, "quote": "お問い合わせ"},
            {"url": "https://arbitrary.example/ir", "parent_url": destination, "parent_snapshot": path, "quote": "IR情報"}]}]})
        plan = followups.build_plan(self.output)
        self.assertEqual([destination + "ir"], [task["url"] for task in plan["selected"]])
        self.assertEqual("official_ir_discovery_link_not_verified_contact", plan["selected"][0]["association_basis"])
        self.assertFalse(plan["selected"][0]["explicit_ir_link"])
        page["text"] = "別の会社 IR情報"
        self.save(path, page)
        self.assertEqual([], followups.build_plan(self.output)["selected"])

    def test_audit_exact_ir_section_binds_generic_form_without_trusting_nav_or_product(self):
        record = self.fixture("2935", links=[])
        parent = record["official_url"] + "contact/"
        target = parent + "form/"
        quote = "IRに関するお問い合わせ 04-0000-0000 お問い合わせフォーム 商品に関するお問い合わせ"
        path = self.save("evidence/2935/contact.json", {"url": parent, "http_status": 200,
            "title": "お問い合わせ", "text": "テスト会社 " + quote,
            "links": [{"url": target, "label": "お問い合わせフォーム"},
                      {"url": "https://products.example/form", "label": "商品のお問い合わせ"}]})
        evidence = {"snapshot": path, "url": parent, "quote": quote, "source_link_url": target}
        audit = {"reviews": [{"security_code": "2935", "new_evidence": [evidence], "todos": [
            {"url": target, "parent_url": parent, "parent_snapshot": path, "quote": "お問い合わせフォーム"}]}]}
        self.save("parts/adaptive-audit-new.json", audit)
        plan = followups.build_plan(self.output)
        self.assertEqual([target], [task["url"] for task in plan["selected"]])
        self.assertEqual(quote, plan["selected"][0]["binding_evidence"]["quote"])
        for negative in ("IR情報 お問い合わせフォーム", "IRに関するお問い合わせは電話のみ 商品に関するお問い合わせフォーム"):
            page = followups.read_json(self.output / path)
            page["text"] = negative
            self.save(path, page)
            evidence["quote"] = negative
            self.save("parts/adaptive-audit-new.json", audit)
            self.assertEqual([], followups.build_plan(self.output)["selected"])
        evidence["quote"] = quote  # An invented quote is rejected too.
        self.save("parts/adaptive-audit-new.json", audit)
        self.assertEqual([], followups.build_plan(self.output)["selected"])

    def test_faq_exact_ir_link_carries_scope_to_only_public_iframe_on_generic_page(self):
        record = self.fixture("2923", links=[])
        root = record["official_url"]
        faq = self.save("evidence/2923/faq.json", {"url": root + "ir/faq/", "http_status": 200,
            "title": "IR よくあるご質問", "text": "IRに関するお問い合わせはこちらから",
            "links": [{"url": root + "contact/general", "label": "IRに関するお問い合わせはこちらから"}]})
        external = "https://forms.example/public/opaque?iframe=true"
        generic = self.save("evidence/2923/generic.json", {"url": root + "contact/general", "http_status": 200,
            "title": "お問い合わせフォーム", "text": "お問い合わせフォーム",
            "links": [{"url": external, "label": "embedded frame"},
                      {"url": "https://www.googletagmanager.com/ns.html?id=GTM-X", "label": "embedded frame"}]})
        for snapshot in (faq, generic):
            record["fetches"].append({"snapshot": snapshot, "url": followups.read_json(self.output / snapshot)["url"], "http_status": 200})
        self.save("records/2923.json", record)
        self.save("parts/adaptive-audit-new.json", {"todos": [{"security_code": "2923", "url": external,
            "parent_snapshot": generic, "parent_url": root + "contact/general", "quote": "embedded frame"}]})
        plan = followups.build_plan(self.output)
        self.assertEqual([external], [task["url"] for task in plan["selected"]])
        self.assertEqual(faq, plan["selected"][0]["ir_scope_evidence"][0]["parent_snapshot"])
        # A generic contact in an IR navbar does not establish this association.
        faq_page = followups.read_json(self.output / faq)
        faq_page.update(title="IR情報", text="IR情報 お問い合わせ", links=[{"url": root + "contact/general", "label": "お問い合わせ"}])
        self.save(faq, faq_page)
        self.assertEqual([], followups.build_plan(self.output)["selected"])
        faq_page["links"][0]["label"] = "IRに関するお問い合わせはこちらから"
        self.save(faq, faq_page)
        generic_page = followups.read_json(self.output / generic)
        generic_page["links"].append({"url": "https://other.forms.example/public/two", "label": "embedded frame"})
        self.save(generic, generic_page)
        self.assertEqual([], followups.build_plan(self.output)["selected"])

    def test_weak_result_keeps_good_record_and_new_page_only_requests_review(self):
        original = self.fixture()
        task = followups.build_plan(self.output)["selected"][0]
        followups.append_observation(self.output, task, {"http_status": 403, "url": task["url"]}, "evidence/failed.json", 1)
        failed = followups.read_json(self.output / "records/500A.json")
        for field in ("investigation_status", "verification_level", "evidence", "conditions", "limitations", "manual_review"):
            self.assertEqual(original[field], failed[field])
        self.assertFalse(failed["manual_review_required"])
        followups.append_observation(self.output, task, {"http_status": 200, "url": task["url"], "text": "IRフォーム"}, "evidence/new.json", 1)
        updated = followups.read_json(self.output / "records/500A.json")
        self.assertEqual("provisional", updated["investigation_status"])
        self.assertTrue(updated["manual_review_required"])
        self.assertEqual([original["manual_review"]], updated["previous_manual_review"])
        self.assertEqual(original["evidence"], updated["evidence"])
        archived = followups.read_json(self.output / failed["previous_attempts"][0])
        self.assertEqual(original, archived)

    def test_followup_recounts_saved_success_bodies_for_zero_or_missing_scalar(self):
        for scalar in (None, 0):
            with self.subTest(previous_scalar=scalar):
                record = self.fixture()
                task = followups.build_plan(self.output)["selected"][0]
                if scalar is not None:
                    record["successful_official_page_count"] = scalar
                    self.save("records/500A.json", record)
                source_bytes = (self.output / "evidence/500A/root.json").read_bytes()
                page = {"requested_url": task["url"], "url": task["url"], "http_status": 200,
                        "http_get_attempted": True, "text": "新しい質問フォーム本文"}
                snapshot = self.save("evidence/500A/followup.json", page)
                followups.append_observation(self.output, task, page, snapshot, 1)
                updated = followups.read_json(self.output / "records/500A.json")
                self.assertEqual(2, updated["successful_official_page_count"])
                self.assertTrue(updated["manual_review_required"])
                self.assertTrue(updated["followup_review_pending"])
                self.assertEqual(source_bytes, (self.output / "evidence/500A/root.json").read_bytes())
                self.assertEqual(record, followups.read_json(self.output / updated["previous_attempts"][-1]))
                # Duplicate references to the same observation do not add bodies.
                updated["fetches"].append(dict(updated["fetches"][-1]))
                self.assertEqual(2, followups.successful_saved_body_count(self.output, updated, snapshot, page))

    def test_empty_shell_robots_and_local_stops_do_not_increase_success_count(self):
        invalid_pages = [
            {"http_status": 200, "text": ""},
            {"http_status": 200, "text": " \n\t"},
            {"http_status": 200, "text": "質問フォーム", "error": "LookupError"},
            {"http_status": 200, "text": "User-agent: *", "url": "https://issuer500a.example/robots.txt"},
            {"http_status": 200, "text": "本文", "http_get_attempted": False},
            {"error": "robots_unreachable_stopped", "http_get_attempted": False,
             "robots": {"http_status": 200, "text": "User-agent: *", "http_get_attempted": True}},
        ]
        for page in invalid_pages:
            with self.subTest(page=page):
                record = self.fixture()
                task = followups.build_plan(self.output)["selected"][0]
                record["successful_official_page_count"] = 1
                self.save("records/500A.json", record)
                followups.append_observation(self.output, task, page, "evidence/500A/empty.json", 1)
                updated = followups.read_json(self.output / "records/500A.json")
                self.assertEqual(1, updated["successful_official_page_count"])
                if page.get("http_status") == 200 and not page.get("error"):
                    self.assertTrue(updated["manual_review_required"])
                    self.assertTrue(updated["followup_review_pending"])
                else:
                    self.assertFalse(updated["manual_review_required"])

    def test_plan_only_performs_no_get_or_output_write(self):
        self.fixture()
        before = {str(path): path.read_bytes() for path in self.output.rglob("*") if path.is_file()}
        with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")), \
                patch.object(self.research, "write_json", side_effect=AssertionError("write prohibited")), redirect_stdout(io.StringIO()):
            self.assertEqual(0, followups.main(["--output", str(self.output), "--plan-only"]))
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.output.rglob("*") if path.is_file()})

    def test_total_get_cap_and_resume_do_not_repeat_completed_contact(self):
        for code in ("500A", "500B"):
            self.fixture(code)
        calls = []

        def reply(url, **kwargs):
            calls.append(url)
            self.assertFalse(kwargs["allow_redirects"])
            self.assertEqual({"User-Agent": self.research.USER_AGENT}, kwargs["headers"])
            return self.response(url, 404 if url.endswith("robots.txt") else 200,
                                 "新規上場" if "jpx.co.jp" in url else "IRフォーム")

        state = self.output / "run.json"
        plan = followups.build_plan(self.output)
        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(0, followups.collect(self.output, state, plan, 3, 1))
        first = followups.read_json(state)
        self.assertEqual("get_budget_exhausted", first["status"])
        self.assertEqual(3, first["http_get_attempt_count"])
        self.assertEqual(1, len(first["done"]))
        self.assertEqual(1, len(first["todo"]))
        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(0, followups.collect(self.output, state, followups.build_plan(self.output), 6, 1))
        second = followups.read_json(state)
        self.assertEqual("completed", second["status"])
        self.assertEqual(6, second["http_get_attempt_count"])
        self.assertEqual([], second["todo"])
        self.assertEqual(1, calls.count("https://issuer500a.example/ir/contact"))

    def test_common_failure_and_failed_preflight_keep_unstarted_records_pending(self):
        for code in ("500A", "500B"):
            self.fixture(code)
        untouched = (self.output / "records/500B.json").read_bytes()
        calls = []

        def reply(url, **kwargs):
            calls.append(url)
            if "jpx.co.jp" in url:
                return self.response(url, 200, "新規上場")
            if url.endswith("robots.txt"):
                return self.response(url, 404, "")
            return self.response(url, 503, "Invalid argument|remote address:envoy://cloudflare_https_tunnel/")

        state = self.output / "run.json"
        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(2, followups.collect(self.output, state, followups.build_plan(self.output), 100, 1))
        stopped = followups.read_json(state)
        self.assertEqual("environment_stopped", stopped["status"])
        self.assertEqual(2, len(stopped["todo"]))
        self.assertEqual(1, stopped["common_transport_503_count"])
        self.assertEqual(untouched, (self.output / "records/500B.json").read_bytes())
        self.assertFalse((self.output / "attempts/500B").exists())
        self.assertEqual(3, len(calls))
        # Invalid preflight body, even with HTTP 200, never starts a company GET.
        before = {str(path): path.read_bytes() for path in (self.output / "records").glob("*.json")}
        clock, http = self.network(lambda url, **kw: self.response(url, 200, "unrelated page"))
        with clock, http:
            self.assertEqual(2, followups.collect(self.output, self.output / "failed-preflight.json",
                                                  followups.build_plan(self.output), 100, 1))
        self.assertEqual(before, {str(path): path.read_bytes() for path in (self.output / "records").glob("*.json")})

    def test_unreachable_robots_stops_body_get_and_preserves_nested_diagnostics(self):
        for code, failure in (("5400", "http_503"), ("5401", "exception"), ("5402", "common_503")):
            with self.subTest(failure=failure):
                original = self.fixture(code)
                root = original["official_url"]
                calls = []

                def reply(url, **kwargs):
                    calls.append(url)
                    if "jpx.co.jp" in url:
                        return self.response(url, 200, "新規上場")
                    self.assertEqual(root + "robots.txt", url, "body GET must remain unattempted")
                    if failure == "exception":
                        raise self.research.requests.ConnectionError("mock unavailable")
                    text = ("Invalid argument|remote address:envoy://cloudflare_https_tunnel/"
                            if failure == "common_503" else "temporary service failure")
                    return self.response(url, 503, text)

                state_path = self.output / (code + "-run.json")
                clock, http = self.network(reply)
                with clock, http:
                    result = followups.collect(self.output, state_path,
                                               followups.build_plan(self.output, only_codes=[code]), 100, 1)
                self.assertEqual(2 if failure == "common_503" else 0, result)
                self.assertEqual([followups.PREFLIGHT, root + "robots.txt"], calls)
                state = followups.read_json(state_path)
                self.assertEqual(2, state["http_get_attempt_count"])
                self.assertEqual(1 if failure == "common_503" else 0, state["common_transport_503_count"])
                self.assertEqual(1 if failure == "common_503" else 0, len(state["todo"]))
                record = followups.read_json(self.output / "records" / (code + ".json"))
                for field in ("investigation_status", "evidence", "conditions", "manual_review"):
                    self.assertEqual(original[field], record[field])
                self.assertFalse(record["manual_review_required"])
                page = followups.read_json(self.output / record["fetches"][-1]["snapshot"])
                self.assertEqual("robots_unreachable_stopped", page["error"])
                self.assertFalse(page["http_get_attempted"])
                self.assertTrue(page["robots"]["http_get_attempted"])
                self.assertTrue(page["robots"]["http_get_completed_at"])
                if failure == "exception":
                    self.assertEqual("ConnectionError", page["robots"]["error"])
                else:
                    self.assertEqual(503, page["robots"]["http_status"])
                    self.assertEqual("common_transport_503" if failure == "common_503" else "http_503",
                                     page["robots"].get("failure_signature"))
                plan = followups.build_plan(self.output, only_codes=[code])
                self.assertEqual([], plan["selected"])
                self.assertEqual(1, plan["rejected_counts"]["saved_robots_unreachable_current_route_unconfirmed"])

    def test_unlinked_or_private_redirect_is_stopped_before_target_get(self):
        self.fixture()
        calls = []

        def reply(url, **kwargs):
            calls.append(url)
            if "jpx.co.jp" in url:
                return self.response(url, 200, "新規上場")
            if url.endswith("robots.txt"):
                return self.response(url, 404, "")
            return self.response(url, 302, "", {"Location": "https://unlinked.example/form"})

        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(0, followups.collect(self.output, self.output / "run.json", followups.build_plan(self.output), 100, 1))
        self.assertFalse(any("unlinked.example" in url for url in calls))
        self.assertIsNone(followups.safe_url("http://169.254.169.254/latest/meta-data"))
        record = followups.read_json(self.output / "records/500A.json")
        self.assertEqual("robots_unreachable_stopped", record["fetches"][-1]["error"])
        page = followups.read_json(self.output / record["fetches"][-1]["snapshot"])
        self.assertFalse(page["http_get_attempted"])
        self.assertEqual("unlinked_redirect_host", page["robots"]["error"])


    def finite_reviewed_fixture(self, code):
        """Small saved-only proof graphs for the two fixed reviewed cases."""
        import copy
        frozen = followups.FINITE_REVIEWED_AUTHORITIES[code]
        root = frozen["official_url"]
        record = self.fixture(code, links=[], status="provisional" if code == "6383" else "unconfirmed")
        record.update(company_name=frozen["company_name"], official_url=root,
                      verification_level="official_form_link_only" if code == "6383" else "none",
                      identity_status="name_or_security_code_observed" if code == "6383" else "issuer_unverified",
                      identity_matches=[], individual_access="not_stated", outreach_suitability="unconfirmed",
                      channels=["form"] if code == "6383" else [], public_ir_emails=[],
                      contact_url=followups.FINITE_REVIEWED_ROUTES[code][0]["target_url"] if code == "6383" else None,
                      evidence=[], fetches=[], discovery={"security_code": code, "official_url": root, "seed_company_name": frozen["company_name"]},
                      manual_review={"reviewer": frozen["reviewer"], "reviewed_at": "2026-10-11T01:00:00+00:00"})
        bindings = []
        for route in followups.FINITE_REVIEWED_ROUTES[code]:
            ref, index = route["snapshot"], route["index"]
            links = [{"url": root + "#nav" + str(i), "href": "#nav" + str(i), "label": "Navigation"} for i in range(index)]
            link = {"url": route["target_url"], "href": route["target_url"], "label": route["label"]}
            links += [link, {"url": "https://brand.example/ir/contact", "href": "https://brand.example/ir/contact", "label": "IRお問い合わせ"}]
            page = {"security_code": code, "url": route["parent_url"], "requested_url": route.get("parent_requested_url", route["parent_url"]),
                    "http_status": 200, "http_get_attempted": True, "retrieved_at": "2026-10-11T00:00:00+00:00",
                    "title": "お問い合わせ | ダイフク" if code == "6383" else "HEIWA", "headings": [],
                    "text": route["quote"], "links": links, "forms": []}
            self.save(ref, page)
            record["fetches"].append({"snapshot": ref, "url": page["url"], "http_status": 200})
            record["evidence"].append({"snapshot": ref, "url": page["url"], "retrieved_at": page["retrieved_at"],
                "quote": route["quote"], "role": route["evidence_role"], "source_link_index": index, "source_link_url": link["url"]})
            bindings.append({"source_snapshot": ref, "source_link_index": index, "source_link": link,
                "security_code": code, "company_name": frozen["company_name"], "seed_company_name": frozen["company_name"],
                "official_seed_url": root, "url": route["target_url"], "target_url": route["target_url"],
                "quote": route["quote"], "raw_href": link["href"], "retrieved_at": page["retrieved_at"],
                "reviewer": frozen["reviewer"], "reviewed_at": record["manual_review"]["reviewed_at"],
                "purpose": "issuer_identity_discovery", "method": "GET", "current_issuer_identity_verified": False,
                "financial_ir_reception_verified": False, "actual_form_fields_verified": False, "old_form_or_conditions_inherited": False})
        historical = self.save(f"evidence/{code}/past.json", {"security_code": code, "http_status": 503, "text": "old transport failure"})
        archive = self.save(f"attempts/{code}/past.json", {"security_code": code, "fetches": [{"snapshot": historical}]})
        record["previous_attempts"] = [archive]
        if code == "6383":
            identity = {"JPX_issuer": {"security_code": code, "company_name": frozen["company_name"]},
                        "IR_NAV_footer_used_as_contact_purpose": False}
            for name, ref, url, title, text in (
                ("homepage_proof", f"evidence/{code}/home.json", root, "日本 | ダイフク", "日本 | ダイフク"),
                ("issuer_IR_page_proof", f"evidence/{code}/ir.json", root + "ir/", "IR情報 | ダイフク",
                 "最新のIR資料 決算関連資料 一括ダウンロード（ZIP） 統合報告書 ダイフクレポート2026")):
                self.save(ref, {"security_code": code, "url": url, "requested_url": url, "http_status": 200,
                    "http_get_attempted": True, "title": title, "text": text, "links": [], "forms": [], "retrieved_at": "2026-10-11T00:00:00+00:00"})
                record["fetches"].append({"snapshot": ref, "url": url, "http_status": 200})
                identity[name] = {"snapshot": ref, "url": url, "retrieved_at": "2026-10-11T00:00:00+00:00", "quote": text,
                                  "title_quote": title, "financial_IR_quote": text}
            target = followups.FINITE_REVIEWED_ROUTES[code][0]["target_url"]
            stop_ref = frozen["historical_stop_snapshot"]
            self.save(stop_ref, {"security_code": code, "requested_url": target, "error": "robots_disallowed", "http_get_attempted": False,
                "retrieved_at": "2026-10-11T00:01:00+00:00", "robots": {"requested_url": "https://inquiry.daifuku.com/robots.txt",
                    "url": "https://inquiry.daifuku.com/robots.txt", "http_status": 200, "http_get_attempted": True,
                    "retrieved_at": "2026-10-11T00:00:30+00:00", "text": "User-agent: *\nDisallow: /\nAllow: /others_jp\n"}})
            record["fetches"].append({"snapshot": stop_ref, "url": target, "error": "robots_disallowed"})
            route, page = followups.FINITE_REVIEWED_ROUTES[code][0], followups.read_json(self.output / followups.FINITE_REVIEWED_ROUTES[code][0]["snapshot"])
            packet = {"approved_by": "/root", "binding_reviewed_by": frozen["binding_reviewer"],
                "authority_recorded_at_utc": "2026-10-11T03:00:00+00:00", "record_transition": {},
                "verification": {"pending": [], "update_races": [], "validation_errors": 0},
                "current_JPX_issuer_and_financial_IR_identity": identity,
                "actual_indexed_official_financial_IR_anchor": {"snapshot": route["snapshot"], "source_link_index": route["index"],
                    "actual_source_link": page["links"][route["index"]], "exact_primary_receipt_quote": route["quote"],
                    "retrieved_at": page["retrieved_at"], "attribute_kind": "anchor href",
                    "source_anchor_attribute_is_form_POST_action": False, "source_captured_link_is_embedded_iframe_src": False}}
        else:
            original = {"secondary_binding_decision_deferred": True, "primary_discovery": copy.deepcopy(bindings[0]),
                        "secondary_ir_route_candidate": {**copy.deepcopy(bindings[1]), "purpose": "ir_contact_followup"}}
            packet = {"approved_by": "/root", "security_code": code, "authorized_at_utc": "2026-10-11T03:00:00+00:00",
                      "completed_audit_part": frozen["audit_path"], "original_proposal_exact": original,
                      "current_issuer_identity_verified": False, "financial_ir_reception_verified": False, "actual_form_fields_verified": False,
                      "finite_discovery_proposals": bindings}
            audit = {"status": "completed_finite_batch", "closed_at_utc": "2026-10-11T02:00:00+00:00",
                     "validation_pending_security_codes": [], "error_count": 0, "race_count": 0, "pending_count": 0,
                     "saved_count": 1, "selected_company_count": 1, "reviewed": [{"security_code": code, "saved": True,
                         "reviewed_at": record["manual_review"]["reviewed_at"]}]}
            self.save(frozen["audit_path"], audit)
        self.save("records/" + code + ".json", record)
        self.save(frozen["path"], packet)
        freeze_patch = patch.dict(frozen, copy.deepcopy(frozen))
        freeze_patch.start()
        self.addCleanup(freeze_patch.stop)
        self.refreeze_finite_reviewed_fixture(code)
        return record

    def refreeze_finite_reviewed_fixture(self, code):
        """Bind mock SHAs again for semantic negatives, without weakening guards."""
        frozen = followups.FINITE_REVIEWED_AUTHORITIES[code]
        packet = followups.read_json(self.output / frozen["path"])
        record = followups.read_json(self.output / "records" / (code + ".json"))
        record_sha = followups.file_sha256(self.output / "records" / (code + ".json"))
        frozen["record_sha256"] = record_sha
        refs = {f["snapshot"] for f in record["fetches"]} | {f["snapshot"] for f in record["evidence"]}
        archives = set(record["previous_attempts"])
        for ref in archives:
            refs.update(f["snapshot"] for f in followups.read_json(self.output / ref)["fetches"])
        guards = {ref: followups.file_sha256(self.output / ref) for ref in refs | archives}
        if code == "6383":
            packet["record_transition"]["new_record_sha256"] = record_sha
            packet["verification"].update(source_snapshot_sha256={r: h for r,h in guards.items() if r.startswith("evidence/")},
                                          previous_attempt_sha256={r: h for r,h in guards.items() if r.startswith("attempts/")})
            packet["actual_indexed_official_financial_IR_anchor"]["snapshot_sha256"] = guards[followups.FINITE_REVIEWED_ROUTES[code][0]["snapshot"]]
            for proof in packet["current_JPX_issuer_and_financial_IR_identity"].values():
                if isinstance(proof, dict) and "snapshot" in proof: proof["snapshot_sha256"] = guards[proof["snapshot"]]
        else:
            audit = followups.read_json(self.output / frozen["audit_path"])
            row = audit["reviewed"][0]
            row.update(record_sha256_after_review=record_sha,
                       original_evidence_sha256={r:h for r,h in guards.items() if r.startswith("evidence/")},
                       original_attempt_sha256={r:h for r,h in guards.items() if r.startswith("attempts/")})
            self.save(frozen["audit_path"], audit)
            frozen["audit_sha256"] = followups.file_sha256(self.output / frozen["audit_path"])
            packet.update(completed_audit_sha256=frozen["audit_sha256"], source_record_sha256=record_sha,
                          recursive_source_and_archive_sha256=guards)
            for binding in packet["finite_discovery_proposals"]:
                binding.update(source_record_sha256=record_sha, source_sha256=guards[binding["source_snapshot"]])
            for key, binding in zip(("primary_discovery", "secondary_ir_route_candidate"), packet["finite_discovery_proposals"]):
                packet["original_proposal_exact"][key] = {**binding, "purpose": "issuer_identity_discovery" if key == "primary_discovery" else "ir_contact_followup"}
            original_bytes = (json.dumps(packet["original_proposal_exact"], ensure_ascii=False, indent=2) + "\n").encode()
            frozen["original_proposal_sha256"] = followups.hashlib.sha256(original_bytes).hexdigest()
            packet["original_proposal_sha256"] = frozen["original_proposal_sha256"]
        self.save(frozen["path"], packet)
        frozen["sha256"] = followups.file_sha256(self.output / frozen["path"])

    def test_finite_reviewed_plan_only_three_exact_targets_no_get_no_write(self):
        originals = {code: self.finite_reviewed_fixture(code) for code in ("6383", "6412")}
        with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")), \
                patch.object(self.research, "write_json", side_effect=AssertionError("write prohibited")), redirect_stdout(io.StringIO()):
            self.assertEqual(0, followups.main(["--output", str(self.output), "--plan-only", "--only-codes", "6383", "6412"]))
            plan = followups.build_plan(self.output, only_codes=["6383", "6412"])
        self.assertEqual((2, 3), (plan["selected_company_count"], plan["selected_url_count"]))
        for task in plan["selected"]:
            proof = task["reviewed_ir_route_proof" if task["security_code"] == "6383" else "identity_discovery_proof"]
            self.assertEqual("ir_contact_followup" if task["security_code"] == "6383" else "issuer_identity_discovery", task["purpose"])
            self.assertFalse(proof["current_issuer_reception_verified"])
            self.assertFalse(proof["actual_form_fields_verified"])
            self.assertEqual(task["security_code"] == "6383", task["explicit_ir_link"])
            if task["security_code"] == "6383": self.assertIn("robots_literal_allow_correction", task)
            self.assertEqual(originals[task["security_code"]], followups.read_json(self.output / "records" / (task["security_code"] + ".json")))
        self.assertIn("https://www.heiwa-hd.co.jp/ja/inquiry/contact//", [t["url"] for t in plan["selected"]])
        self.assertNotIn("https://brand.example/ir/contact", [t["url"] for t in plan["selected"]])

    def test_finite_reviewed_missing_authority_and_source_changes_never_fallback(self):
        for code in ("6383", "6412"):
            for damage in ("record", "parent", "historical", "archive", "authority", "missing_authority", "missing_source", "audit"):
                if code == "6383" and damage == "audit": continue
                with self.subTest(code=code, damage=damage):
                    self.finite_reviewed_fixture(code)
                    frozen, route = followups.FINITE_REVIEWED_AUTHORITIES[code], followups.FINITE_REVIEWED_ROUTES[code][0]
                    rel = "records/" + code + ".json" if damage == "record" else route["snapshot"] if damage in {"parent", "missing_source"} else \
                        f"evidence/{code}/past.json" if damage == "historical" else f"attempts/{code}/past.json" if damage == "archive" else \
                        frozen["audit_path"] if damage == "audit" else frozen["path"]
                    if damage.startswith("missing_"): (self.output / rel).unlink()
                    else:
                        changed = followups.read_json(self.output / rel); changed["external_writer"] = True; self.save(rel, changed)
                    with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                        self.assertEqual([], followups.build_plan(self.output, only_codes=[code])["selected"])

    def test_finite_reviewed_semantic_negatives_strict_index_issuer_times_and_purpose(self):
        for code in ("6383", "6412"):
            for damage in ("bool_index", "string_index", "wrong_index", "nav", "raw_href", "other_company", "seed", "official_path", "official_host", "source_issuer",
                           "naive_capture", "naive_review", "unreviewed", "refusal", "POST", "already_fetched", "unclosed"):
                if code == "6383" and damage == "unclosed": continue
                with self.subTest(code=code, damage=damage):
                    self.finite_reviewed_fixture(code)
                    frozen, route = followups.FINITE_REVIEWED_AUTHORITIES[code], followups.FINITE_REVIEWED_ROUTES[code][0]
                    packet, record = followups.read_json(self.output / frozen["path"]), followups.read_json(self.output / "records" / (code + ".json"))
                    page = followups.read_json(self.output / route["snapshot"])
                    binding = packet["actual_indexed_official_financial_IR_anchor"] if code == "6383" else packet["finite_discovery_proposals"][0]
                    if damage in {"bool_index", "string_index", "wrong_index"}: binding["source_link_index"] = True if damage == "bool_index" else str(route["index"]) if damage == "string_index" else route["index"] - 1
                    elif damage == "nav": page["text"] = "会社案内 IR 採用 製品 お問い合わせ"
                    elif damage == "raw_href": page["links"][route["index"]]["href"] = "https://brand.example/"
                    elif damage == "other_company": record["company_name"] = "別発行体"
                    elif damage == "seed": record["discovery"]["official_url"] = "https://brand.example/"
                    elif damage == "official_path": record["official_url"] += "different/"
                    elif damage == "official_host": record["official_url"] = "https://brand.example/"
                    elif damage == "source_issuer": page["security_code"] = "6383" if code == "6412" else "6412"
                    elif damage == "naive_capture": page["retrieved_at"] = "2026-10-11T00:00:00"
                    elif damage == "naive_review": record["manual_review"]["reviewed_at"] = "2026-10-11T01:00:00"
                    elif damage == "unreviewed": record["manual_review_required"] = True
                    elif damage == "refusal": record["outreach_suitability"] = "restricted"
                    elif damage == "POST": page["forms"] = [{"action": route["target_url"], "method": "post"}]
                    elif damage == "already_fetched":
                        ref = self.save(f"evidence/{code}/already.json", {"requested_url": route["target_url"], "url": route["target_url"], "http_status": 200, "http_get_attempted": True})
                        record["fetches"].append({"snapshot": ref, "url": route["target_url"], "http_status": 200})
                    else:
                        audit = followups.read_json(self.output / frozen["audit_path"]); audit["status"] = "fixed_batch_validation_pending"; self.save(frozen["audit_path"], audit)
                    self.save(f"records/{code}.json", record); self.save(route["snapshot"], page); self.save(frozen["path"], packet)
                    self.refreeze_finite_reviewed_fixture(code)
                    with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                        tasks = followups.build_plan(self.output, only_codes=[code])["selected"]
                    if code == "6412" and damage in {"POST", "already_fetched"}:
                        self.assertEqual([followups.FINITE_REVIEWED_ROUTES[code][1]["target_url"]], [t["url"] for t in tasks])
                    else: self.assertEqual([], tasks)

    def test_finite_mixed_ir_anchor_keeps_denied_robots_and_changed_policy_stopped(self):
        for damage in ("HTTP403", "HTTP429", "HTTP503", "different_origin", "narrow_deny", "unsupported", "naive"):
            with self.subTest(damage=damage):
                self.finite_reviewed_fixture("6383")
                ref = followups.FINITE_REVIEWED_AUTHORITIES["6383"]["historical_stop_snapshot"]
                page = followups.read_json(self.output / ref); robot = page["robots"]
                if damage.startswith("HTTP"): robot["http_status"] = int(damage[4:])
                elif damage == "different_origin": robot["requested_url"] = robot["url"] = "https://brand.example/robots.txt"
                elif damage == "narrow_deny": robot["text"] += "Disallow: /others_jp\n"
                elif damage == "unsupported": robot["text"] = "User-agent: *\nDisallow: /\nAllow: /others*\n"
                else: robot["retrieved_at"] = "2026-10-11T00:00:30"
                self.save(ref, page); self.refreeze_finite_reviewed_fixture("6383")
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                    self.assertEqual([], followups.build_plan(self.output, only_codes=["6383"])["selected"])

    def stop_finite_reviewed_run(self, code, budget=False):
        original = self.finite_reviewed_fixture(code)
        plan = followups.build_plan(self.output, only_codes=[code]); calls = []
        state_path = self.output / (code + "-finite-stop.json")
        if state_path.exists(): state_path.unlink()

        def reply(url, **kwargs):
            calls.append(url)
            if url == followups.PREFLIGHT: return self.response(url, 200, "新規上場")
            if url.endswith("/robots.txt"): return self.response(url, 404, "")
            if code == "6412" and url == plan["selected"][0]["url"] or budget:
                return self.response(url, 200, "<form><input type='email'><textarea name='question'></textarea></form>IRお問い合わせ")
            return self.response(url, 503, "Invalid argument|remote address:envoy://cloudflare_https_tunnel/")

        clock, http = self.network(reply)
        with clock, http:
            cap = (2 if code == "6383" else 3) if budget else 1000
            self.assertEqual(0 if budget else 2, followups.collect(self.output, state_path, plan, cap, 0.25))
        return original, plan, state_path, calls

    def test_finite_reviewed_resume_keeps_two_holding_links_and_financial_ir_pending(self):
        for code in ("6383", "6412"):
            for budget in (False, True):
                with self.subTest(code=code, budget=budget):
                    original, plan, state_path, calls = self.stop_finite_reviewed_run(code, budget)
                    stopped = followups.read_json(state_path)
                    self.assertEqual("get_budget_exhausted" if budget else "environment_stopped", stopped["status"])
                    fresh = followups.build_plan(self.output, only_codes=[code])
                    self.assertEqual([], fresh["selected"])
                    resumed = []

                    def healthy(url, **kwargs):
                        resumed.append(url)
                        return self.response(url, 404 if url.endswith("/robots.txt") else 200,
                            "新規上場" if url == followups.PREFLIGHT else "新しい会社案内 IRお問い合わせ")

                    clock, http = self.network(healthy)
                    with clock, http, redirect_stdout(io.StringIO()):
                        self.assertEqual(0, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", code, "--global-rps", "0.25"]))
                    final = followups.read_json(state_path)
                    self.assertEqual(("completed", [], len(plan["selected"])), (final["status"], final["todo"], len(final["done"])))
                    self.assertEqual(len(calls)+len(resumed), final["http_get_attempt_count"])
                    if followups.task_key(plan["selected"][0]) in stopped["done"]:
                        self.assertNotIn(plan["selected"][0]["url"], resumed)
                    updated = followups.read_json(self.output / "records" / (code + ".json"))
                    for key in ("identity_status", "investigation_status", "verification_level", "conditions", "evidence", "public_ir_emails"):
                        self.assertEqual(original[key], updated[key])
                    self.assertTrue(updated["manual_review_required"])
                    with patch.object(self.research.requests, "get", side_effect=AssertionError("completed GET prohibited")), redirect_stdout(io.StringIO()):
                        self.assertEqual(0, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", code]))

    def test_finite_reviewed_resume_rejects_writer_archive_source_part_and_old_state(self):
        for code in ("6383", "6412"):
            for damage in ("record", "source", "past_source", "authority", "archive", "audit", "old_state", "saved_url"):
                if code == "6383" and damage == "audit": continue
                with self.subTest(code=code, damage=damage):
                    _, plan, state_path, _ = self.stop_finite_reviewed_run(code)
                    stopped = followups.read_json(state_path)
                    frozen = followups.FINITE_REVIEWED_AUTHORITIES[code]
                    lineage_field = "reviewed_ir_record_lineage" if code == "6383" else "identity_record_lineage"
                    if damage == "old_state": stopped.pop(lineage_field); self.research.write_json(state_path, stopped)
                    elif damage == "saved_url": stopped["selected"][-1]["url"] = "https://brand.example/contact"; self.research.write_json(state_path, stopped)
                    else:
                        ref = f"records/{code}.json" if damage == "record" else plan["selected"][0]["parent_snapshot"] if damage == "source" else \
                            f"evidence/{code}/past.json" if damage == "past_source" else frozen["path"] if damage == "authority" else \
                            frozen["audit_path"] if damage == "audit" else stopped[lineage_field][code]["original_record_archive"]
                        value = followups.read_json(self.output / ref); value["external_writer"] = True; self.save(ref, value)
                    before = (self.output / f"records/{code}.json").read_bytes()
                    with patch.object(self.research.requests, "get", side_effect=AssertionError("tampered resume GET prohibited")), redirect_stdout(io.StringIO()):
                        self.assertEqual(2, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", code]))
                    after = followups.read_json(state_path)
                    self.assertEqual((stopped["done"], len(stopped["todo"]), stopped["http_get_attempt_count"]),
                                     (after["done"], len(after["todo"]), after["http_get_attempt_count"]))
                    self.assertEqual(before, (self.output / f"records/{code}.json").read_bytes())

    def test_finite_reviewed_rechecks_all_guarded_dependencies_after_preflight(self):
        for code in ("6383", "6412"):
            for damage in ("historical_source", "original_archive", "authority", "audit"):
                if code == "6383" and damage == "audit": continue
                with self.subTest(code=code, damage=damage):
                    self.finite_reviewed_fixture(code)
                    plan = followups.build_plan(self.output, only_codes=[code]); calls = []
                    frozen = followups.FINITE_REVIEWED_AUTHORITIES[code]

                    def preflight(url, **kwargs):
                        calls.append(url); self.assertEqual(followups.PREFLIGHT, url)
                        ref = f"evidence/{code}/past.json" if damage == "historical_source" else f"attempts/{code}/past.json" if damage == "original_archive" else \
                            frozen["path"] if damage == "authority" else frozen["audit_path"]
                        value = followups.read_json(self.output / ref); value["changed_during_preflight"] = True; self.save(ref, value)
                        return self.response(url, 200, "新規上場")

                    clock, http = self.network(preflight)
                    state_path = self.output / f"{code}-finite-preflight-{damage}.json"
                    with clock, http:
                        self.assertEqual(2, followups.collect(self.output, state_path, plan, 1000, 0.25))
                    stopped = followups.read_json(state_path)
                    self.assertEqual([followups.PREFLIGHT], calls)
                    self.assertEqual(([], len(plan["selected"]), 1), (stopped["done"], len(stopped["todo"]), stopped["http_get_attempt_count"]))

    def test_finite_reviewed_guard_prefix_bounds_recursive_issuer_and_missing_references(self):
        for code in ("6383", "6412"):
            for damage in ("absolute", "wrong_issuer", "escape", "omitted_history", "nonstring_archive", "archive_issuer"):
                with self.subTest(code=code, damage=damage):
                    self.finite_reviewed_fixture(code)
                    frozen = followups.FINITE_REVIEWED_AUTHORITIES[code]
                    packet = followups.read_json(self.output / frozen["path"])
                    guards = packet["verification"]["source_snapshot_sha256"] if code == "6383" else packet["recursive_source_and_archive_sha256"]
                    original_ref = f"evidence/{code}/past.json"
                    if damage == "omitted_history": guards.pop(original_ref)
                    elif damage in {"absolute", "wrong_issuer", "escape"}:
                        bad = str(self.output / original_ref) if damage == "absolute" else "evidence/9999/past.json" if damage == "wrong_issuer" else f"evidence/{code}/../9999/past.json"
                        guards[bad] = guards[original_ref]
                    else:
                        ref = f"attempts/{code}/past.json"; archive = followups.read_json(self.output / ref)
                        if damage == "archive_issuer": archive["security_code"] = "9999"
                        else: archive["previous_attempts"] = [True]
                        self.save(ref, archive)
                        hashes = packet["verification"]["previous_attempt_sha256"] if code == "6383" else guards
                        hashes[ref] = followups.file_sha256(self.output / ref)
                    self.save(frozen["path"], packet)
                    frozen["sha256"] = followups.file_sha256(self.output / frozen["path"])
                    with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                        self.assertEqual([], followups.build_plan(self.output, only_codes=[code])["selected"])

    def test_finite_holding_discovery_refuses_false_claims_and_old_unclosed_authority(self):
        for damage in ("original_changed", "old_deferred_removed", "top_identity", "binding_identity", "binding_reception", "binding_fields",
                       "old_conditions", "other_purpose", "other_target", "other_seed", "missing_binding", "naive_authority", "closure_after_authority"):
            with self.subTest(damage=damage):
                self.finite_reviewed_fixture("6412")
                frozen = followups.FINITE_REVIEWED_AUTHORITIES["6412"]
                packet = followups.read_json(self.output / frozen["path"])
                binding = packet["finite_discovery_proposals"][1]
                if damage == "original_changed": packet["original_proposal_exact"]["other_note"] = "mutation"
                elif damage == "old_deferred_removed": packet["original_proposal_exact"]["secondary_binding_decision_deferred"] = False
                elif damage == "top_identity": packet["current_issuer_identity_verified"] = True
                elif damage == "binding_identity": binding["current_issuer_identity_verified"] = True
                elif damage == "binding_reception": binding["financial_ir_reception_verified"] = True
                elif damage == "binding_fields": binding["actual_form_fields_verified"] = True
                elif damage == "old_conditions": binding["old_form_or_conditions_inherited"] = True
                elif damage == "other_purpose": binding["purpose"] = "ir_contact_followup"
                elif damage == "other_target": binding["url"] = "https://brand.example/ir/contact"
                elif damage == "other_seed": binding["official_seed_url"] = "https://brand.example/"
                elif damage == "missing_binding": packet["finite_discovery_proposals"].pop()
                elif damage == "naive_authority": packet["authorized_at_utc"] = "2026-10-11T03:00:00"
                else:
                    audit = followups.read_json(self.output / frozen["audit_path"]); audit["closed_at_utc"] = "2026-10-11T04:00:00+00:00"
                    self.save(frozen["audit_path"], audit)
                    frozen["audit_sha256"] = followups.file_sha256(self.output / frozen["audit_path"])
                    packet["completed_audit_sha256"] = frozen["audit_sha256"]
                self.save(frozen["path"], packet)
                frozen["sha256"] = followups.file_sha256(self.output / frozen["path"])
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                    self.assertEqual([], followups.build_plan(self.output, only_codes=["6412"])["selected"])

    def test_finite_financial_route_newer_robots_denials_never_reuse_old_allow(self):
        for status in (200, 401, 403, 429, 503):
            with self.subTest(status=status):
                record = self.finite_reviewed_fixture("6383")
                ref = self.save("evidence/6383/newer-robots.json", {"security_code": "6383",
                    "requested_url": "https://inquiry.daifuku.com/robots.txt", "url": "https://inquiry.daifuku.com/robots.txt",
                    "http_status": status, "http_get_attempted": True, "retrieved_at": "2026-10-11T00:30:00+00:00",
                    "text": "User-agent: *\nDisallow: /\n"})
                record["fetches"].append({"snapshot": ref, "url": "https://inquiry.daifuku.com/robots.txt", "http_status": status})
                self.save("records/6383.json", record); self.refreeze_finite_reviewed_fixture("6383")
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                    self.assertEqual([], followups.build_plan(self.output, only_codes=["6383"])["selected"])

    def test_finite_resume_original_archive_race_stops_immediately_after_preflight(self):
        for code in ("6383", "6412"):
            for damage in ("mutated", "missing", "symlink_outside"):
                with self.subTest(code=code, damage=damage):
                    _, plan, state_path, _ = self.stop_finite_reviewed_run(code)
                    before = followups.read_json(state_path)
                    lineage_field = "reviewed_ir_record_lineage" if code == "6383" else "identity_record_lineage"
                    archive = before[lineage_field][code]["original_record_archive"]
                    path = self.output / archive
                    original_record = (self.output / f"records/{code}.json").read_bytes()
                    calls = []

                    def preflight(url, **kwargs):
                        calls.append(url)
                        self.assertEqual(followups.PREFLIGHT, url, "archive change must prevent extra robots and target GETs")
                        if damage == "mutated":
                            value = followups.read_json(path); value["changed_during_preflight"] = True; self.save(archive, value)
                        elif damage == "missing": path.unlink()
                        else:
                            outside = self.output / "outside-original-record.json"
                            outside.write_bytes(path.read_bytes()); path.unlink(); path.symlink_to(outside)
                        return self.response(url, 200, "新規上場")

                    clock, http = self.network(preflight)
                    with clock, http, redirect_stdout(io.StringIO()):
                        self.assertEqual(2, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", code, "--global-rps", "0.25"]))
                    after = followups.read_json(state_path)
                    self.assertEqual([followups.PREFLIGHT], calls)
                    self.assertEqual("reviewed_ir_source_changed_stopped" if code == "6383" else "identity_source_changed_stopped", after["status"])
                    self.assertEqual((before["done"], before["todo"]), (after["done"], after["todo"]))
                    self.assertEqual(before["http_get_attempt_count"] + 1, after["http_get_attempt_count"])
                    self.assertEqual(original_record, (self.output / f"records/{code}.json").read_bytes())

    def test_finite_resume_invalid_original_archive_reference_stops_before_body_get(self):
        for code in ("6383", "6412"):
            for damage in ("wrong_issuer", "absolute", "escape", "nonstring", "missing_reference"):
                with self.subTest(code=code, damage=damage):
                    _, _, state_path, _ = self.stop_finite_reviewed_run(code)
                    before = followups.read_json(state_path)
                    lineage_field = "reviewed_ir_record_lineage" if code == "6383" else "identity_record_lineage"
                    archive = before[lineage_field][code]["original_record_archive"]
                    wrong = self.output / "attempts/9999/original.json"
                    wrong.parent.mkdir(parents=True, exist_ok=True); wrong.write_bytes((self.output / archive).read_bytes())
                    changed = "attempts/9999/original.json" if damage == "wrong_issuer" else str(self.output / archive) if damage == "absolute" else \
                        f"attempts/{code}/../9999/original.json" if damage == "escape" else True if damage == "nonstring" else None
                    before[lineage_field][code]["original_record_archive"] = changed
                    self.research.write_json(state_path, before)
                    original_record = (self.output / f"records/{code}.json").read_bytes()
                    calls = []

                    def preflight(url, **kwargs):
                        calls.append(url)
                        # The legacy verifier accepts an absolute path inside
                        # the issuer's archive root; the finite dispatch guard
                        # still rejects it before any extra robots/body GET.
                        self.assertEqual("absolute", damage)
                        self.assertEqual(followups.PREFLIGHT, url)
                        return self.response(url, 200, "新規上場")

                    clock, http = self.network(preflight)
                    with clock, http, redirect_stdout(io.StringIO()):
                        self.assertEqual(2, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", code]))
                    after = followups.read_json(state_path)
                    self.assertEqual([followups.PREFLIGHT] if damage == "absolute" else [], calls)
                    self.assertEqual((before["done"], before["todo"], before["http_get_attempt_count"] + len(calls)),
                                     (after["done"], after["todo"], after["http_get_attempt_count"]))
                    self.assertEqual(original_record, (self.output / f"records/{code}.json").read_bytes())

    def finite_symlink_dependency(self, code, kind, outside_dataset=True):
        """Move only a synthetic fixture dependency, keeping its exact bytes."""
        if kind in ("evidence", "attempts"):
            source = self.output / kind / code
        else:
            key = "path" if kind == "authority" else "audit_path"
            source = self.output / followups.FINITE_REVIEWED_AUTHORITIES[code][key]
        base = self.output.parent if outside_dataset else self.output / (
            kind if kind in ("evidence", "attempts") else "parts") / "relocated"
        destination = base / (code + "-" + kind + (source.suffix if source.is_file() else ""))
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
        source.symlink_to(destination, target_is_directory=destination.is_dir())

    def test_finite_reviewed_plan_rejects_external_issuer_dirs_authority_and_closed_part(self):
        for code in ("6383", "6412"):
            kinds = ("evidence", "attempts", "authority") + (("closed_part",) if code == "6412" else ())
            for kind in kinds:
                with self.subTest(code=code, kind=kind):
                    case = type(self)(); case.setUp()
                    try:
                        case.finite_reviewed_fixture(code)
                        plan = followups.build_plan(case.output, only_codes=[code])
                        task = plan["selected"][0]
                        proof = task["reviewed_ir_route_proof" if code == "6383" else "identity_discovery_proof"]
                        case.finite_symlink_dependency(code, kind)
                        with patch.object(case.research.requests, "get", side_effect=AssertionError("GET prohibited")), \
                                patch.object(case.research, "write_json", side_effect=AssertionError("plan write prohibited")):
                            self.assertEqual([], followups.build_plan(case.output, only_codes=[code])["selected"])
                        self.assertFalse(followups.completed_identity_audit_matches(case.output, proof))
                    finally:
                        case.doCleanups()

    def test_finite_resume_external_dir_or_authority_race_retains_pending_without_extra_get(self):
        for code in ("6383", "6412"):
            kinds = ("evidence", "attempts", "authority") + (("closed_part",) if code == "6412" else ())
            for kind in kinds:
                with self.subTest(code=code, kind=kind):
                    case = type(self)(); case.setUp()
                    try:
                        _, _, state_path, _ = case.stop_finite_reviewed_run(code)
                        before = followups.read_json(state_path)
                        original_record = (case.output / f"records/{code}.json").read_bytes()
                        calls = []

                        def preflight(url, **kwargs):
                            calls.append(url)
                            self.assertEqual(followups.PREFLIGHT, url, "escaped dependency must stop before robots/body")
                            case.finite_symlink_dependency(code, kind)
                            if kind == "attempts":
                                task = before["todo"][0]
                                field = "reviewed_ir_route_proof" if code == "6383" else "identity_discovery_proof"
                                lineage = "reviewed_ir_record_lineage" if code == "6383" else "identity_record_lineage"
                                self.assertFalse(followups.finite_own_archive_matches(case.output, task[field], before[lineage][code]))
                            return case.response(url, 200, "新規上場")

                        clock, http = case.network(preflight)
                        with clock, http, redirect_stdout(io.StringIO()):
                            self.assertEqual(2, followups.main(["--output", str(case.output), "--state", str(state_path), "--only-codes", code]))
                        after = followups.read_json(state_path)
                        self.assertEqual([followups.PREFLIGHT], calls)
                        self.assertEqual("reviewed_ir_source_changed_stopped" if code == "6383" else "identity_source_changed_stopped", after["status"])
                        self.assertEqual((before["done"], before["todo"], before["http_get_attempt_count"] + 1),
                                         (after["done"], after["todo"], after["http_get_attempt_count"]))
                        self.assertEqual(original_record, (case.output / f"records/{code}.json").read_bytes())
                    finally:
                        case.doCleanups()

    def test_finite_reviewed_inside_dataset_symlinks_preserve_exact_plan_and_resume(self):
        for code in ("6383", "6412"):
            with self.subTest(code=code):
                case = type(self)(); case.setUp()
                try:
                    _, _, state_path, _ = case.stop_finite_reviewed_run(code)
                    before = followups.read_json(state_path)
                    kinds = ("evidence", "attempts", "authority") + (("closed_part",) if code == "6412" else ())
                    original = followups.read_json(case.output / before[
                        "reviewed_ir_record_lineage" if code == "6383" else "identity_record_lineage"][code]["original_record_archive"])
                    proof_record_sha = followups.FINITE_REVIEWED_AUTHORITIES[code]["record_sha256"]
                    expected, _ = followups.company_candidates(case.output, original, [], proof_record_sha256=proof_record_sha)
                    for kind in kinds: case.finite_symlink_dependency(code, kind, outside_dataset=False)
                    with patch.object(case.research.requests, "get", side_effect=AssertionError("plan GET prohibited")), \
                            patch.object(case.research, "write_json", side_effect=AssertionError("plan write prohibited")):
                        actual, _ = followups.company_candidates(case.output, original, [], proof_record_sha256=proof_record_sha)
                    self.assertEqual(expected, actual)
                    resumed = []

                    def healthy(url, **kwargs):
                        resumed.append(url)
                        return case.response(url, 404 if url.endswith("/robots.txt") else 200,
                                             "新規上場" if url == followups.PREFLIGHT else "新会社情報")

                    clock, http = case.network(healthy)
                    with clock, http, redirect_stdout(io.StringIO()):
                        self.assertEqual(0, followups.main(["--output", str(case.output), "--state", str(state_path), "--only-codes", code]))
                    after = followups.read_json(state_path)
                    self.assertEqual(("completed", []), (after["status"], after["todo"]))
                    self.assertEqual(before["http_get_attempt_count"] + len(resumed), after["http_get_attempt_count"])
                    for task in before["selected"]:
                        self.assertEqual(0 if followups.task_key(task) in before["done"] else 1, resumed.count(task["url"]))
                finally:
                    case.doCleanups()


    def named_current_issuer_fixture(self):
        """Portable six-file lineage; the observed C&G history stays frozen."""
        import copy
        import shutil

        if self.output.exists():
            shutil.rmtree(self.output)
        frozen = followups.FINITE_REVIEWED_AUTHORITIES["6633"]
        if not getattr(self, "named_authority_patch_started", False):
            guard = patch.dict(frozen, copy.deepcopy(frozen))
            guard.start()
            self.addCleanup(guard.stop)
            self.named_authority_patch_started = True
        route = followups.FINITE_REVIEWED_ROUTES["6633"][0]
        refs = frozen["source_references"]
        current, historical, archives = refs[:2], refs[2:4], refs[4:]
        root, target = route["parent_url"], route["target_url"]
        links = [{"url": root + "#nav" + str(i), "href": "#nav" + str(i),
                  "label": "Navigation"} for i in range(route["index"])]
        link = {"url": target, "href": target, "label": route["label"]}
        links += [link, {"url": root + "ir/contact", "href": root + "ir/contact",
                         "label": "IRお問い合わせ"}]
        page = {"security_code": "6633", "url": root, "requested_url": root,
                "http_status": 200, "error": None, "http_get_attempted": True,
                "retrieved_at": "2026-10-11T18:32:37+00:00",
                "http_get_started_at": "2026-10-11T18:32:52+00:00",
                "http_response_received_at": "2026-10-11T18:32:54+00:00",
                "http_get_completed_at": "2026-10-11T18:32:55+00:00",
                "title": "C&G SYSTEMS", "text": "C&G SYSTEMS " + route["quote"],
                "headings": [], "links": links, "forms": []}
        self.save(current[0], page)
        self.save(current[1], {**page, "url": root + "re/contact/",
                              "requested_url": root + "re/contact/",
                              "text": "C&G SYSTEMS 採用お問い合わせ", "links": [], "forms": []})
        for ref in historical:
            self.save(ref, {"security_code": "6633", "http_status": 503,
                            "text": "原取得障害", "http_get_attempted": True})
        self.save(archives[0], {"security_code": "6633", "previous_attempts": [],
                               "fetches": [{"snapshot": historical[0]}]})
        self.save(archives[1], {"security_code": "6633", "previous_attempts": [archives[0]],
                               "fetches": [{"snapshot": historical[1]}]})
        record = {"security_code": "6633", "company_name": frozen["company_name"],
                  "market": "スタンダード", "jpx_sector": "電気機器", "official_url": root,
                  "attempted_at": "2026-10-11T18:32:22+00:00",
                  "completed_at": "2026-10-11T18:33:10+00:00",
                  "discovery": {"security_code": "6633", "official_url": root,
                                "seed_company_name": frozen["seed_company_name"]},
                  "investigation_status": "unconfirmed", "verification_level": "none",
                  "unconfirmed_reason": "issuer_unverified", "channels": [], "contact_url": None,
                  "public_ir_emails": [], "individual_access": "not_stated",
                  "outreach_suitability": "unconfirmed", "manual_review_required": False,
                  "identity_status": "name_or_security_code_observed",
                  "identity_matches": [{"snapshot": ref, "matched_name": "cgs"} for ref in current],
                  "successful_official_page_count": 2, "http_get_attempt_count": 4,
                  "previous_attempts": list(archives),
                  "fetches": [{"snapshot": ref, "url": root if i == 0 else root + "re/contact/",
                               "http_status": 200} for i, ref in enumerate(current)],
                  "manual_review": {"reviewer": frozen["reviewer"],
                                    "reviewed_at": "2026-10-11T20:22:38+00:00"},
                  "evidence": [{"snapshot": current[0], "quote": "C&G SYSTEMS"},
                               {"snapshot": current[0], "url": root, "retrieved_at": page["retrieved_at"],
                                "quote": route["quote"], "role": route["evidence_role"],
                                "source_link_index": 41, "source_link_url": target}],
                  "conditions": ["原条件", "原条件"], "limitations": ["原制限"],
                  "manual_followup_candidates": [{"purpose": "issuer_identity_discovery", "method": "GET",
                      "source_link_index": 41, "source_snapshot": current[0], "parent_snapshot": current[0],
                      "source_link": link, "url": target, "IR_channel_verified": False,
                      "IR_purpose_verified": False, "current_issuer_reception_verified": False}]}
        immutable = ("security_code", "company_name", "market", "jpx_sector", "official_url",
                     "attempted_at", "completed_at", "fetches", "discovery", "identity_status",
                     "identity_matches", "successful_official_page_count", "http_get_attempt_count", "previous_attempts")
        original = {"security_code": "6633", "record_sha256": "a" * 64,
                    "immutable_record_fields": {k: copy.deepcopy(record[k]) for k in immutable},
                    "original_evidence": copy.deepcopy(record["evidence"][:1]),
                    "original_conditions": copy.deepcopy(record["conditions"]),
                    "original_limitations": copy.deepcopy(record["limitations"])}
        row = {"security_code": "6633", "reviewed_at": record["manual_review"]["reviewed_at"]}
        others = [{"security_code": str(6620 + i)} for i in range(9)]
        audit = {"status": "completed", "pending_validation": [], "pending_company_count": 0,
                 "validator_error_count": 0, "conflict_count": 0, "reviewed_company_count": 10,
                 "completed_at": "2026-10-11T21:06:13+00:00",
                 "selected": [original] + copy.deepcopy(others), "reviewed": [row] + copy.deepcopy(others)}
        binding = {"security_code": "6633", "company_name": frozen["company_name"],
            "seed_company_name": frozen["seed_company_name"], "official_seed_url": root,
            "purpose": "issuer_identity_discovery", "kind": "reviewed_named_current_issuer_site_discovery",
            "method": "GET", "url": target, "target_url": target, "parent_url": root,
            "parent_requested_url": root, "source_url": root,
            "parent_snapshot": current[0], "source_snapshot": current[0],
            "retrieved_at": page["retrieved_at"], "parent_retrieved_at": page["retrieved_at"],
            "source_link": copy.deepcopy(link), "source_link_url": target, "raw_href": target,
            "source_link_index": 41, "quote": route["quote"], "quote_field_path": "text",
            "field_path": "links.41", "raw_href_field_path": "links.41.href",
            "resolved_url_field_path": "links.41.url", "source_record_path": "records/6633.json",
            "source_record_candidate_path": "manual_followup_candidates.0",
            "source_record_evidence_path": "evidence.1", "reviewer": frozen["reviewer"],
            "reviewed_at": record["manual_review"]["reviewed_at"], "source_audit_part": frozen["audit_path"],
            "parent_http_status": 200, "parent_error": None, "parent_http_get_attempted": True,
            "parent_actual_http_times": {k: page[k] for k in ("http_get_started_at", "http_response_received_at", "http_get_completed_at")}}
        for key in ("IR_channel_verified", "IR_purpose_verified", "current_issuer_reception_verified",
                    "current_issuer_identity_verified", "financial_ir_reception_verified", "actual_form_fields_verified",
                    "old_form_or_conditions_inherited", "legal_migration_or_split_or_date_inferred", "raw_url_normalized"):
            binding[key] = False
        authority = {"approved_by": "/root", "reviewer": frozen["binding_reviewer"],
                     "status": "authorized_finite_identity_discovery", "security_code": "6633",
                     "source_proposal_path": frozen["original_proposal_path"],
                     "source_proposal_sha256": frozen["original_proposal_sha256"],
                     "closed_audit_part": frozen["audit_path"], "source_record_path": "records/6633.json",
                     "maximum_candidate_count": 1, "secondary_ir_route_candidate_present": False,
                     "root_actual_primary_meaning_review_completed": True,
                     "source_record_initial_identity_status_and_matches_are_immutable_history": True,
                     "authority_recorded_at_utc": "2026-10-11T21:21:04+00:00",
                     "original_record_sha256": "a" * 64, "finite_discovery_proposals": [binding]}
        self.save("records/6633.json", record)
        self.save(frozen["audit_path"], audit)
        self.save(frozen["path"], authority)
        self.refreeze_named_current_issuer_fixture()
        return record

    def refreeze_named_current_issuer_fixture(self):
        """Re-sign mocks for semantic negatives; frozen history is not rewritten."""
        import copy

        frozen = followups.FINITE_REVIEWED_AUTHORITIES["6633"]
        record = followups.read_json(self.output / "records/6633.json")
        audit = followups.read_json(self.output / frozen["audit_path"])
        packet = followups.read_json(self.output / frozen["path"])
        logical = lambda value: followups.hashlib.sha256(json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        frozen["record_sha256"] = followups.file_sha256(self.output / "records/6633.json")
        frozen["record_logical_sha256"] = logical(record)
        guards = {r: followups.file_sha256(self.output / r) for r in frozen["source_references"]}
        original, row = audit["selected"][0], audit["reviewed"][0]
        refs = frozen["source_references"]
        original.update(original_source_snapshot_sha256={r: guards[r] for r in refs[:2]},
                        original_historical_source_snapshot_sha256={r: guards[r] for r in refs[2:4]},
                        original_attempt_archive_sha256={r: guards[r] for r in refs[4:]})
        row.update(record_sha256_after_review=frozen["record_sha256"],
                   reviewed_at=record["manual_review"]["reviewed_at"])
        self.save(frozen["audit_path"], audit)
        frozen["audit_sha256"] = followups.file_sha256(self.output / frozen["audit_path"])
        packet.update(closed_audit_part_sha256=frozen["audit_sha256"],
                      source_record_sha256=frozen["record_sha256"], source_record_logical_sha256=frozen["record_logical_sha256"],
                      recursive_source_and_archive_sha256=guards,
                      source_audit_company_row_exact=copy.deepcopy(row), source_audit_company_row_sha256=logical(row))
        binding = packet["finite_discovery_proposals"][0]
        binding.update(source_record_sha256=frozen["record_sha256"], source_audit_part_sha256=frozen["audit_sha256"],
                       source_sha256=guards[refs[0]], parent_snapshot_sha256=guards[refs[0]])
        self.save(frozen["path"], packet)
        frozen["sha256"] = followups.file_sha256(self.output / frozen["path"])

    def test_named_current_issuer_plan_one_exact_target_preserves_observed_history(self):
        original = self.named_current_issuer_fixture()
        frozen = followups.FINITE_REVIEWED_AUTHORITIES["6633"]
        before = {str(p.relative_to(self.output)): p.read_bytes() for p in self.output.rglob("*.json")}
        with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")), \
                patch.object(self.research, "write_json", side_effect=AssertionError("write prohibited")), redirect_stdout(io.StringIO()):
            self.assertEqual(0, followups.main(["--output", str(self.output), "--plan-only", "--only-codes", "6633"]))
            plan = followups.build_plan(self.output, only_codes=["6633"])
        self.assertEqual((1, 1), (plan["selected_company_count"], plan["selected_url_count"]))
        task, = plan["selected"]
        proof = task["identity_discovery_proof"]
        self.assertEqual(("https://www.cgshd.co.jp/", "issuer_identity_discovery", 4, False),
                         (task["url"], task["purpose"], task["priority"], task["explicit_ir_link"]))
        self.assertEqual("reviewed_named_current_issuer_site_discovery", proof["kind"])
        self.assertEqual(41, proof["source_link_index"])
        self.assertEqual(set(frozen["source_references"]), set(proof["finite_saved_source_guards"]))
        for key in ("current_issuer_identity_verified", "IR_channel_verified", "IR_purpose_verified",
                    "current_issuer_reception_verified", "actual_form_fields_verified"):
            self.assertIs(False, proof[key])
        self.assertNotEqual(original["company_name"], original["discovery"]["seed_company_name"])
        self.assertEqual("name_or_security_code_observed", original["identity_status"])
        self.assertEqual(before, {str(p.relative_to(self.output)): p.read_bytes() for p in self.output.rglob("*.json")})

    def test_named_current_issuer_missing_or_changed_dependencies_never_generic_fallback(self):
        for damage in ("authority_missing", "authority_changed", "source_changed", "history_changed",
                       "archive_changed", "audit_changed", "record_changed", "registration_missing"):
            with self.subTest(damage=damage):
                self.named_current_issuer_fixture()
                frozen = followups.FINITE_REVIEWED_AUTHORITIES["6633"]
                reference = {"authority_missing": frozen["path"], "authority_changed": frozen["path"],
                             "source_changed": frozen["source_references"][0], "history_changed": frozen["source_references"][2],
                             "archive_changed": frozen["source_references"][4], "audit_changed": frozen["audit_path"],
                             "record_changed": "records/6633.json"}.get(damage)
                if damage == "authority_missing":
                    (self.output / reference).unlink()
                elif reference:
                    value = followups.read_json(self.output / reference)
                    value["changed"] = True
                    self.save(reference, value)
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                    if damage == "registration_missing":
                        entry = followups.FINITE_REVIEWED_AUTHORITIES.pop("6633")
                        try:
                            self.assertEqual([], followups.build_plan(self.output, only_codes=["6633"])["selected"])
                        finally:
                            followups.FINITE_REVIEWED_AUTHORITIES["6633"] = entry
                    else:
                        self.assertEqual([], followups.build_plan(self.output, only_codes=["6633"])["selected"])

    def test_named_current_issuer_semantic_negatives_are_bound_to_exact_source_and_history(self):
        route = followups.FINITE_REVIEWED_ROUTES["6633"][0]
        damages = [
            ("binding", "source_link_index", True), ("binding", "source_link_index", "41"),
            ("binding", "source_link_index", 41.0), ("binding", "source_link_index", 40),
            ("binding", "raw_href", route["target_url"] + "?ir=1"),
            ("binding", "url", route["target_url"] + "?ir=1"),
            ("binding", "source_snapshot", "evidence/9999/01.json"),
            ("binding", "field_path", "links.40"), ("binding", "raw_href_field_path", "links.41.url"),
            ("binding", "source_record_candidate_path", "manual_followup_candidates.1"),
            ("binding", "source_record_evidence_path", "evidence.0"),
            ("binding", "purpose", "ir_contact_followup"), ("binding", "method", "POST"),
            ("authority", "approved_by", None), ("authority", "maximum_candidate_count", True),
            ("authority", "secondary_ir_route_candidate_present", True),
            ("authority", "source_record_initial_identity_status_and_matches_are_immutable_history", False),
            ("authority", "authority_recorded_at_utc", "2026-10-11T19:00:00+00:00"),
            ("audit", "status", "running"), ("audit", "pending_company_count", 1),
            ("audit", "pending_validation", ["6633"]), ("audit", "completed_at", "2026-10-11T21:06:13"),
            ("record", "company_name", "Ｃ＆Ｇシステムズ"), ("record", "official_url", "https://www.cgshd.co.jp/"),
            ("record", "identity_status", "issuer_unverified"), ("record", "identity_matches", []),
            ("record", "manual_review_required", True), ("record", "channels", ["form"]),
            ("record", "conditions", ["原条件"]), ("record", "evidence", []),
            ("record", "previous_attempts", [True]),
            ("page", "security_code", "9999"), ("page", "requested_url", route["parent_url"] + "?legacy=1"),
            ("page", "http_status", 403), ("page", "http_get_attempted", False),
            ("page", "text", route["quote"] * 2), ("page", "text", "IRお問い合わせ"),
            ("page", "http_get_completed_at", "2026-10-11T21:00:00+00:00"),
            ("page", "http_get_started_at", "2026-10-11T18:32:52"),
            ("archive", "security_code", "9999"), ("archive", "previous_attempts", [False]),
            ("history", "security_code", "9999"),
        ]
        damages += [("binding", key, True) for key in (
            "IR_channel_verified", "IR_purpose_verified", "current_issuer_reception_verified",
            "current_issuer_identity_verified", "financial_ir_reception_verified", "actual_form_fields_verified",
            "old_form_or_conditions_inherited", "legal_migration_or_split_or_date_inferred", "raw_url_normalized")]
        for location, key, value in damages:
            with self.subTest(location=location, key=key, value=value):
                self.named_current_issuer_fixture()
                frozen = followups.FINITE_REVIEWED_AUTHORITIES["6633"]
                ref = {"binding": frozen["path"], "authority": frozen["path"], "audit": frozen["audit_path"],
                       "record": "records/6633.json", "page": frozen["source_references"][0],
                       "archive": frozen["source_references"][5], "history": frozen["source_references"][2]}[location]
                data = followups.read_json(self.output / ref)
                if location == "binding":
                    data["finite_discovery_proposals"][0][key] = value
                else:
                    data[key] = value
                self.save(ref, data)
                self.refreeze_named_current_issuer_fixture()
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                    self.assertEqual([], followups.build_plan(self.output, only_codes=["6633"])["selected"])

    def test_named_current_issuer_recursive_graph_and_physical_bounds_fail_closed(self):
        for damage in ("extra_source_snapshot", "nonstring_archive", "foreign_archive", "source_symlink_foreign",
                       "source_dir_symlink_foreign", "history_symlink", "archive_symlink", "authority_symlink",
                       "audit_symlink", "record_symlink", "source_symlink_external"):
            with self.subTest(damage=damage):
                self.named_current_issuer_fixture()
                frozen = followups.FINITE_REVIEWED_AUTHORITIES["6633"]
                if damage in ("extra_source_snapshot", "nonstring_archive", "foreign_archive"):
                    record = followups.read_json(self.output / "records/6633.json")
                    if damage == "extra_source_snapshot":
                        record["hidden_unbound_reference"] = {"source_snapshot": "evidence/9999/extra.json"}
                    elif damage == "nonstring_archive":
                        record["previous_attempts"] = [None]
                    else:
                        ref = "attempts/9999/past.json"
                        self.save(ref, followups.read_json(self.output / frozen["source_references"][4]))
                        record["previous_attempts"] = [ref]
                    self.save("records/6633.json", record)
                    self.refreeze_named_current_issuer_fixture()
                elif damage == "source_dir_symlink_foreign":
                    import shutil
                    path = self.output / "evidence/6633"
                    other = self.output / "evidence/9999"
                    shutil.move(str(path), str(other))
                    path.symlink_to(other, target_is_directory=True)
                else:
                    ref = {"history_symlink": frozen["source_references"][2], "archive_symlink": frozen["source_references"][4],
                           "authority_symlink": frozen["path"], "audit_symlink": frozen["audit_path"],
                           "record_symlink": "records/6633.json"}.get(damage, frozen["source_references"][0])
                    path = self.output / ref
                    other = Path(self.temporary.name) / "external.json" if damage == "source_symlink_external" else self.output / "evidence/9999/alias.json"
                    other.parent.mkdir(parents=True, exist_ok=True)
                    other.write_bytes(path.read_bytes())
                    path.unlink()
                    path.symlink_to(other)
                with patch.object(self.research.requests, "get", side_effect=AssertionError("GET prohibited")):
                    self.assertEqual([], followups.build_plan(self.output, only_codes=["6633"])["selected"])

    def stop_named_current_issuer_run(self):
        original = self.named_current_issuer_fixture()
        plan = followups.build_plan(self.output, only_codes=["6633"])
        self.assertEqual(1, len(plan["selected"]))
        state_path, calls = self.output / "named-stop.json", []

        def reply(url, **kwargs):
            calls.append(url)
            if url == followups.PREFLIGHT:
                return self.response(url, 200, "新規上場")
            if url.endswith("/robots.txt"):
                return self.response(url, 404, "")
            return self.response(url, 503, "Invalid argument|remote address:envoy://cloudflare_https_tunnel/")

        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(2, followups.collect(self.output, state_path, plan, 1000, 0.25))
        return original, plan, state_path, calls

    def test_named_current_issuer_healthy_dispatch_never_promotes_intake_or_identity(self):
        original = self.named_current_issuer_fixture()
        plan = followups.build_plan(self.output, only_codes=["6633"])
        state_path, calls = self.output / "named-healthy.json", []

        def reply(url, **kwargs):
            calls.append(url)
            if url == followups.PREFLIGHT:
                return self.response(url, 200, "新規上場")
            if url.endswith("/robots.txt"):
                return self.response(url, 404, "")
            self.assertEqual("https://www.cgshd.co.jp/", url)
            return self.response(url, 200, "<form><input type='email'><textarea name='question'></textarea></form>IRお問い合わせ")

        clock, http = self.network(reply)
        with clock, http:
            self.assertEqual(0, followups.collect(self.output, state_path, plan, 1000, 0.25))
        state = followups.read_json(state_path)
        saved = followups.read_json(self.output / "records/6633.json")
        self.assertEqual([followups.PREFLIGHT, "https://www.cgshd.co.jp/robots.txt", "https://www.cgshd.co.jp/"], calls)
        self.assertEqual(len(calls), state["http_get_attempt_count"])
        self.assertEqual(("completed", [], 1), (state["status"], state["todo"], len(state["done"])))
        for key in ("investigation_status", "verification_level", "identity_status", "identity_matches",
                    "individual_access", "channels", "contact_url", "public_ir_emails", "evidence", "conditions"):
            self.assertEqual(original[key], saved[key], key)
        self.assertIs(True, saved["manual_review_required"])
        with patch.object(self.research.requests, "get", side_effect=AssertionError("completed state may not fetch")):
            self.assertEqual(0, followups.collect(self.output, state_path, plan, 1000, 0.25))

    def test_named_current_issuer_resume_uses_exact_own_archive_without_generic_plan(self):
        original, plan, state_path, first_calls = self.stop_named_current_issuer_run()
        before = followups.read_json(state_path)
        self.assertEqual([], followups.build_plan(self.output, only_codes=["6633"])["selected"])
        self.assertEqual(1, len(before["todo"]))
        lineage = before["identity_record_lineage"]["6633"]
        self.assertEqual(followups.FINITE_REVIEWED_AUTHORITIES["6633"]["record_sha256"],
                         followups.file_sha256(self.output / lineage["original_record_archive"]))
        calls = []

        def reply(url, **kwargs):
            calls.append(url)
            if url == followups.PREFLIGHT:
                return self.response(url, 200, "新規上場")
            if url.endswith("/robots.txt"):
                return self.response(url, 404, "")
            return self.response(url, 200, "CGSホールディングス IR")

        clock, http = self.network(reply)
        with clock, http, redirect_stdout(io.StringIO()):
            self.assertEqual(0, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", "6633"]))
        after = followups.read_json(state_path)
        self.assertEqual("completed", after["status"])
        self.assertEqual(len(first_calls) + len(calls), after["http_get_attempt_count"])
        self.assertEqual(plan["selected"], after["selected"])
        saved = followups.read_json(self.output / "records/6633.json")
        for key in ("identity_status", "identity_matches", "investigation_status", "channels", "public_ir_emails", "evidence", "conditions"):
            self.assertEqual(original[key], saved[key], key)

    def test_named_current_issuer_fresh_robots_and_site_denials_respected(self):
        for kind in ("robots_disallow", "robots_tls_503", "robots_429", "target_403", "target_429"):
            with self.subTest(kind=kind):
                original = self.named_current_issuer_fixture()
                plan = followups.build_plan(self.output, only_codes=["6633"])
                state_path, calls = self.output / "named-site-denial.json", []

                def reply(url, **kwargs):
                    calls.append(url)
                    if url == followups.PREFLIGHT:
                        return self.response(url, 200, "新規上場")
                    if url.endswith("/robots.txt"):
                        if kind == "robots_disallow":
                            return self.response(url, 200, "User-agent: *\nDisallow: /\n",
                                                 {"Content-Type": "text/plain; charset=utf-8"})
                        if kind == "robots_tls_503":
                            return self.response(url, 503, "CERTIFICATE_VERIFY_FAILED")
                        if kind == "robots_429":
                            return self.response(url, 429, "rate limited", {"Retry-After": "900"})
                        return self.response(url, 404, "")
                    self.assertIn(kind, ("target_403", "target_429"), "robots denial must stop before body GET")
                    return self.response(url, 403 if kind == "target_403" else 429, "site denial", {"Retry-After": "900"})

                clock, http = self.network(reply)
                with clock, http:
                    followups.collect(self.output, state_path, plan, 1000, 0.25)
                state = followups.read_json(state_path)
                self.assertEqual([followups.PREFLIGHT, "https://www.cgshd.co.jp/robots.txt"]
                                 + ([] if kind.startswith("robots_") else ["https://www.cgshd.co.jp/"]), calls)
                self.assertEqual((len(calls), 0.25), (state["http_get_attempt_count"], state["global_rps"]))
                if kind.endswith("429"):
                    # This finite run has one task. The observation is done;
                    # completed never asserts successful issuer/IR discovery.
                    self.assertEqual(("completed", 1, 1),
                                     (state["status"], state["http_429_count"], len(state["done"])))
                saved = followups.read_json(self.output / "records/6633.json")
                for key in ("identity_status", "identity_matches", "investigation_status", "channels", "public_ir_emails", "evidence", "conditions"):
                    self.assertEqual(original[key], saved[key], key)

    def test_named_current_issuer_dependency_races_during_preflight_stop_before_target(self):
        for damage in ("source", "history", "archive", "authority", "audit", "record", "source_symlink", "authority_symlink", "record_symlink"):
            with self.subTest(damage=damage):
                self.named_current_issuer_fixture()
                plan = followups.build_plan(self.output, only_codes=["6633"])
                frozen = followups.FINITE_REVIEWED_AUTHORITIES["6633"]
                ref = {"source": frozen["source_references"][0], "history": frozen["source_references"][2],
                       "archive": frozen["source_references"][4], "authority": frozen["path"], "audit": frozen["audit_path"],
                       "record": "records/6633.json", "source_symlink": frozen["source_references"][0],
                       "authority_symlink": frozen["path"], "record_symlink": "records/6633.json"}[damage]
                calls, state_path = [], self.output / "named-race.json"

                def reply(url, **kwargs):
                    calls.append(url)
                    self.assertEqual(followups.PREFLIGHT, url)
                    path = self.output / ref
                    if damage.endswith("symlink"):
                        other = self.output / "evidence/9999/preflight-alias.json"
                        other.parent.mkdir(parents=True, exist_ok=True)
                        other.write_bytes(path.read_bytes()); path.unlink(); path.symlink_to(other)
                    else:
                        value = followups.read_json(path); value["changed_during_preflight"] = True; self.save(ref, value)
                    return self.response(url, 200, "新規上場")

                clock, http = self.network(reply)
                with clock, http:
                    self.assertEqual(2, followups.collect(self.output, state_path, plan, 1000, 0.25))
                state = followups.read_json(state_path)
                self.assertEqual([followups.PREFLIGHT], calls)
                self.assertEqual(("identity_source_changed_stopped", [], plan["selected"], 1),
                                 (state["status"], state["done"], state["todo"], state["http_get_attempt_count"]))

    def test_named_current_issuer_own_archive_race_during_resume_preflight_keeps_pending(self):
        for damage in ("changed", "missing", "symlink_other_issuer"):
            with self.subTest(damage=damage):
                _, _, state_path, _ = self.stop_named_current_issuer_run()
                before = followups.read_json(state_path)
                reference = before["identity_record_lineage"]["6633"]["original_record_archive"]
                path = self.output / reference
                current_bytes = (self.output / "records/6633.json").read_bytes()
                calls = []

                def reply(url, **kwargs):
                    calls.append(url)
                    self.assertEqual(followups.PREFLIGHT, url)
                    if damage == "changed":
                        value = followups.read_json(path); value["changed"] = True; self.save(reference, value)
                    elif damage == "missing":
                        path.unlink()
                    else:
                        other = self.output / "attempts/9999/alias.json"
                        other.parent.mkdir(parents=True, exist_ok=True)
                        other.write_bytes(path.read_bytes()); path.unlink(); path.symlink_to(other)
                    return self.response(url, 200, "新規上場")

                clock, http = self.network(reply)
                with clock, http, redirect_stdout(io.StringIO()):
                    self.assertEqual(2, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", "6633"]))
                after = followups.read_json(state_path)
                self.assertEqual([followups.PREFLIGHT], calls)
                self.assertEqual("identity_source_changed_stopped", after["status"])
                self.assertEqual((before["done"], before["todo"]), (after["done"], after["todo"]))
                self.assertEqual(before["http_get_attempt_count"] + 1, after["http_get_attempt_count"])
                self.assertEqual(current_bytes, (self.output / "records/6633.json").read_bytes())

    def test_named_current_issuer_invalid_own_archive_lineage_stops_before_preflight(self):
        for damage in ("wrong_issuer", "absolute", "traversal", "nonstring", "missing", "symlink"):
            with self.subTest(damage=damage):
                _, _, state_path, _ = self.stop_named_current_issuer_run()
                state = followups.read_json(state_path)
                lineage = state["identity_record_lineage"]["6633"]
                original_ref = lineage["original_record_archive"]
                alias = self.output / "attempts/9999/alias.json"
                alias.parent.mkdir(parents=True, exist_ok=True)
                alias.write_bytes((self.output / original_ref).read_bytes())
                lineage["original_record_archive"] = {
                    "wrong_issuer": "attempts/9999/alias.json", "absolute": str(self.output / original_ref),
                    "traversal": "attempts/6633/../9999/alias.json", "nonstring": True, "missing": None,
                    "symlink": original_ref}[damage]
                if damage == "symlink":
                    path = self.output / original_ref; path.unlink(); path.symlink_to(alias)
                self.research.write_json(state_path, state)
                current_bytes = (self.output / "records/6633.json").read_bytes()
                with patch.object(self.research.requests, "get", side_effect=AssertionError("no preflight permitted")), redirect_stdout(io.StringIO()):
                    self.assertEqual(2, followups.main(["--output", str(self.output), "--state", str(state_path), "--only-codes", "6633"]))
                after = followups.read_json(state_path)
                self.assertEqual((state["done"], state["todo"], state["http_get_attempt_count"]),
                                 (after["done"], after["todo"], after["http_get_attempt_count"]))
                self.assertIn(after["status"], ("identity_source_changed_stopped", "identity_resume_proof_missing_stopped"))
                self.assertEqual(current_bytes, (self.output / "records/6633.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
