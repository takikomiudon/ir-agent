# アンリツの公開2資料を保存・分類

会社のQ1決算説明資料と公開Q&Aを実DBへ追加し、同じ1つのintake jobのattempt 1で分類を完了した。原資料の独立点検後に取り込み、[実行記録](actual-import.json)と保存済みpacket・要求receiptを保持する。分類は財務内容の存在の確認であり、予測・評価入力の検証ではない。

保存資料は100（公開99・市場1）、公開資料あり15社・財務内容あり14社。分類99、完了intake38、attempt35/events70/要求receipt35。能力計測は分類leaseに限定される。source来歴はlegacy28/trusted72、[read-only coverage](coverage-after-import.json)を保存した。

初回の処理では2資料の追加とqueue/claim後、主担当がclaim応答をpacketと取り違えた。確認中も応答のjob_idをidと取り違えたため、保存されたjobを直接取得し、同じattempt 1を完了した。誤りを隠して処理時刻を付け直さず、実sourceのfirst-save receiptと履歴を保持した。

旧98source、旧97分類、全1,819社の会社metadataは不変。現行schemaの保有申告receipt tableを作成したが実申告0、thesis・質問・返信・policy採用も0である。coverageのheld falseは台帳metadataであり実保有確認ではない。実行前backupはGit対象外data内。外部送信・注文は0。
