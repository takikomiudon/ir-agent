"""Offline scalar restatement of pinned disclosed amounts, using stdlib only.

This is independently written research arithmetic, not execution of crible,
provider data, an adopted financial model, or an assertion of accounting fit.
"""
from datetime import datetime, timezone
from decimal import Decimal, Inexact, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PIN_SHA = "786cb6ceeecc835b84be23d4d832d766ba195e9080984f10ab498957e424f6f7"
PERIODS = {"2025-03-31": "2024-04-01", "2026-03-31": "2025-04-01"}
# Each mapping is a research assertion, not provider/canonical certification.
MAPPING = {
    "reported_consolidated_current_assets": ("current_assets", "instant", "current-assets"),
    "reported_consolidated_tangible_fixed_assets": ("net_ppe", "instant", "tangible-fixed-assets"),
    "reported_consolidated_current_liabilities": ("current_liabilities", "instant", "current-liabilities"),
    "reported_consolidated_operating_income": ("operating_income_comparison_only", "annual_duration", "operating-income"),
    "reported_consolidated_profit_before_income_taxes": ("income_before_tax", "annual_duration", "profit-before-income-taxes"),
    "reported_consolidated_interest_expense": ("interest_expense", "annual_duration", "interest-expense"),
    "reported_consolidated_income_taxes_total": ("income_tax_expense", "annual_duration", "income-taxes-total"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def object_sha(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8"))


def integer_decimal(value, label):
    require(isinstance(value, str) and re.fullmatch(r"-?[0-9]+", value) is not None,
            f"{label}: explicit integer string required")
    number = Decimal(value)
    require(number.is_finite() and len(number.as_tuple().digits) <= 24,
            f"{label}: unsupported nonfinite/oversized input")
    return number


def amount(value):
    return format(value, "f")


def fraction(numerator, denominator, unit):
    require(denominator > 0, "fraction denominator must be positive")
    with localcontext() as context:
        context.prec, context.rounding = 80, ROUND_HALF_EVEN
        context.clear_flags()
        result = numerator / denominator
        inexact = bool(context.flags[Inexact])
    return {"numerator": amount(numerator), "denominator": amount(denominator),
            "decimal_approximation": amount(result), "unit": unit,
            "precision_significant_digits": 80, "rounding": "ROUND_HALF_EVEN",
            "division_inexact_at_this_precision": inexact}


def bind(pins, bundle, incoming):
    require(bundle["schema_version"] == 1 and bundle["theses"] == [], "unexpected bundle")
    require(len(bundle["sources"]) == 2, "exact origin plus one derived source required")
    origin, derived = bundle["sources"]
    require(origin == incoming["source"], "original source snapshot differs")
    require(origin["id"] == pins["original_source_id"], "origin ID differs")
    origin_sha = object_sha(origin)
    require(origin_sha == pins["original_source_canonical_sha256"], "origin object SHA differs")
    text = origin["content"]
    text_sha = digest(text.encode("utf-8"))
    require(text_sha == pins["original_source_content_sha256"], "origin content SHA differs")
    payload = json.loads(derived["content"])
    require(payload["original_source_id"] == origin["id"] and
            payload["original_source_content_sha256"] == text_sha, "derived origin differs")
    require(derived["metadata"]["original_source_snapshot_sha256"] == origin_sha,
            "derived snapshot binding differs")
    facts = payload["facts"]
    require(len(facts) == len(incoming["facts"]) == 14, "exact 14 facts required")
    require(len({f["id"] for f in facts}) == 14, "duplicate fact IDs")
    by_period = {end: {} for end in PERIODS}
    bindings = []
    for index, (fact, raw) in enumerate(zip(facts, incoming["facts"])):
        require(all(fact.get(key) == value for key, value in raw.items()),
                "normalized fact differs from original extraction")
        concept = fact["concept"]
        require(concept in MAPPING, "unexpected concept")
        canonical, kind, suffix = MAPPING[concept]
        period = fact["period"]
        end = period["end_date"]
        require(end in PERIODS and canonical not in by_period[end], "duplicate/unexpected period")
        require(period["period_kind"] == kind, "period kind differs")
        if kind == "instant":
            require(period["start_date"] is None and period["as_of_date"] == end,
                    "balance date differs")
        else:
            require(period["start_date"] == PERIODS[end], "annual duration differs")
        expected_id = f"5988-reported-{end.replace('-', '')}-{suffix}-annual-20260618"
        require(fact["id"] == expected_id, "fact ID/concept/period binding differs")
        scope = fact["scope"]
        require(fact["company_id"] == scope["company_id"] == "jp:5988" and
                fact["source_id"] == fact["original_source_id"] == origin["id"], "company/source differs")
        require(scope["consolidation_scope"] == "連結" and scope["historical_only"] is True,
                "entity or historical scope differs")
        require("accounting_basis" in scope and scope["accounting_basis"] is None,
                "unexpected accounting-basis assertion")
        require(fact["kind"] == "reported_fact" and fact["financial_inputs_verified"] is False and
                fact["meaning_review_required"] is True, "fact adoption category differs")
        require(fact["unit"] == "JPY" and fact["raw_unit_label"] == "百万円" and
                fact["normalization"]["explicit_unit_multiplier"] == "1000000" and
                fact["normalization"]["canonical_unit"] == "JPY", "unit/conversion differs")
        token = fact["raw_value"]
        require(isinstance(token, str) and
                re.fullmatch(r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)", token) is not None,
                "unrecognized display token; do not fill")
        value = integer_decimal(fact["value"], "normalized value")
        require(value == Decimal(token.replace(",", "")) * Decimal("1000000"), "amount differs")
        loc = fact["location"]
        quote = text[loc["source_character_start"]:loc["source_character_end"]]
        require(quote == fact["basis_quote"], "source quote offset differs")
        require(text.encode("utf-8")[loc["source_UTF8_byte_start"]:loc["source_UTF8_byte_end"]]
                == quote.encode("utf-8"), "source quote UTF8 offset differs")
        row = text[loc["row_source_character_start"]:loc["row_source_character_end"]]
        require(loc["row"] in row and token in row, "row label/token absent")
        require(text.encode("utf-8")[loc["row_UTF8_byte_start"]:loc["row_UTF8_byte_end"]]
                == row.encode("utf-8"), "row UTF8 offset differs")
        binding = {"fact_id": fact["id"], "reported_concept": concept,
                   "research_canonical_input": canonical, "value_JPY": amount(value),
                   "raw_value": token, "raw_unit": "百万円", "period": period,
                   "scope": scope, "definition": fact["definition"],
                   "mapping_kind": "explicit_research_only_not_provider_certified",
                   "normalization_input_pointer": f"/facts/{index}",
                   "normalization_value_pointer": f"/facts/{index}/raw_value",
                   "bundle_json_string_pointer": "/sources/1/content",
                   "parse_bundle_content_as": "JSON",
                   "decoded_fact_pointer": f"/facts/{index}",
                   "decoded_value_pointer": f"/facts/{index}/value",
                   "origin_bundle_pointer": "/sources/0", "origin_source_id": origin["id"],
                   "origin_canonical_SHA256": origin_sha, "origin_content_SHA256": text_sha,
                   "derived_source_id": derived["id"],
                   "derived_content_SHA256": digest(derived["content"].encode("utf-8")),
                   "source_location": loc, "scope_meaning_independently_verified": False}
        bindings.append(binding)
        by_period[end][canonical] = (value, fact["id"])
    require(all(len(group) == 7 for group in by_period.values()), "missing concept/period")
    return bindings, by_period


def compute(group):
    values = {key: value for key, (value, _) in group.items()}
    ids = {key: fact_id for key, (_, fact_id) in group.items()}
    ebit = values["income_before_tax"] + values["interest_expense"]
    wc = values["current_assets"] - values["current_liabilities"]
    capital = wc + values["net_ppe"]
    pbt, tax = values["income_before_tax"], values["income_tax_expense"]
    raw_tax, clipped, nopat = None, None, None
    clip_action = "undefined_nonpositive_PBT"
    if pbt > 0:
        raw_tax = fraction(tax, pbt, "ratio")
        if tax < 0:
            tax_num, tax_den, clip_action = Decimal(0), Decimal(1), "lower_clip"
        elif tax * 2 > pbt:
            tax_num, tax_den, clip_action = Decimal(1), Decimal(2), "upper_clip"
        else:
            tax_num, tax_den, clip_action = tax, pbt, "within_bounds"
        clipped = fraction(tax_num, tax_den, "ratio")
        nopat = fraction(ebit * (tax_den - tax_num), tax_den, "JPY")
    return {"input_fact_ids": ids,
            "fallback_scope": "No direct canonical EBIT/WC supplied in this selected 14-fact cohort; not a claim of issuer nondisclosure",
            "ebit_fallback_JPY": amount(ebit),
            "reported_operating_income_JPY_comparison_only": amount(values["operating_income_comparison_only"]),
            "same_as_reported_operating_income": ebit == values["operating_income_comparison_only"],
            "working_capital_fallback_JPY": amount(wc),
            "pretax_ROC_denominator_JPY": amount(capital),
            "pretax_ROC": fraction(ebit, capital, "ratio") if capital > 0 else None,
            "pretax_ROC_unresolved_reason": None if capital > 0 else "nonpositive_denominator",
            "raw_display_amount_tax_ratio": raw_tax,
            "maintainer_clipped_tax_ratio": clipped, "maintainer_clip_action": clip_action,
            "maintainer_clipped_NOPAT_research_JPY": nopat,
            "accounting_basis": None, "accounting_compatibility_verified": False,
            "company_normal_tax_rate_adopted": False,
            "model_financial_inputs_adopted": False}


def main():
    pin_bytes = (HERE / "input-pins.json").read_bytes()
    require(digest(pin_bytes) == PIN_SHA, "input manifest changed")
    pins = json.loads(pin_bytes)
    for path, expected in pins["files"].items():
        require(digest((ROOT / path).read_bytes()) == expected, f"pinned file changed: {path}")
    bundle = json.loads((ROOT / pins["bundle"]).read_bytes())
    incoming = json.loads((ROOT / pins["normalization_input"]).read_bytes())
    with localcontext() as context:
        context.prec, context.rounding = 80, ROUND_HALF_EVEN
        bindings, groups = bind(pins, bundle, incoming)
        periods = {end: compute(group) for end, group in groups.items()}
    output = {"kind": "independent_decimal_scalar_restatement_of_displayed_amounts",
              "company_id": "jp:5988", "research_only": True,
              "script_SHA256": digest(Path(__file__).read_bytes()),
              "input_manifest_SHA256": PIN_SHA, "input_file_SHA256": pins["files"],
              "bindings": bindings, "period_results": periods,
              "formulas": {"EBIT": "PBT + interest (C:189-190)",
                           "WC": "CA - CL (C:184-185)",
                           "pretax_ROC": "EBIT / (WC + netPPE), positive denominator (E:92-93)",
                           "tax_NOPAT": "tax/PBT with positive PBT; clip 0..0.5; EBIT*(1-clipped tax) (E:65-69)"},
              "not_calculated": {
                  "ROIC": {"value": None, "missing": ["two-period mapped total_equity", "two-period total_debt", "two-period cash_and_equivalents", "two-period total_assets"]},
                  "EY": {"value": None, "missing": ["source-bound price and observation time", "verified price-share denominator", "total_debt", "cash_and_equivalents"]},
                  "valuation": {"value": None, "reason": "no adopted model/forecast/valuation inputs"},
                  "rank": {"value": None, "reason": "EY/universe/rank kernel not supplied or adopted"},
                  "future_ROC_new": {"value": None, "reason": "historical pretax ROC or clipped NOPAT is not a future stable-period after-tax new-investment return"}},
              "limits": ["Accounting basis remains unknown, not verified by two equal nulls",
                         "Displayed million-JPY inputs do not expose unrounded economic amounts",
                         "Published p94 tax percentage is not an input or an exact-equality target",
                         "Tangible fixed assets to net_ppe and other canonical mappings are research assertions",
                         "No operating-income ROC variant; no ROC_new/policy/model adoption",
                         "Maintainer clipping is a financial convention, not company normal tax or Greenblatt author endorsement",
                         "No upstream/pandas runtime reproduction; Decimal division is labeled approximation"],
              "recorded_at": datetime.now(timezone.utc).isoformat()}
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    print("PASS: frozen files; 14 unique source-bound facts; 7 concepts x 2 periods; research-only scalar output", file=sys.stderr)


if __name__ == "__main__":
    main()
