#!/usr/bin/env python3
"""Read saved date-only catalyst mappings without marking events as occurred."""
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ir_agent.catalyst_schedule import report_catalyst_schedule
from ir_agent.models import json_text, now_iso, parse_json


def read_report(path: str | Path, event_requests: list[dict], *, as_of: str,
                now: str, calendar_window: dict | None = None) -> dict:
    database = Path(path).resolve(strict=True)
    connection = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)
    try:
        connection.execute('PRAGMA query_only=ON')
        connection.execute('BEGIN')
        return report_catalyst_schedule(connection, event_requests, as_of=as_of,
                                       now=now, calendar_window=calendar_window)
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    parser.add_argument('--events', help='JSON array of explicit schedule-only mappings; defaults to []')
    parser.add_argument('--as-of', help='Offset-aware cutoff; defaults to the runtime clock')
    parser.add_argument('--date-from', help='Display window starting calendar date; requires --date-through')
    parser.add_argument('--date-through', help='Display window ending calendar date; requires --date-from')
    args = parser.parse_args(argv)
    if (args.date_from is None) != (args.date_through is None):
        parser.error('Provide both --date-from and --date-through, or neither')
    window = ({'date_from': args.date_from, 'date_through': args.date_through}
              if args.date_from is not None else None)
    try:
        requests = parse_json(Path(args.events).read_text(encoding='utf-8')) if args.events else []
        current = now_iso()
        result = read_report(args.db, requests, as_of=args.as_of or current,
                             now=current, calendar_window=window)
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.error(str(error))
    sys.stdout.write(json_text(result) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
