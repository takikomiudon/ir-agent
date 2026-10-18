# 5988：固定14factからの独立scalar算術再記述

**公開表示額に厳格bindingした2期のEBIT fallback、WC fallback、税前ROC、税率clip/NOPATを再記述できた。モデル金融入力・会社の正常税率・投資方針へは採用していない。** これはupstream pandas runtime再現ではなく、標準ライブラリDecimalによる独立の研究scriptである。

## 研究計算の結果

以下の金額はJPY。ROC/税率は百分率ではなくratio。表の比率は小数10桁、NOPATはJPY小数2桁のROUND_HALF_EVEN表示。全精度（precision80）・分子分母は[reproduction.stdout.json](reproduction.stdout.json)に保持し、非終端除算は近似と明記する。百万円表示からの換算額は原表にない未丸め経済額ではない。

| 年度末 | EBIT fallback | reported営業利益（比較のみ） | WC fallback | 税前ROC分母 | 税前ROC比率 | 表示額税率 | maintainer clip後税率 | clip後NOPAT（研究値） |
|---|---|---|---|---|---|---|---|---|
| 2025-03-31 | 3,416,000,000 | 2,382,000,000 | 52,180,000,000 | 85,752,000,000 | 0.0398358056 | 0.4553203998 | 0.4553203998 | 1,860,625,514.40 |
| 2026-03-31 | 1,017,000,000 | 1,470,000,000 | 24,599,000,000 | 60,435,000,000 | 0.0168279970 | 1.0078636959 | 0.5000000000 | 508,500,000.00 |

年度は2024-04-01〜2025-03-31、2025-04-01〜2026-03-31。BSはそれぞれ同じ年度末のinstantに限定。営業利益とEBIT fallbackは**両期とも別額**で、独自の営業利益版ROCは作らない。当期は表示税額/PBTが1を超える一方、maintainer conventionにより0.5へclipされる。clipを単なる欠損除去、原会計税率、会社の正常税率と呼ばない。p94の公表百分率は算術入力・厳密一致目標にせず、原表の丸め前内部額が不明な差を補正しない。

## 入力と研究用mapping

親のfreezeで指定された[normalized-bundle.json](../ir-case-studies-2026-10-15/5988/annual-capital-disclosed-facts/normalized-bundle.json)（SHA `4c7723e2667252489997eaa2abaf99862c6c87b3d1fd02cef4053a890ec9683e`）、normalization-input（SHA `fb25a22fa8d5c5b29a38593fd5c6ea27698ff55bb233e5396bfb135ad2446ced`）、producer validation（SHA `ad911dbb07af45ae5697a5258884a4cc8526d7e6c7a0630b535cd8816904c299`）を固定した。[input-pins.json](input-pins.json)は元raw/PDF、元source object/content、既読式・MITを別hash domainで保持する。

各factはreported_consolidated_の次の7概念×2期だけ。これは**今回の明示した研究用mapping**で、provider実データや財務・株式モデル適合の認証ではない。

| reported概念の末尾 | canonical仮入力／用途 |
|---|---|
| profit_before_income_taxes | income_before_tax |
| interest_expense | interest_expense |
| income_taxes_total | income_tax_expense |
| current_assets | current_assets |
| current_liabilities | current_liabilities |
| tangible_fixed_assets | net_ppe（有形固定資産合計の範囲適合は別の意味レビューを要する） |
| operating_income | 比較表示だけ。EBITへ置換せずROCの分子にしない |

選択14factコホートに直接のcanonical EBIT/WCを入力していないため、既読コードの**全期欠損時fallback**の算術を選んだ。この限定入力にないことを、会社が非開示・原報告書全体にも指標が存在しないという主張にしない。

scope.accounting_basisは全14factでnullを保持。会社/連結・日付・期間・JPY単位の一致を保存schemaで検査するが、null同士の一致で会計適合確認済みとはしない。p26等の別の記載を元factへ追記せず、独立fact意味レビューの受入も本計算では未消費。sourceやfact原文を変更していない。

出力のbindingsは14factそれぞれのfact ID・reported概念・仮canonical名・value・期間・scope・元source object/content SHA・元原文row/quote offsetを含む。bundleのcontentはJSON文字列なので、`/sources/1/content`→JSON parse→`/facts/N/value`という**二段pointer**を使う。JSON文字列内を直接辿る存在しないpointerを作らない。元抽出inputの`/facts/N/raw_value`と元sourceの位置も残す。

## 式・精度・再実行

[reproduce.py](reproduce.py)はstdlibのみ、固定manifestのSHAを照合してから全入力fileを検証する。既読の式の参照は以下（前段と同じ固定commit `00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7`）。

- canonical.py:189–190 — PBT＋支払利息のEBIT fallback。
- canonical.py:184–185 — CA−CLのWC fallback。
- extras.py:92–93 — EBIT fallback÷(WC fallback＋仮net_ppe)、分母>0。
- extras.py:65–69 — PBT>0で税額/PBT、0〜0.5へclip、EBIT fallback×(1−clip後税率)。今回はROIC分母を作らずNOPATで止める。

Decimalのprecision80・ROUND_HALF_EVENを指定。clip境界は近似した税率を比較せず元額のcross-comparisonで決め、NOPATも分子分母を保持する。主な処理は記述式の独立実装でありupstreamのimport・実行・pip導入はない。元[MIT本文](../ir-transparent-metric-library-discovery-2026-10-15/LICENSE.upstream.txt)とSHAを参照し、ソフトウェアの条件をissuer原典・providerデータの利用許可へ拡張しない。maintainer式はGreenblatt本人の方式・承認とは区別する。

再実行（repo root、ネット・DBアクセスなし）:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python research/ir-capital-metric-scalar-reproduction-2026-10-16/reproduce.py
```

初回stdout/logは[reproduction.stdout.json](reproduction.stdout.json)/[reproduction.log](reproduction.log)、再実行はreplay.stdout.json/replay.log。recorded_atだけを除いた結果は完全一致。script自身のSHAと入力SHAを出力する。recorded_atは本研究の計算時計でDB初回保存時刻ではない。

[finite-binding-checks.json](finite-binding-checks.json)はmemory copyに限った9拒否例（重複/欠損/異単位/異期間/無断basis追記/非有限/表示値不一致/原source改変/引用offset不一致）。本番・元fileを変更せず全拒否。product testsやupstreamテストを実行した意味ではない。[validation.json](validation.json)に実行出力/入力/script SHAと精度、再実行一致、限界を固定した。

## nullのまま残したもの

- ROIC: 2期の適合確認済みtotal_equity・負債・現金等・総資産がこのコホートにない。日本原典の純資産や株主資本を勝手に対応しない。
- EY: この入力にsource-bound価格/観測時刻・価格用株式分母・負債・現金等を供給していない。実DBや他資料の価格を探索・転用していない。
- valuation/rank: モデル/予測/倍率・比較universe・EY・順位kernelを供給・採用していない。Brazil順位方式へ混合0。
- future ROC_new: 歴史税前ROCとclip後の歴史NOPATは、将来安定期の税後新規投資利回りを与えない。自動代入0。

これらは理由付きnullとして出力。会社原典の引用や算術が通ることは、研究mappingの経済的妥当性、実データPIT、将来予測、投資有効性の認定ではない。計算に限る研究利用でありmodel_financial_inputs_adopted/financial_inputs_verifiedはfalse。GET・DB・product src/CLI・共有file・原bundle・他担当file変更、外部依存導入/import、upstream実行、質問/外部送信は0。有限算術の再記述を終了する。
