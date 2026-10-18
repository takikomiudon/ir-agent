# 2315 指定9/14営業外損益noticeの有限リンク確認

指定された原題名について、保存root `02.json` links[80] の「ニュースリリース一覧 その他のIR情報・開示資料はこちらからご確認いただけます。」が公式開示一覧へのliteralであることを確認した。別phaseは**最大2 GET、実績2、本文0で停止**した。

1. `https://www.caica.jp/tag/news,disclosure,pr,kessan,other/` → 200・完全86,586B。raw SHA `5acc3ecb995ee8a4d1a6e33c346b95ab1a4fecdf1d6ac6a7f9264a2d8af1dc93`。一覧に「2026.09.14 適時開示 営業外収益（補助金収入等）及び営業外費用（持分法による投資損失等）の計上に関するお知らせ」を確認し、links[87]の正確hrefを得た。
2. `https://www.caica.jp/2026/09/20260914-3-kaiji-pdf/` → **302・完全0B**。rawは空entityのSHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。`02.json → $.response_headers.location` は `https://www.caica.jp/wp-content/uploads/2026/09/20260914_3_kaiji.pdf` を明示したが、このphaseでは追跡/取得していない。

2 GET上限・no-redirect条件に従いfreezeする。302はtransport errorではないがnotice本文の取得成功でもない。この履歴の取得数・本文0を後続の取得で書き換えない。新しいLocationを推測URLや旧notice再試行とは扱わず、未試行の明示先として保存しただけで追加GET予定0。

同hostのrobotsは初期取得完了 `2026-10-16T04:49:11.614248+00:00` の完全404 missing branchを再利用。404 HTMLを許可規則としてparseしていない。holds-v8全12hostと各actualhostを照合、固定UA・通常proxy/TLS、retry/自動redirect/JS/検索/URL推測/ページ送り/別カテゴリは0。Fisco・旧10月1日302notice・窓口へのGET0。

新sourceは一覧原本1本のみ、全文visible textを保持した。意味確認は指定noticeの題名/日付・href、および同日同Q3の補足資料/動画ラベルの位置だけ。金融本文/金額/影響の確認ではなくmetadata.financial_content=false。native分類や入力採用とも別。notice公表日は一覧のday表示、exact clock不明。一覧自体の公表日時も不明。原HTTP開始/headers/完了/原raw保存は `capture.json` と01–02.jsonに保持し、実DB初保存とは区別する。

`link-provenance.json` に対象[87]、未取得Location、同一覧[89]補足資料・[81]補足動画のexact hrefを保存した。後2件も未試行で、題名を内容確認に昇格させない。公表Q&Aや全資料不存在は認定していない。補助金/持分法損失/業績影響・将来guide・正常利益の意味レビューは本文未取得のため未完了。

source-only1本・引用2件。原object/content/raw SHAとUnicode/UTF8 offsetは `source-quotes.json`。既存sharedbuilderを再利用し原capture/完全rawを保持、producerで2entity(うち空302)/一覧text/契約/stableID/2引用と初期36pins不変を照合。汎用byte verifier未実行をmatchedとはしない。notice画像/意味ページ0。

DB/code/共有旧file/case/normalizer/金融採用/IR草案/送信0。root受入待ち。追加GET0で停止。
