# 5988年次14factの独立レビュー

**14fact・9契約確認を受入れ、指摘0件。** 年次discovery/normalizationの作成担当から独立して点検した。以前の税注記p94レビューは担当したが、今回のp63/64/65は原PDFから独立再抽出・再描画し、保存画像を目視して確認した。原本全頁や金融モデルの認定へは広げていない。

| 原会計名（百万円） | 前期 | 当期 | 物理頁/印字頁 |
| --- | --- | --- | --- |
| 流動資産合計 | 64,398 | 58,140 | 63/60 |
| 有形固定資産合計 | 33,572 | 35,836 | 63/60 |
| 流動負債合計 | 12,218 | 33,541 | 64/61 |
| 営業利益 | 2,382 | 1,470 | 65/62 |
| 税金等調整前当期純利益 | 3,402 | 763 | 65/62 |
| 支払利息 | 14 | 254 | 65/62 |
| 法人税等合計 | 1,549 | 769 | 65/62 |

B/S6factは2025-03-31/2026-03-31の連結時点値、P/L8factは2024-04-01〜2025-03-31/2025-04-01〜2026-03-31の連結年間flowに対応した。会計名・前当期の左右列・百万円を保持し、換算は×1,000,000の表示単位整形だけ。営業利益をEBITへ改名せず、支払利息を受取利息と混同せず、法人税等合計を現金税や正常税率へ変換していない。会計基準nullと未表示精度の留保も維持する。

保存原PDFからpdftotextで再抽出した3頁は保存頁と完全一致した。末尾formfeedを除いたときだけ元全文の各pageと一致する区別も確認した。120dpiでメモリ上へ再描画した3PNGも保存PNGとbyte一致し、全画像の表見出し・単位・対象行を独立目視した。3連続引用と14行の文字/UTF8 byte半開offset、引用参照、標準派生source内value_pathを照合した。

標準 `reproduce_disclosed_fact_source` をオフラインで実行し、`reproduced`、原文SHA matched、原snapshot matched_supplied_snapshot。返却objectはwriterのreproduction.jsonと同値だった。元sourceは旧tax入力の `/source` およびbundleの `/sources/0` と全object同値で、native/canonical JSONの別SHA・content SHA・旧取得日時を保持する。派生生成/取得時刻と抽出review時刻を、実DB初保存や会社公表時刻に置き換えていない。

旧索引107factとのID/同社同concept同periodの重複は0。今回7conceptは旧同社conceptとも重ならない。producerの全20入力pin・9成果物pinを照合し、旧税fact・discovery・索引・原source・writer成果は不変だった。チェックリスト14件、再現返却値、全32参照SHAと未実施範囲を[independent-review.json](independent-review.json)に保存した。

これは公表表示額の限定的な意味/構造化レビューであり、税率・NOPAT・ROC/EY/EV・valuation・現在適合や投資判断の認定ではない。新GET・DBアクセス・元成果/共有文書/コード編集・金融採用は0。
