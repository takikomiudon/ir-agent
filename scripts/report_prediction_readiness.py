#!/usr/bin/env python3
"""Print forecast/observation readiness checks from a consistent read-only DB."""
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ir_agent.models import now_iso, parse_json
from ir_agent.prediction_readiness import audit_prediction_readiness


def read_snapshot(path: str | Path) -> dict:
    database = Path(path).resolve(strict=True)
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        result = {}
        specifications = (
            ("observation_versions", "ir_observation_versions", ("observation_id", "version", "design_sha256", "data", "first_saved_at")),
            ("predictions", "ir_predictions", ("id", "observation_id", "observation_version", "model_id", "model_version", "request_sha256", "data", "first_saved_at")),
            ("models", "ir_prediction_models", ("model_id", "model_version", "commitment_sha256", "data", "first_saved_at")),
        )
        for section, table, fields in specifications:
            if table not in tables:
                continue
            result[section] = []
            for row in connection.execute("SELECT " + ",".join(fields) + " FROM " + table):
                item = dict(zip(fields, row)); item["record"] = parse_json(item.pop("data"))
                result[section].append(item)
        connection.execute("ROLLBACK")
        return result
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--as-of", help="Offset-aware cutoff; defaults to the current time")
    args = parser.parse_args(argv)
    try:
        result = audit_prediction_readiness(read_snapshot(args.db), as_of=args.as_of or now_iso())
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.error(str(error))
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2, allow_nan=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
