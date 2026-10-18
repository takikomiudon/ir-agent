v41 canonical接続：root実保存後の読取専用照合

新canonical disclosed-fact-index-v41.jsonは33社247fact・50親entry・52派生source・43会社/原典組。実接続は50派生240fact、8331/9702の2派生7factはfile-only。全項目のper-fact artifact/source overrideを優先して原bundleへ解決し、索引に存在するfieldを照合した。

artifactにある96source objects中、実DBにある92件についてwhole object/nativeSHA・本文SHA・最新分類・引用・source保存来歴を照合。対象外2社の原本/派生4source objectsは未接続のまま。新21sourceもroot receiptのnativeSHA/信頼された初保存時刻と一致した。新7factは実績/当時予想・旧/修正・DPS期間labelonlyを維持し、金融入力を採用していない。

実DBはmode=ro/query_only、明示transaction、contextlib.closingで閉鎖済み。DBmain前後SHAは9baff7307207746bbc6402e4a0123e9d1dc6eadb6aca0f960283409e4789a1d6で一致。root actual-verification.json（fd68fcf…）の全27table件数、source型、job状態/種別、保存来歴、32native heads・72版・187既読、管理日分布、指定8case要約、新21分類のtrue10/false10/null1も一致した。

今回snapshotは253source・分類252・全166job完了。財務内容41社には会社目標/収益モデル等の議論を含み、年次財務認証41社や金融モデル入力採用を意味しない。これらは読取時点のsnapshotであり、将来の現在値保証ではない。

旧v40の48親240factはwhole同一、旧v40 actual227source全体もhistoryに保持。旧4fact候補・rev2候補、producer原本・既存索引を変更していない。新2親の実保存flagだけをtrueへ接続し、候補は過去の準備状態のまま残した。

worker-validation.jsonに照合/閉鎖記録・入力pins。DB/Store書込・GET・共有docs変更・金融採用0。root受入待ち。
