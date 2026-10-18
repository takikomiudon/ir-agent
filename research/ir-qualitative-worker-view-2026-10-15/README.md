# 定性worker向けの固定入力表示

実際の1980レビューpacketは185,844 UTF8 bytesで、case snapshotだけで141,514 bytesだった。引継ぎの同じmanifest全文がfilesとbootstrapで重複していた。原packetを維持したまま、worker向け表示を明示的に選べるようにした。

```bash
.venv/bin/ir-agent --db PATH packet JOB_ID --view qualitative-worker
```

無指定のpacket表示は従来どおり。新しい表示は、元packetのSHA、会社と論点、元case文書全文、新規source全文とSHA、既読sourceと根拠fileの参照、管理日と引用を保持する。同じmanifest全文の反復は参照へ置き換える。文章をLLMで要約して意味を落とす処理ではない。原packetの各file本文は引き続きfull表示で確認できる。

この投影は閲覧用で、現在の完了権限は`not_checked`。過去jobも当時のcaseを表示し、現在のcase・ファイルの状態へすり替えない。完了時のlease・世代・原典・case版の検証は既存処理へ委ねる。intakeや金融jobには適用せず、誤ったkindを拒否する。DBや外部ファイルを書き換えない。

[実資料のread-only点検](actual-worker-view.json)では、同じ元case文書と新規sourceを保持し、185,844→50,444 UTF8 bytes（72.86%減）だった。実DBのSHAも不変。これは1packetのbyte数で、token数・LLM精度・実行時間・対象企業数の処理能力を測定した結果ではない。

根拠は既存の固定packet契約と、Anthropic thesis-trackerの構造化保存・簡潔な出力原則。[設計](design.json)に適応範囲を固定した。表示形式はプロジェクトの実装であり、投資方針や著者の売買規則ではない。

5つの新規テストで、原source・case全文・hashの維持、bootstrap参照の維持、投影の変更が原packetへ波及しないこと、過去表示、別kindの拒否とCLIを確認した。[全1,405件・37.213秒成功](full-suite.json)を[ログ](full-suite.log)と[受入](parent-acceptance.json)へ保存した。実DB117資料のSHAは不変。新GET・金融条件採用・実IR・注文は0。独立agentコード点検は未完了。
