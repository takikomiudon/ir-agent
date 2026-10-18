# 適応型取得の頻度と503の途中比較

集計時点：2026-10-11T17:46:09.255200+09:00（日本時間）／2026-10-11T08:46:09.255200+00:00（UTC）。開始目標は 2026-10-11T06:12:06.589723+00:00。これは収集中の中間結果であり、全社の窓口を確認したという報告ではない。保存済みログだけを解析し、この比較作業の新GET・IR送信は0回。

collectorの実GETは合計 **2,932回**。別枠の診断は**12回**なので、合わせて **2,944回**。共通 `Invalid argument` 型503はcollectorで9件、診断で0件。HTTP 429は0件、保存応答のRetry-Afterは1件。初期30社・60社は共通503なしで完了し、続く取得では再発した。30分休止後の0.25 RPSの30社も共通503なしで完了し、現在は後続バッチを取得中である。

| 区間の開始（JST）・設定RPS | 会社の完了／選択 | 実GET | 200応答 | 共通503 | TLS等サイト503 | 通常503 | 429 | 状況 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 15:18:27／1 | 30/30 | 172 | 122 | 0 | 12 | 0 | 0 | completed |
| 15:26:03／2 | 60/60 | 341 | 258 | 0 | 16 | 0 | 0 | completed |
| 15:33:05／3→2.4→1.92 | 100/100 | 647 | 497 | 0 | 16 | 4 | 0 | completed |
| 15:44:39／1.92→1.536→0.768→0.384→0.25 | 82/100 | 497 | 394 | 3 | 17 | 2 | 0 | environment_stopped |
| 15:58:37／0.25 | 11/30 | 21 | 1 | 3 | 13 | 0 | 0 | environment_stopped |
| 16:15:03／0.25 | 15/30 | 28 | 1 | 3 | 16 | 2 | 0 | environment_stopped |
| 16:46:55／0.25 | 30/30 | 140 | 109 | 0 | 8 | 1 | 0 | completed |
| 16:56:18／0.25 | 30/30 | 143 | 109 | 0 | 8 | 1 | 0 | completed |
| 17:05:51／0.75→0.6 | 60/60 | 380 | 321 | 0 | 1 | 1 | 0 | completed |
| 17:17:28／0.35 | 60/60 | 372 | 292 | 0 | 2 | 0 | 0 | completed |
| 17:35:14／0.35→0.28→0.25 | 26/60 | 191 | 154 | 0 | 2 | 3 | 0 | running |

各collectorは4 workers。RPSの矢印は保存された減速履歴を示す。同じrunのprogressとfinalはfinalを優先して一度だけ数える。実GETにはrobots、redirect、接続確認の各送信を含む。200はこれらを含む応答数であり、IR窓口確認社数ではない。

集計内訳は初期90社の513 GET＋finalのあるwrapper実行2,228 GET＋実行中progressの191 GET。controllerの完了子実行累計2,228 GETはfinal側に含まれる観測なので再び加算しない。進行中の数字は今回読んだ各ファイルの観測時刻までで、後から増える。HTTP statusのない例外もあるため、応答数と送信数は一致しない場合がある。

## 保存された送信時刻から読める頻度

`http_get_started_at` はhost/globalの待機後、`requests.get` の直前に記録される。`http_response_received_at` はヘッダーを受け取って呼出が戻った時点で、ネットワークパケットや提供側の着信ログではない。

