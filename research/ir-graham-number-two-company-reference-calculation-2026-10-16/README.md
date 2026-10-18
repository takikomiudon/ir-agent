# 二社のsource-bound Graham式参考計算

保存済み `actual-input-audits` のrequest/result/native bindingと、受入済み正規化bundleに対応する4つの表示入力だけを使った。独立著者による新しい会社予測や投資方針ではなく、maxgfr/crible maintainerの固定式 `sqrt(22.5 × EPS × BPS)` の日付付き歴史的referenceである。Graham原著の防御条件全体・株価到達期限・買付適格性は認定しない。

| 会社 | 会社表示・連結年間実績EPS | 同年度末BPS | 参考計算の2桁表示（円/株） |
|---|---:|---:|---:|
| 1975 朝日工業社 | 358.13 | 1,965.51 | 3,979.69 |
| 3817 SRAホールディングス | 443.34 | 2,659.88 | 5,150.99 |

EPSはいずれも2025-04-01〜2026-03-31、BPSは2026-03-31。普通株主・平均対期末株・OCI等の意味は元の引用/研究の範囲で保持し、今回の数値一致を意味認証や金融採用へ上げない。会社直接表示のlane Aだけを使い、丸め済み総額からのlane B、会社予想やQ1年率化へ置換しない。二社の価格差、上昇余地、割安順位の比較ではない。

`reference-calculation.json` は実productionの `_prepare`（Graham2入力・正/有限/サイズ・unweighted検証）→ `_fair_value` をprecision80の独立Decimal contextで呼んだ実出力と、独立Fraction/Decimal60の結果を残す。二社ともproduction80を60桁へ丸めた値が独立60桁と一致し、厳密Fractionの上下half-ULPの二乗で60桁/80桁の丸めを確認した。1975の既存lane A `3979.68995862114866833731552861620930236481372293476293651401` と平方根内部の有理数も一致する。表示2桁だけROUND_HALF_UP。

公開 `calculate_valuation` / `value --price` は正の価格が必須で、price由来upside/downside等を同時に返す。**今回は公開wrapperを実行せず、同じproduction内部の検証・計算関数を価格なしで呼んだ**。dummypriceも作らず、ratio/MOS/EV/actionは生成していない。価格なしscalar用の安定した公開入口がない点は現APIの制約として残す。私用関数を呼ぶfile-only再現は固定code SHAに拘束され、公開APIを追加したとの主張はしない。

再現はリポジトリルートで次の1コマンド。入力・source・旧結果・共有codeの13pinsを前後照合し、stdoutだけを返す。

```bash
.venv/bin/python -B research/ir-graham-number-two-company-reference-calculation-2026-10-16/reproduce.py
```

`input-bindings.json` に保存監査への参照、`method-reference.json` にmaintainer原文5引用/正確位置とAPI制約、`execution.json` に今回の実行時刻を保持した。保存されたinput-auditの `source_values_matched` は当時の供給snapshotに対する数値対応で、現DB分類/意味/適用性の再認証ではない。今回はDB/Store/GET/normalize/共有code・旧artifact変更0、新thesis/確率/閾値/targetprice/売買/金融採用0。rootの独立受入前である。
