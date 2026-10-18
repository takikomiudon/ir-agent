# v40のread-only接続確認

新しいdisclosed-fact-index-v40.jsonは33社・240項目・48親・50派生・41会社/原典ペア。旧v39の45親234項目はwhole同一、全240項目の索引内フィールドは各解決先に一致。v39 actual全体は別historyへwhole保存。8331/9702の2派生7項目は対象外のまま。

root receipt後、明示DBをmode=ro/query_onlyで照合。50artifact内92sourceのうち88sourceが実DBのwhole object・content/native SHA・最新分類・source availabilityに一致し、残る4sourceは対象外2社の原典/派生。実48派生233項目。227sources/226classifications/136completed jobs、133attempts/266events/133receipts、32heads/64versions/176readsも一致。DB SHAは前後不変、接続閉鎖済み。

追加は1518年次実績148.30/1453.23、6200年次実績49.20/148.70、6814年次実績529.53/2826.61（いずれも円/株）。1518の既存予想を上書きせず、6200のconcept・duration/frequencyを名称統一せず保持。各株式/期間/BBT/NCI/OCI/会計変更/未確認範囲も原scopeのまま。新6sourceのnative/実firstsaveも一致。

初回RO補助チェックで全3社の管理日をJan16と誤って要求し停止した。初回driver/停止証跡/候補を保持し、会社別凍結packetとwhole一致する確認へ修正して再照合した。1518は既存Jan15、6200/6814はJan16、全体Jan15=12/Jan16=20を保持。原データ修正や成功mutatorの再実行はない。

金融意味・モデル入力・価格・売買・IR送信の採用なし。GET・DB/Store書込・旧索引/旧成果物/公開code/共有docs編集なし。root独立受入待ち。詳細と全SHAはworker-validation.json。
