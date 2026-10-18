"""Historical per-share NCAV screen bridge; local saved inputs only, stdout only."""
import json
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, localcontext, ROUND_HALF_UP

here = Path(__file__).resolve().parent
x = json.loads((here / "inputs.json").read_bytes())
issued = int(x["end_issued_common_including_treasury_raw"].replace(",", ""))
treasury = int(x["end_treasury_common_raw"].replace(",", ""))
end_common = issued - treasury
assert end_common > 0
f = x["accepted_company_NCAV_ceiling_JPY_fraction"]
company_ceiling = Fraction(f["numerator"], f["denominator"])
boundary = company_ceiling / end_common
with localcontext() as ctx:
    ctx.prec = 60
    display = (Decimal(boundary.numerator) / Decimal(boundary.denominator)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
result = {
    "company_id": x["company_id"], "historical_accounting_as_of": x["historical_accounting_as_of"],
    "period_end_issued_common_including_treasury": issued, "reported_treasury_common": treasury,
    "project_mapped_period_end_outstanding_common": end_common, "denominator_label": x["period_end_common_label"], "weighted_average_used": False,
    "average_fallback_used": False, "accepted_company_screen_ceiling_JPY": {"numerator": company_ceiling.numerator, "denominator": company_ceiling.denominator},
    "historical_screen_boundary_JPY_per_share_exact": {"numerator": boundary.numerator, "denominator": boundary.denominator},
    "reference_display_JPY_per_share_2dp": str(display), "display_rounding": "ROUND_HALF_UP, reference only",
    "comparison_boundary": "exact fraction above; 2dp display is not a trading threshold",
    "observed_price_JPY": None, "observed_market_cap_JPY": None, "screen_pass": None,
    "current_outstanding_shares": None, "buy_price_or_order_or_exit_trigger": None,
    "fair_value_certified": False, "ordinary_common_claims_and_recoverability_certified": False,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
