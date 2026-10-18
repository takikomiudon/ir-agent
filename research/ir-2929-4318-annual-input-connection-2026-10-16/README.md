# 2929・4318の年次原典と入力を接続

2929の原年次短信・訂正通知・派生2値と、4318の年次短信・派生2値の計5sourceを実保存した。分類2jobと定性比較2jobを完了し、両caseはv2/config1（既読3/2）、内部管理Jan16維持・再queue0となった。[最終DB検証](actual-verification.json)は221資料・分類220・全130job完了、native30case/59版/170既読。旧27tableのschemaと全旧行を保持した。

| 会社 | 対象年度 | 年間連結実績EPS | 同年度末BPS |
|---|---|---:|---:|
| 2929 ファーマフーズ | 2025-08-01〜2026-07-31 | 68.61円 | 453.35円 |
| 4318 クイック | 2025-04-01〜2026-03-31 | 74.11円 | 345.24円 |

2929の訂正表は原文PDFでは画像であり、テキストにない数値をsource quoteや新factへ混ぜない。既知訂正を参照し、原年次本文を機械的に訂正後へ変更していない。4318は分割調整済み表示を再調整せず、ESOPの平均/期末、千株/株、千円/百万円と自己資本/純資産を区別した。[結果受入](qualitative-reviews/parent-result-acceptance.json)は両caseを未解決とし、金融採用・新IR質問は0である。

[実source入力監査2929](actual-input-audits/2929/result.json)・[4318](actual-input-audits/4318/result.json)は新しい保存時点以後の原典と数値pathを照合した。意味の自動認証や金融採用ではない。新公開`reference-value`の価格なし参考計算はそれぞれ836.57円・758.74円で、unweightedの期待参考値はnull。買値や利確価格へ採用していない。監査内部の旧数値検証用価格1は市場観測と区別し、公開参考計算には価格を渡していない。

[索引v39](../ir-case-studies-2026-10-15/disclosed-fact-index-v39.json)は31社234fact・45親・47派生、実45派生/227fact。旧230factとv38のactual全体、対象外8331/9702の2派生7factを保持した。コード受入は別の[1,585テスト](../ir-reference-value-integration-2026-10-16/parent-acceptance.json)で、この実データphaseで全suiteを再実行していない。
