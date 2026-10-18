# 次回決算予定への保存ルート：135A・1721・9765

新GET0で保存公式snapshotを点検しました。具体的な次回決算日として確定できたものはありません。予定と実施、研究管理日2027年1月15日は別です。全候補のtime/timezone/scheduled_at/dueはnullを保持しています。

| 会社 | 保存根拠で確認できたこと | 次の有限確認 |
|---|---|---|
| 135A | 公式IRカレンダー本文に「1月中旬 第3四半期決算発表」等の年間一般表。年・対象FY・具体日・時刻・timezoneは未明示。 | 取得済み一般表から1/15を作らない。今回追加取得案なし。 |
| 1721 | 保存会社予想HTML links[64] にactualhref `/ir/schedule.html`、「IRスケジュール」。その本文は未取得。 | 同じ公式実URL1頁だけ、必要なrobotsを含め最大2GETを提案。 |
| 9765 | 点検した保存公式HTML群にはcalendar/schedule実hrefや次回の具体日を見つけていない。 | 推測URLや空動的短信index/保留hostへ進まず、追加取得案なし。 |

1721の実URLは `https://www.comsys-hd.co.jp/ir/schedule.html` です。今は本文未読で、日程が載ることや最新性を認定していません。135Aは中旬という精度を保持し、過去の発表日や現FYから将来日を補完していません。9765で未発見なのも、会社全体で予定非公表という結論ではありません。8151は会社hostの保存保留を維持するため対象外です。

`routes.json` に各社の原fileSHA・JSONpath・逐語引用/offset、135A/1721のrawSHA、既存の著者条件/未解決定義IDを保存しました。具体的な日程を得ても、予定≠発表済み、timezone不明ならdue=nullという既存契約を保持します。sourceのDB来歴/分類、monitor実行・入力投影・manifest更新は今回行っていません。

管理日については既存operational-calendar-basisの3記録を参照しました。Asia/Tokyoは研究管理用の設定であり、会社発表予定のtimezoneではありません。GET/DB/code/旧資料/manifest/モデル/IR操作は0、旧入力不変は `validation.json` に記録しています。
