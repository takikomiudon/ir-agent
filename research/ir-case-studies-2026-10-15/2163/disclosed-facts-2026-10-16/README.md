# 2163 中間短信の直接表示10値

root受入済み原短信の物理1・2・4・6頁を根拠に、既存 `normalize_disclosed_facts`（CLI `normalize-facts` と同じ処理）で10表示だけを構造化しました。金融入力・予測・売買方針への採用ではありません。新GET、DB接続、旧資料・共有コード・索引変更は0、説明資料/FAQの未freeze成果は参照していません。root独立レビュー待ちです。

| 対象 | 原表示 | 原単位 | 保存値/単位 | kind |
|---|---:|---|---:|---|
| 中間売上高 p6 | 7,075,025 | 千円 | 7075025000 JPY | reported_fact |
| 中間営業利益 p6 | 1,217,085 | 千円 | 1217085000 JPY | reported_fact |
| 中間親会社株主利益 p6 | 815,269 | 千円 | 815269000 JPY | reported_fact |
| 中間基本EPS p1 | 38.43 | 円 | 38.43 JPY-per-share | reported_fact |
| FY会社予想売上高 p1 | 14,021 | 百万円 | 14021000000 JPY | issuer_guidance |
| FY会社予想営業利益 p1 | 2,017 | 百万円 | 2017000000 JPY | issuer_guidance |
| FY会社予想親会社株主利益 p1 | 1,248 | 百万円 | 1248000000 JPY | issuer_guidance |
| FY会社予想EPS p1 | 58.85 | 円 | 58.85 JPY-per-share | issuer_guidance |
| 当中間DPS p1・分割前 | 43.00 | 円 | 43.00 JPY-per-share | reported_fact |
| 期末予想DPS p1・分割後 | 21.50 | 円 | 21.50 JPY-per-share | issuer_guidance |

中間実績は2026-02-01〜07-31、通期会社予想は2026-02-01〜2027-01-31。千円のPL実績を表紙の切捨て百万円へ置換せず、二つの精度を混合していません。前年中間連結値・増減率は非表示であり、前年単体の代用やYoYを作りません。9月10日の据置観測と3月13日原予想を区別し、3月13日原本の独立読了やOctober現在予想の確認は主張しません。

EPSと株数は会社が8月1日の1→2分割を反映した表示です。二重調整やEPS/現在分母の逆算は0。DPSは当中間reportedと期末issuer forecastを別concept・別列・別share basisで保存しました。配当支払いの実施確認ではなく、年間ダッシュのfact・合算・分割調整後年額は作っていません。DPSの正確な年度/期間両端・record date・会計/連結scopeはnullを維持します。

入力は[normalization-input.json](normalization-input.json)、4つの連続basis引用と10tokenのUnicode/UTF8位置・固定画像SHAは[quotes.json](quotes.json)、原raw/text/source/旧32fileは[source-reference.json](source-reference.json)です。p2/4/6の長いcontextは原引用id/file SHA/spanへ参照し、各factへ全文を重複させません。これらの概念・列・期間・株basisは意味確認者の明示assertionで、自動金融認証ではありません。表示精度以下の実額は推定しません。

原HTTP取得時刻は **2026-10-16T04:32:46.857649+00:00**、公表日は **2026-09-10**（正確な公表時刻null）。抽出reviewは **2026-10-16T04:40:54.368932+00:00**、primary生成/派生retrieved_atは **2026-10-16T04:41:03.995793+00:00**。いずれも実DB初保存時刻の代用にはしません。

primary生成は[generate_once.py](generate_once.py)で1回。[reproduce.py](reproduce.py)で同じnowのwhole bundle/ID一致、既存reproducer、10値の独立Decimal単位換算、引用/原token/30context参照、旧32file不変を確認しました。再現呼出しと既存reproducer内部の再構築はprimary回数と別です。[generation.log](generation.log)・[reproduction.json](reproduction.json)・[validation.json](validation.json)に証跡を保存しています。

元source全object不変＋派生1sourceの2件bundleです。会社予想の再表現を新公表/独自予測や税/CF/正常利益の採用にしません。次はrootの独立意味レビューと受入判断です。この作業はfile-onlyでfreezeして停止します。
