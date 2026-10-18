"""Bounded research transport: one explicit URL, no retries or redirects."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


def main() -> None:
    url = sys.argv[1]
    folder = Path(__file__).resolve().parent
    manifest_path = folder / "transport-manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "maximum_GETs": 6, "GETs": [], "retries": 0, "automatic_redirects": 0,
        "proxy_retained": True, "TLS_verification": True,
    }
    if len(manifest["GETs"]) >= 6:
        raise ValueError("GET budget exhausted")
    if any(row["url"] == url for row in manifest["GETs"]):
        raise ValueError("Same URL already requested; no retry")
    sequence = len(manifest["GETs"]) + 1
    row = {"sequence": sequence, "url": url,
           "retrieved_at": datetime.now(timezone.utc).isoformat(),
           "method": "GET", "status": None, "error": None}
    # Reserve before sending: interrupted requests also consume the budget.
    manifest["GETs"].append(row)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    raw = bytearray()
    try:
        with requests.get(url, headers={"User-Agent": "Codex-IR-Research/0.1"},
                          timeout=(10, 25), allow_redirects=False, stream=True) as response:
            row["status"] = response.status_code
            row["headers"] = {key: value for key, value in response.headers.items()
                              if key.lower() in {"content-type", "content-length", "location", "last-modified"}}
            for chunk in response.iter_content(65536):
                raw.extend(chunk)
                if len(raw) > 16 * 1024 * 1024:
                    raise ValueError("Response exceeds bounded 16 MiB body limit")
    except (requests.RequestException, ValueError) as error:
        row["error"] = f"{type(error).__name__}: {error}"
    digest = hashlib.sha256(raw).hexdigest()
    destination = folder / "raw" / digest
    destination.write_bytes(raw)
    row.update(sha256=digest, byte_count=len(raw), raw_file=str(destination.relative_to(folder)),
               completed_at=datetime.now(timezone.utc).isoformat())
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (folder / f"{sequence:02d}.json").write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
