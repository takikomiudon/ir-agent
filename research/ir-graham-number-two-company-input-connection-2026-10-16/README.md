# 1975・3817の年次入力を実台帳へ接続

1975の既存通期原典を保持し、3817の通期原典と二社のEPS/BPS派生資料の計3sourceを保存した。分類2jobと定性比較2jobを完了し、1975はnative v4/config1・既読8、3817はv2/config1・既読2となった。内部管理日は2027-01-16 Asia/Tokyoを維持する。

[最終実DB照合](actual-verification.json)は216資料（公開215・市場1）・分類215、全126job完了・lease0。native28case/55版/165既読、公開資料37社・財務内容32社。バックアップとの比較で旧27tableのschemaと全旧行を保持し、新規行だけの増分を確認した。新しい金融thesis・policy・正式IR・送信・注文はない。

| 会社 | 年間実績EPS（円／株） | 同年度末BPS（円／株） | 今回の保存先 |
|---|---:|---:|---|
| 1975 朝日工業社 | 358.13 | 1,965.51 | [派生資料](../ir-case-studies-2026-10-15/1975/annual-per-share-disclosed-facts-2026-10-16/normalized-bundle.json) |
| 3817 SRAホールディングス | 443.34 | 2,659.88 | [派生資料](../ir-case-studies-2026-10-15/3817/annual-per-share-disclosed-facts-2026-10-16/normalized-bundle.json) |

対象年度はどちらも2025-04-01〜2026-03-31。EPSの年間平均株数とBPSの期末株数、連結と個別、実績と予想を分ける。1975のOCIと日本基準「株主資本」、3817の純資産と自己資本の違いを、総額の単純代入で消さない。

[実sourceへの入力照合1975](actual-input-audits/1975/result.json)・[3817](actual-input-audits/3817/result.json)は、実初保存以後の時点で4値とnative snapshotを照合した。先行するfile-only auditは当時の記録として残す。`source_values_matched`は意味の自動認証・金融入力の採用ではなく、`financial_inputs_verified`と`expected_value_available`はfalseのままである。

[結果受入](qualitative-reviews/parent-result-acceptance.json)と各completionを保存した。1975の公開既答を削除した質問整理も、既存のsummary/観測の履歴ごと保持する。3817は年次basisを支持する資料と、意味の未解決を分けた。[構造化索引v38](../ir-case-studies-2026-10-15/disclosed-fact-index-v38.json)は旧226factを保持して新4factを追加し、29社230fact・実43派生/223factとなる。対象外8331/9702の2派生7factはfile-only。

Graham Numberの式とコードの受入は[別の変更記録](../ir-graham-number-valuation-integration-2026-10-16/README.md)。このphaseの変更は実データと記録で、コードの全1,573テスト成功を再実行したものではない。市場の数値表示を正式な価格入力へ補わず、買い・売り・利確条件の採用へ進めていない。
