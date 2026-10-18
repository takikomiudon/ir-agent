# 規制資本再投資から株主CFの中間量を計算する

Damodaranの金融機関評価原典p22にある、次の式だけを再現する。

```text
FCFE = 純利益 − 規制資本への再投資
```

```bash
.venv/bin/ir-agent regulatory-fcfe examples/regulatory-fcfe.json
```

例は架空の年次入力15−10=5。実企業の予測・資本政策・株価ではない。CLIはDBを開かず、APIは`calculate_regulatory_fcfe`。原典p22の[本文・画像・SHA](../research/ir-regulatory-fcfe-integration-2026-10-15/author-evidence.json)を確認し、[金融評価仕様](financial-equity-valuation-spec.md)の未実装だった中間計算へ接続した。

## 入力

最上位は`method, basis, rows, assessment`だけ。methodは`financial_regulatory_fcfe`。basisは`company_id, currency, amount_unit, entity_scope, equity_scope`で、通貨は大文字3文字、金額単位はunits/thousands/millions/billions。通貨や億円の換算はしない。

rowsは空でない配列。各rowは`period, net_income, regulatory_capital_reinvestment`を持つ。periodは`kind: full_fiscal_year`とlabel/start/end。期間は明示し、年次rowの重複・逆順・重なりを拒否する。最初のAPIの対象は明示年次入力であり、四半期実績を年率化しない。日数だけで52/53週や年次適合を認定する機能でもない。

各金額は次の情報を持つ。

- value：有限Decimal文字列。0・負の値を許し、nullやboolを0にしない。
- concept：純利益は`net_income_to_equity_holders`、再投資は`regulatory_capital_reinvestment`。営業利益や総資本残高を代用しない。
- basisとperiod：共通の会社・通貨・金額単位・主体・株主範囲と、当該rowの期間に完全一致する宣言。
- measurement_basis：それぞれの会計/資本測定の定義。利益の会計基準と規制資本の定義は異なり得るため、同じ文字列であることを要求しない。
- data_kind：reported_fact / issuer_guidance / author_estimate / explicit_assumption / synthetic_example。
- source_refs：`id, version, sha256, location, quote`。version/SHAは不明ならnull。参照を解決したり、引用の正しさを認定したりしない。
- rationale：その入力を渡す理由。

assessmentにはcapital_definition_rationale / capital_target_and_buffer_rationale / equity_claim_scope_rationale / forecast_comparability_rationaleとsource_refsを置く。未確認の説明はnullのまま返し、入力や根拠を作らない。

## 結果と適用限界

各年のNI・再投資・FCFEを元の金額単位で返す。小数計算は隔離したDecimal contextで行い、負のFCFEを0へ切り上げない。負の再投資を入力した場合も、その資本が実際に解放・分配できると認定する意味ではない。異なる年を合計・平均したり、無指定の成長率を掛けたりしない。

statusはintermediate_only、adoptionはunresolved、出典・利益帰属・年次比較・資本政策・予測・資金調達の検証はunverified。同じmetadataや説明があることを意味や経済性の証明にしない。

必要な再投資は外側で根拠付きに用意する。規制比率、RWA、必要/目標資本、buffer、期末残高差からの再投資をこの計算器は作らない。[5831の実例](../research/ir-case-studies-2026-10-15/5831/regulatory-capital-followup/README.md)で確認した8%計算や足元の資本残高を、将来の年間再投資へそのまま転用しない。会社固有の年度・株主範囲・資本目標・資産成長との整合が必要になる。

FCFEの終価、割引、総株主価値や1株価値、増資・希薄化、金融thesis、IR回答適用や売買は対象にしない。DDMのDPS終価へ記号だけを置き換えない。これはvaluation methodへ追加したものではなく、既存stable-reinvestment等と同様の中間計算である。
