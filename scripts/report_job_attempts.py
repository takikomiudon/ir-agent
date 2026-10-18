#!/usr/bin/env python3
"""Read saved lease attempts into an explicit capacity request plus audit."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ir_agent.attempt_measurements import build_attempt_measurements
from ir_agent.models import load_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Existing SQLite file; opened mode=ro and query_only")
    parser.add_argument("--as-of", required=True, help="Knowledge cutoff, including timezone offset")
    parser.add_argument("--window-start", required=True, help="Explicit measurement-window start")
    parser.add_argument("--window-end", required=True, help="Explicit window end, no later than as-of")
    parser.add_argument("--operator-capacity", help="Optional explicit operator-capacity JSON object")
    parser.add_argument("--output", help="Write the request+audit artifact here; default stdout")
    args = parser.parse_args(argv)
    try:
        if args.output and Path(args.output).resolve() == Path(args.db).resolve():
            raise ValueError("Report output must not overwrite the source database")
        result = build_attempt_measurements(
            args.db, as_of=args.as_of,
            window={"started_at": args.window_start, "ended_at": args.window_end},
            operator_capacity=load_json(args.operator_capacity) if args.operator_capacity else None)
        rendered = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
