# 1904：Q1実績3・8月時点会社予想3の構造化

受入済み12頁全文sourceの全objectを再利用し、financial-observationsのp1表示token6つだけを既存normalizerで構造化した。原著者は大成温調、抽出review担当はCodex。金融採用・実DB登録は0、親レビュー待ちでfreezeする。

| 原会計項目 | Q1実績（百万円） | 通期会社予想（百万円） |
|---|---|---|
| 売上高 | 14,276 | 64,000 |
| 営業利益 | 553 | 3,700 |
| 親会社株主に帰属する純利益 | 364 | 5,300 |

実績3はreported_fact（2026-04-01〜06-30）、予想3はissuer_guidance（2026-04-01〜2027-03-31）。日本基準・連結、百万円未満切捨てを保持し、JPYへ明示換算しただけ。p7 P/Lの千円を混ぜたり、より細かな精度に置き換えたりしない。未表示精度を未丸めの正確経済額とはしない。

p1の原表画像とp4の予想据置説明を直接確認した。予想版は「2026-08-06時点で2026-05-13公表から変更なし」として、参照発表日と今回の観測日を分けた。5月13日原通知/当時保存は確認しておらず、10月時点の最新会社予想・達成確率も認定しない。p2の株式報酬信託・Q1連結範囲/四半期固有処理の注記は文脈として保持するが、仕組みを金融入力へ採用していない。

後日公表の分割・配当・子会社化等の基準は別sourceであり、今回6factに移植しない。EPS/DPS/shares、分割調整、annualization、差額合成、取得寄与、正常利益・税・CFは作成0。会社予想の親会社純利益と営業利益の関係も、推測した一時要因で説明しない。元の意味確認p1/2/4/7や全12頁保存を、全冊意味確認へ広げない。

原source IDは `case-public:cd0710232d105dbfbd9a4fff16df1b2d631daf2d95337c50e771fa7d486d2e29`。原raw/text/transport SHA、元source snapshotとroot受入receiptの一致をfileで照合し、ID/全文/metadata/公表・取得時刻を変更していない。原PDF取得完了は2026-10-16T01:51:18.361738+00:00、公表日は2026-08-06・時刻不明のpublished_at:null。root保存receiptのfirst-saveは2026-10-16T01:59:22.254207+00:00で、今回ライブDBへ再照会していない。

派生IDは `disclosed-facts:e7ca122ed5aaa0bfc91f7ff96d815b499b472fae77f3c9132d507def18454826`。派生retrieved_atの2026-10-16T02:16:24.212634+00:00はbundle生成時刻であり、原典取得・公表・実DB first-saveではない。新派生はまだ実DB保存していない。

quotes/locationに同一原全文substring、単位・期・表列、文字/UTF8 byte offsetと画像SHAを保持。normalizerとreproduce_disclosed_fact_sourceは原content matched・原snapshot matched_supplied_snapshotでreproduced、固定nowのbundle replayも完全一致。原典閉包は1source、companies/theses空、全financial_inputs_verified=false/meaning_review_required=true。generic byte verifierのmatchedや意味の独立認証とは呼ばない。

リポジトリルートで `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python research/ir-case-studies-2026-10-15/1904/disclosed-facts-2026-10-16/reproduce.py` を実行すると、DB/GETなしで同じ入力・bundle・原snapshotを再検証する。結果はreproduction.log/json、value path参照はaudit-source-pathsに保存した。value pathは金融モデル入力割当ではない。

旧37fileのSHA不変。新GET・DB接続・新case/質問・旧file/production/schema/共有文書/索引変更・金融採用・full suite再実行0。現在進行/完了した定性jobへこの派生を後付けせず、source登録と以後の研究はrootが別途判断する。
