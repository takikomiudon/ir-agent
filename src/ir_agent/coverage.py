"""Read-only inventory of saved research prerequisites, never eligibility scores."""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256

from .decision import _PARAMETERS, _check_source_origins, validate_decision_policy
from .intake import KINDS
from .models import available, integer, json_text, object_value, text, timestamp, validate_source


_SECTIONS = ("companies", "sources", "theses", "policies", "questions")
_FINANCIAL_KINDS = ("financial_statement", "earnings_release", "earnings_presentation", "annual_report", "quarterly_report")


def _contact(company, cutoff):
    value = company.get("ir_contact")
    result = {"recorded": isinstance(value, dict), "confirmed_available": False,
              "individual_access": None, "reason_codes": []}
    if not isinstance(value, dict):
        result["reason_codes"] = ["contact_metadata_missing"]
        return result
    for key in ("verified_at", "imported_at"):
        if value.get(key) is None:
            result["reason_codes"].append("contact_" + key + "_missing")
        elif timestamp(value[key]) > cutoff:
            result["reason_codes"].append("contact_" + key + "_after_as_of")
    for reference in value.get("provenance", {}).get("source_references", []):
        for key in ("published_at", "retrieved_at"):
            if reference.get(key) is not None and timestamp(reference[key]) > cutoff:
                result["reason_codes"].append("contact_evidence_after_as_of")
    if value.get("channel_status") != "confirmed" or not value.get("contact_url"):
        result["reason_codes"].append("contact_not_confirmed")
    if not set(value.get("channels", [])) & {"email", "form"}:
        result["reason_codes"].append("electronic_ir_channel_not_confirmed")
    result["confirmed_available"] = not result["reason_codes"]
    if result["confirmed_available"]:
        result["individual_access"] = value.get("individual_access")
    return result


