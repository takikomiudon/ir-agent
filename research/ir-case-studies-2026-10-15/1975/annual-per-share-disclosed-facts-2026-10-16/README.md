# 1975 通期実績EPS・期末BPSの2表示値

受入済み年次原本source `case-public:f733d2deff739e7de2b2f93256929a68e1eb1d6b88ec50ef3c828e0f27f9036f` を全object・16頁全文そのまま使い、既存 `normalize-facts` のfile-only経路で2factsだけ正規化した。新derivedは `disclosed-facts:9d7b21bfd8ffec2d0369103cfcdf945e6407dff6e690816edc895d115470d313`。

| fact | 会社直接表示 → canonical value | 期間区分 |
|---|---|---|
| 連結通期実績・普通株EPS | 358.13円 → 358.13 JPY-per-share | duration / annual、2025-04-01〜2026-03-31 |
| 連結期末・普通株BPS | 1,965.51円 → 1965.51 JPY-per-share | instant、2026-03-31 |

両basis_quoteは物理15の同一連続表で、当期列・円・年度両端・直接表示値を保持。物理1の連結/日本基準と年度、物理15のordinary-share算定基礎、物理2の平均株/期末株の区別、物理7の株主資本/OCIの区別は `quotes.json` の逐語引用/位置参照として残した。BPSbasis50,858百万円を株主資本44,745へ置換せず、年次平均株・百万円/千株の丸めからEPS/BPSを再計算していない。予想357.48/357.49、個別、Q1はfactに含めない。

`normalization-input.json` が入力、`normalized-bundle.json` は元source＋derivedの2件、companies/theses空。`validation.json` に既存reproducer、同now全文再生成一致、Unicode/UTF8位置、元受入source/nativeSHA・normalizerの前後pinと、model-inputsで参照可能な2つのvalue_pathを保存した。conceptは既存normalizer上は非空text、period descriptorの意味は抽出者の申告で自動認証ではない。

原sourceの公表2026-05-14はday precision/published_at:null、元取得完了を維持。派生取得は `2026-10-16T09:48:51.082723+00:00` で、実DBfirstsaveではない。新derivedの実DBfirstsaveはnull、旧DB保存日時は照合/変更していない。金融verified/adopted=false、meaning_review_required=trueのまま。DB/Store/GET・旧artifact/共有code変更・model-inputs実行・Graham計算・金融採用/IR/売買は0。rootの独立レビュー・次操作を待つ。
