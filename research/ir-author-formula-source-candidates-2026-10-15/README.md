# 岩井コスモ公式保存導線：別の日本株個別レポート候補は0

**日本株の採用EPS年度・目標倍率を確認するための、未処理の別銘柄アナリストレポートURLは、この保存済み導線内では0件。追加取得せず本経路を閉じる。** 未読の米国株個別レポートへのliteral linkは1件あるが、日本株という対象範囲から除外した。これは同社の他の全ページに資料が存在しないという結論ではない。

## 確認範囲と保存状態

`research/published-rating-policies-2026-10-15/sources.json` の `retrievals[10]`、公式 `https://www.iwaicosmo.co.jp/investment/net_report/` entryを確認した。旧entryは可視textを保存するが、raw HTMLや元href列を含まない。申告body SHAは `2ccf0a4d3c0f6d079aec3aa696a4c9ad2987fc2d07b3f3c5f4e5649c62185aeb`、27,928bytes、HTTP200、受領2026-10-15T01:19:22.901295+00:00、公表日不明である。

既存関連capture `research/ir-explicit-valuation-route-review-2026-10-15/iwaicosmo-entry-followup/` の `capture.json`、`actual-anchors.json`、README、および入口raw HTMLだけを利用した。同followupの `GETs[1]` は同じURLのHTTP200入口で、本文完了2026-10-15T10:31:47.492242+00:00、raw SHAは旧entryの申告SHAと同値。rawファイルは `raw/2ccf0a4d3c0f6d079aec3aa696a4c9ad2987fc2d07b3f3c5f4e5649c62185aeb`。7件の可視sample anchorについて保存offsetの逐語一致とraw SHAをread-onlyで照合した。offsetはdecoded HTMLのUnicode code point、end-exclusiveである。

既読6323 `sample_analyst.pdf` の再取得・PDF復号・画像表示・意味再読は行っていない。既存anchorの処理済みフラグと既存followup READMEの結論だけを参照した。PDF原本を新たに評価・引用していない。

## 候補判定

日本株で詳細分析を述べる「アナリスト銘柄情報」の唯一の実hrefは `/investment/net_report/pdf/sample_analyst.pdf`。保存anchorは `previously_read_known_report:true`、既読6323と同一URLのため候補から除外した。「岩井コスモ投資情報」`sample_info_investment.pdf` も既存followupで処理済みであり、同READMEは対象紹介範囲で目標株価・選択年度EPSによる目標PER/明示評価式未確認と報告している。今回は同PDF本文を再読していない。

範囲外の未処理個別レポート参考は次の1件だけである。これを日本株の著者評価式の取得候補として採用しない。

| literal URL | 保存場所・元href | 既存処理状態 | 著者式確認との関係・除外理由 |
|---|---|---|---|
| https://www.iwaicosmo.co.jp/investment/net_report/pdf/sample_usa1.pdf | 上記`actual-anchors.json`の`$.anchors[6]` / `capture.json`の`$.GETs[1].links[102]`。元href `/investment/net_report/pdf/sample_usa1.pdf`。raw HTML文字offset [14562, 14671)。 | 同anchorでは`body_read_this_task:false`、`previously_read_known_report:false`、`Not fetched`。この有限保存範囲で未処理。本文未取得なので実銘柄・採用EPS年度・目標倍率・著者式の有無は不明。 | 入口の名称「米国株オリジナル個別銘柄情報」と説明「世界市場の主役である米国の有望銘柄情報をご紹介いたします。」は個別レポートを示すが、式掲載は保証しない。米国株のため対象外。 |

残る可視sampleは「マーケットの窓」（国内指標終値・米国市場概況）、「投資のミカタ」（投資情報活用方法）、「高利回り銘柄特集」（テーマ別の一覧）、「株式分割銘柄」（分割発表一覧）。可視説明から別の日本株個別分析・目標評価式を期待する具体的根拠がなく、候補に追加しない。HTMLコメント内には`sample_select.pdf`という文字列もあるが、可視/有効anchorではないため活動中の導線として扱わず、再開・取得候補としない。

## 実施境界

新GET・ネットワーク・実DB操作・コード変更・著者式作成は0。このREADMEだけを新規保存した。URLの命名規則推測、JS/API、会員ログイン、別host探索は行っていない。著者threshold未指定を0へ補わず、市場PERから公正倍率を逆算しない。対象0件のため、当該導線で不足する採用EPS年度・倍率を解消できたとは述べない。

確認した保存ファイルのSHA-256：

- `sources.json`: `a47b717e3f73da5f5eff7d7e4c099ca43444c2af2590a6a1cd8bccb193eced73`
- 既存followup `capture.json`: `90cf5e1e4ef11df42c3f7fcf0889b8e5f44dd2b47124a9dfab72a44f79aed539`
- 既存followup `actual-anchors.json`: `e22a80f894a9ce8db1b5e9da1dc4a1bcc84fcb2d51b1ae0d0be2698d9969a45c`
- 入口raw HTML: `2ccf0a4d3c0f6d079aec3aa696a4c9ad2987fc2d07b3f3c5f4e5649c62185aeb`

記録時刻：2026-10-15T21:27:53.700148+00:00。
