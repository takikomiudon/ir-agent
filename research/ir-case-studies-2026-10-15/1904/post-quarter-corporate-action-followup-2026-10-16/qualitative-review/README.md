# 1904分割・取得通知の定性比較結果（file-only）

job `qualitative-848384970b063c94e7a6ce2a`／worker `codex-1904-corporate-action-qualitative`／generation1、保存claimのleaseは2026-10-16T02:26:40.945950UTC。固定packet `qualitative_review/author_condition_review`、case v1/config1、prior_review:null。初回bootstrap後に直前jobがない状態であり、過去観測を作っていない。claimのactiveは保存当時の表示で、現在権限はrootが確認してcompleteする。本担当のDB/API/GET/claim/renew/completeは0。

原2頁の分割通知と1頁の取得通知の3画像・全文、7逐語引用と元case3条件、root受入を比較した。2sourceとも **supports** は「該当する公開定義が確認された」の意味。case全体は **unresolved**：下表の未確認が残り、投資の好悪は判定しない。

| 対象 | 解消した公表内容 | 保持した不足/境界 |
|---|---|---|
| 分割/配当/優待 | 1→4の日程、99円中間pre/24.75円期末post、年間dash・単純合計不可、会社の分割前参考198円、優待新基準2027-03-31 | 公表/基準/効力日と独立実施確認は別。古いQ1の信託分母/EPSを現在へ移さず、独自DPS合計・利回り・新EPSを作らない |
| 全株取得 | 取締役会9/10と取得完了9/30、事業/目的と会社の軽微見込み | 資本金1,000万円≠対価。連結取込・寄与・対価/取得会計/CFは未確認。軽微≠0、目的≠実現済みシナジー |
| 元case全体 | 後日の公開本文で解けた事項を既知へ移す | Q1/annual、OP/NI、百万円/千円、現時点の株式/範囲・正常利益CF等の不足を残す |

resultは既存5項目だけ、pending全2source各1回、snapshot SHAとsource.content内の逐語quoteを使用。取得通知のbasisは`acquisition-completion-and-disclosure-scope` [464,620)、分割は`dividends-mixed-share-bases-no-annual-sum` [2327,3225)（Unicode半開区間、改行保持）。全7引用も照合し、表の前後分母は画像で確認した。September公表日とOctober取得/新保存を混同しない。

recorded_at **2026-10-16T02:14:27.960365+00:00** ≥ packet.as_of **2026-10-16T02:11:40.932699+00:00**。管理日2027-01-16 Asia/Tokyoは記録時の現地日付より先、due_occurrence:nullでretain。会社予定/売却期限ではない。金融入力/数値thesis/投資action/新質問/新閾値0。元原本/条件/共有file不変。

固定packet native SHA `b83954e0fe769b0aa4c865062738e0573b785db0288ac024aca0b2f9dcb56fca`。結果file SHA **`1aea6e0693060cce2f3edc925797ebb1f5e1ff807939217e51863f9bbc83f5d5`**。原入力SHAは以下（原典は元作者大成温調、今回比較・結果作成はCodex）。

```json
{
  "research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/qualitative-review/packet.json": "2430fdc08166ecea38877d8aa3f5b4318cecd20c90f772e71b7a14567d932878",
  "research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/qualitative-review/claim-envelope.json": "417b53a51e2738a01a4d5e71a3eaaad23c9a2b51618f0b0c68d3017a597b5fc3",
  "research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/qualitative-review/assignment.json": "55b3118daa89473796f93c44a516cae65f3977400494bebec99ef1bc892f2c2e",
  "research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/source-bundle.json": "22abeef446081df6fa541badcfdef897dfb7aab901aa99f0fb974621e882b6c5",
  "research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/source-quotes.json": "97dd1f18e09ef9e1de2c6e461894011ce05d137a01ecad07f158915fafe81779",
  "research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/parent-acceptance.json": "a3187fd0b97583cf0705265350ed78f67edecf4d43b1b684e6ee20d7942ebb72",
  "research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/README.md": "090d01f9f239251feb2f8ecc7d8a8ca6d812a6a26366e1d87eb0131cae3e9f3a",
  "research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/review.json": "3b4ae7af915b7eda2e385011b0718bcae33e274736e03cf2ecc086f2fbb435be",
  "research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/images/01-page01.png": "436ddc2c4f2c6255786ec4479c8a6d772a4c200211419426ef8eab142c0e137a",
  "research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/images/01-page02.png": "73b90d9de0b2a9c4a4d96144b367321c7d98393f77f22f10ecfdd933b2fce401",
  "research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/images/02-page01.png": "aae453ac08c65604d02f0d24d3f1ce96dc8384d3e1e70f6b88fd069d3b7e0729",
  "research/ir-case-studies-2026-10-15/1904/native-case-setup-2026-10-16/case-context.json": "48c6b4edc78e884e14b6244f3edb4f84cdab53b4711bd280b4798abacbed1f6e",
  "research/ir-case-studies-2026-10-15/1904/native-case-setup-2026-10-16/management-basis.json": "45769b778d5633b770326c2387671105c616d672a3e870a436a748391c1f40b5"
}
```

上記は意味比較の引渡しであり、native完了や現在leaseの認証・金融モデル適合を主張しない。rootの独立確認後に実completeする。
