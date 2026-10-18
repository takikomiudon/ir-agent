# VRAIN Solution（135A）：未着手台帳1社の初期公開調査

**公式の事業説明・IR導線・月内カレンダーを保存した。決算本文・最新決算期・公開決算Q&A本文は未取得で、モデル適合は未確定。** この1社で区切り、投資選定・予測・売買判断・送信には進めていない。

## 再現可能な台帳抽出

既存窓口台帳1,819社と実DBをread-onlyで照合し、公開source未登録1,815社を証券コード昇順にした先頭は135A。選定時刻・台帳SHA・公開source数のSQL/観測・会社snapshotは [selection.json](selection.json) に保存した。既存 `jp:135A` はwatch・非保有で、今回会社作成/状態変更なし。公式hostと株式会社VRAIN Solutionの社名を照合し、コードは既存台帳・実DBとの対応に基づく。

過去台帳の窓口は https://vrain.co.jp/ir/inquiry/ 、個人受付explicit。これは過去の確認で、現在の受付条件・沈黙期間・送信適格性を確認したことにはしない。フォームは取得/入力/送信していない。

## 最大5 GETの範囲

| capture ID | URL/資料 | HTTP | 初回取得UTC |
|---|---|---|---|
| vrain135a-01 | [robots.txt](https://vrain.co.jp/robots.txt) | 200 | `2026-10-15T04:30:00.550844+00:00` |
| vrain135a-02 | [株式会社VRAIN Solution | 製造業に特化したAI技術でDXを実現 株式会社 VRAIN Solution](https://vrain.co.jp/) | 200 | `2026-10-15T04:30:04.908390+00:00` |
| vrain135a-03 | [IR情報 | 株式会社 VRAIN Solution IR情報 | 株式会社 VRAIN Solution](https://vrain.co.jp/ir/) | 200 | `2026-10-15T04:30:16.640989+00:00` |
| vrain135a-04 | [IRライブラリ | 株式会社 VRAIN Solution IRライブラリ | 株式会社 VRAIN Solution](https://vrain.co.jp/ir/library/) | 200 | `2026-10-15T04:30:46.115175+00:00` |
| vrain135a-05 | [IRカレンダー | 株式会社 VRAIN Solution IRカレンダー | 株式会社 VRAIN Solution](https://vrain.co.jp/ir/calendar/) | 200 | `2026-10-15T04:31:04.492114+00:00` |

全5件200、各1回だけ、redirect/retry/検索/URL推測なし。robotsの/vrain/wp-admin/禁止を尊重し管理領域へアクセスしていない。原raw/text/snapshotとSHA・初回取得を保存。[source-bundle.json](source-bundle.json) はcompanies=[]/sources5/theses=[]、金融入力未検証。公開日が未確認なので全件published_at=null/metadata.publication_date=null。ニュース日付・copyright・scriptのversionを財務開示公表日へ読み替えない。

IR/最新資料一覧は資料区分への案内がある一方、取得静的本文には日付付き決算本文/具体的PDFリンクがなかった。元HTMLにはXjStorageLoaderLibrary.jsへのliteral参照がある（[sources.json](sources.json)にraw SHA/quote/位置を保存）が、script/外部データをGET・実行していない。決算資料や公開Q&Aが存在しないという意味ではない。5 GETの上限で止め、エンドポイントを推測して埋めていない。

## 確認できた事業と意味の不足

公式rootは製造業向けのAI外観・異音振動検査ソフトウェアPhoenixシリーズと、人材育成から開発実装支援までのDXコンサルティングを説明する。提供製品は確認できるが、認識済売上・販売単位・継続課金/保守・セグメント構成は未確認。

DXコンサル欄に会社が「リピート率90%以上」と表示することは確認した。ただし対象母集団・計測期・リピートの定義が未確認なので、企業全体の収益継続率・ARR・回答確率や購入閾値へ変換しない。

カレンダーは通期4月中旬、総会5月下旬、1Q7月中旬、2Q10月中旬、3Q1月中旬という年/具体日/時刻のない目安で、予告なく変更可能との注記がある。期首期末や今年の発表日、取得時点で発表済みかは不明。次回正確日付はnull。

## 公開回答とモデル適合

公開決算Q&A本文を取得していないので、「公開Q&Aで解決した質問」は0件。不存在の断定でもない。一般的な製品/サービスの内容、カレンダーの月内目安は公開ページ本文で既に説明されているため、そのままの質問を未解決IR質問にしない。IR FAQと商品FAQの異なる明示リンクを保存し、内容を同一視していない。

Anthropicのearnings-preview/thesis-trackerに沿って公開情報・未確認・反証に必要な入力を分け、Damodaranの採用済みroutingに沿って事業自身の利益/再投資/資金/履歴を点検する。AI・グロース市場・製造業顧客というラベルからyoung-loss/景気循環/投資適格性を機械判定しない。

| 点検 | status | 確認内容または不足 |
|---|---|---|
| business_offer | supported_public_description | 製造現場向けAI外観/異音振動検査ソフトと、人材育成から開発実装までのDXコンサルティングを公式に説明。 |
| repeat_kpi_meaning | needs_definition | 会社はDXコンサル欄でリピート率90%以上と表示。 |
| latest_financial_material | needs_data | IR/資料一覧の静的本文と導線はあるが、最新期・日付付き決算本文/PDFは今回未取得。 |
| public_earnings_qa | needs_data | IR FAQへの明示リンクは保存。決算説明会の公開Q&A本文は未取得。 |
| reporting_period_and_basis | unknown | 正式な会計年度末・期首期末、連結/単体、日本基準/IFRS、比較期間・株数。4月通期発表の目安から2月期と推測しない。 |
| scheduled_event_dates | partial_calendar_only | 通期4月中旬/1Q7月中旬/2Q10月中旬/3Q1月中旬、総会5月下旬という目安と変更可能注記を確認。 |
| ordinary_model_fit | needs_data | 認識済売上/費用・利益・CF・再投資・税/株数、前提と定義。売上構造が分からないままEPS×PERやDCFへ進めない。 |
| cyclical_or_commodity_fit | unknown | 製造業顧客向けという説明だけでは自身の利益循環を確定できない。多年度履歴、顧客設備投資/採用期間、原価/再投資・現在規模の根拠。 |
| young_loss_fit | unknown | 創業/商用化履歴、営業赤字の有無、収益化と資金/希薄化。AI・グロース市場・製品の存在だけでyoung-lossへ分類しない。 |
| financial_equity_fit | unknown | 規制資本/金融仲介の実態確認。業種タグから機械的にモデルを確定/排除しない。 |

次は保存された明示リンクから正式短信/説明資料・IR FAQ本文を得られるか確認する余地があるが、今回の5 GETでは実施しない。最新性・期/基準/比較範囲・株数と、多年度利益/CF/再投資/資金が不足するため、仮説や送信準備済み質問は作成していない。

詳細は [draft.json](draft.json)。実DB登録/分類完了・会社状態変更・株価/倍率/確率/数値方針/予測・IR質問登録/送信なし。

## 本文を含む代表引用

### business-introduction

`case-public:bdae3949d5e7a93f60ac5675ecd9635ca759a4362dd71bdf0984e70e4738a3e1`、本文文字位置 `831:900`（HTML、PDF頁なし）。支持する範囲: 製造現場向けの事業紹介本文。売上・利益実績を証明する引用ではない。

> BUSINESS 事業紹介 製造現場の業務効率化に貢献 「最先端のAI技術」と「豊富な現場知識」で 製造業のあらゆる課題を解決し続けます 

### ai-product-offering

`case-public:bdae3949d5e7a93f60ac5675ecd9635ca759a4362dd71bdf0984e70e4738a3e1`、本文文字位置 `912:1115`（HTML、PDF頁なし）。支持する範囲: Phoenixシリーズの外観検査等ソフトウェア提供を会社が説明。認識済売上/継続課金の形態は未確認。

> AI PRODUCT AI プロダクト 独自のAI技術を活用したアプリケーション"Phoenixシリーズ"で 従来の手法では難しかったような外観検査の自動化を実現させます AI学習・検証用ソフトウェア Phoenix Vision 詳しくはこちら > AI外観検査ソフトウェア Phoenix Eye 詳しくはこちら > AI異音振動検査ソフトウェア Phoenix Analyzer 詳しくはこちら > 

### consulting-and-repeat-claim

`case-public:bdae3949d5e7a93f60ac5675ecd9635ca759a4362dd71bdf0984e70e4738a3e1`、本文文字位置 `1115:1271`（HTML、PDF頁なし）。支持する範囲: DX支援の内容と会社マーケティング上のリピート率表示。期間/母集団/定義の妥当性は未確認。

> DX CONSULTING DX コンサルティング 製造業のお客様のあらゆる課題を解決するお手伝いさせていただきます。 その内容は人材育成から開発実装支援まで幅広いサービスを展開しています。 サービス開始時よりご好評いただき、リピート率は90%以上を維持しています。 DX コンサルティング 詳しくはこちら > 

### generic-calendar

`case-public:decc7b41b89118944070d42554aef7998516b16bba1bd993c6afcd6c5076d98c`、本文文字位置 `483:617`（HTML、PDF頁なし）。支持する範囲: 年/具体日/時刻のないカレンダーの月内区分と変更可能の注記。実際の開催済み判定や次回ISO日付は支持しない。

> IRカレンダー ホーム IR情報 IRカレンダー IRカレンダー ４月中旬 通期決算発表 ５月下旬 定時株主総会 ７月中旬 第１四半期決算発表 10月中旬 第２四半期決算発表 １月中旬 第３四半期決算発表 ※都合により予告なく変更する場合があります。ご了承ください。 

## 親の取り込み

[実分類記録](actual-intake.json)で親も5raw/text/snapshot SHAと7本文引用・1原HTML観測をCRLF保持で照合。5sourceを追加・分類し、実台帳は41source/41分類、完了intake7件。既存36sourceと会社watch/非保有は不変。135Aのfinancial_contentは全falseで、財務本文を得たと報告しない。新leaseを計測したがactive分析や会社処理能力は未計測、仮説/予測/送信は追加していない。
