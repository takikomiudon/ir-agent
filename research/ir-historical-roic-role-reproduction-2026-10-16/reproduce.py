"""One selected FY2026 role-based Decimal research calculation; stdlib only."""
from datetime import datetime, timezone
from decimal import Decimal, Inexact, ROUND_HALF_EVEN, localcontext
from hashlib import sha1, sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PIN_SHA = "56f28e652c51306ba65639f288b1d439c4db3a950b1b8eb9cafbaabecd868289"
SUFFIXES = [
    "20250331-cash-and-cash-equivalents-annual-20260618",
    "20260331-cash-and-cash-equivalents-annual-20260618",
    "20250331-net-assets-for-common-shares-annual-20260618",
    "20260331-net-assets-for-common-shares-annual-20260618",
    "20250331-total-assets-annual-20260618",
    "20260331-total-assets-annual-20260618",
    "annual-20260618-borrowings-schedule-total-opening_balance",
    "annual-20260618-borrowings-schedule-total-closing_balance",
]
ROLES = ["C_opening_reference", "C_closing", "E_opening_reference", "E_closing",
         "A_opening_reference", "A_closing", "D_opening", "D_closing"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def object_sha(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode())


def fraction(numerator, denominator, unit):
    require(denominator > 0, "positive denominator required")
    with localcontext() as context:
        context.prec, context.rounding = 80, ROUND_HALF_EVEN
        context.clear_flags()
        value = numerator / denominator
        return {"numerator": format(numerator, "f"),
                "denominator": format(denominator, "f"),
                "decimal_approximation": format(value, "f"), "unit": unit,
                "precision_significant_digits": 80, "rounding": "ROUND_HALF_EVEN",
                "division_inexact_at_this_precision": bool(context.flags[Inexact])}


def main():
    pin_bytes = (HERE / "input-pins.json").read_bytes()
    require(digest(pin_bytes) == PIN_SHA, "pin manifest changed")
    pins = json.loads(pin_bytes)
    documents = {}
    for key, ref in pins["references"].items():
        data = (ROOT / ref["path"]).read_bytes()
        require(digest(data) == ref["sha256"], f"pinned file changed: {key}")
        if key in pins["git_blob_SHA1"]:
            blob = b"blob " + str(len(data)).encode() + b"\0" + data
            require(sha1(blob).hexdigest() == pins["git_blob_SHA1"][key], "Git blob mismatch")
        if ref["path"].endswith(".json"):
            documents[key] = json.loads(data)
    selection = documents["selection"]
    require(selection["status"] == "selected_for_conditional_research_arithmetic_only"
            and selection["financial_model_inputs_adopted"] is False, "selection scope changed")
    require(selection["independent_balance_fact_review_sha256"] ==
            pins["references"]["balance8_independent_review"]["sha256"], "review mismatch")
    require(documents["balance8_parent_acceptance"]["financial_inputs_adopted"] is False,
            "display-fact acceptance is not financial adoption")
    b8, b14 = documents["balance8_bundle"], documents["old14_bundle"]
    origin = b8["sources"][0]
    require(origin == b14["sources"][0], "different original source")
    original_sha = object_sha(origin)
    content_sha = digest(origin["content"].encode())
    payload = json.loads(b8["sources"][1]["content"])
    facts = payload["facts"]
    require(len(facts) == len(documents["balance8_input"]["facts"]) == 8, "exact eight facts required")
    require(len({f["id"] for f in facts}) == 8, "duplicate facts")
    amounts, bindings = {}, []
    with localcontext() as context:
        context.prec, context.rounding = 80, ROUND_HALF_EVEN
        for i, (fact, suffix, role) in enumerate(zip(facts, SUFFIXES, ROLES)):
            raw = documents["balance8_input"]["facts"][i]
            require(all(fact.get(k) == v for k, v in raw.items()), "extraction changed")
            require(fact["id"] == "5988-reported-" + suffix, "fact role mismatch")
            require(fact["company_id"] == "jp:5988" and
                    fact["source_id"] == origin["id"], "company/source mismatch")
            require(fact["unit"] == "JPY" and fact["raw_unit_label"] == "百万円", "unit mismatch")
            require(fact["scope"]["accounting_basis"] is None and
                    fact["scope"]["canonical_financial_field_binding"] is None,
                    "do not silently certify accounting/canonical scope")
            value = Decimal(fact["value"])
            require(value.is_finite() and
                    value == Decimal(fact["raw_value"].replace(",", "")) * Decimal("1000000"),
                    "display amount conversion mismatch")
            period = fact["period"]
            if role.startswith("D_"):
                require(all(period[k] is None for k in
                            ("as_of_date", "start_date", "end_date", "exact_calendar_date_binding")),
                        "debt dates must stay null")
                require(period["boundary_role"] ==
                        ("opening_balance" if role == "D_opening" else "closing_balance"), "debt role mismatch")
            else:
                expected = "2025-03-31" if role.endswith("opening_reference") else "2026-03-31"
                require(period["as_of_date"] == period["end_date"] == expected, "balance date mismatch")
            loc = fact["location"]
            require(origin["content"][loc["source_character_start"]:loc["source_character_end"]]
                    == fact["basis_quote"], "original quote mismatch")
            amounts[role] = value
            bindings.append({"fact_id": fact["id"], "reported_concept": fact["concept"],
                             "value_JPY": fact["value"], "raw_value": fact["raw_value"],
                             "raw_unit": fact["raw_unit_label"], "research_role": role,
                             "original_period_unchanged": period, "scope_unchanged": fact["scope"],
                             "bundle_content_pointer": "/sources/1/content", "parse_as": "JSON",
                             "decoded_fact_pointer": f"/facts/{i}",
                             "decoded_value_pointer": f"/facts/{i}/value",
                             "origin_source_id": origin["id"], "origin_object_SHA256": original_sha,
                             "origin_content_SHA256": content_sha, "source_location": loc})
        previous = documents["existing_NOPAT_output"]
        require(previous["company_id"] == "jp:5988" and previous["research_only"] is True,
                "prior result scope mismatch")
        require(previous["input_file_SHA256"][pins["references"]["old14_bundle"]["path"]]
                == pins["references"]["old14_bundle"]["sha256"], "NOPAT bundle lineage mismatch")
        prior_ids = previous["period_results"]["2026-03-31"]["input_fact_ids"]
        used_ids = {prior_ids[key] for key in ("income_before_tax", "interest_expense", "income_tax_expense")}
        prior_bindings = [binding for binding in previous["bindings"] if binding["fact_id"] in used_ids]
        require(len(prior_bindings) == 3 and all(binding["origin_canonical_SHA256"] == original_sha
                for binding in prior_bindings), "NOPAT fact lineage mismatch")
        nopat_ref = previous["period_results"]["2026-03-31"]["maintainer_clipped_NOPAT_research_JPY"]
        nopat_num, nopat_den = Decimal(nopat_ref["numerator"]), Decimal(nopat_ref["denominator"])
        require(nopat_num.is_finite() and nopat_den.is_finite() and nopat_den > 0, "invalid NOPAT")
        opening = amounts["E_opening_reference"] + amounts["D_opening"] - amounts["C_opening_reference"]
        closing = amounts["E_closing"] + amounts["D_closing"] - amounts["C_closing"]
        average_capital = (opening + closing) / Decimal(2)
        average_assets = (amounts["A_opening_reference"] + amounts["A_closing"]) / Decimal(2)
        minimum_capital = average_assets * Decimal("0.1")
        guard = average_capital > 0 and average_capital >= minimum_capital
        roic = fraction(nopat_num, nopat_den * average_capital, "ratio") if guard else None
    output = {"kind": "one_FY2026_conditional_role_scalar_research",
              "conditional_on_research_mapping": True, "FY_start_context": "2025-04-01",
              "FY_end_context": "2026-03-31", "selection": selection,
              "script_SHA256": digest(Path(__file__).read_bytes()), "input_manifest_SHA256": PIN_SHA,
              "input_pins": pins, "balance_fact_bindings": bindings,
              "existing_NOPAT": {"source_file": pins["references"]["existing_NOPAT_output"],
                                  "pointer": "/period_results/2026-03-31/maintainer_clipped_NOPAT_research_JPY",
                                  "rational_value_unchanged": nopat_ref,
                                  "input_fact_ids": prior_ids,
                                  "source_fact_bindings_reused_unchanged": prior_bindings},
              "role_arithmetic": {"opening_capital_JPY": format(opening, "f"),
                                  "closing_capital_JPY": format(closing, "f"),
                                  "average_capital_JPY": format(average_capital, "f"),
                                  "average_total_assets_JPY": format(average_assets, "f"),
                                  "maintainer_10percent_threshold_JPY": format(minimum_capital, "f"),
                                  "maintainer_positive_capital_and_10percent_guard_pass": guard,
                                  "conditional_FY2026_role_ROIC": roic},
              "not_calculated": {"strict_dated_window_FY2026_ROIC": {"value": None, "reason": "debt dates null; C.average dated window not reproduced"},
                                 "FY2025_ROIC": {"value": None, "reason": "2024 opening reference inputs absent"},
                                 "future_ROC_new": {"value": None, "reason": "historical hypothetical scope is not future after-tax new investment return"},
                                 "EY": {"value": None, "reason": "price/share bindings outside scope"},
                                 "valuation": {"value": None, "reason": "no adopted valuation inputs"},
                                 "rank": {"value": None, "reason": "no universe or adopted rank kernel"}},
              "equity_provider_and_profit_scope_equivalence_verified": False,
              "lease_debt_provider_scope_equivalence_verified": False,
              "accounting_compatibility_verified": False, "financial_inputs_adopted": False,
              "upstream_runtime_reproduced": False, "IR_price_branch_policy_changed": False,
              "recorded_at": datetime.now(timezone.utc).isoformat()}
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    print("PASS: one FY2026 role calculation; dates unchanged/null; conditional research only", file=sys.stderr)


if __name__ == "__main__":
    main()
