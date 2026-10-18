# 次の定性packetへ前回観測を固定する

元のcaseを保持しつつ、次のworkerが前回の観測を読めるようにした。新しくqueueするpacketは、直前に完了した定性jobのsummary・case observation・元sourceのsnapshot SHA・結果SHA・日時を`prior_review`へ固定する。Anthropic thesis-trackerの更新ログを研究段階へ適応し、後から得た事実を当初の著者条件へ書き換えない。

前回jobは同一case/論点/versionの完了結果であり、時刻と既読sourceのhashが対応することを確認する。変更された前回結果は新しいclaimを拒否し、参照不正はそのcaseだけを保留する。worker表示は凍結されたprior_reviewを読むため、後でDBが変わっても表示を置き換えない。前回の観測も命令や投資判断の正解として扱わない。

旧packetはそのまま。prior_reviewがなかった場合は`not_in_legacy_packet`と表示し、現在の結果から過去のpacketへ補完しない。元case・旧source・金融処理・case版を移行する機能ではない。

新規4テストを含む全1,409件が成功（unittest39.328秒）。[ログ](full-suite.log)・[時刻/SHA](full-suite.json)と受入を保存。検証中の実DB121資料はSHA不変。1980と5831の実完了結果も[read-onlyで参照照合](actual-prior-reference-check.json)し、case v2・前回結果SHA・sourceの対応を確認した。新しい実jobを作ったり過去packetを書き換えたりしていない。独立agentによるコード点検は未完了。金融条件の採用・実IR・注文・新GETは0。
