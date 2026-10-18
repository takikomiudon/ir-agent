"""File-only proposed v33; no DB/Store/network/normalization or final index write."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OLD = ROOT / 'research/ir-case-studies-2026-10-15/disclosed-fact-index-v32.json'
OLD_SHA = 'e286df49362595e297db5adaa2c6381bc9334ecae1ac2b6b1a2bb38f6d0070cc'
BUNDLE = HERE.parent / 'normalized-bundle.json'
BUNDLE_SHA = '6d678bd2209ec9f0a90a0f7545ca612a3c51844a67a3116ee3e7440aeede465f'
ORIGINAL_ID = 'case-public:1be0616e6cd3190c24777d4fc73d7e98da23fef874d4049aa38b667dbefdbdea'
DERIVED_ID = 'disclosed-facts:145cc30798194e4ec4e26d62eec8fa408c9c9e94125a587653d5cb19cc3664e5'


def load(path):
    return json.loads(path.read_bytes())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as output:
        output.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def resolved(entry, fact):
    return fact.get('source_id', entry['source_id'])


def main():
    outputs = ('proposed-index-v33.json', 'expected-diff.json', 'validation.json', 'manifest.json')
    assert not any((HERE / name).exists() for name in outputs)
    pins = load(HERE / 'input-pins.json')
    assert all(digest(ROOT / path) == wanted for path, wanted in pins.items())
    assert digest(OLD) == OLD_SHA and digest(BUNDLE) == BUNDLE_SHA
    old = load(OLD)
    assert len(old['companies']) == 36 and old['fact_count'] == 171
    assert sum(len(e['facts']) for e in old['companies']) == 171
    original, derived = load(BUNDLE)['sources']
    assert (original['id'], derived['id']) == (ORIGINAL_ID, DERIVED_ID)
    accepted = load(HERE.parent / 'parent-acceptance.json')
    assert accepted['status'] == 'accepted_nine_direct_disclosed_facts_file_only'
    assert accepted['bundle_SHA'] == BUNDLE_SHA and accepted['derived_source_ID'] == DERIVED_ID
    assert load(HERE.parent / 'normalization-input.json')['source'] == original
    prior_replay = load(HERE.parent / 'reproduction.log')
    assert prior_replay['status'] == 'reproduced_nine_direct_display_tokens_file_only'
    assert prior_replay['same_now_whole_bundle_and_ID_exact']
    facts = json.loads(derived['content'])['facts']
    assert len(facts) == 9 and [f['value'] for f in facts] == [
        '19483000000', '2205000000', '1546000000', '112500000000', '12200000000',
        '9250000000', '59.78', '357.49', '144.00']
    assert all(f['source_id'] == f['original_source_id'] == ORIGINAL_ID for f in facts)
    assert all(not f['financial_inputs_verified'] and not f['scope']['model_or_policy_adopted']
               and not f['scope']['October_current_guidance_or_share_basis_verified'] for f in facts)
    dps = facts[-1]
    assert dps['period']['start_date'] is dps['period']['end_date'] is dps['period']['dividend_record_date'] is None
    assert dps['scope']['accounting_basis'] is dps['scope']['consolidation_scope'] is None
    assert not dps['scope']['investor_DDM_dividend_column_adopted']
    assert dps['scope']['annual_total_not_computed'] and dps['location']['raw_token_source_character_start'] == 3330
    selection = load(HERE.parents[1] / 'initial-public-review-2026-10-16/selection.json')
    assert selection['selected_code'] == selection['selected_csv_row']['security_code'] == '1975'
    assert selection['DB']['company_snapshot']['id'] == 'jp:1975'
    entry = {'artifact': str(BUNDLE.relative_to(ROOT)), 'artifact_sha256': BUNDLE_SHA,
        'company_id': 'jp:1975', 'contact_catalog_member': True,
        'derived_retrieved_at': derived['retrieved_at'],
        'derived_source_imported_into_actual_database': False,
        # Raw fact.source_id binds the primary quote; it is not an index override.
        'facts': [{key: deepcopy(f[key]) for key in ('id', 'concept', 'kind', 'period', 'scope', 'unit', 'value')}
                  for f in facts],
        'original_retrieved_at': original['retrieved_at'], 'original_source_id': ORIGINAL_ID,
        'source_id': DERIVED_ID}
    value = deepcopy(old)
    value['companies'].append(entry)
    assert value['companies'][:36] == old['companies']
    assert all(resolved(entry, f) == DERIVED_ID and 'source_id' not in f for f in entry['facts'])
    flattened = [(e, f) for e in value['companies'] for f in e['facts']]
    counts = {'unique_companies': len({e['company_id'] for e in value['companies']}),
        'parent_entries': len(value['companies']), 'facts': len(flattened),
        'resolved_derived_sources': len({resolved(e, f) for e, f in flattened}),
        'company_original_pairs': len({(e['company_id'], f.get('original_source_id', e['original_source_id']))
                                       for e, f in flattened})}
    assert counts == {'unique_companies': 24, 'parent_entries': 37, 'facts': 180,
                      'resolved_derived_sources': 39, 'company_original_pairs': 30}
    assert len({f['id'] for _, f in flattened}) == 180
    assert not any(e['company_id'] == 'jp:1975' for e in old['companies'])
    now = datetime.now(timezone.utc).isoformat()
    value.update(recorded_at=now, previous_index=str(OLD.relative_to(ROOT)), previous_index_sha256=OLD_SHA,
        fact_count=180, company_source_entry_count=37, unique_company_count=24,
        unique_derived_source_count=39, unique_original_company_source_pair_count=30)
    # Keep the old observed DB snapshot verbatim; it is not a current v33 attestation.
    assert value['actual_research_source_connections'] == old['actual_research_source_connections']
    value['candidate_connection_state'] = {'stage': 'file_only_proposal_before_1975_actual_intake',
        'recorded_at': now, 'DB_connection_performed': False, '1975_actual_registration_verified': False,
        'new_derived_source_actual_first_saved_at': None,
        'inherited_actual_connections_are_v32_historical_snapshot_only': True,
        'current_total_connected_or_unconnected_counts_not_recomputed': True,
        'finalization_requires_separate_root_instruction_and_actual_receipts_RO_verification': True}
    value['layout_note'] = ('PROPOSAL ONLY: 37 parents resolve to 39 derived sources and 180 facts across '
        '24 companies/30 company-original pairs. New1975 entry remains file-only. '
        'actual_research_source_connections is the unchanged historical v32 observation, not current v33 DB coverage. '
        'No new database coverage or future registration asserted; no financial adoption.')
    value['limitations'].append('1975 nine direct Aug4 issuer tokens retain Q1 actual sales/OP/parent NI/basic EPS '
        'and dated FY sales/OP/parent NI/EPS/annual-total DPS forecasts. DPS calendar boundaries/record date/GAAP/'
        'consolidation stay null; prior total144/current interim72/final72 are separate cells, not added. '
        'May14 earnings-guidance reference is not applied to dividend or evidence of May original firstsave. '
        'Quarter-specific treatment/consolidation no-change statements are period-limited; historical shares are '
        'not current denominator. No October current forecast, DDM, normal profit or financial model adoption. '
        'Later explanation PDF is a separate source and is not included here.')
    value['revision_basis'] = {'kind': 'proposed_append_1975_nine_disclosed_facts_before_actual_intake',
        'added_fact_count': 9, 'added_parent_entry_count': 1,
        'prior_36_parent_entries_171_facts_all_fields_exact': True,
        'existing_per_fact_source_artifact_overrides_preserved': True,
        'actual_connection_not_checked_or_forecast': True, 'financial_model_adoption': False}
    save('proposed-index-v33.json', value)
    changed = [key for key in old if old[key] != value[key]]
    diff = {'status': 'expected_append_only_file_proposal_verified', 'old_index': str(OLD.relative_to(ROOT)),
        'old_sha256': OLD_SHA, 'proposed_sha256': digest(HERE / 'proposed-index-v33.json'),
        'old_parent_entries_all_fields_exact': 36, 'old_facts_all_fields_exact': 171,
        'added_parent_entries': 1, 'added_facts': 9, 'computed_counts': counts,
        'changed_top_level_keys': changed, 'new_top_level_keys': ['candidate_connection_state'],
        'old_actual_connection_snapshot_all_fields_exact': True,
        'new_index_fact_source_resolution': DERIVED_ID,
        'raw_fact_primary_source_binding_kept_in_original_bundle': ORIGINAL_ID,
        'final_index_written': False, 'current_DB_count_claims_created': False}
    save('expected-diff.json', diff)
    assert all(digest(ROOT / path) == wanted for path, wanted in pins.items())
    save('validation.json', {**diff, 'status': 'frozen_file_only_v33_proposal_pending_root_actual_phase',
        'recorded_at': now, 'all_frozen_dependency_pins_unchanged': True,
        'all_new_projected_fact_fields_exact': True, 'old_overrides_all_fields_exact': True,
        'DPS_nulls_total_cell_no_DDM_preserved': True, '9_unique_fact_IDs_added': True,
        'existing_accepted_generation_and_replay_receipts_checked_not_reexecuted': True,
        'new_primary_normalizer_calls': 0, 'new_replay_calls': 0,
        'DB_connections': 0, 'DB_writes': 0, 'GETs': 0, 'production_code_shared_docs_old_index_edits': 0,
        'financial_inputs_adopted': False})
    save('execution.log', {'status': 'proposal_build_succeeded_file_only', 'recorded_at': now,
        'command': '.venv/bin/python ' + str(Path(__file__).relative_to(ROOT)),
        'computed_counts': counts, 'proposed_sha256': digest(HERE / 'proposed-index-v33.json'),
        'final_index_written': False, 'DB_connections': 0, 'GETs': 0})
    save('manifest.json', {'status': 'frozen_proposed_index_only', 'recorded_at': now,
        'files': {path.name: {'sha256': digest(path), 'bytes': path.stat().st_size}
                  for path in sorted(HERE.iterdir()) if path.is_file()},
        'frozen_dependency_pins': pins, 'self_excluded': True,
        'finalization_deferred_until_root_actual_instruction': True,
        'DB_connections': 0, 'GETs': 0, 'financial_adoption': False})
    print(json.dumps({'status': 'file_only_proposed_v33_created_no_final_index',
        'proposed_sha256': digest(HERE / 'proposed-index-v33.json'),
        'validation_sha256': digest(HERE / 'validation.json'),
        'manifest_sha256': digest(HERE / 'manifest.json'), 'computed_counts': counts}))


if __name__ == '__main__':
    main()
