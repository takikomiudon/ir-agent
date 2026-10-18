# 2410：非連結の公表12表示値（file-only）

受入済み原短信1source全objectを無改変で保持し、既存v1 normalizerで派生1sourceだけを作成した。7月31日公表の非連結Q3累計（2025-10-01〜2026-06-30）と当時FYguide（2025-10-01〜2026-09-30）を分離する。抽出時点ではFY終了済みだが、その後の実績/予想を確認したものではない。

| 種類 / concept | 原表示 | 原単位 | 保存値 / unit |
| --- | ---: | --- | --- |
| reported_fact / revenue | 14,243,525 | 千円 | 14243525000 JPY |
| reported_fact / reported_operating_income | 1,323,906 | 千円 | 1323906000 JPY |
| reported_fact / reported_ordinary_income_or_loss | 1,336,744 | 千円 | 1336744000 JPY |
| reported_fact / net_income | 915,373 | 千円 | 915373000 JPY |
| reported_fact / reported_quarter_earnings_per_share | 173.51 | 円 | 173.51 JPY-per-share |
| issuer_guidance / revenue | 20,000 | 百万円 | 20000000000 JPY |
| issuer_guidance / reported_operating_income | 1,890 | 百万円 | 1890000000 JPY |
| issuer_guidance / reported_ordinary_income_or_loss | 1,900 | 百万円 | 1900000000 JPY |
| issuer_guidance / net_income | 1,272 | 百万円 | 1272000000 JPY |
| issuer_guidance / issuer_forecast_earnings_per_share | 242.32 | 円 | 242.32 JPY-per-share |
| reported_fact / reported_interim_dividend_per_share | 0.00 | 円 | 0 JPY-per-share |
| issuer_guidance / annual_dividend_per_share | 160.00 | 円 | 160.00 JPY-per-share |

PL千円の実績と表紙百万円未満切捨て予想を区別し、日本基準・非連結を保持する。NI915,373千円とFYguide1,272百万円は非連結純利益で、親会社帰属NIではない。EPS173.51は基本欄で希薄化後dashを0にしない。単一小数tokenを既存円変換で処理し、新円・銭formatや新codeは使わない。

年間予想160.00は合計欄の当時予想で、同じ連続basisに**普通配当140円00銭＋特別配当20円00銭**の注記を保存した。scope/definitionにも保持し、普通160・永続配当・支払実施・年率CF・将来DPS列へ転用しない。この内訳は文脈で追加numericfactではない。中間0.00と年度予想を分け、DPSの正確period両端/recorddate/会計・連結basisはnullのまま。

受入済み初回/注記から11引用をpath/SHA/JSONpointer/UnicodeUTF8spanだけ参照する。報酬としての自己株25,042株処分、Q3CF非作成と償却、事業別ordinary対全社OP、前年同期比増益対当時計画未達を保持し、処分を消却/現在分母/現金収入へ変換しない。CF/正常税率/将来CF/分母逆算は0。新しいlisting noticeはこの12値作業のscope外で読解/pin/先取り0。元sourceの歴史未取得記述は変更していない。

原source公表日2026-07-31はday精度/published_at null、原取得2026-10-16T06:26:19.044914UTC、抽出review06:58:52.213791、生成06:59:06.823495を区別。originalのroot実保存とは別時刻で、今回派生は実DB未投入。

primary1回、same-now wholebundle/ID再現1回、標準reproducer1回はreproduced/matched_supplied。独立Decimal12件、token/basis UnicodeUTF8、132文脈参照、旧10pins不変を検証。入力作成前のNI行選択は最初に税前NI行を部分一致で拾いassert停止したため、行頭一致へ限定し出力前に訂正した。原数値/元sourceやprimary出力の訂正・再生成は0。

GET/DB接続/Store/API/商品code/旧facts索引/採用forecast/価格/金融採用/IR0。12点でfreezeしrootレビュー待ち。索引・実台帳はrootの別接続。
