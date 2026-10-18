# Graham Numberの参考計算

`graham_number` は保存済みmaxgfr/cribleの式 `sqrt(22.5 × EPS × BVPS)` を独立実装した。固定係数22.5の出典は[maintainerの説明](../research/ir-transparent-metric-formula-review-2026-10-15/upstream-INDICATORS.md)の第5節、固定commitは `00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7`。[入力仕様の確認](../research/ir-case-studies-2026-10-15/1975/graham-number-input-spec-review-2026-10-16/README.md)と[実績による算術](../research/ir-case-studies-2026-10-15/1975/graham-number-annual-arithmetic-2026-10-16/README.md)を保持する。Graham原著の全適格条件や運用戦略を再現したものではない。

入力は次の2項目だけで、両方とも正の有限数・単位JPY／株とする。係数、倍率、成長率、株数を追加すると拒否する。

| キー | 今回の研究で確認する内容 |
|---|---|
| `eps_jpy` | 対象年度の会社表示の連結実績EPS。会社予想、個別、Q1の年率化と混ぜない |
| `book_value_per_share_jpy` | 同年度末の会社表示BPS。普通株主の持分・期末株式基準を確認する |

計算器は期間・株主範囲・実績か予測かを自動認証しない。EPSの年間平均株数とBPSの期末株数、自己株式、OCI・非支配持分の扱いを原典で別に確認する。日本基準「株主資本」を英語StockholdersEquityの直訳で代用しない。会社表示の1株値と、百万円未満切捨ての総額から再計算した値は精度が異なる。

[未記入template](../examples/valuation-graham-number.template.json)の2数値を出典付きで埋め、既存の `value FILE --price PRICE_JPY` を使う。確率を設定していない研究は `aggregation: unweighted` のまま扱う。価格の根拠がない場合は価格を補って実企業の比較を実行せず、式の参考計算と入力準備を進める。`model-inputs` は原典・派生sourceと値のpathを照合できるが、意味確認と金融採用は別である。

出力は既存の `fair_value_jpy` 等の形式を共用する。この名前だけで公正価値・購入価格・利確価格を認定せず、出典付きの式による計算値として読む。1975のFY2026年3月期の直接表示EPS358.13/BPS1965.51では3,979.69円。丸め済み総額からの別計算は3,979.53円で、両方を保持する。NCAVの2/3条件と合成しない。

計算は既存の独立Decimal contextを使い、表示時のみ小数2桁へROUND_HALF_UPする。`include_unrounded` は有限精度の計算値を保持する。新methodの各入力は係数の桁数・指数・調整指数を各10,000以内、Grahamを含む計算全体は必要精度100,000桁以内とする。これは極端な数値表現による資源消費を抑える技術上限で、投資対象の閾値ではない。旧methodだけの計算には新上限を適用しない。
