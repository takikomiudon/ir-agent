# データ取得アダプター

J-Quants公式Python SDKと独立プロジェクト `edinet-tools` を、読み取り専用のアダプターとして接続する。基本機能とモックテストはPython標準ライブラリで動く。APIを実際に利用する場合は任意依存を追加する。

```bash
python -m pip install -e '.[data]'
```

対象SDKは `jquants-api-client==2.8.0`、`edinet-tools==0.9.0`。公開PyPIメタデータ・SHA-256を照合した配布wheelと以下の固定コミットの実装を2026-10-11（日本時間）に確認した。SDK契約・データの利用権限はOSSライセンスと別に確認する。

| 接続先 | 確認した既存実装 | 利用するAPI |
|---|---|---|
| J-Quants | [公式ClientV2](https://github.com/J-Quants/jquants-api-client-python/blob/4a6ab360dbd43e763595f7ad362e749a25d6439d/jquantsapi/client_v2.py) | `ClientV2(api_key=...)`、`get_eq_master(date=...)`、`get_eq_bars_daily(date_yyyymmdd=...)`、`get_fin_summary_cursor(date_yyyymmdd=...)` |
| EDINET | [edinet-toolsのAPI関数](https://github.com/matthelmer/edinet-tools/blob/94fb7ec5843b751c15379f053ee70ceb8d6d0445/edinet_tools/api.py)、[公開解析関数](https://github.com/matthelmer/edinet-tools/blob/94fb7ec5843b751c15379f053ee70ceb8d6d0445/edinet_tools/parsers/__init__.py) | `fetch_documents_list(date, type=2, api_key=...)`、`parse_xbrl(zip_bytes, doc_type_code, source=..., doc_id=...)` |

このプロジェクトのアダプターは独自に書いている。runtimeは上記SDKをimportし、SDK実装を組み込んでいない。財務summary連携の根拠確認用コピーは、licenseとともに[隔離したSDK根拠](../research/ir-jquants-financial-summary-integration-2026-10-15/sdk-contract-evidence.json)へ保存する。J-QuantsクライアントはApache-2.0、edinet-toolsはMITで、後者は金融庁の公式SDKではない。

## 共通出力

公開Webの追加取得前に[収集保留の中央索引v4](../research/ir-source-access-holds-2026-10-15/README-v4.md)を読む。今回の8つのexact hostについて、robots原文・HTTP状態・取得完了時刻・UA設定根拠と限界を保存した。wildcard禁止、403で規則未確認、AI個別禁止を受けた運用保留を区別し、同じ取得の再試行・UA変更・迂回を避ける。過去の取得へ新しい規則を遡及したり、アクセス制約を投資対象の除外理由へ置き換えたりしない。

完全受信したrobotsのHTTP 404は、既存FetcherとPython標準の扱いに合わせ「robots未配置」として記録する。404のHTMLを規則や明示的な許可とせず、そのURLを再取得せずに、既知の公開本文URLの初回取得を残りGET予算内で行える。[1723での適用根拠](../research/ir-case-studies-2026-10-15/1723/robots404-handling-clarification/README.md)を参照する。401/403/429、5xx、通信/TLS失敗、中央保留や本文の制約は別に扱い、この404手順で解除しない。

出力は `{"schema_version": 1, "companies": [...], "sources": [...]}` のJSON互換辞書。

- 会社IDは `jp:130A` のような証券コードに基づく。コードは数値として計算せず、4桁英数字を保持する。SDKの `130A0` / `72030` は末尾の普通株識別のゼロだけ外す。5桁末尾非0の別種証券は行単位で除外し、`skipped_security_codes` にコード・原行件数・理由を残す。同じ普通株へ併合せず、他の銘柄の取り込みも止めない。
- マスター等から取り込んだ会社の `status=active` は監視レコードの状態で、上場適格性・投資推奨・業界スクリーニングの完了を意味しない。投資対象としての確認は別工程で行う。
- 資料には原資料または認証情報を含まないAPI参照URL、原値、取得日時、公表日時、元データのメタデータを残す。
- 資料IDは会社・参照URL・内容・メタデータのSHA-256。取得日時はハッシュに含めず、同じ内容の再取得を重複資料として扱わない。原値や訂正内容が変われば別IDになる。

公開GETから新しいsourceを作るときは、本文の受信完了時刻を `source.retrieved_at` に使う。capture側の同名欄をそのまま転記せず、要求準備・送信開始・応答到着・本文受信完了のどれを指すか確認する。今回の有限取得で使うFetcherは、captureの `retrieved_at` が要求準備時刻で、完了は別の `http_get_completed_at` にある。両方を原記録に保持する。[1833の取り込み用別版](../research/ir-case-studies-2026-10-15/1833/initial-public-review/ingest-timing-review.json)は、本文・ID・metadataを変えずsource取得時刻だけを完了へ合わせた。

先に保存した1518/1721のsourceは要求準備時刻を引き継いでいる。既存原記録を上書きせず、詳細captureの完了時刻と実DBのtrusted first-saveを併せて読む。今回の実DB保存は完了より後であり、公開時刻や過去の投資判断時点へ遡らせない。研究ファイルの申告日時や取得時刻だけで、当時のシステム利用可能性を認定しない。
- 株価は `source_type=market_data`、`requires_research=false`。EDINETの提出一覧・解析結果は `source_type=public_disclosure`、`requires_research=true`。
- JSONの欠損は `null` とし、ゼロには置換しない。Decimalは精度を失わない文字列で保存する。単位・会計基準・連結範囲を確認してから別の計算処理へ入力する。

## J-Quantsの日次取得

```python
from ir_agent.adapters import fetch_jquants_daily

bundle = fetch_jquants_daily("2026-06-10")
```

`JQUANTS_API_KEY` と利用プランをSDKの手順で設定する。明示的な `api_key=` も渡せるが、キーをスクリプト・データファイル・コマンド履歴に書かない。アダプターはキーを保存・出力せず、参照URLにも含めない。

全銘柄の当日マスターと株価を2回のSDKメソッド呼び出しで取得する。各メソッドはSDK内部でページングするため、HTTPリクエストが必ず2回という意味ではない。銘柄ごとにAPIを呼ぶ処理や、SDKの並列 `_range` メソッドは使わない。休日などの株価空結果から終値や出来高を作らない。株価のない日でも取得した会社一覧は残る。

APIの株価 `Date` は取引日であり、公表時刻ではない。このため `published_at` は `null`。取引日は `metadata.trading_date` に保持する。価格調整の原値 `AdjC` 等と銘柄マスター `S33`・`ProdCat` 等も保持し、価格変動率や投資対象の選別は後段で行う。

取得プラン・格納期間・回数制限は [公式データ仕様](https://jpx-jquants.com/ja/spec/data-spec) と [取得制限](https://jpx-jquants.com/ja/spec/rate-limits) に従う。日次処理では必要な営業日のデータを一度取得して共有する。レート制限を並列エージェントで回避する構成にはしない。

## J-Quantsの財務summary

[単日snapshotの契約](jquants-financial-summary.md)を使い、`sync --provider jquants-financials --date YYYY-MM-DD` で明示的に取得する。既存company IDだけをscopeにし、会社追加・status/held更新は行わない。開示日で1 SDK呼出を行うが、内部paginationを含み得る。非空cursor・差分継続・銘柄別並列は使わない。

保存するのはSDK返却rowのJSONで、原HTTP数値tokenや会社PDFの保存ではない。metadata providerは `jquants_financials`、sourceは `public_disclosure` / `requires_research:true`。SDK受領後のローカル時刻を取得時刻とし、`published_at:null` を維持する。各期/予想/非連結fieldの意味・単位の確認、資料分類、金融モデルへの採用は別工程とし、取得成功だけで自動採用しない。

## EDINETの提出一覧と保存済みパッケージ

```python
from ir_agent.adapters import fetch_edinet_documents, parse_edinet_package

index = fetch_edinet_documents("2026-06-10")
# 手元に保存したtype=1のZIPと、その提出一覧の元メタデータを使う。
parsed = parse_edinet_package("data/filing.zip", document_metadata,
                             source="instance")
```

一覧取得は `EDINET_API_KEY` または明示的な `api_key=` を利用する。`edinet_tools.configure()` の共有状態は変更しない。APIのエラー本文を「開示ゼロの日」と誤認しないように、HTTP 200本文内の `StatusCode` / `metadata.status` も確認する。

一覧取得の `content` は**提出メタデータ**。全文を取得したことや財務情報を抽出したことは意味せず、`metadata.index_only=true` を付ける。選別した資料について別途正規の方法でtype=1 ZIPを保存し、`parse_edinet_package()` に渡す。保存済みZIPの解析はキー不要で、インスタンスXBRLかInline XBRLを明示的に選ぶ。未対応形式はエラーになり、別形式へ自動切替しない。

公表時刻には提出一覧の `submitDateTime` を使い、日本時間のオフセットを付ける。日付しかない場合は時刻を作らず `published_at=null` とする。訂正資料の本文に元の提出日が残っても、提出一覧の新しい提出日時と混同しない。`docTypeCode`、対象期間、EDINETコード、本文の単位・出典要素・文脈・抽出フラグを保持する。SDKが `to_dict()` から外す原文・未対応要素のマップも保存する。

`secCode` のない提出者は日本株の会社へ推測で割り当てない。このベースラインの一覧取り込みでは対象外となり、`skipped_documents` に資料IDと理由を残す。大量保有報告等を報告者から投資対象会社へ対応付けるには、本文の対象会社を別途検証する工程が必要。投資信託の複数サブファンド・セグメントの小計・単体と連結など、財務値の対象範囲を自動的に合算しない。

## 検証済みの範囲

キーを持たないモックで、実SDKのメソッド・引数、全銘柄取得、英数字証券コード、日時の扱い、同じ内容の重複排除、訂正資料、欠損値、精度・単位・原文保存、エラーと空結果の区別を検証している。任意SDKがインストールされている場合は、実SDKでのDataFrame変換と合成XBRLの解析もオフラインで検証する。テストが外部APIを呼び出すことはない。

開発時にはJ-Quants 2.8.0・pandas 2.2.3のDataFrame変換を実行し、EDINET 0.9.0には[固定コミットの公開テスト資料](https://github.com/matthelmer/edinet-tools/blob/94fb7ec5843b751c15379f053ee70ceb8d6d0445/tests/fixtures/xbrl/S100YRDM_type1.zip)を渡した。instance / xbrl の両方式で369件の原ファクトと8件の原文ブロックをJSONへ保存できた。元の提出一覧を照合した投資対象会社への帰属や、資料中の全財務値の正しさを検証したという意味ではない。

初期adapter接続時は `uv.lock` の任意SDK入り環境でも、実SDKのDataFrame変換・合成XBRL解析を含む当時の全73テストを実行した。財務summary追加分は[専用の検証記録](../research/ir-jquants-financial-summary-integration-2026-10-15/README.md)、全体の最新受入は[継続作業](ongoing-work.md)を参照する。

契約APIへ接続した実データ取得、EDINETの全42形式、最新のデータ利用権限、証券コードの履歴・企業の合併や上場廃止への対応は未検証。外部APIの利用枠が準備できた後に、取得日の資料件数・会社名・価格・実提出日時を一次資料と照合する。
