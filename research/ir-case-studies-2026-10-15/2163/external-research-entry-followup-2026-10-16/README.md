# 2163 外部研究レポート入口：公式スポンサーindexの有限確認

旧0 GET成果をfreeze後、保存済み初期 `02.json → $.html_visible_text.links[89]` の `https://www.artner.co.jp/ir/filings-reports/sponsored-research/` を1 GETだけ取得。200・完全161,900B、raw SHA `80d4bae957fc8212324caca27c513ec16014a855cea636ab6d607100bab4b306`、原取得完了 `2026-10-16T05:23:08.428111+00:00`。条件付き上限は2 GETだが、著者組織候補と実PDFリンクが得られたのでアナリストカバレッジへの2 GET目は使わない。

公式一覧の「株式会社アクションラーニング」節で以下のexact literalを確認した。**PDFは両方とも未取得**。

| 掲載日・題名 | 保存pointer | 実href |
| --- | --- | --- |
| 2026/4/30「ひねけんの企業研究」[5.60MB/22頁というラベル] | `01.json → $.html_visible_text.links[388]` | `/asset-ir/download_file/sponsored-research-report-script_20260430.pdf` |
| 2026/5/8「アクションレポート」[2.15MB/18頁というラベル] | `01.json → $.html_visible_text.links[389]` | `/asset-ir/download_file/sponsored-research-report_20260508.pdf` |

両方は `https://www.artner.co.jp` へ解決し、actual hostはholds-v8非該当。全anchor/href/解決URL/host/掲載日/作者候補の位置は `report-entries.json`。公式HTMLの作者は発行会社アルトナーであり、レポートの組織候補がアクションラーニング。個人著者・対象FY・予測数値の有無・会社予想転載と独自予測の区別・評価方法・スポンサー契約/独立性は**本文未確認**。掲載日をexact PDF公表時計や、当時の実保存・現在の妥当性へ昇格させない。発行会社資料の予想を外部著者予測へ読み替えない。

同hostの保存robots200観測は `2026-10-16T04:32:06.957542+00:00`。rules rawSHA/各actualhost/holds-v8を照合し、通常proxy/TLS・固定UA、retry/auto redirect/JS/検索/URL推測0。現在rules再GETではない。PDF/外host/保留Fisco/SharedResearch本文、説明会対談/別会社/2983旧経路のGETは0。

原raw/HTTP開始・headers・完了/原保存/response/完全性は `capture.json`/01.json。全文visible textを新source.contentへ保持したが、意味確認はスポンサー節の組織/掲載日/題名/リンクまで。予測・評価・金融本文確認ではなくmetadata.financial_content=false、native分類/金融採用とも別。index自体の公表・改訂日時は不明でsource.published_atはnull、取得/local抽出観測/実DB初保存を区別する。

source-only1本・逐語引用1件。native object/content/raw SHAとUnicode/UTF8位置は `source-quotes.json`。既存sharedbuilderを再利用しwhole original capture/rawを保持し、producer側でraw/text/契約/stableID/引用/2anchorsと初期32pins不変を照合。汎用byte verifier未実行をmatchedとはしない。

DB/production code/旧file/case/normalizer/金融採用/IR草案/送信0。今回の1 GET phaseをfreezeし追加GET0、root受入待ち。
