# 1975 朝日工業社：有限の初期公開研究

343社の個人IR受付明示候補のcoverage順で1963の次が1975。投資順位や業種除外ではない。1,819社の元台帳との同一行、個人explicit、実SQLiteの公開source0をURI mode=ro / query_onlyで照合。会社研究dirなし。旧記録は窓口の成功7 GETと保存本文を使った外部著者検索route0で、財務資料の取得停止ではなかった。SQL・会社snapshot・両CSVのSHA/列/件数・旧coverage/保存経路は `selection.json`。

今回3 GETで停止した。全て同host、holds-v8の12 exact hostを照合し固定UA/通常proxy/TLS、redirect/retry/JS/検索/フォーム/Cloud診断は0。

| GET | 取得対象 | 結果 |
| --- | --- | --- |
| 1 | `https://www.asahikogyosha.co.jp/robots.txt` | 200・完全243B。管理領域等のDisallowを読み、各対象URLへのcan_fetchを照合 |
| 2 | `https://www.asahikogyosha.co.jp/` | 200・完全86,150B。rootに日本語Q1短信と対応説明資料のliteralがある |
| 3 | `https://www.asahikogyosha.co.jp/wp-content/uploads/2026/08/98_1st-quarter-financial-results.pdf` | 200・完全263,639B、日本基準・連結Q1短信12頁 |

root links[102]→本文を直接たどったため中間indexは取得不要だった。短信p4自体に経営成績の説明があり、残枠消化は行わない。root links[101]の対応決算説明PDFは未試行の次候補として `link-provenance.json` に保存。2026年8月4日という掲載ラベルは本文確認ではない。今回見たrootの財務リンクから公開決算Q&Aは特定していないが、全サイトの不存在は認定しない。採用のFAQは対象外。

raw完全entity・全HTTP開始/headers/完了/原raw保存時刻・response・SHAは `capture.json` と `01–03.json`。PDF全文を `text/03-full.txt` とsource.contentに保持した。**画像/意味確認は物理1・2・4・7の4頁だけ**。3は見出し等の場所選定のみ、5/6/8/9/10/11/12は未読。全文抽出は全冊意味読了ではない。公表日8月4日は物理1のday精度、source.published_atはnull。原HTTP取得完了をsourceの取得時刻として保持し、後のlocal抽出観測や実DB初保存とは区別する。

- Q1実績は2026年4月1日–6月30日、比較は2025年同期間。百万円未満切捨て、売上19,483・OP2,205・経常2,334・親会社純利益1,546。通期2026年4月–2027年3月の112,500・12,200・12,400・9,250は**会社予想**、8月4日時点で据え置き。分析者の将来予測や入力採用ではない。
- 設備工事は売上増/粗利率改善で営業増益、機器製造販売は売上/受注減で営業損失拡大。機器事業の下半期受注回復は会社の「見込み」であり契約成立・実績・確率ではない。原材料/労務費などのリスクを述べることと正確な将来費用は別。
- Q1の重要な連結範囲変更/四半期特有処理/列挙された方針・見積・修正再表示は「無」。現在まで範囲不変とは認定しない。発行済自己株込み27,200,000株・自己株1,324,717株・Q1期中平均25,875,312株を区別し、現在/希薄化後分母へ転用しない。EPS/DPSは円。配当合計144円は会社表示で、独自の将来配当列を作っていない。
- P/Lは営業/経常/税前/税/親会社利益を分ける。表示0は百万円未満切捨てで、厳密0や一時要因不存在とは認定しない。BS説明の現金預金減少をCFO/FCFと扱わない。CF/セグメント注記p9・連結受注補足p10は保存全文内にあるが未読で、未作成/0も認定しない。

詳細は `review.json`、原文5引用のnative object/content/raw SHAとUnicode/UTF8位置は `source-quotes.json`。Anthropicの公開情報先行・metrics/guidance/strategy-changeとDD前読、Damodaranの利益/主体/期間/単位/将来CFの分離を使用した。業種名によるモデル選択、正常利益、価格/倍率/確率/閾値は作っていない。

source-only2本（root索引・原PDF）。rootの資料ラベルを金融本文と呼ばず、metadata.financial_contentはproducerの内容判断であってnative分類/金融採用ではない。既存sharedbuilderを再利用し、原capture object・raw全文を保持。汎用byte verifierは未実行でmatchedとはしていない。`validation.json` はraw/全文/契約/stableID/5引用/4画像のproducer照合で、rootの独立意味受入待ち。

DBwrite・共有code/旧file変更・normalizer・新case・金融採用・IR草案・外部送信は0。今回をfreezeし追加GET予定0。
