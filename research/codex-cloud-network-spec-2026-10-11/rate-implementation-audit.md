# 収集実装とレート制限仮説のオフライン監査

監査時点：2026-10-11 06:00 UTC。新GET・再試行・設定変更・コード変更は0。対象は現行の `scripts/research_ir_universe.py` と保存済み証拠。スクリプトのSHA-256は `4669f4d457dcb55fcd17106666860f14b3933c2446ca5ea276a4fb930ee73e75`。

並行数8→24は、異なる接続先を合算したHTTP頻度や同時接続数を増やし得る。全体のRPS制限は実装されていないため、レート制限は検討可能な仮説である。ただし、今回の503の根本原因がレート制限であること、また8→24への変更が原因であることは保存情報だけでは確定できない。

## 1. `retrieved_at` の意味

| 項目 | 実装と読み方 |
|---|---|
| HTTP証拠の `retrieved_at` | [`Fetcher.raw_get` の184行](../../scripts/research_ir_universe.py#L184)で、結果辞書を作るときに設定する。その後に回路チェック、host lock、間隔待機、HTTP送信、本文読取がある。**呼出開始側の時刻であり、実際のHTTP送信時刻でも本文取得完了時刻でもない。** |
| 実HTTP送信 | 現行209行の `requests.get`。送信直前・応答ヘッダー受信・本文読取完了の個別時刻は保存しない。 |
| 会社単位の時刻 | `investigation` の420行で `attempted_at`、518行で `completed_at` を設定する。会社内のrobots、間隔待機、redirect、複数ページ、解析・証拠保存を含み、個々のHTTP時間ではない。 |
| ローカル停止の時刻 | `raw_get` の187行や `capture_one` の275行でも日時付きの結果を作る。HTTPを実行していないものにも `retrieved_at` がある。 |
| redirect・robotsの時刻 | `capture` は最終ホップの辞書を返し、`requested_url` を最初のURLに戻す。中間ホップは `redirects` に残る。robotsはキャッシュされ、後の証拠に同じ取得済みrobotsを再添付するため、会社ごとに新GETがあったとは解釈しない。 |

例として、[1720の保存証拠](../ir-contacts-universe-2026-10-11/evidence/1720/20261011T044640963269Z/01.json)では、同じoriginのrobotsの時刻が `04:46:40.963346`、本文の時刻が `04:46:41.744818` UTCで、差は約0.781秒。この差から「1秒間隔を破った」とは言えない。本文側の時刻は間隔待機の前に付く。会社の完了は `04:46:42.718117` UTCだった。

## 2. workers・ホスト間隔・追加GET

| 制御 | 具体的な範囲と制約 |
|---|---|
| workers | [`main` の738行](../../scripts/research_ir_universe.py#L738)のThreadPoolExecutorは会社の調査単位を並行化する。各workerのGETは同期式なので、8→24はこの収集プロセスの同時企業処理枠を3倍にする。実RPSや総GET数が3倍になったという意味ではない。応答時間、待機、ページ数、同一originの競合によって変わる。 |
| origin単位の直列化 | `raw_get` の181行で `scheme://netloc` をキーにし、190行でlockを取る。厳密にはドメイン単位ではなくorigin単位で、http/https、ポート、www有無が違えば別枠になる。 |
| origin単位の間隔 | 164行の既定 `delay=1.0` と、194行・206行の `next_allowed` により、同originではGET開始の間隔を1秒以上にする。レスポンスの本文を読み終わるまで同じlockを持つため、遅い応答ではそれより長くなる。 |
| robotsの間隔 | `capture_one` の267行で `RobotFileParser.crawl_delay(USER_AGENT)` が返す値を取り、既定値より大きい場合に採用する。パーサーが返さない指定・Request-rate等まで包括的に実装した制御ではない。 |
| 全体の上限 | 全originを合算したRPS、短時間のburst、共有proxyへの同時接続数を別に制限するtoken bucket等はない。worker数は当該プロセスの並行枠。別agent、別プロセス、curlや接続確認のGETとの合算制御もない。 |
| 実行区間の切替 | 8worker区間を止めて24workerで起動し直すと、`main` の707行で新Fetcherを作る。origin間隔、robotsキャッシュ、denied、障害origin集合はプロセス内の値なので、次区間では初期化される。 |
| robots GET | `capture_one` の253行で、初めて使うoriginの `/robots.txt` をGETする。robotsのredirectを最大5回追うので、robots確認自体は初回を含め最大6 GET。キャッシュの未登録確認と取得は一つのlock内で完結しないため、同originを複数workerが初めて使う際には重複したrobots GETが起こり得る。 |
| 本文redirect | `requests.get` は209行で `allow_redirects=False`。`capture` の287行が最大8ホップを手動追跡し、各targetでrobotsを確認する。外部フォーム等の別originへ移ると、そのoriginのrobots GETも追加される。 |
| ページ上限 | `investigation` の432行の `max_pages=7` は論理的なcapture回数の上限であり、実HTTP数の上限ではない。redirectなし・同originだけでも、robots未取得なら本文7回にrobots1回が加わる。preflightも別に1 GETある。 |

GETごとにトップレベルの `requests.get` を使い、調査全体で長く共有するSessionは作っていない。HTTP頻度に加えて接続確立の負荷・共有proxyの資源制限も候補になるが、実際の接続数やproxy内部の再利用はこの証拠では測定していない。

## 3. 429・503と回路停止

| 応答 | 実装上の扱い |
|---|---|
| 401 / 403 / 429 | [`raw_get` の221行](../../scripts/research_ir_universe.py#L221)でそのoriginをdeniedへ追加し、以後の同origin GETを停止する。robotsで返った場合は275行で本文GETも止める。Retry-Afterを読んだ再試行、指数backoff、429に基づく全体RPSの調整は行わない。 |
| 通常の503 | 同originをdeniedにしない。503というstatusだけで全体を停止しない。TLS_errorやconnection terminationなどの別の503と、今回の共通エラーを区別する必要がある。 |
| 共通503 | 238行の条件は、status503かつ本文に `Invalid argument\|remote address:envoy://cloudflare_` があること。該当する**異なるoriginが3つ**になると242行で共有Eventを立てる。同じhostnameでもscheme/port違いは別origin。失敗originはrun内で累積し、成功が間にあってもリセットしない。 |
| 回路判定の意味 | 3originは収集コードが共通障害へのアクセスを止めるために定めた閾値である。提供側のレート上限・許容量を発見した値ではない。robotsのGETもこの判定に入る。ProxyError等の例外や一般的な503は、このstrict条件によるglobal回路判定とは別。 |

保存された再試行の流れは以下の通り。時刻はいずれも送信前に付けた `retrieved_at`、またはmanifestの操作記録である。

- [manifest](../ir-contacts-universe-2026-10-11/runs/20261011T044639285379Z/manifest.json)：8workerで229社を保存後、`04:50:46.493871` UTCに一旦停止し、残る3,179社を24worker区間へ移した。
- [2回目のJPX preflight](../ir-contacts-universe-2026-10-11/network-healthchecks/20261011T045047358210Z.json)：`04:50:46.955077` UTC、HTTP200。
- [2760の外部Euroland証拠](../ir-contacts-universe-2026-10-11/evidence/2760/20261011T045047804438Z/04.json)：`04:50:54.429699` UTC、共通Invalid argument型503。保存されたretry証拠内では、この型の最も早い呼出開始時刻だった。
- [291Aのrobotsと本文](../ir-contacts-universe-2026-10-11/evidence/291A/20261011T045057513498Z/01.json)、[2908の本文](../ir-contacts-universe-2026-10-11/evidence/2908/20261011T045052664997Z/02.json)等でも同じ本文を保存。原応答のSHA-256は `971f01aae81a63c435e602a1a728c8894b1527150a621d70d735aaca6ff930ea` で一致する。
- [3001の証拠](../ir-contacts-universe-2026-10-11/evidence/3001/20261011T045058556276Z/01.json)：`04:50:58.556302` UTC、HTTP statusなし・`environment_circuit_breaker_open`。企業へのHTTP応答ではない。
- [再試行summary](../ir-contacts-universe-2026-10-11/runs/20261011T044639285379Z/summary.json)：更新3,408社のうち本文GET試行255社、成功本文244社、GETなし回路停止3,145社、本文GET前のpolicy停止8社。回路停止の大量レコードをHTTP頻度に数えてはならない。

8worker区間にも、前述の1720等でTLS_error型503がある。それらは共通Invalid argument型とは異なる。現在保存されている全社調査の `evidence/` 内のJSONを検索した範囲では、literalな `"http_status": 429` は0件だった。**429が保存されていないことは、proxy側のレート制限が存在しない証明にはならない。**

停止後の[単発curl観測](runtime-observation.json)でも同じInvalid argument型503が出ている。これは障害状態が単発アクセスでも継続していた証拠だが、その状態を作った原因や、冷却時間で解除される種類の制限かどうかは分からない。

なお現行コードは、この収集後に未着手futureのキャンセル、実GET前に停止した会社の旧レコード保持、host lock・間隔待機後の回路再チェックを追加した。今回の過去レコードを、この事後修正で作ったログとして解釈しない。新しいGET試行カウンタも過去の完全な送信ログを後付けで復元するものではない。

## 4. レート制限の確定に不足する情報

| 不足する観測 | 判断への意味 |
|---|---|
| 提供側のquota仕様・適用状態・throttleログ | proxy、環境、IP、利用者等のどの単位に上限があり、当該時刻にそれを超えたかを確認する必要がある。現在は内部ログを取得していない。 |
| 応答ヘッダー | 収集コードはContent-Type・charsetとredirect用Location以外のヘッダーを保存しない。Retry-After、RateLimit/X-RateLimit、Server/Via、request-ID等が不足しており、503の生成元・制限時間・リクエストの照合ができない。 |
| 実送信・受信・完了時刻と待機時間 | `retrieved_at` だけでは実RPS、同時HTTP数、first-byte latency、停止Eventが立った厳密な時刻を再構成できない。robots・redirect・例外も含む各GETの時刻が必要。 |
| 共有経路を使う全処理の合計 | 今回のworker処理だけでなく、他agentや接続確認、別プロセスのGETも同じ通信経路を使い得る。完全な合計数・connection数は未観測。 |
| 条件を揃えた比較 | 8workerと24workerの区間は接続先、処理ページ、経過時間、累積利用量、キャッシュ、環境状態も異なる。並行数だけを変えた比較ではない。 |

時間を空けた低頻度の単発GETは、**その時点の回復・継続障害**を確認する用途に適する。成功した場合も、冷却による制限解除、通信設備の回復、policy反映などを区別する追加根拠は必要であり、レート制限と確定しない。大量の負荷試験や連続再試行を、この原因調査の前提にはしない。
