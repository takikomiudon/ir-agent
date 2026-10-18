# 保有申告とカタログ既定値の判断境界：実装checkpoint

**会社metadataのheld値と、実判断に使う明示保有申告を分離した。** 旧company JSON・position履歴を移行で更新せず、既存position_observationsに結ぶ小さなposition_declarations receiptを追加する。既存position_atはmetadata履歴として維持し、DecisionLifecycleだけdeclared_position_atへ接続した。

明示のcompany set-status --held/--no-held、又はStore.declare_position APIは新しい観測と現在の申告receiptを同時保存する。同値でも新観測で、旧行へreceiptを後付けしない。kind=user_declaration / origin=explicit_user_declaration / broker_verified=falseは利用者申告の意味であり、証券口座の監査ではない。実時計はwrite transaction取得後に採取し、試験用now注入はtrusted runtime入力として扱う。

catalog・ingestの省略/明記held・provider更新・再起動・held省略status変更はmetadataに留まり、新たな申告receiptを作らない。queueのheld metadata利用は従来どおり。実判断ではas_of以前の最新観測そのものにreceiptが必要で、receipt時刻もas_of以下とする。最新行が無資格なら古い申告へfallbackしない。synthetic_positionの既存限定例外は維持する。

対象80テスト（新規12を含む）が成功。catalog/明記false/true、同値申告、時点、legacy再open、provider更新、receipt途中失敗時の会社・status・観測rollback、固定済み質問不変、CLIのheld省略/--no-held/--heldを確認した。既存金融期待値は弱めず、宣言のkindと失敗注入先だけ新責務へ合わせた。全件suiteは実行していない。

[implementation.json](implementation.json)に実API・対象テスト・SHA・変更範囲を保存し、[source-after](source-after/)に変更3code/既存1test/新規1testの全文byte copyを固定した。旧before/review/probeは変更していない。実DBアクセス・GET・送信は0。

旧保存判断をcurrent_decision_viewで表示する際のposition由来再点検は、親が別に確認する隣接境界として今回変更していない。またpure decision/ir-plan CLIは従来からsnapshot-onlyで、この修正によりlive DB保有確認が付いたとはしない。金融閾値・予測・方針は追加していない。以後このcheckpointのコード編集を停止し、独立レビューへ渡す。
