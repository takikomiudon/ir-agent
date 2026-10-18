# 6323 ローツェ：正式短信の5公表事実

記録: 2026-10-15T16:01:06.123683+00:00。保存済み正式中間短信〔日本基準・連結〕から最大5件だけを既存APIで構造化した。原source object/ID・取得時刻・pubnullを保持し、実DB/Store/GETは使っていない。元資料の独立点検を再利用し、今回の意味確認はp1とp10の値/期/行列に限定した。原PDF全文再監査はしていない。

| 指標 | raw表示 | 正規化 | 種別 |
|---|---|---|---|
| p1中間基本EPS（2026-03-01〜08-31） | 91.33円 | 91.33 JPY-per-share | reported_fact |
| p1通期会社予想EPS（2026-03-01〜2027-02-28） | 217.84円 | 217.84 JPY-per-share | issuer_guidance |
| p10半導体関連装置 受注高 | 120,540百万円 | 120540000000 JPY | reported_fact |
| 同行 受注残高 | 103,863百万円 | 103863000000 JPY | reported_fact |
| 同行 受注高の前年同期比水準 | 256.4％ | 2.564 ratio | reported_fact |

受注表は物理p10/印字8で、初期依頼のp4ではなかった。正式品目は『半導体関連装置』。全体合計の255.5％ではなく同品目の受注高側256.4％を保持し、前年比水準を増減率へ変えず100を引く独自差分も作っていない。受注残高側229.8％と区別する。受注は販売価格基準、生産実績は製造原価基準であり、受注/残高を実現売上や利益へ代用しない。金額の百万円未満切捨てを保持し、JPY換算で未表示精度を増やしたとはしない。

中間EPSは左の基本列（潜在調整後と同じ表示でも別列）で、半年を年率化しない。通期EPSは会社の修正有の予想で、独立著者予想や実績ではない。p2の期末発行済・自己株・中間期中平均株を区別し、通期予想EPSの将来分母/希薄化/株式分割前提を実績株数から推定・再計算しない。

原sourceID `case-public:27f85d208c1d6ecc4faa1df0b5a9491cc70f577b1808c98b5b8dd630b5e33b4a`、派生ID `disclosed-facts:36b4e01e64949c8e6cc6a1cd76052a8b3929bb78defe9376715395366b492d03`。review `2026-10-15T16:01:06.123683+00:00` と実派生retrieval `2026-10-15T16:01:06.124209+00:00` を分離。親の実DB trusted first-save `2026-10-15T15:54:47.678750+00:00` は保存親receiptの参照であり、この作業でDBを確認/更新したものではない。原metadataの過去firstsave不明やpubnullは変更していない。

同じ引用内token/単位/期、global/頁offset、API全bundle replay/reproducer、独立Decimal換算が一致した。原文照合を意味/最新性/モデル適合まで検証済みとはせず、financial_inputs_verified:false・meaning_review_required:trueを保持する。入力/出力/引用は [normalization-input.json](normalization-input.json)、[normalized-bundle.json](normalized-bundle.json)、[source-quotes.json](source-quotes.json)、検証は [validation.json](validation.json)。

モデル・価格倍率・確率・IR条件/質問・売買・新索引entry・監視・コード/テスト・旧source/facts/index変更は0。金融評価の完成ではなく、原典に結びつく公表事実5件の入力整形である。新5filesを固定し、以降は別版/補足で訂正する。
