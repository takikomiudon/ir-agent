# HTTP成功と503の条件比較

調査日：2026年10月11日。表の時刻は日本時間。保存済みログの解析と、回復確認の低頻度・単発GETを行った。

アクセス量・同時接続数・休止時間が今回の障害に影響した可能性がある。8から24へ並行処理枠を増やした直後に複数originで共通503が現れ、この調査の外部アクセスを約49分休止した後には200へ回復した。**レート制限または通信中継の一時的な過負荷に合う観測だが、原因の確定ではない。**

## 条件の差

| 区間 | 観測 | 読めること |
|---|---|---|
| 13:46:39〜13:50:46、8並列 | JPXの接続確認は200。229社を保存して手動で一旦停止。証明書など別種の上流エラーによる503は含む。 | 通信経路はこの期間に多数の正常応答を返した。229社保存はHTTPリクエスト数ではない。 |
| 13:50:46以降、24並列へ再開 | 再開直前のJPXは200。共通 `Invalid argument` 型503の最も早い保存呼出時刻は13:50:54.429699。直後には200と503が混在した。 | 並列増加と障害再発の時期は近い。接続先、累積利用量、キャッシュも違うため、並列数だけを変えた実験ではない。 |
| 停止後〜14:09:16 | JPX、企業サイト、公式ドキュメント、GitHubが共通503。単発curlでも503。 | 単発へ減らして直ちに解消する状態ではなかった。休止を要する制限も、通信設備の故障継続も説明候補。 |
| 14:09頃〜14:58:44、この調査の外部アクセスを約49分休止 | JPX単発GETが200、約0.31秒。 | 時間を置いて回復した。49分が必要な冷却時間・上限だと証明したものではない。 |
| 14:59:15、別originへ単発GET | ラクスの `/contact/ir/` は実サイトの404ページ。 | 通信経路の共通503は解消していた。この診断URLは誤ったパスで、IR窓口の確認結果としては使わない。 |
| 15:04〜15:06、低頻度の単発GET | 公式OpenAIドキュメントの本文と、正しいラクスIR URL `/ir/` は200。 | JPXに加え、別originでも正常な本文取得を確認できた。 |

同じ `network_policy.mode=unrestricted`、`state=unknown`、設定revision6の状態で200を得た。今回のunknownだけでは503の成功・失敗を説明できない。取得できた状態から中継設備の内部状態までは見えない。

## 保存応答の比較集計

[オフライン集計JSON](rate-analysis-agent.json)では、再試行の保存応答をURLと `retrieved_at` で重複排除した。robotsキャッシュの再添付を除き、保存されたredirectホップは別応答として含めた。

| 再試行の区間 | 保存HTTP応答 | 200 | 共通Invalid argument型503 | その他503 |
|---|---:|---:|---:|---:|
| 8 workerの企業調査 | 1,527 | 1,274 | 0 | 13（TLS関連） |
| 24 workerの企業調査 | 194 | 158 | 8 | 2（connection termination） |
| JPX・ラクスの接続確認 | 5 | 2 | 3 | 0 |
| 合計 | 1,726 | 1,434 | 11 | 15 |

429の保存応答は0件。表の残る応答はredirect・403・404である。これは保存されている応答イベントの集計で、完全な送信ログや実RPSではない。保存されなかったredirect途中のrobots、HTTP statusなしの例外などがあり、単純に件数を時間で割って提供側の上限を推定しない。

初回の障害は再試行と別に集計した。最初の共通503は13:01:49.787792、コシダカHDの保存呼出時刻。直前10秒の保存呼出時刻範囲には80の応答イベント（200が69、404が10、403が1）がある。初回worker数の実行根拠と正確な送信時刻は残っていない。これもアクセス集中の可能性を調べる材料になるが、再試行の8→24と同一条件ではない。**8 workerを安全な閾値と確認したわけではない。**

## 503を一種類として数えない

`Invalid argument|remote address:envoy://cloudflare_https_tunnel/` を含む共通503と、上流TLS証明書エラー・`WRONG_VERSION_NUMBER`・`connection termination` などの503は分けて集計する。HTTP statusだけで全件をレート制限と解釈しない。

回路が開いた後に生成された `environment_circuit_breaker_open` はローカル停止で、企業へのHTTP応答ではない。robotsキャッシュの再添付と、同一証拠の複数コピーも新規アクセスとして数えない。

## レート制限について分かったことと不足

- 既存収集実装は同originで1秒以上の間隔を設けるが、全origin・全プロセスを合算したHTTP頻度制限はない。多くの接続先へ並行してアクセスすると、中継への総負荷は増え得る。
- workersは同時に処理する会社の数であり、8→24から実際のRPSが3倍になったとは言えない。
- 過去の証拠は実送信・応答完了時刻や `Retry-After` / `RateLimit` ヘッダーを保存していない。`retrieved_at` はhost lock・間隔待機・HTTP送信より前の呼出時刻。正確なRPSや同時接続数は復元できない。
- 429が保存されていないことは、中継側のレート制限がなかった証明にはならない。503の本文にも明示的なquota超過や解除時刻はなかった。
- 回復が冷却時間によるものか、中継設備の復旧・共有負荷の変化によるものかは、提供側ログなしでは区別できない。
- 取得できた [現行Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments) と [Legacy Internet access](https://learn.chatgpt.com/docs/cloud/internet-access) には、HTTP RPS・並列数・日次件数の数値quotaや、この503とrate limitの対応は記載されていない。[本文と引用の記録](public-documentation-observation.json)を保存した。

再開時には、少数workerに加え、robots・redirectも含めた**全体のGET頻度**を制限する。共通503が複数originで出たら処理を止め、時間を置いて単発GETで回復を確認する運用が妥当。具体的な安全件数・RPS・休止時間は未確定で、仮の値をCodex Cloudの公式上限として扱わない。

## 証拠

- [実装のオフライン監査](rate-implementation-audit.md)
- [応答の重複排除・区間別集計](rate-analysis-agent.json)
- [再試行manifest](../ir-contacts-universe-2026-10-11/runs/20261011T044639285379Z/manifest.json)
- [停止中の状態・単発curl](runtime-observation.json)、[回復後の状態](recovery-runtime-observation.json)
- [JPX回復の200](network-probes/20261011T055844445687Z.json)、[ラクス別originの404](network-probes/20261011T055915212483Z.json)
- [正しいラクスIR URLの200](network-probes/20261011T060651236812Z.json)、[現行公式資料の200](network-probes/20261011T060504182141Z.json)

JPX回復証拠の文字列抜粋には診断時のcharset誤りがあり、[別ファイルの補正](network-probes/20261011T055844445687Z-text-correction.json)を保存した。原snapshot・HTTP status・原応答SHAはそのまま保持し、補正ファイルを別のGETとして数えない。
