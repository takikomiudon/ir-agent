# network_policy.state = unknown の仕様確認

確認日：2026年10月11日（日本時間）。これはこの環境の状態取得ツールが返した値の調査。公開Codex CloudのUIに `unknown` というアクセス設定モードがあると確認したものではない。

## 取得できた仕様の原文

状態取得ツール `cloud_environment.environment_status` の説明：

> These resolved lists describe the desired spec; state reports whether it is enforced.

設定として希望された許可一覧と、その設定の適用状態を区別するという説明。ツール説明と今回の返却値は [unknown-state-evidence.json](unknown-state-evidence.json) に保存した。

[cloud-environment-runtime / SKILL.md](skill://plugin_connector_1p_c5b7d5df5d7081918f2c4be5a633ed5d/cloud-environment-runtime/SKILL.md) の原文：

> Network policy is applied only when its current state is `enforced`. Missing or any other states, including `skipped` and `unsupported`, do not establish readiness.

この仕様は、適用済みと判断できる状態を `enforced` とし、それ以外から準備完了を判断しないよう指示する。**`unknown` の個別定義、生成条件、どれくらいで変わるか、どの内部処理が原因でunknownになるかは、取得できた資料に明記されていない。**

[How Codex cloud onboarding works](skill://plugin_connector_1p_ed5feb9070a08191b08c81c47947bc16/setup/references/onboarding.md) の原文：

> Saving configuration edits through the user-facing editor can request a runtime update; propagation can be asynchronous. Recheck the affected operation before claiming it works.

設定反映は非同期になり得る。ただし、この一般仕様を根拠に「今回のunknownは反映待ち」と決めつけることはできない。

## 今回の値をどう読むか

| フィールド | 返却値 | 読めること |
|---|---|---|
| network_policy.mode | unrestricted | 設定として希望されているHTTPアクセスは制限なし。 |
| network_policy.state | unknown | この値から適用済みという確認は得られない。未適用・許可拒否・故障の確定にも使えない。 |
| observations_current | true | 状態報告は現在の設定に対応していると報告されている。個別項目がすべて準備完了とは限らない。 |
| spec_revision / observed_spec_revision | 6 / 6 | 設定revisionと観測revisionは一致。古いrevisionしか観測されていない状態ではないが、network policyの適用完了の代用にはならない。 |
| connectivity / observed_phase | connected / running | 環境との接続・稼働が報告されている。外部サイトへのHTTP成功の保証とは扱わない。 |

したがって、前に説明した「適用済みと確認できていない」は上記契約に基づく読み方であり、**unknownの発生理由を特定した説明ではない**。この値そのものが通信を拒否する設定だという根拠もない。

## 503との関係と未確認事項

実通信では `Invalid argument|remote address:envoy://cloudflare_https_tunnel/` を含む503が返った。このHTTPエラーと `unknown` の因果関係は確認できていない。設定を追加し直せば解消するとも判断できない。

公開ドキュメントの前回取得は同じ503により本文未取得だった。その後、この調査の外部アクセスを約49分休止し、設定変更なしでJPXへの単発GETが14:58:44に200へ回復した。回復後のruntimeもrevision6、`unrestricted` / `unknown` のまま。[回復時の記録](recovery-runtime-observation.json)と[成功・失敗の比較](rate-comparison.md)を保存した。

回復後、公式redirect経由で [Legacy Internet access](https://learn.chatgpt.com/docs/cloud/internet-access) と、同ページが案内する [現行Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments) の本文を取得して読んだ。現行資料は設定保存と実通信の検証、公開後の新taskでの検証を案内するが、`network_policy.state=unknown` の個別定義や解消時間は記載していない。[取得本文と引用](public-documentation-observation.json)を参照。

**unknownは成功時にも失敗時にも観測されたため、この値だけでは今回の503を説明できない。** 成功した操作は実測できたが、このことを全許可設定の適用確認の代用にはしない。

unknownの生成条件や解消方法まで確定するには、状態取得APIの実装仕様または提供側の診断情報が必要。このセッションに公開されているツールには、その内部実装・中継ログ・強制再同期の取得操作がない。
