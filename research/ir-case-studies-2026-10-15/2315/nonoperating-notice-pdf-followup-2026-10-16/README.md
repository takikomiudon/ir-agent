# 2315 営業外損益notice：新明示PDF実体の1 GET確認

前phaseの `02.json → $.response_headers.location` が新たに明示した同hostの実体 `https://www.caica.jp/wp-content/uploads/2026/09/20260914_3_kaiji.pdf` だけを別phase最大1 GETで取得。200・完全163,959B、raw SHA `77aa7a943faa988247b82698ed9eb286ddb55fd76f5b4ef72ce5e350e1a63936`。原取得完了 `2026-10-16T05:05:06.665111+00:00`。**PDFは1頁で、全文text・画像・意味を全1頁確認した。** 参照先の他資料や元短信全18頁まで読了したわけではない。

前phaseは2 GET・index1source・金融本文0のまま不変。今回の実体取得は旧URL再試行や自動転送追跡ではなく、別の明示URLに対する独立1 GET。前index sourceは複製していない。元302 capture全体SHA/Location pointer/保存header subset native SHA/空entity raw SHAを `guard.json` に分けた。空body SHAだけでheaderを結合せず、wire header captureとも称さない。

保存robotsは初期の完全404 missing branch、観測完了 `2026-10-16T04:49:11.614248+00:00`。actualhost/holds-v8を照合、現在robots再GETなし・固定UA/通常proxyTLS・redirect/retry/JS/検索/別host0。旧notice/Fisco/窓口へのGET0。全HTTP開始・headers・完了・原raw保存・responseは `capture.json`/01.json。

原資料は会社による2026年9月14日付notice（公表日day精度、exact clock不明）。取得・local全文抽出観測・実DB初保存と分けた。冒頭対象は**第3四半期連結会計期間2026年5月1日–7月31日**。短信のQ3累計2025年11月–2026年7月や、通期予想2025年11月–2026年10月と同一期間にしない。

- 善光総研の補助金32百万円等を含む営業外収益56百万円は、主に東京都協定事業の最終実績に応じ協定額が確定したこと等によるという会社説明。確定を入金日/額・反復的な正常利益と扱わない。
- 7月29日Fisco株式追加取得後の持分法適用開始で、過去の段階取得による投資差額の一部を、開始時点の時価評価と簿価の関係から減損したと説明する。営業外費用179百万円は投資損失「等」を含む表示で、179全額を特定会社の減損額と断定しない。将来の時価変動等による追加減損可能性も明記する。持株数/比率/取得単価や未取得7月29日noticeの内容は補完しない。
- 本件は同日Q3短信に反映済みと記載する。Q3累計の経常/親会社利益は前回予想を下回る推移だが、営業外項目と直近動向を勘案し、2025年12月19日公表の通期会社予想は据え置くという説明。今後の影響は精査中、修正要否を含め必要時に開示するとする。据置を影響0・達成/反転・将来無修正の保証にはしない。

初期受入済み短信p5の補助金/持分法損失説明、追加受入済みp10の据置理由と同じ方向であり、今回新たに原noticeの短い全体と狭い会計期間を確認した。新金額・予想・正常利益を作ったり、既読p10/13/18を未読状態へ戻したりしない。noticeの百万円表示を、既存p13の千円行へ上書きしていない。参照pinと比較は `review.json`。

新原source1本・全1頁逐語引用1件。原object/content/raw SHAとUnicode/UTF8位置は `source-quotes.json`。metadata.financial_contentはproducer内容判断でnative分類/金融採用とは別。既存sharedbuilderを再利用しwhole original capture/rawを保存。producerはraw/全文/契約/stableID/引用/画像と旧2phaseの57pins不変を照合、汎用byte verifier未実行をmatchedとはしない。

Anthropic公開先行DDとDamodaranの主体/利益段階/期間/CF分離による読解。独自forecast/正常利益/確率/価格/IR草案、DB/code/旧source履歴編集/case/normalizer/金融採用/送信は0。1 GETでfreeze、追加GET0、root独立画像/意味受入待ち。
