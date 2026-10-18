#!/usr/bin/env python3
"""Read explicit research follow-up manifests without queuing jobs."""
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ir_agent.models import json_text, now_iso, parse_json
from ir_agent.research_monitoring import report_research_monitoring


def read_report(path, case_requests, *, as_of, now, research_root):
    database = Path(path).resolve(strict=True)
    connection = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)
    try:
        connection.execute('PRAGMA query_only=ON')
        connection.execute('BEGIN')
        return report_research_monitoring(connection, case_requests, as_of=as_of, now=now,
                                          research_root=research_root)
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    parser.add_argument('--cases', required=True, help='Explicit JSON case array; each entry requires recorded_at')
    parser.add_argument('--research-root', required=True)
    parser.add_argument('--as-of', help='Offset-aware cutoff; defaults to trusted runtime now')
    args = parser.parse_args(argv)
    try:
        cases = parse_json(Path(args.cases).read_text(encoding='utf-8'))
        current = now_iso()
        result = read_report(args.db, cases, as_of=args.as_of or current, now=current,
                             research_root=args.research_root)
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.error(str(error))
    sys.stdout.write(json_text(result) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
