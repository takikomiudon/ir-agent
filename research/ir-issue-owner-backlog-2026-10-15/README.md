# 未解決点の答えを誰が持つか：6社の依存付きbacklog

**公開根拠を照合し、残る会社定義だけを研究草案へ。その先の予測・評価式・採用方針は投資家側の仕事として分ける。** 既存監視v8の6社35sourceを基準に、19項目を整理した。優先順位や実行日ではなく依存関係を示す。今回DBは開いておらず、1518ニュース一覧と7525FAQは親の取り込み記録を参照する。

| 会社・既存論点 | 公開確認が先（P） | 会社の定義だけ（C：P後も残る場合） | 外部著者/提供者の答え（A：並行） |
|---|---|---|---|
| 135A · `135A-author-condition-case-monitor` | `135A-public-basis`：同じ顧客単位/売上コホート/期で次の原表を照合。既読KPIや金沢営業開始を再質問しない。 | `135A-company-definition`：既存v2の「1社」単位・比較期間の範囲変更。受注基準は既答。 | `135A-author-boundary`：AENTROの近辺/頭打ち期間/CAGR基準。明示ANDの片側だけを採用しない。 |
| 1518 · `1518-existing-business-and-investment-profit-drivers` | `1518-public-basis`：山洋の実施/連結開始・同範囲の事業と投資利益。ニュース一覧では完了未確認。 | `1518-company-definition`：公開注記でも残る会社固有の帰属/連結範囲。既知のP/L区分は再質問しない。 | `1518-author-boundary`：FISCOの将来重要性・反復性という定性解釈。会社の将来運用益保証にはできない。 |
| 1721 · `1721-author-condition-case-monitor` | `1721-public-basis`：正式原表/同版・精度の照合。raw点検済みでもNI表示差の原因は未選択。 | `1721-company-definition`：会社の精度/予想版、事業/segment・消去/費用定義。既知の未消去注記は使う。 | `1721-author-boundary`：SRの強み3/弱み3・同業相対評価の意味/許容幅。単一Q1で構造を断定しない。 |
| 7525 · `7525-author-watch-original-product-ratio` | `7525-public-basis`：GP/LV・空の入口・FAQ10問は読了。比率固有の売上範囲は未解決。 | `7525-company-definition`：既存preflight-v2の連単/内部取引/GP-LV共通性。Aでも過去実績の期/分類まで認証しない。 | `7525-author-boundary`：QUICKの「伸び悩み」の許容幅/期間。会社長期目標は著者の反証規則ではない。 |
| 8151 · `8151-astris-20250603-forecast-conditions-monitor` | `8151-public-basis`：正式会社本文はrobots保留。旧Astris EとQUICK会社NI換算を同じ予測にしない。 | `8151-company-definition`：公表会社の受注→売上/納入/検収・株式等の定義。将来利益を保証させない。 | `8151-author-boundary`：Astrisの感応度、QUICK日次分母/算定日・平均窓。会社IRが決めるものではない。 |
| 9765 · `9765-sessa-author-conditions-monitor` | `9765-public-basis`：正式短信未取得。SIR本文/表の年度差とEPS/利益率基準の一次照合が不足。 | `9765-company-definition`：官民/子会社の受注範囲、人員/資格者の数え方等。国交省日額の一般説明は既答。 | `9765-author-boundary`：SIR上振れ/需要捕捉の定性評価。原因列挙をformalAND/ORや十分条件へしない。 |

P→Cは、利用可能な公開情報を読んでも会社の定義が残る場合だけ。新たな公表定義が答えていれば草案を除く。既存135A/7525草案を再利用し、他4社の質問文は今回作っていない。8151の会社host、1721のSR、9765の動的E-IR等の既存取得制約を尊重し、迂回取得や会社からの送付を実行計画にしていない。

横断項目 `investor-model-adoption-gap` は**選ぶ会社/モデルごと**の不足を残す。KPI→利益→税後EPS/CFの数量関係、同じ期/株基準、評価式の適合と採用方針は研究担当/利用者側にある。6社全ての完了や著者の返答を、他社の公開比較を止める条件にはしない。足りない予測・倍率・閾値・確率をAPIのために仮置きしない。

| 数値の主体を混ぜない | 今回の扱い |
|---|---|
| 135A | 会社予想とAENTROの条件付き将来見通しを分離。社数・単価・継続売上はEPSそのものではない。 |
| 1518 | 通期EPS/DPSの旧/新は会社予想。FISCO独自EPSにしない。投資利益の将来継続性は別。 |
| 1721 | SRの通期数値は会社計画再掲。会社HTMLとの表示差を、原raw点検後も丸め等へ決めつけない。 |
| 7525・8151 QUICK | 会社純利益予想を基にした著者EPS換算を、会社公表EPS原値/独自利益予測へ置換しない。日次分母は提供者側の仕様。 |
| 8151 Astris | 既存E予測を別著者/別時点として保持。後のQUICKを改訂版や成否ラベルへしない。 |
| 9765 | SIRの会社予想再処理と、上振れ/EPS改定への定性見方は別。会社基準を著者の買い条件にしない。 |

方法の原則は保存原典から参照した。Anthropic thesis-trackerは “Does this strengthen, weaken, or neutralize a specific pillar?”（AT03）、earnings-previewは会社前四半期コメントの確認（EP01）を求める。Damodaranは “Tie your narrative to key numbers that you will be using in your valuation.”（slide4、DM01）。固定commit URL・短引用・頁/offset・SHAは[backlog.json](backlog.json)に保存した。**IRの答えの所有者、公開→条件付き草案→必要時の数値根拠という具体的な依存設計は本プロジェクトの適応**で、原著が6社の質問や閾値を指定したものではない。数値評価の不足は定性的な資料比較を止める理由ではない。

各タスクの必要資料・完了条件・次依存と根拠file/hashは[backlog.json](backlog.json)。既存ready判定、管理日、preflightを変更していない。具体的な次回決算日は補わず、一般年間表・会社予定・研究管理日を分ける。新calendarの受信/登録・具体日確認は別作業で、このbacklogが確認済みへ昇格するものではない。情報価値は未推定で、0とも正とも判定していない。新GET/DB/production/旧file変更・新IR草案/送信・モデル採用は0。これはIR送信の実行計画でも売買判断でもない。
