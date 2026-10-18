# claim/renew再送の冪等性：公式原典の確認

AWS Builders’ Library（Malcolm Featonby）とGoogle AIP-155の2 URLを各1回GETし、両方HTTP200。リダイレクト追従・再試行・追加検索なし。原バイト、抽出本文、初回取得日時とSHA-256は [manifest.json](manifest.json) / [sources.json](sources.json)、12箇所の逐語引用とUnicode文字位置をsources.jsonへ保存した。本文のコード例・外部リンクは実行/追加取得していない。

## 原典が述べていること

- [AWS](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) はcaller提供の一意IDを優先し、同caller・同IDを重複として扱う。同一パラメータだけでは別の意図を区別できない。同IDでパラメータが変われば、元パラメータを保持してvalidation mismatchを返す。
- AWSは「recording the idempotent token and all mutating operations…」をACIDのall-or-nothingにするよう明記する。重複時は意味的に等価な応答を返す。EC2の削除後の遅延再送でも元の冪等契約を保つ例だが、資源の現在状態はterminatedとなり、必ずしも同一bytesではない。
- [Google AIP-155](https://google.aip.dev/155) はIDを提供する場合の冪等性を保証し、重複時は以前の成功応答を返すべきとする。ただし歴史的な応答が保持できない場合に現在の資源状態を返すことも許す。request_idは任意を推奨し、形式制約を明文化する。
- 保持期間はAWSではサービス/資源依存、Googleでは合理的な期間を任意に選べる。両原典ともこのscheduler用の数値TTLを指定しない。EC2の資源寿命＋遅延期間という例をlease期限に読み替えない。

## このSQLite schedulerへの適応案

| 論点 | project adaptation | 原典との境界 |
|---|---|---|
| caller request ID | caller/operationのscopeを定義し、同じ論理要求の再送では同IDを保持。IDなしの既存要求へ同保証を自動主張しない。 | key構成・worker識別・UUID制約は原典で未指定。 |
| 同ID別payload | 意味上の正規化payloadを保存/照合して拒否。延長量やworker/job/lease世代を抜かさない。 | field一覧・正規化方式・エラー表現はproject契約。 |
| 原子的な応答保存 | job/lease変更、request記録、再送用receipt保存を同じSQLite commitに含める。再送は保存結果を返し再更新しない。 | token＋変更のACIDはAWSの直接指針。SQLite手順や厳密response JSON保存は適応。 |
| 再送時に元leaseが期限切れ | 元job/期限/世代のreceiptであり、現在の実行権限とは分ける。lease復活・再延長・別job取得にしない。 | lease expiry/fencingの明示規則は両原典にない。古いreceiptか専用エラーかは別途固定。 |
| 保持期間後・復元欠落後のunknown | 記録がないことを未実行の証拠にしない。過去IDの有効範囲と削除/復元の契約を定める。 | unknownの状態/コードは原典の直接指示ではない。削除済み/未使用IDの区別にはtombstone/世代/期限など追加設計が必要。 |
| 新pollと再送 | 同じclaimの再送は同ID、新しいclaim pollや新しい延長意図には別ID。初回no-jobを後から別jobへ変えない案。 | identical payloadが別意図になり得る点はAWS。scheduler poll/null結果の扱いは適応。 |

厳密な保存snapshotを返す設計は選択可能だが、原典が全APIへbyte-for-byte・無期限の同一応答を義務付けたという意味ではない。保存成功receiptを再表示しても現在leaseが有効とは限らない。具体的な同時重複の排他処理、保持削除/復元・IDの有効範囲、期限後の応答契約は別途実装・検証事項として残す。

詳細は [guidance.json](guidance.json)。本体・docs・tests・実DBの変更、金融判断条件・投資閾値の追加は行っていない。
