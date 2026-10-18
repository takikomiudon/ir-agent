"""One reviewed research draft; preserve a successful result before readback."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json

from ir_agent.research_inquiries import ResearchInquiries
from ir_agent.store import Store


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


parser = argparse.ArgumentParser()
parser.add_argument("--db", required=True)
parser.add_argument("--request", required=True)
parser.add_argument("--request-sha256", required=True)
parser.add_argument("--output-directory", required=True)
args = parser.parse_args()
request_bytes = Path(args.request).read_bytes()
request_sha = hashlib.sha256(request_bytes).hexdigest()
if request_sha != args.request_sha256:
    raise ValueError("Reviewed request SHA mismatch")
request = json.loads(request_bytes)
output = Path(args.output_directory)
# A started directory is never reused automatically, even after an exception.
output.mkdir(exist_ok=False)
save(output / "started.json", {
    "runtime": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "request_sha256": request_sha,
    "inquiry_id": request["id"],
    "database": args.db,
})
store = None
try:
    store = Store(args.db)
    api = ResearchInquiries(store)
    result = api.add_inquiry(request)
    save(output / "add.json", result)
    save(output / "show.json", api.show_inquiry(request["id"]))
    save(output / "list.json", api.list_inquiries())
    save(output / "view.json", api.current_view(request["id"]))
except Exception as exc:
    save(output / "error.json", {"type": type(exc).__name__, "message": str(exc)})
    raise
finally:
    if store is not None:
        store.close()
save(output / "completed.json", {
    "runtime": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "request_sha256": request_sha,
    "inquiry_id": request["id"],
    "database_sha256_after_close": hashlib.sha256(Path(args.db).read_bytes()).hexdigest(),
    "sent_or_reply_or_review_created": False,
})
print(json.dumps({"saved": request["id"], "output_directory": str(output)}))
