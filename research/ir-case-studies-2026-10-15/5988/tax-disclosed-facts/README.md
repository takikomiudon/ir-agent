# 5988：歴史的な連結税効果注記6値の構造化

保存有報の物理p94/印刷p91、当連結会計年度（2026年3月31日）の**確認済み6値だけ**を既存`normalize_disclosed_facts`で構造化した。元の[税効果基礎レビュー](../tax-basis-review/tax-basis-review.md)とrootの画像確認を利用し、担当も同じ保存画像の当期列を照合した。

| 原文行・表の性質 | 当期raw表示 | canonical |
|---|---|---|
| 法定実効税率：税率差異表 | 30.58％ | ratio `0.3058` |
| 税効果会計適用後法人税等負担率：税率差異表 | 100.77（同表の％単位） | ratio `1.0077` |
| 繰越欠損金：DTA原因別内訳 | 338 百万円 | JPY `338000000` |
| 減損損失否認：DTA原因別内訳 | 211 百万円 | JPY `211000000` |
| 評価性引当額：DTA全体の控除行 | △788 百万円 | JPY `-788000000` |
| 繰延税金資産の純額：負債との相殺後 | 516 百万円 | JPY `516000000` |

全て`reported_fact`。DTA4値は期末会計残高、税率2値は当連結年度の歴史的な税率差異表として区別する。1.0077を1へclampせず、前年度の欠損金行のダッシュも0へ補完しない。p94に会計基準の明示確認はないため`accounting_basis:null`を保持した。年度開始日はこの頁から補完せずnullとし、期末日・当連結年度ラベルを直接保存する。

338は税務欠損金の元本ではなくDTA原因別の会計額、211は中国損失の税効果と同定できない。全体の評価性引当額を欠損金へ配賦せず、相殺前/後やDTA/現金を混ぜない。法定税率・過去の会計負担率を、現金納付・将来/正常税率・NOPAT等へ採用していない。

## 原典と再現

Primaryは[年度末BPS入力](../annual-bps-basis/normalization-input.json)の`/source`を完全copyした。ID `case-public:5d5a98a7770af91318e9bb24fd4bdac483b20cb5fc96a79f58474dbd77f57365`、取得時刻2026-10-15T01:12:38.091035+00:00、既存raw/text/transport metadata・公表日精度・`published_at:null`を不変保持している。[source-reference.json](source-reference.json)は既存tax参照のbyte同値copyである。旧取得時刻をHTTP完了・DB初回保存へ読み替えず、派生sourceの取得時刻だけを今回の処理時刻とする。

[normalization-input.json](normalization-input.json)・[normalized-bundle.json](normalized-bundle.json)に原典1件＋派生1件を保存した。[quotes.json](quotes.json)は各tableの見出し・前当期列・期末日・単位と対象行を含む連続引用で、離れた行を結合していない。百万円/％の表示が同じquoteに必要なため、DTAと税率差異表の2blockを保持する。原文SHA・文字/UTF8 byte offset・物理/印刷頁・画像SHAを付けた。これらの存在照合と、表列や金融意味の担当者による解釈は別である。

実際のメモリ内API返値は[reproduction.json](reproduction.json)と[reproduction.log](reproduction.log)。6値・source schema・原primary同値・原文SHA/offset・依存閉包・`reproduced`を確認した。全`financial_inputs_verified:false`、`meaning_review_required:true`、companies/theses空、モデル採用0を維持する。[validation.json](validation.json)に照合と保護file SHAを保存した。

新GET・実DB操作・source code/nativecase/索引/共有docs変更は0。この新派生sourceは進行中の旧23source batchへ投入していない。rootの別途採否判断を待って凍結する。
