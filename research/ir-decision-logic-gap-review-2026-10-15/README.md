次の実装は、未送信質問の閉鎖状態を修正する小タスクが先。公開資料だけによる保存判断は別agentの設計候補へ留める。新規方針・閾値・予測は必要ない。

1. **優先1：未送信draftをno_response/declinedへ閉じられる故障。** `Harness.close_question`（harness.py:449）はdraft/awaiting_replyを同じ許可集合にし、理由との組合せを見ていない。productionメソッドをSQL記録だけのstand-inへ接続すると、draft→no_responseでexpired/sent_at:null、draft→declinedも成功する。前者にadd_replyするとINSERT前に`timestamp must be a nonempty string`。DB接続/書込み0で分岐を再現した。
2. **優先2：公開資料だけによるpolicy判断の保存経路（設計のみ）。** 単体`decision`は既実装。一方、保存decision_reviewsはreply_id必須、DecisionLifecycle.add_reviewは適用済み返信必須で、公開研究のcompleteは入力されたproposed_actionを保存する。別agentが最小設計を担当中なので、ここでは重複設計・実装を増やさない。

閉鎖の最小状態表（列はno_response / declined / cancelled、記号×は拒否）：

|元状態|現在|修正後|
|---|---|---|
|draft|expired / declined / cancelled|× / × / cancelled|
|awaiting_reply（送信記録あり）|expired / declined / cancelled|expired / declined / cancelled|
|answered|× / × / ×|× / × / ×|
|expired|× / × / ×|× / × / ×|
|declined|× / × / ×|× / × / ×|
|cancelled|× / × / ×|× / × / ×|

既存の不整合データでawaiting_reply/expired等なのにsent_atがない場合も、返信を記録できる状態とはせず明確に拒否する。旧行の書換えや新しい期限の発明はしない。既存workflow.py:420のテストは送信後のexpiryだけを扱うため、未送信拒否・18組合せ・拒否時不変・送信済expiry後の遅延返信維持が追加点になる。

運用上の閉鎖と観測cohortは別。observations.py:229は未送信を分母から除外し、241/258は独立に固定されたreply_deadlineとresponse_check.checked_throughを使う。close_questionのno_response/closed_atだけでno_response_by_deadlineを作らない。ここは既実装であり、集計やEVSIを作り直す必要はない。

採用元はAnthropic thesis-trackerの新情報ごとの影響記録・反証追跡、idea-generationの結果追跡。状態遷移と保存APIはその研究運用への適応で、著者の売買閾値や待機日数ではない。事前分岐・入力差分・公開性訂正・価格鮮度・unweighted・定性job等も既実装で再提案しない。

[詳細と具体的path/lines](gap-review.json)、[全18状態再現](closure-reproduction.json)。SQLite統合テストは今回未実施で、修正タスクでfocusedに行う。ネット・DB・既存ファイル変更0。

## 修正の受入

下書きは取消だけ、無回答・辞退は有効な送信時刻のある返信待ち質問だけに限定した。旧時刻不整合への新返信は、原子性を保って明確に拒否する。取消による片づけと送信済み期限切れ後の返信は維持し、期限・観測信号・金融条件は追加しない。主担当が最小diffと新4テストを確認し、[全1,448件・36.901秒成功](parent-full-suite.json)、実DB124資料SHA不変を確認した。[受入記録](parent-acceptance.json)。
