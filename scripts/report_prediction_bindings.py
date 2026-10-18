#!/usr/bin/env python3
"""Report saved forecast evidence bindings from one read-only SQLite snapshot."""
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ir_agent.models import json_text, now_iso, parse_json
from ir_agent.prediction_bindings import report_prediction_bindings


def read_report(path: str | Path, binding_requests: list[dict], *, as_of: str, now: str) -> dict:
    database = Path(path).resolve(strict=True)
    connection = sqlite3.connect(database.as_uri()+'?mode=ro', uri=True)
    try:
        connection.execute('PRAGMA query_only=ON')
        connection.execute('BEGIN')
        return report_prediction_bindings(connection, binding_requests, as_of=as_of, now=now)
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    parser.add_argument('--bindings', help='JSON array of explicit observation/source/reply mappings; defaults to []')
    parser.add_argument('--as-of', help='Offset-aware historical cutoff; defaults to the current time')
    args = parser.parse_args(argv)
    try:
        requests = parse_json(Path(args.bindings).read_text()) if args.bindings else []
        current = now_iso()
        result = read_report(args.db, requests, as_of=args.as_of or current, now=current)
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.error(str(error))
    sys.stdout.write(json_text(result)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
