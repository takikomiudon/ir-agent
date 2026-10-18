"""Read-only comparison with the closed SQLite backup, never a mutator retry."""
from contextlib import closing
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import sqlite3


def snapshot(path):
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        schema = db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()
        tables = [r[0] for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        rows = {name: sorted(db.execute('SELECT * FROM "' + name + '"').fetchall(), key=repr)
                for name in tables}
        columns = {name: [r[1] for r in db.execute('PRAGMA table_info("' + name + '")')]
                   for name in tables}
    return schema, rows, columns


parser = argparse.ArgumentParser()
parser.add_argument("--before", required=True)
parser.add_argument("--after", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--readback-directory", required=True)
args = parser.parse_args()
before_schema, before_rows, before_columns = snapshot(args.before)
after_schema, after_rows, after_columns = snapshot(args.after)
assert before_schema == after_schema
assert before_columns == after_columns
for table in before_rows:
    if table != "research_inquiries":
        assert before_rows[table] == after_rows[table], table
columns = after_columns["research_inquiries"]
old = {row[0]: row for row in before_rows["research_inquiries"]}
new = {row[0]: row for row in after_rows["research_inquiries"]}
assert all(new[key] == value for key, value in old.items())
identity = "research-inquiry:135A:customer-counting-unit:20261016"
assert set(new) - set(old) == {identity}
row = dict(zip(columns, new[identity]))
assert row["company_id"] == "jp:135A" and row["status"] == "draft"
assert row["sent_at"] is None and row["closed_at"] is None
readback = Path(args.readback_directory)
view = json.loads((readback / "view.json").read_bytes())
assert view["reason_codes"] == ["no_reply"]
assert view["financial_inputs_verified"] is False and view["case_applied"] is False
report = {
    "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "database": args.after,
    "database_sha256_after_connections_closed": hashlib.sha256(Path(args.after).read_bytes()).hexdigest(),
    "schema_unchanged": True,
    "all_other_tables_exact_rows_unchanged": len(before_rows) - 1,
    "previous_research_inquiry_exact_rows_unchanged": len(old),
    "added_inquiry_id": identity,
    "first_saved_at": row["first_saved_at"],
    "status": row["status"],
    "current_view_reason_codes": view["reason_codes"],
    "table_counts": {name: len(rows) for name, rows in after_rows.items()},
    "sources_case_heads_jobs_financial_inputs_sent_reply_reviews_unchanged": True,
}
output = Path(args.output)
with output.open("x") as stream:
    stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"verified": identity, "other_tables_unchanged": len(before_rows) - 1,
                  "first_saved_at": row["first_saved_at"], "status": row["status"]}))
