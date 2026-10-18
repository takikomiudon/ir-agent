# 3inquiryの保存公表coverage（新GET0）

保存された公式一覧だけを照合。**135Aは一覧の最上位の短信・説明資料を既読。7388/7525は静的一覧から後発本文の有無を判定できない。** これは現Webの全最新性、後発公表なし、既存質問への公開回答不存在の認証ではない。

| 会社 | 現caseの原典期／保存coverage | 保存一覧の後発決算・Q&A literal／公表表示 | holds-v9／扱い |
|---|---|---|---|
| 135A | FY27Q2中間（2026-03-01〜08-31）の短信・説明資料は既読。一般FAQとFY27Q1の会社作成Q&Aも既読。[既存読解](../ir-case-studies-2026-10-15/135A/author-condition-followup/case-record-v2.json)を再利用。 | 10/15保存の公式2一覧の最大公表表示は **2026/10/14 16:15:00**、短信/説明資料とも取得済み。Q&A最大は **2026/07/14 16:00:00** のFY27Q1で取得済み。現Q2より後の個別決算/Q&A本文literalはこの2一覧では未確認。日時のtimezoneは未明示。 | 一覧www.xj-storage.jp・配信contents.xj-storage.jpは現在hold。既保存本文の有効性を否定せず、再取得0。現Q2の別Q&Aが存在しないとは認定しない。 |
| 7388 | 統合報告書2026のFY2025/11振り返り（料率低下p30）を基準。p27のFY2026/11計画見直しも既読。[既存追補](../ir-case-studies-2026-10-15/7388/quality-support-rate-saved-report-followup-2026-10-16/review.json)。 | 10/16保存の短信一覧と四半期Q&A入口はいずれも静的資料欄が空、dated PDF literal0。入口URLは下記。**後発期/公表日/最新本文は未確定**。未取得を公表なしに読み替えない。 | ir.fpp.jpは13holdに含まれないが、旧静的入口の有限停止を保持。JS/feed/providerや別入口を再探索せず、新しい日時付き本文候補を作らない。 |
| 7525 | 10/2のQUICK著者資料、会社GP2026の27/3期目標とLV2030の31/3期目標、転載29.3%/足元約30%が現比較。転載値の期表記・厳密測定期間は旧留保を保持。[既存読解](../ir-case-studies-2026-10-15/7525/author-original-product-review/case-record-v2.json)。 | 10/15保存の公式説明資料一覧に実決算/Q&Aのdated PDF literalなし。loaderはPDF URLを未取得data応答から得る構造で、実応答未取得。**後発決算/Q&Aの期・公表日・最新本文は未確定**。 | www.rix.co.jpは中央hold外だが旧空一覧の停止保持。loader接続先www.xj-storage.jpはholdでdata/PDF0のまま。旧JPX発表予定を公表実施/本文取得にしない。 |

## 実literalの根拠（取得候補を増やす指示ではない）

- **135A-S** `/text`の保存JSONP内 `/items/0/files/0/url`：<https://contents.xj-storage.jp/xcontents/AS06543/0e4abefd/2c7d/4512/9376/0761580b1ba5/140120260831528808.pdf>。取得済みは `135A/library-followup/03.json`。
- **135A-P** 同 `/items/0/files/0/url`：<https://contents.xj-storage.jp/xcontents/AS06543/add89fe1/7c75/426d/908b/a7cb51fa85bb/140120260831528813.pdf>。Q&Aは `/items/1/files/0/url`：<https://contents.xj-storage.jp/xcontents/AS06543/716abbe4/683a/4898/b4c1/de6c6a8fff61/140120260630584501.pdf>。それぞれ取得済み `135A/presentation-followup/03.json`・`04.json`。一覧にはさらに古い資料があるが今回再読しない。
- **7388-S** `/GETs/2/url`=<https://ir.fpp.jp/ir/results/>（完了10/16 10:32:23UTC）、**7388-Q** `/GETs/0/url`=<https://ir.fpp.jp/ir/quarterly_results/>（同12:16:40UTC）。実回答PDFのliteralではなく入口。静的結果の既受入reviewを再利用した。
- **7525-P** `/url`=<https://www.rix.co.jp/ir/lib/presentation_material/>（完了10/15 10:08:01UTC）。実資料PDFでなく入口。loader停止根拠は [既存結果](../ir-case-studies-2026-10-15/7525/issuer-loader-followup/README.md)。

保存一覧に後発の未取得決算本文があると新たに確定した会社は今回0。7388/7525はcoverage不明であり、最新財務内容が全て変化していないという結論ではない。既存3draft・期/分岐・native case・金融入力を変更していない。HTTP/検索/DB接続/キー参照/旧file変更は0。

固定根拠（whole SHA、6件だけ）：

- [135A-S](../../research/ir-case-studies-2026-10-15/135A/library-followup/02.json) `4fe4b9260d9360e22c70a684d6ccb23ebd01b9d55b4b219bbbfc6263746b135e`
- [135A-P](../../research/ir-case-studies-2026-10-15/135A/presentation-followup/01.json) `d278a28256705d953e2dce05687c68011a294588f3b4dd6afef3c15dd1f154e8`
- [7388-S](../../research/ir-case-studies-2026-10-15/7388/annual-accounting-input-discovery-2026-10-16/capture.json) `b0697d2045f98f23940396b62cfb0ff6a37e0c81bb4f95d15315babf6caa918d`
- [7388-Q](../../research/ir-case-studies-2026-10-15/7388/quarterly-QA-index-public-review-2026-10-16/capture.json) `36801919a1e63dc3c3ad47535c5245114adc9eb37d986414e4721ee3672bc440`
- [7525-P](../../research/ir-case-studies-2026-10-15/7525/issuer-presentation-followup/01.json) `7fdab6de1a0c60d634de58813f4ce54eee43eabb1cc99a43d6a55add18729bf2`
- [H9](../../research/ir-source-access-holds-2026-10-15/holds-v9.json) `4fb00a614863759398832cd1368b77535505cc885c4cd21433edafaccc22ec65`
