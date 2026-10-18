# v13親索引の独立有限点検

不整合は検出されませんでした。 点検は索引の保持・参照解決・指定SHA・構造化値の一致に限定しました。

|確認項目|結果|
|---|---|
|v12の旧entry / fact|15 / 67、完全なJSON object一致|
|v13のentry / fact|17 / 75|
|新規entry / fact|2 / 8、derived source.content JSONの対応factと一致|
|会社IDの重複除去|14|
|会社IDと原典IDの重複除去|16、per-fact override優先|
|解決したnormalized artifact|19 paths、索引の17行と区別|
|per-fact override|5 records、全件解決|
|bundle内original content SHA|38宣言一致（metadata/contentの各19）|
|bundle内original snapshot SHA|19宣言一致|
|索引・parentの宣言SHA|旧v12、新v13、artifact、明示SHA付きsidecar一致|

17はcompanies配列の派生artifact entry数です。5480の売上と135AのCF系4factsは別artifactへoverrideされるため、解決先のartifactは19です。16は会社IDと原典IDの組合せ数で、独立予測数ではありません。新しい短信entryの原典は旧3774 EPS/DPS entryと共通であり、2entry追加に対して原典pairは1だけ増えています。

新8recordsは同一会社の売上収益・営業利益・税引前利益・親会社所有者利益という4会社予想のFAQ/短信2表示です。各組のconcept・kind・value・unitは一致し、独立予測増0という説明と整合します。FAQの日付nullを維持しており、同じ版・最新性・詳細範囲の一致や原典の真正性は認定しません。

全原典引用・offset・表構造の再監査、単位換算や金融計算の再計算、GET/API/プロジェクトCLI/実DB/full suiteは実施していません。SHA点検は索引宣言とbundle内derived sourceのcontent/snapshotまでで、raw transport等の多段来歴SHA全体は対象外です。既存ファイルを変更せず、本JSONとMarkdownのみ新規保存しました。

点検開始UTC: 2026-10-15T13:00:57+00:00  
点検完了UTC: 2026-10-15T13:04:06.488021+00:00

詳細・75件の解決結果・SHA・再現用checkerは同名JSONに保存しています。