| 区間 | 時刻付き保存GET／collector実GET | 保存間隔からの平均RPS | 最小保存送信間隔（秒） | 1秒窓の最多保存送信 |
|---|---:|---:|---:|---:|
| 15:18:27／初期1 RPS | 162/172 | 0.595 | 1.000111 | 1 |
| 15:26:03／初期2 RPS | 334/341 | 0.938 | 0.500103 | 2 |
| 15:33:05／初期3 RPS | 622/647 | 0.901 | 0.333496 | 3 |
| 15:44:39／初期1.92 RPS | 482/497 | 0.900 | 0.520954 | 2 |
| 15:58:37／初期0.25 RPS | 21/21 | 0.247 | 4.000146 | 1 |
| 16:15:03／初期0.25 RPS | 28/28 | 0.246 | 3.999738 | 1 |
| 16:46:55／初期0.25 RPS | 138/140 | 0.246 | 4.000069 | 1 |
| 16:56:18／初期0.25 RPS | 138/143 | 0.241 | 3.999919 | 1 |
| 17:05:51／初期0.75 RPS | 366/380 | 0.609 | 1.333421 | 1 |
| 17:17:28／初期0.35 RPS | 355/372 | 0.334 | 2.857209 | 1 |
| 17:35:14／初期0.35 RPS | 184/191 | 0.280 | 2.857254 | 1 |

時刻付きの保存GETは計2,830件で、collector計数との差は102件。robotsキャッシュの再添付は送信時刻で重複排除した。平均は保存された送信間の件数と最初〜最後の時刻差、1秒窓は半開区間 `[t,t+1秒)`。これらは部分観測であり、安全な頻度や提供側の上限を示さない。JSONには10秒窓・各送信時の設定RPS・欠けた件数も残した。

以前の `retrieved_at` は待機前の呼出時刻だったため、旧8→24 workersの期間にこの計算法を遡及しない。[以前の比較](rate-comparison.md)と一次証拠は変更していない。

## 共通503の接続先と休止

共通トンネル503、TLS・証明書・connection termination由来のサイト別503、通常503を本文・failure signatureに基づいて分けた。以下は9件の共通503そのものの送信先で、原因となったサイトの断定ではない。

| 送信開始（JST） | 送信先 | robots／本文 | 送信時の設定RPS | 保存証拠 |
|---|---|---|---:|---|
| 15:53:28.893096 | www.startiaholdings.com | company body | 1.536 | [snapshot](../ir-contacts-universe-2026-10-11/evidence/3393/20261011T065247044216Z/05.json) `/` |
| 15:53:30.515017 | www.felissimo.co.jp | company body | 0.768 | [snapshot](../ir-contacts-universe-2026-10-11/evidence/3396/20261011T065312321015Z/02.json) `/` |
| 15:53:33.466891 | www.toridoll.com | company body | 0.384 | [snapshot](../ir-contacts-universe-2026-10-11/evidence/3397/20261011T065312688870Z/05.json) `/` |
| 15:59:49.477166 | www.csmen.co.jp | robots | 0.25 | [snapshot](../ir-contacts-universe-2026-10-11/evidence/3083/20261011T065934382879Z/01.json) `/robots` |
| 15:59:54.167291 | www.festaria.jp | company body | 0.25 | [snapshot](../ir-contacts-universe-2026-10-11/evidence/2736/20261011T065923494761Z/01.json) `/` |
| 15:59:58.326325 | www.shinyei.co.jp | company body | 0.25 | [snapshot](../ir-contacts-universe-2026-10-11/evidence/3004/20261011T065926009010Z/01.json) `/` |
| 16:16:44.574627 | www.toray.co.jp | robots | 0.25 | [snapshot](../ir-contacts-universe-2026-10-11/evidence/3402/20261011T071629174494Z/01.json) `/robots` |
| 16:16:48.822718 | www.kuraray.co.jp | robots | 0.25 | [snapshot](../ir-contacts-universe-2026-10-11/evidence/3405/20261011T071633582798Z/01.json) `/robots` |
| 16:16:53.261323 | progresstech-group.jp | company body | 0.25 | [snapshot](../ir-contacts-universe-2026-10-11/evidence/339A/20261011T071621091121Z/01.json) `/` |

15:53頃の3件を受けて5分休止し、0.25 RPSで再開した15:59頃にも3件が発生した。15分休止後の16:16頃は、東レ・クラレのrobotsとプログレス・テクノロジーズの本文に新たな3件が出た。神栄・フェスタリア・シーズメンの同区間の失敗はTLS系または通常503であり、「同じ3社だけに固定した共通障害」とは扱わない。

