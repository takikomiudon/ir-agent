"""Append the three accepted artifacts; read the actual ledger without writes."""
import copy
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'research/ir-case-studies-2026-10-15'


def save(path, value):
    with path.open('x', encoding='utf8') as output:
        json.dump(value, output, ensure_ascii=False, sort_keys=True, indent=2)
        output.write('\n')


def main():
    old_path = BASE / 'disclosed-fact-index-v27.json'
    new_path = BASE / 'disclosed-fact-index-v28.json'
    assert not new_path.exists() and not (HERE / 'parent-acceptance.json').exists()
    old = json.loads(old_path.read_bytes())
    new = copy.deepcopy(old)
    db = ROOT / 'data/ir-research-2026-10-15.sqlite3'
    accepted = json.loads((HERE.parent / 'disclosed-fact-qualitative-review/parent-acceptance.json').read_bytes())
    assert sha256(db.read_bytes()).hexdigest() == accepted['database_main_sha256']
    clock = datetime.now(timezone.utc).isoformat()
    paths = ['1866/disclosed-facts-2026-10-16/normalized-bundle.json',
             '1870/disclosed-facts-2026-10-16/statement-normalized-bundle.json',
             '1870/disclosed-facts-2026-10-16/previous-guidance-normalized-bundle.json']
    with closing(sqlite3.connect(db.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        for relative in paths:
            path = BASE / relative
            original, derived = json.loads(path.read_bytes())['sources']
            facts = json.loads(derived['content'])['facts']
            # Normalized fact source_id binds its original quotation, whereas
            # the index parent source_id identifies the derived artifact.
            assert all(f['original_source_id'] == f['source_id'] == original['id'] for f in facts)
            for source in (original, derived):
                assert json.loads(connection.execute('SELECT data FROM sources WHERE id=?',
                    (source['id'],)).fetchone()[0]) == source
            new['companies'].append({
                'artifact': str(path.relative_to(ROOT)),
                'artifact_sha256': sha256(path.read_bytes()).hexdigest(),
                'company_id': derived['company_id'], 'contact_catalog_member': True,
                'derived_retrieved_at': derived['retrieved_at'],
                'derived_source_imported_into_actual_database': True,
                'facts': [{k: f[k] for k in ('id', 'concept', 'kind', 'period', 'scope', 'unit', 'value')}
                          for f in facts],
                'original_retrieved_at': original['retrieved_at'],
                'original_source_id': original['id'], 'source_id': derived['id']})
        assert new['companies'][:len(old['companies'])] == old['companies']
        facts = [(entry, fact) for entry in new['companies'] for fact in entry['facts']]
        assert len({fact['id'] for _, fact in facts}) == len(facts)
        sources = {fact.get('source_id', entry['source_id']) for entry, fact in facts}
        pairs = {(entry['company_id'], fact.get('original_source_id', entry['original_source_id']))
                 for entry, fact in facts}
        companies = {entry['company_id'] for entry in new['companies']}
        actual = {source for source in sources if connection.execute(
            'SELECT 1 FROM sources WHERE id=?', (source,)).fetchone()}
        actual_facts = sum(fact.get('source_id', entry['source_id']) in actual for entry, fact in facts)
        assert (len(companies), len(facts), len(new['companies']), len(sources), len(pairs), len(actual),
                actual_facts) == (20, 144, 32, 34, 25, 32, 137)
    new.update(recorded_at=clock, previous_index=str(old_path.relative_to(ROOT)),
        previous_index_sha256=sha256(old_path.read_bytes()).hexdigest(), fact_count=144,
        company_source_entry_count=32, unique_company_count=20, unique_derived_source_count=34,
        unique_original_company_source_pair_count=25)
    new['actual_research_source_connections'].update(
        actual_database_main_sha256=accepted['database_main_sha256'], database_snapshot_recorded_at=clock,
        database_source_count=164, connected_derived_source_count=32, connected_fact_count=137)
    new['actual_research_source_connections']['connection_receipts'] += [
        'research/ir-new-company-intake-2026-10-16/disclosed-fact-connection/actual-completion.json',
        'research/ir-new-company-intake-2026-10-16/disclosed-fact-qualitative-review/parent-acceptance.json']
    new['layout_note'] = ('32 parent entries resolve to 34 unique derived sources, 144 facts across '
        '20 companies/25 company-original pairs. 32 sources/137 facts are stored and classified '
        'in the actual research ledger; two out-of-scope sources/7 facts remain file-only. '
        'No financial input adoption.')
    new['limitations'].append('1866 and 1870 quarter actuals, annual guidance and prior guidance '
        'retain separate kinds, periods and forecast vintages. 1870 May12 guidance is observed '
        'retrospectively in the Aug7 presentation; exact calendar boundaries, accounting basis '
        'and rounding remain unknown for those three facts. Retrieval and first-save dates '
        'do not prove earlier market availability.')
    new['revision_basis'] = {'kind': 'append_1866_and_1870_fifteen_disclosed_facts',
        'added_fact_count': 15, 'added_parent_entry_count': 3,
        'prior_129_fact_values_periods_scope_and_29_parent_entries_exact': True,
        'financial_model_adoption': False}
    save(new_path, new)
    receipt = {'recorded_at': clock, 'status': 'accepted_append_only_v28',
        'previous_index_sha256': new['previous_index_sha256'],
        'new_index_sha256': sha256(new_path.read_bytes()).hexdigest(),
        'old_29_parent_entries_and_129_facts_exact': True, 'new_facts': 15,
        'fact_count': 144, 'parent_entries': 32, 'unique_sources': 34, 'unique_companies': 20,
        'original_company_source_pairs': 25, 'actual_sources': 32, 'actual_facts': 137,
        'file_only_sources': 2, 'file_only_facts': 7, 'financial_inputs_adopted': False,
        'actual_db_main_sha256': accepted['database_main_sha256'],
        'prewrite_readonly_assertion_correction': 'The first attempt incorrectly expected '
            'normalized fact source_id to be the derivative ID. The normalized schema '
            'binds the original quotation there. No file/DB mutation occurred in that attempt.'}
    save(HERE / 'parent-acceptance.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
