# claim・renewの再送を安全に扱うreceipt

**最小実装を接続済み。** claimの応答を失ったworkerが同じ要求を再送して別のjobを確保したり、renewの再送で期限をもう一度延ばしたりしないための契約。`job_requests.py`、Store/Harness/CLIへ接続し、全1,111テスト成功（36.360秒）を確認した。実IR送信や日次スケジューラの起動は行っていない。

既存のlease世代fencingと[試行計測](job-attempt-measurement.md)は再利用する。`jobs.attempts` は古い処理から新しいleaseへの書込みを防ぐが、同じclaim要求を二度実行しない保証ではない。また、試行イベントの同内容再送は、相対秒数で指定したrenew要求の再送を識別するreceiptの代わりにはならない。

## 原典の原則とleaseへの適応

根拠は、Malcolm Featonbyによる[AWS Builders’ Library](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)と[Google AIP-155](https://google.aip.dev/155)。2 URLを各1 GETし、原バイト・抽出本文・12引用の位置を[保存済み証拠](../research/idempotent-job-requests-2026-10-15/sources.json)で確認している。本設計のための追加取得は行わない。

| 原典の原則 | 短い原文・保存引用ID | 本プロジェクトへの適応 |
|---|---|---|
| caller提供のIDで要求の意図を区別する | AWS “a unique caller-provided client request identifier”（`aws-id-intent`）。同じパラメーターでも二つの資源を望む場合がある（`aws-parameters-not-intent`）。 | 同一pollの再送は同じID、新poll・新しい延長意図は別ID。payloadだけで重複判定しない。 |
| 同IDでパラメーターが違えば拒否する | AWS “a validation error indicating a parameter mismatch”（`aws-mismatch`）。 | worker、job、lease世代、延長秒数、計測区分等の意味ある入力を保存して比較する。 |
| tokenと関連する変更をACIDで一緒に扱う | AWS “recording the idempotent token and all mutating operations”（`aws-atomic`）。 | job・lease更新、試行イベント、再送用receiptを同じSQLite transactionに含める。response metadataの厳密な凍結は本プロジェクトの選択。 |
| 重複には以前の成功に対応する応答を返す | AWS “a semantically equivalent response”（`aws-equivalent`）、Google “the response for the previously successful request”（`google-replay`）。 | 不変の元応答と、現在のlease有効性を別欄で返す。再送で新しい実行権を付与しない。 |
| 現在の資源が変わっている場合がある | AWSの削除後の遅延再送（`aws-late`）、Googleの現在状態を返せる例外（`google-stale`）。 | 元jobが完了・期限切れ・再取得済みでも別jobをclaimし直さない。leaseの状態名やfencingは原典の直接規則ではない。 |
| 保持期間はサービスに依存する | AWS “Requirements for retention vary across services and service resources.”（`aws-retention`）、Google “any reasonable timeframe”（`google-replay`）。 | 数値TTLを作らない。初期実装では削除を行わず、復元や記録欠落時の不明を未実行と決め付けない。 |

Googleはrequest IDの任意性と形式制約の明記も推奨している（`google-optional-format`）。原典が全APIに無期限・同一bytesの応答を要求しているとは読まない。以下のキー、JSON、SQLite手順、null応答の固定、lease有効性の返却は本プロジェクトへの適応である。

## APIと旧呼出の互換

`claim` / `renew` に、任意の `request_id` と `caller_namespace` を追加した。片方だけの指定は検証エラーにする。

```text
claim(worker, lease_seconds, *, request_id=None, caller_namespace=None,
      measurement_synthetic=None, now=None)
renew(job_id, worker, lease_seconds, *, expected_attempt,
      request_id=None, caller_namespace=None, now=None)
```

`now` はテスト用の信頼runtime時計で、要求本文やCLIから取らない。通常はwriterを取得した後に現在時刻を読み、待ち時間を新leaseの経過へ入れない。時計はreceiptの同一性に含めない。

- **両方省略：** 既存の戻り値と動作を保持する。新しい冪等性保証を表示しない。旧呼出へ受信のたびにIDを自動発行して「再送を防いだ」としない。
- **両方指定：** receipt付き契約で処理し、後述のenvelopeを返す。同じ論理要求の再送は同じ組を使う。
- **ID形式：** 前後空白のない非空文字列とし、UUIDを使えるようにする。大文字小文字を変換したり空白を削ったりして別IDをまとめない。具体的な技術上限を導入するなら入力契約で明記する。

既存の `expected_attempt` は引き続きclaimで受け取った試行番号をrenewへ返す。receiptがあるからといって、古い番号を現在の `jobs.attempts` へ自動更新しない。

### callerとworkerは異なる役割

主キーは **`(caller_namespace, request_id)`** とする。operationも正規化payloadへ含め、同じ組をclaimとrenewへ流用した場合も別payloadとして拒否する。このキー範囲は本プロジェクトの選択である。

`caller_namespace` は要求IDの衝突を分離する実行主体の名前空間、`worker` はjobのlease所有者である。複数workerを管理する一つのcallerでも、workerを変えた同ID再送は拒否する。別namespaceの同じ文字列IDは別要求になるため、再送のたびにnamespaceを変えない。

名前空間は認証情報ではない。現行のローカルworker名や、任意のnamespace文字列を認証済みcallerとみなさない。将来認証層を加える場合は、その層が名前空間の利用権限を確認してからreceiptへアクセスする。request IDやhashが存在することだけで実行権限を認定しない。

## 意味のある入力を固定する

receiptの照合用payloadは、未知欄を受け取らない小さなallowlistにする。既定引数を解決した後の値と契約版を保存し、既定値が将来変わる場合も元の意味を再現できるようにする。

| 操作 | hash・完全一致比較に含める入力 |
|---|---|
| claim | 操作名、契約版、worker、要求した `lease_seconds`、`measurement_synthetic`。将来選択filter等を追加するなら、その意味ある入力も契約版とともに含める。 |
| renew | 操作名、契約版、job ID、worker、`expected_attempt`、要求した `lease_seconds`。 |

`measurement_synthetic` のtrue・false・nullは異なる入力であり、unknownをfalseへ補完しない。workerセッションを将来開始計測へ渡す場合も、要求の意味が変わるなら照合対象へ加える。

実runtimeの `now`、receiptを再読取りした時刻、transport retry回数、trace ID等はhashへ含めない。同じ要求でもruntimeの現在時刻は変わるためである。絶対期限は最初の処理時の `now + lease_seconds` から一度だけ計算して応答に固定し、再送で再計算しない。実験用の注入時計もserver時計という位置付けであり、callerがidempotencyの意味を変える入力にはしない。

既存の `json_text` によるcanonical JSONとSHA-256を使う案とし、hashだけでなく小さい正規化payload本体も保存して完全一致を確認する。job packet、資料本文、プロンプト、APIキー、認証ヘッダーを照合payloadへ複製しない。新しい機密原文をreceiptのmetadataとして増やさない。

## 最小のreceiptスキーマ

新設した一つの `job_request_receipts` テーブルで、最初に成功した要求の意味と応答を保持する。

| 欄 | 内容 |
|---|---|
| `caller_namespace`, `request_id` | 複合主キー。一意性をアプリケーション内の事前チェックだけに依存させない。 |
| `contract_version`, `operation` | 正規化・戻り値の契約版とclaim/renewの区別。 |
| `request_json`, `request_sha256` | allowlistだけの正規化payloadとhash。保存済みIDとの意味の不一致を検出する。 |
| `original_response_json` | 後述の最小応答metadata、またはno-jobを表すJSON null。現在のjob全体を再取得した値で上書きしない。 |
| `job_id`, `generation`, `attempt_id` | 対象がある場合の参照。no-jobではnull。既存の開始未計測jobのrenewでは、試行番号はあっても計測attempt IDはnullになり得る。 |
| `measurement_event_id` | 初回の開始・更新計測がある場合の参照。receiptから計測イベントを新しく発明しない。 |
| `first_saved_at` | 信頼できるruntime時計で保存時に付ける時刻。callerからの過去指定を受け取らない。厳密な外側transactionのcommit時刻を証明するものではない。 |

物理列は `caller_namespace`, `request_id`, `data`, `first_saved_at`。上表の契約版・payload・元応答等は `data` のJSONに保存し、参照欄は元応答内に保持する。上表のrequest_json/original_response_jsonは概念名であり、その名前のSQL列は作らない。

要求ID付きの新しいclaimとrenewだけがこのテーブルへ保存する。旧要求の履歴を、現在のjob状態から遡及作成しない。既存の完了再送は本体の世代・結果一致確認で扱い、この最小案はcompleteのrequest ID APIまで拡張しない。

## 初回処理と再送の順序

### 同じtransactionでlookupから保存まで行う

1. ID・名前空間・正規化payloadを検証する。認証層がある場合はそれを先に通す。
2. 書込みtransaction内でreceiptを検索する。**既存claimの期限切れcleanupや、renewの新期限計算より先**に行う。
3. 見つかった場合はpayloadを比較する。同じなら元応答を読み、現在のleaseを読取り確認して返す。期限切れcleanup、job選択、試行数の加算、renew、計測イベント追加を実行しない。違えば通常の検証エラーにする。
4. 見つからず、台帳の継続性が確認できる新規要求なら、既存のclaim/renew処理と世代fencingを行う。job・lease変更と試行計測を同じtransactionへ含める。
5. 最小の元応答を作り、receiptを保存する。claimがno-job/nullに終わった場合も成功したpollの結果として保存する。
6. 同じtransactionがcommitした後に応答する。commit後に応答だけ失われたら、同ID再送は保存receiptへ到達する。

SQLiteの具体的な排他は本プロジェクトの適応である。単独操作では `BEGIN IMMEDIATE` 等でwriterを直列化し、複合主キーで二重保存を防ぐ。既に外側transactionがある場合はsavepointで合流し、自分で外側をcommitしない。現行Harnessのtransaction内へ処理を置くか、共有transactionを使う内部関数へ整理し、公開 `claim` を入れ子に呼んで二重にBEGINしない。

同時に来た同じIDは一方のcommit後に同じreceiptを読む。同ID・別payloadもwinnerのreceiptを見て拒否する。jobだけ更新してreceipt保存に失敗した場合、または計測保存に失敗した場合は全変更をrollbackする。外側が後でrollbackした場合も、receipt・job・イベントが一緒に消える。commit前に成功receiptを外へ送ったり、別connectionで先に保存したりしない。

入力不正や本体の世代・期限検証の失敗は、この最小案では成功receiptとして保存しない。副作用とreceiptが残っていないことを確認してエラーを返す。通信が切れただけで「rollback済み」と推測せず、成否不明なら元IDで再送する。

## 元応答と現在のleaseを分ける

request ID付きAPIは、次の欄を持つenvelopeを返す。

| 欄 | 意味 |
|---|---|
| `request_ref` | namespace、ID、operation、契約版。 |
| `replayed` | 保存receiptを返したかどうか。再送で新しいleaseを付与したという意味ではない。 |
| `original_response` | 最初に返すべきだった不変metadata、またはnull。 |
| `current_lease` | 今回読取り時点の同じjob・世代・workerの有効性、確認時刻、理由。no-jobの元応答ならnull。 |

claimの `original_response` は、job ID、会社ID、worker、試行番号、元の `lease_until`、計測attempt参照、packet SHA等の最小metadataとする。renewは同じ識別子と、初回に確定した更新後期限・更新イベント参照を保持する。資料本文やプロンプトを含むjob全体をreceiptへコピーしない。packetが必要なら不変の参照から読み、保存SHAとの一致を確認する。

`current_lease` は現在のstatus・owner・試行番号・期限を照合し、少なくとも有効、完了、期限切れ、再取得済み、状態不明、時計不整合を区別する。状態名はプロジェクトの契約である。初回のleaseが後でrenewされていれば、元応答の期限と現在の期限は異なり得る。前者を上書きせず、後者は現在の確認として返す。

| 再送時の状況 | 返すものと禁止する変更 |
|---|---|
| 元claimがまだ同世代・同workerで有効 | 同じ元応答と現在の有効性。新しいjobを選ばず、開始イベントを増やさない。 |
| 元jobが完了済み | 元応答と完了状態。成功receiptを新しい実行権として使わない。 |
| 元leaseが期限切れ | 元応答と期限切れ。再送で期限を延ばさず、別jobをclaimしない。 |
| 同じjobが別世代へ再取得済み | 元応答と世代不一致。worker名が同じでも旧世代を現在のleaseへ付け替えない。 |
| 元renewの後に別IDのrenewも成功 | 元renew応答は当初の期限のまま。現在の期限を別欄に表示し、初回更新イベントを再適用しない。 |
| 初回claimはno-job/null、今はjobがある | 同じnull応答。新しい仕事を探す場合は新しいpoll IDを使う。 |
| 元job・packet参照が欠損/不一致 | 受領済みreceiptと現在状態の不明を示し、別jobで穴埋めしない。 |

これらの有効性は読取り時点の機械的なlease確認であり、その後の実行を予約する保証ではない。workerはrenew/complete時にも元の試行番号を返す。二つのプロセスが同じ成功receiptを受け取って同じ分析を並行実行することまで、このreceiptだけで防いだとは主張しない。実行側でも同じattemptを重複開始しない管理が別途必要である。

## 時計異常と観測時刻

再送のたびにruntime `now` が変わっても、request hash・元応答は変わらない。現在の有効性を確認するための時計だけを新しく使う。

現在時刻が元receiptの保存時刻や当該試行の直前観測より逆行している等、正常な有効区間と確認できない場合は、元応答を保持したまま現在の実行権を確認不能とする。計測の `normal_interval:false` や終端を無視して、期限切れのleaseが復活したと報告しない。時間を丸め直して新しい期限を作ることもしない。

新規要求では本体のlease判定と既存計測が時計異常を扱う。receiptはその意味を独自に修正しない。後から過去の時刻を指定して、当時receiptを保存していたことにする経路を設けない。

## 保持、削除、復元の境界

初期実装にはTTL削除を入れない。leaseが終わったことはreceiptを削除してよい理由にはならず、保持期限をlease秒数と同じにしない。原典から具体的な日数を流用・推測しない。

「検索して見つからない」だけでは、未使用IDなのか、削除・古いbackupへの復元で記録が失われたのかを一般には判別できない。通常の新規要求として扱えるのは、当該namespaceについて台帳の継続性を運用上確認できる範囲である。この前提を保証せず、任意の欠損IDから未実行を証明したとはしない。

最小実装のサポート範囲は、receiptを削除せず、過去のreceiptを失うDB復元をしていない継続した台帳である。その範囲ではmissing IDを新規として扱う。全てのmissingを無条件にunknownにして新しい要求を一切受け付けない契約ではない。一方、同じDB識別子のまま古いbackupへ無言で戻した状態を自動検知できるとは主張しない。

将来削除するなら、再送の有効範囲、削除済みIDのtombstone、復元時のstore/namespace世代等を別途設計する必要がある。削除・復元による欠損が既知または疑われる状態では、該当範囲を `unknown` として保留し、盲目的に新しいclaim/renewへ進めない。新しいIDやnamespaceへ切り替えるだけで過去の副作用が消えたとは扱わない。

復元epochやrequest scopeを導入する場合も、DB側で運用上切り替えることと、callerが送信先scopeを知って再送時に照合できることの両方が必要である。同epochのsilent rollbackは、別証跡なしに解決済みにはできない。

欠損検出・復元プロトコルは未実装である。receiptを残す最小案と、保存喪失を自動検知する能力を区別する。既存台帳を無言で消去して全IDを新規扱いにするcleanupは設けない。

## 具体的な受入ケース

1. claimのcommit後に応答を失って同IDを再送しても、同じ元応答を返し、jobの試行数・開始イベント・別jobのleaseは変わらない。
2. 初回no-job/nullの後に新jobを追加しても、同IDはnullを返す。新しいpoll IDだけが新規claimを試みる。
3. renew応答を失って再送しても、初回に計算した期限を返し、後の `now + lease_seconds` へ再延長せず、renewイベントが一件のまま。
4. 同IDでworker、lease秒数、計測区分、job、試行番号、operationを変えればpayload不一致で拒否し、書込みがない。
5. 同じpayloadでも異なるIDは異なる意図として本体へ渡る。ただし通常のlease排他・fencing・入力検証は引き続き働く。
6. 完了・期限切れ・別世代再取得の後に同claimを再送しても元応答を保持し、現在の状態を分離して返す。新しい実行権を付与しない。
7. 別IDによる後続renew後も、前のrenewの再送は前の元応答と現在期限を分け、イベントや期限を更新しない。
8. 同一IDの並行要求は一つのreceiptと一回の本体変更になり、別payload競合は拒否する。名前空間の分離と同namespaceのworker変更も確認する。
9. job更新後のreceipt保存失敗、試行イベント保存失敗、savepoint失敗、外側rollbackで、job・イベント・receiptが片方だけ残らない。
10. 実runtime時刻・transport metadataが変わっても同じ要求を照合し、時計逆行では元応答を変えず現在の有効性を保留する。
11. IDなし旧呼出は既存の形を維持し、receipt保証を表示しない。片方だけのID指定、未知欄、空ID等は本体変更前に拒否する。
12. 自動TTL削除を行わず、時間経過でreceiptが消えない。記録喪失・復元不明を自動検出するAPIはないため、その場合は運用側で新規要求を止めて照合する。無言の復元をこの実装が検出したとの検証にはしない。
13. receiptのpayload・元応答にpacket本文、プロンプト、APIキーや認証ヘッダーを複製しない。再送を実作業時間・利用量・会社完了件数として増やさない。

この設計は、要求の再送によるjob状態の二重変更を防ぐためのものに限る。日次の詳細分析、IR送信、注文、金融条件や会社数上限を追加・実行するものではない。


## CLIでの使用

```bash
.venv/bin/ir-agent --db PATH claim --worker analyst-1 \
  --measurement-kind observed --caller-namespace daily-runner --request-id POLL_ID
.venv/bin/ir-agent --db PATH renew JOB_ID --worker analyst-1 \
  --expected-attempt GENERATION --lease-seconds N \
  --caller-namespace daily-runner --request-id RENEW_ID
```

`POLL_ID` / `RENEW_ID` はcallerが保存する論理要求ID。同じ要求の通信再送は同じ組・同じ引数を使い、新pollや追加延長は別IDにする。no-jobの元応答がnullなら同じpoll IDでは仕事を取り直さない。

ID付きclaimでは `original_response.job_id` をpacket取得へ、`original_response.generation` をrenew/completeの `--expected-attempt` へ使う。実作業の前に `current_lease.valid_now` がtrueか確認し、packetのSHAを元応答と比較する。元の `lease_until` だけで今も有効と判断しない。IDなし旧claimの `id` / `attempts` とは戻り値の形が異なる。

検証はlibrary23件、Harness統合9件、CLI2件を含む全1,111件。時計待ち、並行connection、内外rollback、expired/reclaimed/completed再送も確認した。テストは架空台帳上の検証であり、実企業の分析完了件数や能力の測定ではない。
