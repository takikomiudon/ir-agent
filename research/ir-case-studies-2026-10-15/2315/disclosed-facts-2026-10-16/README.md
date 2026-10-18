# 2315 公表12表示値の構造化

root受入済み短信/注記から、既存 `normalize_disclosed_facts`（CLI `normalize-facts`と同じ処理）で12表示のみを保存しました。**営業黒字、会社独自の調整後EBITDA、経常赤字、親会社赤字を別concept/利益段階として保持**します。金融モデル・正常利益・独自予測・価格・IR質問へは採用していません。root独立レビュー待ちです。

| 対象 | 原表示 | 原単位 | 保存値 | kind |
|---|---:|---|---:|---|
| Q3累計売上 p13 | 4,693,842 | 千円 | 4693842000 JPY | reported_fact |
| Q3累計OP p13 | 111,568 | 千円 | 111568000 JPY | reported_fact |
| Q3累計経常損失 p13 | △12,167 | 千円 | -12167000 JPY | reported_fact |
| Q3累計親会社損失 p13 | △126,493 | 千円 | -126493000 JPY | reported_fact |
| 基本EPS p1 | △0.75 | 円 | -0.75 JPY-per-share | reported_fact |
| 会社定義調整後EBITDA p1 | 199 | 百万円 | 199000000 JPY | reported_fact |
| FY会社予想売上 p1 | 6,166 | 百万円 | 6166000000 JPY | issuer_guidance |
| FY会社予想OP p1 | 107 | 百万円 | 107000000 JPY | issuer_guidance |
| FY会社予想経常 p1 | 107 | 百万円 | 107000000 JPY | issuer_guidance |
| FY会社予想親NI p1 | 91 | 百万円 | 91000000 JPY | issuer_guidance |
| FY会社予想EPS p1 | 0.66 | 円 | 0.66 JPY-per-share | issuer_guidance |
| 中間DPS p1 | 0.00 | 円 | 0 JPY-per-share | reported_fact |

千円のQ3実績は表紙の切捨て百万円へ置換していません。Q3は2025-11-01〜2026-07-31、FY会社予想は2025-11-01〜2026-10-31。FYのOP107と経常107は別列・別token位置です。Q4必要利益・年率化・予想反転や確度を計算しません。

調整後EBITDAは専用 `issuer_defined_adjusted_ebitda` conceptで、会社定義のOP＋減価償却費＋のれん償却費と非GAAP/他社非同一性の留保へ参照します。公表199を単位換算しただけで、構成額から再計算せず、標準EBITDA・CFO/FCFF・正常利益にしません。税/NCI、段階取得差益207,825と減損207,719、特別損失合計などは原文の文脈参照だけで、相殺・OP足戻し・端数修復は0です。

9月14日の据置は12月19日2025年の旧予想への会社参照で、その旧原本を独立読了していません。注記の「Q3経常/親会社利益が前回予想を下回る推移、影響精査・必要時修正」の留保を保持します。現在株数やFY EPS0.66の分母/basisは未確認、逆算や矛盾断定はしません。

中間DPS0.00は当期第2四半期末のreported表示で支払実施の確認ではありません。原文字列0.00を保持し、normalizerの0表現と区別します。期末/年間予想は未定/ダッシュのためfactを作らず、DPSの正確な期間両端・record date・会計/連結scopeはnullを維持します。

[入力](normalization-input.json)・[4連続basis引用/12token位置](quotes.json)・[原source/旧59file参照](source-reference.json)を保存。長いp2/4/5/10/13/18文脈は7quoteのid/file SHA/span参照とし、各factへ本文を複製しません。p1/p13画像を再確認し、利益段階・列・原単位・期間・会社独自指標の意味は明示したreviewer assertionに留めます。元source全object不変＋派生1の2source bundleで、未freeze通知はpinしていません。

primary生成は1回、**2026-10-16T05:05:38.751754+00:00**。原取得時刻 **2026-10-16T04:50:11.745012+00:00**、公表日 **2026-09-14**（正確な時刻null）、抽出review時刻 **2026-10-16T05:05:20.245335+00:00**と区別します。生成/取得時刻を実DB初保存へ遡らせません。

[再現証跡](reproduction.json)はsame-now whole bundle/ID、標準reproducer、独立Decimal換算、Unicode/UTF8 basis/token/84context参照、受入済PL33行、旧59file不変を確認しています。参照walkerが旧listと注記dictの外形・page keyの差を見落とし2回停止したため、専有scriptだけ修正して3回目に全確認しました。[修正履歴](validation-correction.json)と失敗前2scriptを保存し、明示replay/標準reproducerは各3回、primaryは1回です。値・入力・生成bundleは変更していません。保存前のPL行/列metadataを原表どおりへ整えたことも[validation.json](validation.json)に記録します。

DB接続/書込、GET、共有コード/索引/旧file変更、金融採用・thesis・policy・IRdraft・送信・注文はいずれも0。file-onlyでfreezeしrootレビューを待ちます。
