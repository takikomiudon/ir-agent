# 質問前の研究baselineを固定する

`research-decision-review`で保存した判断を、任意の`decision_contract.research_baseline_id`で新しい質問へ結び付ける。回答前にどの保存判断を選んだかを残すもので、金融入力の採用、IRの効果の実証、送信許可ではない。baselineの作成・計算は[保存研究の判断](research-decision-reviews.md)の既存APIを使う。

```json
{
  "decision_contract": {
    "policy_id": "ADOPTED_POLICY_ID",
    "policy_version": 1,
    "quote": {},
    "synthetic": false,
    "research_baseline_id": "SAVED_RESEARCH_REVIEW_ID"
  }
}
```

`quote`には実際の出典付き価格snapshotを指定する。上はID参照の形式であり、空の価格や未設定方針で判断が完了する例ではない。callerはbaseline IDだけを追加し、snapshot/SHA/初回保存時刻/basis/current_viewを渡さない。

サーバは同company、thesis版・snapshot SHA、policy ID/版・SHA、quote snapshot、synthetic区分、有効なheldを照合する。baselineの実`first_saved_at`と評価`recorded_at`は質問`created_at`以前を要する。元source閉包のID/SHA、当時の保存来歴も確認し、申告日だけの後付けを認めない。既知の不一致は保存前に拒否する。

契約に追加される`research_baseline_binding`はサーバ専用で、baselineの不変record SHA、実初回保存時刻、評価時刻、basis、保存時の結果statusを保持する。`current_view`は凍結しない。`verify_saved_contract`はrecord/SHA/初回保存時刻を再照合する。元baselineの編集や自動再評価は行わない。

baselineの担当者assessmentと質問の根拠は、同じthesis内の別subsetでよい。positionの観測IDや時刻が違っても、質問時点で利用可能な有効heldが同じなら受け入れる。回答前のassessmentと各回答枝の条件付きthesis_status/actionも同一である必要はない。

`basis.kind: saved_research`には既存IRを含む場合がある。`public_only`と`has_IR_reply_origin`をそのまま保持し、prior IR入りを公開資料のみのbaselineと呼ばない。今回質問自身への返信を含むbaselineは拒否する。いずれの区分も、公開性や企業原文の真正性を独立に認定するものではない。

保存結果が未解決のbaselineは参照付きdraftにできるが、preflightは`needs_review`になり、送信済み記録へ進めない。必要な保存来歴やpositionが未知の場合も保留する。後から時間が経っただけで元baselineを完了へ昇格させない。前提が変われば新しいbaselineと質問を作る。

価格・保有と情報訂正の時計を分ける。既存`mark-sent`は外部で送信済みの事実を記録する操作で、価格鮮度と保有は申告`sent_at`基準を維持する。現在のbaseline表示が価格期限切れ/保有変更という理由だけで、当時有効だった歴史送信記録を追加拒否しない。一方、情報訂正はtrusted runtime nowでも確認し、quoteだけにあるIR祖先も含む全baseline閉包のhold/未消費分類版を無視しない。歴史baselineの好結果で現在の情報holdを迂回できない。このハーネスは外部送信を行わない。

baseline IDを省略した旧契約は従来のserver JSONと動作を保つ。同じ質問の完全再送は最初の凍結結果を返し、IDの追加・削除・差替えを認めない。再送が成功することと、現在その契約を利用できることは別で、利用時に元の価格/保有/情報gateが働く。旧質問へbaselineを後付けしない。
