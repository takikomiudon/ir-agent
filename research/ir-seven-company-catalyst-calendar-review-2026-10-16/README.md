# 公開IRカレンダーの独立点検（今回4社）

2929・4318・3817・6814の保存raw内の該当表／年区画、visible text、source bundle、引用、予定候補、worker validationを確認した。重大な誤対応は0。1975や他の受入済み資料は再調査していない。

| 会社 | 実行用requestへの投影で保持すること |
|---|---|
| 2929 | 将来の掲載は2026-10-28総会のみ。決算発表kindへ置換しない。次の決算日はこの範囲で未確認。 |
| 4318 | rawのy2026区画で2026-10-30＝2027年3月期2Q発表予定。5月12日の説明会／10:30は別の過去行で、発表時刻へ借用しない。 |
| 3817 | 11月中旬の発表／11月下旬の機関向け説明会／2月中旬の発表は別候補。date:nullと原月区分を保持し、具体日を埋めない。 |
| 6814 | 2027-01-08、04-09は2027年2月期Q3／通期、07-09、10-08は2028年2月期Q1／Q2。全て予定。2028年中旬・下旬や総会を勝手に追加しない。 |

4sourceのcontent＝保存text/02＝builder snapshot.text、native整合、29引用のUnicode/UTF8位置と4318のraw年binding2引用を独立に確認。builder whole再生成一致はworker証跡を点検したもので、ここで再実行していない。raw/content/nativeのSHAは別域。元資料は不変更。

現APIの厳密allowlistへ別requestを投影する際は、2種類のevent kind、単一schedule claim、time/timezone:nullを守る。3817説明会の期ラベル未記載は、periodの必須文字列descriptorで未記載と明示し、具体期を創作しない。raw HTMLの引用／offsetをsource.content引用へ混ぜず、4318年結合の手動根拠は別rationaleへ残す。

全件due/scheduled_atはnull、実施・結果資料は未確認。沈黙期間は当該calendar範囲に明示未確認で、全社方針不存在を意味しない。DB保存・分類・availability・request実行はこの点検範囲外。GET・DB接続・Store・既存ファイル編集・テスト／共有code変更なし。input pinsと詳細はindependent-review.json。

非重大のbundle境界：2929/4318は会社stub各1件、3817/6814はcompanies=[]。rootの実保存用集約ではwhole sourceだけを取り込みcompanies=[]とし、元bundleと既存会社状態は変更しない。
