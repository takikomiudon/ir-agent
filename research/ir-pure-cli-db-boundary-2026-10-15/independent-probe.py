"""Three before/after probes; saved CLI snapshots and SQLite :memory: only."""
import argparse
import ast
from contextlib import redirect_stderr, redirect_stdout
import csv
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import types

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tests'))
from ir_agent.store import Store
from test_contacts import row

NOW = '2026-10-15T12:30:00+00:00'
PURE = {'value', 'cycle-margin', 'decision', 'ir-plan', 'information-value', 'screen',
        'capacity', 'stable-reinvestment', 'model-inputs', 'score-probabilities',
        'normalize-quote', 'normalize-facts'}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load_snapshot(name, path):
    module = types.ModuleType('ir_agent.' + name)
    module.__package__ = 'ir_agent'
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def ast_dump(node):
    return ast.dump(node, include_attributes=False)


def finite_structural_checks(before, after):
    bt = ast.parse((BASE / 'source-before/cli.py').read_bytes())
    at = ast.parse((BASE / 'source-after/cli.py').read_bytes())
    bf = {n.name: n for n in bt.body if isinstance(n, ast.FunctionDef)}
    af = {n.name: n for n in at.body if isinstance(n, ast.FunctionDef)}
    assert ast_dump(bf['parser']) == ast_dump(af['parser'])

    def command_names(node):
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
            return set()
        cmp = node.test
        if ast_dump(cmp.left) != ast_dump(ast.parse('args.command', mode='eval').body):
            return set()
        try:
            value = ast.literal_eval(cmp.comparators[0])
        except ValueError:
            return set()
        return {value} if isinstance(value, str) else set(value)

    moved_before = [n for n in bf['run'].body if command_names(n) & PURE]
    moved_after = [n for n in af['_run_file_command'].body if command_names(n) & PURE]
    assert len(moved_before) == len(moved_after) == 11
    assert [ast_dump(n) for n in moved_before] == [ast_dump(n) for n in moved_after]
    rest_before = [n for n in bf['run'].body if n not in moved_before]
    rest_after = af['run'].body[1:]
    assert [ast_dump(n) for n in rest_before] == [ast_dump(n) for n in rest_after]

    before_main = bf['main']
    after_main = af['main']
    old_try = next(n for n in before_main.body if isinstance(n, ast.Try))
    new_try = next(n for n in after_main.body if isinstance(n, ast.Try))
    assert isinstance(new_try.body[0], ast.If)
    assert len(new_try.body[0].body) == 1 and not new_try.body[0].orelse
    assert ast_dump(new_try.body[0].body[0]) == ast_dump(old_try.body[0])
    assert [ast_dump(n) for n in new_try.body[1:]] == [ast_dump(n) for n in old_try.body[1:]]
    assert [ast_dump(n) for n in new_try.handlers] == [ast_dump(n) for n in old_try.handlers]
    assert [ast_dump(n) for n in new_try.finalbody] == [ast_dump(n) for n in old_try.finalbody]
    assert [ast_dump(n) for n in before_main.body if n is not old_try] == [ast_dump(n) for n in after_main.body if n is not new_try]
    assert after._FILE_COMMANDS == frozenset(PURE)
    choices = next(a.choices for a in after.parser()._actions if isinstance(a, argparse._SubParsersAction))
    assert len(choices) == 36
    matrix = []
    for command in choices:
        args = argparse.Namespace(command=command, operation=None, file=None, dry_run=False)
        expected = command in PURE
        assert after._runs_without_store(args) is expected
        matrix.append({'command': command, 'without_store': expected})
    conditional = [
        ('observations', 'summarize', 'records.json', False, True),
        ('observations', 'summarize', None, False, False),
        ('observations', 'summarize', '', False, False),
        ('observations', 'register', 'record.json', False, False),
        ('observations', 'append', 'record.json', False, False),
        ('observations', 'show', None, False, False),
        ('contacts', 'import', 'catalog.csv', True, True),
        ('contacts', 'import', 'catalog.csv', False, False),
    ]
    for command, operation, file, dry_run, expected in conditional:
        args = argparse.Namespace(command=command, operation=operation, file=file, dry_run=dry_run)
        assert after._runs_without_store(args) is expected
    return {'parser_AST_equal': True, 'eleven_moved_branch_ASTs_equal': True,
            'remaining_DB_run_AST_equal': True, 'main_result_error_finally_AST_equal': True,
            'pure_allowlist_exact12': True, 'top_command_matrix': matrix,
            'conditional_guard_cases': len(conditional),
            'decision_and_ir_plan_before': 'Both already evaluate(load_json(args.file)); no live DB validation removed.'}


def invoke(module, args, *, must_skip_store):
    output, error = io.StringIO(), io.StringIO()
    requested = []
    closed = []
    opened = []
    old_store, old_harness, old_now = module.Store, module.Harness, module.now_iso

    def factory(path):
        requested.append(str(path))
        if must_skip_store:
            raise AssertionError('Pure route opened Store')
        store = Store(':memory:')
        opened.append(store)
        real_close = store.close

        def close():
            closed.append(True)
            real_close()
        store.close = close
        return store

    def forbidden_harness(store):
        raise AssertionError('Pure route constructed Harness')
    module.Store = factory
    if must_skip_store:
        module.Harness = forbidden_harness
    module.now_iso = lambda: NOW
    try:
        with redirect_stdout(output), redirect_stderr(error):
            code = module.main(args)
    finally:
        module.Store, module.Harness, module.now_iso = old_store, old_harness, old_now
    for store in opened:
        try:
            store.connection.execute('SELECT 1')
        except sqlite3.ProgrammingError:
            pass
        else:
            raise AssertionError('Memory Store not closed')
    return {'exit_code':code,'stdout':output.getvalue(),'stderr':error.getvalue(),
            'Store_calls':len(requested),'actual_Store_paths':[':memory:']*len(opened),
            'close_calls':len(closed)}


