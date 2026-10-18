# 価格なしの参考計算

`calculate_reference_value(valuation, *, include_unrounded=False)` と `reference-value FILE` は、市場価格が未取得でも既存の6methodによる参考計算を行う。`value` / `calculate_valuation` と同じ入力検証・計算kernel・Decimal精度・小数2桁のROUND_HALF_UPを使う。価格、ダミー価格、価格由来の比率、MOS、投資actionを入力・生成しない。DBやStoreには接続しない。

入力は既存のvaluationオブジェクト。Grahamの[未記入template](../examples/valuation-graham-number.template.json)を別ファイルへコピーし、対象年度の会社表示EPSと同年度末BPSを出典付きで埋める。templateのnullはそのままでは拒否される。

```bash
.venv/bin/ir-agent reference-value PATH/valuation.json
.venv/bin/ir-agent reference-value PATH/valuation.json --include-unrounded
```

```python
from ir_agent.valuation import calculate_reference_value

result = calculate_reference_value(valuation, include_unrounded=True)
```

各scenarioは `reference_value_jpy` を返す。`aggregation: unweighted` は確率を補わず、`expected_reference_value_jpy: null` と `reference_range_jpy` を返す。weighted（既定値）は入力に明示された確率だけを使い、合計が厳密に1でなければ拒否する。期待参考値は表示前の各計算値から求める。`include_unrounded` は有限Decimal contextの値を追加し、平方根の無理数を厳密値へ変えるものではない。

Grahamを含む場合は、価格を除く全入力・明示確率・混在methodの期間を精度算定に含め、既存の総精度上限をContext確保前に適用する。Grahamを含まない既存methodへ新しい上限を追加しない。価格付きAPIの入力・出力・価格による精度算定は維持する。

出力は `status: reference_values_only`、`meaning_review_required: true`、`financial_inputs_verified: false`。期間・株主範囲・会社実績/予想・単位・方法の適合や売買条件を認定せず、参考値を公正価値・購入価格・利確価格へ昇格しない。[入力由来の監査](workflow.md#モデルに使う数値の出所を点検する)・意味レビュー・金融採用は別の操作である。
