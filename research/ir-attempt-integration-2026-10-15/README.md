# ジョブ試行計測の接続

全1033テスト成功（33.573秒）。OpenTelemetryの開始・終端・属性の考え方を参照し、将来のジョブ確保からleaseの開始・更新・完了・観測した期限切れを不変に記録する。DB台帳・CAS・投影はプロジェクトの設計であり、外部標準の金融判断方式ではない。

研究結果と資料分類の両経路で、結果と計測を同じトランザクションで保存する。開始・更新・完了・期限切れの記録失敗を注入し、結果やleaseの更新が一緒にrollbackすることを確認した。CLIのclaimは `--measurement-kind observed / synthetic / unknown` で区分を明示でき、省略はunknown。未知区分と時計異常は能力集計へ入れず理由を残す。

[実DBの読取り結果](actual-attempt-measurements.json)では計測済み0件、旧ジョブ3件が未計測。台帳用2tableのみ追加し、過去の開始時刻は捏造していない。原source JSON群の前後hash一致を[summary](summary.json)へ記録した。active・tokens・費用は未計測であり、0にしない。会社数上限も推定しない。

[原テストログ](tests.log)、コードhash、3種の架空デモを同梱する。claim/renewの再送receiptは未実装。別の独立点検で、後から保存した仮説が古いas-of表示へ混入する不備を再現した。判断履歴の実保存時刻は正しく残っており、次はこの過去表示の問題を修正する。