集計時点のcontroller状態は `collecting`、設定0.35 RPS、未処理2,732社、exhausted 13社。30分休止後の16:46:54 JSTに再開し、最初の30社は16:56:12 JSTに140 GETで完了した。現時点のcooldownは詳細JSONのcontroller_observationを参照。未処理数は通信回復対象の進捗であり、IR受付の有無を意味しない。

17:17:27 JST に調査側の試行上限を0.35 RPSへ変更した。直前の0.75→0.6 RPSバッチは60/60社・380 GET・共通503/429なしで自然完了し、既存wrapper/collectorの終了を確認して単一collectorを再開した。理論上は1260 GET/時だが、公開quotaや安全な頻度が判明したという意味ではない。現在バッチの数字は上表の進行記録の観測時刻までの中間値。

## 0.35 RPSの試行と後続バッチ

固定観測境界は2026-10-11T17:46:09.255200+09:00／2026-10-11T08:46:09.255200+00:00。各collectorは下表に示した保存済みprogress/finalの時刻までを集計し、その後の取得は含めていない。後続バッチは途中であり、完了バッチと分けて読む。

| collector開始（JST） | 完了／選択 | GET | 設定の推移 | 共通503 | TLS等サイト503 | 通常503 | 429 | 観測時刻（JST） |
|---|---:|---:|---|---:|---:|---:|---:|---|
| 17:17:28 | 60/60 | 372 | 0.35 RPS | 0 | 2 | 0 | 0 | 17:35:09.515362 |
| 17:35:14 | 26/60 | 191 | 0.35→0.28→0.25 RPS | 0 | 2 | 3 | 0 | 17:46:08.930401 |

0.35 RPSの完了バッチは60社・372 GETで、共通503と429は0。次のバッチの減速履歴は以下のとおり。`http_503` は個別接続先から得た通常503の分類で、共通 Invalid argument 型とは区別する。TLS等のサイト別503も上表で別に数えた。

- 17:37:25.817720 JST：`https://ir.rent.co.jp`／`http_503`を受け、子collectorが0.35→0.28 RPSへ減速。
- 17:45:24.885326 JST：`https://www.iij.ad.jp`／`http_503`を受け、子collectorが0.28→0.25 RPSへ減速。

固定観測のwrapper設定は0.35 RPSだが、稼働中の子collectorの最新保存設定は0.25 RPS。前者を現在の実送信設定と解釈しない。これらは調査側の制御設定と観測結果であり、後の増速・公開quotaの推定・安全閾値の確定は行わない。

[過去60分の固定観測](cap-observation.md)に、報告GET数・時刻付き保存数・origin数・欠測と、同一設定の送信間隔を整理した。

## 30分休止後の同じURL・異なるURLの比較

[復旧後30社のfinal](../ir-contacts-universe-2026-10-11/collection-runs/20261011T074655005552Z.json)は0.25 RPS・4 workers、30/30社・140 GET、共通503=0、HTTP429=0。以下は直前の16:16頃とこの完了バッチの保存送信を照合した結果であり、復旧の原因を確定する実験ではない。

| 接続先 | 休止前（JST） | 休止後（JST） | 比較の範囲 |
|---|---|---|---|
| プログレス本体 `https://progresstech-group.jp/` | 16:16:53／共通503 | 16:47:59／200 | 同じ本文URLの応答回復 |
| 東レ `https://www.toray.co.jp/robots.txt` | 16:16:44／共通503 | 16:47:51／302 | 同じrobots URLは302。転送先notfound.htmlは16:48:07にHTTP200だが本文は404 NOT FOUND |
| 東レ本体 `https://www.toray.co.jp/` | robotsの失敗で本文未取得 | 16:48:23／200 | robotsと本文は別URL。本文取得の復帰を確認 |
| クラレrobots | 16:16:48／`kuraray.co.jp/robots.txt` 共通503 | 16:48:27／`kuraray.com/robots.txt` 200 | ホストが異なる。旧co.jpの同一robots応答は今回の保存資料に残っておらず、同じURLの200とは扱わない |

