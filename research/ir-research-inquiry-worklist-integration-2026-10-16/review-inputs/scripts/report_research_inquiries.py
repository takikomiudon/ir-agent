#!/usr/bin/env python3
"""Print current research inquiry work metadata, without question/reply text."""
from pathlib import Path
import argparse
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ir_agent.models import json_text
from ir_agent.research_inquiry_worklist import read_research_inquiry_worklist


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True, type=Path, help='Existing SQLite database (read-only)')
    args = parser.parse_args(argv)
    try:
        report = read_research_inquiry_worklist(args.db)
    except (ValueError, OSError, sqlite3.Error):
        parser.error('Cannot read an existing research inquiry database')
    print(json_text(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
