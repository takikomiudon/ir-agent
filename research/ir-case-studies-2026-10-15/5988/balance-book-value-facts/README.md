# 5988：2026年6月末の会計上の財政状態3値

保存済み公式短信の当期期末表示から、総資産・純資産・参考自己資本の**3factだけ**を既存normalizerで構造化した。既存5988の正規化3factはEPS実績・通期EPS予想・年間DPS予想であり、今回の値の重複はなかった。EPS/DPSは再抽出していない。

| 原文の概念 | 当期原token・単位 | 表示単位換算後 | 原典位置 |
|---|---|---|---|
| 総資産 | 100,182 百万円 | 100,182,000,000 JPY | 物理p1「連結財政状態」、当第1四半期行・総資産列。物理p5/印刷p3の資産合計・当期列でも照合。 |
| 純資産 | 65,372 百万円 | 65,372,000,000 JPY | 同p1の純資産列。物理p6/印刷p4の純資産合計・当期列でも照合。 |
| （参考）自己資本 | 64,077 百万円 | 64,077,000,000 JPY | p1の参考自己資本行、2027年3月期第1四半期の表示。 |

時点は**2026-06-30**、日本基準・連結の実績stockであり、3カ月flowや将来予想ではない。p5–6の当第1四半期連結会計期間の列に期末日を直接表示している。金額は原文の百万円未満切捨て表示で、換算後の数値が未丸めの社内残高と一致すると主張しない。

純資産と参考自己資本は別概念として保持した。連結BSには非支配株主持分が別行にあるが、差額から同持分を計算していない。参考自己資本を株主資本合計や直接確認していない親会社持分の定義へ置換しない。簿価を清算価値・本源価値へ昇格させない。

**確認したp1財政状態とp5–6対象BS表には、直接の一株純資産/BPS列・行が見当たらない。** 会社全体の非開示や他の全保存資料での不在を意味しない。純資産・自己資本・株数から逆算せず、BPS factや欠損0は作成していない。

## 原典と来歴

公式URLは `https://www.piolax.co.jp/jp/wp-content/uploads/2026/08/20260805_2026-q1_tanshin.pdf`。原sourceは `case-public:9e8b6afc70e3e312c989be58aa52f253e9d49b2699a3d7662eb2e0add624ef12`。既存 `disclosed-facts-normalized.json` のprimary snapshotをそのまま使い、既存raw/text/metadataを変更していない。

- 原PDF：`../raw/9960235822c9f224e178472064f39186645ca411b754621bd9ed6fdd91a0f9ff`、SHAはファイル名と一致。
- 既存抽出：`../07.txt`、SHA `3b1258cc4e95b63a6a355a8e96091887651f2d42e175492f328ff1564aa7749c`。primary contentと改行を含め一致。
- 原sourceの保存済み取得時刻は2026-10-15T01:11:44.134787+00:00のまま保持。今回、その時刻をHTTP本文完了や実DB初回保存へ再解釈しない。
- 文書日付は2026-08-05、公表時刻は不明で`published_at:null`を維持。派生sourceの取得時刻は今回の処理時刻で、原典取得時刻へ遡及しない。

## 成果物と有限検証

[normalization-input.json](normalization-input.json)と[normalized-bundle.json](normalized-bundle.json)に3factを保存した。`period_kind:instant`、`as_of_date:2026-06-30`とし、株数・BPS・PBR・将来BPS・倍率・割安条件は追加していない。原典は1sourceだけで、派生sourceの依存先もその1sourceに閉じる。会社・thesis配列は空、全factの`financial_inputs_verified:false`と`meaning_review_required:true`を維持した。

必要最小の財政状態ヘッダ/当期行と参考行を[quotes.json](quotes.json)へ保存し、元本文SHA・文字/UTF8 byte offset・物理頁・画像SHAを付けた。`images/`のp1・p5・p6を視認し、表行列・単位・当期期末を照合した。BSの他の残高は新factにしていない。

メモリ内で既存source schema、正規化結果の3値、原source同値、全文/quote offset、既存再現APIの`reproduced`を確認した。これは引用/表示単位算術の再現であり、会計的意味や投資への採用をengineが認証したものではない。詳細は[validation.json](validation.json)。既存5988ファイル64件の前後SHA一致を確認し、元derived・indexは変更していない。

新GET・実DB操作・src/tests/機能追加・モデル/方針採用は0。旧codeの全件テストは再実行していない。root受入後のDB登録・索引更新は別判断であり、このbundle出力は実施を意味しない。
