# 保存済み定性jobのworker viewサイズ監査

**既存viewだけで、同一CLI整形のJSONが2,129,989 bytesから609,035 bytesになった（差1,520,954 bytes）。** 新projectionやコード変更は不要。この結果は2315年次の保存完了job1件の実測で、会社数上限・token/料金・処理所要時間への推定ではない。

| 同じUTF8 JSON条件での比較 | full frozen packet | existing worker view | 差 |
| --- | ---: | ---: | ---: |
| CLI形式（indent2・非ASCII保持・末尾LF） | 2,129,989 | 609,035 | 1,520,954 |
| models.json_text（sort_keys・既定区切り・末尾LFなし） | 2,124,812 | 604,898 | 1,519,914 |

保存job-packet.jsonの全bytesはCLI形式の再シリアライズと一致した。actual-job.json.packetも同じJSON object。既存QualitativeResearch.worker_packetを、jobだけを返す保存JSON adapterで実際に呼び出した。adapter.connectionはNoneで、Store/SQLite/ネットワークには接続していない。scriptは1runごとにworker_packet/jobを各1回呼び、stdout replayでもreport.json全bytes一致を確認した。新unit testは作成/実行していない。

## 何が大きく、何を保つか

fullの主な寄与はcase_snapshot 1,645,626 bytes、sources 473,409 bytes、company 4,731 bytes（各field値をnative JSONにした長さ、相互に足す場合のkey/区切りはreportで別計上）。case_snapshotのfilesは931,142 bytes、reviewed_sourcesは713,238 bytesだった。

同じmanifest本文が、filesのbootstrap7件＋manifest_ref1件＋reviewed_sources各review_file7件に**15回**現れる。本文単体UTF8は95,007 bytes、JSON string表現は101,121 bytes。15回のstring payload計1,516,815 bytes、1copyを超える重複は1,415,694 bytes。viewではこの同一文字列の出現は0で、file参照とレビュー記録を残す。これは完全一致する長い文字列の測定であり、意味的/部分文字列の全重複や任意のdedupe方式の効果を推定したものではない。

viewでは**新source全文・全object 473,409 bytesを完全保持**し、元case文書のcontentとreferenceもfrozen_case_document 118,173 bytesとして完全保持する。全reference_files、reviewed_sourcesのreview_file以外の全fieldも一致した。旧資料本文を新着sourceとして追加したり、元case条件を現在の観測に置き換えたりはしない。全full packet自体は保存されたままでcanonical_packet_sha256が一致する。

## summary / case_observationの境界

このfrozen packetはlast_review_id:null、prior_review:nullで、worker viewもnullをそのまま保持する。prior_review_availability:frozenはfieldが元packetに存在するという実装上の表示であり、非nullの過去観測が入っている証明ではない。

保存済み完了jobにはresult.request.summary（native JSON 2,690 bytes）とcase_observation（3,290 bytes）が実在する。これらは今回完了後の結果であり、元full packetにもworker viewにもresultを後付けしていない。現在の完了結果の消失を意味せず、actual-job.jsonの結果に別途保持されている。_prior_reviewの既存実装は、次回起票時に正当に照合した前回結果からsummary/case_observationと日時/hashを取得する。worker_packetは凍結packet.prior_reviewを丸ごとdeepcopyするため、存在する過去summary/観測を意図的に落とすprojectionではない。ここでは次jobの起票や非null合成fixtureのtestは実施しておらず、このコード読取を別caseでの実測と混ぜない。

## 既存の利用手順

運用中workerは取得したjobの既存 `packet JOB_ID --view qualitative-worker` を読める。CLI分岐とdocsは入力pinに含めた。例示は次のとおりで、この監査ではactual CLI/Storeを実行していない。

```bash
.venv/bin/ir-agent --db PATH packet JOB_ID --view qualitative-worker
```

元packetは無指定のpacket又はfull viewで参照できる。worker viewは読取用で、保存job_status:completed、lease所有者/期限、current_completion_authorization:not_checkedを**現在の完了権限の証明にしない**。有効なclaim/世代/lease・head等の既存実行契約を別に満たす必要がある。projectionが現在caseや完了後資料を取得して凍結packetへ混ぜた、とも解釈しない。

## 再現と固定

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python research/ir-qualitative-worker-view-size-audit-2026-10-16/reproduce.py
```

既定はstdoutだけ。--outputは新規fileを排他的に作成し、既存reportを上書きしない。input-pins.jsonの8ファイルを前後で照合する。report.jsonにはfield寄与の加算式、15箇所のJSON pointers、source/原文保持・canonical hash・完了結果/過去観測の区別、adapter呼出範囲を保存した。原資料全体の意味・金融的正しさ・現在DB/leaseを再監査したものではない。

GET・actual Store初期化・DB接続/書込み・production/旧file変更・新API/feature/test/cohort・金融採用は0。新4filesを固定し、親レビュー待ちで停止する。

固定SHA-256: report.json `8db60ff2406b92ff2114ed18581c71d7415238d55d1081f42851b5bd14a6a64f`、reproduce.py `bb5342c28fd9b48726885fb3320fc434e9015b81bc2c217e4353e9e108f842b2`、input-pins.json `a6836c26e4160dc96d8155257c11ba184c6a16638a2f821aba296940b25ab781`。
