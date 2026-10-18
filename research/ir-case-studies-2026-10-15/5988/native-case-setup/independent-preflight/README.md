# 独立preflight：旧8原sourceの初回保存未知で登録拒否

**登録候補の9原sourceとfile根拠の照合は通ったが、現在のbootstrap契約により一時DBへの登録は拒否された。** 成功したnativecase追加・既読9・queueとは報告しない。producer候補・コード・実DBは変更せず、この失敗結果を凍結する。

実DBは`data/ir-research-2026-10-15.sqlite3`をSQLite `mode=ro`・`PRAGMA query_only=ON`の一貫した読取transactionで開き、snapshot照合とSQLite backupだけを行った。Store/Harnessは削除される一時backupにだけ作成し、実DBへStoreを使っていない。

## 通った確認

- 原source9件は実DBの現在snapshotと保存bundleのsnapshotが完全一致し、native `models.json_text` SHAと実DB保存dataのSHAも一致した。bootstrapのID/SHAとreview_ref、既読範囲を照合した。
- 候補case/context/manifest/managementと既存根拠fileのSHA、過去レビューの同source引用34件について原文一致と明示頁内一致を確認した。HTML4件は導線・カレンダー等の限定既読であり、全文の財務意味を認証しない。
- Anthropicの四半期点検原文・SHAを確認した。内部管理日2027-01-16はTokyo現地研究日2026-10-16から3暦月という明示的な研究管理上の適応であり、会社予定・反証期限・売却日ではない。
- 正常利益・DCF適格性・将来税/NOL・CF・数値方針の採用なし、closedの中国集計/現金調査等を新資料なしで再開しない境界を確認した。

## APIが拒否した理由

一時Storeのschema初期化前後に旧rowの変化は0。`QualitativeResearch.register_case(..., expected_version=0, research_root=repo)`は次のValueErrorを返した。

`Bootstrap source was not usable at the declared review time`

[source-usability-diagnostic.json](source-usability-diagnostic.json)で、旧初回bundle由来8件はhistorical usabilityとcurrent useがいずれも`matched`であり、snapshot/分類の不一致はなかった。しかし正確な初回保存が未知のため、既存`_source`検査が`source_first_save_unknown`を追加して全体をunknownにする。追加3Qの原source1件だけは`first_save_known:true`でmatchedだった。現在知っていることとexact初回保存を混同せず、receiptや時刻を補って通していない。

登録拒否後の全table row fingerprint差分は空で、nativecase追加0・native既読0・旧row不変を確認した。登録が成立しないためqueue/claim/completeは実行しなかった。

照合した読取snapshotでは5988のsourceは10件で、候補9原source以外は既存BS派生の`disclosed-facts:f7efe93a490b1bf5051da04bce9259f17ab78ef8e4eeb0700f344d8dc5660d5d`だけだった。これは集合差の確認に限り、queue成功やpending適格の認定ではない。root後段のsource追加・分類で集合は変わり得るため、本結果を本番packetへ転用しない。

詳細は[independent-validation.json](independent-validation.json)、実API失敗とrollbackの記録は[register-attempt.log](register-attempt.log)。一時SQLiteは削除済み。実DB application書込み・実DB Store・新GET・共有/producer file/コード変更は0、full suiteは実行していない。
