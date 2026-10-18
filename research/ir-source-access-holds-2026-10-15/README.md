現在の索引は[v5・9 exact host](README-v5.md)。以下は旧v4時点の記録を保持する。

最新の収集保留は[v4・8 exact host](README-v4.md)。旧v3の7entryを保持し、data.swcms.netのrobots403を規則未確認として追加した。以下は初回索引の履歴。

# 保存済み収集保留の索引：5 exact hosts

後続workerが同じ停止経路を再要求しないため、保存済みcapture/rawだけから索引を作成した。**新GET・DBアクセス・既存file変更・runtime/Fetcher変更は0**。これは読み取るための研究artifactであり、コードに接続された自動ガードではない。

| exact host | 保存時の根拠 | 次の取得への扱い |
|---|---|---|
| `contents.xj-storage.jp` | 1332 longterm、robots200、wildcard `User-Agent: *` / `Disallow: /` | 保存された規則により保留。PDFへのHTTP前に停止。 |
| `ssl4.eir-parts.net` | 1379 annual、robots200、wildcard `User-agent: *` / `Disallow: /` | 保存された規則により保留。feed/PDFへのHTTP前に停止。 |
| `web.fisco.jp` | 1827 external、robots**403**、118bytesのHTML Forbidden | 規則は未確認のまま保留。wildcard禁止でも記事本文403でもない。 |
| `sharedresearch.jp` | 1721 external、robots200、wildcardは字義上許可だがChatGPT/GPTBot/ClaudeBot等の個別全面禁止 | custom UAへのwildcard許可をAI取得許可へ一般化しないproject hold。 |
| `www.toyo.co.jp` | 8151 annual、robots200、wildcard Allow /とGPTBot/ClaudeBot/Claude-SearchBotへの個別全面禁止 | 同じproject hold。短信入口/PDFには進まず停止。 |

`holds.json`に各rawの元path/SHA256/bytes、HTTPstatus、開始・ヘッダ受信・本文完了時刻、task申告UA、原文quoteと文字/byte offsetを保存した。1332/1379の旧capture `retrieved_at`はrequest開始なので、本文完了`completed_at`と別に保持する。元artifactを書き換えて補正していない。Content-LengthはHTTP符号化側の宣言であり、特にgzip復号後の保存entity bytesと同じだとは扱わない。

`validation.json`は全5raw・19原文引用・元input19件のSHA不変を点検し、UA設定7引用も原文offsetとproducer全fileSHAとともに保持する。一部producerは/tmpにあり消え得るが、必要な設定部分はこの索引に保存済み。producerの再実行/コピー実行はしていない。task申告と`requests`のheader設定は一致する一方、実際のwire/per-response request headerは保存されておらず、独立通信検証済みとはしない。

## Workerの使い方と境界

1. 取得前に宛先の**exact hostname**を照合し、該当すれば既存根拠を再利用してholdを返す。robotsや本文の「念のため再試行」、UA変更、JS/ブラウザ、別host・転載・proxy経路での回避を行わない。別途明示された有限の再検討以外で、再取得・接続診断へ展開しない。
2. 環境で利用者がドメインを許可していても、それはサイトrobots確認を免除しない。ネットワーク許可/到達性とサイト側制約・project holdを別に扱う。
3. 保存時点の観測である。現在の全pathアクセス・他subdomain・他domain・永久禁止を確認したとは主張しない。wildcard Disallow /が観測されたことと、全pathのHTTP拒否を実測したことも別。
4. SharedResearchはrobots200→本文200の後にAI個別禁止の保留を記録した経緯を維持する。今回の索引でその過去raw/本文/分類を後付けで変更したり、旧取得時にこの新しいholdが実行済みだったとしない。他hostの古い別取得にも遡及しない。
5. 収集制約は投資対象の除外ではない。会社の質・予測精度・評価額・IR適格性・買い/売り判断へ変換しない。今回財務値/予測/IR質問は作成していない。

規則の種類を保ったまま止めることが目的であり、取得エラーの原因診断やネットワーク設定の変更を行う索引ではない。