各比較の実送信時刻・HTTP status・snapshot・JSON pointerは詳細JSONのrecovery_after_30_minute_cooldownに保存した。東レのrobots転送先のHTTP200をrobots.txtの200やIRフォームの確認に置き換えない。旧URLから新URLへのredirect・robotsチェック・会社本文はそれぞれ別のGETとして数える。時間、累積アクセス、休止、collectorの実装も変化しており、URLが一致しても中継cacheや内部状態まで同一とは確認できない。

## 0.25 RPSでの診断

16:08:42〜16:12:11 JSTの診断は単一collectorで、初回9 GET＋追加3 GETの合計12 GET。extended-summaryの12には初回9が含まれるので二重加算しない。

| 保存ケース | 対象 | 結果 |
|---|---|---|
| [ healthy_before ](../ir-contacts-universe-2026-10-11/diagnostic-runs/20261011T070842437298Z/01-healthy_before-3001.json) | 3001／company body target | HTTP 200 |
| [ suspect_robots ](../ir-contacts-universe-2026-10-11/diagnostic-runs/20261011T070842437298Z/02-suspect_robots-3004.json) | 3004／robots resource | HTTP 503／site_tls_503 |
| [ healthy_middle ](../ir-contacts-universe-2026-10-11/diagnostic-runs/20261011T070842437298Z/03-healthy_middle-3053.json) | 3053／company body target | HTTP 200 |
| [ suspect_robots ](../ir-contacts-universe-2026-10-11/diagnostic-runs/20261011T070842437298Z/04-suspect_robots-2736.json) | 2736／robots resource | HTTP 503／site_tls_503 |
| [ healthy_after ](../ir-contacts-universe-2026-10-11/diagnostic-runs/20261011T070842437298Z/05-healthy_after-3001.json) | 3001／company body target | HTTP 200 |
| [ healthy_after ](../ir-contacts-universe-2026-10-11/diagnostic-runs/20261011T070842437298Z/06-healthy_after-3053.json) | 3053／company body target | HTTP 200 |
| [ suspect_shared_signature ](../ir-contacts-universe-2026-10-11/diagnostic-runs/20261011T070842437298Z/07-suspect_shared_signature-3083.json) | 3083／robots resource | HTTP 503／http_503 |
| [ healthy_after_shared_signature ](../ir-contacts-universe-2026-10-11/diagnostic-runs/20261011T070842437298Z/08-healthy_after_shared_signature-3001.json) | 3001／company body target | 本文未取得（GET上限。redirect 302・robots 200のみ保存） |

神栄・フェスタリアのrobotsはTLS系503、シーズメンのrobotsは通常503だった。同時期の片倉・ペッパーフードの本文には200応答がある。最後の片倉ケースは本文GETをしていないため、本文200の成功例には数えない。これらは特定接続先による差を示すが、内部レート制限の存在を否定せず、共通503の内部原因も確定しない。

保存されたRetry-Afterは `0`（解析値0.0秒）、URL `https://www.asahi-kasei.com/jp/index.html`／HTTP301／[保存証拠](../ir-contacts-universe-2026-10-11/evidence/3407/20261011T074840237262Z/01.json) `/redirects/1`。0秒のredirectヘッダーであり、429応答や正の待機時間指定ではない。公開レートquotaとは扱わない。

## runtime状態・解釈の限界

15:41:53 JSTの成功期と16:22:39〜40 JSTの休止期に保存したruntime状態は、どちらもrevision 6／observed revision 6、observations current true、unrestricted／unknown、connected／running、failure nullだった。`unknown` だけでは成功と503を区別できず、policyがenforcedと判明した証拠としては扱わない。内部で何を意味するかも推測しない。

保存した429は0件、Retry-Afterは1件。Retry-Afterの値・対象・statusは詳細JSONの各runへ保存した。429がないことやヘッダーの有無だけでは、中継レート制限の有無を確定できない。通常503後の減速、共通503後の5／15／30分休止はcollectorの実装動作で、外部サービスの公開quotaではない。アクセス量・同時接続・共有経路・累積負荷・休止時間が影響する可能性は残る。接続先、時刻、遅延も違うため、RPS変更だけを切り離した実験ではなく、因果関係やCodex Cloudの公開閾値・安全なRPSは確定していない。

