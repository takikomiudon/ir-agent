# 1375：canonical決算ページの限定追加確認

**3 GETは全て成功したが、取得できたのは決算ページの静的索引・E-IR設定・ローダーまで。財務本文はまだ0件で、最新決算期・会計基準・連結範囲・数値は未確認。** 初期5 GETとは別枠の追加確認として、この3件で区切った。IR送信、予測・モデル採用、実DB操作なし。

## 明示されたLocationと静的参照

| capture | 実リクエストURL | HTTP | 初回取得UTC |
|---|---|---|---|
| 01 | [canonical決算短信ページ](https://www.yukiguni-factory.co.jp/ir/library/results/) | 200 | 2026-10-15 05:07:55.430243 |
| 02 | [日本語E-IR config](https://www.yukiguni-factory.co.jp/wp-content/themes/ai-yukiguni/assets/js/ir/eir/eir_v5.js) | 200 | 05:08:19.887233 |
| 03 | [E-IR core](https://ssl4.eir-parts.net/Custom/public/v5parts/1375/jp/20250305/core/eir_common.js) | 200 | 05:08:32.386471 |

初期04の301応答が明記するLocationの文字列を、そのまま**新しい明示URL**として親の許可した別枠で01 GETした。初期301と今回200は別snapshot・別取得日時のまま保持。slash補完を推測したり、自動redirectに設定を変えたりしていない。301は503等のアクセス障害と区別する。

01の静的可視本文には、期・日付付きの財務PDFリンクがなかった。原HTMLには `html lang="ja"` と、英語/日本語でconfigファイルを選ぶliteral式がある。これをデータとして読み、日本語側の明記パスを02として取得した。02に明記された1375/jp/20250305、HTTPS/public branch、coreパスと、01の `eir_common.js` 参照から03を構成した。JSを実行していない。原文・位置と解釈は `request-derivation.json` に保存した。

03は次の `app/conf/common_conf.js` のliteral参照を含むが、その段階で3 GET上限に到達した。追加設定・feed・PDFは取得せず終了。全URL各1回、retry/自動redirect/JS実行0、URL・companyID・endpointの推測なし。今回の未取得理由は有限な参照深度の上限で、全3件ともHTTP200だった。本文が不存在、サイトがアクセス不能とは結論しない。

## 保存したものと意味の限界

rawバイト/SHA、raw decode、静的可視本文、transport snapshot、初回取得時刻、manifestを保存。`source-bundle.json` は既存 `jp:1375` の3 sourceだけで、`companies=[]`、`theses=[]`。document_kindで索引/config/loaderを明示し、財務本文に数えない。全件 `financial_inputs_verified:false` / `financial_values_automatically_adopted:false` / `financial_statement_body_obtained:false`。

公開金融資料の日付が確認できないため `published_at:null`。software version日付、JSパスの日付風識別子、web page schema等を決算発表日・最新決算期へ変換しない。

`sources.json` に設定・次の参照の逐語引用3件と、元HTMLのconfig選択式1件をraw文字位置付きで保存した。これらは取得経路だけの証拠で、見出しや会社コードを財務数値・会計範囲の根拠にしていない。新しい金融数値の公開回答は得ていない。

初期caseで分かった会社事業/コード/毎年3月末決算などの一般FAQの確認は保持するが、正式な最新期/比較期・日本基準/IFRS・連結/単体・実績/会社予想・単位・株数等はnullのまま。公開決算Q&A・具体的IR予定も未取得。モデル適合を業種だけで確定せず、金利・税率・予測・確率・閾値も補完していない。

`review.json` に欠損と上限による停止を記録。`validation.json` でsource契約3件、raw/text/snapshot SHA、literal引用4件と初期26ファイル不変を確認した。実DB登録・分類・status変更・IR質問登録・フォーム入力/送信は実行していない。
