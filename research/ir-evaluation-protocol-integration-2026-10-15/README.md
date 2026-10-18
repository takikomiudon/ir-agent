# 評価手順の不変記録

全1,154テスト成功（35.163秒）。[原典の支持範囲と評価手順設計](../../docs/evaluation-protocol-design.md)のAだけを実装し、不変版・CAS・再送・trusted first-saveを持つprotocol registryをStore/CLI/statusへ接続した。Gneiting–Rafteryのproper scoringとgroup/time分割の原則を踏まえた記録方式はプロジェクトへの適応である。

返却はprotocol_commitment_only。空欄を補わずdraft/unset_fieldsへ残す。全欄を埋めても参照・引用・著者原則の採用・規則・前向き性・盲検・独立性はunverified、実行not_performed、採点適格not_assessed。packet builder、判定レビュー、scorer接続は未実装。

[全件ログ](tests.log)、[対象25件](target-tests.log)、[独立再確認](independent-recheck.json)、[コードSHA](source-code-sha256.json)、[要約](summary.json)を保存。別担当は後続版後の旧版retry、2connection競合、外側rollback、late recorded_atでも非昇格、CLIと他table不変を確認した。

[実スキーマ確認](actual-schema-check.json)では空tableだけを追加。以前の全table行とSHAは完全不変、実protocol登録0件。34source/34分類、仮説・実予測・送信・注文0件。初回CLI対象テストのエラー文期待の修正はsummaryへ記録し、登録や金融条件の変更と混同しない。