## 保存根拠

- [詳細JSON・重複排除したリクエスト証跡](adaptive-rate-comparison.json)
- [adaptive manifest](../ir-contacts-universe-2026-10-11/adaptive-runs/20261011T061206589723Z/manifest.json)（開始状態を保持）
- [診断 extended-summary](../ir-contacts-universe-2026-10-11/diagnostic-runs/20261011T070842437298Z/extended-summary.json)（原9＋追加3の12 GET）
- [controller progress](../ir-contacts-universe-2026-10-11/adaptive-runs/20261011T061206589723Z/progress.json)（wrapper内の累計。更新されるため今回読んだ値とSHAを詳細JSONへ保存）
- [controller events](../ir-contacts-universe-2026-10-11/adaptive-runs/20261011T061206589723Z/events.jsonl)（休止・再開履歴）
- [試行上限の切替](../ir-contacts-universe-2026-10-11/adaptive-runs/20261011T061206589723Z/rate-cap-transition.json)（完了後の停止・再開時刻と保存制御設定）
- [runtime状態 runtime-state-20261011T064153Z.json](evidence/runtime-state-20261011T064153Z.json)
- [runtime状態 runtime-state-adaptive-cooldown.json](evidence/runtime-state-adaptive-cooldown.json)
- [開始前の一次証拠の不変性検証](../ir-contacts-universe-2026-10-11/adaptive-runs/20261011T061206589723Z/baseline-evidence-integrity.json)（9,339 snapshot全一致、errors 0、GET 0）
- [collector 20261011T061827616992Z](../ir-contacts-universe-2026-10-11/collection-runs/20261011T061827616992Z.json)（final優先。集計値とSHAを詳細JSONにも保存）
- [collector 20261011T062603607402Z](../ir-contacts-universe-2026-10-11/collection-runs/20261011T062603607402Z.json)（final優先。集計値とSHAを詳細JSONにも保存）
- [collector 20261011T063305375549Z](../ir-contacts-universe-2026-10-11/collection-runs/20261011T063305375549Z.json)（final優先。集計値とSHAを詳細JSONにも保存）
- [collector 20261011T064439109210Z](../ir-contacts-universe-2026-10-11/collection-runs/20261011T064439109210Z.json)（final優先。集計値とSHAを詳細JSONにも保存）
- [collector 20261011T065837473521Z](../ir-contacts-universe-2026-10-11/collection-runs/20261011T065837473521Z.json)（final優先。集計値とSHAを詳細JSONにも保存）
- [collector 20261011T071503656332Z](../ir-contacts-universe-2026-10-11/collection-runs/20261011T071503656332Z.json)（final優先。集計値とSHAを詳細JSONにも保存）
- [collector 20261011T074655005552Z](../ir-contacts-universe-2026-10-11/collection-runs/20261011T074655005552Z.json)（final優先。集計値とSHAを詳細JSONにも保存）
- [collector 20261011T075618247918Z](../ir-contacts-universe-2026-10-11/collection-runs/20261011T075618247918Z.json)（final優先。集計値とSHAを詳細JSONにも保存）
- [collector 20261011T080551672765Z](../ir-contacts-universe-2026-10-11/collection-runs/20261011T080551672765Z.json)（final優先。集計値とSHAを詳細JSONにも保存）
- [collector 20261011T081728684344Z](../ir-contacts-universe-2026-10-11/collection-runs/20261011T081728684344Z.json)（final優先。集計値とSHAを詳細JSONにも保存）
- [collector 20261011T083514678887Z](../ir-contacts-universe-2026-10-11/collection-runs/20261011T083514678887Z-progress.json)（final優先。集計値とSHAを詳細JSONにも保存）

応答ヘッダーは既存実装のsafe whitelist項目だけを扱った。各リクエストは保存snapshot・JSON pointer・実送信時刻と対応し、robotsキャッシュの再添付を重複排除した。元の本文・ハッシュ・取得時刻、会社records、全社集計レポートはこの比較作業では変更していない。
