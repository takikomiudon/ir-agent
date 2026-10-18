# 定性jobの起票上限と既存jobの扱い

明示した2caseを`limit=1`で繰り返し起票すると、最初のcaseの同一triggerが毎回先頭枠を占め、2番目が進まなかった。新規jobを数える前に候補列を切っていたためで、17件中1件の回帰テスト失敗として再現した。[変更前コード](before-qualitative_research.py)と[再現記録](reproduction.json)を保持する。

候補を優先順に点検し、既存jobはskippedへ返してから、新規jobだけに上限を適用する。deferred_countも上限で繰り越す新規候補だけを数える。二度目は後続caseを1件作成し、三度目は新規0・繰越0・既存2になることを確認した。起票順や投資方針・会社単位lease・原典条件は変更していない。

[定性17件](focused-tests.log)と全1,397件が成功（unittest38.907秒）。[全件ログ](full-suite.log)・[時刻/SHA](full-suite.json)を保存した。検証中の実DBは117資料のままSHA不変。独立agentによるコード点検は未完了で、親による再現・修正・テストの受入範囲である。実IR・注文・ネットワーク・実DB変更は0。

この修正は`qualitative queue`の新規job上限である。既存の`daily`/`intake`は起票済みjobもselectedへ返す別の既存契約で、当該APIの意味を黙って変更していない。日次の呼出し側では選択済みと新規作成を区別する必要がある。
