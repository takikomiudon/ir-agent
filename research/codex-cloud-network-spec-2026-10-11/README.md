# Codex Cloud の通信仕様と今回の503

20:45:24の初429は[追加観測](first-429-observation.md)に保存した。[5分間の休止・再開](first-429-cooldown-observed.md)も実ログで確認した。以前の固定比較窓と分け、共通503と同一原因とは扱わない。

調査日：2026年10月11日。クラウド環境のネットワーク設定変更・環境再起動・企業への送信は行っていない。調査プログラムの取得頻度は観測に応じて調整している。

後続の低頻度調査を含む[503のケース比較](503-case-summary.md)を保存した。[直前の負荷窓](rolling-load-comparison.md)、[0.35 RPS試行の固定観測](cap-observation.md)、[上限変更後の完全60分窓](clean-low-rate-window.md)では、実GET時刻・休止・同一URLの成否を分けて確認している。共通503とレート制限の因果関係や数値quotaは未確定。

## 結論

今回の失敗は、企業のIRページより手前にあるクラウドの通信中継が、外部接続を開始する処理でエラーになっているという説明と整合する。応答には `immediate connect error: Invalid argument|remote address:envoy://cloudflare_https_tunnel/` が含まれる。**この調査の外部アクセスを約49分休止した後、設定を変更せずにJPXと公式ドキュメントへのアクセスが回復した。** アクセス量や同時接続数に応じた制限・過負荷は原因候補だが、通信設備の復旧との区別はできていない。

停止中はCodexの公式ドキュメント、OpenAIのヘルプ、公開GitHubへのアクセスでも同じ503を再現した。企業調査用のPythonとは独立した単発のcurlでも再現し、curl側のTLS検証は成功した。再試行の並列数を8から24へ増やした時期と障害再発が近いが、因果関係は未確認。単発でも一時的に継続して失敗した事実は、休止で解除される種類の制限を否定しない。詳細は [HTTP成功と503の条件比較](rate-comparison.md)。

## 確認できた仕様

以下は、この実行環境向けに提供されたOpenAIの環境プラグインの説明で確認した事項。公開Web版の現行Codex CloudドキュメントとLegacy版のInternet accessも、回復後に本文を取得して確認した。

