# 保存来歴と過去の仮説表示

全1056テスト成功（34.052秒）。後から保存した返信評価が、以前のas-ofの仮説・daily packetを変える不備を修正した。[別担当による再確認](independent-recheck.json)で17:30の仮説v1・job ID・packetが不変で、明示したretrospectiveだけv2を選ぶことを確認した。元の未修正再現は別の研究ディレクトリで保持する。

source/thesis/reply/questionの元JSONを変更せず、初回INSERTと同じtransactionで保存来歴を記録する。strict PITは対象時点とDB存在の締切を等しくし、全原典DAGも確認する。retrospectiveは二時刻・modeを明示したread-only表示で、通常のjobへ渡さない。旧DBの現在表示は保持し、過去の保存不明・時計異常・不正な申告日時を保留する。

実DBには保存来歴tableを追加し、既存28sourceの今回の存在観測のみを保存した。全28件のfirst_saved_atはnullで、過去の初回保存を推測していない。元source JSON群の前後hash一致を確認。1,819社、28分類、仮説/質問/実予測/送信/注文0件を維持する。

[原ログ](tests.log)、[実来歴](actual-availability-receipts.json)、コードhashと3架空demoを保存した。質問状態などの可変履歴、pure計算へのcaller snapshotの当時存在、投資判断の有効性を完全再現した意味ではない。次は返信後の判断表示の価格鮮度を、申告評価日時と実保存時刻で点検する。
