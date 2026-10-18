# 1870：短信6値と回顧掲載された旧会社予想3値

受領済みfull-extraction-variantの2原sourceをそれぞれ既存normalizerへ渡し、短信6値・説明資料の旧予想3値を別input/別派生として構造化した。旧partial sourceで生成していない。同じFY・同額の売上予想も旧新を上書き/混合せず保存する。実DB登録・金融モデル採用0、親レビュー待ち。

| 会社の表示項目 | Q1実績 | 8月7日時点の通期予想 | 8月7日資料が示す5月12日旧通期予想 |
|---|---|---|---|
| 売上高（百万円） | 31,596 | 150,000 | 150,000 |
| 営業利益（百万円） | 1,540 | 9,500 | 9,000 |
| 親会社株主に帰属する純利益（百万円） | 2,953 | 9,300 | 8,200 |

短信p1の実績3はreported_fact、予想3はissuer_guidance。明示期間は実績2026-04-01〜2026-06-30、予想2026-04-01〜2027-03-31。日本基準・連結・百万円未満切捨てという短信の表示を保持し、JPY換算値を未丸めの正確経済額とは扱わない。連結2社追加と株式報酬信託の既存注記は別の文脈引用に残す。EPS/株数を抽出・逆算したり、将来の連結範囲を認証したりしていない。

説明資料p2の「前回発表予想（Ｃ）」3値もissuer_guidanceである。1518の旧新予想記録と同様にversion_reference_announcement_date=2026-05-12、observed_in_source_disclosure_date=2026-08-07を分ける。**取得したのは8月7日資料の回顧掲載で、5月12日原版や当時の初回保存・利用可能性は確認していない。** 旧値のsource取得/派生時刻を5月へ遡及しない。

この説明頁は「2027年3月期通期」と連結を明示するが、正確な開始/終了日、日本基準、切捨て規約は同頁で未確認。旧3factはfiscal_year_end_month=2027-03、start_date/end_date=null、accounting_basis=nullとし、丸め規約も未確認に保った。別sourceの短信から補完しない。旧新差額、前年比率、EPS分母、正常利益・税・FCFF、追加の将来予測は作っていない。

`statement-normalization-input.json` / `statement-normalized-bundle.json` は短信6値、`previous-guidance-normalization-input.json` / `previous-guidance-normalized-bundle.json` は説明旧3値。原primaryは各bundle1件ずつで、両originalの全object/metadata/日付・時刻を保持する。原sourceは短信 `case-public:08da739f9283478997dbe73a4e83cf1a13ebba6d3dcafb250614bd227ff93ebe`、説明 `case-public:f8a7900514b1bb4fce3a34846fea09dede4667f97e120b153e95f018624c085f`。派生は順に `disclosed-facts:fbb51dba2b157c33e566d7a6ebc691b1fcef8bfc034509a74b4032b68b9b3a5c` / `disclosed-facts:0c49dc68fc0d0410bfcc3125457fc5636219fff836f99846813d61aa46d14e85`。

対象の短信p1と説明p2の画像を今回目視し、表の列・行・tokenを確認。quotesにはfull source内の逐語文字/UTF8 offset、画像SHA、旧新vintageを保持した。原variantの全text機械抽出を全冊意味確認へ昇格せず、generic byte verifierのmatchedとも呼ばない。原著者は矢作建設工業、抽出reviewはCodexとして分ける。

2派生ともreproduce_disclosed_fact_sourceでreproduced、原content matched、原snapshot matched_supplied_snapshot。同じ生成時刻でのAPI replayも完全一致。値/時刻/再現logとvalue pathを保存したが、value pathはモデル入力割当ではない。旧62fileのSHA不変、9ID重複なし。全financial_inputs_verified=false/meaning_review_required=true、companies/theses空。

新GET・DB接続・原file/production code/schema/共有文書/索引変更・IR質問作成・full suite再実行は0。15値batchのうち本社9値、1866が6値であり、正規化と投資判断への採用を分けたままfreezeする。
