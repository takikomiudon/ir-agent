# 明示終価FCFFと、非営業資産・少数持分を分ける株主価値調整

`dcf_explicit_terminal_equity_bridge`を[既存評価器](../src/ir_agent/valuation.py)へ追加した。営業価値から株主価値へ移る際、現金、非営業資産、負債、少数持分を別の入力として扱う。これは著者の表示式を純粋に計算する機能であり、現企業の予測や調整額の適合・時価・重複排除を認証する機能ではない。

## 原典とプロジェクトの契約

Damodaran, *Ups and Downs: Valuing Cyclical and Commodity Companies*, September 2009、ToyotaのIllustration 3（PDF17–18頁）とIllustration 5（23–25頁）が出典である。[35逐語引用・頁/位置と必要9群](../research/ir-toyota-author-valuation-readiness-2026-10-15/readiness.json)、[再現準備レビュー](../research/ir-toyota-author-valuation-readiness-2026-10-15/readiness.md)、[保存原典](../research/valuation-model-routing-2026-10-15/sources.json)を参照する。原PDF SHA-256は`16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40`。

- p17–18/TY11–15は営業価値へ現金・非営業資産を加え、負債・少数持分を引き、株数で割る式と各表示値を示す。
- p24/TY17–18は3期の予測FCFFと終価用4年目FCFFを分ける。p25/TY31は“We keep the cost of capital unchanged at 5.09% over the period”、TY32はIllustration 3と同じ株主価値調整を行うと明記する。
- 非営業資産は有価証券・他社持分を含み、簿価を市場価値とする著者仮定。少数持分も簿価で、影響が小さいという著者の判断である。現在の時価を独立に検証した値ではない。

著者の式と表示数値を使うことが原典からの採用部分である。別method名、厳格9キー、非負の調整額、JPY/年末/単一r、入出力形式は本プロジェクトの限定契約。数値の既定値は置かない。即時正常化のn=0例や年別WACCはこの機能の対象外。

## 入力：9項目すべてを明示する

scenarioの`method`を`dcf_explicit_terminal_equity_bridge`とし、`inputs`は次の9キーだけを持つ。ゼロを含め省略不可、未知キーも拒否する。

| key | 意味・受理範囲 |
|---|---|
| `fcf_jpy` | 1〜n年末の会社全体アンレバードFCFF、JPY。n>=1の非空配列で、負/0も保持。 |
| `terminal_fcff_jpy` | n+1期の明示FCFF、JPY。税・再投資後、負債支払前の意味を入力側で揃える。負/0も保持。 |
| `discount_rate` | 予測期・安定期で同じ年率r、小数比率、r>0。 |
| `terminal_growth_rate` | 安定g、小数比率、−1<g<r。 |
| `cash_jpy` | 評価時点に加算する現金。JPY、非負。 |
| `non_operating_assets_jpy` | 現金・営業CFと重複しない非営業資産の加算額。JPY、非負。 |
| `debt_jpy` | 評価時点に控除する負債。JPY、非負。 |
| `minority_interests_jpy` | 連結営業価値から控除する少数持分。JPY、非負。 |
| `shares_outstanding` | 同じ株主帰属・持分単位に対応する株数。正。 |

数値の受理形式は既存評価器どおり、有限のnumeric string/int/float/Decimal。bool、null、NaN/Infinity、コンテナは数値として拒否する。金額はすべてJPY実単位、株数も実株数。百万円/十億円の無換算入力、異通貨、ADR比率・時点・連結/会計範囲の不一致を計算器が自動検出・修正するとはしない。これらの意味と適合は出典付きの別レビューで確認する。

新2項目も明示0が必要で、missingを0へ変えない。負の簿価・他の優先請求権・重複や所有範囲がある場合は別の適合点検が必要。絶対値への変換やcash/debtへの埋め込みでこの契約へ通さない。非負制限は機能範囲で、企業を除外する投資条件ではない。

## 算術と時点

```text
TV_n = terminal_fcff_jpy / (r − g)
PVoperating = Σ[t=1..n] fcf_jpy[t]/(1+r)^t + TV_n/(1+r)^n
Equity = PVoperating + cash_jpy + non_operating_assets_jpy
                     − debt_jpy − minority_interests_jpy
Value/share = Equity / shares_outstanding
```

