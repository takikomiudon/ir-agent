# 2315 CAICA DIGITAL：有限の初期公開研究

343個人IR明示候補のcoverage順で2163の次が2315。投資順位ではない。元1,819台帳同一行・explicit・実DB公開source0（mode=ro/query_only）・会社研究dir0を照合。旧窓口はroot503の後に保存root200/form200で確認完了済み。この回復を再開せず、公式issuer財務本文の初回研究として分けた。web.fisco.jpのrobots拒否/holds-v8は維持し、旧10月1日notice302も追跡/再試行0。元CSVのSHA/列/件数・SQL・会社snapshot・旧record/author scan route0・経路区別は `selection.json`。

| GET | 対象 | 結果 |
| --- | --- | --- |
| 1 | `https://www.caica.jp/robots.txt` | 404・完全60,487B。既存complete404 missing branch、HTMLを許可規則としてparseしていない |
| 2 | `https://www.caica.jp/` | 200・完全92,083B |
| 3 | `https://www.caica.jp/ir-library/` | 200・完全106,937B。root literal[25]から静的資料一覧へ |
| 4 | `https://www.caica.jp/wp-content/uploads/2026/09/20260914_1_tanshin.pdf` | 200・完全524,739B。一覧literal[64]の最新日本語Q3短信18頁 |

最大5 GETに対し4で停止した。samehost/holds-v8/robots branchを各対象で照合、固定UA/通常proxyTLS、redirect/retry/JS/検索/フォーム/Cloud診断0。旧Fisco/旧notice/窓口のGET0。別の資料探索や枠消化はしない。

原raw/全HTTP時刻/response/原保存/完全性/SHAは `capture.json` と01–04.json。18頁の全文textを `text/04-full.txt` とsource.contentへ保存。**本文の意味/画像確認は物理1・2・4・5の4頁**。3は場所選定、6–18は未読。p5のITサービス節はp6へ続くため、全節を読了とはしない。公表日は9月14日day精度、source.published_atはnull。原取得/local抽出観測/実DB初保存を区別する。

今回、公表本文で確認できた境界は以下。

- Q3累計は2025年11月1日–2026年7月31日、百万円未満切捨て。売上4,693・OP111・会社調整後EBITDA199・経常△12・親会社利益△126。通期2025年11月–2026年10月の売上6,166・OP107・経常107・親会社利益91は9月14日時点据え置きの**会社予想**。独自のQ4利益・予想修正・正常利益を作らない。期末配当予想は未定で、dashを0にしない。
- 善光総研は2月6日子会社化、BSは中間期末から連結、当Q3PLは2026年3–5月の3か月分を反映と明記。9か月フル寄与や同一範囲の有機成長としない。7月1日吸収分割、7月29日Fisco追加取得/持分法化も会社説明として確認した。p4の7–8月PoC完了は7月末を超える記述を含み、商用化移行を売上/受注保証へ昇格させない。
- 会社定義の調整後EBITDAはOP＋減価償却費＋のれん償却費。p5は非GAAP補足・他社単純比較不可と説明する。のれん償却57百万円は公表値だが、調整後指標をCF/正常利益/評価入力へ採用しない。
- 営業外収益56百万円には補助金32、営業外費用179には持分法投資損失等を含む。179全額をFisco減損額と断定しない。会社は時価変動による追加減損の可能性にも言及する。営業利益・経常損失・親会社損失を混同しない。
- 特別利益の段階取得益207、のれん減損207・特別損失計214を別区分で保持。「自社株価上昇に伴う取得額上振れで、善光総研の事業価値低下によらない」は会社の説明であり、独立した事業価値認定ではない。ほぼ同額をもって税/純損益/CF影響0とせず、OPへの足戻しもしない。
- 期末発行自己株込み181,081,018・自己株8,799,185・累計平均168,046,645株。自己株/平均の控除には子会社/持分法関連会社保有の自社株も含む。現在/希薄化後分母へ転用しない。今期の希薄化後EPSのdashは「希薄化効果を有する潜在株式がない」という説明で、潜在株式が一切ないと一般化しない。

P/L13・業績予想説明10・株式注記15・セグメント16/17・CF注記18は全文保存内だが未読。CF作成有無/0や正常化、詳細な取得会計・株式/税/CF、将来収益力は別確認に残す。表紙の補足資料「有」だけで本文確認とはしない。今回の静的一覧から特定の最新説明/公表Q&A literalは確認できておらず、全サイトの不存在認定や別経路探索はしない。

source-only3本（root・静的一覧・原PDF）、逐語引用6件。HTML資料ラベルは金融本文ではなく、metadata.financial_contentはproducerの内容判断でnative分類/金融採用とは別。原object/content/raw SHAとUnicode/UTF8 offsetは `source-quotes.json`、解釈と残余は `review.json`。Anthropicの公開先行DD/metrics/guidance/strategyとDamodaranの主体/利益段階/単位/期間/CF分離を適用し、業種名で除外/モデル選択したり価格/倍率/確率/閾値を作ったりしていない。

既存sharedbuilderを再利用しwhole original capture/rawを保存。producer検証は4entity/raw/全文/3契約/stableID/6引用/4画像まで、汎用byte verifier未実行をmatchedとはしない。DBwrite・共有code/旧file変更・新case・normalizer・金融採用・IR草案・送信0。freeze後追加GET0、root独立意味受入待ち。
