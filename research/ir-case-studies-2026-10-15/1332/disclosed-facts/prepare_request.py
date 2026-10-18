"""One-time declaration creation from existing captures; no network or DB.

Use build_and_verify.py for replays. Refuse to overwrite an existing request.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASE = HERE.parent


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    if (HERE / "normalization-request.json").exists():
        raise SystemExit("Keep the saved review immutable; use build_and_verify.py to replay")
    followup = CASE / "statement-calendar-followup"
    source = next(s for s in json.loads((followup / "source-bundle.json").read_text())["sources"]
                  if s["metadata"]["capture_source_id"] == "nissui-statement-calendar-01")
    supplement = next(s for s in json.loads((CASE / "source-bundle.json").read_text())["sources"]
                      if s["metadata"]["capture_source_id"] == "nissui1332-04")
    pages = source["content"].split("\f")
    first, seventh = pages[0], pages[6]
    actual_quote = first[first.index("１．2027年３月期第１四半期の連結業績"):first.index("(注) 包括利益")]
    eps_quote = first[first.index("潜在株式調整後"):first.index("（２）連結財政状態")]
    guidance_quote = seventh[seventh.index("2027年３月期   通期連結業績予想数値の修正"):seventh.index("         差額（Ｂ－Ａ）")]
    actual_period = {"label": "2027年３月期第１四半期連結累計期間", "start_date": "2026-04-01", "end_date": "2026-06-30",
                     "frequency": "quarterly", "aggregation": "first_quarter_cumulative", "standalone_quarter_derived": False,
                     "actual_or_forecast": "reported_actual"}
    guidance_period = {"label": "2027年３月期通期連結会社予想", "start_date": "2026-04-01", "end_date": "2027-03-31",
                       "frequency": "annual", "aggregation": "full_year_guidance", "actual_or_forecast": "issuer_guidance",
                       "as_published_date": "2026-08-06"}

    def fact(identifier, concept, kind, raw, raw_unit, unit, quote, page, row, column, definition, share_basis=None):
        actual = kind == "reported_fact"
        scope = {"company_id": "jp:1332", "entity": "株式会社ニッスイグループ", "consolidation": "consolidated",
                 "accounting_basis_as_stated": "日本基準", "accounting_meaning_verified": False,
                 "comparability_review_required": True}
        if share_basis:
            scope["share_basis"] = share_basis
        start = pages[page-1].index(quote)
        return {"id": identifier, "concept": concept, "kind": kind, "raw_value": raw,
                "raw_unit_label": raw_unit, "unit": unit,
                "raw_period_label": "2027年３月期第１四半期" if actual else "2027年３月期",
                "period": actual_period if actual else guidance_period, "basis_quote": quote,
                "definition": definition, "scope": scope,
                "location": {"pdf_page": page, "printed_page": None if page == 1 else page-2,
                             "saved_text": "1332/statement-calendar-followup/01.txt",
                             "section": "連結経営成績(累計)" if actual else "通期連結業績予想数値の修正",
                             "row_label": row, "column_label": column, "page_text_start": start,
                             "page_text_end_exclusive": start+len(quote),
                             "character_offset_unit": "Unicode code points, zero-based, end exclusive"}}

    facts = [
        fact("nissui1332-2027q1-basic-eps", "reported_basic_eps", "reported_fact", "24.53", "円", "JPY-per-share",
             eps_quote, 1, "2027年３月期第１四半期", "１株当たり四半期純利益（潜在株式調整後の隣列とは別）",
             "当1Q連結累計の１株当たり四半期純利益。潜在株式調整後欄のダッシュは0ではない。前年同期20.94円、通期予想95.62円と区別し、円銭表示の小数値を円/株として保持する抽出主張。年率換算・将来EPS・モデル採用なし。",
             "basic/unadjusted column; weighted-average denominator and dilution meaning require review"),
        fact("nissui1332-2027fy-company-eps", "issuer_forecast_eps", "issuer_guidance", "95.62", "円", "JPY-per-share",
             guidance_quote, 7, "今回発表予想（Ｂ）", "1株当たり当期純利益",
             "2026年8月6日短信の今回発表予想(B)行の通期１株当たり当期純利益。前回予想(A)も同額だが別行。当1Q実績や前期実績と区別し、会社予想を自作予測・達成実績として採用しない。",
             "unadjusted one-share earnings; forward share count and dilution assumptions not independently verified"),
        fact("nissui1332-2027q1-consolidated-operating-income", "reported_consolidated_operating_income", "reported_fact",
             "12,435", "百万円", "JPY", actual_quote, 1, "2027年３月期第１四半期", "営業利益／百万円",
             "当1Q連結累計の営業利益12,435百万円。前年同期10,281百万円、増減率20.9%、当期経常利益11,670百万円と区別する。正常化利益、EBITDA、営業CFへ読み替えない。"),
        fact("nissui1332-2027fy-company-operating-income", "issuer_forecast_consolidated_operating_income", "issuer_guidance",
             "42,500", "百万円", "JPY", guidance_quote, 7, "今回発表予想（Ｂ）", "営業利益／百万円",
             "今回発表予想(B)行の通期連結営業利益42,500百万円。営業利益は前回予想(A)から据置であり、全体の業績予想修正有を営業利益上方修正と解釈しない。達成実績・全サイクル正常営業利益・自作シナリオとして採用しない。"),
    ]
    now = datetime.now(timezone.utc).isoformat()
    review = {"author": "agent:/root/quote_normalization", "recorded_at": now,
              "rationale": "正式短信PDF1・7頁を原PDF画像と保存本文で照合した4公表値。基本/潜在株式調整後、当期/比較期、累計/通期、実績/会社予想を区別。連結比較範囲・在池魚評価・株数・四半期CF未作成の意味レビューは別途保持し、会計意味・モデル適合・正常化・モデル採用は未検証。"}

    def cite(identifier, cited_source, page, begin, end):
        text = cited_source["content"].split("\f")[page-1]
        start = text.index(begin)
        finish = text.index(end, start) + len(end)
        return {"id": identifier, "source_id": cited_source["id"], "pdf_page": page,
                "printed_page": None if page <= 2 else page-2,
                "page_text_start": start, "page_text_end_exclusive": finish, "quote": text[start:finish]}

    citations = [
        cite("formal-accounting-and-entity", source, 1, "2027年３月期", "第１四半期決算短信〔日本基準〕(連結)"),
        cite("formal-period", source, 1, "１．2027年３月期", "2026年６月30日）"),
        cite("in-quarter-scope", source, 2, "（１）当四半期連結累計期間における連結範囲の重要な変更", "：無"),
        cite("share-denominator", source, 2, "（４）発行済株式数（普通株式）", "上控除する自己株式数に含めております。"),
        cite("new-consolidation-comparison", source, 5, "【南米】", "りました。"),
        cite("formal-quarter-cf-not-prepared", source, 13, "当第１四半期連結累計期間に係る四半期連結キャッシュ", "とおりであります。"),
        cite("guidance-updated-vs-unchanged", source, 7, "売上高は、為替前提の見直し", "セグメント別業績予想を修正しております。"),
        cite("fish-valuation-component", supplement, 27, "※1 生簀にいる出荷前の魚", "※2 在庫に含まれる未実現利益の調整"),
        cite("fish-ifrs-component", supplement, 27, "         在池魚評価損益", "（IFRS評価）※1"),
        cite("fish-comparison-scope", supplement, 27, "＜在池魚評価損益 内訳＞", "SA社・Yadran社計"),
        cite("reported-amount-precision", source, 1, "(百万円未満切捨て)", "(百万円未満切捨て)"),
    ]
    for citation in citations:
        if citation["source_id"] == supplement["id"]:
            citation["printed_page"] = 27
    meaning = {
        "schema_version": 1, "recorded_at": now, "company_id": "jp:1332", "status": "meaning_review_required",
        "citations": citations,
        "limitations": [
            "Formal consolidated reporting states Japanese GAAP; the supplement labels a fish-valuation component IFRS. The consolidated bridge has not been reconciled.",
            "No significant scope change within this quarter is not proof of like-for-like prior-year scope: formal narrative mentions a new South American consolidated subsidiary; supplement compares SA with SA plus Yadran.",
            "Basic and potential-share-adjusted EPS are separate. Diluted dash is not zero; weighted-average, treasury/BBT-RS and future dilution assumptions need review.",
            "Formal quarterly consolidated CF statement was not prepared. Supplemental CF cannot become verified formal-quarterly-CF data through this extraction.",
            "FY guidance is as published 2026-08-06, not achieved results, a project forecast, calibrated probability or endorsed valuation input.",
            "The cover states amounts below one million yen are truncated. Multiplying the disclosed million-yen token into JPY preserves the display basis; it does not verify the underlying amount to single-yen precision.",
        ], "financial_inputs_verified": False, "model_adopted": False}
    existing = {}
    for directory in (CASE, followup):
        for name in ("manifest.json", "source-bundle.json"):
            path = directory/name
            existing[str(path.relative_to(CASE))] = sha256(path.read_bytes()).hexdigest()
    write(HERE / "normalization-request.json", {"company_id": "jp:1332", "source": source, "review": review, "facts": facts})
    write(HERE / "meaning-review.json", meaning)
    write(HERE / "baseline.json", {"recorded_at": now, "existing_input_files": existing})
    print("Created explicit four-fact review at", now)


if __name__ == "__main__":
    main()
