7社の公開検証予定：接続前の準備

新規カレンダー原典5件（2929/4318/3817/6200/6814）を `source-bundle.json` に集約した。source whole object・ID・native SHAはproducerと同一。2929/4318の旧bundleには会社stubが各1件あるが、ここでは会社更新を除き `companies:[]`、`theses:[]` を維持した。1518既存会社カレンダー/JPX・1975既存カレンダーは再登録しない。

| 会社 | 予定request数 | 確認内容 |
|---|---:|---|
| 1518 | 1 | 既存JPX・10月8日時点のQ2予定11月13日。会社カレンダー直接記載と混同しない |
| 1975 | 4 | 既存4requestを値としてそのまま再利用 |
| 2929 | 0 | 10月28日定時株主総会はAPI未対応でomittedへ。次の決算日は不明 |
| 3817 | 3 | Q2「11月中旬」、機関投資家説明会「11月下旬」、Q3「２月中旬」。全date:null |
| 4318 | 1 | 2026年10月30日Q2予定。明示year selectorと同idのtable対応根拠を保持 |
| 6200 | 0 | 次日未確認。旧2025年次日程を新年へ移さない。年間画像は未取得 |
| 6814 | 4 | 2027年1月8日Q3、4月9日通期、7月9日Q1、10月8日Q2 |

3817機関投資家説明会には対象FY・四半期が明記されていない。APIの非空文字列descriptorには「未記載」と記録し、Q2への帰属を推測していない。earnings_presentationの機械形式へ対応した候補であり、その説明会が特定決算の説明会であるという意味確認は未了として `schedule-inventory.json` に残す。

`catalyst-schedule-requests.json` は既存allowlist7fieldsとschedule claim契約だけ。13件の内10件に日付があり3件は不明。全件time/timezone/supersedes:null、予定は実施未確認、due:null。新5sourceの公表時刻と実DB初保存はnull。既存1518/1975の初保存は保存済みtrusted receiptを参照した履歴で、現在DBを再確認した主張ではない。

Anthropic catalyst-calendarの公表予定収集・日程変更の再確認を参照し、既存projectのschedule-only仕様へ適応した。影響度・株価・結果改善・退出期限を補っていない。元caseの条件ID・管理日は変更していない。対象は既存producerが限定読解した次の検証予定であり、7社全サイト・全予定の網羅表ではない。

検証は `prepare.py --check` でローカルの原object一致/native hash/原文位置/既存純粋形式検証・保存成果のbytes再現まで。新API、report実行、DB/Storeアクセス、CLI mutator、GET、金融採用、IR送信は0。実際のsource保存・分類・read-only reportはrootの次phaseであり、ここではsource_bound_candidateと認定しない。
