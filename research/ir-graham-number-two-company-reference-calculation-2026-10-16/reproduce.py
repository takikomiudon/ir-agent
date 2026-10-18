"""Read pinned inputs; print a price-free, non-adopted historical reference.

No network, Store, normalizer, ingestion or output-file mutation is performed.
The private production helpers are used deliberately because the public wrapper
requires a market-price argument and returns price-derived ratios.
"""

from __future__ import annotations

from decimal import (Context, Decimal, DivisionByZero, InvalidOperation,
                     Overflow, ROUND_HALF_EVEN, ROUND_HALF_UP, Underflow,
                     getcontext, localcontext)
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ir_agent import valuation as production
from ir_agent.models import json_text, timestamp


def load(path):
    return json.loads(path.read_bytes())


def check_pins(pins):
    for item in pins:
        path = ROOT / item["file"]
        if sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Pinned input changed: " + item["file"])


def rational(value):
    return {"numerator": str(value.numerator),
            "denominator": str(value.denominator)}


def context(precision, rounding):
    return Context(prec=precision, rounding=rounding, Emin=-999999,
                   Emax=999999, flags=[],
                   traps=[InvalidOperation, DivisionByZero, Overflow, Underflow])


def fingerprint():
    current = getcontext()
    return (current.prec, current.rounding, current.Emin, current.Emax,
            current.capitals, current.clamp,
            tuple(sorted((key.__name__, value)
                         for key, value in current.traps.items())),
            tuple(sorted((key.__name__, value)
                         for key, value in current.flags.items())))


def exact_rounding_interval(root_value, exact_radicand):
    exponent = root_value.as_tuple().exponent
    ulp = (Fraction(10 ** exponent) if exponent >= 0
           else Fraction(1, 10 ** (-exponent)))
    center = Fraction(root_value)
    lower, upper = center - ulp / 2, center + ulp / 2
    # Strict containment excludes a midpoint/tie and proves this rounding.
    assert lower > 0 and lower * lower < exact_radicand < upper * upper
    return {"half_ulp_exact": rational(ulp / 2),
            "strict_lower_square_below_radicand": True,
            "strict_upper_square_above_radicand": True}


