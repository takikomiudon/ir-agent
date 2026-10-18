# v39のread-only接続確認

新しい`disclosed-fact-index-v39.json`は31社・234項目・45親・47派生・38会社/原典ペア。旧v38の43親230項目はwhole同一で、全234項目について索引に含まれる値・kind・period・scope・unit等が解決先と一致する。8331・9702の2派生7項目は対象外のまま。

root receiptの後、実DBを`mode=ro`・`query_only`で照合。47artifact内86sourceのうち82sourceが実DBのwhole object・native/content SHA・分類・availabilityと一致し、残る4sourceは対象外2社の原典/派生。実保存45派生227項目。221sources・220classifications・130completed jobs・127attempts/254events/127receipts・30heads/59versions/170readsを確認。DB SHAは前後不変、照合用の接続は全て閉鎖済み。

2929は原本のEPS68.61円/BPS453.35円と訂正の別参照を維持し、訂正適用・最新値の認証をしない。4318はEPS74.11円/BPS345.24円、既分割調整・ESOP平均/期末の区分を保持。新5sourcesの実firstsaveとnative SHAもroot receiptに一致。v38のactual whole objectは新索引内の別historyへ保存。

候補・旧索引・原本・旧定性結果・公開code・共有docsは変更していない。金融意味/入力・参考価格・売買・IR送信の採用なし。rootの独立受入は未完了。詳細と全SHAは`worker-validation.json`。
