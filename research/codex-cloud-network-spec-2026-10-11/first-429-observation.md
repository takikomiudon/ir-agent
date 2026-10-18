# 調査再開後に初めて観測した429

2026年10月11日20:45:24.564059 JST、`https://www.lancers.co.jp/robots.txt` のGETが429を返した。取得開始時の設定は0.25 RPSで、応答は0 bytes、`Retry-After`の指定はない。`Server: envoy`は正常応答にも現れるため、サイト側と中継側のどちらが制限したかは特定できない。

robots取得を停止し、同サイトのページ本文GETは行っていない。受付拒否や窓口不存在という判断には使わない。wrapperはこの区間が終了した後に最低5分の休止を行い、待機時間の指定があれば延長する実装である。この観測時点で休止が完了したとは記録しない。

429は制限を示す追加観測だが、以前の共通503 `Invalid argument|remote address:envoy://cloudflare_https_tunnel/` と同じ原因だと示す証拠はない。直前の完全60分窓や同一URLの503/200比較は、各資料に記載した固定時刻の観測として維持する。

この確認による追加GETとIR送信は0件。原snapshotは変更していない。

- [元の保存記録](../ir-contacts-universe-2026-10-11/evidence/4484/20261011T114509049587Z/01.json)
- [取得時刻・ヘッダー・原資料SHA](first-429-observation.json)
- [後から確認した5分間の休止・再開](first-429-cooldown-observed.md)
- [503と正常時の比較](503-case-summary.md)
