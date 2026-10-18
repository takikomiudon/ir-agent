# 独立review後の最小修正01

主担当から再現済みとして届いた2件を修正した。供給済みquote価格は部分quoteでも正・有限を先行検査し、position/policy不足の早期returnで0/負値/非有限値を隠さない。原raw sourceをSHA/receiptのためそのまま保持し、metadata/requires_research等の既定値が必要な価格・金融計算には別のvalidated copyを渡す。raw IRのmetadata省略はmissing reply identity理由へ進み、KeyErrorにしない。旧pureのearly-returnや数値方針は変更していない。

[修正receipt](fix-receipt.json)、[修正前完全bytes](before-files.json)、[focusedログ](focused-tests.log)を保存した。新3回帰を含む32件が成功し、正常なraw market content内の価格/観測pathsを使ってbuy_reviewを保存でき、原snapshot/receipt/SHAが不変であることも確認した。全入力は架空、memory/temp DBのみ。

元integrationのimplementation.json/ログを過去の版として保持した。独立reviewは継続中で、この修正の再確認とfull suiteは主担当待ち。実運用DBアクセス/書込み・network・外部送信/注文は0。
