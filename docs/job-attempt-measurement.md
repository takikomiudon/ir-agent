# ジョブ試行の計測を既存レポートへ接続する

**世代fencing・最小lease台帳・read-only投影・要求receiptは実装済み。active/usageは設計案。** 将来の実ジョブについて、claimから更新・完了・期限切れまでの履歴を不変に保存し、[既存のcapacity集計](capacity-measurement.md)へ渡す契約を提案する。当初は文書だけの設計として保存し、その後に最小実装を接続した。スケジューラ起動は行っていない。

最初に測れるのは**リースを確保していた経過時間**である。分析に集中した実作業時間、モデルの利用量、問い合わせ待ち、会社全体の調査完了時間とは区別する。現時点の実測や架空デモから「毎日何社まで」といった会社数の上限、worker数に比例する能力、予算値を作らない。

## 標準の根拠とプロジェクトの設計

OpenTelemetry公式の[Trace API](https://opentelemetry.io/docs/specs/otel/trace/api/)と[Common](https://opentelemetry.io/docs/specs/otel/common/)を各1 GETで保存した。2 URLともHTTP200で、再試行・redirect追従・追加検索はない。[保存証拠](../research/job-attempt-measurement-2026-10-15/sources.json)に取得時刻、原バイト・抽出本文のSHA、照合した7引用を記録した。Commonには独立したTime節がなく、時刻の根拠はTrace APIのSpan lifetimeを使う。

| 原典の短い引用・規則 | 採用する範囲 | このプロジェクトで追加するもの |
|---|---|---|
| “The start time is recorded when the Span is created.” | 開始を実際の開始時に観測する考え方。 | 過去ジョブに開始時刻を捏造しない、という保存上の制約。原典APIが明示的な過去開始時刻を許す場合と、本契約の旧ジョブ移行は別である。 |
| “The end time needs to be recorded when the operation is ended.” | 計測する操作とその終端を定義する。 | leaseの終端をworker停止や分析完了と同一視しない。 |
| 終端後にSpanの属性・イベント・状態を変更しないという規則 | 過去の観測を上書きしないための参照。 | DBのappend-onlyイベント、CAS、再試行のreceipt、SQLite原子性。OpenTelemetryがこの台帳方式を規定するわけではない。 |
| “An Attribute is a key-value pair” | 識別子と計測の意味を属性として明示する。 | job・attempt・stage・lease世代を区別する。Commonは同じキーの属性上書きを許すが、本台帳の保存済みイベントには適用しない。 |

OpenTelemetry SDK・exporterは導入しない。将来traceへ出力する場合も、sampling・転送障害のあるtraceを全試行の耐久台帳の代わりにしない。計測の語彙を参考にしたのであって、外部標準が金融調査能力の算式を提供したとは扱わない。

## 現在の接続点

| 既存コード | 現在の動作 | 計測を差し込む場所 |
|---|---|---|
| `Harness.claim` | 期限切れleaseをpendingへ戻し、同一会社を排他してclaimする。`jobs.attempts`を増やす。 | リセット前に旧leaseの終了観測を追記し、新claimと開始レコードを同じトランザクションで保存する。 |
| `Harness.renew` | 現在のworker・未期限切れを確認し、`lease_until`を更新する。 | 同じattemptへ更新イベントを追記する。新しい開始や完了件数は作らない。 |
| `Harness.complete` | 版・リース・根拠を検証し、研究結果を保存する。 | 成功した結果保存と同じトランザクションで完了を追記する。検証失敗だけでは完了としない。 |
| `Intake.complete` | 公開資料の分類を保存する。仮説や金融入力を検証したことにはしない。 | 共通completeのintake分岐にも同じ終端計測を入れる。早期returnで記録を落とさない。 |
| `capacity.py` | 呼出元の明示した試行を読取り集計する。状態履歴やDBを管理しない。 | 新しいadapterがas-ofで各attemptを一件へ投影し、現在の入力契約へ渡す。元イベントは別途保持する。 |

元の `job_id + worker` だけの照合では、期限後に同じworker名で再claimした古い処理を区別できなかった。現在は後述の世代照合を実装済みで、計測IDの追加に依存しない。

### 先に行える最小のfencing修正

既存の `jobs.attempts` はclaimごとに増加し、claim戻り値にもある。この値をworkerが `expected_attempt` としてrenew/completeへ返し、保存済み `jobs.attempts` と同じトランザクション内で照合する案なら、新しいtokenや計測テーブルを作らず、同名workerの旧世代を拒否できる。

この修正は、研究とintakeの両分岐で、現在のworker・未期限切れ・期待する試行番号を併せて点検する。worker側が都合よく最新番号を読み直して古い結果へ付け替えず、最初に受け取ったclaimの番号を返すことが必要である。旧形式を互換のため残す場合、その呼出は世代fencingを確認した範囲に含めない。番号の比較は既存のworker識別を補うもので、新しい認証方式ではない。

| 段階 | 変更範囲と保証 | まだ分からないこと |
|---|---|---|
| 先行修正：`expected_attempt` の照合 | 既存の試行カウンターを再利用して旧世代のrenew/completeを拒否する。新DBスキーマは不要。 | 実際の開始時刻、更新履歴、active、usage、claim再送の冪等性は増えない。 |
| 後段：開始ヘッダー・不変イベント | 将来のclaimから開始・更新・終端を記録する。attempt IDは既存 `(job_id, attempts)` に結び付け、新しい秘密tokenは必須にしない。 | 取得できない利用量や旧jobの開始は未計測のまま。 |
| さらに後段：要求receipt | claim/renew/completeの同一要求再送を識別する。 | 外部providerの課金やworkerの実作業時間を自動的に確認するものではない。 |

fencingの不備を先に直すことと、完全な計測契約を導入することを分ける。計測・receiptの実装を、先行修正の全体停止条件にしない。世代照合は[全983テストのチェックポイント](../research/ir-job-fencing-2026-10-15/README.md)で実装・確認済み。CLIは `--expected-attempt` 必須、Pythonの省略は現在番号ではなく固定の1として扱う。この先行チェックポイントでは計測・receiptは未実装。その後、[全1033テストの接続記録](../research/ir-attempt-integration-2026-10-15/README.md)でlease台帳とread-only投影を追加した。receipt・progress・usage・failed/cancelled操作は引き続き未実装。

## 最小の保存スキーマ案

以下は全体設計であり、一部は未実装。現行の最小DB契約は [job_attempts.py](../src/ir_agent/job_attempts.py) のSCHEMAとAPIを参照する。開始header、lease_started/lease_renewed/completed/lease_expiredのみ接続済み。元の `jobs`、packet、研究結果、分類結果は引き続き本体が管理する。

### `job_attempts`：成功したclaimの不変ヘッダー

| 欄 | 内容 |
|---|---|
| `attempt_id` | 一回の新しいclaimを特定する安定ID。同IDを別の試行へ再利用しない。 |
| `job_id`, `company_id` | 実在するjobと会社。callerの会社申告ではなく保存jobから導出する。 |
| `lease_generation` | claimが成功した時点の `jobs.attempts` と対応させる世代。`(job_id, lease_generation)` を一意にする。 |
| `worker_id`, `worker_session_id` | 担当者と、その実行セッション。セッションが不明ならnullとし、worker名を変えて重複を隠さない。 |
| `job_kind`, `stage` | packetから確認した段階。intakeは資料分類、researchは当該研究jobの点検であり、全工程完了という段階名にしない。 |
| `packet_sha256` | claim時の固定packetのcanonical JSON hash。後から別の資料に置換しない。 |
| `started_at`, `first_saved_at` | 成功したclaimを観測した信頼時計の時刻と、DB保存処理の時刻。callerが開始を過去へ指定しない。 |
| `claim_request_id`, `previous_attempt_id` | 冪等なclaim要求と、同jobの前試行が計測済みならその参照。旧試行不明はnullのままにする。 |
| `measurement_scope` | `lease_ownership` を明示する。workerプロセス全体やactive分析のspanとは区別する。 |

### `job_attempt_events`：開始・更新・終端・付随観測

各イベントは `event_id`、`attempt_id`、連番 `sequence`、`kind`、`observed_at`、`first_saved_at`、元要求のhash、完全な `payload` を持つ。書込みは期待する直前sequenceを確認するCASとし、保存済み行を更新・削除しない。payloadへAPIキー、認証情報、プロンプト原文を入れない。

| `kind` 案 | payloadと意味 |
|---|---|
| `lease_started` | 開始ヘッダーと一致する時刻・worker・世代、最初の `lease_until`。claim成功時に一度だけ。 |
| `lease_renewed` | 更新前後の期限、担当・世代、更新要求。開始からの経過をリセットしない。 |
| `progress_observed` | 実際の進捗確認と時刻。heartbeatそのものをactive秒数やlease延長にしない。 |
| `completed` | 本体の結果保存の成功、結果hash、完了時刻。研究とintakeで同じ終端規則を使う。 |
| `failed` / `cancelled` | 実行側が実際に終了を確認した場合の理由と時刻。本体にない終了操作を、計測ログだけから実施済みとしない。 |
| `lease_expired` | 保存済みの最終期限、期限切れを観測した時刻、旧worker・世代。期限は権限の境界であり、workerの停止時刻ではない。 |
| `usage_observed` | モデル/APIの呼出IDと保存根拠、実際に得たusage、費用と通貨、対象区間。不明値はnull。終端後の請求確認も履歴へ追記できる。 |
| `clock_anomaly` | 逆行・不整合の元時刻、同一時計区間の情報、影響。時刻を無言で丸め直さない。 |

lease終端は一attemptにつき一度だけとし、完了・失敗・取消・期限切れが競合したら現在の所有権と保存済み終端を検証する。終端後のusage等は追加観測であり、試行を再開したり別の完了を増やしたりしない。

### 後段の `job_attempt_requests`：操作の再送を区別するreceipt

`request_id`、操作種別、対象job/attempt、要求hash、保存した応答参照、保存時刻を一意に保持する。claimで仕事がなくnullを返した場合もreceiptに残せば、同じ要求の再送で新しいjobをclaimしない。新しいpollは新しいrequest IDにする。

同ID・同要求の再試行は元の応答を返し、同ID・別内容は拒否する。古いclaim応答の再送は現在もleaseが有効だと保証しないため、元attemptと現在の有効性を区別する。renewの再送で期限を二重に延長せず、completeの再送で完了イベントや利用量を重複追加しない。

## 操作と状態遷移

1. **新しいclaim：** 本体が選んだjob、現在の試行数、packetを同じ書込みトランザクション内で確認する。lease更新、attemptヘッダー、開始イベント、要求receiptを一緒に保存する。workerが開始済みのつもりでもclaimがrollbackした場合は、確保された試行として数えない。
2. **更新：** job・worker・attempt・世代と未期限切れを確認し、期限更新と `lease_renewed` を一緒に保存する。同じworkerでも前世代の要求は拒否する。進捗通知やusage通知は期限延長の代わりにしない。
3. **完了：** 本体の検証・研究またはintake結果保存が成功した場合だけ、同じトランザクションで終端を追加する。入力不正・版競合・期限切れは、成功した完了へ変換しない。
4. **期限切れの観測：** 現行claimの一括pending化の前に対象を読み、計測済みの旧attemptへ `lease_expired` を追記する。そのpayloadは元の `lease_until` と現在の観測時刻を分ける。再取得するclaimは新しいattemptと世代にする。
5. **workerが消えた場合：** 実際の停止を推測しない。期限切れで所有権が終わった記録は残せるが、モデル処理や外部APIが同時に停止したとしない。旧workerから遅れて届くusageは旧attemptへ結び付け、新しいworkerへ付け替えない。

期限を過ぎても次のclaim等でまだ観測されていない場合、読取りレポートが履歴を無言で書き足さない。保存済み履歴の未終端と、予定期限を超えていることを併記する。将来、期限観測処理を別に実装しても、常駐監視を既に行っているとは扱わない。

## active時間とモデル利用量

lease開始から完了までには、API待ち、資料取得、反証担当待ち、中断、CPU処理、実際の分析が混ざる。`lease_until - started_at`、heartbeatの回数、生成トークン数からactive時間を逆算しない。最初の最小実装ではlease計測の `active_seconds` をnullにする。

activeを後に記録する場合は、同じ実行セッションの明示した作業区間と、待ち・中断を分離する計測方法を追加する。単調時計の差もsleepや待ちを含むため、そのままactiveと呼ばない。同じworkerの区間重複、別マシン・別プロセスの時計、プロセス再起動を区別し、分離できなければnullを保つ。

`usage_observed` は安定したprovider request/call IDに結び付ける。同じ請求・usage通知を別イベントで二重加算しない。入力/出力/cacheの内訳と総量の関係が確認できない場合、都合よく足して総tokensを作らない。利用量が取れなかったことは0 tokensではない。

費用は実際に得た金額と通貨、根拠を保存する。最新の価格表や為替を勝手に使って過去費用を確定せず、見積りと請求値を区別する。失敗・再試行・期限切れの呼出も削除しない。終端後に判明した費用は、請求確認の新しい観測として追記し、以前のas-ofレポートを上書きしない。

leaseを越えて継続した呼出や、複数attemptで共有した呼出のusageは、lease区間へ比例配賦しない。原記録と既知の費用は監査用に残し、capacityへ渡す当該区間の総量はnull、未配賦理由を別の監査出力へ残す。旧workerの継続稼働が不明な状態で、新旧workerの全利用量が揃ったと報告しない。

## 時計逆行とトランザクション

- 壁時計はオフセット付きUTCとして保存する。操作の順序はイベントsequence・lease世代・receiptで示し、時計が常に単調だとは仮定しない。
- 壁時計が逆行して終了が開始より前になる等の場合、元時刻と異常を保存し、capacity用の正常な区間へ補正しない。該当試行は時間集計への投影を保留し、件数と理由を返す。単調時計が別途あっても、勝手に壁時計や別マシンの時刻へ変換しない。
- 現行のlease判定自体も壁時計を使う。計測側が独自の時計で本体の期限判定を上書きする設計にはしない。本体に影響した逆行は、計測品質の問題とともに別途報告する。
- 計測ヘルパーは既存トランザクションがあればsavepointを使い、外側のcommit・rollbackを奪わない。単独操作だけ自分のtransactionを開始する。別connectionで先に計測成功だけをcommitしない。
- 計測イベントと本体更新のどちらかが失敗したら、その操作の書込みを一緒にrollbackする。外側が後からrollbackした場合、完了・開始・receiptも残らない。返された値やログを、外側commit前の耐久保存の証拠にしない。
- `first_saved_at` は信頼時計で採番する保存処理時刻であり、外側transactionの厳密なcommit時刻を証明する値ではない。長い外側transactionを含む過去の同時読取り可視性を完全に再現したとは主張しない。レポートはcommit済みの一貫したDB snapshotから作る。

将来OpenTelemetryへ複製する場合も、DBのcommit前に外部へ成功イベントを送らない。trace配送を待って本体transactionを長時間保持せず、必要ならcommit済みのイベントを別途exportする。trace送信失敗とジョブ実行失敗は区別する。

## capacityへ渡す投影

投影は計測済みattemptごとに一件だけを生成する。更新イベントを複数の物理試行として並べない。出力窓と知識の `as_of` を分け、窓は既存の `[started_at, ended_at)` 規約、利用可能なイベントはcommit済みsnapshot内の指定時点までに記録されたものに限定する。

| 既存measurement欄 | 投影規則 |
|---|---|
| `id`, `attempt_id` | 同じclaim試行を表す安定ID。モデル呼出やrenewのIDで試行数を増やさない。 |
| `company_id`, `worker_id` | 保存済みattemptの識別子。workerセッションは監査出力へ保持する。 |
| `stage` | `lease:<job_kind>:<stage>` のようにlease経過であることを明示。分析・反証・問い合わせ待ちと混ぜない。名称はプロジェクトの規約案。 |
| `started_at` | 将来の成功claimで実際に記録した開始。旧jobのpacket.as_of、資料公表日、最後のlease期限から逆算しない。 |
| `ended_at` | 完了・確認した失敗/取消の終端。期限切れは、保存済みの既知のlease期限を権限区間の終端として使い、期限切れの観測時刻を監査出力へ残す。 |
| `status` | 完了は `completed`、確認した失敗は `failed`、取消は `cancelled`、未終端は `in_progress`。期限切れは `failed` として渡し、監査出力に `termination_reason: lease_expired` を残す。これは当該lease試行の未完了を表し、jobやworker全体の失敗・停止を意味しない。 |
| `active_seconds` | 最小実装ではnull。明示したactive区間を別途実測できた場合だけ検討する。 |
| `tokens`, `cost` | 全試行区間への帰属・完全性・単位が確認できた実測だけ。欠損や未配賦があればnull。既知の部分量と根拠は監査出力へ保持する。 |
| `synthetic` | 架空検証と実観測を明示して分離する。旧jobから再構成した推定を実観測の開始に昇格させない。 |

「再試行が必要」という終了理由を確認した試行だけ既存の `retry` とし、単に後から再claimされた事実を理由に過去の `failed` を書き換えない。新claimは常に別attemptであり、前後の関連を監査出力に示す。

期限切れは後で観測される場合があるため、終端の有効時刻と観測・保存時刻の差を残す。後から期限切れが見つかったレポートと、その時点では未終端だった旧レポートを区別する。終端を知る前のas-ofへ新しいイベントを遡及混入しない。

測定値の新しいsnapshotを後に再出力しても、同じバッチにin_progress版とcompleted版を同時投入しない。capacityは不変な一バッチの重複を点検する計算器であり、別バッチ間の状態履歴を永続管理する機能ではない。出力には、元DB snapshot、使用イベントID/sequence、投影版、除外・未配賦件数を監査用に付ける。未知欄を既存measurementへ紛れ込ませない。

## 旧job、未開始需要、会社数

移行前の `jobs.attempts` や `completed_at` しかないjobには、開始時刻を後付けしない。現在leasedでも新しいclaimを観測していなければ、完全な開始計測があるかのように出力しない。既存job数、未計測job数、移行後に測れたattempt数を分ける。過去の採用済み研究・資料分類結果も変更しない。

pending jobの件数は、ジョブを作る前の未調査企業数や全需要と同じではない。現行jobsに実際の到来時刻・期限がない場合、待ち時間・期限超過をpacket.as_ofから計算しない。次の段階では、未来のenqueue時刻と期限、未開始需要のsnapshot、通常日と決算集中日の段階構成、反証担当、共有API/DBの制約を実測する。

この最小接続だけで回答できるのは「どの段階のlease試行が何件発生し、どの経過時間で終端を観測したか、どれだけ未計測か」である。全工程を完了した会社数、日次監視可能数、必要worker数の推定には追加の実測が必要であり、既存の `company_upper_bound: null` / `capacity_status: not_estimated` を維持する。

## 実装時の有限テスト

1. 新claimと開始・receiptが原子的に保存され、仕事なしの同一要求再送は新試行を作らない。別要求による再取得は別attemptとなる。
2. renewの同一再送はイベントや期限を増やさず、同じworker名でも古い世代のrenew/completeを拒否する。
3. researchとintakeの成功だけが一度の完了を作り、同じcomplete再送で件数やusageを増やさない。
4. 期限切れ観測とpending化、新claimが一貫し、元の既知期限と後の観測時刻を区別する。旧workerの遅い完了は新attemptに適用されない。
5. 検証失敗、計測保存失敗、内側savepoint失敗、外側rollbackで本体・attempt・イベント・receiptが不整合に残らない。
6. 開始未計測の旧jobは未計測のままで、完了時刻やlease期限から開始を作らない。
7. 同じprovider call IDのusage再送を一回にまとめ、欠損と計測した0、請求と見積り、異通貨、区間外・未配賦を区別する。
8. 時計逆行・終了前後不整合・別processの単調時計を正常区間へ補正せず、時間投影を保留して理由を残す。
9. as-of前後、窓を跨ぐ試行、窓末ちょうどの終端、未終端、期限後観測を既存capacity規約へ接続し、更新履歴を重複試行にしない。
10. 同workerの重複占有と別workerの並行を保持し、active欠損や費用欠損をworker能力や予算へ補完しない。出力の会社数上限はnullのまま。

これらは全体設計の確認項目である。後述のlease台帳・read-only投影と[要求receipt](idempotent-job-requests.md)は最小実装を接続したが、active/usageは未実装。架空テストを実ジョブの全工程計測と数えない。


## 接続した最小実装の利用

`claim --measurement-kind observed` / `synthetic` で区分を明示する。省略時のunknownは開始自体を記録するが、能力レポートの実観測へ混入しない。過去ジョブ3件は未計測のまま保存した。

```bash
.venv/bin/python scripts/report_job_attempts.py \
  --db data/ir-research-2026-10-15.sqlite3 \
  --as-of AS_OF --window-start START --window-end END --output REPORT_FILE
```

時刻はoffset付きISO日時、`START < END <= AS_OF`。read-onlyの一貫したsnapshotから `capacity_request` と `audit` を返す。table欠損はmeasurements:null、既知の空台帳は[]。出力する各試行はleaseの1世代だけで、active/tokens/costはnull、異常・未知区分は理由付きで除外する。現DBの未計測job一覧は現在snapshotの棚卸しであり、過去job状態の完全再現ではない。

`capacity_request.measurements` が配列なら既存の `report_research_capacity()` へ渡せるが、監査側の未計測・除外を無視して運用能力を主張しない。会社数上限は引き続き未推定。

要求ID付きclaim/renewは、[receipt契約とCLI](idempotent-job-requests.md#cliでの使用)を使う。再送は元metadataと現在lease確認を返し、lease/event件数を増やさない。active時間や利用量の計測は追加しない。
