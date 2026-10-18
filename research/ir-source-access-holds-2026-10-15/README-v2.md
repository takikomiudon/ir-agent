# 収集保留索引 v2：保存済み6 exact host

[holds-v2.json](holds-v2.json) は旧 [holds.json](holds.json) の**5entryをJSON値としてそのまま保持**し、`www.xj-storage.jp`の保存robots停止根拠を1entry追加した。旧README・holds・validationは変更していない。今回の索引更新はGET・DB・code変更0で、実取得は別の[7525ローダー確認](../ir-case-studies-2026-10-15/7525/issuer-loader-followup/README.md)に属する。

| exact host | 保存された停止理由 |
|---|---|
| `contents.xj-storage.jp` | 旧entry：robots200のwildcard `Disallow: /` |
| `ssl4.eir-parts.net` | 旧entry：robotsのwildcard禁止 |
| `web.fisco.jp` | 旧entry：robots403で規則未確認。全path禁止本文・記事403とは別 |
| `sharedresearch.jp` | 旧entry：AI個別規則を受けたprojectの収集保留。実UAのliteral許可と区別 |
| `www.toyo.co.jp` | 旧entry：AI個別規則を受けたprojectの収集保留。実UAのliteral許可と区別 |
| `www.xj-storage.jp` | **新entry**：robots200・26bytes、wildcard `Disallow: /`。データGET0で停止 |

新しいrobots URLは `https://www.xj-storage.jp/robots.txt`、受信完了は **2026-10-15T11:09:53.720443UTC**。宣言／prepared request UAは`Codex-IR-Research/0.1`で、独立wire確認とはしない。captureの正確JSONpath、原raw・SHA・bytes、全原文とoffset、明示データ要求URL、2GET（許可された会社host JS1＋datahost robots1）とdata0停止を結び付けた。未使用1GETを別path/hostや実行回避へ回していない。

```text
User-Agent: *
Disallow: /
```

新www entryの原raw SHA `7ea4052aea20413007bfc2686ba0ad7276882075c2606c86a9e6b08742b3a4ca` は旧contents entryと一致するが、**取得URL・origin・capture・時刻は別**。同じバイトだから同じhostとしたり、片方のアクセス条件を他方の根拠にしたりしない。

workerは追加取得前にexact hostを照合し、保存根拠を再利用する。停止済みrobots/targetの自動再GET、UA変更、別経路・JS実行・診断による回避は行わない。これは保存時点の収集制約であり、他subdomain・現在以後の恒久禁止・企業の投資除外ではない。利用者のドメイン許可はサイトrobots確認を免除しない。以前の取得・分類や許可された会社host JSを後付けで無効化しない。

[validation-v2.json](validation-v2.json) に16有限チェック成功、不一致0、旧3ファイルと固定済みloader成果の不変を保存した。旧5entryの原点検は旧validationを再利用し、この版で全て再実行したとはしない。本索引はruntime guardの追加実装ではなく、入口で参照する研究記録である。
