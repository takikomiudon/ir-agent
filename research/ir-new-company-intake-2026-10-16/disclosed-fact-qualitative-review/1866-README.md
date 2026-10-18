# 1866 定性job結果（file-only）

凍結job `qualitative-4aebb7a6be9fe37e528d9584`、worker `codex-new-company-facts-qualitative-1`、generation1。packet kind/stageはqualitative_review/author_condition_review。元case v1の3論点を読み、prior_reviewなし、pending派生1source/6factを一度ずつ扱った。論点の比較方針は元caseがAnthropic earnings-preview/thesis-trackerから適応した研究手順であり、著者の会社別売買ruleではない。

source/case outcomeはunchanged。既知のQ1実績/年次会社予想を再構造化した資料で、新しい会社開示ではない。Q1と通期、親会社NIと営業利益、8月6日観測と5月12日予想参照、分割EPS/会社総額の区分を維持した。詳細segment・受注/原価/CF等の未解決範囲を増減させない。内部管理日2027-01-16（Asia/Tokyo）は未到来、due_occurrence=nullにつきretain。売却期限/会社予定とは扱わない。

検査はfile-only。結果は5field、pending1件のID/全snapshot SHA一致、case issue一致、evidenceはpending内だけ。basis_quoteは保存されたminified source.contentの直接substring（文字offset 3250:3354、0-based/end-exclusive）で、JSON表示の整形から転記していない。結果recorded_atはpacket.as_of以後・保存claimのlease期限より前。ただし現在leaseを再確認するDBアクセスやrenewはしておらず、親がcounterreview/complete時に確認する。

- packet file SHA: `a57ab558f3aa9f6029d59dbf704dcc32c6b3d7b6e03b7958daab1b3838800bc3`
- native packet SHA: `ef49122c38d10ca3bc4e3568847d326d75d077bb7176e399eccff9c03b8ce028`（claim envelopeと一致）
- pending source snapshot SHA: `ddcd33dad3466dd8c9ca2de85e09b505a83e8aa31edd356c853560e1ddc22e6e`
- result SHA: `a016c47afd35df350d07e489e112cd760e52d1a72b2980056694ed1780657694`

元のclaim/packet/case/sourceは変更0。Store/DB接続・claim/renew/complete・GET・金融採用・数値thesis・将来利益・独自閾値・IR質問・共有文書変更0。親counterreview待ちでfreezeする。
