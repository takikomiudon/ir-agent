# 明示表示された株数の単位換算

`normalize-facts`は既存JPY/JPY-per-share/ratioに加え、canonical単位`shares`を受け取る。原文の単位ラベルとの対応は次の5組だけで、曖昧な表記やsuffixを推測しない。

| 原文ラベル | canonical単位 | 倍率 |
|---|---|---|
| shares | shares | 1 |
| 株 | shares | 1 |
| 千株 | shares | 1000 |
| 万株 | shares | 10000 |
| 百万株 | shares | 1000000 |

原文数値token、同じ引用内の単位・期ラベル、概念、定義、scope、位置は従来通り保持する。Decimal換算は丸めず、小数や符号を整数・正数に補正しない。0は明示0で、ダッシュ・空欄・nullは従来通り未確定のnull。株数と金額・1株金額・比率の相互変換は行わない。

発行済株式数（自己株を含む）、自己株数、自己株控除後、期中平均、希薄化後、EPS分母、評価時点の株数は別概念である。同じ数値でも同一概念にはせず、自己株の自動控除やEPS等からの逆算をしない。unit:sharesだけでは`shares_outstanding`への適合・採用を確認したことにならない。

Damodaranの保存原典は株主価値をnumber of sharesで割る式を示す（[既存原典レビューTY12、PDF17頁](../research/ir-toyota-author-valuation-readiness-2026-10-15/readiness.json)）。[既存9入力契約](explicit-equity-bridge-spec.md)は実株数と正値を要求する。今回のunit名と換算表はプロジェクトの構造化契約であり、新しい金融ルールや株式定義の採用ではない。valuation側の正値guardは既存通りで、fact正規化に一律の負値禁止を加えない。

[設計](../research/ir-disclosed-share-unit-design-2026-10-15/design.md)は135Aの期末発行済株数と期中平均の同値例を引用している。今回の実装自体はその実数値を抽出・登録・評価採用せず、合成fixtureで検証する。

API/schema/normalization_versionは1を維持し、旧factの本文・metadata・limitations・IDを変更しない。既存の原典再現を同じ換算表で利用する。shares対応前のbuildでは新しいpairを再現できずneeds_reviewとなるため、意味を推測して受理しない。モデル入力監査の数値一致・再現成功でも、期間・定義・株主帰属・株式調整・時点適合・財務妥当性は未確認、financial_inputs_verified:falseのままである。

既存workflowの3単位表記をこの追加説明で補足する。旧資料のhash参照と過去レコードを保持し、旧記録を新版として書き換えない。新予測・確率・投資条件・IR送信・DB更新は追加していない。