def main():
    bindings = load(HERE / "input-bindings.json")
    check_pins(bindings["external_pins"])
    before = fingerprint()
    rows = []
    for company in bindings["companies"]:
        request = load(ROOT / company["audit_request"])
        audit = load(ROOT / company["audit_result"])
        native = load(ROOT / company["native_binding"])
        bundle = load(ROOT / company["normalized_bundle"])
        code = company["security_code"]
        assert request["company_id"] == audit["company_id"] == "jp:" + code
        assert audit["status"] == "source_values_matched"
        assert audit["missing_paths"] == []
        assert audit["meaning_review_required"] is True
        assert audit["financial_inputs_verified"] is False
        assert request["as_of"] == audit["as_of"]
        assert request["valuation"] == company["valuation"]
        assert request["valuation"]["aggregation"] == "unweighted"
        sources = {source["id"]: source for source in request["sources"]}
        assert len(sources) == 2
        assert sources == {source["id"]: source for source in bundle["sources"]}
        source_hashes = {key: sha256(json_text(value).encode()).hexdigest()
                         for key, value in sources.items()}
        assert source_hashes == audit["source_snapshot_sha256"]
        assert {item["source_id"]: item["native_SHA"]
                for item in native["source_bindings"]} == source_hashes
        for item in native["source_bindings"]:
            assert item["wholeobject_matches_original_file_audit"] is True
            for receipt in item["actual_availability"]:
                assert timestamp(receipt["first_saved_at"]) <= timestamp(request["as_of"])
        assert len(audit["inputs"]) == 2
        assert all(item["status"] == "source_value_matched"
                   and item["reason_codes"] == [] for item in audit["inputs"])

        prepared = production._prepare(request["valuation"])
        assert len(prepared) == 1
        scenario = prepared[0]
        assert scenario.method == "graham_number" and scenario.probability is None
        assert 80 <= production._GRAHAM_MAX_CONTEXT_PRECISION
        values = request["valuation"]["scenarios"][0]["inputs"]
        fact_bindings = []
        for key in ("eps_jpy", "book_value_per_share_jpy"):
            path = "scenarios." + scenario.name + ".inputs." + key
            origin = request["provenance"][path]
            value_path = origin["value_path"]
            assert value_path[:2] == ["content", "facts"]
            assert type(value_path[2]) is int and value_path[3:] == ["value"]
            source = sources[origin["source_id"]]
            fact = json.loads(source["content"])["facts"][value_path[2]]
            assert origin["kind"] == fact["kind"] == "reported_fact"
            assert origin["unit"] == fact["unit"] == "JPY-per-share"
            assert values[key] == fact["value"]
            fact_bindings.append({
                "input": key, "value": fact["value"],
                "fact_id": fact["id"], "kind": fact["kind"],
                "unit": fact["unit"], "period": fact["period"],
                "source_id": source["id"], "value_path": value_path,
                "native_snapshot_sha256": source_hashes[source["id"]],
                "original_source_id": fact["original_source_id"],
                "financial_inputs_verified": False,
            })

        # Actual existing production kernel after its own input validation.
        # No price argument or wrapper output is created.
        with localcontext(context(80, ROUND_HALF_UP)):
            core, details = production._fair_value(scenario)
            production_display = format(core.quantize(Decimal("0.01"),
                                                       rounding=ROUND_HALF_UP), "f")
        assert details == {} and core.is_finite() and core > 0

        # Independent exact arithmetic on the specified displayed inputs.
        eps = Fraction(values["eps_jpy"])
        bps = Fraction(values["book_value_per_share_jpy"])
        radicand = Fraction("22.5") * eps * bps
        with localcontext(context(120, ROUND_HALF_EVEN)):
            exact_decimal_radicand = Decimal(radicand.numerator) / Decimal(radicand.denominator)
        assert Fraction(exact_decimal_radicand) == radicand
        with localcontext(context(60, ROUND_HALF_EVEN)):
            independent = exact_decimal_radicand.sqrt()
            rounded_core = +core
            independent_display = format(independent.quantize(Decimal("0.01"),
                                                              rounding=ROUND_HALF_UP), "f")
        assert independent == rounded_core
        assert independent_display == production_display
        independent_proof = exact_rounding_interval(independent, radicand)
        core_proof = exact_rounding_interval(core, radicand)
        rows.append({
            "company_id": company["company_id"], "security_code": code,
            "source_bindings": fact_bindings,
            "frozen_actual_input_audit_status": audit["status"],
            "source_native_hashes": source_hashes,
            "production": {
                "path": "ir_agent.valuation._prepare -> _fair_value",
                "context_precision": 80,
                "reference_JPY_per_share_decimal80": format(core, "f"),
                "reference_JPY_per_share_display2_HALF_UP": production_display,
                "exact_midpoint_interval_proof": core_proof,
                "public_wrapper_executed": False,
            },
            "independent": {
                "EPS_exact": rational(eps), "BPS_exact": rational(bps),
                "radicand_exact_JPY_squared_per_share_squared": rational(radicand),
                "radicand_terminating_decimal_exact": format(exact_decimal_radicand, "f"),
                "sqrt_decimal60_HALF_EVEN": format(independent, "f"),
                "reference_display2_HALF_UP": independent_display,
                "exact_midpoint_interval_proof": independent_proof,
            },
            "production80_rounded60_equals_independent60": True,
            "price_jpy": None, "dummy_price_used": False,
            "margin_of_safety": None, "price_derived_ratios": None,
            "expected_value": None, "investment_action": None,
            "financial_adopted": False, "meaning_certified": False,
        })

    old = load(ROOT / bindings["old_1975_lane_A"])
    old_a = next(item for item in old["lanes"] if item["lane"] == "A_direct_issuer_display")
    current = next(item for item in rows if item["security_code"] == "1975")
    assert (current["independent"]["sqrt_decimal60_HALF_EVEN"]
            == old_a["sqrt_Decimal60_JPY_per_share"])
    assert (current["independent"]["radicand_exact_JPY_squared_per_share_squared"]
            == old_a["radicand_exact_JPY_squared_per_share_squared"])
    assert before == fingerprint()
    check_pins(bindings["external_pins"])
    return {
        "status": "source_bound_historical_reference_arithmetic_reproduced",
        "formula": "sqrt(22.5 * EPS * BPS)",
        "method_author": "maxgfr/crible maintainers, fixed commit00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7",
        "companies": rows,
        "prior_1975_lane_A_exact60_and_radicand_match": True,
        "prior_lane_B_not_used": True,
        "price_free_public_API_available": False,
        "private_validated_production_core_used": True,
        "public_wrapper_response": None,
        "caller_decimal_context_unchanged": True,
        "pins_before_after_unchanged": True,
        "financial_adoption_or_original_Graham_strategy_certified": False,
        "GET_DB_Store_upstream_import_normalize_or_sharedcode_changes": 0,
    }


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, allow_nan=False))
