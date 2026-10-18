# 旧daily/intakeへ新規だけの起票を追加

旧daily/intakeは同じtriggerのjobをselectedへ再表示する契約だった。小さい上限で定期実行すると、先頭の未完了jobを再表示し続け、後続会社を新しく起票できない場合がある。旧selectedの意味と固定packetを保持するため、新しい`--new-only`を明示指定する方式を追加した。

```bash
.venv/bin/ir-agent --db PATH intake --new-only --limit 10
.venv/bin/ir-agent --db PATH daily --new-only --limit 10
```

このmodeでは、現在の同一signatureを持つjobをstatus付きskippedへ返し、新しい候補だけにlimitを適用する。selectedとjobs_createdは今回の新規jobを表し、deferred_countは新規候補の繰越件数となる。既存jobのpacket、優先順、会社単位lease、世代や再送receiptは変更しない。superseded jobを再有効化するmodeではない。

無指定の返り値・再表示契約は従来どおり。APIは`Harness.daily(..., new_only=True)`／`Intake.queue(..., new_only=True)`。boolean以外を拒否する。3社・上限1の連続呼出しでa→b→c→新規0を確認し、既存packetの不変と旧modeの再表示も点検した。

3つの新規テスト（両API・両CLI・型）と全1,400件が成功、unittest37.961秒。[全件ログ](full-suite.log)・[時刻とSHA](full-suite.json)・[受入](parent-acceptance.json)に保存。検証中の実DB117資料はSHA不変。独立agentコードレビューは未完了。新規ネットワーク、金融条件の採用、実IR、注文は0。
