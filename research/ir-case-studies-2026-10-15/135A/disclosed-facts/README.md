# 135A VRAIN Solution：中間短信の5公表値

保存済み中間短信の表を原PDF画像と抽出本文で確認し、既存`normalize_disclosed_facts`契約で5項目を構造化した。**全て非連結・日本基準**であり、連結指標へ読み替えていない。実績と会社予想を区別し、会計意味・将来予測への適合・正常化・モデル採用は未検証のまま。新GET、実DBの読書き、既存source・他社の記録・共通索引の変更は行っていない。

## 5項目と期間

| fact ID（先頭`vrain135a-`） | 指標 | raw値・単位 | 正規化値 | 区分・表位置 |
| --- | --- | --- | --- | --- |
| `2027interim-basic-eps` | 基本EPS・1株当たり中間純利益 | `26.06` 円 | `26.06` JPY-per-share | `reported_fact`。当期中間行、潜在株式調整前の列 |
| `2027fy-company-eps` | 通期会社予想EPS | `94.85` 円 | `94.85` JPY-per-share | `issuer_guidance`。通期行、1株当たり当期純利益列 |
| `2027interim-operating-income` | 中間営業利益 | `409` 百万円 | `409000000` JPY | `reported_fact`。当期中間行、営業利益列 |
| `2027fy-company-operating-income` | 通期会社予想営業利益 | `1,449` 百万円 | `1449000000` JPY | `issuer_guidance`。通期行、営業利益列 |
| `2027fy-company-annual-dividend` | 年間配当会社予想 | `0.00` 円 | `0` JPY-per-share | `issuer_guidance`。2027年2月期(予想)行、年間配当金の合計列 |

- **中間実績**：2026-03-01〜2026-08-31、2027年2月期の中間累計。単独の第2四半期ではなく、年率換算もしていない。
- **通期会社予想・年間配当予想**：2026-03-01〜2027-02-28の2027年2月期。短信表紙の2026-10-14時点の公表内容で、達成実績や独自シナリオではない。

原典は[2027年2月期 第2四半期（中間期）決算短信〔日本基準〕（非連結）](https://contents.xj-storage.jp/xcontents/AS06543/0e4abefd/2c7d/4512/9376/0761580b1ba5/140120260831528808.pdf)。5値ともPDF物理1頁にある。保存された決算短信カテゴリー索引11件の中で最新と確認した資料であり、全カテゴリーの更新を網羅したという意味ではない。公表日だけが確認され、正確な公表時刻は不明。索引の時刻へタイムゾーンを補っていない。

## 行・列で分けたもの

- 当中間期の基本EPSは26.06円、隣の潜在株式調整後EPSは25.94円。前年中間期の6.04円・6.00円とも別である。基本EPSだけを今回のfactとし、将来の株数・潜在株式を補っていない。
- 当中間期の営業利益と経常利益はともに409百万円、通期会社予想の両指標も1,449百万円だが別列である。値が一致していても指標を同一視せず、営業利益の列を指定した。増減率328.1%・58.5%も金額ではない。
- 年間配当予想0.00円は当年度**予想行の合計列に存在する数字**。前年実績0.00、中間実績0.00、期末予想0.00、各四半期のダッシュ・空欄とは区別した。`raw_numeric_token_verified:true`、`numeric_token_normalized`で、欠損をゼロへ置換したものではない。
- 金額は百万円未満切捨て表示。JPYへの明示単位変換は、基礎となる実額を1円精度で確認したことを意味しない。

各factは、期・単位ラベルが同じ引用に入る保存原文を持つ。[normalization-request.json](normalization-request.json)にPDF頁、頁内Unicode文字位置、行・列ラベルを保持した。配当の通期対象期間は同じ頁の業績予想見出しとも対応付けた抽出担当の意味主張であり、自動確認済みとはしない。

原PDF1頁を`pdftoppm`で画像化して表列を目視確認した。一時画像は`/tmp/vrain-135a-statement-p1.png`、そのSHAと原PDF SHA、確認者・方法を[meaning-review.json](meaning-review.json)へ残した。画像がなくなっても元PDFを同じ頁指定で再表示できる。

## 原source・実時計・再現

原source snapshotを`library-followup/source-bundle.json`と完全同一で保持した。

- original source ID：`case-public:4b9aaae627aa90731140aa648b9c8bf60be1767accaab06041ac23dc5f6955fb`
- 原PDF SHA：`6c7d2b098b4ac5f8ed797ff552b8be239237a54e72824cb60ab25df9d49f9515`
- 元の初回取得：`2026-10-15T04:42:37.094960+00:00`
- reviewの実記録時刻：`2026-10-15T04:51:43.827086+00:00`。既存契約の`review.recorded_at`で保持し、検証記録にも`reviewed_at`として記録した。
- derived source ID：`disclosed-facts:3a6c2eaebf52cba09b060669bfb00dea510dc16d5be6fb370045e9b2e8171911`

派生取得時刻は今回の実行時計を使い、元の取得時刻や表紙日付へbackdateしていない。[normalized-bundle.json](normalized-bundle.json)は原資料と派生資料の2source、companies/thesesは空。元本文・snapshotのSHAと`original_source_id`を保持する。実DBには取り込んでいない。

[verification.json](verification.json)は、library-followupのraw/text/snapshot SHA各3件、source ID再計算3件、PDFの`pdftotext -layout`再抽出とJS/JSONPのバイトからのUTF-8復元3件、5factの頁・引用位置、6意味レビュー引用を確認した。JS/JSONPは保存データとしてのみ扱い実行していない。`reproduce_disclosed_fact_source`は`reproduced`となり、元snapshot一致・派生内容/IDを再現した。元ファイルは不変。

## 残る不明点とモデルへの境界

- 基本/希薄化後EPSと期中平均株式数の意味、将来EPS予想の分母、将来の希薄化は独立確認していない。期末発行済数へ置き換えたり利益から任意の株数を推計していない。
- 会社はPDF5頁で4月14日公表の通期予想から変更なしと説明する。その会社説明を引用したが、4月のPDFを取得・比較したわけではない。予想の達成を確認していない。
- 配当1期の明示0は、長期DPS列や将来の無配継続、配当可能利益0、DDM価値0を与えない。資本コスト・安定成長率・終価配当・買戻しも補完しない。
- 中間期の利益を恒常利益や全サイクル正常値として採用しない。再投資、運転資本、CFの将来化、企業規模変化、会計調整を点検する必要がある。今回CFは構造化していない。
- 説明資料・公開Q&Aや次の決算予定の確認は、この抽出の対象外。株価、評価倍率、確率、価格目標、売買条件は作っていない。

全factで`financial_inputs_verified:false`、`meaning_review_required:true`、全体で`model_adopted:false`を維持した。引用・単位算術・再現成功と、会計意味や投資上の採用判断を区別している。

再検証は次のオフライン処理だけで行う。

```bash
.venv/bin/python research/ir-case-studies-2026-10-15/135A/disclosed-facts/build_and_verify.py
```

保存済み派生取得時刻を明示して成果物を再現し、現在時刻での再計算でもID・本文・metadataが同じことを点検する。これは過去に新しい取得を行ったという主張ではない。取得スクリプト・DB・既存の他社成果物は操作しない。
