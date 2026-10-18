"""Saved two-input NCAV arithmetic only. No network, database, or upstream imports."""
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

here = Path(__file__).resolve().parent
inputs = json.loads((here / "inputs.json").read_bytes())
unit = Decimal(inputs["JPY_per_reported_unit"])
periods = []
for item in inputs["periods"]:
    assets = Decimal(item["current_assets"]["raw_value"].replace(",", ""))
    liabilities = Decimal(item["total_liabilities"]["raw_value"].replace(",", ""))
    ncav = assets - liabilities
    ceiling = Fraction(ncav) * Fraction(2, 3)
    yen_ceiling = ceiling * Fraction(unit)
    periods.append({
        "role": item["role"], "as_of": item["as_of"],
        "current_assets_reported_million_JPY": str(assets),
        "all_liabilities_reported_million_JPY": str(liabilities),
        "ncav_reported_million_JPY": str(ncav),
        "ncav_reported_equivalent_JPY": str(ncav * unit),
        "screen_market_cap_ceiling_million_JPY_exact": {"numerator": ceiling.numerator, "denominator": ceiling.denominator},
        "screen_market_cap_ceiling_reported_equivalent_JPY_exact": {"numerator": yen_ceiling.numerator, "denominator": yen_ceiling.denominator},
        "observed_market_cap_JPY": None, "observed_share_price_JPY": None,
        "ncav_to_market_cap": None, "screen_pass": None, "per_share_ceiling_JPY": None,
        "comparison_status": "unresolved_missing_market_cap",
    })
print(json.dumps({"company_id": inputs["company_id"], "formula": "current_assets - total_liabilities", "screen_rule": "market_cap <= (2/3) * NCAV", "precision": "Exact arithmetic on reported truncated-million-JPY inputs, not exact underlying ledger yen.", "periods": periods}, ensure_ascii=False, indent=2))
