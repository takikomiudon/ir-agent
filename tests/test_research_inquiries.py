"""Synthetic pre-thesis inquiry persistence; no network or operational DB."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import tempfile
import unittest

from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.models import json_text
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.research_inquiries import ResearchInquiries, SCHEMA
from ir_agent.store import Store


def at(minute, second=0):
    return datetime(2026, 10, 15, 10, minute, second, tzinfo=timezone.utc)


class ResearchInquiryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.store = Store(':memory:')
        self.addCleanup(self.store.close)
        self.store.connection.executescript(SCHEMA)
        self.harness = Harness(self.store)
        self.api = ResearchInquiries(self.store)
        self.harness.ingest({'schema_version': 1, 'companies': [
            {'id': 'synthetic', 'name': 'Synthetic company'}]}, now=at(0))
        self.source = self.add_source('public')
        p = self.root / 'case.json'
        p.write_text('Synthetic issue: which rate? Not an investment decision.', encoding='utf-8')
        ref = {'path': p.name, 'sha256': sha256(p.read_bytes()).hexdigest()}
        self.case_request = {'case_id': 'rate-case', 'company_id': 'synthetic',
            'issue_id': 'rate-definition', 'synthetic': True, 'enabled': True,
            'recorded_at': at(2).isoformat(), 'case_ref': ref, 'manifest_ref': ref,
            'management_review': None, 'bootstrap_reviews': []}
        QualitativeResearch(self.store).register_case(self.case_request, 0,
                                                     research_root=self.root, now=at(2))

    def add_source(self, identity, minute=0, **changes):
        value = {'id': identity, 'company_id': 'synthetic', 'title': 'Synthetic disclosure',
                 'url': 'https://example.invalid/disclosure', 'source_type': 'public_disclosure',
                 'retrieved_at': at(0).isoformat(), 'published_at': None,
                 'content': 'Synthetic public rate applies to the specified product.',
                 'metadata': {'synthetic': True}, 'requires_research': True}
        value.update(changes)
        self.harness.ingest({'schema_version': 1, 'sources': [value]}, now=at(minute))
        return self.store.source(identity)

    def binding(self, source=None, minute=3):
        s = source or self.source
        return {'reviewed_at': at(minute).isoformat(), 'reviewer': 'synthetic reviewer',
                'rationale': 'Public text does not identify the compared product series.',
                'sources': [{'source_id': s['id'], 'source_snapshot_sha256':
                    sha256(json_text(s).encode()).hexdigest(), 'scope': 'Synthetic paragraph only',
                    'basis_quote': s['content']}]}

    def inquiry(self, **changes):
        value = {'id': 'research-one', 'case_id': 'rate-case', 'issue_id': 'rate-definition',
                 'expected_case_version': 1, 'expected_config_revision': 1,
                 'created_at': at(4).isoformat(), 'topic': 'rate',
                 'question': 'Which public product series and comparison period?',
                 'already_answered': 'Product rates differ.',
                 'remaining_uncertainty': 'Same-series rate or composition effect?',
                 'branches': [
                     {'id': 'A', 'condition': 'Same-series change clarified publicly',
                      'comparison_note': 'Annotate the specified series only.'},
                     {'id': 'mixed', 'condition': 'More than one public component',
                      'comparison_note': 'Keep components separate without contribution estimates.'},
                     {'id': 'unresolved', 'condition': 'Ambiguous or no response',
                      'comparison_note': 'Comparison scope remains unresolved.'}],
                 'public_information_review': self.binding()}
        value.update(changes)
        return value

    def prepare(self):
        return self.api.add_inquiry(self.inquiry(), now=at(4))

    def receive(self):
        self.prepare()
        self.api.mark_sent('research-one', at(5).isoformat(), now=at(5))
        return self.api.add_reply({'id': 'research-reply', 'inquiry_id': 'research-one',
                                  'received_at': at(6).isoformat(),
                                  'raw_text': 'See the specified product series in the public paragraph.'}, now=at(7))

    def review(self, **changes):
        value = {'reply_id': 'research-reply', 'expected_version': 0, 'branch_id': 'A',
                 'basis_quote': 'specified product series', 'rationale': 'Public scope identified; assertion only.',
                 'recorded_at': at(8).isoformat(), 'information_status': 'public_clarification',
                 'public_information_review': self.binding(minute=7)}
        value.update(changes)
        return value

    def old_tables(self):
        tables = [r[0] for r in self.store.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'research_inquir%'")]
        return {t: sorted(repr(tuple(r)) for r in self.store.connection.execute('SELECT * FROM ' + t))
                for t in tables}

    def test_vertical_slice_without_thesis_preserves_all_old_tables_and_fixed_note(self):
        before = self.old_tables()
        self.receive()
        saved = self.api.add_review(self.review(), now=at(8))
        current = self.api.current_view('research-one', now=at(9))
        self.assertEqual(current['status'], 'comparison_note')
        self.assertEqual(current['comparison_note'], self.inquiry()['branches'][0]['comparison_note'])
        self.assertFalse(saved['financial_inputs_verified'])
        self.assertFalse(current['case_applied'])
        self.assertEqual(self.old_tables(), before)
        self.assertEqual(self.harness.inbox(), {'drafts': [], 'awaiting_replies': [], 'replies_for_review': []})

    def test_add_retry_retains_original_first_save_and_branch_changes_refused(self):
        saved = self.prepare()
        self.assertEqual(self.api.add_inquiry(self.inquiry(), now=at(10)), saved)
        changed = self.inquiry()
        changed['branches'][0]['comparison_note'] = 'Changed meaning'
        with self.assertRaises(ValueError): self.api.add_inquiry(changed, now=at(10))
        self.assertEqual(self.api.show_inquiry('research-one')['record'], saved)

    def test_strict_branches_reject_financial_actions_missing_unresolved_and_duplicate(self):
        for mode in ('valuation', 'action', 'duplicate', 'missing', 'extra'):
            value = self.inquiry()
            if mode in {'valuation', 'action'}: value['branches'][0][mode] = 'buy'
            elif mode == 'duplicate': value['branches'][1]['id'] = 'A'
            elif mode == 'missing': value['branches'].pop()
            else: value['financial_inputs_verified'] = True
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.api.add_inquiry(value, now=at(4))

    def test_missing_or_changed_public_proof_rejects_without_partial_record(self):
        for mode in ('missing', 'quote', 'hash', 'future'):
            value = self.inquiry()
            if mode == 'missing': del value['public_information_review']
            elif mode == 'quote': value['public_information_review']['sources'][0]['basis_quote'] = 'absent'
            elif mode == 'hash': value['public_information_review']['sources'][0]['source_snapshot_sha256'] = '0'*64
            else: value['public_information_review']['reviewed_at'] = at(5).isoformat()
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.api.add_inquiry(value, now=at(4))
        self.assertEqual(self.api.list_inquiries(), [])

    def test_late_saved_origin_cannot_be_backfilled_into_old_public_review(self):
        root = self.add_source('derived', minute=1,
                               metadata={'original_source_id': 'late-parent'})
        self.add_source('late-parent', minute=5)
        with self.assertRaises(ValueError):
            self.api.add_inquiry(self.inquiry(public_information_review=self.binding(root)), now=at(6))

    def test_cross_company_and_missing_origin_and_cycle_are_not_usable(self):
        self.harness.ingest({'schema_version': 1, 'companies': [{'id': 'other', 'name': 'Other'}]}, now=at(0))
        other = self.add_source('other-public', company_id='other')
        missing = self.add_source('missing-origin', metadata={'original_source_id': 'absent'})
        cyc = self.add_source('cycle', metadata={'original_source_id': 'cycle'})
        for s in (other, missing, cyc):
            with self.subTest(source=s['id']), self.assertRaises(ValueError):
                self.api.add_inquiry(self.inquiry(public_information_review=self.binding(s)), now=at(4))

    def test_duplicate_open_same_company_topic_against_research_and_old_questions(self):
        self.prepare()
        with self.assertRaises(ValueError): self.api.add_inquiry(self.inquiry(id='second'), now=at(4))
        self.api.close_inquiry('research-one', 'cancelled', now=at(5))
        self.store.connection.execute('INSERT INTO questions(id,company_id,topic,status,data) VALUES (?,?,?,?,?)',
                                     ('old-question', 'synthetic', 'rate', 'draft', '{}'))
        with self.assertRaises(ValueError): self.api.add_inquiry(self.inquiry(id='second'), now=at(6))

    def test_sent_record_retry_is_historical_and_changed_time_cannot_replace(self):
        self.prepare()
        sent = self.api.mark_sent('research-one', at(5).isoformat(), now=at(5))
        self.assertEqual(self.api.mark_sent('research-one', at(5).isoformat(), now=at(9)), sent)
        with self.assertRaises(ValueError): self.api.mark_sent('research-one', at(6).isoformat(), now=at(9))

    def test_sent_and_reply_future_or_inverse_times_rejected(self):
        self.prepare()
        for sent in (at(3), at(6)):
            with self.assertRaises(ValueError): self.api.mark_sent('research-one', sent.isoformat(), now=at(5))
        self.api.mark_sent('research-one', at(5).isoformat(), now=at(5))
        for received in (at(4), at(8)):
            with self.assertRaises(ValueError): self.api.add_reply(
                {'id': 'r', 'inquiry_id': 'research-one', 'received_at': received.isoformat(), 'raw_text': 'raw'}, now=at(7))

    def test_reply_requires_sent_immutable_and_unclear_by_default(self):
        self.prepare()
        value = {'id': 'r', 'inquiry_id': 'research-one', 'received_at': at(6).isoformat(), 'raw_text': 'raw'}
        with self.assertRaises(ValueError): self.api.add_reply(value, now=at(7))
        self.api.mark_sent('research-one', at(5).isoformat(), now=at(5))
        saved = self.api.add_reply(value, now=at(7))
        self.assertEqual(saved['request']['information_status'], 'unclear')
        self.assertEqual(self.api.add_reply(value, now=at(9)), saved)
        with self.assertRaises(ValueError): self.api.add_reply({**value, 'raw_text': 'different'}, now=at(9))
        with self.assertRaises(ValueError): self.api.add_reply({**value, 'id': 'r2', 'information_status': 'public_clarification'}, now=at(9))

    def test_case_and_files_stale_hold_and_do_not_block_historical_receipt(self):
        self.receive()
        saved = self.api.add_review(self.review(), now=at(8))
        self.case_request['recorded_at'] = at(9).isoformat()
        QualitativeResearch(self.store).register_case(self.case_request, 1, research_root=self.root, now=at(9))
        view = self.api.current_view('research-one', now=at(10))
        self.assertEqual(view['status'], 'held')
        self.assertIsNone(view['comparison_note'])
        self.assertEqual(self.api.add_review(self.review(), now=at(10)), saved)
        with self.assertRaises(ValueError): self.api.add_review(self.review(expected_version=1, recorded_at=at(10).isoformat()), now=at(10))
        self.api.add_reply({'id': 'late-reply', 'inquiry_id': 'research-one',
                            'received_at': at(10).isoformat(), 'raw_text': 'late actual receipt'}, now=at(10))

    def test_changed_case_file_holds_prepared_and_current_view(self):
        self.prepare()
        (self.root/'case.json').write_text('Changed case meaning', encoding='utf-8')
        with self.assertRaises(ValueError): self.api.mark_sent('research-one', at(5).isoformat(), now=at(5))
        self.assertIn('case_or_files_changed', self.api.current_view('research-one', now=at(6))['reason_codes'])

    def test_public_review_needs_quote_proof_and_fixed_branch(self):
        self.receive()
        for mode in ('quote', 'public', 'branch', 'extra'):
            value = self.review()
            if mode == 'quote': value['basis_quote'] = 'not in reply'
            elif mode == 'public': del value['public_information_review']
            elif mode == 'branch': value['branch_id'] = 'uncommitted'
            else: value['comparison_note'] = 'Caller forged effect'
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.api.add_review(value, now=at(8))

    def test_information_correction_appends_and_holds_current_without_mutating_history(self):
        self.receive()
        first = self.api.add_review(self.review(), now=at(8))
        corrected = self.review(expected_version=1, recorded_at=at(9).isoformat(),
                                information_status='potential_nonpublic', branch_id='unresolved')
        del corrected['public_information_review']
        second = self.api.add_review(corrected, now=at(9))
        view = self.api.current_view('research-one', now=at(10))
        self.assertIn('reply_information_held', view['reason_codes'])
        self.assertIsNone(view['comparison_note'])
        self.assertEqual(self.api.show_reply('research-reply')['reviews'], [first, second])
        self.assertEqual(self.api.add_review(self.review(), now=at(10)), first)

    def test_review_CAS_firstsave_and_timing(self):
        self.receive()
        first = self.api.add_review(self.review(), now=at(9))
        self.assertEqual(first['first_saved_at'], at(9).isoformat())
        for changes in ({'rationale': 'different'}, {'expected_version': 1, 'recorded_at': at(6).isoformat()},
                        {'expected_version': 1, 'recorded_at': at(8,30).isoformat()},
                        {'expected_version': 1, 'recorded_at': at(11).isoformat()}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.api.add_review(self.review(**changes), now=at(10))

    def test_no_response_not_an_answer_or_negative_investment_signal(self):
        self.prepare()
        with self.assertRaises(ValueError): self.api.close_inquiry('research-one', 'no_response', now=at(5))
        self.api.mark_sent('research-one', at(5).isoformat(), now=at(5))
        closed = self.api.close_inquiry('research-one', 'no_response', now=at(6))
        self.assertEqual(self.api.close_inquiry('research-one', 'no_response', now=at(7)), closed)
        view = self.api.current_view('research-one', now=at(7))
        self.assertEqual(view['branch_id'], 'unresolved')
        self.assertEqual(view['reason_codes'], ['no_response'])
        self.assertIsNone(view['comparison_note'])
        self.assertEqual(self.api.show_inquiry('research-one')['state']['status'], 'expired')

    def test_late_actual_reply_after_expiry_and_listing_stays_separate(self):
        self.prepare()
        self.api.mark_sent('research-one', at(5).isoformat(), now=at(5))
        self.api.close_inquiry('research-one', 'no_response', now=at(6))
        self.api.add_reply({'id': 'late', 'inquiry_id': 'research-one', 'received_at': at(7).isoformat(), 'raw_text': 'Late actual reply'}, now=at(8))
        self.assertEqual(self.api.list_inquiries()[0]['status'], 'answered')
        self.assertEqual(self.api.show_inquiry('research-one')['state']['closure_reason'], 'no_response')

    def test_current_view_checks_saved_boundary_and_reply_identity(self):
        self.receive()
        self.api.add_review(self.review(), now=at(8))
        self.assertIn('review_not_saved_at_boundary', self.api.current_view('research-one', now=at(7))['reason_codes'])
        other = self.inquiry(id='other-inquiry', topic='other')
        self.api.add_inquiry(other, now=at(8))
        with self.assertRaises(ValueError): self.api.current_view('other-inquiry', reply_id='research-reply', now=at(9))

    def test_nonpublic_correction_survives_stale_case_but_never_applies(self):
        self.receive()
        first = self.api.add_review(self.review(), now=at(8))
        (self.root/'case.json').write_text('Later changed file', encoding='utf-8')
        request = self.review(expected_version=1, information_status='potential_nonpublic',
                              recorded_at=at(9).isoformat(), branch_id='unresolved')
        del request['public_information_review']
        correction = self.api.add_review(request, now=at(9))
        self.assertEqual(correction['version'], 2)
        view = self.api.current_view('research-one', now=at(10))
        self.assertIn('case_or_files_changed', view['reason_codes'])
        self.assertIn('reply_information_held', view['reason_codes'])
        self.assertIsNone(view['comparison_note'])
        self.assertEqual(self.api.show_reply('research-reply')['reviews'][0], first)

    def test_new_receipts_cannot_rollback_global_subsystem_clock_but_retry_can_read_history(self):
        self.receive()
        first = self.api.add_review(self.review(), now=at(10))
        self.assertEqual(self.api.add_review(self.review(), now=at(10)), first)
        with self.assertRaises(ValueError): self.api.add_inquiry(self.inquiry(id='rolled', topic='other'), now=at(9))
        with self.assertRaises(ValueError): self.api.add_reply({'id': 'rolled-reply', 'inquiry_id': 'research-one',
            'received_at': at(6).isoformat(), 'raw_text': 'new actual raw'}, now=at(9))
        with self.assertRaises(ValueError): self.api.add_review(self.review(expected_version=1,
            recorded_at=at(9).isoformat()), now=at(9))

    def test_invalid_status_types_raise_valueerror_not_membership_typeerror(self):
        self.receive()
        for invalid in ([], {}, 3, None):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.api.add_review(self.review(information_status=invalid), now=at(8))

    def test_case_basis_source_hold_is_checked_separately_from_public_review_source(self):
        # S1 is already part of the case; the inquiry cites a separate S2.
        Intake(self.store).queue(at(1).isoformat(), now=at(1))
        job = self.harness.claim('synthetic-classifier', now=at(1,1), measurement_synthetic=True)
        completed = self.harness.complete(job['id'], 'synthetic-classifier', {'classifications': [{
            'source_id': self.source['id'], 'expected_version': 0, 'kind': 'other',
            'financial_content': None, 'basis_quote': self.source['content'],
            'rationale': 'Synthetic source kind; financial meaning remains unverified.'}]}, now=at(1,2))
        native = sha256(json_text(self.source).encode()).hexdigest()
        p = self.root/'read.json'
        p.write_text(self.source['id']+' '+native, encoding='utf-8')
        request = deepcopy(self.case_request)
        request.update(recorded_at=at(3).isoformat(), bootstrap_reviews=[{
            'source_id': self.source['id'], 'source_snapshot_sha256': native,
            'reviewed_at': at(2,1).isoformat(), 'review_ref': {
                'path': p.name, 'sha256': sha256(p.read_bytes()).hexdigest()}}])
        QualitativeResearch(self.store).register_case(request, 1, research_root=self.root, now=at(3))
        s2 = self.add_source('separate-public', minute=3)
        inquiry = self.inquiry(expected_case_version=2, expected_config_revision=2,
                               public_information_review=self.binding(s2, minute=4))
        self.api.add_inquiry(inquiry, now=at(4))
        self.api.mark_sent('research-one', at(5).isoformat(), now=at(5))
        self.api.add_reply({'id': 'research-reply', 'inquiry_id': 'research-one',
                            'received_at': at(6).isoformat(), 'raw_text': 'specified product series'}, now=at(7))
        self.api.add_review(self.review(public_information_review=self.binding(s2, minute=7)), now=at(8))
        self.assertEqual(self.api.current_view('research-one', now=at(8))['status'], 'comparison_note')
        # Simulate an append-only classification revision in this synthetic DB.
        prior = deepcopy(completed['result']['classifications'][0])
        prior.update(version=2, kind='unresolved', recorded_at=at(9).isoformat(), first_saved_at=at(9).isoformat())
        self.store.connection.execute('INSERT INTO source_classifications VALUES (?,?,?,?,?)',
            (self.source['id'], 2, json_text(prior), at(9).isoformat(), job['id']))
        view = self.api.current_view('research-one', now=at(10))
        self.assertEqual(view['status'], 'held')
        self.assertIsNone(view['comparison_note'])
        self.assertIn('case_or_files_changed', view['reason_codes'])

    def test_real_case_rejects_synthetic_public_root_and_parent(self):
        real = deepcopy(self.case_request)
        real.update(case_id='real-case', synthetic=False, recorded_at=at(3).isoformat())
        QualitativeResearch(self.store).register_case(real, 0, research_root=self.root, now=at(3))
        derived = self.add_source('ordinary-root', minute=3,
                                  metadata={'original_source_id': self.source['id']})
        for s in (self.source, derived):
            with self.subTest(source=s['id']), self.assertRaises(ValueError):
                self.api.add_inquiry(self.inquiry(case_id='real-case',
                    public_information_review=self.binding(s, minute=4)), now=at(4))

    def test_synthetic_case_can_use_source_without_demo_flag_like_existing_monitor(self):
        plain = self.add_source('plain', metadata={})
        self.api.add_inquiry(self.inquiry(public_information_review=self.binding(plain)), now=at(4))
        self.assertEqual(self.api.list_inquiries()[0]['status'], 'draft')


if __name__ == '__main__':
    unittest.main()
