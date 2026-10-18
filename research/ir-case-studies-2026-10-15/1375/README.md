# ユキグニファクトリー（1375）：公開資料未登録企業の初期確認

**公式事業説明・一般IR FAQ・IR資料室を保存した。決算短信本文は未取得。** 明示された決算短信URLが301を返したため、初期5 GETでは追従せず区切った。投資候補の選別・仮説・予測・IR送信へ進めていない。

## 再現可能なcoverage順の選択

既存窓口台帳1,819社と実DBをURI `mode=ro` で読み、sourceが0件の既存会社1,814社を証券コードの辞書順で並べた先頭が1375。投資順位ではなく公開資料カバレッジを埋める順番である。`selection.json` に抽出SQL・時刻・台帳SHA・既存会社snapshotを保存。会社はwatch・held falseのまま、DB書込み・会社新規作成なし。

過去確認された公式URLは https://www.yukiguni-factory.co.jp/ 、窓口は https://www.yukiguni-factory.co.jp/contact/ 。窓口の過去確認は、現在の受付条件・沈黙期間・送信適格性の確認ではない。フォームへアクセス/入力/送信していない。公式hostの社名とFAQの明示1375を照合した。

## 初期5 GETと原文

| capture | URL | HTTP | 初回取得UTC |
|---|---|---|---|
| 01 | [robots.txt](https://www.yukiguni-factory.co.jp/robots.txt) | 200 | 2026-10-15 05:04:54.042210 |
| 02 | [公式root](https://www.yukiguni-factory.co.jp/) | 200 | 05:05:02.056842 |
| 03 | [IR資料室](https://www.yukiguni-factory.co.jp/ir/library/) | 200 | 05:05:12.576401 |
| 04 | [資料室に明記された決算短信URL](https://www.yukiguni-factory.co.jp/ir/library/results) | 301 | 05:05:25.667461 |
| 05 | [rootに明記されたIR FAQ](https://www.yukiguni-factory.co.jp/ir/faq/) | 200 | 05:05:32.203321 |

最大5 URLを各1回。retry/redirect追従/JavaScript実行0、URL推測・検索・障害診断なし。robotsはwildcard Disallow空、sitemapは取得しなかった。root→資料室、資料室→決算短信、root→FAQのliteralリンクとindexを `link-provenance.json` に保存した。商品Q&AとIR FAQは異なるリンク/用途として扱った。

04のLocationは `https://www.yukiguni-factory.co.jp/ir/library/results/`。**301はcanonical先の案内で、503などの取得障害と同じ分類にはしない。** この初期調査では自動/手動いずれの追従もせず、転送先の本文を取得済みとしていない。受信した0byte本文は明示の空rawとSHA（`e3b0c442...`）、空text、transport snapshot/Locationとして保存し、発行体の公開本文sourceにはしなかった。

全5 captureのraw/text/SHA/transport/初回取得を保存。HTMLのraw decodeと `*.visible.txt` の可視本文を分け、元データを保持した。成功4 sourceだけを `source-bundle.json` に格納し、`companies=[]`、`theses=[]`、全件 `financial_inputs_verified:false` / `financial_values_automatically_adopted:false`。索引やFAQを財務本文へ読み替えない。公開日を金融開示として確認していないため `published_at:null`。rootニュース日付、ページschema/software日付、copyrightで最新決算期を補わない。

## 本文で確認したこと

本文10引用・source ID・文字offsetは `sources.json` に保存した。見出しだけではなく回答/説明本文を含めた。

| 確認 | 原文/引用ID | 支持する範囲 |
|---|---|---|
| 事業 | 「茸事業、その他食品事業を行っています。」`faq-business` | 公式の事業説明。セグメント売上・収益認識の確認ではない。rootのキノコ生産/開発の説明も `root-business-origin-and-product-story` に保存。 |
| 会社コード | 「証券コードは何番ですか？ 1375です。」`faq-code` | 公式host/会社名と既存台帳の会社identityを対応。 |
| 決算月 | 「決算はいつですか？ 毎年3月末です。」`faq-year-end` | 一般的な期末。最新の正式会計期間の開始日・比較期・基準・連結範囲は別確認。 |
| 設立 | 「1983年7月です。」`faq-company-founding` | FAQの会社設立説明。比較可能な財務履歴、赤字成長/循環ルートの確定には使わない。 |
| 公開資料への案内 | `library-category-body` は決算短信/有報/半期報告/説明資料等を案内。`faq-latest-material-pointer` は最新・過去資料の所在を説明。 | 具体的最新決算本文・日付はまだ未確認。 |
| 予定と配当基準日 | `faq-announcement-schedule-pointer` はIRカレンダーへの案内。`faq-dividend-record-dates` は期末3月31日/中間9月30日の基準日を記載。 | 次回決算の確定日、配当金額/支払日/配当方針ではない。 |

事業/コード/決算月/資料所在/一般的な配当基準日は公開回答があるため、同じ質問をIRへ送る必要はない。今回のFAQは一般IR FAQで、公開決算説明会Q&Aを取得したことにはならない。

## 残る不足

最新決算期・正式期首期末・日本基準/IFRS・連結/単体・比較期・金額単位・実績と会社予想の区分、財務数値そのものは未取得。カレンダー本文も未取得で、次回日付を推測しない。公開決算Q&Aの存在/本文もunknownで、公開資料で未解決と断定していない。

保存済みDamodaran routingに必要な認識済売上・費用・利益/CF・税・再投資・株数・資金制約・比較可能な履歴が不足する。通常model点検はneeds_data、金融/循環/young-lossの該当はnull。食品業という業種名や設立年だけで評価routeや除外を決めない。Anthropic参照の公開情報先行で事実と不足を分けた研究記録であり、将来予測・倍率・確率・税率・売買閾値・モデル評価を作成していない。

`review.json` に確認済み/未確認/IR不要の問いを保存。`validation.json` で成功source4件の契約/stable ID/raw・snapshot・本文、全5raw/text SHA、本文10引用とliteralリンク3経路を確認した。DB分類/登録・仮説/質問登録・会社状態変更・IR送信/注文は行っていない。初期5 GETはここで終了。
