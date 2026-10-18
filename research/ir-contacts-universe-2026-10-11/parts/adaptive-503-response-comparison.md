# 保存済み503/200の応答比較

調査日: 2026-10-11T08:07:42.548328+00:00。既存の証拠だけを読んだメモ。新規GET、設定・コード・企業records・原証拠の変更は0。ヘッダーは既存の安全な保存対象だけを使用。

339Aの同じ公式トップは、失敗時と回復時の両方でdispatch設定が0.25 RPSだった。休止後に企業HTMLの取得が回復した事実は確認できるが、瞬間の設定RPSだけで成否の違いを説明できない。証明書検証エラーは同じ休止後にも残り、共通Invalid argument型と分ける必要がある。

| 保存例 | 実GET開始（JST、2026-10-11） | HTTP / classifier signature | 設定RPS | 全取得所要時間 | 本文 | 保存したServer / Via |
|---|---|---|---|---|---|---|
| C1: 339A 公式トップ・共通障害 | 16:16:53.261 | 503 / common_transport_503 | 0.25 | 0.167秒 | 215 bytes、text/plain | envoy / なし |
| C2: 339A 同一トップ・回復 | 16:47:59.900 | 200 / なし | 0.25 | 0.764秒 | 16490 bytes、text/html | envoy / 1.1 21c13e694345b80cbdf4d13b60011712.cloudfront.net (CloudFront) |
| T1: 1758 robots・休止前TLS障害 | 16:15:19.657 | 503 / site_tls_503 | 0.25 | 1.023秒 | 216 bytes、text/plain | envoy / なし |
| T2: 1758 同一robots・休止後TLS障害 | 16:47:11.006 | 503 / site_tls_503 | 0.25 | 0.762秒 | 216 bytes、text/plain | envoy / なし |

`Server: envoy` は共通503、TLS503、正常200のすべてで保存されている。そのヘッダー単独で障害や制限を示すとはいえない。C1の共通503本文は次の原文で、東レのrobots503にも同じ215-byte SHA-256 (`971f01aae81a63c435e602a1a728c8894b1527150a621d70d735aaca6ff930ea`) が保存されている。

> upstream connect error or disconnect/reset before headers. reset reason: remote connection failure, transport failure reason: immediate connect error: Invalid argument|remote address:envoy://cloudflare_https_tunnel/

Envoyの上流接続失敗を報告し、`envoy://cloudflare_https_tunnel/` を含むため中継の接続経路で生成された失敗を示唆する。企業固有のHTMLや明示的な制限通知は保存されていない。C2は公式社名を含むHTMLで、`Via: ...cloudfront.net (CloudFront)` が保存されている。接続経路から企業/CDNの応答を受け取れたことと整合するが、どの内部コンポーネントが復旧したかは分からない。

T1/T2の失敗本文は休止前後で同じ216-byte SHA-256 (`b5b660bc2bb92e97199b4b045f7e21eca39307fa087b8be85bb006cc7d83b34b`) のまま。原文は次のとおり。

> upstream connect error or disconnect/reset before headers. reset reason: remote connection failure, transport failure reason: TLS_error:|268435581:SSL routines:OPENSSL_internal:CERTIFICATE_VERIFY_FAILED:TLS_error_end

253Aのrobotsでも同じ本文・SHA・`site_tls_503` が休止前後に保存されている。これは`CERTIFICATE_VERIFY_FAILED`を報告するTLS接続失敗で、共通Invalid argument型とは文言が違う。classifier名は本文に基づくプログラムの分類であり、証明書チェーン・信頼ストア・中継側設定のどれが原因かはこの記録だけでは特定できない。新しいT2では上位の本文ページは`robots_unreachable_stopped` / `http_get_attempted:false`なので、公式トップに新たな503が返ったと数えない。

4例の保存ヘッダーに`Retry-After`・`RateLimit`・`X-RateLimit`系はない。共通障害直前のrunも休止後のrunも`http_429_count=0`だった。明示的なレート制限の通知は観測されていないが、通知しない中継側の割当・時間窓・遮断を否定する情報でもない。`Invalid argument`だけでRPS上限、アカウント/IP単位の割当、必要休止時間、内部ソケット状態を確定できない。休止、以前の累積負荷、当時の経路状態などを固定した比較実験にはなっていない。

時刻には`http_get_started_at` / `http_response_received_at` / `http_get_completed_at`を使う。C2のnested robots404は実GET開始07:47:43.899UTCに対しHTTP `Date: Sun, 11 Oct 2026 07:16:37 GMT`で、休止前の404と同じDate・本文SHAだった。キャッシュされた応答と整合するが、保存ヘッダーだけではキャッシュの内部状態は確定できない。HTTP Dateを新たな通信実施時刻として使わない。

東レの回復後robotsは、元の`/robots.txt`が07:47:51.899UTCにHTTP302で`/notfound.html`へ遷移し、遷移先が07:48:07.900UTCにHTTP200・title `404 NOT FOUND | TORAY`だった。元URLが直接robots200になった観測でも、robots規則の存在を実証する観測でもない。東レ公式トップ自体は別の実GETでHTTP200を取得している。

保存証拠（partsからの相対リンク）:

- [C1: 339A 公式トップ・共通障害](../evidence/339A/20261011T071621091121Z/01.json)。JSON対象: $。
- [C2: 339A 同一トップ・回復](../evidence/339A/20261011T074727705096Z/01.json)。JSON対象: $。
- [T1: 1758 robots・休止前TLS障害](../evidence/1758/20261011T071504156895Z/01.json)。JSON対象: $.robots。
- [T2: 1758 同一robots・休止後TLS障害](../evidence/1758/20261011T074655414885Z/01.json)。JSON対象: $.robots。
- [東レ 共通503と同一本文](../evidence/3402/20261011T071629174494Z/01.json)。JSON対象: $.robots。
- [東レ 回復後の302→notfound.html200と公式トップ200](../evidence/3402/20261011T074735548577Z/01.json)。JSON対象: $.robots.redirects[0]、$.robots、$。
- [253A TLS503休止前](../evidence/253A/20261011T071532437960Z/01.json) / [休止後](../evidence/253A/20261011T074711775468Z/01.json)。JSON対象: $.robots。
- [共通障害run](../collection-runs/20261011T071503656332Z.json) / [休止後run](../collection-runs/20261011T074655005552Z.json)。