終価はn期末に置きn期分だけ割り引く。明示n+1 FCFFへg・税・再投資を再適用しない。負の営業価値でも明示調整後のequityが非負なら計算できる。equity<0は丸め前に拒否し、0は有効。負値を0へclampしない。

既存のprivate Decimal contextと入力依存の精度を使い、計算途中の金額は丸めない。callerの精度・丸め・traps・flagsを変えず、入力オブジェクトも変更しない。

## 出力と互換性

新methodは既存explicitの`enterprise_value_jpy`（PV営業価値）、`equity_value_jpy`、`terminal_fcff_jpy`、`forecast_periods`、`terminal_value_jpy`、`present_value_of_terminal_value_jpy`、`present_value_of_forecast_fcf_jpy`を保持する。追加は次の5キーだけで、scenario直下のflatな値である。

| 追加key | 型・表示 |
|---|---|
| `cash_jpy` | 小数2桁のmoney文字列。 |
| `non_operating_assets_jpy` | 小数2桁のmoney文字列。 |
| `debt_jpy` | 小数2桁のmoney文字列。 |
| `minority_interests_jpy` | 小数2桁のmoney文字列。 |
| `equity_bridge_formula` | 固定文字列`enterprise_value_jpy + cash_jpy + non_operating_assets_jpy - debt_jpy - minority_interests_jpy`。 |

金額・株価・百分率の表示は既存どおりROUND_HALF_UPで小数2桁。`terminal_fcff_jpy`は既存explicit同様、入力精度を保つ正規化decimal文字列、`forecast_periods`はint。表示した各内訳を再合計した値は、未丸め値による内部計算と端数だけ異なる場合がある。`include_unrounded=True`は既存どおり未丸めの1株価値等を返す。

`dcf`は引き続き未知キーを無視し、新2項目を消費しない。`dcf_explicit_terminal`は厳格7入力のままで、新2項目が0でも付加すれば拒否する。旧DDM/EPSを含む全旧出力へ新フィールドを加えず、旧ID・保存値や過去質問の意味を変更しない。

新2項目は`_prepare`のcanonical inputsに残るため、既存の出典監査・IR変更範囲の経路へ渡せる。これは新しい質問を準備するための入力で、旧仮説・質問を自動移行する根拠ではない。この変更自体はpolicy、decision、IR送信、DB採用を行わない。計算結果へ`verified`/`model_adopted`等の自動認定も加えない。

## 保存した2例と検証

[合成例](../examples/valuation-equity-bridge.synthetic.json)は既存explicitの試験設定を再利用し、FCFF[10,000,000]、terminal80,000,000、r.1/g.02、cash/debt0、株数10,000,000に、非営業資産20,000,000と少数持分10,000,000を分離した。net調整10,000,000で1株＋1円、旧例91.818181…円から**92.818181…円（92.82）**になる。比較価格100円も仮想で、金融採用値ではない。

[Toyota著者表示例](../examples/valuation-equity-bridge.toyota-author-display.json)は3期CF[−412,−88,314]、明示4年目713、cash2,288/nonop6,845/debt11,862/NCI583を各十億円×1e9、株数3.448十億株×1e9としている。unweightedで確率・期待値は補わない。表示入力の計算は**3,944.09円**、著者表示は**3,943円**と併記する。原典の16,907十億円は`Value of Operating Assets`で、非営業資産や現金の加算前の営業資産価値である。出力名`enterprise_value_jpy`も同じくPV営業価値を指し、株主価値とは区別する。713/(.0509−.015)自体が19,860.724233…十億円で、著者表示TV19,856と異なる。最終株価だけの丸め差と断定せず、未表示精度/手順・Table 3の税/ROC/NOLの不整合は未確認のまま、713を逆算補正しない。

著者比較価格3,060円は2009年2月という表示で、正確な日時は不明。現在相場として使わない。exampleの`research_context`は出典・仮想/過去・簿価/時価仮定・採用未検証を説明する補助metadataであり、評価器が解決・認証する入力ではない。

[新単体テスト](../tests/test_equity_bridge_valuation.py)は独立Fraction式、9入力境界、旧キー無視/厳格7と出力互換、n/n+1、負/0のCFと株主価値、微小・大きな相殺額、Decimal隔離、入力不変、両例、canonical inputsを有限に検証する。[統合チェックポイント](../research/ir-equity-bridge-integration-2026-10-15/README.md)には新統合8件を含む全1,281件成功、親の独立再計算、実DB不変の確認を残した。
