# v2独立preflight：登録成功、queueは旧8sourceでcase全体保留

**v2は一時DBでcase version1・native既読1として登録できた。queueは0件で、旧8原sourceの初回保存未知によりcase全体が保留された。** 旧8件をnative既読にしたり、個別skipした残りだけを起票できたと報告しない。実DBへの登録・queueは実施していない。

入力`case-register-input-v2.json`のSHAは指定の`8ef08806ff63d32da00b496eb665cc7cf47987bdb60152bb4d953e41318b8b47`と一致。context/manifest-v2と全file参照を照合し、native bootstrapは追加3Q原source1件だけ、旧8件はv1の限定既読contextと`source_first_save_unknown`の理由を保持していることを確認した。著者手順・内部管理日2027-01-16・金融未採用・closed中国調査を再開しない境界も維持している。

## 一時登録とqueueの実結果

実DBを`mode=ro`・`PRAGMA query_only=ON`の一貫した読取transactionで開き、SQLite backupを一時pathへ作成した。snapshotはsources150、classifications149、completed jobs73、pending0。元source9件の現在snapshotと保存参照は完全一致した。実DBへStoreは使わず、一時copyでのみStore/Harness/QualitativeResearchを起動した。

- Store初期化の旧row差分0。
- `register_case(..., expected_version=0)`成功。新case行1・既読1、変更tableは`qualitative_case_versions`だけ。既存rowの削除/変更0。
- `queue_cases([case_id], as_of=current)`は`jobs_created:0`、`source_evidence_held`。queue前後のrow差分0。
- 旧8件はいずれも`source_first_save_unknown`で、case全体の保留要因になった。現在の実装は、この8件を個別に除外して他sourceだけを起票する挙動ではない。

個別の既存source検査では、native未読でmatchedの派生sourceは次の3件だった。これはqueue成功や意味レビュー完了を示す一覧ではない。

| 構造化資料 | source ID |
|---|---|
| 6月末の総資産・純資産・参考自己資本3値 | `disclosed-facts:f7efe93a490b1bf5051da04bce9259f17ab78ef8e4eeb0700f344d8dc5660d5d` |
| 既存EPS実績・EPS/DPS会社予想3値 | `disclosed-facts:350ff4b665b890148361dbb95305956570763182c3078f95d0665ac79a6c15fb` |
| 3月末の直接BPS1値 | `disclosed-facts:bef81e966c226b614fdd7cb359d26ae670d892cbf6fd97d934aee742f333ef50` |

今回作成した税6factの派生sourceは実DBに不在で、file-onlyであることも確認した。

## 保存した証拠と境界

実APIの結果は[api-preflight.log](api-preflight.log)、登録結果の最小投影は[registration-projection.json](registration-projection.json)、queue原返値は[queue-result.json](queue-result.json)、table差分・全source検査・参照SHAは[validation.json](validation.json)に保存した。再利用可能な本番worker packetは作成していない。claim/completeは不要として実行していない。

actual DB main SHAは指定の`32ca3efada89ec565715957806df02bef7a5462b2fa9a5c44419b42e6dafa3b9`と一致し、前後不変。実DB application書込み・Store・新GET・producer/共有file/コード変更は0。一時SQLiteは削除済み。最初のfailed preflightも全SHA不変で保持した。現契約の変更や旧8件の初回保存推定は行わず、ここで凍結する。
