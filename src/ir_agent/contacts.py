"""Offline import of the reviewed IR contact catalog as company metadata.

Contact reception evidence is not a financial disclosure, thesis, permission to
send, or eligibility to invest. This converter does no network or DB writes.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from .adapters.common import canonical_json, normalize_security_code
from .models import object_value, strings, text, timestamp


_REQUIRED = {
    "security_code", "company_name", "channel_status", "contact_url", "channels",
    "public_ir_emails", "individual_access", "outreach_suitability", "conditions",
    "limitations", "reviewed_at", "review_source", "source_record", "contact_observations",
}
_EMAIL = re.compile(r"[^\s<>@]+@[^\s<>@.]+(?:\.[^\s<>@.]+)+\Z")


def _http_url(value: object, label: str) -> str:
    value = text(value, label)
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError
        if any(c.isspace() or ord(c) < 32 for c in value):
            raise ValueError
        parsed.port
    except ValueError:
        raise ValueError(f"{label} must be an HTTP(S) reference URL without credentials") from None
    return value


def _json(value: object, label: str):
    def unique(items):
        result = {}
        for key, child in items:
            if key in result:
                raise ValueError(f"{label} contains duplicate JSON keys")
            result[key] = child
        return result

    def nonfinite(value):
        raise ValueError(f"{label} contains non-finite JSON")

    try:
        return json.loads(text(value, label), object_pairs_hook=unique, parse_constant=nonfinite)
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} must be valid JSON") from error


def _row_company(row: dict, *, imported_at: str, imported, catalog: dict, row_number: int, line_number: int) -> dict:
    code = text(row.get("security_code"), "security_code")
    if not re.fullmatch(r"[0-9A-Z]{4}", code) or normalize_security_code(code) != code:
        raise ValueError("security_code must be a canonical four-character ordinary-share code")
    name = text(row.get("company_name"), "company_name")
    if row.get("channel_status") != "confirmed" or row.get("outreach_suitability") != "candidate":
        raise ValueError("contact must be confirmed and an outreach candidate")
    contact_url = text(row.get("contact_url"), "contact_url")
    channels = strings(_json(row.get("channels"), "channels"), "channels", nonempty=True)
    if not set(channels) <= {"email", "form", "phone", "fax", "postal"} or not set(channels) & {"email", "form"}:
        raise ValueError("channels must include email or form and contain only recognized channels")
    emails = strings(_json(row.get("public_ir_emails"), "public_ir_emails"), "public_ir_emails")
    if any(not _EMAIL.fullmatch(email) for email in emails):
        raise ValueError("public_ir_emails must contain plain public email addresses")
    if ("email" in channels) != bool(emails):
        raise ValueError("email channel and public_ir_emails must agree")
    if contact_url.startswith("mailto:"):
        parsed = urlsplit(contact_url)
        # Some original reviews retained a space after the mailto colon.
        # Validate the target but retain the exact catalog reference unchanged.
        target = unquote(parsed.path).strip()
        if "form" in channels or parsed.query or parsed.fragment or target not in emails or not _EMAIL.fullmatch(target):
            raise ValueError("mailto contact_url must match a listed public IR email without extra actions")
    else:
        _http_url(contact_url, "contact_url")
    access = row.get("individual_access")
    if access not in {"explicit", "not_stated"}:
        raise ValueError("individual_access must be explicit or not_stated for an outreach candidate")
    conditions = strings(_json(row.get("conditions"), "conditions"), "conditions")
    limitations = strings(_json(row.get("limitations"), "limitations"), "limitations")
    verified_at = text(row.get("reviewed_at"), "reviewed_at")
    if timestamp(verified_at, "reviewed_at") > imported:
        raise ValueError("reviewed_at cannot be later than imported_at")
    observations = _json(row.get("contact_observations"), "contact_observations")
    if not isinstance(observations, list) or any(not isinstance(x, dict) for x in observations):
        raise ValueError("contact_observations must be a list of review objects")
    selected = [x for x in observations if x.get("contact_url") == contact_url
                and x.get("channel_status") == "confirmed" and x.get("outreach_suitability") == "candidate"]
    if not selected:
        raise ValueError("contact_url has no matching confirmed candidate observation")
    observed_channels = set()
    observed_emails = set()
    for observation in selected:
        observed_channels.update(strings(observation.get("channels", []), "observation.channels"))
        observed_emails.update(strings(observation.get("public_ir_emails", []), "observation.public_ir_emails"))
    if not set(channels) <= observed_channels or not set(emails) <= observed_emails:
        raise ValueError("catalog channels/emails are not supported by selected confirmed observations")
    if access == "explicit" and not any(x.get("individual_access") in ("explicit", "explicitly_allowed") for x in selected):
        raise ValueError("explicit individual access lacks a selected confirming observation")
    references, seen = [], set()
    for observation in selected:
        if observation.get("security_code") not in (None, code):
            raise ValueError("selected contact observation belongs to a different security code")
        if observation.get("reviewed_at") is not None:
            if timestamp(observation["reviewed_at"], "observation.reviewed_at") > imported:
                raise ValueError("selected contact observation is later than imported_at")
        refs = observation.get("source_references", [])
        if not isinstance(refs, list):
            raise ValueError("source_references must be a list")
        for reference in refs:
            reference = object_value(reference, "source_reference")
            text(reference.get("snapshot"), "source_reference.snapshot")
            _http_url(reference.get("url"), "source_reference.url")
            # A migration/link-navigation reference may have an empty quote.
            # Keep it, but require substantive quoted evidence in the set below.
            if not isinstance(reference.get("quote", ""), str):
                raise ValueError("source_reference.quote must be a string when present")
            if reference.get("retrieved_at") is not None:
                if timestamp(reference["retrieved_at"], "source_reference.retrieved_at") > imported:
                    raise ValueError("contact source reference is later than imported_at")
            saved = dict(reference)
            if "source_directory" not in saved and observation.get("source_directory"):
                saved["source_directory"] = observation["source_directory"]
            if "source_directory" in saved:
                text(saved["source_directory"], "source_reference.source_directory")
            identity = canonical_json(saved)
            if identity not in seen:
                seen.add(identity)
                references.append(saved)
    if not references or not any(x.get("quote", "").strip() for x in references):
        raise ValueError("confirmed contact requires original source references with quoted evidence")
    provenance = {
        **catalog, "csv_row_number": row_number, "csv_line_number": line_number,
        "source_record": text(row.get("source_record"), "source_record"),
        "review_source": text(row.get("review_source"), "review_source"),
        "source_references": references,
        "reference_scope": "Original references from confirmed candidate observations for the selected contact URL; not independent re-verification.",
    }
    return {
        "id": f"jp:{code}", "security_code": code, "name": name, "status": "watch",
        "ir_contact": {
            "contact_url": contact_url, "channels": channels, "public_ir_emails": emails,
            "channel_status": "confirmed", "outreach_suitability": "candidate",
            "individual_access": access, "conditions": conditions, "limitations": limitations,
            "verified_at": verified_at, "imported_at": imported_at, "provenance": provenance,
        },
    }


def build_contact_bundle(path, *, imported_at: str) -> dict:
    """Convert reviewed CSV rows into watch-only companies with contact metadata.

    Invalid rows and *all* occurrences of duplicate codes are quarantined with
    logical CSV row numbers and physical starting lines. A malformed file/header
    raises because trustworthy row boundaries/field meanings cannot be assumed.
    The source is read once, SHA-256 identified, and never changed. Repeating the
    same input and imported_at returns the same result without a new verification.
    The caller owns ingestion and preservation of existing company status/holdings.
    """
    imported = timestamp(imported_at, "imported_at")
    catalog_path = Path(path)
    raw = catalog_path.read_bytes()
    catalog = {"catalog_path": str(catalog_path.resolve()), "catalog_sha256": hashlib.sha256(raw).hexdigest()}
    reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
    try:
        fields = next(reader)
    except StopIteration:
        raise ValueError("Contact catalog is empty and has no header") from None
    except csv.Error as error:
        raise ValueError(f"Malformed contact CSV header: {error}") from error
    if len(fields) != len(set(fields)):
        raise ValueError("Contact catalog contains duplicate header names")
    if not _REQUIRED <= set(fields):
        raise ValueError("Contact catalog is missing required headers: " + ", ".join(sorted(_REQUIRED - set(fields))))
    pending, rejected, codes = [], [], {}
    previous_line = reader.line_num
    try:
        for row_number, values in enumerate(reader, 2):
            line_number = previous_line + 1
            previous_line = reader.line_num
            if len(values) != len(fields):
                code_index = fields.index("security_code")
                malformed_code = values[code_index] if len(values) > code_index else None
                if malformed_code is not None:
                    codes.setdefault(malformed_code, []).append((row_number, line_number))
                rejected.append({"row_number": row_number, "line_number": line_number,
                                 "security_code": malformed_code,
                                 "reason_codes": ["malformed_csv_columns"],
                                 "reasons": ["CSV row field count differs from its header"]})
                continue
            row = dict(zip(fields, values))
            code = row.get("security_code")
            codes.setdefault(code, []).append((row_number, line_number))
            try:
                company = _row_company(row, imported_at=imported_at, imported=imported, catalog=catalog,
                                       row_number=row_number, line_number=line_number)
                pending.append((row_number, line_number, company))
            except ValueError as error:
                rejected.append({"row_number": row_number, "line_number": line_number,
                                 "security_code": code, "reason_codes": ["invalid_contact_row"], "reasons": [str(error)]})
    except csv.Error as error:
        raise ValueError(f"Malformed contact CSV near physical line {reader.line_num}: {error}") from error
    duplicates = {code for code, occurrences in codes.items() if len(occurrences) > 1}
    indexed_rejections = {row["row_number"]: row for row in rejected}
    for code in sorted(duplicates):
        for row_number, line_number in codes[code]:
            item = indexed_rejections.get(row_number)
            if item is None:
                item = {"row_number": row_number, "line_number": line_number, "security_code": code,
                        "reason_codes": [], "reasons": []}
                rejected.append(item)
                indexed_rejections[row_number] = item
            item["reason_codes"].append("duplicate_security_code")
            item["reasons"].append("All rows with the same security code are quarantined; no row was chosen implicitly")
    companies = [company for _, _, company in pending if company["security_code"] not in duplicates]
    rejected.sort(key=lambda x: x["row_number"])
    return {
        "bundle": {"schema_version": 1, "companies": companies, "sources": [], "theses": []},
        "summary": {
            **catalog, "imported_at": imported_at, "input_rows": len(companies) + len(rejected),
            "accepted_rows": len(companies), "rejected_rows": len(rejected),
            "duplicate_codes": sorted(duplicates),
            "individual_access_explicit": sum(c["ir_contact"]["individual_access"] == "explicit" for c in companies),
            "individual_access_not_stated": sum(c["ir_contact"]["individual_access"] == "not_stated" for c in companies),
            "financial_sources_created": 0, "theses_created": 0,
        },
        "rejected_rows": rejected,
    }
