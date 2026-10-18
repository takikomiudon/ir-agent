#!/usr/bin/env python3
"""Print a consistent, read-only SQLite research-coverage inventory as JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ir_agent.coverage import summarize_coverage
from ir_agent.models import now_iso


def read_snapshot(path: str | Path) -> dict:
    database = Path(path).resolve(strict=True)
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "companies" not in tables:
            raise ValueError("Database has no company inventory")
        result = {}
        for section, table in (("companies", "companies"), ("sources", "sources"), ("theses", "theses"), ("questions", "questions")):
            if table in tables:
                result[section] = [json.loads(row[0]) for row in connection.execute("SELECT data FROM " + table)]
        if "decision_policies" in tables:
            result["policies"] = [{"policy": json.loads(row[0]), "first_saved_at": row[1]}
                                  for row in connection.execute("SELECT data,first_saved_at FROM decision_policies")]
        if "source_classifications" in tables:
            result["source_classifications"] = [json.loads(row[0]) for row in
                                                connection.execute("SELECT data FROM source_classifications")]
        connection.execute("ROLLBACK")
        return result
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--as-of", help="Offset-aware cutoff; default is current time")
    args = parser.parse_args(argv)
    try:
        result = summarize_coverage(read_snapshot(args.db), as_of=args.as_of or now_iso())
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.error(str(error))
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
