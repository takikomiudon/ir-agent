# 単一の明示確率予測を採点する

`ir_agent.probability_scoring.score_categorical_forecast(request)` は、呼出元が指定したカテゴリ予測1件に対してBrier lossと自然対数のlog lossを計算する純粋関数である。ネットワーク、DB、観測台帳、モデル学習には接続しない。

計算方法はGneiting & Raftery (2007), *Strictly Proper Scoring Rules, Prediction, and Estimation*, JASA 102(477),359–378、PDF5ページ・誌面363のExamples 1/3を採用した。[原典](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)と[保存本文・逐語引用・適用限界](../research/probabilistic-evaluation-2026-10-15/README.md)を参照する。原典のrewardは大きいほどよい。本実装は符号反転したlossを使う。

## 入力

[架空の動作例](../examples/probability-scoring.json)にある6フィールドが全て必須で、未知のフィールドは拒否する。例のカテゴリ・確率・参照は動作確認用の架空値であり、実観測、推奨確率、較正済みモデルではない。

| キー | 契約 |
| --- | --- |
| `categories` | 事前に定義したカテゴリ名の非空配列。重複不可。要素は前後空白のない非空文字列。順序によってlossは変わらない |
| `probabilities` | 全カテゴリとキーが完全に一致するobject。各値は有限の0〜1で、十進値の合計が**厳密に1** |
| `observed_category` | `categories` のいずれか一つを明示。欠損や未知カテゴリは採点しない |
| `prediction_ref` | 予測への明示参照文字列 |
| `observation_ref` | 観測への明示参照文字列 |
| `definition_ref` | カテゴリ定義への明示参照文字列 |

3参照は前後空白のない非空文字列で、呼出元の宣言としてそのまま返す。実在する資料や版を参照しているか、予測が事前保存されたか、観測が適格かは検証しない。

数値は`str`、`int`、有限の`float`、`Decimal`を受け取る。`bool`、`null`、配列、object、空文字、非数、無限大、空白・桁区切り・underscoreを含む文字列は拒否する。数値文字列は符号、小数点、十進指数表記を許容する。floatは`str(float)`が表す十進値として扱うため、厳密な十進値は文字列で渡す。合計の許容誤差、再正規化、欠損の補完はない。

カテゴリ配列の重複を拒否する。Pythonのdictに変換される前のJSONキー重複はこのAPIでは観測できないため、JSONを読む側の契約で扱う必要がある。

## 計算と出力

`p_j`は各カテゴリの確率、`y`は実現カテゴリとする。

- `brier_loss = Σ_j (p_j - 1[j=y])²`。**全カテゴリ**を足す。二値でも両要素を足すため、二値scalar式`(p-y)²`の2倍になる。範囲0〜2はこの定義の数学上の範囲であり、投資やモデル採用の閾値ではない。
- `log_loss = -ln(p_y)`。自然対数を使い単位はnats。観測カテゴリの確率が正なら有限、1なら0、0なら正の無限大となる。epsilonへの置換や上限丸めは行わない。他のカテゴリの確率0は、その観測についての無限大を意味しない。

結果には`schema_version:1`、`status:"calculation_only"`、参照、カテゴリ、正規化した十進確率文字列、実現カテゴリを返す。

```json
{
  "brier_loss": {
    "status": "finite",
    "value": "0.38",
    "convention": "multiclass_sum_squared_error"
  },
  "log_loss": {
    "status": "finite",
    "value": "0.69314718055994530941723212145817656807550013436025525412068000949339362196969472",
    "unit": "nats"
  }
}
```

観測カテゴリの確率0の場合は`log_loss`を次のように返す。`null`はこのstatusと組み合わせて無限大を表すため、観測欠損、未計算、有限の0とは区別できる。JSONの非標準`Infinity`や`NaN`を返さない。

```json
{"status": "positive_infinity", "value": null, "unit": "nats"}
```

Brierは入力の小数位置とカテゴリ件数から十分な独立Decimal精度を確保して正確に計算する。logは独立した80有効桁の`Decimal.ln`で計算する近似値で、丸めは`ROUND_HALF_EVEN`。精度・方式は出力の`arithmetic`にも示す。呼出元のDecimal精度、丸め、トラップ、flagsを使わず、入力を変更しない。

資源保護の技術上限はカテゴリ1,000件、数値トークン2,048文字、十進係数256桁、Decimal指数の絶対値1,000、内部精度4,096桁。上限超過は黙って丸めず`ValueError`にする。これらは統計的に必要な標本数やモデル品質の基準ではない。

## 呼び出し例

```python
import json
from pathlib import Path
from ir_agent.probability_scoring import score_categorical_forecast

request = json.loads(Path("examples/probability-scoring.json").read_text())
result = score_categorical_forecast(request)
print(json.dumps(result, ensure_ascii=False, allow_nan=False))
```

入力不備は`ValueError`。参照が解決できることや結果の保存成功を示す戻り値は設けない。

## この計算からは確認できないこと

出力の`verification`は`references_resolved`、`prior_prediction_verified`、`observation_eligibility_verified`、`calibration_verified`を全て`false`にする。これは未検証を示す。各事実が誤りと判定されたという意味ではない。

事前予測であること、信号分類の妥当性、後日の外部状態ラベル、公開性・観測期限・送達、標本の選択や企業間依存は別途確認する必要がある。未送信や状態不明を0点として投入してはならない。状態別の`p(signal|state)`を扱う場合も、どの状態の行が採点可能かは呼出元が明示して点検する。

propernessは期待スコアの性質であり、1件のlossや少数標本の平均は較正、母集団の精度、EVSI、利益確率の証明にはならない。batch集計、信頼区間、尤度学習、既定の確率、合格閾値、損益や投資判断はこのAPIの対象にしていない。

検証は `.venv/bin/python -m unittest discover -s tests -p test_probability_scoring.py -v`。全カテゴリの手算術・二値尺度・ゼロ/1境界・極小確率・カテゴリ順・厳密合計・不正入力・技術上限・入力不変・呼出元Decimal contextからの独立を確認する。過去の変換エラーや丸めで既に立っているflagsも、成功時・入力拒否時とも保持されることを確認する。
