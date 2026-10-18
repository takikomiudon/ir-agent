# 数値仮説前の定性レビューjobの接続

watchで数値thesisがない会社は通常dailyの対象にならず、著者論点の新資料・管理日を手動で点検していた。専用のopt-in case台帳とqualitative_review packetを追加し、既存のjobs・会社単位lease・世代・要求receiptを再利用した。Anthropic thesis-trackerの新データ/pillar点検と四半期レビューを研究段階へ適応したもので、著者の売買条件を追加していない。

[使い方](../../docs/qualitative-research-jobs.md)／[実装](../../src/ir_agent/qualitative_research.py)／[統合テスト](../../tests/test_qualitative_research_integration.py)。通常daily/intake/金融thesis・IR返信処理は保持する。明示caseだけが対象で、外部manifestを書き換えず台帳versionへ進捗を追記する。

親による16統合テストと全1,396件が成功（unittest39.381秒）。全体検証中は実DB不変。結果・ログ・sourceSHAはparent-full-suite.json/log、受入範囲はparent-acceptance.json。新コードの独立agentレビューは完了していない。源流DAG/公開性/保存来歴は既存readerを再利用し、意味や投資成績は認証しない。

実適用前にDBコピーで12case・62sourceの引継ぎと重複起票0を確認。旧checkpointにsourceID/SHAが直接ない場合は拒否され、明示inventoryを持つ固定manifestをreview_refとするv2へ修正した。初回失敗・旧入力も保持。検証を弱めて通していない。bootstrapの日時は既存レビューの再利用を確認した現在のcheckpointで、旧原記録のレビュー日時を遡及更新していない。

バックアップ後に実DBへ12case version1を登録。新規job0、旧全テーブルの行数/全行SHAは不変。sources116、分類115、job47/attempt44/event88/receipt44、legacy28/trusted88、金融thesis/質問/返信/採用policy0も保持。実clock/バックアップ/前後SHA/queue結果はactual-bootstrap.jsonとexecution-start.json。登録は研究進捗の引継ぎで、bootstrapの意味検証はfalse。

デモはメモリ内DBで分類→定性review→version2を通し、新規1/重複0/完了後0・金融thesis0を確認。demo-smoke.jsonに保存。新GET、IR送信、注文、外部scheduler設置は0。

worker用SKILLの新kind分岐だけを追加し、旧全文をbefore-jp-equity-ir-SKILL.mdへ保存した。過去の研究が持つskill指紋は当時の版で、skill-update.jsonに新旧対応を記録。旧研究ファイルや原文sourceは編集していない。

後続の[実公式資料1件によるレビュー](../ir-case-studies-2026-10-15/1980/issuer-quarter-followup/README.md)も完了。bootstrap時点の116資料・12case v1は履歴として保持し、現在の進捗を後付けしない。
