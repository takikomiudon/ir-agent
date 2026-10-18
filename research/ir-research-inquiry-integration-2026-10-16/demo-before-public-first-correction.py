#!/usr/bin/env python3
"""Synthetic research inquiry demo; temporary files only, no network or sending."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ir_agent.harness import Harness
from ir_agent.models import json_text, now_iso, timestamp
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.research_inquiries import ResearchInquiries
from ir_agent.store import Store


def reference(path):
    return {'path': path.name, 'sha256': sha256(path.read_bytes()).hexdigest()}


def public_review(source):
    return {'reviewed_at': now_iso(), 'reviewer': 'synthetic-demo-reviewer',
            'rationale': 'Synthetic public text identifies the product and comparison period; '
                         'this is a caller meaning review, not a financial conclusion.',
            'sources': [{'source_id': source['id'],
                         'source_snapshot_sha256': sha256(json_text(source).encode('utf-8')).hexdigest(),
                         'scope': 'The single synthetic public paragraph only.',
                         'basis_quote': source['content']}]}


def main():
    with tempfile.TemporaryDirectory(prefix='ir-research-inquiry-demo-') as directory:
        root = Path(directory)
        case_file = root / 'case.md'
        case_file.write_text('Synthetic research issue: distinguish a same-product rate '
                             'comparison from a change in product composition. No valuation.', encoding='utf-8')
        manifest = root / 'manifest.md'
        manifest.write_text('Synthetic demonstration only. No real company, external contact '
                            'or investment input is represented.', encoding='utf-8')
        store = Store(root / 'demo.sqlite3')
        try:
            harness = Harness(store)
            company_id = 'synthetic-inquiry-demo'
            harness.ingest({'schema_version': 1, 'companies': [
                {'id': company_id, 'name': 'Synthetic research inquiry demonstration', 'status': 'watch'}],
                'sources': [{'id': 'synthetic-public-definition', 'company_id': company_id,
                    'title': 'Synthetic public definition', 'source_type': 'public_disclosure',
                    'url': 'https://example.invalid/synthetic-public-definition',
                    'retrieved_at': now_iso(), 'published_at': None,
                    'content': 'Synthetic definition: the comparison covers product A in the '
                               'same evaluation category between FY1 and FY2.',
                    'metadata': {'synthetic': True}}]}, now=timestamp(now_iso()))
            source = store.source('synthetic-public-definition')
            registry = QualitativeResearch(store)
            case = registry.register_case({'case_id': 'synthetic-rate-case', 'company_id': company_id,
                'issue_id': 'synthetic-rate-comparison', 'synthetic': True, 'enabled': True,
                'recorded_at': now_iso(), 'case_ref': reference(case_file),
                'manifest_ref': reference(manifest), 'management_review': None,
                'bootstrap_reviews': []}, research_root=root)
            before_case = registry.show_case(case['case_id'])
            old_tables = ('theses', 'questions', 'replies', 'evaluations', 'jobs', 'sources',
                          'qualitative_case_versions')
            before_counts = {t: store.connection.execute('SELECT count(*) FROM ' + t).fetchone()[0]
                             for t in old_tables}
            api = ResearchInquiries(store)
            public = public_review(source)
            inquiry = api.add_inquiry({'id': 'synthetic-rate-inquiry', 'case_id': case['case_id'],
                'issue_id': 'synthetic-rate-comparison', 'expected_case_version': case['version'],
                'expected_config_revision': case['config_revision'], 'created_at': now_iso(),
                'topic': 'synthetic-rate-definition',
                'question': 'Which public product series and period does the comparison cover?',
                'already_answered': 'A public product definition exists.',
                'remaining_uncertainty': 'The comparative interpretation remains a research question.',
                'branches': [
                    {'id': 'A', 'condition': 'Public text identifies a same-product comparison.',
                     'comparison_note': 'Annotate only product A, the same category, and FY1–FY2; '
                                        'do not estimate profit or extrapolate to other products.'},
                    {'id': 'mixed', 'condition': 'The answer distinguishes multiple components.',
                     'comparison_note': 'Keep the stated components separate; contribution amounts remain unknown.'},
                    {'id': 'unresolved', 'condition': 'Ambiguous or no response.',
                     'comparison_note': 'The comparison scope remains unresolved.'}],
                'public_information_review': public})
            stages = [{'stage': 'prepared', 'status': api.show_inquiry(inquiry['id'])['state']['status']}]

            # Simulation only: no email, form, HTTP request or dispatch occurs.
            api.mark_sent(inquiry['id'], now_iso())
            stages.append({'stage': 'external_sent_record_simulation',
                           'status': api.show_inquiry(inquiry['id'])['state']['status']})
            reply = api.add_reply({'id': 'synthetic-rate-reply', 'inquiry_id': inquiry['id'],
                'received_at': now_iso(), 'raw_text': 'Synthetic reply: please see the public '
                    'definition of product A, the same category, and FY1–FY2.'})
            stages.append({'stage': 'received', 'information_status': reply['request']['information_status'],
                           'current_status': api.current_view(inquiry['id'])['status']})
            public = public_review(source)
            first = api.add_review({'reply_id': reply['id'], 'expected_version': 0, 'branch_id': 'A',
                'basis_quote': 'product A, the same category, and FY1–FY2',
                'rationale': 'Synthetic caller interpretation matches the limited public paragraph.',
                'recorded_at': now_iso(), 'information_status': 'public_clarification',
                'public_information_review': public})
            compared = api.current_view(inquiry['id'])
            stages.append({'stage': 'public_review', 'status': compared['status'],
                           'branch_id': compared['branch_id'], 'comparison_note': compared['comparison_note']})
            api.add_review({'reply_id': reply['id'], 'expected_version': 1, 'branch_id': 'unresolved',
                'basis_quote': 'Synthetic reply', 'rationale': 'Synthetic safety correction: the claimed '
                    'public status needs further verification. Keep the old review unchanged.',
                'recorded_at': now_iso(), 'information_status': 'potential_nonpublic'})
            held = api.current_view(inquiry['id'])
            history_unchanged = api.show_reply(reply['id'])['reviews'][0] == first
            stages.append({'stage': 'information_correction', 'status': held['status'],
                           'reason_codes': held['reason_codes'], 'comparison_note': held['comparison_note'],
                           'past_review_unchanged': history_unchanged})
            counts = {t: store.connection.execute('SELECT count(*) FROM ' + t).fetchone()[0]
                      for t in old_tables}
            assert counts == before_counts
            assert registry.show_case(case['case_id']) == before_case
            assert counts['theses'] == counts['questions'] == counts['replies'] == counts['evaluations'] == 0
            assert compared['status'] == 'comparison_note' and held['status'] == 'held'
            assert held['comparison_note'] is None and history_unchanged
            print(json_text({'synthetic': True, 'temporary_DB_and_files_only': True,
                'stages': stages, 'clock_semantics': {
                    'inquiry_created_at': inquiry['request']['created_at'],
                    'inquiry_first_saved_at': inquiry['first_saved_at'],
                    'claimed_dates_are_not_first_save_receipts': True},
                'case_head_unchanged': True, 'old_table_counts_unchanged': counts,
                'financial_inputs_verified': False, 'case_applied': False,
                'network_requests': 0, 'external_sends': 0}))
        finally:
            store.close()


if __name__ == '__main__':
    main()