def main():
    fixed = [BASE/'review.json', BASE/'reproduction.json', BASE/'implementation.json',
             BASE/'source-before/cli.py', BASE/'source-after/cli.py',
             BASE/'source-after/test_pure_cli_db_boundary.py', ROOT/'src/ir_agent/cli.py',
             ROOT/'tests/test_pure_cli_db_boundary.py', ROOT/'src/ir_agent/harness.py',
             ROOT/'src/ir_agent/contacts.py', ROOT/'tests/test_contacts.py',
             ROOT/'examples/disclosed-facts.json']
    before_hashes = {str(p.relative_to(ROOT)): digest(p) for p in fixed}
    assert (ROOT/'src/ir_agent/cli.py').read_bytes() == (BASE/'source-after/cli.py').read_bytes()
    assert (ROOT/'tests/test_pure_cli_db_boundary.py').read_bytes() == (BASE/'source-after/test_pure_cli_db_boundary.py').read_bytes()
    before = load_snapshot('_independent_cli_before', BASE/'source-before/cli.py')
    after = load_snapshot('_independent_cli_after', BASE/'source-after/cli.py')
    structure = finite_structural_checks(before, after)
    probes = []
    with tempfile.TemporaryDirectory(prefix='ir-pure-cli-independent-') as temporary:
        temp = Path(temporary)
        blocker = temp/'blocked-parent'
        blocker.write_bytes(b'synthetic file preventing DB parent creation')
        db_arg = str(blocker/'db.sqlite3')
        previous = Path.cwd()
        os.chdir(temp)
        try:
            commands = [
                ('P01-normalize-facts-clock-and-output', ['--db',db_arg,'normalize-facts',str(ROOT/'examples/disclosed-facts.json')], True),
            ]
            catalog = temp/'catalog.csv'
            good = row()
            bad = row('130B', channels='not-json')
            with catalog.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(good))
                writer.writeheader()
                writer.writerows([good,bad])
            commands.extend([
                ('P02-contacts-dryrun-with-rejected-row', ['--db',db_arg,'contacts','import',str(catalog),'--dry-run','--imported-at',NOW], True),
                ('P03-observations-without-file-still-stateful', ['--db',db_arg,'observations','summarize','--as-of',NOW], False),
            ])
            for label, args, pure in commands:
                old = invoke(before,args,must_skip_store=False)
                new = invoke(after,args,must_skip_store=pure)
                assert (old['exit_code'],old['stdout'],old['stderr']) == (new['exit_code'],new['stdout'],new['stderr'])
                assert old['exit_code']==0 and old['stderr']==''
                assert old['Store_calls']==old['close_calls']==1
                assert new['Store_calls']==new['close_calls']==(0 if pure else 1)
                value=json.loads(new['stdout'])
                if label.startswith('P01'):
                    assert value['sources'][1]['retrieved_at']==NOW
                    focus={'derived_source_id':value['sources'][1]['id'], 'derived_retrieved_at':value['sources'][1]['retrieved_at'],'financial_inputs_verified':value['sources'][1]['metadata']['financial_inputs_verified']}
                elif label.startswith('P02'):
                    assert value['status']=='dry_run' and len(value['rejected_rows'])==1
                    focus={'status':value['status'],'rejected_rows':value['rejected_rows'],'summary':value['summary']}
                else:
                    assert value['record_count']==0
                    focus={'record_count':value['record_count']}
                probes.append({'id':label,'comparison':'same exit/stdout/stderr at fixed CLI clock',
                               'before':{k:v for k,v in old.items() if k not in ['stdout','stderr']},
                               'after':{k:v for k,v in new.items() if k not in ['stdout','stderr']},
                               'stdout_sha256':sha256(new['stdout'].encode()).hexdigest(),
                               'stderr':new['stderr'],'focus':focus})
            assert blocker.read_bytes()==b'synthetic file preventing DB parent creation'
            assert not (temp/'data').exists()
        finally:
            os.chdir(previous)
    assert all(digest(ROOT/p)==digest_at_start for p,digest_at_start in before_hashes.items())
    result={'schema_version':1,'status':'three_differential_memory_temp_probes_passed',
            'fixed_cli_now':NOW,'structural_checks':structure,'probes':probes,
            'source_hashes_unchanged':before_hashes,
            'scope':{'probe_count':3,'main_invocations':6,'real_research_DB_accesses':0,
                     'persistent_SQLite_DBs_created':0,'SQLite_memory_Store_opens':4,
                     'new_GETs':0,'production_or_test_edits':0,'fullsuite_runs':0},
            'limit':'Before Store constructor was deliberately mapped to :memory: to compare calculation/output without opening a persistent DB. The supplied impossible path was not used for a real before-Store connection. After pure Store/Harness construction was forbidden.'}
    (BASE/'independent-probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'probe_count':3,'fixed_inputs_unchanged':len(before_hashes),'output_file':'independent-probe.json'},ensure_ascii=False))


if __name__=='__main__':
    main()
