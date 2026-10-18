# 135A IRライブラリの限定追加確認

初期5 GETで得られなかった財務本文を、別枠の最大3 GETで取得した。3件ともHTTP 200、各URL1回、再試行・リダイレクト追従0、JavaScript実行0。対象会社はVRAIN Solution（135A）。投資先選定・モデル予測の採用・IR送信適格性の確認ではない。元caseの原文・manifest・source-bundleを変更していない。実DBの読取・更新も行っていない。

## 取得経路と範囲

1. 元の公式IRライブラリHTMLに明記された [XjStorageLoaderLibrary.js](https://www.xj-storage.jp/resources/AS06543/XjStorageLoaderLibrary.js) を**データとして**取得。初回取得2026-10-15 04:39:21.769011 UTC。
2. JSに明記されたdomain、endpoint、company=AS06543、決算短信doctype、既定len=10000、output=jsonから [一覧URL](https://www.xj-storage.jp/public-list/GetList2.aspx?company=AS06543&len=10000&doctype=1,2,3,4,16,17,18,19,20,21&output=json&callback=ir_agent_review) を構成。初回取得04:42:15.119500 UTC。callbackだけはcaller側が作るtransport識別子として固定の `ir_agent_review` を指定した。jQueryが実際に生成する識別子を再現したとは主張しない。`request-derivation.json` に8箇所の逐語引用・offsetと構成理由を保存。
3. 前後空白を除いた応答が厳密に `ir_agent_review(` と `);` で囲まれることを検証。JSON部分だけを既存 `ir_agent.models.parse_json` で読み、重複キー・非有限数を拒否した。応答のコードは実行していない。11件の公開索引の先頭が、日付の降順と最大日付の両方で最新だった。その項目が明記する [PDF-GENERAL](https://contents.xj-storage.jp/xcontents/AS06543/0e4abefd/2c7d/4512/9376/0761580b1ba5/140120260831528808.pdf) を最後の1 GETで取得。初回取得04:42:37.094960 UTC。

**JSとJSONPは索引・取得経路であり財務本文ではない。財務本文は3件目のPDF1件、9頁だけ。** 最新という表現は取得した決算短信カテゴリー11件の範囲。説明資料/Q&A/別カテゴリーを網羅したとはしない。元ページのrobots確認を引き継いだ限定リンク追跡で、追加のrobots/root探索やURL推測はしていない。

各rawバイト、UTF-8抽出本文、snapshot、SHA-256、初回取得日時は `manifest.json` と `01..03.json` に保存した。`source-bundle.json` は既存会社 `jp:135A` の3 sourcesのみ、`companies=[]`、`theses=[]`。公開索引の `2026/10/14 16:15:00` にtimezoneが明記されないため、全sourceの `published_at` はnull。短信表紙の日付に基づくPDFの `metadata.publication_date` は2026-10-14である。

## 公開情報で確認できたこと

以下の引用IDの全文・PDF頁・頁内文字offsetは `sources.json` に保存した。見出しだけで本文の結論を支えないよう、該当本文または期間・単位付き表まで含めた。

| 確認事項 | 公開根拠と範囲 |
|---|---|
| 正式な期・会計範囲 | PDF1頁 `identity-and-interim-period`：「2027年２月期 第２四半期（中間期）決算短信〔日本基準〕(非連結)」、中間期2026年3月1日〜8月31日。会社名とコードも同頁。 |
| 最新の会社予想の対象と変更有無 | PDF1頁 `full-year-company-forecast` は通期2026年3月1日〜2027年2月28日、EPS欄等を含む。PDF5頁 `investing-financing-and-forecast-unchanged` は4月14日公表予想から変更なしと説明。これは会社予想であり独自予測ではない。 |
| 配当予想と株数 | PDF1頁 `dividend-company-forecast` は実績・予想の区別と年間配当表、PDF2頁 `shares-and-caution` は自己株式を含む発行済株数/自己株式/期中平均株式数。予測EPSの分母・将来希薄化・長期配当列の十分な根拠とはしない。 |
| 有償事業の会社説明 | PDF4頁 `business-and-observed-interim-results` に製造業向けAI/IoT、画像検査/コンサルティング、受注残の納品・拠点開設・採用活動等の会社説明。PDF9頁 `notes-and-single-segment` は製造業DX単一セグメントを明記。成長率や費用の持続性は別途検証が必要。 |
| 中間CF本文 | PDF8頁 `cashflow-comparison-period-and-table` に営業/投資/財務CF、有形固定資産取得、減価償却・運転資本項目、単位百万円を確認。比較期は2025年3月1日〜8月31日、当期は2026年3月1日〜8月31日。PDF4〜5頁にはその会社説明もある。 |
| 予想の限界 | PDF2頁 `shares-and-caution` は短信が監査人レビュー対象外であることと、業績見通しの達成を約束しないことを記載。 |

「最新短信/対象期間/会計範囲は何か」「会社予想は変更されたか」「CFや有形固定資産取得支出は公表されているか」「単一セグメントか」は公開資料で答えを得たため、IRへ送る質問にしない。公開資料先行の既存Anthropic参照手順に従った研究上の整理で、質問登録は0件。

## 残る不足と次の入力

- 補足説明資料・説明会は表紙に「有」とあるが本文未取得。公開Q&Aも未取得。全公開資料で答えがないとはまだいえない。
- カレンダーは初期確認の概括的な月予定だけで、次回の確定日・時刻を補っていない。
- 会社予想EPS/年間配当、中間CF等は構造化候補に留めた。予想と実績、半期と通期、基本/希薄化後EPSと株数、単位・予想分母の意味を別に確認する必要がある。会社1期予想を将来EPS列・将来DPS列・確率に延長しない。
- 保存済みDamodaran方針のモデル適合には、単一半期の比較だけでは不足する。循環歴・現在規模の再投資正常化、金融規制資本との関係、赤字成長/資金調達の推移等は未確認。業種名、今期増益、今期黒字だけでrouteを断定しない。中間実績CFを通期将来アンレバードFCFへ自動変換しない。
- 株価、独立した将来予測、評価倍率、割引率、確率、価格判断の条件は未取得・未設定。買い/売り、価格目標、現在のIR送信候補は作っていない。歴史的な窓口台帳を現在の送信適格性と読み替えない。

`review.json` に項目別の解決・未確認・次に必要な意味確認を保存。全sourceは `financial_inputs_verified:false`、`financial_values_automatically_adopted:false`。`validation.json` は3 sourceのJSON契約、raw/text/snapshotのSHA、本文11引用の位置、JS設定8引用、JSONP wrapperをオフライン確認した結果であり、投資上の妥当性を保証するものではない。今回の3 GETで調査を区切った。
