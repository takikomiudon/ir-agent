# 5480：年間入力の限定追加確認

**正式な通期決算短信・比較年度の表は未取得。既存株主メッセージの当年度2数値だけを、正確な期・原文付きの抽出候補に整理した。** 新たに取得した成功2資料は配信設定で、財務本文に数えない。3 GET目のHTTP503で終了し、残り枠を障害調査や別host再試行へ使っていない。

## 最大4 GETの範囲と停止

初期8資料とは別のfollowupとして、保存済み公式HTML・E-IR configのliteral参照から進んだ。

| capture | 実リクエスト | 初回取得UTC | HTTP/内容 |
|---|---|---|---|
| 01 | [core/eir_common.js](https://ssl4.eir-parts.net/Custom/public/v5parts/5480/jp/20230517/core/eir_common.js) | 2026-10-15 05:00:44.109034 | 200 / ローダーのみ |
| 02 | [app/conf/common_conf.js](https://ssl4.eir-parts.net/Custom/public/v5parts/5480/jp/20230517/app/conf/common_conf.js) | 05:01:07.275789 | 200 / 配信設定のみ |
| 03 | [announcement_0.js](https://v4.eir-parts.net/V4Public/eir/5480/ja/announcement/announcement_0.js) | 05:02:03.470246 | 503 / 91bytesの失敗本文、公開財務資料ではない |

01の経路は元の公式HTMLの `scriptLoader.setSrc(eirPassCore + 'eir_common.js')` と保存済みconfigのdomain/company/language/version、02は01内の明示 `conf/common_conf.js` に基づく。JSはデータとして保存・読取しただけで実行していない。動的なcache-busting queryは付けず、その選択を `request-derivation.json` に記録した。

02が明記したfeedは `http://v4.eir-parts.net/V4Public/eir/5480/ja/announcement/announcement_0.js`。取得器のtransport選択として、親の明示許可のもと**同じhost/path/queryを保ったHTTP→HTTPSのschemeだけの変更**を03に用いた。サイトの `_e.toSslPath` 実装は未取得で、その動作を再現・確認したとは主張しない。hostをssl4等に置換していない。この選択理由・元URL・実URLは03 snapshotとmanifestにも保存した。

全3 URL各1回、redirect/retry0。01/02/03のraw/text/snapshot/初回取得/SHAは保存した。03の503を受け、追加GET・新helper/endpoint探索・接続診断を行わず区切った。`source-bundle.json` は既存 `jp:5480` の成功設定2 sourceのみで `companies=[]` / `theses=[]`。503本文を発行体の開示sourceにしない。公開財務索引すら取得できていないため、最新の正式通期短信のタイトル・日付・日本基準/IFRS・比較列・最新性はnullのまま。

## 保存済み資料から渡せる候補

元source `case-public:7ebd4f421bb0d918ddc742534804347eb60927dfe2b6c6371b56af46358fcf00`（[株主メッセージ](https://www.nyk.co.jp/investors/message.html)、初回取得2026-10-15 02:46:12.089948 UTC、表示2026年6月）の本文だけを再読した。source ID・本文・取得日時・原バイトは不変。新規に取得した正式決算短信の代替や、10月時点の再確認済み業績とはしない。

| 指標の原ラベル | 原token/単位 | 対象・範囲 | 状態 |
|---|---|---|---|
| 連結売上高 | `150,866` 百万円 | 第144期、2025-04-01〜2026-03-31、連結 | 会社メッセージが説明する通期実績。候補のみ。 |
| 連結営業利益 | `10,973` 百万円 | 同上 | 同上。経常利益や税引前純利益、NOPAT、正常化利益に置換しない。 |

`sources.json` の `existing-message-period-and-annual-results` は、正式対象日付の本文からこれら数値・単位・「当連結会計年度」までを含む逐語引用とoffsetを保持する。このメッセージ内で10,973百万円の年度対応は確認できるが、正式短信との独立した同一期照合は未達。

`candidate-raw-tokens.json` は別担当への2候補の引継ぎ用。各token・期・単位・scope・実績区分・非空location・原source ID/初回取得・同じ引用内の期間と値を保持した。normalizerは実行せず、投資モデルへ採用していない。会計基準は未確認のためnullである。

本文にある「前年度比21,231百万円減」「前年度比5,994百万円減」は**変化額**として別項目に記録した。前年度の売上・営業利益の実額ではなく、差額から逆算しない。正式な比較期の開始/終了日・表列も未確認のまま。

## 解決と残る不足

保存済みメッセージの当年度数値がどの期に属するかは公開本文で分かるため、同じ問いをIRへ送る必要はない。一方、最新正式短信・明示の比較年度表・会計基準・連結範囲の継続性・営業利益の評価モデル上の意味は、正式資料での確認が残る。公開資料で解決不能と判定したわけではない。

得られた1年の要約と前年比変化だけでは全サイクルを確認できない。Damodaran原典に沿う利益率・再投資・現在規模・資金条件の正常化には、比較可能な履歴と一巡の根拠が別に必要である。固定年数・税率・ROC・将来予測・評価値・確率・投資閾値を補完していない。質問登録・IR送信・モデル評価は0件。

`validation.json` はraw/text3件、成功snapshot/source契約2件、既存本文引用1件と新規literal引用2件、原token位置2件、元31ファイル不変を確認する範囲。実DBへアクセス/更新せず、会社status/保有も変更していない。原文一致と形式検証を、金融入力の妥当性や全サイクルの確認済みへ読み替えない。