| 仕様 | 説明・今回への意味 | 根拠 |
|---|---|---|
| HTTP/HTTPSは中継経由 | 環境は通常 `HTTP_PROXY` / `HTTPS_PROXY` を使う。エグレスプロキシのsidecarがアクセス制御を行う。 | [Cloud environment networking](skill://plugin_connector_1p_c5b7d5df5d7081918f2c4be5a633ed5d/cloud-environment-runtime/references/networking.md) |
| 一般のインターネットへの直接経路はない | プロキシ環境変数の解除、経路変更、手元のpolicyファイルの編集はアクセス許可を与えない。 | 同上 |
| 設定と準備状態は別 | `network_policy.state` が `enforced` のときに適用状態を確認できる。`unknown` は適用済みという証拠にならない。 | [cloud-environment-runtime](skill://plugin_connector_1p_c5b7d5df5d7081918f2c4be5a633ed5d/cloud-environment-runtime/SKILL.md) |
| 設定ドラフトと稼働中の環境は別 | ドラフト保存は実行・適用・公開を行わない。ユーザーによる設定保存後の稼働環境への反映は非同期になり得る。 | [How Codex cloud onboarding works](skill://plugin_connector_1p_ed5feb9070a08191b08c81c47947bc16/setup/references/onboarding.md) |
| 公開・復元時に接続を引き継ぐとは限らない | 公開はファイル状態のsnapshotと環境の復元・再接続を伴い、live process・open connection・runtime authenticationの維持を前提にできない。ただし今回それが障害の原因かは未確認。 | 同上 |

上記資料および今回取得した公開2ページには、今回の `envoy://cloudflare_https_tunnel/` エラーの具体的な修復方法や、HTTPのRPS・並列数・日次取得数のquotaは記載されていない。このことから、製品全体に上限がないとは結論しない。

公開の [Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments#connect-to-services) は、許可ドメインの設定、設定保存と実アクセスの検証、公開後の新しいtaskでの検証を説明する。また、公開インターネットへのegress IP rangesは顧客間で共有されると説明する。**IP共有の記載は、今回どの単位でレート制限されたかを証明するものではない。** 公開のInternet access旧URLは公式redirectを経て [Legacy版](https://learn.chatgpt.com/docs/cloud/internet-access) に到達し、現行のCloud environmentsを案内していた。旧版と現行版を同一仕様として混同しない。

## 現在の設定と実測

- 起動時policyファイル、現在のruntime、設定ドラフトはいずれもHTTP通信を `unrestricted` としている。
- runtimeは `connected` / `running`、設定revisionと観測revisionはいずれも6。ただしnetwork policyの適用状態は `unknown`。
- JPXの接続確認は13:46:39と13:50:46（日本時間、以下同じ）に200だった。その後、企業サイトとJPX・ラクスで同じ503が再発。
- 14:08の公式ドキュメント・ヘルプ取得、公開GitHubへのnative Git、14:09の単発curlでも同じ503を確認。
- 14:58:44のJPX単発GETは200。15:04〜15:05の公開公式ドキュメント本文も200へ回復。runtimeのrevision6、network policyのunknownはそのままだった。
- これらの確認でドメイン許可拒否を示す応答は得られていない。ただしpolicy適用状態がunknownであるため、内部の許可設定の適用まで正常とは断定できない。
- `cloudflare` という内部名から、訪問先サイトのボット遮断だとは推定しない。

設定・単発curl・native Gitの結果は [runtime-observation.json](runtime-observation.json)。以前の200/503は [全社調査の接続確認](../ir-contacts-universe-2026-10-11/network-healthchecks/) に保存している。回復後の状態は [recovery-runtime-observation.json](recovery-runtime-observation.json)、新しいGETは [network-probes](network-probes/) に保存した。

## 公開ドキュメントの取得結果

| 参照先 | 取得結果 |
|---|---|
| [Codex Cloud: Internet access](https://developers.openai.com/codex/cloud/internet-access/) | 14:08は503。回復後、308を2回経て公式learn.chatgpt.comのLegacy版に到達、15:04にHTMLとMarkdownが200。本文取得済み。 |
| [現行Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments) | Legacy版本文から案内された現行資料。15:05にMarkdown200、本文取得済み。 |
| [Codex Cloud: Environments旧URL](https://developers.openai.com/codex/cloud/environments/) | 14:08は503。この旧URLそのものは回復後に再取得していない。 |
| [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan) | 14:08は503。回復後は再取得していない。本文未取得。 |

応答をこのディレクトリのJSONに保存し、[evidence-index.json](evidence-index.json) に保存ファイルのSHA-256を記録した。確認した本文と仕様の引用は [public-documentation-observation.json](public-documentation-observation.json)。今回読んだ2ページからHTTP件数・時間・並列数の数値上限やunknownの個別定義は得られなかった。

## 次に切り分ける点

1. 実GETの開始・完了・待機時間、503/429の診断ヘッダーを今後保存する。過去ログの日時から正確なRPSを復元できるとは扱わない。
2. 少数workerに加えて、robots・redirectを含む全体のGET頻度を制限し、共通503で停止して休止・単発確認を行う。具体的な安全RPS・休止時間は未確定。
3. 制限発動か設備故障かを確定するには提供側の中継・throttleログが必要。設定は変更せず回復したため、ドメイン許可の追加や再作成を必須の解決策とは扱わない。

サポートへの送信、環境の再起動・設定変更はいずれも実行していない。IR調査の証拠・再開対象はそのまま保持している。
