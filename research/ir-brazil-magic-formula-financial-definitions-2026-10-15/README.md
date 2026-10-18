# Brazil財務定義：入力列は分かったがROIC構成式は未取得

固定commit `ac05a3bd3e146aa924b2b5e11ebffa3484c2c81d` の `2_magic_financials.ipynb` 1blobだけを新予算1GETで取得した。HTTP200・完全158,630bytes、復号114,926bytes、Git blob SHA1 `98d7b92a2839aad0265b2a4402d68a2b0557e8f7` 一致。旧4GET/3GET phaseは不変、robots/tree/commit再取得・他data/別source・実行/import/install0。

このnotebookは既処理featherを読んで選別するもので、ROICを会計原票から作る処理ではない。セル番号は0始まり、native cell IDなし。

| 対象 | 選択fileで実際にする処理 | 未確認のままの意味 | セル |
|---|---|---|---|
| 税率 | 定数0.34を宣言、後続参照なし | NOPAT/ROICへ適用した税率ではない | 1 |
| EBIT/ROIC | 入力列を正値で選び出力する | 税引前営業利益との対応、NOPAT/ROICの計算式 | 2/13/14 |
| 投下資本 | 欠損行の表示診断、正値選別 | 構成、期首期末平均、期末値との区別 | 12/13 |
| 現金/総自己資本 | 入力各列の正値を要求 | 現金内訳/余剰性、持分範囲、投下資本への組替 | 13 |
| 純負債 | 入力列を出力へ保持 | 負債/現金の差引式、負・0・欠損の直接filter | 13/14 |
| 株数 | 入力列の正値を要求し出力 | 期末/平均/自己株/diluted/分割/尺度 | 13/14 |
| 単位 | 入力コメントは金額百万BRL | 全fieldの尺度、株数、後段価格との整合 | 2 |
| 期間/範囲 | DFP・CON・per_ref=0で選ぶ | 実12カ月、原票/監査/公表日との対応 | 7 |

最終filterは売上・ROIC・投下資本・EBIT・総現金・総自己資本・株数の7列すべて厳密な正値（cell13）。0と負値は通さず、欠損を0へ埋める処理はない。投下資本欠損のcell12は表示診断だけ。数値NaNは通常の正値比較では条件を満たさないが、元dtype/nullable挙動や全列の有限性検査を実行検証したとはしない。純負債はこの7列に含まれない。

前phaseの作者summaryは負NetDebt除外と説明する一方、この選択fileに純負債の直接filterは見当たらない。この記述差を保持し、upstreamにfilterがないとも、net cash企業を全て除くとも補完しない。Damodaran参照も、作者が既処理ROICにその定義を適用したという説明と、実際の分子/分母/税/平均の検証を分ける。0.34の未使用宣言から正常税率・NOPATを作らない。

出力は先頭5列と株数/純負債/EBIT/ROICで、先頭5列は元schemaの順序依存。会社CVMコードPSVやローカルfeather、指標作成工程、会計原典は未取得である。必要なinput列と正値制約を把握したことは、企業会計との対応や日本株適合・モデル採用を確認したことではない。

[review.json](review.json)にfieldごとの処理/不足、[evidence-map.json](evidence-map.json)にセルJSONpath・source/Git/セルsource SHAを保持した。保存出力/実行カウントは作者artifactのみで実行証拠にしない。生成原典引用0語、既phase込み64語を維持。license未確認で移植0、金融値/方針/thesis/DB/共有fileの変更0。この1GETで有限終了し、別file/dataへ広げない。
