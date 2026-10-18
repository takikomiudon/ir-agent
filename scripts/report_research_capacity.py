#!/usr/bin/env python3
"""Summarize explicit work measurements offline; does not run research jobs."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ir_agent.capacity import report_research_capacity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Measurement/window/operator-capacity JSON")
    parser.add_argument("--output", help="Write report here instead of stdout")
    args = parser.parse_args()
    result = report_research_capacity(json.loads(Path(args.input).read_text(encoding="utf-8")))
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