def summarize_coverage(snapshot: dict, *, as_of: str) -> dict:
    """Describe a saved snapshot; missing arrays are unknown, explicit [] is zero.

    Policies are wrappers {policy: registered policy, first_saved_at: timestamp}.
    Financial content requires explicit financial classification, rather than a
    title keyword or an EDINET index entry. Unclassified disclosures are retained
    and routed to review, not automatically fetched again.
    """
    snapshot = object_value(snapshot, "coverage snapshot")
    if "companies" not in snapshot:
        raise ValueError("A company inventory is required; unknown coverage is not zero companies")
    cutoff = timestamp(as_of, "coverage.as_of")
    sections = {}
    missing = []
    for section in _SECTIONS:
        if section not in snapshot:
            missing.append(section); sections[section] = []
        elif not isinstance(snapshot[section], list):
            raise ValueError(section + " must be a list")
        else:
            sections[section] = snapshot[section]
    companies = sections["companies"]
    ids = [text(c.get("id"), "company.id") for c in companies]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate company ID")
    sources = {}; by_company = defaultdict(list)
    for raw in sections["sources"]:
        source = validate_source(raw)
        if source["id"] in sources:
            raise ValueError("Duplicate source ID")
        sources[source["id"]] = source
        by_company[source["company_id"]].append(source)
    classification_rows = snapshot.get("source_classifications", [])
    if not isinstance(classification_rows, list):
        raise ValueError("source_classifications must be a list")
    classifications = {}; classification_keys = set()
    for record in classification_rows:
        record = object_value(record, "source classification")
        source_id = text(record.get("source_id"), "classification.source_id")
        version = integer(record.get("version"), "classification.version", minimum=1)
        key = (source_id, version)
        if key in classification_keys:
            raise ValueError("Duplicate source classification version")
        classification_keys.add(key)
        if timestamp(record.get("recorded_at")) > cutoff or timestamp(record.get("first_saved_at")) > cutoff:
            continue
        source = sources.get(source_id)
        if source is None:
            raise ValueError("Source classification has no saved source")
        if (record.get("source_sha256") != sha256(source["content"].encode()).hexdigest() or
                record.get("source_snapshot_sha256") != sha256(json_text(source).encode()).hexdigest()):
            raise ValueError("Source classification differs from its saved source snapshot")
        if text(record.get("basis_quote"), "classification.basis_quote") not in source["content"]:
            raise ValueError("Classification quote is absent from the saved source")
        if record.get("financial_content") is not None and type(record["financial_content"]) is not bool:
            raise ValueError("classification.financial_content must be boolean or null")
        if not isinstance(record.get("kind"), str) or record["kind"] not in KINDS:
            raise ValueError("Invalid source classification kind")
        if source_id not in classifications or version > classifications[source_id]["version"]:
            classifications[source_id] = record
    policies = {}; registry_counts = Counter()
    for entry in sections["policies"]:
        entry = object_value(entry, "policy entry")
        policy = validate_decision_policy(entry.get("policy"))
        key = (policy["id"], policy["version"])
        if key in policies:
            raise ValueError("Duplicate policy version")
        saved = timestamp(entry.get("first_saved_at"), "policy.first_saved_at")
        visible = saved <= cutoff and timestamp(policy["recorded_at"]) <= cutoff
        configured = all(policy["parameters"].get(p) is not None for p in _PARAMETERS)
        synthetic = any(p.get("kind") == "synthetic_example" for p in policy.get("parameter_sources", {}).values())
        policies[key] = {"available": visible, "configured": configured, "synthetic": synthetic}
        registry_counts["recorded"] += 1
        registry_counts["available"] += visible
        registry_counts["configured_available_nonsynthetic"] += visible and configured and not synthetic
    theses_by_company = defaultdict(list)
    for thesis in sections["theses"]:
        text(thesis.get("company_id"), "thesis.company_id")
        integer(thesis.get("version"), "thesis.version", minimum=1)
        timestamp(thesis.get("recorded_at"), "thesis.recorded_at")
        theses_by_company[thesis["company_id"]].append(thesis)
    questions_by_company = defaultdict(list)
    for question in sections["questions"]:
        questions_by_company[question["company_id"]].append(question)
    rows = []; actions = Counter()
    for company in sorted(companies, key=lambda c: c["id"]):
        company_id = company["id"]; contact = _contact(company, cutoff)
        local = by_company[company_id]
        usable = []; unavailable = []
        for source in local:
            if not available(source, cutoff):
                unavailable.append({"source_id": source["id"], "reason": "source_after_as_of"})
                continue
            try:
                issue = _check_source_origins([source["id"]], sources, company_id, cutoff)
            except ValueError as error:
                issue = str(error)
            if issue:
                unavailable.append({"source_id": source["id"], "reason": issue})
            else:
                usable.append(source)
        public = [s for s in usable if s["source_type"] == "public_disclosure"]
        index_only = [s for s in public if s["metadata"].get("index_only") is True or
                      classifications.get(s["id"], {}).get("kind") == "index_only"]
        financial = [s for s in public if s not in index_only and
                     (classifications[s["id"]].get("financial_content") is True if s["id"] in classifications else
                      s["metadata"].get("financial_document") is True or s["metadata"].get("document_kind") in _FINANCIAL_KINDS)]
        unclassified = [s for s in public if s not in index_only and s not in financial and
                        (s["id"] not in classifications or classifications[s["id"]].get("financial_content") is None)]
        market = [s for s in usable if s["source_type"] == "market_data"]
        historical = [t for t in theses_by_company[company_id] if timestamp(t["recorded_at"]) <= cutoff]
        latest = max(historical, key=lambda t: t["version"]) if historical else None
        thesis_issue = None
        if latest is not None:
            if not isinstance(latest.get("evidence_ids"), list) or not latest["evidence_ids"]:
                thesis_issue = "thesis_evidence_missing"
            else:
                try:
                    thesis_issue = _check_source_origins(latest["evidence_ids"], sources, company_id, timestamp(latest["recorded_at"]))
                except ValueError as error:
                    thesis_issue = str(error)
        references = []
        reference = company.get("decision_policy_ref")
        if isinstance(reference, dict):
            references.append({"id": reference.get("id"), "version": reference.get("version"),
                               "available_assignment": reference.get("recorded_at") is not None and timestamp(reference["recorded_at"]) <= cutoff,
                               "origin": "company_explicit_reference"})
        for question in questions_by_company[company_id]:
            contract = question.get("decision_contract")
            if isinstance(contract, dict) and contract.get("frozen_at") is not None and timestamp(contract["frozen_at"]) <= cutoff:
                references.append({"id": contract.get("policy_id"), "version": contract.get("policy_version"),
                                   "available_assignment": contract.get("synthetic", False) is False, "origin": "frozen_question_contract",
                                   "question_id": question["id"]})
        adopted = False
        for reference in references:
            state = policies.get((reference["id"], reference["version"]))
            reference["registered_policy_available"] = state is not None and state["available"]
            reference["configured_nonsynthetic"] = state is not None and state["configured"] and not state["synthetic"]
            adopted |= bool(reference["available_assignment"] and state is not None and state["available"] and state["configured"] and not state["synthetic"])
        needed = []
        if not contact["confirmed_available"]:
            needed.append({"kind": "confirm_ir_reception", "reason": contact["reason_codes"]})
        elif contact["individual_access"] != "explicit":
            needed.append({"kind": "confirm_individual_reception_conditions", "reason": "Individual access is not explicitly stated; no sending permission inferred."})
        if not financial:
            needed.append({"kind": "classify_saved_public_disclosures" if unclassified else "obtain_public_financial_content",
                           "saved_source_ids": [s["id"] for s in unclassified],
                           "reason": "Financial content is unclassified or missing; index entries and contact metadata are not financial evidence."})
        if not market:
            needed.append({"kind": "obtain_saved_market_data", "reason": "No available market source is saved; freshness and price-field suitability remain separate checks."})
        if latest is None or thesis_issue:
            needed.append({"kind": "prepare_sourced_thesis", "reason": thesis_issue or "No thesis available at the cutoff."})
        if not adopted:
            needed.append({"kind": "record_company_policy_adoption", "reason": "No available, fully configured, nonsynthetic policy assignment is evidenced for this company."})
        if company.get("financial_model") is None:
            needed.append({"kind": "review_financial_model", "reason": "No explicit model classification is saved; industry name alone does not exclude a company."})
        actions.update(action["kind"] for action in needed)
        rows.append({"company_id": company_id, "security_code": company.get("security_code"), "name": company.get("name"),
                     "current_status": company.get("status"), "current_held": company.get("held"),
                     "ir_contact": contact, "saved_source_count": len(local) if "sources" not in missing else None,
                     "available_public_disclosure_count": len(public) if "sources" not in missing else None,
                     "financial_content_source_ids": [s["id"] for s in financial],
                     "source_classification_refs": [{"source_id": s["id"], "version": classifications[s["id"]]["version"]}
                                                    for s in public if s["id"] in classifications],
                     "unclassified_public_source_ids": [s["id"] for s in unclassified],
                     "index_only_source_ids": [s["id"] for s in index_only],
                     "market_source_ids": [s["id"] for s in market], "unavailable_sources": unavailable,
                     "financial_content_available": bool(financial) if "sources" not in missing else None,
                     "market_data_available": bool(market) if "sources" not in missing else None,
                     "latest_thesis": None if latest is None else {"version": latest["version"], "recorded_at": latest["recorded_at"],
                          "current_price_jpy": latest.get("current_price_jpy"), "evidence_issue": thesis_issue},
                     "future_thesis_count": len(theses_by_company[company_id])-len(historical),
                     "policy_references": references, "configured_nonsynthetic_policy_assigned": adopted if "policies" not in missing else None,
                     "next_required_materials": needed})
    return {"status": "coverage_inventory_only", "as_of": cutoff.isoformat(), "company_count": len(rows),
            "snapshot_sections_missing": missing,
            "policy_registry": {k: registry_counts.get(k, 0) if "policies" not in missing else None for k in ("recorded", "available", "configured_available_nonsynthetic")},
            "summary": {"confirmed_contact_available": sum(r["ir_contact"]["confirmed_available"] for r in rows),
                        "individual_access": dict(Counter(r["ir_contact"]["individual_access"] or "unknown_or_unavailable" for r in rows)),
                        "with_financial_content": sum(bool(r["financial_content_source_ids"]) for r in rows) if "sources" not in missing else None,
                        "with_market_source": sum(bool(r["market_source_ids"]) for r in rows) if "sources" not in missing else None,
                        "with_available_thesis": sum(r["latest_thesis"] is not None and r["latest_thesis"]["evidence_issue"] is None for r in rows) if not {"theses", "sources"} & set(missing) else None,
                        "with_company_policy_assignment": sum(bool(r["configured_nonsynthetic_policy_assigned"]) for r in rows) if "policies" not in missing else None,
                        "status_counts": dict(Counter(r["current_status"] or "unknown" for r in rows)),
                        "held_true": sum(r["current_held"] is True for r in rows), "held_unknown": sum(r["current_held"] is None for r in rows)},
            "next_material_counts": dict(sorted(actions.items())), "companies": rows,
            "limitations": ["Company status and holdings are current saved metadata, not reconstructed historical positions.",
                            "Saved market-source coverage does not certify a fresh, tradable or source-bound decision quote.",
                            "Financial document classification is supplied metadata, not independent financial verification.",
                            "No GET, message, DB update, ranking, threshold, prior or likelihood estimate is performed."]}
